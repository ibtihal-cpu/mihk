import textwrap
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

INK = "#1F1A33"
cards = [
    ("Hardware", "#6B4FA3", "Intel Core i7-13650HX: 6 P-cores and 8 E-cores (14 cores in total)."),
    ("Software", "#E07B22", "Ubuntu 24.04, GCC 13.3 (-O2), Open MPI 4.1.6, written in\u00a0C."),
    ("Protocol", "#2A9D8F", "Median of 5 runs; AC power, governor set to performance; MPI processes bound to cores (P-cores first); sequential baseline pinned to one P-core."),
    ("Data", "#E0457B", "8 standard 512 × 512 images: 4 grayscale and 4 color."),
    ("LBG settings", "#2E2055", "4 × 4 blocks, K = 64 codewords, δ = 0.01, ε = 0.0001 (relative improvement in distortion), at most 100 iterations per level."),
    ("Strategies", "#F2B134", "Equal (P\u00a0≤\u00a06, P-cores only) and Adaptive speed-aware (P\u00a0>\u00a06, P- and E-cores)."),
]


def draw(full, path):
    W, H = (16, 9) if full else (16, 7.4)
    fig = plt.figure(figsize=(W, H), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis("off")
    top = 0.0
    if full:
        ax.add_patch(FancyBboxPatch((0.25, 0.45), 3.85, 0.9, boxstyle="round,pad=0,rounding_size=0.18", fc="#2A9D8F", ec="#2A9D8F"))
        ax.text(0.45, 0.9, "Experimental Results", ha="left", va="center", fontsize=17, fontweight="bold", color="white", family="DejaVu Sans")
        ax.text(4.75, 0.9, "Experimental Setup", ha="left", va="center", fontsize=30, fontweight="bold", color="#FF0000", family="DejaVu Serif")
        top = 1.7
    cw, ch, gx, gy = 7.4, 2.15, 0.35, 0.3
    x0 = 0.4
    y0 = top + (0.0 if full else 0.15)
    for i, (title, col, body) in enumerate(cards):
        r, c = divmod(i, 2)
        x = x0 + c * (cw + gx); y = y0 + r * (ch + gy)
        ax.add_patch(FancyBboxPatch((x, y), cw, ch, boxstyle="round,pad=0,rounding_size=0.12", fc="white", ec=col, lw=2.4))
        ax.add_patch(Rectangle((x, y + 0.02), 0.17, ch - 0.04, fc=col, ec="none"))
        ax.text(x + 0.45, y + 0.5, title, ha="left", va="center", fontsize=21, fontweight="bold", color=col)
        ax.text(x + 0.45, y + 0.95, "\n".join(textwrap.wrap(body, 58)), ha="left", va="top", fontsize=15.5, color=INK, linespacing=1.4)
    fig.savefig(path, facecolor="white")


draw(True, "figs/Experimental_Setup_slide.png")
draw(False, "figs/Experimental_Setup_cards.png")
