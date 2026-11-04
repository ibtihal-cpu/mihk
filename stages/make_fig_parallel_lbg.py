#!/usr/bin/env python3
"""Workflow of the MPI-based parallel LBG (seminar figure corrected against codep_min.c; Process instead of Rank)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Circle

W, H = 11.9, 19.6
fig = plt.figure(figsize=(W, H)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')
NAVY = '#14264A'
PEACH = ('#FDEAD7', '#D49A55'); BLUE = ('#DCEBFA', '#4A90D9'); PURPLE = ('#E6DCF3', '#8E6BBF'); GREEN = ('#E3F1DB', '#6AA84F'); WHITE = ('#FFFFFF', '#9DB8D6')
X0, X1 = 0.6, 11.0; CX = (X0 + X1) / 2

def rbox(x, y, w, h, col, lw=2.0, r=0.14, ls='-', z=1):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0.01,rounding_size={r}', fc=col[0], ec=col[1], lw=lw, ls=ls, zorder=z))
def T(x, y, s, fs=13, bold=False, color='#111111', ha='center', z=6):
    ax.text(x, y, s, fontsize=fs*1.3, fontweight='bold' if bold else 'normal', color=('#000000' if color == '#111111' else color), ha=ha, va='center', zorder=z, linespacing=1.3)
def arrow(x1, y1, x2, y2, lw=2.8, ms=20):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='-|>', lw=lw, color='#111111', mutation_scale=ms, shrinkA=0, shrinkB=0), zorder=7)
def line(xs, ys, lw=2.8):
    ax.plot(xs, ys, lw=lw, color='#111111', solid_capstyle='butt', zorder=7)
def badge(n, y):
    ax.add_patch(Circle((X0 + 0.42, y), 0.27, fc='#CFE6F7', ec='#2F6DB5', lw=1.6, zorder=8)); T(X0 + 0.42, y, str(n), fs=13, bold=True, z=10)

GAP = 0.32
cur = 19.1
def step(h, col, title, sub=None, n=None, tfs=13.5, sfs=12):
    global cur
    y = cur - h
    rbox(X0, y, X1 - X0, h, col)
    if sub:
        T(CX + 0.25, y + h * 0.66, title, fs=tfs, bold=True); T(CX + 0.25, y + h * 0.3, sub, fs=sfs)
    else:
        T(CX + 0.25, y + h / 2, title, fs=tfs, bold=True)
    if n: badge(n, y + h / 2)
    cur = y - GAP
    return y, h

boxes = []
boxes.append(step(1.2, PEACH, 'Process 0: read the image and build the training vectors', '4 × 4 blocks → N = 16,384 vectors of dimension d = 16', 1))
boxes.append(step(0.95, PURPLE, 'MPI_Bcast: broadcast the number of training vectors N', None, 2))
boxes.append(step(1.45, BLUE, 'Determine the workload and compute counts and displacements', 'Equal (P ≤ 6)  or  Adaptive (P > 6: speed calibration + MPI_Allgather)', 3))
boxes.append(step(0.95, PURPLE, 'MPI_Scatterv: distribute the training vectors to all processes', None, 4))
boxes.append(step(1.45, BLUE, 'All processes: compute the global mean (initial codeword c₁, K = 1)', 'local sums and counts → MPI_Allreduce (sum) → c₁ = Σ S / Σ n', 5))
y6, h6 = step(1.05, GREEN, 'All processes: binary splitting of the shared codebook', 'K ← 2K,   c → (1 + δ)c  and  (1 − δ)c,   δ = 0.01', 6, sfs=12)
# loop box
LH = 2.55; yl = cur - LH
rbox(X0, yl, X1 - X0, LH, ('#EAF3FC', '#2F6DB5'), lw=2.0, ls='--')
badge(7, yl + LH / 2)
T(CX + 0.25, yl + LH - 0.35, 'LBG iteration (for the current K), executed by all processes', fs=13.0, bold=True, color='#1B3E7A')
rbox(1.25, yl + 0.2, 3.75, 1.6, WHITE, lw=1.8, r=0.1)
T(3.125, yl + 1.0, 'Each process (local data):\nnearest-codeword assignment;\nlocal sums $S_k$, counts $n_k$,\nlocal distortion $D_{local}$', fs=11.0)
rbox(5.3, yl + 0.65, 1.9, 0.8, PURPLE, lw=2.0, r=0.2); T(6.25, yl + 1.05, 'MPI_Allreduce\n(sum)', fs=11.2, bold=True)
rbox(7.55, yl + 0.2, 2.75, 1.6, WHITE, lw=1.8, r=0.1)
T(8.925, yl + 1.0, 'All processes:\n$c_k = S_k / n_k$\nglobal distortion $D$', fs=11.0)
arrow(5.01, yl + 1.05, 5.28, yl + 1.05, lw=2.2, ms=15); arrow(7.22, yl + 1.05, 7.53, yl + 1.05, lw=2.2, ms=15)
cur = yl - GAP
# convergence diamond
dh1 = 2.0; dw1 = 6.4; yd1 = cur - dh1; yc1 = yd1 + dh1 / 2
ax.add_patch(Polygon([(CX, yd1 + dh1), (CX + dw1/2, yc1), (CX, yd1), (CX - dw1/2, yc1)], closed=True, fc='#FFE08A', ec='#C99A1E', lw=2.0, zorder=2))
T(CX, yc1 + 0.32, 'Converged?', fs=14, bold=True); T(CX, yc1 - 0.08, r'$\Delta D = |D_{prev} - D| / D \leq \varepsilon$  or  iter $\geq$ 100', fs=11.3)
T(CX, yc1 - 0.45, '(for each codebook size)', fs=10.5)
cur = yd1 - GAP
dh2 = 1.3; dw2 = 3.6; yd2 = cur - dh2; yc2 = yd2 + dh2 / 2
ax.add_patch(Polygon([(CX, yd2 + dh2), (CX + dw2/2, yc2), (CX, yd2), (CX - dw2/2, yc2)], closed=True, fc='#FFF1C7', ec='#C99A1E', lw=2.0, zorder=2))
T(CX, yc2, 'K < 64 ?', fs=14, bold=True)
cur = yd2 - GAP
yg, hg = step(0.95, PURPLE, 'MPI_Gatherv: collect the indices on Process 0 (block order)', None, 8)
yp, hp = step(1.2, PEACH, 'Process 0: delta coding → canonical Huffman coding', 'produces the compressed container', 9)

# arrows between boxes (vertical)
ys = [(b[0], b[1]) for b in boxes] + [(y6, h6)]
for (ya, ha), (yb, hb) in zip(ys[:-1], ys[1:]):
    arrow(CX, ya - 0.01, CX, yb + hb + 0.01)
arrow(CX, y6 - 0.01, CX, yl + LH + 0.01)
arrow(CX, yl - 0.01, CX, yd1 + dh1 + 0.01)
arrow(CX, yd1 - 0.01, CX, yd2 + dh2 + 0.01); T(CX + 0.55, yd1 - 0.17, 'Yes', fs=12.5, bold=True)
arrow(CX, yd2 - 0.01, CX, yg + hg + 0.01); T(CX + 0.5, yd2 - 0.17, 'No', fs=12.5, bold=True)
arrow(CX, yg - 0.01, CX, yp + hp + 0.01)
# No loop (converged? -> iteration)
xr = X1 + 0.35
line([CX + dw1/2, xr], [yc1, yc1]); line([xr, xr], [yc1, yl + LH/2]); arrow(xr, yl + LH/2, X1 + 0.01, yl + LH/2)
T(CX + dw1/2 + 0.45, yc1 + 0.25, 'No', fs=12.5, bold=True)
# Yes loop (K<64 -> splitting)
xl = X0 - 0.3
line([CX - dw2/2, xl], [yc2, yc2]); line([xl, xl], [yc2, y6 + h6/2]); arrow(xl, y6 + h6/2, X0 - 0.01, y6 + h6/2)
T(CX - dw2/2 - 0.45, yc2 + 0.25, 'Yes', fs=12.5, bold=True)

fig.savefig('stages/figures/Figure_parallel_LBG_workflow.png', dpi=210, facecolor='white')
print('bottom of the flow =', round(yp, 2))
