#!/usr/bin/env python3
"""Per-image summary: one row per test image = [thumbnail | CR bar | PSNR bar | LBG-speedup bar].

usage (from the repo root):
  python3 make_per_image_figure.py out.png results/final_campaign \
      gray=/path/gray.txt boat_img=/path/boat_img.txt cameraman_img=/path/cameraman_img.txt peppers_img=/path/peppers_img.txt \
      lena_color=/path/lena_color.txt peppers_color2=/path/peppers_color2.txt f16_color=/path/f16_color.txt goldhill_color=/path/goldhill_color.txt
The .txt files are the same files read by the LBG programs (512x512; 1 value/pixel gray, "R G B"/pixel color).
CR and PSNR come from correctness.csv (sequential column), the speedup from timing_final.csv (P = 14, LBG).
An image whose path is missing is drawn as an empty box (the numbers are still plotted).
"""
import csv, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

if len(sys.argv) < 4:
    sys.exit(__doc__)
out, res = sys.argv[1], sys.argv[2]
paths = dict(a.split("=", 1) for a in sys.argv[3:])
ORDER = [("gray", "Lena (gray)"), ("boat_img", "Boat"), ("cameraman_img", "Cameraman"), ("peppers_img", "Peppers (gray)"),
         ("lena_color", "Lena (color)"), ("peppers_color2", "Peppers (color)"), ("f16_color", "F16"), ("goldhill_color", "Gold Hill")]
cor = list(csv.DictReader(open(os.path.join(res, "correctness.csv"))))
tim = list(csv.DictReader(open(os.path.join(res, "timing_final.csv"))))

def load(key):
    p = paths.get(key)
    if not p or not os.path.exists(p):
        return None
    v = np.fromfile(p, dtype=int, sep=" ")
    img = v.reshape(512, 512) if v.size == 512 * 512 else v.reshape(512, 512, 3)
    return np.clip(img, 0, 255).astype(np.uint8)

rows = []
for key, label in ORDER:
    cr, mse, psnr, ssim, it = [r for r in cor if r["image"] == key][0]["seq"].split()
    sp = [r for r in tim if r["image"] == key and r["np"] == "14"][0]["SpeedupLBG"]
    rows.append((key, label, float(cr), float(psnr), float(sp), key in ("lena_color", "peppers_color2", "f16_color", "goldhill_color")))

BL, OR = "#2a76d9", "#d95f2b"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False})
fig, axs = plt.subplots(len(rows), 4, figsize=(8.2, 0.78 * len(rows) + 0.7), gridspec_kw={"width_ratios": [1.15, 3, 3, 3]})
heads = ["Image", "Compression ratio", "PSNR (dB)", "LBG speedup (P = 14)"]
xmax = [34, 36, 11.5]
for r, (key, label, cr, psnr, sp, color) in enumerate(rows):
    a = axs[r][0]; a.set_xticks([]); a.set_yticks([])
    for s in a.spines.values():
        s.set_visible(False)
    img = load(key)
    if img is not None:
        a.imshow(img, cmap=None if img.ndim == 3 else "gray", vmin=0, vmax=255)
    a.set_ylabel(label, rotation=0, ha="right", va="center", fontsize=8.5, labelpad=4)
    a.set_frame_on(False)
    for c, (v, fmt) in enumerate(((cr, "{:.2f}"), (psnr, "{:.2f}"), (sp, "{:.2f}")), start=1):
        b = axs[r][c]
        b.barh([0], [v], color=OR if color else BL, height=0.62)
        b.set_xlim(0, xmax[c - 1]); b.set_ylim(-0.5, 0.5); b.set_yticks([])
        b.text(v + xmax[c - 1] * 0.015, 0, fmt.format(v), va="center", fontsize=8)
        b.spines["bottom"].set_visible(r == len(rows) - 1)
        if r != len(rows) - 1:
            b.set_xticks([])
        b.grid(axis="x", color="#e5e4e0", linewidth=0.6); b.set_axisbelow(True)
for c in range(1, 4):
    axs[0][c].set_title(heads[c], fontsize=9, pad=6)
h = [plt.Rectangle((0, 0), 1, 1, color=BL), plt.Rectangle((0, 0), 1, 1, color=OR)]
fig.legend(h, ["Grayscale", "Color"], loc="lower center", ncol=2, frameon=False, fontsize=8.5, bbox_to_anchor=(0.6, -0.005))
fig.tight_layout(rect=(0, 0.03, 1, 1), h_pad=0.25)
fig.savefig(out, dpi=300); print("saved", out)
