#!/usr/bin/env python3
"""General framework: sequential baseline (2A) and MPI-parallel LBG (2B) as two independent paths, same stages around them."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle

W, H = 21.0, 12.4
fig = plt.figure(figsize=(W, H)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')
NAVY = '#14264A'
C = dict(s1='#2F6DB5', s2a='#5E7385', s2b='#C98424', s3='#2A8C82', s4='#6A4C93')

def rbox(x, y, w, h, fc, ec, lw=2.0, r=0.14, ls='-', z=1):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0.01,rounding_size={r}', fc=fc, ec=ec, lw=lw, ls=ls, zorder=z))
def txt(x, y, s, fs=12, bold=False, color='#111111', ha='center', z=5, style='normal'):
    ax.text(x, y, s, fontsize=fs, fontweight='bold' if bold else 'normal', color=color, ha=ha, va='center', zorder=z, linespacing=1.25, fontstyle=style)
def arrow(x1, y1, x2, y2, lw=2.2, color='#111111', ms=18):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='-|>', lw=lw, color=color, mutation_scale=ms, shrinkA=0, shrinkB=0), zorder=6)
def line(xs, ys, lw=2.2, color='#111111'):
    ax.plot(xs, ys, lw=lw, color=color, solid_capstyle='butt', zorder=6)

# columns
cols = {'s1': (0.35, 3.1), 's2a': (3.95, 3.9), 's2b': (8.35, 5.6), 's3': (14.45, 3.2), 's4': (18.15, 2.55)}
TOP, HEAD_H, BODY_B = 11.0, 1.55, 1.95
heads = {
 's1': 'Stage 1\nBlock Formation',
 's2a': 'Stage 2A\nSequential LBG\n(Baseline)',
 's2b': 'Stage 2B\nMPI-Based Parallel\nLBG (Proposed)',
 's3': 'Stage 3\nLossless Index\nCoding',
 's4': 'Stage 4\nDecoding and\nReconstruction',
}
for k, (x, w) in cols.items():
    rbox(x, BODY_B, w, TOP - BODY_B, 'white', C[k], lw=2.6, r=0.2)
    rbox(x, TOP - HEAD_H, w, HEAD_H, C[k], C[k], lw=2.6, r=0.2, z=2)
    ax.add_patch(Rectangle((x + 0.02, TOP - HEAD_H), w - 0.04, 0.3, fc=C[k], ec=C[k], zorder=2))
    txt(x + w/2, TOP - HEAD_H/2, heads[k], fs=17, bold=True, color='white')

PURPLE = ('#E6DCF3', '#8E6BBF'); BLUE = ('#D6E8FA', '#4A90D9'); WHITE = ('#FFFFFF', '#9DB8D6'); ORANGE = ('#FBE8D0', '#D28A2B')

# ---------------- Stage 1 ----------------
x, w = cols['s1']; cx = x + w/2
txt(cx, 8.45, 'Input image', fs=13, bold=True)
txt(cx, 8.05, '512 × 512 (gray / color)', fs=11.5)
gx, gy, gs = cx - 0.9, 5.95, 0.3
for i in range(6):
    for j in range(6):
        ax.add_patch(Rectangle((gx + i*gs, gy + j*gs), gs, gs, fc='#E3E3E3', ec='#8A8A8A', lw=0.8, zorder=3))
arrow(cx, 5.85, cx, 5.3)
bx, by, bs = cx - 0.45, 4.2, 0.3
for i in range(3):
    for j in range(3):
        ax.add_patch(Rectangle((bx + i*bs, by + j*bs), bs, bs, fc='#E3E3E3', ec='#8A8A8A', lw=0.8, zorder=3))
ax.add_patch(Rectangle((bx + bs, by + bs), bs, bs, fc='white', ec='#2F6DB5', lw=1.8, zorder=4))
txt(cx, 3.65, '4 × 4 blocks\n→ 16-D vectors\n(N = 16,384)', fs=12)
rbox(x + 0.15, 2.1, w - 0.3, 0.95, '#EEF4FB', C['s1'], lw=1.5, r=0.1)
txt(cx, 2.575, 'Color images: R, G, B channels\nare processed one after another', fs=10.2, style='italic')

# ---------------- Stage 2A ----------------
x, w = cols['s2a']; cx = x + w/2
rbox(cx - 1.15, 8.35, 2.3, 0.55, ORANGE[0] if False else '#E8EDF2', C['s2a'], lw=1.8, r=0.25)
txt(cx, 8.62, 'Repeat until K = 64', fs=12, bold=True)
rbox(x + 0.2, 4.3, w - 0.4, 3.85, BLUE[0], BLUE[1], lw=2.0)
txt(cx, 7.8, 'LBG iteration (k)', fs=14, bold=True)
for i, s in enumerate(['1. Nearest-codeword\nassignment', '2. Update codebook\n(centroids)', '3. Convergence check']):
    yy = 6.95 - i*0.95
    rbox(x + 0.4, yy - 0.38, w - 0.8, 0.78, WHITE[0], WHITE[1], lw=1.4, r=0.1)
    txt(cx, yy, s, fs=11.5)
arrow(cx, 4.3, cx, 3.85)
rbox(x + 0.2, 2.1, w - 0.4, 1.7, PURPLE[0], PURPLE[1], lw=2.0)
txt(cx, 2.95, 'Codebook C (K = 64)\n+ index array L\n(N = 16,384)', fs=12, bold=True)
txt(cx, 1.62, 'executed by a single process', fs=10.5, style='italic', color=C['s2a'])

# ---------------- Stage 2B ----------------
x, w = cols['s2b']; cx = x + w/2
rbox(x + 0.2, 8.1, w - 0.4, 0.8, '#FFF3E0', ORANGE[1], lw=1.6, r=0.1)
txt(cx, 8.5, 'Work distribution: Equal (P ≤ 6) or Adaptive (P > 6)', fs=10.8, bold=True)
txt(cx, 8.22, 'MPI_Scatterv sends each process its vectors', fs=10.2)
rbox(cx - 1.15, 7.45, 2.3, 0.5, '#FBE8D0', C['s2b'], lw=1.8, r=0.25)
txt(cx, 7.7, 'Repeat until K = 64', fs=12, bold=True)
rbox(x + 0.2, 3.4, w - 0.4, 3.85, BLUE[0], BLUE[1], lw=2.0)
txt(cx, 6.95, 'MPI iteration (k), all processes in parallel', fs=12.5, bold=True)
chips = ['Process 0', 'Process 1', '…', 'Process P − 1']
cw = [1.05, 1.05, 0.4, 1.35]; cxs = x + 0.4
for s, ww in zip(chips, cw):
    if s != '…':
        rbox(cxs, 6.28, ww, 0.42, '#FFF6E8', '#C0602B', lw=1.3, r=0.08)
    txt(cxs + ww/2, 6.49, s, fs=9.2, bold=True, color='#B03020')
    cxs += ww + 0.12
items = ['1. Nearest assignment (local vectors)', '2. Local sums, counts, distortion', '3. MPI_Allreduce (global sums)', '4. Codebook update (all processes)', '5. Convergence check']
for i, s in enumerate(items):
    yy = 5.75 - i*0.5
    rbox(x + 0.45, yy - 0.2, w - 0.9, 0.4, WHITE[0], WHITE[1], lw=1.3, r=0.08)
    txt(cx, yy, s, fs=10.6)
arrow(cx, 3.4, cx, 3.12)
rbox(x + 0.2, 2.1, w - 0.4, 1.0, PURPLE[0], PURPLE[1], lw=2.0)
txt(cx, 2.6, 'Codebook C (K = 64) + index array L\n(N = 16,384), MPI_Gatherv to Process 0', fs=11.2, bold=True)
txt(cx, 1.62, 'all MPI processes work together', fs=10.5, style='italic', color=C['s2b'])

# ---------------- Stage 3 ----------------
x, w = cols['s3']; cx = x + w/2
rbox(x + 0.2, 7.2, w - 0.4, 1.55, BLUE[0], BLUE[1], lw=2.0)
txt(cx, 8.35, 'Delta coding', fs=13.5, bold=True)
txt(cx, 7.75, 'differences of consecutive\nindices (offset 128)', fs=10.8)
arrow(cx, 7.2, cx, 6.75)
rbox(x + 0.2, 5.0, w - 0.4, 1.75, BLUE[0], BLUE[1], lw=2.0)
txt(cx, 6.2, 'Canonical Huffman', fs=13.5, bold=True)
txt(cx, 5.55, 'variable-length codes built\nfrom code lengths', fs=10.8)
arrow(cx, 5.0, cx, 4.6)
rbox(x + 0.2, 2.1, w - 0.4, 2.5, PURPLE[0], PURPLE[1], lw=2.0)
txt(cx, 3.95, 'Compressed container', fs=13, bold=True)
txt(cx, 3.15, 'header\n+ codebook (8-bit)\n+ code-length table\n+ coded bitstream', fs=10.8)
txt(cx, 1.62, 'executed by Process 0', fs=10.5, style='italic', color=C['s3'])

# ---------------- Stage 4 ----------------
x, w = cols['s4']; cx = x + w/2
labels = [('Huffman decoding', 'from the code-length\ntable and bitstream'), ('Inverse delta coding', 'recovers the\nVQ indices'), ('VQ reconstruction', 'codebook lookup')]
yy = 8.0
for i, (t, s) in enumerate(labels):
    rbox(x + 0.18, yy - 0.95, w - 0.36, 1.5, '#EADFF5', '#8E6BBF', lw=2.0)
    txt(cx, yy + 0.18, t, fs=12.2, bold=True)
    txt(cx, yy - 0.42, s, fs=10.2)
    if i < 2: arrow(cx, yy - 0.95, cx, yy - 1.4)
    yy -= 2.0
rbox(x + 0.18, 2.1, w - 0.36, 0.6, '#E3F1DB', '#3F7F2A', lw=2.0, r=0.1)
txt(cx, 2.4, 'Reconstructed image', fs=10.6, bold=True)
txt(cx, 1.62, 'executed by Process 0', fs=10.5, style='italic', color=C['s4'])

# ---------------- arrows between stages ----------------
ym = 5.9
x1 = cols['s1'][0] + cols['s1'][1]; x2a = cols['s2a'][0]; x2b = cols['s2b'][0]; x3 = cols['s3'][0]; x4 = cols['s4'][0]
arrow(x1 + 0.02, ym, x2a - 0.02, ym, lw=3.0, ms=22)
# Stage 1 -> 2B over the top (independent path)
top_y = 11.75
line([cols['s1'][0] + 1.3, cols['s1'][0] + 1.3], [TOP, top_y]); line([cols['s1'][0] + 1.3, cols['s2b'][0] + 2.0], [top_y, top_y])
arrow(cols['s2b'][0] + 2.0, top_y, cols['s2b'][0] + 2.0, TOP + 0.02)
# 'versus' marker between 2A and 2B
gx = (cols['s2a'][0] + cols['s2a'][1] + x2b) / 2
ax.add_patch(Circle((gx, ym), 0.3, fc='white', ec='#555555', lw=1.8, zorder=7))
txt(gx, ym, 'vs.', fs=11, bold=True, color='#555555', z=8)
# outputs -> Stage 3
arrow(cols['s2b'][0] + cols['s2b'][1] + 0.02, 2.6, x3 - 0.02, 2.6, lw=3.0, ms=22)
bot = 1.2
sx = cols['s2a'][0] + cols['s2a'][1] - 0.5
line([sx, sx], [2.1, bot]); line([sx, cols['s3'][0] + 0.45], [bot, bot])
arrow(cols['s3'][0] + 0.45, bot, cols['s3'][0] + 0.45, 2.08)
arrow(cols['s3'][0] + cols['s3'][1] + 0.02, ym, x4 - 0.02, ym, lw=3.0, ms=22)

# legend
rbox(6.3, 0.18, 0.9, 0.38, C['s2b'], C['s2b'], lw=1, r=0.1); txt(7.35, 0.37, 'Parallel: all MPI processes work together', fs=12.5, bold=True, ha='left')
rbox(12.8, 0.18, 0.9, 0.38, C['s2a'], C['s2a'], lw=1, r=0.1); txt(13.85, 0.37, 'Sequential: executed by a single process', fs=12.5, bold=True, ha='left')
fig.savefig('stages/figures/Figure_framework_sequential_vs_parallel.png', dpi=170, facecolor='white')
print('saved')
