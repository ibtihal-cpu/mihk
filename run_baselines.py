#!/usr/bin/env python3
"""Rate-matched comparison of the proposed codec with JPEG and JPEG 2000 (grayscale images).

For every image the baseline is encoded at (approximately) the SAME compression ratio as the proposed codec; PSNR and
SSIM are then computed with exactly the formulas of sem_v3.c:
  PSNR = 10 log10(255^2 / MSE);  SSIM = 11x11 Gaussian window (sigma 1.5), K1=0.01, K2=0.03,
  mean over the valid region (same as SSIM_window_based()).
CR of the baselines = W*H bytes / size of the COMPLETE encoded file (headers included).
The proposed-codec values (system CR, PSNR, SSIM) are read from correctness.csv (written by run_correctness*.sh), so they
always come from the same run as the other tables.

usage:  python3 run_baselines.py correctness.csv img1.txt img2.txt ...  > baselines.csv
Needs numpy and Pillow with JPEG 2000 support. Images are the same .txt files used by the C programs (grayscale, 512x512).
"""
import csv, io, os, sys
import numpy as np
from PIL import Image

N = 512

def gauss_win():
    r = np.arange(-5, 6)
    g = np.exp(-(r.astype(float) ** 2) / (2 * 1.5 ** 2))
    return g / g.sum()

def filt(a, g):  # separable 11x11 Gaussian, valid region only
    t = sum(g[k] * a[:, k:k + a.shape[1] - 10] for k in range(11))
    return sum(g[k] * t[k:k + a.shape[0] - 10, :] for k in range(11))

def ssim(x, y):
    x = x.astype(float); y = y.astype(float); g = gauss_win()
    mx, my = filt(x, g), filt(y, g)
    sx = filt(x * x, g) - mx * mx
    sy = filt(y * y, g) - my * my
    sxy = filt(x * y, g) - mx * my
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    return float((((2 * mx * my + c1) * (2 * sxy + c2)) / ((mx * mx + my * my + c1) * (sx + sy + c2))).mean())

def psnr(x, y):
    return 10 * np.log10(255.0 ** 2 / np.mean((x.astype(float) - y.astype(float)) ** 2))

def enc_jpeg(img, q):
    b = io.BytesIO(); Image.fromarray(img, "L").save(b, "JPEG", quality=q, optimize=True); return b.getvalue()

def enc_j2k(img, cr):
    b = io.BytesIO()
    Image.fromarray(img, "L").save(b, "JPEG2000", quality_mode="rates", quality_layers=[cr], irreversible=True)
    return b.getvalue()

def dec(data):
    return np.array(Image.open(io.BytesIO(data)).convert("L"))

def best_jpeg(img, target):
    best = None
    for q in range(1, 96):  # quality whose CR is closest to the target
        d = enc_jpeg(img, q); cr = img.size / len(d)
        if best is None or abs(cr - target) < abs(best[1] - target):
            best = (d, cr, q)
    return best

if len(sys.argv) < 3:
    sys.exit("usage: run_baselines.py correctness.csv img1.txt [img2.txt ...]")
prop = {}
for row in csv.DictReader(open(sys.argv[1])):
    if row["mode"] != "gray":
        continue
    cr, mse, p, s, it = row["seq"].split()   # "CR MSE PSNR SSIM iters"
    prop[row["image"]] = (float(cr), float(p), float(s))

print("image,method,setting,CR,PSNR_dB,SSIM")
for path in sys.argv[2:]:
    key = os.path.basename(path)[:-4] if path.endswith(".txt") else os.path.basename(path)
    if key not in prop:
        print(f"# skip {key}: not in {sys.argv[1]} (gray rows only)", file=sys.stderr); continue
    v = np.fromfile(path, dtype=int, sep=" ")
    if v.size != N * N:
        print(f"# skip {key}: {v.size} values", file=sys.stderr); continue
    img = np.clip(v, 0, 255).astype(np.uint8).reshape(N, N)
    cr0, p0, s0 = prop[key]
    print(f"{key},Proposed,4x4 K=64,{cr0:.2f},{p0:.2f},{s0:.4f}")
    d, cr, q = best_jpeg(img, cr0); r = dec(d)
    print(f"{key},JPEG,quality={q},{cr:.2f},{psnr(img, r):.2f},{ssim(img, r):.4f}")
    d = enc_j2k(img, cr0); r = dec(d)
    print(f"{key},JPEG 2000,target CR={cr0:.2f},{img.size / len(d):.2f},{psnr(img, r):.2f},{ssim(img, r):.4f}")
