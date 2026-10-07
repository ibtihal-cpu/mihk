#!/usr/bin/env python3
"""Rate-matched comparison of the proposed codec with JPEG and JPEG 2000 (8 grayscale images).

Each baseline is encoded at (approximately) the SAME compression ratio as the proposed codec; PSNR and SSIM are
then computed with exactly the formulas of sem_v3.c:
  PSNR = 10 log10(255^2 / MSE);  SSIM = 11x11 Gaussian window (sigma 1.5), K1=0.01, K2=0.03,
  mean over the valid region (same as SSIM_window_based()).
CR of the baselines = W*H bytes / size of the COMPLETE encoded file (headers included).
CR of the proposed codec = "System total" of sem_v3 (final campaign values below).

usage:  python3 run_baselines.py [IMG_DIR] > baselines.csv        (default IMG_DIR = $HOME)
Needs numpy and Pillow with JPEG 2000 support. Images are the same .txt files used by the C programs.
"""
import io, os, sys
import numpy as np
from PIL import Image

D = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~")
IMAGES = [  # name, txt path, proposed codec (final): CR_system, PSNR, SSIM
    ("Lena",        "lbg_exp/gray.txt",    23.50, 30.44, 0.8431),
    ("Boat",        "boat_img.txt",        26.54, 29.65, 0.8522),
    ("Cameraman",   "cameraman_img.txt",   28.88, 30.60, 0.9031),
    ("Peppers",     "peppers_img.txt",     24.75, 30.24, 0.7875),
    ("Chest_X-ray", "chest_xray2_img.txt", 23.39, 34.14, 0.8890),
    ("Mammogram",   "mammo2_img.txt",      31.56, 36.73, 0.9392),
    ("Lung_CT",     "lung_ct2_img.txt",    24.63, 28.90, 0.8666),
    ("Brain_MRI",   "brain_mri2_img.txt",  33.49, 34.50, 0.9474),
]
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

print("image,method,setting,CR,PSNR_dB,SSIM")
for name, rel, cr0, p0, s0 in IMAGES:
    path = os.path.join(D, rel)
    if not os.path.isfile(path):
        print(f"# skip {name}: {path} not found", file=sys.stderr); continue
    v = np.fromfile(path, dtype=int, sep=" ")
    if v.size != N * N:
        print(f"# skip {name}: {v.size} values", file=sys.stderr); continue
    img = np.clip(v, 0, 255).astype(np.uint8).reshape(N, N)
    print(f"{name},Proposed,4x4 K=64,{cr0:.2f},{p0:.2f},{s0:.4f}")
    d, cr, q = best_jpeg(img, cr0); r = dec(d)
    print(f"{name},JPEG,quality={q},{cr:.2f},{psnr(img, r):.2f},{ssim(img, r):.4f}")
    d = enc_j2k(img, cr0); r = dec(d)
    print(f"{name},JPEG 2000,target CR={cr0:.2f},{img.size / len(d):.2f},{psnr(img, r):.2f},{ssim(img, r):.4f}")
