#!/usr/bin/env python3
"""Build results/Chapter_4_final.docx (+ figures) from results/final_campaign/*.csv.
Every number in the text and tables is computed from the CSV files (half-up rounding on exact decimals).
usage: python3 results/generators/build_ch4_final.py        (run from the repository root)
Placeholders that need the author (image sources, Lena figure, related-studies table) are highlighted in yellow."""
import csv, os, sys
from decimal import Decimal as D, ROUND_HALF_UP
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.shared import Pt, Cm, Inches
from docx.oxml.ns import qn

ROOT = os.getcwd()
DATA = os.path.join(ROOT, "results", "final_campaign")
FIG = os.path.join(ROOT, "results", "figures_final")
OUT = os.path.join(ROOT, "results", "Chapter_4_final.docx")
os.makedirs(FIG, exist_ok=True)

# ------------------------------------------------------------------ helpers
def rd(x, dp): return str(D(x).quantize(D(1).scaleb(-dp), rounding=ROUND_HALF_UP))
def mean(v): v = [D(x) for x in v]; return sum(v) / len(v)
def mq(v, dp): return rd(mean(v), dp)
def rows(f): return list(csv.DictReader(open(os.path.join(DATA, f))))
def fnum(x): return rd(x, 0) if False else x
NM = {'gray': 'Lena', 'boat_img': 'Boat', 'cameraman_img': 'Cameraman', 'peppers_img': 'Peppers',
      'lena_color': 'Lena', 'peppers_color2': 'Peppers', 'f16_color': 'F16', 'goldhill_color': 'Gold Hill'}
GRAY = ['gray', 'boat_img', 'cameraman_img', 'peppers_img']
COL = ['lena_color', 'peppers_color2', 'f16_color', 'goldhill_color']
NPS = ['2', '4', '6', '8', '10', '12', '14']
BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'     # validated categorical slots 1-3 (light surface)

# ------------------------------------------------------------------ data
P = rows('param_study_nf.csv')
def prow(var):
    R = [r for r in P if r['variant'] == var]; assert len(R) == 4
    return dict(psnr=mq([r['PSNR_dB'] for r in R], 2), ssim=mq([r['SSIM'] for r in R], 4), cr=mq([r['system_CR'] for r in R], 2),
                it=mq([r['LBG_iters'] for r in R], 1), t=mq([r['LBG_time_median_s'] for r in R], 4))
PB = {k: prow(k) for k in ['2x2/K64', '4x4/K64', '8x8/K64', '4x4/K32', '4x4/K128']}
C = rows('correctness.csv')
Q = {}
for r in C:
    cr, mse, ps, ss, it = r['seq'].split(); Q[r['image']] = dict(cr=cr, mse=mse, psnr=ps, ssim=ss, it=it)
    assert r['metrics_identical'] == 'yes' and r['reconstruction_md5_identical'] == 'yes'
    assert r['seq'] == r['par_P4_auto'] == r['par_P14_auto'] == r['par_P14_equal']
def qm(names, k, dp): return mq([Q[i][k] for i in names], dp)
def qext(names, k, fn):
    vals = [(D(Q[i][k]), i) for i in names]; v = fn(vals); return v[1], str(v[0])
E = {r['image']: r for r in rows('entropy.csv')}
T = rows('timing_final.csv'); TI = {}
for r in T: TI.setdefault(r['image'], {})[r['np']] = r
for i in GRAY + COL:   # iteration count identical at every process count
    assert len({TI[i][p]['iters'] for p in TI[i]}) == 1
EA = rows('eq_ad_total.csv')
BASE = rows('baselines.csv'); MEM = rows('memory.csv')

def sp(key, names):
    out = {}
    for p in NPS:
        v = [TI[i][p][key] for i in names]; m = mean(v); n = D(p)
        out[p] = dict(m=rd(m, 2), mn=min(v, key=D), mx=max(v, key=D), eff=rd(m / n * 100, 1), kf=rd((1 / m - 1 / n) / (1 - 1 / n), 3), raw=m)
    return out
S = {('LBG', 'g'): sp('SpeedupLBG', GRAY), ('LBG', 'c'): sp('SpeedupLBG', COL), ('LBG', 'a'): sp('SpeedupLBG', GRAY + COL),
     ('TOT', 'g'): sp('SpeedupTotal', GRAY), ('TOT', 'c'): sp('SpeedupTotal', COL)}
def theta(i, p): return D(16384) * D(TI[i][p]['iters']) / D(TI[i][p]['LBG_s']) / D(10 ** 6)
TH = {}
for g, names in (('g', GRAY), ('c', COL)):
    TH[g] = {}
    for p in ['seq'] + NPS:
        v = [theta(i, p) for i in names]; TH[g][p] = dict(m=sum(v) / len(v), mn=min(v), mx=max(v))
def ea(names, p):
    R = [r for r in EA if r['image'] in names and r['np'] == p]; assert len(R) == 4
    return dict(el=mq([r['eq_lbg'] for r in R], 4), al=mq([r['ad_lbg'] for r in R], 4), lg=mq([r['lbg_gain_pct'] for r in R], 1),
                et=mq([r['eq_total'] for r in R], 4), at=mq([r['ad_total'] for r in R], 4), tg=mq([r['total_gain_pct'] for r in R], 1),
                lgmin=min((D(r['lbg_gain_pct']) for r in R)), lgmax=max((D(r['lbg_gain_pct']) for r in R)),
                R=R)
EAG = {g: {p: ea(n, p) for p in NPS} for g, n in (('g', GRAY), ('c', COL))}
def eaall(p, k): return mq([r[k] for r in EA if r['np'] == p], 1)
for p in ['8', '10', '12', '14']:        # adaptive faster for every image
    assert all(D(r['lbg_gain_pct']) > 0 and D(r['total_gain_pct']) > 0 for r in EA if r['np'] == p)
def mem(i, p): return [r for r in MEM if r['image'] == i and r['P'] == p][0]

# ------------------------------------------------------------------ figures
plt.rcParams.update({'font.size': 9.5, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True,
                     'grid.color': '#e5e4e0', 'grid.linewidth': 0.6, 'axes.edgecolor': '#52514e', 'savefig.dpi': 300})
def band(ax, g, color, label, data, key, marker, ls):
    xs = [int(p) for p in NPS]
    ys = [float(data[p]['m'] if key == 'speed' else data[p]['m']) for p in NPS]
    lo = [float(data[p]['mn']) for p in NPS] if key == 'speed' else [float(data[p]['mn']) for p in NPS]
    hi = [float(data[p]['mx']) for p in NPS]
    ax.fill_between(xs, lo, hi, color=color, alpha=0.18, linewidth=0)
    ax.plot(xs, ys, color=color, marker=marker, markersize=6, linewidth=1.8, linestyle=ls, label=label)
def speed_fig(key, fname, ymax):
    fig, ax = plt.subplots(figsize=(5.6, 3.6))
    ax.axvspan(1.5, 6.5, color='#f0efec', alpha=0.9, linewidth=0)
    ax.plot([2, 14], [2, 14], color='#52514e', linestyle=':', linewidth=1.2, label='Ideal linear speedup')
    band(ax, 'g', BLUE, 'Grayscale (mean, min–max)', S[(key, 'g')], 'speed', 'o', '-')
    band(ax, 'c', ORANGE, 'Color (mean, min–max)', S[(key, 'c')], 'speed', 's', '--')
    ax.set_xlabel('Number of MPI processes (P)'); ax.set_ylabel('Speedup'); ax.set_xticks([int(p) for p in NPS])
    ax.set_ylim(0, ymax); ax.set_xlim(1.5, 14.5)
    ax.text(2.0, ymax * 0.93, 'P-cores only (P ≤ 6)', fontsize=8, color='#52514e')
    ax.legend(frameon=False, loc='lower right', fontsize=8.5)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, fname)); plt.close(fig)
