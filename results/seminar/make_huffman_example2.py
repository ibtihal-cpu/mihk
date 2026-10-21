import math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from collections import Counter

INK = "#1F1A33"; DEEP = "#2E2055"; MAG = "#E0457B"; TEAL = "#2A9D8F"; BLUE = "#2F6DB5"

# Example taken from the paper "Lossless Recompression of Vector Quantization Index Table for Texture Images
# Based on Adaptive Huffman Coding Through Multi-Type Processing" (Huffman tree example, 21 symbols)
s = "aaaaaaabccccccddeeeee"
cnt = Counter(s)
assert len(s) == 21 and cnt == {"a": 7, "b": 1, "c": 6, "d": 2, "e": 5}
paper = {"a": "11", "b": "000", "c": "10", "d": "001", "e": "01"}
syms = ["a", "b", "c", "d", "e"]
L = {k: len(v) for k, v in paper.items()}
codes = list(paper.values())
assert not any(x != y and y.startswith(x) for x in codes for y in codes)   # prefix-free
bits = sum(cnt[k] * L[k] for k in syms)
avg = bits / 21
H = -sum(cnt[k] / 21 * math.log2(cnt[k] / 21) for k in syms)

# canonical codes with the same lengths: sort by (length, symbol)
order = sorted(syms, key=lambda k: (L[k], k))
canon = {}
c = 0
prev = L[order[0]]
for i, k in enumerate(order):
    if i > 0:
        c = (c + 1) << (L[k] - prev)
    canon[k] = format(c, "0%db" % L[k])
    prev = L[k]
print(dict(cnt), L, canon, "bits", bits, "avg %.3f H %.3f" % (avg, H))

fig, ax = plt.subplots(figsize=(10.5, 5.1), dpi=200)
ax.axis("off"); ax.set_xlim(0, 10.5); ax.set_ylim(-0.9, 6.2)
ax.text(5.25, 5.85, "Input sequence (21 symbols)", ha="center", fontsize=11, color=DEEP, fontweight="bold")
ax.text(5.25, 5.38, s, ha="center", va="center", fontsize=17, family="monospace", color=INK, fontweight="bold")
ax.add_patch(FancyArrowPatch((5.25, 5.05), (5.25, 4.6), arrowstyle="-|>", mutation_scale=22, lw=2.6, color=INK))
cols = ["Symbol", "Frequency", "Code length", "Huffman code\n(tree: left 0, right 1)", "Canonical code\n(same lengths)"]
xs = [1.0, 2.8, 4.6, 6.9, 9.3]
ws = [1.6, 1.6, 1.6, 2.4, 2.0]
cc = [TEAL, TEAL, TEAL, BLUE, MAG]
for x, w, t, col in zip(xs, ws, cols, cc):
    ax.add_patch(FancyBboxPatch((x - w / 2, 3.55), w, 0.85, boxstyle="round,pad=0.02,rounding_size=0.12", fc=col, ec=col))
    ax.text(x, 3.975, t, ha="center", va="center", color="white", fontsize=9.6, fontweight="bold", linespacing=1.15)
for r, k in enumerate(syms):
    y = 3.0 - r * 0.58
    f = "#EAF6F4" if r % 2 == 0 else "white"
    ax.add_patch(FancyBboxPatch((0.05, y - 0.25), 10.4, 0.5, boxstyle="round,pad=0.01,rounding_size=0.08", fc=f, ec="none"))
    vals = [k, str(cnt[k]), str(L[k]), paper[k], canon[k]]
    for i, (x, v) in enumerate(zip(xs, vals)):
        ax.text(x, y, v, ha="center", va="center", fontsize=12.5,
                color=(MAG if i == 4 else BLUE if i == 3 else INK),
                family="monospace" if (i >= 3 or i == 0) else None,
                fontweight="bold" if i >= 3 else "normal")
ax.text(5.25, 0.18, f"Coded size = Σ f·l = {bits} bits   |   L = {bits}/21 = {avg:.2f} bits/symbol   |   H = {H:.2f} bits/symbol   |   H ≤ L < H + 1",
        ha="center", va="center", fontsize=9.6, color=DEEP, fontweight="bold")
ax.text(5.25, -0.4, "Both code sets have the same lengths, so the coded size is identical; the canonical set needs only (symbol, length) pairs in the header.",
        ha="center", va="center", fontsize=8.6, color="#5B6770", style="italic")
plt.savefig("figs/huffman_example.png", bbox_inches="tight", facecolor="white")
