import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch

INK = "#1F1A33"; DEEP = "#2E2055"; MAG = "#E0457B"; TEAL = "#2A9D8F"; BLUE = "#2F6DB5"; PUR = "#6B4FA3"; ORG = "#E07B22"

# Huffman tree of the example (same shape as the example of the cited paper, delta symbols of this work)
# merges: 130(1)+126(2)=3 ; 3+129(5)=8 ; 127(6)+128(7)=13 ; 8+13=21      left branch = 0, right branch = 1
nodes = {
    "root": (5.0, 5.2, "21", PUR),
    "n8": (2.5, 3.9, "8", BLUE), "n13": (7.5, 3.9, "13", BLUE),
    "n3": (1.3, 2.6, "3", BLUE),
    "l129": (3.7, 2.6, "5", TEAL), "l127": (6.5, 2.6, "6", TEAL), "l128": (8.5, 2.6, "7", TEAL),
    "l130": (0.6, 1.3, "1", TEAL), "l126": (2.0, 1.3, "2", TEAL),
}
edges = [("root", "n8", "0"), ("root", "n13", "1"), ("n8", "n3", "0"), ("n8", "l129", "1"),
         ("n13", "l127", "0"), ("n13", "l128", "1"), ("n3", "l130", "0"), ("n3", "l126", "1")]
leaf = {"l130": ("130", "000"), "l126": ("126", "001"), "l129": ("129", "01"), "l127": ("127", "10"), "l128": ("128", "11")}

fig, ax = plt.subplots(figsize=(9.5, 5.6), dpi=200)
ax.set_xlim(0, 10); ax.set_ylim(-0.3, 6.2); ax.set_aspect("equal"); ax.axis("off")
for a, b, lab in edges:
    xa, ya = nodes[a][:2]; xb, yb = nodes[b][:2]
    ax.plot([xa, xb], [ya - 0.22, yb + 0.22], color="#7F8FA9", lw=2.4, zorder=1)
    ax.text((xa + xb) / 2 + (-0.17 if lab == "0" else 0.17), (ya + yb) / 2 + 0.08, lab, ha="center", va="center",
            fontsize=13, fontweight="bold", color=MAG,
            bbox=dict(boxstyle="circle,pad=0.12", fc="white", ec="none"))
for k, (x, y, t, col) in nodes.items():
    ax.add_patch(Circle((x, y), 0.32, fc=col, ec="white", lw=2, zorder=3))
    ax.text(x, y, t, ha="center", va="center", color="white", fontsize=13, fontweight="bold", zorder=4)
for k, (sym, code) in leaf.items():
    x, y = nodes[k][:2]
    ax.add_patch(FancyBboxPatch((x - 0.52, y - 1.35), 1.04, 0.95, boxstyle="round,pad=0.02,rounding_size=0.1", fc="white", ec=TEAL, lw=1.8, zorder=2))
    ax.text(x, y - 0.72, sym, ha="center", va="center", fontsize=12.5, fontweight="bold", color=INK, family="monospace")
    ax.text(x, y - 1.08, code, ha="center", va="center", fontsize=12.5, fontweight="bold", color=BLUE, family="monospace")
ax.text(9.9, 0.1, "leaf box: symbol D (black) and its Huffman code (blue)", ha="right", va="center", fontsize=8.8, color="#5B6770", style="italic")
ax.text(5.0, 6.0, "Huffman tree: node value = sum of the frequencies below it (left branch 0, right branch 1)",
        ha="center", va="center", fontsize=10, color=DEEP, fontweight="bold")
plt.savefig("figs/huffman_tree.png", bbox_inches="tight", facecolor="white")
