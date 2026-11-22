#!/usr/bin/env python3
"""Figure 3.1: general framework (same structure as the seminar figure; Rank -> Process, code-length table)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

BLUE = ('#DCEBFA', '#2F6DB5'); GREEN = ('#E3F1DB', '#3F7F2A'); ORANGE = ('#FDEBDD', '#C0392B'); NAVY = '#14264A'
W, X0 = 7.0, 0.5
fig = plt.figure(figsize=(8, 12.6)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 8); ax.set_ylim(0, 12.6); ax.axis('off')

def box(y, h, title, sub, col, x=X0, w=W, lw=2.0, dashed=False):
    p = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.12', fc=col[0], ec=col[1], lw=lw,
                       ls='--' if dashed else '-')
    ax.add_patch(p)
    if sub:
        ax.text(x + w/2, y + h*0.66, title, ha='center', va='center', fontsize=15, fontweight='bold', color=NAVY)
        ax.text(x + w/2, y + h*0.26, sub, ha='center', va='center', fontsize=10.5, color='#222222')
    else:
        ax.text(x + w/2, y + h/2, title, ha='center', va='center', fontsize=15, fontweight='bold', color=NAVY)

def arrow(y_from, y_to):
    ax.annotate('', xy=(4, y_to), xytext=(4, y_from), arrowprops=dict(arrowstyle='-|>', lw=1.8, color='#111111', mutation_scale=16))

H, GAP = 0.78, 0.34
y = 11.7
items = [
 ('Input Image', '512 × 512, 8-bit grayscale benchmark image (raw, unfiltered)', BLUE),
 ('Block Formation and Training-Vector Generation', '4 × 4 non-overlapping blocks converted into 16-dimensional vectors', BLUE),
]
ys = []
for t, s, c in items:
    box(y, H, t, s, c); ys.append((y, H)); y -= H + GAP
# parallel LBG
PH = 1.95
p = FancyBboxPatch((X0, y - (PH - H)), W, PH, boxstyle='round,pad=0.02,rounding_size=0.15', fc=ORANGE[0], ec=ORANGE[1], lw=2.0, ls='--')
ax.add_patch(p)
top = y - (PH - H); ys.append((top, PH))
ax.text(4, top + PH - 0.32, 'Parallel LBG (Vector Quantization)', ha='center', va='center', fontsize=16, fontweight='bold', color='#B03020')
for xx, lab in ((0.85, 'Process 0'), (4.55, 'Process P − 1')):
    ax.add_patch(FancyBboxPatch((xx, top + PH - 1.05), 2.6, 0.52, boxstyle='round,pad=0.02,rounding_size=0.08', fc='#FFF6EE', ec='#C0602B', lw=1.6))
    ax.text(xx + 1.3, top + PH - 0.79, lab, ha='center', va='center', fontsize=13, fontweight='bold', color='#B03020')
ax.text(4, top + PH - 0.79, '· · · · · ·', ha='center', va='center', fontsize=14, color='#B03020')
ax.text(4, top + 0.52, 'Codebook training distributed across P MPI processes (0 … P − 1);', ha='center', va='center', fontsize=10.5)
ax.text(4, top + 0.24, 'each process computes assignments and local statistics for its assigned vector subset', ha='center', va='center', fontsize=10.5)
y = top - GAP
rest = [
 ('Delta Encoding', 'Encodes differences between consecutive VQ indices', BLUE),
 ('Huffman Coding', 'Lossless entropy coding with canonical variable-length codes', BLUE),
 ('Compressed Image Data', 'Header + codebook + code-length table + coded indices', GREEN),
 ('Huffman Decoding', 'Recovers the delta-coded index sequence from the entropy-coded bitstream', BLUE),
 ('Inverse Delta Coding', 'Recovers absolute VQ indices from the decoded differences', BLUE),
 ('VQ Reconstruction', 'Rebuilds the image by replacing each index with its codebook vector', BLUE),
 ('Final Reconstructed Image', 'Reconstructed image (without post-processing)', GREEN),
]
for t, s, c in rest:
    y -= H; box(y, H, t, s, c); ys.append((y, H)); y -= GAP
# arrows
for (ya, ha), (yb, hb) in zip(ys[:-1], ys[1:]):
    arrow(ya - 0.02, yb + hb + 0.03)
fig.savefig('stages/figures/Figure_3_1_framework.png', dpi=220, facecolor='white')
print('bottom y =', round(y + GAP, 2))