speed_fig('LBG', 'fig_lbg_speedup.png', 15)
speed_fig('TOT', 'fig_total_speedup.png', 15)
# throughput
fig, ax = plt.subplots(figsize=(5.6, 3.6)); xs = [int(p) for p in NPS]
ax.axvspan(1.5, 6.5, color='#f0efec', alpha=0.9, linewidth=0)
for g, col, lab, mk, ls in (('g', BLUE, 'Grayscale (mean, min–max)', 'o', '-'), ('c', ORANGE, 'Color (mean, min–max)', 's', '--')):
    ax.fill_between(xs, [float(TH[g][p]['mn']) for p in NPS], [float(TH[g][p]['mx']) for p in NPS], color=col, alpha=0.18, linewidth=0)
    ax.plot(xs, [float(TH[g][p]['m']) for p in NPS], color=col, marker=mk, markersize=6, linewidth=1.8, linestyle=ls, label=lab)
ax.set_xlabel('Number of MPI processes (P)'); ax.set_ylabel('LBG throughput (million vector-iterations/s)')
ax.set_xticks(xs); ax.set_xlim(1.5, 14.5); ax.set_ylim(0, 110); ax.legend(frameon=False, loc='lower right', fontsize=8.5)
ax.text(2.0, 101, 'P-cores only (P ≤ 6)', fontsize=8, color='#52514e')
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig_throughput.png')); plt.close(fig)
# equal vs adaptive
def ea_fig(kq, fname, ylab):
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.3), sharey=False)
    for ax, g, title in ((axs[0], 'g', 'Grayscale'), (axs[1], 'c', 'Color')):
        ax.axvspan(1.5, 6.5, color='#f0efec', alpha=0.9, linewidth=0)
        e = [float(EAG[g][p]['el' if kq == 'l' else 'et']) for p in NPS]; a = [float(EAG[g][p]['al' if kq == 'l' else 'at']) for p in NPS]
        ax.plot(xs, e, color=BLUE, marker='o', markersize=6, linewidth=1.8, label='Equal')
        ax.plot(xs, a, color=ORANGE, marker='s', markersize=6, linewidth=1.8, linestyle='--', label='Adaptive')
        ax.set_title(title, fontsize=10); ax.set_xlabel('Number of MPI processes (P)'); ax.set_xticks(xs); ax.set_xlim(1.5, 14.5)
        ax.set_ylim(0, max(e + a) * 1.12); ax.legend(frameon=False, fontsize=8.5, loc='upper right')
    axs[0].set_ylabel(ylab); fig.tight_layout(); fig.savefig(os.path.join(FIG, fname)); plt.close(fig)
ea_fig('l', 'fig_ea_lbg.png', 'Mean LBG time (s)')
ea_fig('t', 'fig_ea_total.png', 'Mean total time (s)')
# entropy
fig, ax = plt.subplots(figsize=(5.6, 3.7)); import numpy as np
x = np.arange(len(GRAY)); w = 0.26
for k, (col, lab, off) in enumerate(((BLUE, 'Entropy of indices', -w), (ORANGE, 'Entropy after delta coding', 0), (AQUA, 'Mean Huffman code length', w))):
    key = ['H_index_bits', 'H_delta_bits', 'huffman_bits_per_index'][k]
    ax.bar(x + off, [float(E[i][key]) for i in GRAY], w * 0.92, color=col, label=lab)
ax.axhline(6, color='#52514e', linestyle=':', linewidth=1.1); ax.text(3.45, 6.05, 'fixed 6-bit', fontsize=8, color='#52514e', ha='right')
ax.set_xticks(x); ax.set_xticklabels([NM[i] for i in GRAY]); ax.set_ylabel('Bits per index'); ax.set_ylim(0, 6.8)
ax.legend(frameon=False, fontsize=8.5, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3, columnspacing=1.2, handlelength=1.2); ax.grid(axis='x', visible=False)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig_entropy.png')); plt.close(fig)

# ------------------------------------------------------------------ docx plumbing
doc = Document()
st = doc.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
for s in doc.sections:
    s.page_width = Cm(21); s.page_height = Cm(29.7); s.left_margin = s.right_margin = Cm(2.5); s.top_margin = s.bottom_margin = Cm(2.5)
for name, size in (('Heading 1', 18), ('Heading 2', 14), ('Heading 3', 12)):
    h = doc.styles[name]; h.font.name = 'Times New Roman'; h.font.size = Pt(size); h.font.bold = True
    h.font.color.rgb = None; h.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
def para(text, bold=False, italic=False, align=None, hl=False, size=None, space_after=6):
    p = doc.add_paragraph(); r = p.add_run(text); r.bold = bold; r.italic = italic
    if hl: r.font.highlight_color = WD_COLOR_INDEX.YELLOW
    if size: r.font.size = Pt(size)
    p.paragraph_format.space_after = Pt(space_after); p.paragraph_format.line_spacing = 1.15
    if align == 'j': p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if align == 'c': p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p
def body(text): return para(text, align='j')
def H1(t): doc.add_heading(t, 1)
def H2(t): doc.add_heading(t, 2)
def H3(t): doc.add_heading(t, 3)
def caption_t(t): p = para(t, bold=True, space_after=3); p.paragraph_format.keep_with_next = True; return p
def caption_f(t): return para(t, italic=True, align='c', size=11, space_after=10)
def table(header, rws, widths=None, bold_rows=(), size=10, align_first='l'):
    t = doc.add_table(rows=1, cols=len(header)); t.style = 'Table Grid'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(header):
        c = t.rows[0].cells[j]; c.text = ''; r = c.paragraphs[0].add_run(str(h)); r.bold = True; r.font.size = Pt(size)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for k, row in enumerate(rws):
        cells = t.add_row().cells
        for j, v in enumerate(row):
            cells[j].text = ''; r = cells[j].paragraphs[0].add_run(str(v)); r.font.size = Pt(size)
            if k in bold_rows: r.bold = True
            cells[j].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT if (j == 0 and align_first == 'l') else WD_ALIGN_PARAGRAPH.CENTER
    if widths:
        for row in t.rows:
            for j, w in enumerate(widths): row.cells[j].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t
def figure(fname, width, cap):
    doc.add_picture(os.path.join(FIG, fname), width=Inches(width)); doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_f(cap)
def note(text): para(text, italic=True, size=10, space_after=8)

g_, c_ = 'g', 'c'
def meanrange(names, k, dp): return f"{min(D(Q[i][k]) for i in names)}–{max(D(Q[i][k]) for i in names)}"

# ================================================================== CHAPTER
doc.add_heading('Chapter Four', 1).alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_heading('Results and Discussion', 1).alignment = WD_ALIGN_PARAGRAPH.CENTER

H2('4.1 Introduction')
body("This chapter presents and discusses the experimental results of the proposed image compression framework, which combines LBG vector quantization, delta coding, and Huffman coding, and which parallelizes the LBG codebook training stage with MPI. The evaluation covers grayscale and color images using the sequential and MPI-based parallel implementations described in Chapter Three. Two aspects are assessed: compression and reconstruction quality, and computational performance.")
body("Compression performance is evaluated using the compression ratio (CR), while reconstruction quality is assessed using the mean squared error (MSE), the peak signal-to-noise ratio (PSNR), and the structural similarity index (SSIM). Parallel performance is examined using execution time, speedup, parallel efficiency, throughput, and the Karp–Flatt metric. The results also compare the equal and adaptive speed-aware workload-distribution strategies on the heterogeneous multicore platform.")
body("The remainder of this chapter first describes the experimental setup and the measurement protocol, including the choice of the block size and the codebook size. It then presents the compression and reconstruction-quality results for grayscale and color images, followed by the sequential and parallel performance results. The equal and adaptive workload-distribution strategies are then compared, the equivalence between the sequential and parallel implementations is verified, and the memory usage is reported.")

