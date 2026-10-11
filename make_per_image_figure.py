#!/usr/bin/env python3
"""Per-image summary: one row per test image = [thumbnail | one chart with three bars: CR, PSNR, LBG speedup (P = 14)].

usage (from the repo root; add --lollipop for line-and-dot style instead of bars):
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
LOLLI = "--lollipop" in sys.argv
paths = dict(a.split("=", 1) for a in sys.argv[3:] if not a.startswith("--"))
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

COLS = {"CR": "#2a76d9", "PSNR (dB)": "#e08a1e", "Speedup (P = 14)": "#2f9e6b"}
plt.rcParams.update({"font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False})
n = len(rows)
fig, axs = plt.subplots(n, 2, figsize=(6.4, 1.08 * n + 0.5), gridspec_kw={"width_ratios": [1, 3.4]})
for r, (key, label, cr, psnr, sp, color) in enumerate(rows):
    a = axs[r][0]; a.set_xticks([]); a.set_yticks([]); a.set_frame_on(False)
    img = load(key)
    if img is not None:
        a.imshow(img, cmap=None if img.ndim == 3 else "gray", vmin=0, vmax=255)
    a.set_title(label, fontsize=8.5, pad=2)
    b = axs[r][1]
    vals = [cr, psnr, sp]
    if LOLLI:   # thin line from zero to a dot instead of a filled bar
        for i, (v, c) in enumerate(zip(vals, COLS.values())):
            b.hlines(i, 0, v, color=c, linewidth=2.2); b.plot([v], [i], "o", color=c, markersize=7, zorder=3)
    else:
        b.barh(range(3), vals, color=list(COLS.values()), height=0.7)
    b.set_yticks(range(3)); b.set_yticklabels(list(COLS.keys()), fontsize=7.5); b.invert_yaxis()
    b.set_xlim(0, 36)
    for i, v in enumerate(vals):
        b.text(v + (1.1 if LOLLI else 0.5), i, "{:.2f}".format(v), va="center", fontsize=7.5)
    b.grid(axis="x", color="#e5e4e0", linewidth=0.6); b.set_axisbelow(True)
    if r != n - 1:
        b.set_xticklabels([])
fig.tight_layout(h_pad=0.4)
fig.savefig(out, dpi=300); print("saved", out)
