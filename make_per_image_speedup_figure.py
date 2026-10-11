#!/usr/bin/env python3
"""One small chart per test image (2 x 4 grid): ideal speedup, LBG speedup, and total-time speedup versus the number of MPI processes.
usage: python3 make_per_image_speedup_figure.py out.png results/final_campaign   (reads timing_final.csv)"""
import csv, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
out, res = sys.argv[1], sys.argv[2]
T = list(csv.DictReader(open(os.path.join(res, "timing_final.csv"))))
ORDER = [("gray", "Lena (gray)"), ("boat_img", "Boat"), ("cameraman_img", "Cameraman"), ("peppers_img", "Peppers (gray)"),
         ("lena_color", "Lena (color)"), ("peppers_color2", "Peppers (color)"), ("f16_color", "F16"), ("goldhill_color", "Gold Hill")]
P = [2, 4, 6, 8, 10, 12, 14]
plt.rcParams.update({"font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": "#e5e4e0", "grid.linewidth": 0.6})
fig, axs = plt.subplots(2, 4, figsize=(9.6, 5.0), sharex=True, sharey=True)
for ax, (key, label) in zip(axs.flat, ORDER):
    R = {int(r["np"]): r for r in T if r["image"] == key and r["np"] != "seq"}
    ax.axvspan(1.5, 6.5, color="#f0efec", linewidth=0)
    ax.plot([2, 14], [2, 14], ":", color="#52514e", linewidth=1.1, label="Ideal")
    ax.plot(P, [float(R[p]["SpeedupLBG"]) for p in P], "o-", color="#2a76d9", markersize=4, linewidth=1.6, label="LBG speedup")
    ax.plot(P, [float(R[p]["SpeedupTotal"]) for p in P], "s--", color="#e08a1e", markersize=4, linewidth=1.6, label="Total speedup")
    ax.set_title(label, fontsize=9, pad=3); ax.set_xticks(P); ax.set_ylim(0, 15); ax.set_xlim(1.5, 14.5)
for ax in axs[1]: ax.set_xlabel("MPI processes (P)")
for ax in axs[:, 0]: ax.set_ylabel("Speedup")
h, l = axs[0][0].get_legend_handles_labels()
fig.legend(h, l, loc="upper center", ncol=3, frameon=False, fontsize=8.5, bbox_to_anchor=(0.5, 1.0))
fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig(out, dpi=300); print("saved", out)