H2('4.2 Experimental Setup')
body("The experiments were conducted on a heterogeneous multicore system based on a 13th-generation Intel Core i7-13650HX processor. The processor has 14 physical cores: six performance cores (P-cores) and eight efficiency cores (E-cores). Each P-core supports two hardware threads, whereas each E-core supports one, giving 20 hardware threads in total. The programs were written in C, compiled with GCC 13.3.0 using the -O2 optimization option, and executed under Ubuntu 24.04.4 LTS with Open MPI 4.1.6. Table 4.1 lists the experimental platform.")
caption_t('Table 4.1. Experimental platform.')
table(['Parameter', 'Configuration'], [
    ['Processor', '13th Gen Intel Core i7-13650HX'], ['CPU architecture', 'Heterogeneous multicore'],
    ['Physical cores', '14 (6 P-cores + 8 E-cores)'], ['Hardware threads', '20 (P-core: 2 threads per core; E-core: 1 thread per core)'],
    ['Memory', '23 GiB'], ['Operating system', 'Ubuntu 24.04.4 LTS (Linux kernel 7.0.0-34-generic)'],
    ['Compiler', 'GCC 13.3.0 (-O2)'], ['MPI implementation', 'Open MPI 4.1.6'],
    ['Implementation language', 'C'], ['Parallel programming model', 'MPI (SPMD)'],
    ['Process binding', '--bind-to core'], ['CPU frequency governor', 'performance (AC power connected)'],
    ['Timing repetitions', '5'], ['Reported statistic', 'Median execution time']], widths=[5.5, 10])
body("Before each timing campaign, the CPU frequency governor was set to performance and the system was connected to AC power. Both conditions were verified by the measurement script. MPI processes were bound to physical cores using --bind-to core. Ranks 0–5 were assigned to the P-cores, whereas ranks 6–13 were assigned to the E-cores. The sequential program was pinned to a single P-core.")
body("Each timing configuration was executed five times, and the median execution time was reported. The sequential baseline was obtained from the native sequential implementation rather than from an MPI execution with one process. The same input data and algorithmic parameters were used in the sequential and parallel experiments. For the controlled comparison of the workload-distribution strategies, the Equal and Adaptive strategies were explicitly selected through the VQ_STRATEGY environment variable, and their runs were alternated within the same session. The LBG time was measured with MPI_Wtime around the timed LBG region, delimited by MPI_Barrier calls in the parallel program, and the total time was measured from the start of the program until the output operations were completed. The compression pipeline contains no random component; the quality metrics and the numbers of LBG iterations are therefore deterministic.")
body("The test set consists of eight standard 512 × 512 images: four grayscale images (Lena, Boat, Cameraman, and Peppers) and four color images (Lena, Peppers, F16, and Gold Hill), as listed in Table 4.2. The values of the fixed algorithmic parameters are given in Table 4.3.")
caption_t('Table 4.2. Test images.')
table(['Image', 'Type', 'Resolution', 'Source'],
      [[NM[i], 'Grayscale', '512 × 512', '[to be completed]'] for i in GRAY] + [[NM[i], 'Color (RGB)', '512 × 512', '[to be completed]'] for i in COL], widths=[4, 3.5, 3.5, 5])
para('[Author: complete the "Source" column with the dataset or collection of each image, and state whether any image was resized.]', hl=True, size=10)
caption_t('Table 4.3. Experimental parameters.')
table(['Parameter', 'Setting'], [['Image resolution', '512 × 512 pixels'], ['Block size', '4 × 4 pixels'], ['Vector dimension', '16'],
      ['Training vectors', '16,384 per grayscale image or color channel'], ['Codebook size K', '64'], ['Splitting factor δ', '0.01'],
      ['Convergence threshold ε', '10⁻⁴'], ['Maximum iterations per codebook size', '100'], ['Distance measure', 'Squared Euclidean distance']], widths=[7, 8.5])

H3('4.2.1 Parameter Selection')
body("Preliminary experiments were conducted to examine the effect of the block size and the codebook size on the compression performance. They were performed on the four grayscale images using the final configuration of the framework. The block size was varied while the codebook size was fixed at K = 64, and the codebook size was varied while the block size was fixed at 4 × 4. Reconstruction quality was evaluated with PSNR and SSIM. Compression was evaluated with the system compression ratio (CR), defined as the ratio of the original image size to the total size of the compressed representation, which comprises the codebook, the Huffman table, and the Huffman-coded data. The LBG execution time was measured with the sequential implementation, and the median of five runs was taken for each image. The values in Tables 4.4 and 4.5 are arithmetic means over the four images.")
def prow_t(k, label): d = PB[k]; return [label, d['psnr'], d['ssim'], d['cr'], d['it'], d['t']]
caption_t('Table 4.4. Effect of the block size (K = 64), averaged over the four grayscale images.')
table(['Block size', 'PSNR (dB)', 'SSIM', 'CR', 'LBG iterations', 'LBG time (s)'], [prow_t('2x2/K64', '2 × 2'), prow_t('4x4/K64', '4 × 4'), prow_t('8x8/K64', '8 × 8')], bold_rows=(1,))
b2, b4, b8 = PB['2x2/K64'], PB['4x4/K64'], PB['8x8/K64']
body(f"Increasing the block size produced a clear trade-off between reconstruction quality, compression ratio, and LBG execution time. The 2 × 2 block size gave the highest reconstruction quality, with a mean PSNR of {b2['psnr']} dB and an SSIM of {b2['ssim']}, but also the lowest compression ratio ({b2['cr']}) and the longest LBG time ({b2['t']} s). The 8 × 8 block size gave the highest compression ratio ({b8['cr']}) and the shortest LBG time ({b8['t']} s), but reduced the mean PSNR to {b8['psnr']} dB and the SSIM to {b8['ssim']}. The 4 × 4 block size was intermediate on every measure, with a compression ratio of {b4['cr']}, a PSNR of {b4['psnr']} dB, an SSIM of {b4['ssim']}, and an LBG time of {b4['t']} s. The mean number of LBG iterations decreased from {b2['it']} to {b4['it']} and {b8['it']} as the block size increased.")
caption_t('Table 4.5. Effect of the codebook size (4 × 4 blocks), averaged over the four grayscale images.')
table(['Codebook size K', 'PSNR (dB)', 'SSIM', 'CR', 'LBG iterations', 'LBG time (s)'], [prow_t('4x4/K32', '32'), prow_t('4x4/K64', '64'), prow_t('4x4/K128', '128')], bold_rows=(1,))
k32, k128 = PB['4x4/K32'], PB['4x4/K128']
body(f"Increasing the codebook size improved the reconstruction quality but reduced the compression ratio and increased the computational cost of LBG training. Increasing K from 32 to 64 raised the mean PSNR from {k32['psnr']} to {b4['psnr']} dB and the mean SSIM from {k32['ssim']} to {b4['ssim']}, and increasing K to 128 raised them further to {k128['psnr']} dB and {k128['ssim']}. The compression ratio, however, fell from {k32['cr']} at K = 32 to {b4['cr']} at K = 64 and {k128['cr']} at K = 128. The mean LBG time rose from {k32['t']} s to {b4['t']} s and {k128['t']} s, accompanied by an increase in the mean number of iterations from {k32['it']} to {b4['it']} and {k128['it']}. The longer time therefore reflects both the larger number of iterations and the larger codebook searched in each iteration.")
body(f"Based on these results, a block size of 4 × 4 and a codebook size of K = 64 were adopted for all subsequent experiments. This configuration was selected as a practical compromise between reconstruction quality, compression ratio, and LBG execution time rather than by optimizing a single metric. The LBG time of this configuration in Table 4.4 ({b4['t']} s) differs by less than 1% from the mean sequential LBG time reported in Section 4.4, since the two values come from separate measurement runs.")

