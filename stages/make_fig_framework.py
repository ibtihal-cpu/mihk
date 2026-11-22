#!/usr/bin/env python3
"""General framework, two-row layout (portrait-friendly): sequential baseline and MPI-parallel LBG as independent paths."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle

W, H = 15.4, 16.2
fig = plt.figure(figsize=(W, H)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')
NAVY = '#0B1F3F'
C = dict(s1='#2F6DB5', s2a='#5E7385', s2b='#C98424', s3='#2A8C82', s4='#6A4C93')
BLUE = ('#D6E8FA', '#3F83CC'); WHITE = ('#FFFFFF', '#8FB0D4'); PURPLE = ('#E6DCF3', '#8E6BBF'); ORANGE = ('#FFF1DC', '#D28A2B'); GREENB = ('#E3F1DB', '#3F7F2A')

def rbox(x, y, w, h, fc, ec, lw=2.8, r=0.16, ls='-', z=1):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0.01,rounding_size={r}', fc=fc, ec=ec, lw=lw, ls=ls, zorder=z))
def T(x, y, s, fs=14, color='#000000', ha='center', style='normal', z=6):
    ax.text(x, y, s, fontsize=fs*1.1, fontweight='bold', color=color, ha=ha, va='center', zorder=z, linespacing=1.25, fontstyle=style)
def arrow(x1, y1, x2, y2, lw=3.0, ms=22):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='-|>', lw=lw, color='#111111', mutation_scale=ms, shrinkA=0, shrinkB=0), zorder=7)
def line(xs, ys, lw=3.0): ax.plot(xs, ys, lw=lw, color='#111111', solid_capstyle='butt', zorder=7)
def stage(key, x, y, w, h, hh, title):
    rbox(x, y, w, h, 'white', C[key], lw=3.2, r=0.22)
    rbox(x, y + h - hh, w, hh, C[key], C[key], lw=3.2, r=0.22, z=2)
    ax.add_patch(Rectangle((x + 0.02, y + h - hh), w - 0.04, 0.3, fc=C[key], ec=C[key], zorder=2))
    T(x + w/2, y + h - hh/2, title, fs=21, color='white')

TOP = 15.3; HH = 1.7; BODY_B = 6.25
# ---------------- top row ----------------
S1 = (0.3, 3.6); S2A = (4.3, 4.3); S2B = (9.2, 5.9)
stage('s1', S1[0], BODY_B, S1[1], TOP - BODY_B, HH, 'Stage 1\nBlock Formation')
stage('s2a', S2A[0], BODY_B, S2A[1], TOP - BODY_B, HH, 'Stage 2A\nSequential LBG\n(Baseline)')
stage('s2b', S2B[0], BODY_B, S2B[1], TOP - BODY_B, HH, 'Stage 2B\nMPI-Based Parallel\nLBG (Proposed)')
# stage 1
cx = S1[0] + S1[1]/2
T(cx, 12.95, 'Input image', fs=16); T(cx, 12.5, '512 × 512 (gray / color)', fs=13)
gs = 0.23; gx, gy = cx - 4*gs, 10.45
for i in range(8):
    for j in range(8):
        ax.add_patch(Rectangle((gx + i*gs, gy + j*gs), gs, gs, fc='#E3E3E3', ec='#8A8A8A', lw=0.8, zorder=3))
ax.add_patch(Rectangle((gx + 2*gs, gy + 2*gs), 4*gs, 4*gs, fc='none', ec='#2F6DB5', lw=3.0, zorder=4))
arrow(cx, 10.3, cx, 9.8)
bs = 0.3; bx, by = cx - 2*bs, 8.5
for i in range(4):
    for j in range(4):
        ax.add_patch(Rectangle((bx + i*bs, by + j*bs), bs, bs, fc='#E3E3E3', ec='#8A8A8A', lw=0.8, zorder=3))
ax.add_patch(Rectangle((bx, by), 4*bs, 4*bs, fc='none', ec='#2F6DB5', lw=3.0, zorder=4))
T(cx, 8.0, '4 × 4 blocks\n→ 16-D vectors\n(N = 16,384)', fs=14)
rbox(S1[0] + 0.15, 6.35, S1[1] - 0.3, 0.95, '#EEF4FB', C['s1'], lw=1.8, r=0.1)
T(cx, 6.83, 'Color images: RGB channels\nare processed sequentially;\nLBG is parallel within each channel', fs=10.4, style='italic')
# stage 2A
cx = S2A[0] + S2A[1]/2
rbox(cx - 1.4, 12.95, 2.8, 0.55, '#E8EDF2', C['s2a'], lw=2.2, r=0.28); T(cx, 13.22, 'Repeat until K = 64', fs=14)
rbox(S2A[0] + 0.2, 8.35, S2A[1] - 0.4, 4.45, BLUE[0], BLUE[1], lw=2.6)
T(cx, 12.45, 'LBG iteration (k)', fs=16)
for i, s in enumerate(['1. Nearest-codeword\nassignment', '2. Update codebook\n(centroids)', '3. Convergence check']):
    yy = 11.4 - i*1.15
    rbox(S2A[0] + 0.4, yy - 0.45, S2A[1] - 0.8, 0.9, WHITE[0], WHITE[1], lw=1.8, r=0.1); T(cx, yy, s, fs=13.5)
arrow(cx, 8.35, cx, 7.95)
rbox(S2A[0] + 0.2, 6.4, S2A[1] - 0.4, 1.55, PURPLE[0], PURPLE[1], lw=2.6)
T(cx, 7.18, 'Codebook C (K = 64)\n+ index array L (N = 16,384)', fs=13.5)
# stage 2B
cx = S2B[0] + S2B[1]/2
rbox(S2B[0] + 0.2, 12.45, S2B[1] - 0.4, 1.0, ORANGE[0], ORANGE[1], lw=2.2, r=0.12)
T(cx, 13.08, 'Equal or Adaptive workload distribution', fs=14.5); T(cx, 12.7, 'MPI_Scatterv sends the vectors to the processes', fs=12.5)
rbox(cx - 1.4, 11.85, 2.8, 0.55, '#FBE8D0', C['s2b'], lw=2.2, r=0.28); T(cx, 12.13, 'Repeat until K = 64', fs=14)
rbox(S2B[0] + 0.2, 7.25, S2B[1] - 0.4, 4.45, BLUE[0], BLUE[1], lw=2.6)
T(cx, 11.35, 'MPI iteration (k), all processes', fs=15)
chips = ['Process 0', 'Process 1', '…', 'Process P − 1']; cw = [1.2, 1.2, 0.5, 1.6]
cxs = S2B[0] + 0.55
for s, w_ in zip(chips, cw):
    if s != '…': rbox(cxs, 10.55, w_, 0.5, '#FFF6E8', '#C0602B', lw=1.6, r=0.08)
    T(cxs + w_/2, 10.8, s, fs=10.6, color='#A82A0E'); cxs += w_ + 0.15
items = ['1. Nearest assignment (local vectors)', '2. Local sums, counts, distortion', '3. MPI_Allreduce (global statistics)', '4. Codebook update (all processes)', '5. Convergence check']
for i, s in enumerate(items):
    yy = 9.95 - i*0.6
    rbox(S2B[0] + 0.45, yy - 0.26, S2B[1] - 0.9, 0.52, WHITE[0], WHITE[1], lw=1.6, r=0.08); T(cx, yy, s, fs=12.6)
arrow(cx, 7.25, cx, 7.0)
rbox(S2B[0] + 0.2, 6.4, S2B[1] - 0.4, 0.6, PURPLE[0], PURPLE[1], lw=2.6, r=0.1)
T(cx, 6.7, 'C on all processes; L on Process 0 (MPI_Gatherv)', fs=10.6)
# ---------------- bottom row ----------------
B_TOP, B_H, BH = 5.3, 4.3, 1.1
S3 = (0.3, 7.1); S4 = (8.0, 7.1)
stage('s3', S3[0], B_TOP - B_H, S3[1], B_H, BH, 'Stage 3: Lossless Index Coding')
stage('s4', S4[0], B_TOP - B_H, S4[1], B_H, BH, 'Stage 4: Decoding and Reconstruction')
y0, bh = 1.75, 1.75
def trio(x, texts, cols, subs):
    w = 2.05; g = 0.3; xs = x + 0.2
    for i, (t, c, sub) in enumerate(zip(texts, cols, subs)):
        rbox(xs, y0, w, bh, c[0], c[1], lw=2.4, r=0.12)
        T(xs + w/2, y0 + bh*0.7, t, fs=12.8); T(xs + w/2, y0 + bh*0.3, sub, fs=10.2)
        if i < 2: arrow(xs + w + 0.01, y0 + bh/2, xs + w + g - 0.01, y0 + bh/2, lw=2.6, ms=18)
        xs += w + g
trio(S3[0], ['Delta coding', 'Canonical\nHuffman Coding', 'Compressed\ncontainer'], [BLUE, BLUE, PURPLE],
     ['offset 128', 'from code lengths', 'header, codebook,\ncode-length table,\nbitstream'])
trio(S4[0], ['Huffman\ndecoding', 'Inverse delta\ncoding', 'VQ\nreconstruction'], [PURPLE, PURPLE, ('#EADFF5', '#8E6BBF')],
     ['code-length table\nand bitstream', 'recovers the\nVQ indices', 'codebook lookup'])
T(S3[0] + S3[1]/2, 1.3, 'executed by Process 0', fs=11.5, color=C['s3'], style='italic')
T(S4[0] + S4[1]/2, 1.3, 'executed by Process 0', fs=11.5, color=C['s4'], style='italic')
# ---------------- arrows ----------------
arrow(S1[0] + S1[1] + 0.02, 10.0, S2A[0] - 0.02, 10.0)
top_y = 15.75
line([S1[0] + 1.4, S1[0] + 1.4], [TOP, top_y]); line([S1[0] + 1.4, S2B[0] + 2.2], [top_y, top_y]); arrow(S2B[0] + 2.2, top_y, S2B[0] + 2.2, TOP + 0.02)
gx_ = (S2A[0] + S2A[1] + S2B[0]) / 2
ax.add_patch(Circle((gx_, 10.0), 0.3, fc='white', ec='#555555', lw=2.0, zorder=8)); T(gx_, 10.0, 'vs.', fs=11, color='#555555', z=9)
# outputs -> stage 3
jy = 5.75
line([S2A[0] + S2A[1]/2, S2A[0] + S2A[1]/2], [6.4, jy]); line([S2B[0] + S2B[1]/2, S2B[0] + S2B[1]/2], [6.4, jy])
line([S2B[0] + S2B[1]/2, S3[0] + S3[1]/2], [jy, jy]); arrow(S3[0] + S3[1]/2, jy, S3[0] + S3[1]/2, B_TOP + 0.02)
arrow(S3[0] + S3[1] + 0.01, B_TOP - B_H/2 - 0.2, S4[0] - 0.01, B_TOP - B_H/2 - 0.2)
# legend
rbox(3.6, 0.2, 0.9, 0.42, C['s2b'], C['s2b'], lw=1, r=0.1); T(4.65, 0.41, 'Parallel: all MPI processes work together', fs=12.5, ha='left')
rbox(9.9, 0.2, 0.9, 0.42, C['s2a'], C['s2a'], lw=1, r=0.1); T(10.95, 0.41, 'Sequential: a single process', fs=12.5, ha='left')
fig.savefig('stages/figures/Figure_framework_sequential_vs_parallel.png', dpi=300, facecolor='white')
matplotlib.rcParams['svg.fonttype'] = 'path'
fig.savefig('stages/figures/Figure_framework_sequential_vs_parallel.svg')
fig.savefig('stages/figures/Figure_framework_sequential_vs_parallel.pdf')
print('saved')
