#!/usr/bin/env python3
"""Equal and Adaptive workload distribution (thesis figure; 'speed' replaced by 'computation')."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

W, H = 10.4, 9.0
fig = plt.figure(figsize=(W, H)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')
BLUE = ('#DCEBFA', '#2F6DB5'); PEACH = ('#FDE3D2', '#C0582B'); RED = '#A82A0E'
def rbox(x, y, w, h, col, lw=2.8, ls='-', r=0.12):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0.01,rounding_size={r}', fc=col[0], ec=col[1], lw=lw, ls=ls, zorder=1))
def T(x, y, s, fs=12, color='#0B1F3F'):
    ax.text(x, y, s, fontsize=fs * 1.3, fontweight='bold', color=color, ha='center', va='center', zorder=5, linespacing=1.3)
def arrow(x1, y1, x2, y2, lw=2.6, ms=18):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='-|>', lw=lw, color='#222222', mutation_scale=ms, shrinkA=0, shrinkB=0), zorder=6)
def line(xs, ys, lw=2.6): ax.plot(xs, ys, lw=lw, color='#222222', solid_capstyle='butt', zorder=6)

# top
rbox(3.5, 7.85, 3.4, 0.95, BLUE); T(5.2, 8.325, 'Training Vectors', fs=13)
cxL, cxR = 2.35, 7.65
line([5.2, 5.2], [7.85, 7.4]); line([cxL, cxR], [7.4, 7.4])
arrow(cxL, 7.4, cxL, 6.98); arrow(cxR, 7.4, cxR, 6.98)
# Equal
rbox(0.35, 3.2, 4.0, 3.75, ('#F4F9FE', '#2F6DB5'), lw=2.6, ls='--', r=0.2); T(cxL, 6.5, 'Equal', fs=14)
rbox(0.85, 4.75, 3.0, 1.25, BLUE); T(cxL, 5.375, 'Equal Counts and\nDisplacements', fs=11.5)
arrow(cxL, 4.75, cxL, 4.3)
rbox(0.85, 3.5, 3.0, 0.8, PEACH); T(cxL, 3.9, 'MPI_Scatterv', fs=11.5, color=RED)
# Adaptive
rbox(5.35, 0.45, 4.6, 6.5, ('#F4F9FE', '#2F6DB5'), lw=2.6, ls='--', r=0.2); T(cxR, 6.5, 'Adaptive', fs=14)
rbox(5.75, 5.2, 3.8, 0.85, BLUE); T(cxR, 5.625, 'Calibrate_Computation', fs=11.5)
arrow(cxR, 5.2, cxR, 4.78)
rbox(5.75, 3.75, 3.8, 1.0, PEACH); T(cxR, 4.25, 'MPI_Allgather\n(computation rates)', fs=11.5, color=RED)
arrow(cxR, 3.75, cxR, 3.33)
rbox(5.75, 1.95, 3.8, 1.35, BLUE); T(cxR, 2.625, 'Computation-Weighted\nCounts and Displacements', fs=11.5)
arrow(cxR, 1.95, cxR, 1.55)
rbox(5.75, 0.75, 3.8, 0.8, PEACH); T(cxR, 1.15, 'MPI_Scatterv', fs=11.5, color=RED)
fig.savefig('stages/figures/Figure_workload_distribution.png', dpi=210, facecolor='white')
print('saved')