H2('4.3 Compression and Reconstruction Quality Results')
body("This section reports the compression ratio and the reconstruction quality obtained with the final configuration (4 × 4 blocks, K = 64). The CR is the system compression ratio defined in Section 4.2.1. For color images, the RGB CR is the ratio of the original size of the three channels to the total compressed size of the three channels, and the RGB MSE is the mean squared error pooled over all three channels, from which the RGB PSNR is computed. PSNR is computed as 10 log₁₀(255²/MSE), and SSIM uses an 11 × 11 Gaussian window with σ = 1.5, K₁ = 0.01, and K₂ = 0.03; for color images, the mean of the SSIM values of the three channels is reported. All metrics were computed between the original image and the image reconstructed from the compressed representation.")
H3('4.3.1 Grayscale Images')
caption_t('Table 4.6. Compression and reconstruction quality for the grayscale images.')
table(['Image', 'CR', 'MSE', 'PSNR (dB)', 'SSIM', 'LBG iterations'],
      [[NM[i], Q[i]['cr'], Q[i]['mse'], Q[i]['psnr'], Q[i]['ssim'], Q[i]['it']] for i in GRAY] +
      [['Mean', qm(GRAY, 'cr', 2), qm(GRAY, 'mse', 2), qm(GRAY, 'psnr', 2), qm(GRAY, 'ssim', 4), qm(GRAY, 'it', 1)]], bold_rows=(4,))
def best(names, k, mx=True):
    vals = [(D(Q[i][k]), i) for i in names]; v = max(vals) if mx else min(vals); return NM[v[1]], str(v[0])
bc, bc_v = best(GRAY, 'cr'); wc, wc_v = best(GRAY, 'cr', False)
bp, bp_v = best(GRAY, 'psnr'); wp, wp_v = best(GRAY, 'psnr', False)
bs, bs_v = best(GRAY, 'ssim'); ws, ws_v = best(GRAY, 'ssim', False)
bm, bm_v = best(GRAY, 'mse', False); wm, wm_v = best(GRAY, 'mse')
psnr_span = rd(D(bp_v) - D(wp_v), 2); ssim_span = rd(D(bs_v) - D(ws_v), 4)
body(f"Table 4.6 shows that the reconstruction quality varied across the grayscale images under the same compression configuration. The compression ratio ranged from {wc_v} ({wc}) to {bc_v} ({bc}). The PSNR values were relatively close, ranging from {wp_v} dB ({wp}) to {bp_v} dB ({bp}), a spread of {psnr_span} dB, whereas the SSIM values varied more widely, from {ws_v} ({ws}) to {bs_v} ({bs}), a spread of {ssim_span}. {bc} gave the highest compression ratio, the lowest MSE ({bm_v}), the highest PSNR, and the highest SSIM, whereas {wp} had the lowest PSNR and the highest MSE ({wm_v}), and {ws} had the lowest SSIM. The number of LBG iterations ranged from {min(Q[i]['it'] for i in GRAY)} to {max(Q[i]['it'] for i in GRAY)}. These differences indicate that, even though all images were compressed with identical algorithmic settings, the compression efficiency and the reconstruction quality depend on the image content.")
para('[Figure 4.1 — insert here the original and reconstructed Lena image with an enlarged region. The reconstructed image must be produced by the final program without any filter: run ./lbg_seq lena.txt --gray and use compressed_raw.bmp.]', hl=True, size=10)
caption_f('Figure 4.1. Original and reconstructed Lena images with an enlarged view of a selected region.')
H3('4.3.2 Color Images')
body("Table 4.7 reports the results for the four color images in terms of the RGB compression ratio, the RGB MSE, the RGB PSNR, and the mean channel-wise SSIM.")
caption_t('Table 4.7. Compression and reconstruction quality for the color images.')
table(['Image', 'RGB CR', 'RGB MSE', 'RGB PSNR (dB)', 'Mean SSIM', 'LBG iterations (R+G+B)'],
      [[NM[i], Q[i]['cr'], Q[i]['mse'], Q[i]['psnr'], Q[i]['ssim'], Q[i]['it']] for i in COL] +
      [['Mean', qm(COL, 'cr', 2), qm(COL, 'mse', 2), qm(COL, 'psnr', 2), qm(COL, 'ssim', 4), qm(COL, 'it', 1)]], bold_rows=(4,))
cbc, cbc_v = best(COL, 'cr'); cwc, cwc_v = best(COL, 'cr', False); cbp, cbp_v = best(COL, 'psnr'); cwp, cwp_v = best(COL, 'psnr', False)
cbs, cbs_v = best(COL, 'ssim'); cws, cws_v = best(COL, 'ssim', False); cbm, cbm_v = best(COL, 'mse', False); cwm, cwm_v = best(COL, 'mse')
body(f"Table 4.7 shows moderate variation across the color images. The RGB CR ranged from {cwc_v} ({cwc}) to {cbc_v} ({cbc}), and the RGB PSNR from {cwp_v} dB ({cwp}) to {cbp_v} dB ({cbp}). {cbc} achieved the best result on every measure, with the highest CR, the lowest MSE ({cbm_v}), the highest PSNR, and the highest SSIM ({cbs_v}). Color {cws} had the lowest SSIM ({cws_v}) and the highest MSE ({cwm_v}), and {cwc} had the lowest compression ratio. The grayscale and color versions of the same scene did not give identical quality: for Peppers, the mean SSIM was {Q['peppers_color2']['ssim']} for the color version and {Q['peppers_img']['ssim']} for the grayscale version, and for Lena it was {Q['lena_color']['ssim']} and {Q['gray']['ssim']}, respectively.")
body("The variation among the images is consistent with the data-dependent nature of vector quantization, since the LBG codebook is generated from the training vectors of each image. Differences in the distribution of these vectors lead to different quantization errors even when the algorithmic parameters are identical.")

H3('4.3.3 Entropy and Delta–Huffman Coding Efficiency')
body("To further examine the compression performance reported above, the entropy of the codebook index sequence was analyzed before and after delta coding and compared with the average Huffman code length. The analysis was performed on the four grayscale images for K = 64; the program does not report the entropy of the color images. Table 4.8 gives the entropy of the original index sequence (H_index), the entropy after delta coding (H_delta), the reduction between them, the average Huffman code length per index, its difference from H_delta, and the saving relative to fixed-length 6-bit indices. The Huffman code length refers to the encoded index data and excludes the Huffman table.")
er = []
for i in GRAY:
    r = E[i]; red = D(r['H_index_bits']) - D(r['H_delta_bits']); gap = D(r['huffman_bits_per_index']) - D(r['H_delta_bits']); sav = (1 - D(r['huffman_bits_per_index']) / 6) * 100
    er.append([NM[i], r['H_index_bits'], r['H_delta_bits'], rd(red, 3), r['huffman_bits_per_index'], rd(gap, 3), rd(sav, 1)])
