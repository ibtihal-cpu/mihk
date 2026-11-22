#!/usr/bin/env python3
"""Build the 'test images' figure (2 x 4 grid: 4 grayscale on top, 4 color below) from the text image files.

usage:
  python3 make_test_images_figure.py out.png \
      gray:Lena=/path/gray.txt gray:Boat=/path/boat_img.txt gray:Cameraman=/path/cameraman_img.txt gray:Peppers=/path/peppers_img.txt \
      color:Lena=/path/lena_color.txt color:Peppers=/path/peppers_color2.txt color:F16=/path/f16_color.txt "color:Gold Hill=/path/goldhill_color.txt"
Each item is  <gray|color>:<label>=<path>.  Files are the same .txt files read by the LBG programs (512x512).
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

if len(sys.argv) < 3:
    sys.exit(__doc__)
out = sys.argv[1]
items = []
for a in sys.argv[2:]:
    kind, rest = a.split(":", 1); label, path = rest.rsplit("=", 1)
    v = np.fromfile(path, dtype=int, sep=" ")
    if kind == "gray":
        assert v.size == 512 * 512, f"{path}: not a 512x512 grayscale file"; img = v.reshape(512, 512)
    else:
        assert v.size == 512 * 512 * 3, f"{path}: not a 512x512 color file"; img = v.reshape(512, 512, 3)
    items.append((kind, label, np.clip(img, 0, 255).astype(np.uint8)))
gray = [i for i in items if i[0] == "gray"]; color = [i for i in items if i[0] == "color"]
rows = [r for r in (gray, color) if r]
fig, axs = plt.subplots(len(rows), 4, figsize=(7.2, 1.9 * len(rows) + 0.2), squeeze=False)
for r, row in enumerate(rows):
    for c in range(4):
        ax = axs[r][c]; ax.axis("off")
        if c < len(row):
            kind, label, img = row[c]
            ax.imshow(img, cmap="gray" if kind == "gray" else None, vmin=0, vmax=255)
            ax.set_title(label, fontsize=9, pad=3)
fig.tight_layout(pad=0.6); fig.savefig(out, dpi=300); print("saved", out)
