#!/usr/bin/env python3
"""Controlled DWT + Huffman baseline implemented in this work (grayscale 512x512), matched to the proposed codec's compression ratio.

For every image the baseline is tuned so that its COMPLETE compressed size gives (approximately) the SAME compression ratio as the
proposed codec (system CR read from correctness.csv); PSNR and SSIM are then computed with exactly the formulas of sem_v3.c
(PSNR = 10 log10(255^2/MSE); SSIM = 11x11 Gaussian window, sigma 1.5, K1 = 0.01, K2 = 0.03, mean over the valid region).

Codec: L-level 2-D Haar DWT of the image -> uniform dead-zone quantization of all coefficients with one step Delta (found by bisection)
-> coefficients scanned subband by subband, coded as (zero-run, non-zero level) tokens -> canonical Huffman over the tokens.
Size = Huffman data bits/8 + 4 bytes per distinct token (the same table accounting as the proposed codec) + 16 bytes of header.
It is a generic DWT + entropy-coding baseline; it is NOT the implementation of any specific published method.
usage: python3 run_wavelet_baseline.py correctness.csv img1.txt img2.txt ...  > wavelet_baseline.csv   (needs numpy only)"""
import csv, heapq, math, os, sys
from collections import Counter
import numpy as np
N, L = 512, 4

def haar2(a):
    a = a.astype(float)
    lo = (a[:, 0::2] + a[:, 1::2]) / 2; hi = (a[:, 0::2] - a[:, 1::2]) / 2
    ll = (lo[0::2] + lo[1::2]) / 2; lh = (lo[0::2] - lo[1::2]) / 2
    hl = (hi[0::2] + hi[1::2]) / 2; hh = (hi[0::2] - hi[1::2]) / 2
    return ll, lh, hl, hh
def ihaar2(ll, lh, hl, hh):
    lo = np.empty((ll.shape[0] * 2, ll.shape[1])); hi = np.empty_like(lo)
    lo[0::2] = ll + lh; lo[1::2] = ll - lh; hi[0::2] = hl + hh; hi[1::2] = hl - hh
    a = np.empty((lo.shape[0], lo.shape[1] * 2)); a[:, 0::2] = lo + hi; a[:, 1::2] = lo - hi
    return a
def dwt(img):
    bands = []; a = img
    for _ in range(L):
        a, lh, hl, hh = haar2(a); bands.append((lh, hl, hh))
    return a, bands
def idwt(ll, bands):
    a = ll
    for lh, hl, hh in reversed(bands): a = ihaar2(a, lh, hl, hh)
    return a
def quant(c, d): return np.sign(c) * np.floor(np.abs(c) / d)        # dead-zone quantizer (zero bin width 2*Delta)
def dequant(q, d): return np.sign(q) * (np.abs(q) + 0.5) * d * (q != 0)

def tokens(qs):
    t = []; run = 0
    for v in np.concatenate([q.ravel() for q in qs]).astype(int):
        if v == 0:
            run += 1
            if run == 255: t.append((255, 0)); run = 0
        else: t.append((run, int(v))); run = 0
    if run: t.append((run, 0))
    return t
def huff_bits(tok):
    cnt = Counter(tok)
    if len(cnt) == 1: return len(tok), 1
    h = [[w, i, [(s, 0)]] for i, (s, w) in enumerate(cnt.items())]; heapq.heapify(h); k = len(h)
    L_ = {s: 0 for s in cnt}
    while len(h) > 1:
        a = heapq.heappop(h); b = heapq.heappop(h)
        for s, _ in a[2] + b[2]: L_[s] += 1
        heapq.heappush(h, [a[0] + b[0], k, a[2] + b[2]]); k += 1
    return sum(cnt[s] * L_[s] for s in cnt), len(cnt)
def encode(img, d):
    ll, bands = dwt(img.astype(float) - 128)
    qll = quant(ll, d); qb = [tuple(quant(x, d) for x in b) for b in bands]
    tok = tokens([qll] + [x for b in qb for x in b])
    bits, ntok = huff_bits(tok)
    size = bits / 8 + 4 * ntok + 16
    rec = idwt(dequant(qll, d), [tuple(dequant(x, d) for x in b) for b in qb]) + 128
    return size, np.clip(np.rint(rec), 0, 255)

def gauss_win():
    r = np.arange(-5, 6); g = np.exp(-(r.astype(float) ** 2) / (2 * 1.5 ** 2)); return g / g.sum()
def filt(a, g):
    t = sum(g[k] * a[:, k:k + a.shape[1] - 10] for k in range(11)); return sum(g[k] * t[k:k + a.shape[0] - 10, :] for k in range(11))
def ssim(x, y):
    x = x.astype(float); y = y.astype(float); g = gauss_win(); mx, my = filt(x, g), filt(y, g)
    sx = filt(x * x, g) - mx * mx; sy = filt(y * y, g) - my * my; sxy = filt(x * y, g) - mx * my
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    return float((((2 * mx * my + c1) * (2 * sxy + c2)) / ((mx * mx + my * my + c1) * (sx + sy + c2))).mean())

if len(sys.argv) < 3: sys.exit(__doc__)
prop = {}
for row in csv.DictReader(open(sys.argv[1])):
    if row["mode"] == "gray": prop[row["image"]] = float(row["seq"].split()[0])
print("image,method,target_CR,CR,bpp,PSNR_dB,SSIM,delta")
for path in sys.argv[2:]:
    key = os.path.basename(path)[:-4]
    if key not in prop: print(f"# skip {key}", file=sys.stderr); continue
    img = np.clip(np.fromfile(path, dtype=int, sep=" "), 0, 255).astype(np.uint8).reshape(N, N)
    target = prop[key]; lo, hi = 0.5, 400.0
    for _ in range(40):                       # bisection on Delta: larger Delta -> smaller file
        mid = (lo + hi) / 2; size, _r = encode(img, mid)
        if N * N / size > target: hi = mid
        else: lo = mid
    d = (lo + hi) / 2; size, rec = encode(img, d); cr = N * N / size
    mse = float(np.mean((img.astype(float) - rec) ** 2)); psnr = 10 * math.log10(255 ** 2 / mse)
    print(f"{key},DWT+Huffman baseline (this work),{target:.2f},{cr:.2f},{8 / cr:.3f},{psnr:.2f},{ssim(img, rec):.4f},{d:.2f}")