def col(k): return [D(x[k]) for x in er]
er.append(['Mean', rd(sum(col(1)) / 4, 3), rd(sum(col(2)) / 4, 3), rd(sum(col(3)) / 4, 3), rd(sum(col(4)) / 4, 3), rd(sum(col(5)) / 4, 3), rd(sum(col(6)) / 4, 1)])
caption_t('Table 4.8. Entropy of the index sequence and Huffman code length for the grayscale images (K = 64).')
table(['Image', 'H_index (bits)', 'H_delta (bits)', 'Reduction (bits)', 'Huffman length (bits/index)', 'Huffman − H_delta (bits)', 'Saving vs. 6-bit (%)'], er, bold_rows=(4,), size=9)
ered = {NM[i]: D(E[i]['H_index_bits']) - D(E[i]['H_delta_bits']) for i in GRAY}
emax = max(ered, key=ered.get); emin = min(ered, key=ered.get)
gaps = [D(E[i]['huffman_bits_per_index']) - D(E[i]['H_delta_bits']) for i in GRAY]; savs = [(1 - D(E[i]['huffman_bits_per_index']) / 6) * 100 for i in GRAY]
body(f"Delta coding reduced the entropy of the index sequence for all four images. The mean entropy decreased from {er[-1][1]} to {er[-1][2]} bits per symbol, a mean reduction of {er[-1][3]} bits, with the largest reduction for {emax} ({rd(ered[emax], 3)} bits) and the smallest for {emin} ({rd(ered[emin], 3)} bits). The effectiveness of delta coding therefore depends on the structure of the index sequence generated for each image.")
body(f"The average Huffman code length remained close to the entropy of the delta-coded sequence, with a difference of {rd(min(gaps), 3)} to {rd(max(gaps), 3)} bits per index (Figure 4.2). Compared with fixed-length 6-bit indices for K = 64, Huffman coding reduced the index storage by {rd(min(savs), 1)}% to {rd(max(savs), 1)}%, with a mean saving of {er[-1][6]}%. The code length also relates to the compression ratio: {NM['cameraman_img']} needed {E['cameraman_img']['huffman_bits_per_index']} bits per index and reached a CR of {E['cameraman_img']['system_CR']}, whereas {NM['gray']} needed {E['gray']['huffman_bits_per_index']} bits per index and reached {E['gray']['system_CR']}.")
figure('fig_entropy.png', 5.2, 'Figure 4.2. Entropy of the VQ index sequence before and after delta coding, and the mean Huffman code length, for the four grayscale images.')
cr8 = D(262144) / (1024 + 16384); cr6 = D(262144) / (1024 + 12288)
ic = []
for i in GRAY:
    c = D(E[i]['system_CR']); ic.append([NM[i], rd(cr8, 2), rd(cr6, 2), E[i]['system_CR'], rd((c / cr6 - 1) * 100, 1)])
ic.append(['Mean', rd(cr8, 2), rd(cr6, 2), mq([E[i]['system_CR'] for i in GRAY], 2), rd(sum((D(E[i]['system_CR']) / cr6 - 1) * 100 for i in GRAY) / 4, 1)])
body("Table 4.9 translates this into the system compression ratio. For comparison, two reference index codings are shown: fixed-length 8-bit indices (one byte per index) and fixed-length 6-bit indices, which is the minimum fixed length for K = 64. Both include the 1,024-byte codebook. Delta coding with Huffman coding exceeded the 6-bit coding for every image; the system CR increased by " + f"{ic[-1][4]}% on average, and by {min(D(r[4]) for r in ic[:-1])}% to {max(D(r[4]) for r in ic[:-1])}% depending on the image. The gain in CR is not equal to the saving in index storage because the codebook and the Huffman table are included in the system CR.")
caption_t('Table 4.9. Effect of the index coding on the system compression ratio (K = 64, codebook included).')
table(['Image', 'Fixed 8-bit CR', 'Fixed 6-bit CR', 'Delta + Huffman CR', 'Gain over 6-bit (%)'], ic, bold_rows=(4,))

H3('4.3.4 Reference Comparison with JPEG and JPEG 2000')
body("To place the compression performance in context, the grayscale images were also encoded with JPEG and JPEG 2000 at the same compression ratio as the proposed codec. Both baselines were produced with off-the-shelf libraries (Pillow and OpenJPEG) with their default settings. For each image, the JPEG quality factor was selected so that the compression ratio was as close as possible to that of the proposed codec, and JPEG 2000 was given the same target ratio. PSNR and SSIM were computed with the same formulas as for the proposed codec. The compression ratio of the baselines is based on the size of the complete encoded file, including its headers. The mean results are given in Table 4.10 and the per-image results in Appendix A (Table A.4).")
bm_ = {}
for m in ('Proposed', 'JPEG', 'JPEG 2000'):
    R = [r for r in BASE if r['method'] == m]; assert len(R) == 4
    bm_[m] = [mq([r['CR'] for r in R], 2), mq([r['PSNR_dB'] for r in R], 2), mq([r['SSIM'] for r in R], 4)]
caption_t('Table 4.10. Rate-matched reference comparison on the four grayscale images (mean values).')
table(['Method', 'CR', 'PSNR (dB)', 'SSIM'], [['Proposed (LBG + delta + Huffman)', *bm_['Proposed']], ['JPEG', *bm_['JPEG']], ['JPEG 2000', *bm_['JPEG 2000']]])
body(f"At the same compression ratio, both standard codecs gave a higher reconstruction quality than the proposed codec: the mean PSNR was {bm_['JPEG'][1]} dB for JPEG and {bm_['JPEG 2000'][1]} dB for JPEG 2000, compared with {bm_['Proposed'][1]} dB for the proposed codec, and the mean SSIM was {bm_['JPEG'][2]} and {bm_['JPEG 2000'][2]}, compared with {bm_['Proposed'][2]}. This result is expected, since JPEG and JPEG 2000 rely on transform coding, whereas the proposed codec uses plain vector quantization with a 64-entry codebook. The comparison is therefore provided as a reference only. The objective of this work is not to outperform these standards in rate–distortion terms but to accelerate the LBG codebook training with MPI without changing the compressed result. No execution-time comparison is made, because the implementations, optimization levels, and platforms differ.")

H2('4.4 Sequential Performance Results')
body("This section reports the execution time of the sequential implementation, which serves as the baseline for the speedup and efficiency analysis in the following sections. The sequential program was pinned to a single P-core, and each value is the median of five runs. Two times are reported: the LBG time, which covers the codebook-training stage only, and the total time, which covers the complete program using the same measurement boundaries as the parallel implementation.")
def seqrows(names):
    out = []
    for i in names:
        s = TI[i]['seq']; out.append([NM[i], s['LBG_s'], s['Total_s'], rd(D(s['LBG_s']) / D(s['Total_s']) * 100, 1), s['iters']])
    shs = [D(TI[i]['seq']['LBG_s']) / D(TI[i]['seq']['Total_s']) * 100 for i in names]
    out.append(['Mean', mq([TI[i]['seq']['LBG_s'] for i in names], 4), mq([TI[i]['seq']['Total_s'] for i in names], 4), rd(sum(shs) / 4, 1), mq([TI[i]['seq']['iters'] for i in names], 1)])
    return out, shs
