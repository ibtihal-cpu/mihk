#!/usr/bin/env python3
"""Experiment: what happens if DNA encoding is applied BEFORE LBG-VQ?
usage: python3 dna_before_vq.py [gray_image.txt]   (512x512, one 0..255 value per line)
Same LBG as the thesis code: mean init, +-1% splitting, Lloyd until rel. change <= 1e-4 (max 100), K=64, 4x4 blocks.
A) pixel vectors (16-d)            -> current method
B) DNA symbols A,C,G,T = 0,1,2,3   -> each pixel = 4 bases (2 bits each, MSB first), vector = 64-d
   B-valid : centroid symbols rounded to the nearest base (a real DNA sequence)
   B-cont  : centroid symbols kept fractional (not valid DNA; best case for B)
"""
import sys, time
import numpy as np

def load(path):
    if path:
        a = np.loadtxt(path, dtype=np.int64)
        n = int(round(a.size ** 0.5)); return a[: n * n].reshape(n, n).astype(np.uint8)
    from sklearn.datasets import load_sample_image
    from PIL import Image
    g = np.asarray(Image.fromarray(load_sample_image("china.jpg")).convert("L"))
    return g[:424, :424]

def blocks(img, b=4):
    h, w = img.shape
    return img.reshape(h // b, b, w // b, b).transpose(0, 2, 1, 3).reshape(-1, b * b)

def unblocks(v, h, w, b=4):
    return v.reshape(h // b, w // b, b, b).transpose(0, 2, 1, 3).reshape(h, w)

def lbg(X, K=64, delta=0.01, eps=1e-4, max_iter=100):
    X = X.astype(np.float64); n = len(X)
    cb = X.mean(0, keepdims=True); k = 1; iters = 0
    x2 = (X * X).sum(1)
    while k < K:
        cb = np.vstack([cb * (1 + delta), cb * (1 - delta)]); k *= 2
        prev = 1e30
        for it in range(max_iter):
            d = x2[:, None] - 2 * X @ cb.T + (cb * cb).sum(1)[None, :]
            lab = d.argmin(1); dist = d[np.arange(n), lab].sum() / n
            for c in range(k):
                m = lab == c
                if m.any(): cb[c] = X[m].mean(0)
            iters += 1
            if abs(prev - dist) / (dist + 1e-9) <= eps: break
            prev = dist
    d = x2[:, None] - 2 * X @ cb.T + (cb * cb).sum(1)[None, :]
    return cb, d.argmin(1), iters

def psnr(a, b):
    mse = ((a.astype(float) - b.astype(float)) ** 2).mean()
    return 10 * np.log10(255 ** 2 / mse), mse

img = load(sys.argv[1] if len(sys.argv) > 1 else None)
h, w = img.shape
V = blocks(img)                                   # (N,16)
print(f"image {h}x{w}, {len(V)} vectors")

t = time.time(); cb, lab, it = lbg(V); tA = time.time() - t
recA = unblocks(np.clip(np.rint(cb[lab]), 0, 255), h, w)
p, m = psnr(img, recA); print(f"A pixels      dim=16  iters={it:3d}  time={tA:6.2f}s  PSNR={p:6.2f} dB  MSE={m:8.2f}")

sym = np.stack([(V >> 6) & 3, (V >> 4) & 3, (V >> 2) & 3, V & 3], axis=2).reshape(len(V), 64)   # (N,64) bases
t = time.time(); cbS, labS, itS = lbg(sym); tB = time.time() - t
wts = np.array([64, 16, 4, 1.0])
def decode(cbS, rnd):
    s = cbS[labS].reshape(len(V), 16, 4)
    if rnd: s = np.clip(np.rint(s), 0, 3)
    return unblocks(np.clip(np.rint((s * wts).sum(2)), 0, 255), h, w)
for name, rnd in (("B-valid DNA ", True), ("B-cont       ", False)):
    p, m = psnr(img, decode(cbS, rnd))
    print(f"{name} dim=64  iters={itS:3d}  time={tB:6.2f}s  PSNR={p:6.2f} dB  MSE={m:8.2f}")
print("same K=64 -> same index bits per block; codebook size equal (16 px x 8 bit = 64 bases x 2 bit)")
