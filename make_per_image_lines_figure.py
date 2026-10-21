#!/usr/bin/env python3
"""One chart per test image (2 x 4 grid) with three lines versus the number of MPI processes P:
   compression ratio, PSNR (dB) and LBG speedup.
CR and PSNR are plotted only at the configurations that were actually verified (sequential = 1, P = 4, P = 14; from correctness.csv),
the speedup at every measured P (timing_final.csv).   usage: python3 make_per_image_lines_figure.py out.png results/final_campaign"""
import csv, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
out, res = sys.argv[1], sys.argv[2]
T = list(csv.DictReader(open(os.path.join(res, "timing_final.csv")))); C = list(csv.DictReader(open(os.path.join(res, "correctness.csv"))))
ORDER = [("gray", "Lena (gray)"), ("boat_img", "Boat"), ("cameraman_img", "Cameraman"), ("peppers_img", "Peppers (gray)"),
         ("lena_color", "Lena (color)"), ("peppers_color2", "Peppers (color)"), ("f16_color", "F16"), ("goldhill_color", "Gold Hill")]
P = [2, 4, 6, 8, 10, 12, 14]
CR_C, PS_C, SP_C = "#2a76d9", "#e08a1e", "#2f9e6b"
plt.rcParams.update({"font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e5e4e0", "grid.linewidth": 0.6})
fig, axs = plt.subplots(2, 4, figsize=(9.8, 5.2), sharex=True, sharey=True)
for ax, (key, label) in zip(axs.flat, ORDER):
    c = [r for r in C if r["image"] == key][0]
    pts = {1: c["seq"], 4: c["par_P4_auto"], 14: c["par_P14_auto"]}
    xs = sorted(pts); cr = [float(pts[x].split()[0]) for x in xs]; ps = [float(pts[x].split()[2]) for x in xs]
    R = {int(r["np"]): r for r in T if r["image"] == key and r["np"] != "seq"}
    sp = [1.0] + [float(R[p]["SpeedupLBG"]) for p in P]
    ax.plot(xs, cr, "o-", color=CR_C, markersize=4.5, linewidth=1.6, label="Compression ratio")
    ax.plot(xs, ps, "s-", color=PS_C, markersize=4.5, linewidth=1.6, label="PSNR (dB)")
    ax.plot([1] + P, sp, "^-", color=SP_C, markersize=4.5, linewidth=1.6, label="LBG speedup")
    ax.set_title(label, fontsize=9, pad=3); ax.set_xticks([1, 2, 4, 6, 8, 10, 12, 14]); ax.set_ylim(0, 35); ax.set_xlim(0.5, 14.8)
for ax in axs[1]: ax.set_xlabel("MPI processes (P)")
for ax in axs[:, 0]: ax.set_ylabel("Value (unit per line)")
h, l = axs[0][0].get_legend_handles_labels()
fig.legend(h, l, loc="upper center", ncol=3, frameon=False, fontsize=8.5, bbox_to_anchor=(0.5, 1.0))
fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig(out, dpi=300); print("saved", out)