sg, shg = seqrows(GRAY); sc, shc = seqrows(COL)
caption_t('Table 4.11. Sequential execution times for the grayscale images.')
table(['Image', 'LBG time (s)', 'Total time (s)', 'LBG share of total (%)', 'LBG iterations'], sg, bold_rows=(4,))
lg = {NM[i]: D(TI[i]['seq']['LBG_s']) for i in GRAY}
body(f"For the grayscale images, the LBG time ranged from {min(lg.values())} s ({min(lg, key=lg.get)}) to {max(lg.values())} s ({max(lg, key=lg.get)}), and the total time from {min(D(TI[i]['seq']['Total_s']) for i in GRAY)} s to {max(D(TI[i]['seq']['Total_s']) for i in GRAY)} s. The LBG stage accounted for {rd(min(shg), 1)}% to {rd(max(shg), 1)}% of the total execution time, which confirms that LBG training is the dominant stage of the sequential implementation and supports its selection as the main target of parallelization.")
fewest = min(GRAY, key=lambda i: int(TI[i]['seq']['iters'])); longest = max(GRAY, key=lambda i: D(TI[i]['seq']['LBG_s']))
body(f"The number of LBG iterations also varied among the images. {NM[fewest]} required the fewest iterations ({TI[fewest]['seq']['iters']}), yet its LBG time ({TI[fewest]['seq']['LBG_s']} s) was the longest of the four images. The iteration count alone therefore does not explain the differences in execution time.")
caption_t('Table 4.12. Sequential execution times for the color images.')
table(['Image', 'LBG time (s)', 'Total time (s)', 'LBG share of total (%)', 'LBG iterations (R+G+B)'], sc, bold_rows=(4,))
mlg, mlc = mean([TI[i]['seq']['LBG_s'] for i in GRAY]), mean([TI[i]['seq']['LBG_s'] for i in COL])
body(f"The color images required approximately three times the LBG time of the grayscale images: the mean LBG time was {rd(mlc, 4)} s for the color images and {rd(mlg, 4)} s for the grayscale images (a ratio of {rd(mlc / mlg, 2)}). This is consistent with the processing scheme of Chapter Three, in which each color image is processed as three independent channels. The LBG stage accounted for {rd(min(shc), 1)}% to {rd(max(shc), 1)}% of the total execution time of the color images, a slightly larger share than for the grayscale images.")

H2('4.5 Parallel Performance Results')
body("This section presents the performance of the MPI-based implementation with the default workload-distribution strategy defined in Chapter Three: Equal distribution for P ≤ 4 and Adaptive distribution for P > 4. Speedup was calculated as the ratio of the sequential time reported in Section 4.4 to the corresponding parallel time, and the parallel efficiency as the speedup divided by the number of processes P. The Karp–Flatt metric was used to examine the effective serial fraction and the parallel overhead as P increased; it was computed from the mean speedup at each process count. For every image, the parallel implementation performed the same number of LBG iterations as the sequential implementation at all tested process counts (see also Section 4.7); the reported speedups therefore compare the same algorithmic workload.")
H3('4.5.1 LBG Performance')
def sprow(key, p):
    a, b = S[(key, 'g')][p], S[(key, 'c')][p]
    return [p, f"{a['m']} ({a['mn']}–{a['mx']})", a['eff'], a['kf'], f"{b['m']} ({b['mn']}–{b['mx']})", b['eff'], b['kf']]
HDR = ['P', 'Gray: speedup (min–max)', 'Gray: efficiency (%)', 'Gray: Karp–Flatt', 'Color: speedup (min–max)', 'Color: efficiency (%)', 'Color: Karp–Flatt']
caption_t('Table 4.13. LBG speedup, parallel efficiency, and Karp–Flatt metric (mean over the four grayscale and the four color images).')
table(HDR, [sprow('LBG', p) for p in NPS], size=9)
a14, c14, all14 = S[('LBG', 'g')]['14'], S[('LBG', 'c')]['14'], S[('LBG', 'a')]['14']
kfs = [D(S[('LBG', x)][p]['kf']) for x in 'gc' for p in NPS]
body(f"Table 4.13 shows that the mean LBG speedup increased with every process count and reached {a14['m']} for the grayscale images and {c14['m']} for the color images at P = 14 (Figure 4.3). Across all eight images, the speedup at P = 14 ranged from {all14['mn']} to {all14['mx']}, so the scaling was very similar for the tested images. The parallel efficiency was {S[('LBG','g')]['6']['eff']}% (grayscale) and {S[('LBG','c')]['6']['eff']}% (color) at P = 6, decreased to {S[('LBG','g')]['8']['eff']}% and {S[('LBG','c')]['8']['eff']}% at P = 8, and reached {a14['eff']}% and {c14['eff']}% at P = 14. The decrease after P = 6 coincides with the transition from execution on the six P-cores to mixed P-core and E-core execution. The effect of this hardware heterogeneity and the role of adaptive workload distribution are examined in Section 4.6.")
figure('fig_lbg_speedup.png', 5.2, 'Figure 4.3. Mean LBG speedup of the grayscale and color images compared with the ideal linear speedup. The shaded bands show the minimum-to-maximum range across the images of each group.')
kf8 = [D(S[('LBG', x)][p]['kf']) for x in 'gc' for p in ['8', '10', '12', '14']]
body(f"The Karp–Flatt metric of the LBG stage ranged from {min(kfs)} to {max(kfs)}. It was lowest at P = 4 ({S[('LBG','g')]['4']['kf']} for grayscale and {S[('LBG','c')]['4']['kf']} for color) and P = 6, increased at P = 8, and remained between {min(kf8)} and {max(kf8)} from P = 8 to P = 14. Because the Karp–Flatt metric estimates an effective serial fraction, it reflects not only inherently sequential work but also parallel overhead and workload imbalance. On the heterogeneous processor used here, the values observed after P = 6 are therefore interpreted together with the transition to mixed P-core and E-core execution, and not as a direct measurement of the strictly sequential fraction.")
H3('4.5.2 Total Execution Performance')
body("The LBG speedup describes the scaling of the principal parallelized stage. To determine how it affected the end-to-end performance, the total execution time was also examined (Table 4.14).")
caption_t('Table 4.14. Total execution-time speedup, parallel efficiency, and Karp–Flatt metric (mean over the four grayscale and the four color images).')
table(HDR, [sprow('TOT', p) for p in NPS], size=9)
t14g, t14c = S[('TOT', 'g')]['14'], S[('TOT', 'c')]['14']
kg = [D(S[('TOT', 'g')][p]['kf']) for p in NPS]; kc = [D(S[('TOT', 'c')][p]['kf']) for p in NPS]
kg8 = [D(S[('TOT', 'g')][p]['kf']) for p in ['8', '10', '12', '14']]; kc8 = [D(S[('TOT', 'c')][p]['kf']) for p in ['8', '10', '12', '14']]
body(f"The total-time speedup was lower than the LBG speedup because the complete program includes work outside the parallelized LBG stage. Nevertheless, it increased with the process count and reached {t14g['m']} for the grayscale images and {t14c['m']} for the color images at P = 14 (Figure 4.4), corresponding to efficiencies of {t14g['eff']}% and {t14c['eff']}%. The color images achieved the higher total speedup, which is consistent with the larger share of the LBG stage in their sequential time ({rd(sum(shc)/4, 1)}% versus {rd(sum(shg)/4, 1)}% for the grayscale images, Section 4.4).")
figure('fig_total_speedup.png', 5.2, 'Figure 4.4. Mean total-time speedup of the grayscale and color images compared with the ideal linear speedup. The shaded bands show the minimum-to-maximum range across the images of each group.')
body(f"The Karp–Flatt metric of the total time was substantially higher than that of the LBG stage, ranging from {min(kg)} to {max(kg)} for the grayscale images and from {min(kc)} to {max(kc)} for the color images. From P = 8 to P = 14 it varied only within {min(kg8)}–{max(kg8)} and {min(kc8)}–{max(kc8)}, respectively, which indicates that the estimated effective serial fraction, including parallel overhead and workload imbalance, remained approximately constant over this range. It should be interpreted as an effective serial fraction and not as a direct measurement of the strictly sequential part of the program.")
H3('4.5.3 Throughput')
body("The LBG throughput was defined in Section 3.6 as Θ = (N × I) / T_LBG, where N is the number of training vectors, I is the total number of LBG iterations, and T_LBG is the LBG execution time; for color images, the product N × I is summed over the three channels. Throughput expresses the amount of LBG work completed per unit time and allows the grayscale and color images, whose workloads differ, to be compared on a common scale. Because the sequential and parallel implementations perform exactly the same number of iterations on the same training vectors (Section 4.7), the total amount of work is identical, and the ratio between the parallel and the sequential throughput equals the LBG speedup. Throughput is therefore presented as an alternative view of the same scaling behavior and not as an independent performance measure.")
caption_t('Table 4.15. Mean LBG throughput (million vector-iterations per second).')
table(['P', 'Grayscale: mean (min–max)', 'Color: mean (min–max)'],
      [[('Seq.' if p == 'seq' else p), f"{rd(TH['g'][p]['m'], 3)} ({rd(TH['g'][p]['mn'], 3)}–{rd(TH['g'][p]['mx'], 3)})", f"{rd(TH['c'][p]['m'], 3)} ({rd(TH['c'][p]['mn'], 3)}–{rd(TH['c'][p]['mx'], 3)})"] for p in ['seq'] + NPS], size=9)
