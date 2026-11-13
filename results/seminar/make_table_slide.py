import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

INK = "#1F1A33"; DEEP = "#2E2055"; TEAL = "#2A9D8F"; MAG = "#E0457B"; PURPLE = "#6B4FA3"

# CR / BPP from the real compressed container (code3 / code4, 8 images); MSE, PSNR, SSIM unchanged (identical reconstructions)
rows = [
    ("Lena", "Gray", "23.99", "0.333", "70.13", "29.67", "0.8190", "row"),
    ("Boat", "Gray", "27.18", "0.294", "79.88", "29.11", "0.8394", "row"),
    ("Cameraman", "Gray", "29.60", "0.270", "68.84", "29.75", "0.8855", "row"),
    ("Peppers", "Gray", "25.30", "0.316", "74.47", "29.41", "0.7624", "row"),
    ("Mean (gray)", "Gray", "26.52", "0.304", "73.33", "29.49", "0.8266", "meang"),
    ("Lena", "Color", "24.52", "0.979", "83.60", "28.91", "0.7594", "rowc"),
    ("Peppers", "Color", "24.40", "0.984", "95.00", "28.35", "0.6964", "rowc"),
    ("F16", "Color", "27.07", "0.887", "73.41", "29.47", "0.8539", "rowc"),
    ("Gold Hill", "Color", "24.03", "0.999", "92.97", "28.45", "0.7520", "rowc"),
    ("Mean (color)", "Color", "25.00", "0.962", "86.25", "28.80", "0.7654", "meanc"),
]
heads = ["Image", "Type", "CR", "BPP", "MSE", "PSNR (dB)", "SSIM"]
colx = [2.1, 4.7, 6.7, 8.5, 10.3, 12.2, 14.0]   # centres
colw = [2.8, 1.9, 1.6, 1.6, 1.6, 1.9, 1.7]

fig = plt.figure(figsize=(16, 9), dpi=150)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 16); ax.set_ylim(9, 0); ax.axis("off")
ax.add_patch(FancyBboxPatch((0.5, 0.4), 2.0, 0.6, boxstyle="round,pad=0,rounding_size=0.12", fc=TEAL, ec=TEAL))
ax.text(1.5, 0.7, "Results", ha="center", va="center", color="white", fontsize=17, fontweight="bold")
ax.text(2.75, 0.7, "Compression Results (4 × 4 blocks, K = 64)", ha="left", va="center", color=DEEP, fontsize=26, fontweight="bold", family="DejaVu Serif")
ax.plot([0.5, 15.5], [1.2, 1.2], color=TEAL, lw=3)
# formulas
ax.add_patch(FancyBboxPatch((1.0, 1.4), 14.0, 1.05, boxstyle="round,pad=0,rounding_size=0.1", fc="#FDF1E6", ec="#E07B22", lw=1.8))
ax.text(8.0, 1.72, "CR = S_orig / S_comp          BPP = 8 · S_comp / pixels (gray),   24 · S_comp / pixels (color)", ha="center", va="center", fontsize=14.5, color=DEEP, fontweight="bold")
ax.text(8.0, 2.17, "MSE = (1/MN) Σ [I(i,j) − K(i,j)]²        PSNR = 10·log₁₀(255² / MSE) dB        SSIM: 11 × 11 Gaussian window, σ = 1.5", ha="center", va="center", fontsize=13.2, color=DEEP, fontweight="bold")
# header
y = 2.75
for x, w, h in zip(colx, colw, heads):
    ax.add_patch(FancyBboxPatch((x - w / 2, y), w - 0.06, 0.55, boxstyle="round,pad=0,rounding_size=0.08", fc=TEAL, ec=TEAL))
    ax.text(x - 0.03, y + 0.28, h, ha="center", va="center", color="white", fontsize=14, fontweight="bold")
fills = {"row": "#EAF6F4", "meang": "#CFEAE6", "rowc": "#F1ECF9", "meanc": "#DDD2F0"}
for r, row in enumerate(rows):
    yy = 3.42 + r * 0.46
    kind = row[-1]
    ax.add_patch(FancyBboxPatch((0.9, yy), 14.2, 0.42, boxstyle="round,pad=0,rounding_size=0.05", fc=fills[kind], ec="none"))
    for i, (x, v) in enumerate(zip(colx, row[:-1])):
        bold = kind in ("meang", "meanc") or i in (2, 3)
        ax.text(x - 0.03 if i else 0.9 + 0.2, yy + 0.21, v, ha="left" if i == 0 else "center", va="center",
                fontsize=13.5, color=(MAG if i in (2, 3) else INK), fontweight="bold" if bold else "normal")
ax.text(8.0, 8.2, "Color images: MSE and PSNR are computed over the RGB channels; SSIM is the mean of the channel-wise values. "
        "Means are the means of the per-image values.", ha="center", va="center", fontsize=11, color=PURPLE, style="italic")
ax.text(8.0, 8.6, "CR = original size / size of the compressed container (14-byte header + code table + codebook + Huffman-coded data).",
        ha="center", va="center", fontsize=11, color=PURPLE, style="italic")
fig.savefig("figs/Compression_Results_slide.png", facecolor="white")
