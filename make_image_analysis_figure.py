#!/usr/bin/env python3
"""Image-analysis table: one row per test image = [thumbnail | adjacent-pixel scatter x(t) vs x(t+1) | histogram (PDF)].
Adjacent pixels are horizontal neighbours; 4000 random pairs per image (fixed seed). Color images are analysed on their luminance
(0.299 R + 0.587 G + 0.114 B). The correlation coefficient of the plotted pairs is written in the scatter panel.
usage: python3 make_image_analysis_figure.py out.png label=path.txt [label=path.txt ...]     (e.g. "Lena (gray)=gray.txt")
Each .txt is the file read by the LBG programs: 512x512 values (gray) or 512x512x3 values (color)."""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
out = sys.argv[1]
items = []
for a in sys.argv[2:]:
    label, path = a.rsplit("=", 1)
    v = np.fromfile(path, dtype=int, sep=" ")
    img = np.clip(v.reshape(512, 512) if v.size == 512 * 512 else v.reshape(512, 512, 3), 0, 255).astype(np.uint8)
    g = img.astype(float) if img.ndim == 2 else (img[..., 0] * 0.299 + img[..., 1] * 0.587 + img[..., 2] * 0.114)
    items.append((label, img, np.rint(g).astype(int)))
rng = np.random.default_rng(1)
n = len(items)
plt.rcParams.update({"font.size": 7.5, "axes.spines.top": False, "axes.spines.right": False})
fig, axs = plt.subplots(n, 3, figsize=(6.4, 1.9 * n), squeeze=False, gridspec_kw={"width_ratios": [1, 1.15, 1.25]})
for r, (label, img, g) in enumerate(items):
    a = axs[r][0]; a.imshow(img, cmap="gray" if img.ndim == 2 else None, vmin=0, vmax=255); a.set_xticks([]); a.set_yticks([]); a.set_ylabel(label, fontsize=8)
    i = rng.integers(0, 512, 4000); j = rng.integers(0, 511, 4000)
    x, y = g[i, j], g[i, j + 1]; rho = np.corrcoef(x, y)[0, 1]
    b = axs[r][1]; b.scatter(x, y, s=2, color="#1b8a8a", linewidths=0); b.set_xlim(0, 255); b.set_ylim(0, 255); b.grid(color="#e5e4e0", linewidth=.5)
    b.set_xlabel("x(t)"); b.set_ylabel("x(t+1)"); b.text(8, 232, "r = {:.3f}".format(rho), fontsize=8)
    c = axs[r][2]; h = np.bincount(g.ravel(), minlength=256) / g.size
    c.plot(np.arange(256), h, color="#2a76d9", linewidth=0.9); c.axhline(1 / 256, color="#d94b4b", linewidth=0.8)
    c.set_xlim(0, 255); c.set_xlabel("Pixel value"); c.set_ylabel("PDF"); c.grid(color="#e5e4e0", linewidth=.5)
fig.tight_layout(); fig.savefig(out, dpi=300); print("saved", out)