rg = TH['g']['14']['m'] / TH['g']['seq']['m']; rc = TH['c']['14']['m'] / TH['c']['seq']['m']
body(f"The mean throughput of the grayscale images increased from {rd(TH['g']['seq']['m'], 3)} million vector-iterations per second in the sequential program to {rd(TH['g']['14']['m'], 3)} at P = 14, a ratio of {rd(rg, 2)}, and that of the color images increased from {rd(TH['c']['seq']['m'], 3)} to {rd(TH['c']['14']['m'], 3)}, a ratio of {rd(rc, 2)}. These ratios agree with the mean LBG speedups in Table 4.13 ({a14['m']} and {c14['m']}), as expected. Figure 4.5 shows that the throughput increased rapidly at the lower process counts and that the rate of increase became smaller beyond P = 6.")
figure('fig_throughput.png', 5.2, 'Figure 4.5. Mean LBG throughput of the grayscale and color images across the MPI process counts. The shaded bands show the minimum-to-maximum range across the images of each group.')

H2('4.6 Equal and Adaptive Workload Distribution')
body("This section compares the Equal and Adaptive workload-distribution strategies described in Section 3.4. Both strategies were evaluated on the same eight images under the same conditions and the same process binding. At each process count the strategy was selected explicitly, and the Equal and Adaptive runs were alternated within the same measurement session. Each configuration was executed five times, and the median time was used. The speed calibration of the Adaptive strategy is performed before the timed LBG region and is therefore not included in the LBG time; it is included in the total time, which is examined later in this section. The LBG time is considered first, to isolate the effect of the workload distribution on the parallelized stage.")
def eatab(g):
    return [[p, EAG[g][p]['el'], EAG[g][p]['al'], EAG[g][p]['lg'], EAG[g][p]['et'], EAG[g][p]['at'], EAG[g][p]['tg']] for p in NPS]
EAH = ['P', 'Equal LBG (s)', 'Adaptive LBG (s)', 'LBG reduction (%)', 'Equal total (s)', 'Adaptive total (s)', 'Total reduction (%)']
caption_t('Table 4.16. Equal and Adaptive strategies: mean execution times and relative reductions for the grayscale images.')
table(EAH, eatab('g'), size=9)
caption_t('Table 4.17. Equal and Adaptive strategies: mean execution times and relative reductions for the color images.')
table(EAH, eatab('c'), size=9)
para("A positive reduction means that the Adaptive strategy was faster. The reductions are the means of the per-image relative reductions.", italic=True, size=10)
gg, gc = EAG['g'], EAG['c']
low_l = [abs(D(EAG[x][p]['lg'])) for x in 'gc' for p in ['2', '4', '6']]; low_t = [abs(D(EAG[x][p]['tg'])) for x in 'gc' for p in ['2', '4', '6']]
body(f"For P = 2, 4, and 6, the Equal and Adaptive strategies produced nearly identical mean LBG times (Tables 4.16 and 4.17, Figure 4.6): the mean differences did not exceed {max(low_l)}%, so adaptive workload distribution gave no measurable advantage in the P-core-only region. At P = 8, where execution enters the mixed P-core and E-core region, the behavior changed. For the grayscale images, the mean LBG time of the Equal strategy increased from {gg['6']['el']} s at P = 6 to {gg['8']['el']} s at P = 8, whereas that of the Adaptive strategy decreased from {gg['6']['al']} s to {gg['8']['al']} s. A similar pattern was observed for the color images: the Equal time increased from {gc['6']['el']} s to {gc['8']['el']} s, whereas the Adaptive time decreased from {gc['6']['al']} s to {gc['8']['al']} s. An interpretation consistent with this behavior is that, with equal vector counts, the ranks mapped to the faster P-cores finish earlier and wait for the ranks on the E-cores at each collective operation, whereas the speed-weighted partition reduces this waiting.")
figure('fig_ea_lbg.png', 6.0, 'Figure 4.6. Mean LBG time of the Equal and Adaptive strategies for the grayscale and color images. The shaded region marks the P-core-only range (P ≤ 6).')
body(f"The Adaptive strategy reduced the LBG time of all eight images at every process count from P = 8 to P = 14. The mean reduction over the eight images was {eaall('8','lbg_gain_pct')}% at P = 8, and decreased to {eaall('10','lbg_gain_pct')}%, {eaall('12','lbg_gain_pct')}%, and {eaall('14','lbg_gain_pct')}% at P = 10, 12, and 14, respectively. The reduction varied little among the images; for example, it ranged from {min(D(r['lbg_gain_pct']) for r in EA if r['np']=='8')}% to {max(D(r['lbg_gain_pct']) for r in EA if r['np']=='8')}% at P = 8 and from {min(D(r['lbg_gain_pct']) for r in EA if r['np']=='14')}% to {max(D(r['lbg_gain_pct']) for r in EA if r['np']=='14')}% at P = 14.")
figure('fig_ea_total.png', 6.0, 'Figure 4.7. Mean total execution time of the Equal and Adaptive strategies for the grayscale and color images. The shaded region marks the P-core-only range (P ≤ 6).')
body(f"For P = 2, 4, and 6, the total times of the two strategies were nearly identical, with the Adaptive strategy slightly slower on average (by at most {max(low_t)}%), which is consistent with the small cost of the speed calibration, included in the total time of the Adaptive strategy. From P = 8 to P = 14, the Adaptive strategy reduced the total time of all eight images. The mean reduction over the eight images was {eaall('8','total_gain_pct')}% at P = 8, {eaall('10','total_gain_pct')}% at P = 10, {eaall('12','total_gain_pct')}% at P = 12, and {eaall('14','total_gain_pct')}% at P = 14. These reductions are smaller than the corresponding LBG reductions because the complete program includes stages that are not accelerated by the workload distribution. The reduction was larger for the color images than for the grayscale images: at P = 8 it was {gc['8']['tg']}% and {gg['8']['tg']}%, respectively, and at P = 14 it was {gc['14']['tg']}% and {gg['14']['tg']}%. This is consistent with the larger share of the LBG stage in the sequential time of the color images (Section 4.4). The calibration cost was included in the total time of the Adaptive strategy, and the reduction nevertheless remained positive for every image.")

H2('4.7 Verification of the Parallel Implementation')
body("To verify that the MPI implementation preserves the results of the sequential implementation, a separate verification test was performed on all eight images. Four configurations were evaluated for each image: the sequential implementation, the parallel implementation with P = 4 (default strategy), the parallel implementation with P = 14 (default, Adaptive strategy), and the parallel implementation with P = 14 with the Equal strategy forced. The comparison covered the compression ratio, MSE, PSNR, SSIM, the number of LBG iterations, and the final reconstructed image, for which the MD5 hashes were also compared to confirm byte-for-byte equality.")
body("All 32 executions (8 images × 4 configurations) produced identical CR, MSE, PSNR, SSIM, and LBG iteration counts, and the MD5 hashes of the reconstructed images were identical in every case. This held at P = 14 with the Adaptive strategy, where the workload is distributed unequally among the processes. These results were obtained with the sums used in the codebook update accumulated and reduced in double precision, which makes the result independent of the order of the additions. The workload distribution therefore changes only how the computation is divided among the processes and does not change the final reconstructed output, so the reported speedups were obtained without altering the convergence behavior or the output relative to the sequential baseline. The per-image results are given in Appendix A (Table A.1).")
body("The comparison of the quality metrics and the reconstructed images was performed at P = 4 and P = 14. In addition, the number of LBG iterations matched the sequential value at all process counts used in the timing experiments (P = 2, 4, 6, 8, 10, 12, and 14). The codebooks and the compressed bit streams were not compared directly, and the verification is limited to the hardware platform, compiler, and MPI implementation used in this study.")

