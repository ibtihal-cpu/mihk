#!/usr/bin/env python3
"""Per-image parameter study (four grayscale images): one row per image = [thumbnail | CR | PSNR | sequential LBG time] for the five tested
configurations (2x2/K64, 4x4/K32, 4x4/K64, 4x4/K128, 8x8/K64). The selected configuration (4x4, K=64) is highlighted.
usage: python3 make_per_image_config_figure.py out.png results/final_campaign [key=path.txt ...]   (keys: gray boat_img cameraman_img peppers_img)"""
import csv, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
out, res = sys.argv[1], sys.argv[2]
paths = dict(a.split("=", 1) for a in sys.argv[3:])
P = list(csv.DictReader(open(os.path.join(res, "param_study_nf.csv"))))
ORDER = [("gray", "Lena (gray)"), ("boat_img", "Boat"), ("cameraman_img", "Cameraman"), ("peppers_img", "Peppers (gray)")]
CONF = ["2x2/K64", "4x4/K32", "4x4/K64", "4x4/K128", "8x8/K64"]
def load(k):
    p = paths.get(k)
    if not p or not os.path.exists(p): return None
    v = np.fromfile(p, dtype=int, sep=" ")
    return np.clip(v.reshape(512, 512), 0, 255).astype(np.uint8)
plt.rcParams.update({"font.size": 7.5, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e5e4e0", "grid.linewidth": 0.5, "axes.axisbelow": True})
n = len(ORDER)
fig, axs = plt.subplots(n, 4, figsize=(7.4, 1.75 * n + 0.6), gridspec_kw={"width_ratios": [1, 1.3, 1.3, 1.3]})
SEL, OTH = "#d95f2b", "#2a76d9"
cols = [SEL if c == "4x4/K64" else OTH for c in CONF]
for r, (key, label) in enumerate(ORDER):
    a = axs[r][0]; a.grid(False); a.set_xticks([]); a.set_yticks([]); a.set_frame_on(False)
    img = load(key)
    if img is not None: a.imshow(img, cmap="gray", vmin=0, vmax=255)
    a.set_title(label, fontsize=8, pad=2)
    R = {x["variant"]: x for x in P if x["image"] == key}
    for col, (fld, ttl, fmt) in enumerate((("system_CR", "CR", "{:.1f}"), ("PSNR_dB", "PSNR (dB)", "{:.1f}"), ("LBG_time_median_s", "LBG time (s)", "{:.2f}")), start=1):
        v = [float(R[c][fld]) for c in CONF]; b = axs[r][col]
        b.bar(range(5), v, color=cols, width=0.7); b.set_ylim(0, max(v) * 1.18)
        for i, x in enumerate(v): b.text(i, x + max(v) * 0.02, fmt.format(x), ha="center", fontsize=6.3)
        b.set_xticks(range(5)); b.grid(axis="x", visible=False)
        if r == 0: b.set_title(ttl, fontsize=8, pad=4)
        if r == n - 1: b.set_xticklabels(CONF, rotation=45, ha="right", fontsize=6.5)
        else: b.set_xticklabels([])
fig.text(0.5, 0.004, "Orange = selected configuration (4 x 4 blocks, K = 64). Times are sequential LBG times (median of runs).", ha="center", fontsize=7)
fig.tight_layout(h_pad=0.6, rect=(0, 0.015, 1, 1)); fig.savefig(out, dpi=300); print("saved", out)
