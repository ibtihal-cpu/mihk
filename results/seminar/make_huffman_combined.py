import math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch

INK = "#1F1A33"; DEEP = "#2E2055"; MAG = "#E0457B"; TEAL = "#2A9D8F"; BLUE = "#2F6DB5"; PUR = "#6B4FA3"; ORG = "#2A9D8F"; YEL = "white"

# Example with the structure of the example of the cited paper (frequencies 7, 6, 5, 2, 1) and the delta symbols of this work
freq = {126: 2, 127: 6, 128: 7, 129: 5, 130: 1}
tree_code = {128: "11", 127: "10", 129: "01", 126: "001", 130: "000"}
syms = sorted(freq); N = 21
L = {s: len(tree_code[s]) for s in syms}
bits = sum(freq[s] * L[s] for s in syms); avg = bits / N
H = -sum(freq[s] / N * math.log2(freq[s] / N) for s in syms)
order = sorted(syms, key=lambda s: (L[s], s)); canon = {}; c = 0; prev = L[order[0]]
for i, s in enumerate(order):
    if i > 0: c = (c + 1) << (L[s] - prev)
    canon[s] = format(c, "0%db" % L[s]); prev = L[s]

fig, ax = plt.subplots(figsize=(13.33, 6.4), dpi=200)
ax.set_xlim(0, 20); ax.set_ylim(-0.6, 8.6); ax.set_aspect("equal"); ax.axis("off")

# ---------------- left: sequence + table ----------------
ax.text(4.85, 8.25, "Delta-coded indices D (21 symbols)", ha="center", va="center", fontsize=14, color=DEEP, fontweight="bold")
ax.text(4.85, 7.55, "128 ×7,  127 ×6,  129 ×5,  126 ×2,  130 ×1", ha="center", va="center", fontsize=14, family="monospace", color=INK, fontweight="bold")
ax.add_patch(FancyArrowPatch((4.85, 7.15), (4.85, 6.6), arrowstyle="-|>", mutation_scale=26, lw=3, color=INK))
cols = ["Symbol\n(D)", "Frequency", "Huffman\ncode", "Canonical\ncode"]
xs = [1.2, 3.45, 5.7, 7.95]; ws = [1.9, 2.4, 2.1, 2.1]; cc = [TEAL, TEAL, BLUE, MAG]
for x, w, t, col in zip(xs, ws, cols, cc):
    ax.add_patch(FancyBboxPatch((x - w / 2, 5.55), w, 0.95, boxstyle="round,pad=0.02,rounding_size=0.15", fc=col, ec=col))
    ax.text(x, 6.025, t, ha="center", va="center", color="white", fontsize=12.5, fontweight="bold", linespacing=1.1)
for r, s in enumerate(syms):
    y = 4.85 - r * 0.8
    ax.add_patch(FancyBboxPatch((0.1, y - 0.35), 9.5, 0.7, boxstyle="round,pad=0.01,rounding_size=0.1",
                                fc="#E1F2EF" if r % 2 == 0 else "white", ec="none"))
    vals = [str(s), str(freq[s]), tree_code[s], canon[s]]
    for i, (x, v) in enumerate(zip(xs, vals)):
        ax.text(x, y, v, ha="center", va="center", fontsize=16, family="monospace" if i != 1 else None,
                color=(MAG if i == 3 else BLUE if i == 2 else INK), fontweight="bold" if i >= 2 else "normal")

# ---------------- right: tree ----------------
ox, oy, sx, sy = 10.4, 0.2, 0.93, 1.0   # offset and scale of the tree coordinates
nodes = {
    "root": (5.0, 7.0, "21", PUR), "n8": (2.5, 5.55, "8", BLUE), "n13": (7.5, 5.55, "13", BLUE),
    "n3": (1.3, 4.1, "3", BLUE), "l129": (3.7, 4.1, "5", ORG), "l127": (6.5, 4.1, "6", ORG), "l128": (8.5, 4.1, "7", ORG),
    "l130": (0.45, 2.65, "1", ORG), "l126": (2.15, 2.65, "2", ORG),
}
edges = [("root", "n8", "0"), ("root", "n13", "1"), ("n8", "n3", "0"), ("n8", "l129", "1"),
         ("n13", "l127", "0"), ("n13", "l128", "1"), ("n3", "l130", "0"), ("n3", "l126", "1")]
leaf = {"l130": 130, "l126": 126, "l129": 129, "l127": 127, "l128": 128}
P = lambda x, y: (ox + x * sx, oy + y * sy - 0.4)
ax.text(ox + 4.65, 8.25, "Huffman tree (left branch 0, right branch 1)", ha="center", va="center", fontsize=14, color=DEEP, fontweight="bold")
for a, b, lab in edges:
    xa, ya = P(*nodes[a][:2]); xb, yb = P(*nodes[b][:2])
    ax.plot([xa, xb], [ya - 0.3, yb + 0.3], color="#7F8FA9", lw=3, zorder=1)
    ax.text((xa + xb) / 2 + (-0.28 if lab == "0" else 0.28), (ya + yb) / 2 + 0.1, lab, ha="center", va="center",
            fontsize=15, fontweight="bold", color=MAG, bbox=dict(boxstyle="circle,pad=0.1", fc="white", ec="none"))
for k, (x, y, t, col) in nodes.items():
    px, py = P(x, y)
    ax.add_patch(Circle((px, py), 0.42, fc=col, ec="white", lw=2, zorder=3))
    ax.text(px, py, t, ha="center", va="center", color="white", fontsize=15, fontweight="bold", zorder=4)
for k, s in leaf.items():
    px, py = P(*nodes[k][:2])
    ax.add_patch(FancyBboxPatch((px - 0.62, py - 1.45), 1.24, 0.95, boxstyle="round,pad=0.02,rounding_size=0.12", fc=YEL, ec=TEAL, lw=2.2, zorder=2))
    ax.text(px, py - 0.82, str(s), ha="center", va="center", fontsize=14.5, fontweight="bold", color=INK, family="monospace")
    ax.text(px, py - 1.17, tree_code[s], ha="center", va="center", fontsize=14.5, fontweight="bold", color=BLUE, family="monospace")

ax.add_patch(FancyArrowPatch((9.75, 3.0), (10.2, 3.0), arrowstyle="-|>", mutation_scale=1, lw=0))
ax.text(10.0, 0.45, f"Coded size = Σ f·l = {bits} bits (fixed 3-bit code: {3 * N} bits)    L = {avg:.2f} bits/symbol    H = {H:.2f} bits/symbol",
        ha="center", va="center", fontsize=12.5, color=DEEP, fontweight="bold")
ax.text(10.0, -0.05, "Illustrative example: same structure as the example in [ref], with the delta symbols of this work. Canonical codes have the same lengths and need only (symbol, length) in the header.",
        ha="center", va="center", fontsize=9.2, color="#5B6770", style="italic")
plt.savefig("figs/huffman_example_tree.png", bbox_inches="tight", facecolor="white")