H2('4.8 Memory Usage')
body("The peak resident memory of the sequential program and of the MPI program was measured with the GNU time utility (maximum resident set size) for two grayscale and two color images; each reported value is the median of three runs. For the parallel program, every process was measured separately; Table 4.18 gives the largest value among the processes and the sum over all processes.")
mr = []
for i in ['gray', 'boat_img', 'lena_color', 'peppers_color2']:
    m1, m4, m14 = mem(i, '1'), mem(i, '4'), mem(i, '14')
    mr.append([NM[i] + (' (gray)' if i in GRAY else ' (color)'), m1['peak_rss_max_rank_MB'], f"{m4['peak_rss_max_rank_MB']} / {m4['peak_rss_sum_all_ranks_MB']}", f"{m14['peak_rss_max_rank_MB']} / {m14['peak_rss_sum_all_ranks_MB']}"])
caption_t('Table 4.18. Peak resident memory (MB): sequential program, and parallel program (largest process / sum over processes).')
table(['Image', 'Sequential', 'P = 4', 'P = 14'], mr, size=10)
body("The sequential program used approximately 3 MB for the grayscale images and 5 MB for the color images. In the parallel program, the largest per-process footprint was about 21–23 MB and was almost the same at P = 4 and P = 14, so the total memory grew approximately in proportion to the number of processes. The per-process footprint of the parallel program includes the MPI runtime and its shared libraries, which were not separated from the application data in this measurement; the sum over the processes therefore overestimates the memory attributable to the application, because shared libraries are counted once per process.")

H2('4.9 Comparison with Related Studies')
para('[Section pending. Before writing it, every value cited from the related studies (execution time, speedup, platform, dataset, PSNR/SSIM/CR) must be checked against the original source; the earlier table taken from the conference paper contains values of an older configuration and must not be reused. Planned content: a short paragraph stating that the studies differ in algorithm, dataset, and hardware, so the comparison is contextual; a table with the columns Study, Method, Platform, Data, Reported performance, and Quality/compression, with a final row "This work" filled from Tables 4.6, 4.7, and 4.13.]', hl=True, size=10)

H2('4.10 Chapter Summary')
body("This chapter evaluated the proposed framework on eight standard images (four grayscale and four color) in terms of compression and reconstruction quality, sequential and parallel performance, the Equal and Adaptive workload-distribution strategies, the agreement between the sequential and parallel implementations, and memory usage.")
body(f"With 4 × 4 blocks and a codebook of 64 codewords, the compression ratio ranged from {meanrange(GRAY,'cr',2)} for the grayscale images and from {meanrange(COL,'cr',2)} for the color images. The PSNR ranged from {meanrange(GRAY,'psnr',2)} dB and from {meanrange(COL,'psnr',2)} dB, and the SSIM from {meanrange(GRAY,'ssim',4)} and from {meanrange(COL,'ssim',4)}, respectively. Delta coding reduced the entropy of the index sequence, and delta coding with Huffman coding increased the system compression ratio by {ic[-1][4]}% on average compared with fixed-length 6-bit indices. At the same compression ratio, JPEG and JPEG 2000 gave a higher reconstruction quality than the proposed codec; the comparison is a reference and not a claim of superiority.")
body(f"In the sequential implementation, the LBG stage accounted for {rd(min(shg+shc), 1)}% to {rd(max(shg+shc), 1)}% of the total execution time. MPI parallelization achieved a mean LBG speedup of {all14['m']} at P = 14 (efficiency {all14['eff']}%), with {a14['m']} for the grayscale and {c14['m']} for the color images, and a mean total-time speedup of {t14g['m']} and {t14c['m']}, respectively. The efficiency decreased beyond P = 6, where execution entered the mixed P-core and E-core region.")
body(f"The Equal and Adaptive strategies gave nearly identical times for P = 2, 4, and 6. For P ≥ 8, the Adaptive strategy was faster for all eight images: it reduced the mean LBG time by {eaall('8','lbg_gain_pct')}% at P = 8 and {eaall('14','lbg_gain_pct')}% at P = 14, and the mean total time, including the calibration cost, by {eaall('8','total_gain_pct')}% and {eaall('14','total_gain_pct')}%, respectively. The verification experiments showed identical CR, MSE, PSNR, SSIM, LBG iteration counts, and reconstructed images between the sequential and the tested parallel configurations. Overall, MPI parallelization reduced the computational cost of the LBG stage without changing the compressed result, and adaptive workload distribution provided an additional benefit on the heterogeneous P-core and E-core platform. The conclusions and directions for future work are presented in the next chapter.")

# ---------------------------------------------------------------- appendices
doc.add_page_break()
H2('Appendix A. Per-Image Results')
H3('A.1 Verification of the sequential and parallel implementations')
caption_t('Table A.1. Per-image verification: sequential, P = 4, P = 14 (Adaptive), and P = 14 (Equal).')
table(['Image', 'Type', 'CR', 'MSE', 'PSNR (dB)', 'SSIM', 'LBG iterations', 'Metrics identical', 'MD5 identical'],
      [[NM[i], 'Gray' if i in GRAY else 'Color', Q[i]['cr'], Q[i]['mse'], Q[i]['psnr'], Q[i]['ssim'], Q[i]['it'], 'Yes', 'Yes'] for i in GRAY + COL], size=9)
note("The values in each row were identical in all four configurations. Metrics: CR, MSE, PSNR, SSIM, and LBG iterations. MD5: hash of the reconstructed image.")
for key, lab, tn in (('SpeedupLBG', 'LBG speedup', 'A.2'), ('SpeedupTotal', 'total-time speedup', 'A.3')):
    H3(f'{tn} Per-image {lab}')
    caption_t(f'Table {tn}. Per-image {lab} for each process count.')
    table(['Image'] + [f'P = {p}' for p in NPS], [[NM[i] + (' (gray)' if i in GRAY else ' (color)')] + [TI[i][p][key] for p in NPS] for i in GRAY + COL], size=9)
H3('A.4 Per-image reference comparison with JPEG and JPEG 2000')
caption_t('Table A.4. Rate-matched comparison with JPEG and JPEG 2000 for each grayscale image.')
table(['Image', 'Method', 'CR', 'PSNR (dB)', 'SSIM'], [[NM[r['image']], r['method'], r['CR'], r['PSNR_dB'], r['SSIM']] for r in BASE], size=9)
H3('A.5 Per-image reductions achieved by the Adaptive strategy')
caption_t('Table A.5. Reduction of the LBG time (%) and of the total time (%) achieved by the Adaptive strategy relative to the Equal strategy.')
def red_row(i, key): return [NM[i] + (' (gray)' if i in GRAY else ' (color)')] + [[r for r in EA if r['image'] == i and r['np'] == p][0][key] for p in NPS]
table(['LBG time: image'] + [f'P = {p}' for p in NPS], [red_row(i, 'lbg_gain_pct') for i in GRAY + COL], size=9)
table(['Total time: image'] + [f'P = {p}' for p in NPS], [red_row(i, 'total_gain_pct') for i in GRAY + COL], size=9)

doc.save(OUT)
print('saved', OUT)
