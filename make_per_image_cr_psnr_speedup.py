#!/usr/bin/env python3
"""Per-image table: one row per test image = [thumbnail | CR | PSNR | LBG/total speedup vs P].
CR and PSNR are shown as a bar for the image with a dashed line at the mean of its group (grayscale or color); the speedup panel
shows ideal, LBG and total speedup versus P.   usage: python3 make_per_image_cr_psnr_speedup.py out.png results/final_campaign [key=path.txt ...]"""
import csv, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
out, res = sys.argv[1], sys.argv[2]
paths = dict(a.split("=", 1) for a in sys.argv[3:])
T = list(csv.DictReader(open(os.path.join(res, "timing_final.csv")))); Cc = list(csv.DictReader(open(os.path.join(res, "correctness.csv"))))
ORDER = [("gray", "Lena (gray)"), ("boat_img", "Boat"), ("cameraman_img", "Cameraman"), ("peppers_img", "Peppers (gray)"),
         ("lena_color", "Lena (color)"), ("peppers_color2", "Peppers (color)"), ("f16_color", "F16"), ("goldhill_color", "Gold Hill")]
GRP = {k: ("gray" if i < 4 else "color") for i, (k, _) in enumerate(ORDER)}
P = [2, 4, 6, 8, 10, 12, 14]
cr, ps = {}, {}
for k, _ in ORDER:
    c = [x for x in Cc if x["image"] == k][0]["seq"].split(); cr[k], ps[k] = float(c[0]), float(c[2])
mean = {g: (np.mean([cr[k] for k, _ in ORDER if GRP[k] == g]), np.mean([ps[k] for k, _ in ORDER if GRP[k] == g])) for g in ("gray", "color")}
def load(k):
    p = paths.get(k)
    if not p or not os.path.exists(p): return None
    v = np.fromfile(p, dtype=int, sep=" ")
    return np.clip(v.reshape(512, 512) if v.size == 512 * 512 else v.reshape(512, 512, 3), 0, 255).astype(np.uint8)
plt.rcParams.update({"font.size": 7.5, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e5e4e0", "grid.linewidth": 0.5})
n = len(ORDER)
fig, axs = plt.subplots(n, 4, figsize=(7.4, 1.6 * n + 0.5), gridspec_kw={"width_ratios": [1, 1, 1, 1.9]})
BL, OR, GR = "#2a76d9", "#e08a1e", "#2f9e6b"
for r, (key, label) in enumerate(ORDER):
    a = axs[r][0]; a.grid(False); a.set_xticks([]); a.set_yticks([]); a.set_frame_on(False)
    img = load(key)
    if img is not None: a.imshow(img, cmap="gray" if img.ndim == 2 else None, vmin=0, vmax=255)
    a.set_title(label, fontsize=8, pad=2)
    for col, (v, m, lim, color, ttl) in enumerate(((cr[key], mean[GRP[key]][0], 34, BL, "CR"), (ps[key], mean[GRP[key]][1], 36, OR, "PSNR (dB)")), start=1):
        b = axs[r][col]; b.bar([0], [v], color=color, width=0.55); b.axhline(m, color="#52514e", linestyle="--", linewidth=0.9)
        b.set_ylim(0, lim); b.set_xlim(-0.6, 0.6); b.set_xticks([]); b.text(0, v - lim * 0.03, "{:.2f}".format(v), ha="center", va="top", fontsize=7.5, color="white", fontweight="bold")
        if r == 0: b.set_title(ttl, fontsize=8, pad=4)
    R = {int(x["np"]): x for x in T if x["image"] == key and x["np"] != "seq"}
    d = axs[r][3]
    d.plot([2, 14], [2, 14], ":", color="#52514e", linewidth=1, label="Ideal")
    d.plot(P, [float(R[p]["SpeedupLBG"]) for p in P], "o-", color=GR, markersize=3.5, linewidth=1.4, label="LBG")
    d.plot(P, [float(R[p]["SpeedupTotal"]) for p in P], "s--", color="#8a5cc9", markersize=3.5, linewidth=1.4, label="Total")
    d.set_ylim(0, 15); d.set_xticks(P)
    if r == 0:
        d.set_title("Speedup vs P", fontsize=8, pad=4); d.legend(frameon=False, fontsize=6.5, loc="lower right")
    if r != n - 1: d.set_xticklabels([])
    else: d.set_xlabel("MPI processes (P)")
fig.text(0.5, 0.003, "Dashed line in the CR and PSNR panels = mean of the image's group (four grayscale or four color images).", ha="center", fontsize=7)
fig.tight_layout(h_pad=0.5, rect=(0, 0.012, 1, 1)); fig.savefig(out, dpi=300); print("saved", out)
