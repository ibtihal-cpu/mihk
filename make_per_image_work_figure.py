#!/usr/bin/env python3
"""Per-image results table built only from this work's measurements: one row per test image =
   [thumbnail (+ CR and PSNR) | speedup vs P (ideal, LBG, total) | LBG time vs P (Equal vs Adaptive)].
usage: python3 make_per_image_work_figure.py out.png results/final_campaign [key=path.txt ...]   (txt paths optional; empty box if missing)"""
import csv, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
out, res = sys.argv[1], sys.argv[2]
paths = dict(a.split("=", 1) for a in sys.argv[3:])
T = list(csv.DictReader(open(os.path.join(res, "timing_final.csv")))); E = list(csv.DictReader(open(os.path.join(res, "eq_ad_total.csv"))))
Cc = list(csv.DictReader(open(os.path.join(res, "correctness.csv"))))
ORDER = [("gray", "Lena (gray)"), ("boat_img", "Boat"), ("cameraman_img", "Cameraman"), ("peppers_img", "Peppers (gray)"),
         ("lena_color", "Lena (color)"), ("peppers_color2", "Peppers (color)"), ("f16_color", "F16"), ("goldhill_color", "Gold Hill")]
P = [2, 4, 6, 8, 10, 12, 14]
def load(k):
    p = paths.get(k)
    if not p or not os.path.exists(p): return None
    v = np.fromfile(p, dtype=int, sep=" ")
    return np.clip(v.reshape(512, 512) if v.size == 512 * 512 else v.reshape(512, 512, 3), 0, 255).astype(np.uint8)
plt.rcParams.update({"font.size": 7.5, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e5e4e0", "grid.linewidth": 0.5})
n = len(ORDER)
fig, axs = plt.subplots(n, 3, figsize=(7.0, 1.75 * n + 0.4), gridspec_kw={"width_ratios": [1, 1.5, 1.5]})
for r, (key, label) in enumerate(ORDER):
    a = axs[r][0]; a.grid(False); a.set_xticks([]); a.set_yticks([]); a.set_frame_on(False)
    img = load(key)
    if img is not None: a.imshow(img, cmap="gray" if img.ndim == 2 else None, vmin=0, vmax=255)
    c = [x for x in Cc if x["image"] == key][0]["seq"].split()
    a.set_title(label + "\nCR " + c[0] + " | PSNR " + c[2] + " dB", fontsize=7.5, pad=2)
    R = {int(x["np"]): x for x in T if x["image"] == key and x["np"] != "seq"}
    b = axs[r][1]
    b.plot([2, 14], [2, 14], ":", color="#52514e", linewidth=1, label="Ideal")
    b.plot(P, [float(R[p]["SpeedupLBG"]) for p in P], "o-", color="#2a76d9", markersize=3.5, linewidth=1.4, label="LBG")
    b.plot(P, [float(R[p]["SpeedupTotal"]) for p in P], "s--", color="#e08a1e", markersize=3.5, linewidth=1.4, label="Total")
    b.set_ylim(0, 15); b.set_xticks(P); b.set_ylabel("Speedup")
    D = {int(x["np"]): x for x in E if x["image"] == key}
    d = axs[r][2]
    d.plot(P, [float(D[p]["eq_lbg"]) for p in P], "o--", color="#8a8a86", markersize=3.5, linewidth=1.3, label="Equal")
    d.plot(P, [float(D[p]["ad_lbg"]) for p in P], "o-", color="#d95f2b", markersize=3.5, linewidth=1.4, label="Adaptive")
    d.set_xticks(P); d.set_ylim(bottom=0); d.set_ylabel("LBG time (s)")
    if r == 0:
        b.set_title("Speedup vs P", fontsize=8, pad=4); d.set_title("LBG time: Equal vs Adaptive", fontsize=8, pad=4)
        b.legend(frameon=False, fontsize=6.5, loc="lower right"); d.legend(frameon=False, fontsize=6.5, loc="upper right")
    if r != n - 1:
        b.set_xticklabels([]); d.set_xticklabels([])
    else:
        b.set_xlabel("MPI processes (P)"); d.set_xlabel("MPI processes (P)")
fig.tight_layout(h_pad=0.5); fig.savefig(out, dpi=300); print("saved", out)
