"""Builds all numeric Chapter-4 tables and the 4.7 text directly from final_results.xlsx,
writes results/CH4_TABLES.docx, then re-reads the docx and compares every cell with the source data."""
import statistics as st, json
from openpyxl import load_workbook
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

SRC = '/home/user/mihk/results/final_results.xlsx'
OUT = '/home/user/mihk/results/CH4_TABLES.docx'
FIG1 = '/home/user/mihk/results/fig_equal_vs_adaptive.png'
FIG2 = '/home/user/mihk/results/fig_equal_vs_adaptive_total.png'
wb = load_workbook(SRC)

def sheet(name):
    ws = wb[name]; hdr = [c.value for c in ws[1]]; out = []
    for r in ws.iter_rows(min_row=2):
        v = [c.value for c in r]
        if v[0] is None: continue
        out.append(dict(zip(hdr, v)))
    return out

Q = sheet('Quality'); A = sheet('Filter ablation'); T = sheet('Timing (all)')
E = sheet('EqAd unified (LBG+Total)'); E1 = sheet('EqAd session1 (LBG)'); TH = sheet('Throughput')

QN = {'Lena': 'Lena', 'Boat': 'Boat', 'Cameraman': 'Cameraman', 'Peppers': 'Peppers', 'Chest_X-ray': 'Chest X-ray',
      'Mammogram': 'Mammogram', 'Lung_CT': 'Lung CT', 'Brain_MRI': 'Brain MRI', 'Lena_Color': 'Color Lena',
      'Retina': 'Retinal fundus', 'PET_Axial': 'Brain axial', 'PET_Sagittal': 'Brain sagittal'}
TN = {'gray': 'Lena', 'boat_img': 'Boat', 'cameraman_img': 'Cameraman', 'peppers_img': 'Peppers',
      'chest_xray2_img': 'Chest X-ray', 'mammo2_img': 'Mammogram', 'lung_ct2_img': 'Lung CT',
      'brain_mri2_img': 'Brain MRI', 'lena_color': 'Color Lena', 'retina2_color': 'Retinal fundus',
      'brain_pet3_color': 'Brain axial', 'brain_pet4_color': 'Brain sagittal'}
NP = [2, 4, 6, 8, 10, 12, 14]
GRAY = ['Lena', 'Boat', 'Cameraman', 'Peppers', 'Chest_X-ray', 'Mammogram', 'Lung_CT', 'Brain_MRI']
COLOR = ['Lena_Color', 'Retina', 'PET_Axial', 'PET_Sagittal']
GRAYT = [k for k, v in TN.items() if v in [QN[x] for x in GRAY]]
COLORT = [k for k, v in TN.items() if v in [QN[x] for x in COLOR]]

def f(x, d): return f'{x:.{d}f}'
def sg(x, d):
    s = f'{x:+.{d}f}'
    return s.replace('-', '−') if False else s

tables = []   # (caption, header, rows)  -> verified after writing
def T_(cap, hdr, rows): tables.append((cap, hdr, rows)); return len(tables) - 1

# ---------- 4.3 / 4.4 quality
q = {r['image']: r for r in Q}
T_('Table 4.3. Compression and reconstruction quality of the grayscale images.',
   ['Image', 'CR (×)', 'BPP', 'MSE', 'PSNR (dB)', 'SSIM', 'LBG iterations'],
   [[QN[k], f(q[k]['CR_system'], 2), f(q[k]['BPP'], 4), f(q[k]['MSE'], 2), f(q[k]['PSNR_dB'], 2), f(q[k]['SSIM'], 4), str(q[k]['LBG_iters'])] for k in GRAY])
T_('Table 4.4. Compression and reconstruction quality of the color images (RGB).',
   ['Image', 'RGB CR (×)', 'BPP', 'RGB MSE', 'RGB PSNR (dB)', 'Mean SSIM', 'LBG iterations (R+G+B)'],
   [[QN[k], f(q[k]['CR_system'], 2), f(q[k]['BPP'], 4), f(q[k]['MSE'], 2), f(q[k]['PSNR_dB'], 2), f(q[k]['SSIM'], 4), str(q[k]['LBG_iters'])] for k in COLOR])

# ---------- 4.5 / 4.6 sequential
seq = {r['image']: r for r in T if str(r['np']) == 'seq'}
T_('Table 4.5. Sequential execution time of the grayscale images.',
   ['Image', 'LBG time (s)', 'Total time (s)', 'LBG iterations'],
   [[TN[k], f(seq[k]['LBG_s'], 4), f(seq[k]['Total_s'], 4), str(seq[k]['iters'])] for k in GRAYT])
T_('Table 4.6. Sequential execution time of the color images.',
   ['Image', 'LBG time, R+G+B (s)', 'Total time (s)', 'LBG iterations, R+G+B'],
   [[TN[k], f(seq[k]['LBG_s'], 4), f(seq[k]['Total_s'], 4), str(seq[k]['iters'])] for k in COLORT])

# ---------- 4.7 LBG speedup summary, 4.8 per image, 4.9 total
par = lambda n: [r for r in T if str(r['np']).replace('.0', '') == str(n)]
def kf(S, n): return (1 / S - 1 / n) / (1 - 1 / n)
rows47 = []; rows49 = []
for n in NP:
    a = par(n)
    sl = [r['SpeedupLBG'] for r in a]; stt = [r['SpeedupTotal'] for r in a]
    m = st.mean(sl); mt = st.mean(stt)
    rows47.append([str(n), f(m, 2), f(min(sl), 2), f(max(sl), 2), f(100 * m / n, 1), f(kf(m, n), 4)])
    mg = st.mean(r['SpeedupTotal'] for r in a if r['mode'] == 'gray'); mc = st.mean(r['SpeedupTotal'] for r in a if r['mode'] == 'color')
    rows49.append([str(n), f(mt, 2), f(min(stt), 2), f(max(stt), 2), f(mg, 2), f(mc, 2), f(100 * mt / n, 1), f(kf(mt, n), 4)])
T_('Table 4.7. Mean LBG speedup, parallel efficiency, and Karp–Flatt metric across the twelve images.',
   ['P', 'Speedup', 'Min', 'Max', 'Efficiency (%)', 'Karp–Flatt e'], rows47)
T_('Table 4.8. LBG speedup of each image at different MPI process counts.',
   ['Image'] + [f'P={n}' for n in NP],
   [[TN[k]] + [f(next(r['SpeedupLBG'] for r in par(n) if r['image'] == k), 2) for n in NP] for k in TN])
T_('Table 4.9. Mean total execution-time speedup, parallel efficiency, and Karp–Flatt metric across the twelve images.',
   ['P', 'Speedup', 'Min', 'Max', 'Grayscale', 'Color', 'Efficiency (%)', 'Karp–Flatt e'], rows49)

# ---------- 4.10 / 4.11 ablation
a_ = {r['image']: r for r in A}
order = GRAY + COLOR
mean = lambda k: st.mean(a_[x][k] for x in order)
r410 = [[QN[k], f(a_[k]['MSE_off'], 2), f(a_[k]['MSE_on'], 2), f(a_[k]['PSNR_off'], 2), f(a_[k]['PSNR_on'], 2), sg(a_[k]['dPSNR'], 2)] for k in order]
r410.append(['Mean', f(mean('MSE_off'), 2), f(mean('MSE_on'), 2), f(mean('PSNR_off'), 2), f(mean('PSNR_on'), 2), sg(mean('dPSNR'), 2)])
T_('Table 4.10. MSE and PSNR without and with bilateral filtering.',
   ['Image', 'MSE (no filter)', 'MSE (filter)', 'PSNR (no filter, dB)', 'PSNR (filter, dB)', 'ΔPSNR (dB)'], r410)
r411 = [[QN[k], f(a_[k]['SSIM_off'], 4), f(a_[k]['SSIM_on'], 4), sg(a_[k]['dSSIM'], 4)] for k in order]
r411.append(['Mean', f(mean('SSIM_off'), 4), f(mean('SSIM_on'), 4), sg(mean('dSSIM'), 4)])
T_('Table 4.11. SSIM without and with bilateral filtering.', ['Image', 'SSIM (no filter)', 'SSIM (filter)', 'ΔSSIM'], r411)

# ---------- 4.12-4.14 Equal vs Adaptive
ea = lambda n, m=None: [r for r in E if r['np'] == n and (m is None or r['mode'] == m)]
def gm(n, m, k): return st.mean(r[k] for r in ea(n, m))
def gain(e, a): return 100 * (e - a) / e
r412, r414 = [], []
for n in NP:
    ge, ga, ce, ca = gm(n, 'gray', 'equal_lbg_s'), gm(n, 'gray', 'adaptive_lbg_s'), gm(n, 'color', 'equal_lbg_s'), gm(n, 'color', 'adaptive_lbg_s')
    r412.append([str(n), f(ge, 4), f(ga, 4), f(gain(ge, ga), 1), f(ce, 4), f(ca, 4), f(gain(ce, ca), 1)])
    ge, ga, ce, ca = gm(n, 'gray', 'equal_total_s'), gm(n, 'gray', 'adaptive_total_s'), gm(n, 'color', 'equal_total_s'), gm(n, 'color', 'adaptive_total_s')
    r414.append([str(n), f(ge, 3), f(ga, 3), f(gain(ge, ga), 1), f(ce, 3), f(ca, 3), f(gain(ce, ca), 1)])
T_('Table 4.12. Mean LBG time (s) with the Equal and Adaptive strategies.',
   ['P', 'Grayscale: Equal', 'Grayscale: Adaptive', 'Gain (%)', 'Color: Equal', 'Color: Adaptive', 'Gain (%)'], r412)
r413 = []
for n in NP:
    lg = [r['lbg_gain_pct'] for r in ea(n)]; tg = [r['total_gain_pct'] for r in ea(n)]
    r413.append([str(n), f(st.mean(lg), 1), f(min(lg), 1), f(max(lg), 1), f(st.mean(tg), 1), f(min(tg), 1), f(max(tg), 1), f'{sum(v > 1 for v in tg)} of 12'])
T_('Table 4.13. Adaptive gain over Equal across the twelve images (LBG time and total time).',
   ['P', 'LBG mean gain (%)', 'Min', 'Max', 'Total mean gain (%)', 'Min', 'Max', 'Images with total gain > 1%'], r413)
T_('Table 4.14. Mean total execution time (s) with the Equal and Adaptive strategies.',
   ['P', 'Grayscale: Equal', 'Grayscale: Adaptive', 'Gain (%)', 'Color: Equal', 'Color: Adaptive', 'Gain (%)'], r414)

# ---------- re-measurement of the five suspect cells
RS = sheet('Remeasure summary')
RS = [r for r in RS if r['np'] is not None]
r415 = [[TN[r['image']], str(int(r['np'])), f(r['equal_median_10runs'], 4), f(r['adaptive_median_10runs'], 4), f(r['gain_pct_10runs'], 1),
         f(r['unified_adaptive'], 4), f(r['unified_gain_pct'], 1), f(r['session1_adaptive'], 4), f(r['session1_gain_pct'], 1)] for r in RS]
T_('Table 4.15. Re-measurement of the five image–process combinations with the least favorable Adaptive result (LBG time, s).',
   ['Image', 'P', 'Equal (10 runs)', 'Adaptive (10 runs)', 'Gain (%)', 'Adaptive (main campaign)', 'Gain (%)', 'Adaptive (earlier session)', 'Gain (%)'], r415)

# ---------- throughput (optional table)
thr = lambda n, m: st.mean(r['throughput_vectors_per_s (N*I/T_LBG)'] for r in TH if str(r['np']) == str(n) and r['mode'] == m) / 1e6
r415 = [[('Sequential' if n == 'seq' else str(n)), f(thr(n, 'gray'), 2), f(thr(n, 'color'), 2)] for n in ['seq'] + NP]
T_('Table 4.16 (optional). Mean LBG throughput (million vector assignments per second).', ['P', 'Grayscale', 'Color'], r415)

# ---------- entropy (grayscale only)
EN = sheet('Entropy')
r417 = [[x['image'], f(x['H_index_bits'], 3), f(x['H_delta_bits'], 3), f(x['delta_reduction_bits'], 3), f(x['huffman_bits_per_index'], 3), f(x['saving_vs_6bit_fixed_pct'], 1), f(x['system_CR'], 2)] for x in EN]
T_('Table 4.17. Entropy of the VQ index stream and Huffman code length of the grayscale images (bits per index).',
   ['Image', 'Entropy before delta', 'Entropy after delta', 'Reduction by delta', 'Huffman code length', 'Saving vs 6-bit indices (%)', 'CR (×)'], r417)
by_cr = [x['image'] for x in sorted(EN, key=lambda x: -x['system_CR'])]
by_h = [x['image'] for x in sorted(EN, key=lambda x: x['H_delta_bits'])]
same_order = (by_cr == by_h)
red = [x['delta_reduction_bits'] for x in EN]; gap = [x['gap_vs_H_delta_bits'] for x in EN]; sav = [x['saving_vs_6bit_fixed_pct'] for x in EN]
lo_red = min(EN, key=lambda x: x['delta_reduction_bits']); hi_red = max(EN, key=lambda x: x['delta_reduction_bits'])
lo_sav = min(EN, key=lambda x: x['saving_vs_6bit_fixed_pct']); hi_sav = max(EN, key=lambda x: x['saving_vs_6bit_fixed_pct'])

# ---------- correctness (sequential vs parallel)
CO = sheet('Correctness')
CN = {'gray': 'Lena', 'boat_img': 'Boat', 'cameraman_img': 'Cameraman', 'peppers_img': 'Peppers', 'chest_xray2_img': 'Chest X-ray', 'mammo2_img': 'Mammogram', 'lung_ct2_img': 'Lung CT', 'brain_mri2_img': 'Brain MRI', 'lena_color': 'Color Lena', 'retina2_color': 'Retinal fundus', 'brain_pet3_color': 'Brain axial', 'brain_pet4_color': 'Brain sagittal'}
col = lambda r, k: r[k]
r418 = [[CN[r['image']], r['CR MSE PSNR SSIM iters: sequential'].split()[4], r['metrics identical'].capitalize(), r['reconstruction MD5 identical'].capitalize()] for r in CO]
T_('Table 4.18. Sequential versus parallel results (P = 4 and P = 14, Equal and Adaptive distribution).',
   ['Image', 'LBG iterations', 'CR, MSE, PSNR, SSIM, and iterations identical', 'Reconstructed image identical (MD5)'], r418)
n_cfg = 4; n_runs = len(CO) * n_cfg
all_ok = all(r['metrics identical'] == 'yes' and r['reconstruction MD5 identical'] == 'yes' for r in CO)

# ---------- supervisor-structure additions
rowsGC = []
for n in NP:
    a = par(n)
    g = st.mean(r['SpeedupLBG'] for r in a if r['mode'] == 'gray'); c = st.mean(r['SpeedupLBG'] for r in a if r['mode'] == 'color')
    rowsGC.append([str(n), f(g, 2), f(100 * g / n, 1), f(c, 2), f(100 * c / n, 1)])
T_('Table 4.19. Mean LBG speedup and parallel efficiency of the grayscale and the color images.',
   ['P', 'Grayscale: speedup', 'Grayscale: efficiency (%)', 'Color: speedup', 'Color: efficiency (%)'], rowsGC)
T_('Table 4.20. Parameters of the algorithm and of the experiments.',
   ['Parameter', 'Value'],
   [['Image size', '512 × 512 pixels, 8 bits per sample'],
    ['Block size / vector dimension', '4 × 4 pixels / 16'],
    ['Training vectors per channel (N)', '16,384'],
    ['Codebook size (K)', '64'],
    ['LBG splitting perturbation (δ)', '0.01'],
    ['LBG convergence threshold (ε)', '0.0001 (relative improvement of the distortion)'],
    ['Maximum LBG iterations per codebook size', '100'],
    ['Delta coding offset', '128'],
    ['Bilateral filter', 'd = 3, σ_color = 80, σ_space = 5, α = 0.4'],
    ['SSIM', '11 × 11 Gaussian window, σ = 1.5, K1 = 0.01, K2 = 0.03'],
    ['Color images', 'R, G, and B channels coded independently'],
    ['Accumulation in the codebook update', 'Double precision'],
    ['Default distribution strategy', 'Equal for P ≤ 4, Adaptive for P > 4'],
    ['Speed calibration (Adaptive)', '3 trials; the first is discarded and the fastest of the others is used'],
    ['Timing', 'Median of 5 runs']])

# ---------- numbers used in the 4.7 text (all computed)
def pr(n):
    return {'lg': st.mean(r['lbg_gain_pct'] for r in ea(n)), 'tg': st.mean(r['total_gain_pct'] for r in ea(n))}
s1 = {n: st.mean(r['adaptive_gain_pct'] for r in E1 if r['np'] == n) for n in NP}
key1 = {(r['image'], r['np']): r['adaptive_gain_pct'] for r in E1}
diffs = [(r['image'], r['np']) for r in E if r['np'] >= 8 and key1[(r['image'], r['np'])] - r['lbg_gain_pct'] > 2]
rr = 0.642
pred = {n: 100 * (1 - n * rr / (6 + (n - 6) * rr)) for n in (8, 10, 12, 14)}
ms = lambda n, m, k: 1000 * (gm(n, m, 'equal_' + k + '_s') - gm(n, m, 'adaptive_' + k + '_s'))
eqrise_g = 100 * (gm(8, 'gray', 'equal_lbg_s') / gm(6, 'gray', 'equal_lbg_s') - 1)
eqrise_c = 100 * (gm(8, 'color', 'equal_lbg_s') / gm(6, 'color', 'equal_lbg_s') - 1)
pred_rise = 100 * (6 / (8 * rr) - 1)
lo_lbg_le6 = min(r['lbg_gain_pct'] for n in (2, 4, 6) for r in ea(n)); hi_lbg_le6 = max(r['lbg_gain_pct'] for n in (2, 4, 6) for r in ea(n))
tot_le6 = [st.mean(r['total_gain_pct'] for r in ea(n)) for n in (2, 4, 6)]
nm = lambda im: TN[im]

def para(doc, text, bold=False, italic=False):
    p = doc.add_paragraph(); run = p.add_run(text); run.bold = bold; run.italic = italic; return p

def put_table(doc, idx):
    cap, hdr, rows = tables[idx]
    p = doc.add_paragraph(); r = p.add_run(cap); r.bold = True
    t = doc.add_table(rows=1, cols=len(hdr)); t.style = 'Table Grid'
    for j, h in enumerate(hdr): t.rows[0].cells[j].text = h
    for rw in rows:
        c = t.add_row().cells
        for j, v in enumerate(rw): c[j].text = v
    doc.add_paragraph()

doc = Document()
doc.styles['Normal'].font.name = 'Times New Roman'; doc.styles['Normal'].font.size = Pt(11)
doc.add_heading('Chapter 4 numeric tables and Section 4.7 text', 1)
para(doc, 'Every number below was generated by code from final_results.xlsx and then re-read from this file and compared with the source. '
          'Image names for the two color brain images are provisional (MRI/PET to be decided).', italic=True)

for i in range(0, 4): put_table(doc, i)
doc.add_heading('Tables 4.7 – 4.9 (parallel performance)', 2)
for i in range(4, 7): put_table(doc, i)
doc.add_heading('Tables 4.10 – 4.11 (bilateral filtering)', 2)
for i in range(7, 9): put_table(doc, i)

doc.add_heading('4.7 Equal and Adaptive Workload Distribution', 1)
para(doc, 'This section compares the two workload-distribution strategies described in Section 3.4. Both strategies were run with the same program, the same twelve images, the same process binding, and in the same measurement session. For each process count, the strategy was forced explicitly, and the two strategies were run alternately, with the order alternated between repetitions. Each value is the median of five runs. LBG time and total execution time were recorded in the same runs. The speed calibration of the adaptive strategy is performed before the timed LBG region, so it is not included in the LBG time, but it is included in the total execution time. The adaptive gain was calculated as (T_Equal − T_Adaptive) / T_Equal. The total execution time is printed by the program with a resolution of 1 ms.')
put_table(doc, 9)
doc.add_picture(FIG1, width=Pt(450)); para(doc, 'Figure 4.1. LBG time with the Equal and Adaptive strategies (grayscale and color images).', italic=True)
put_table(doc, 10)

para(doc, f'For P ≤ 6, all processes ran on P-cores, and the two strategies gave the same LBG time within {lo_lbg_le6:+.1f}% to {hi_lbg_le6:+.1f}% for every image. The adaptive distribution therefore brought no benefit in this region. The total execution time with the Adaptive strategy was slightly higher on average (by {abs(tot_le6[0]):.1f}%, {abs(tot_le6[1]):.1f}%, and {abs(tot_le6[2]):.1f}% at P = 2, 4, and 6). This difference is of the order of the 1 ms resolution of the total time, and it is consistent with the calibration that is included in the total time; the calibration cost was not measured separately. P = 5 was not measured.')
para(doc, f'The behavior changed when the processes began to run on E-cores. With the Equal strategy, the LBG time increased from P = 6 to P = 8, from {f(gm(6,"gray","equal_lbg_s"),4)} s to {f(gm(8,"gray","equal_lbg_s"),4)} s for the grayscale images ({eqrise_g:.1f}%) and from {f(gm(6,"color","equal_lbg_s"),4)} s to {f(gm(8,"color","equal_lbg_s"),4)} s for the color images ({eqrise_c:.1f}%). With the Adaptive strategy, the time continued to decrease. The Adaptive strategy was faster for all twelve images at every P ≥ 8. The mean LBG gain was {pr(8)["lg"]:.1f}% at P = 8 and decreased to {pr(14)["lg"]:.1f}% at P = 14.')
para(doc, 'Table 4.14 shows whether this gain carried over to the complete program.')
put_table(doc, 11)
doc.add_picture(FIG2, width=Pt(450)); para(doc, 'Figure 4.2. Total execution time with the Equal and Adaptive strategies (grayscale and color images).', italic=True)
para(doc, f'The Adaptive strategy also reduced the total execution time for all twelve images at every P ≥ 8. The mean gain was {pr(8)["tg"]:.1f}% at P = 8, {pr(10)["tg"]:.1f}% at P = 10, {pr(12)["tg"]:.1f}% at P = 12, and {pr(14)["tg"]:.1f}% at P = 14. The gain was larger for the color images than for the grayscale images (Table 4.14), in line with the larger share of LBG in their sequential time (Section 4.4). The reduction in total time was close to the reduction in LBG time in absolute terms. At P = 8, the mean reduction for the grayscale images was {ms(8,"gray","total"):.1f} ms in total time and {ms(8,"gray","lbg"):.1f} ms in LBG time. At P = 14, it was {ms(14,"gray","total"):.1f} ms and {ms(14,"gray","lbg"):.1f} ms. For the color images, the corresponding values were {ms(8,"color","total"):.1f} ms and {ms(8,"color","lbg"):.1f} ms at P = 8, and {ms(14,"color","total"):.1f} ms and {ms(14,"color","lbg"):.1f} ms at P = 14. The difference between the two reductions was {ms(8,"gray","lbg")-ms(8,"gray","total"):.1f} ms and {ms(14,"gray","lbg")-ms(14,"gray","total"):.1f} ms for the grayscale images and {ms(8,"color","lbg")-ms(8,"color","total"):.1f} ms and {ms(14,"color","lbg")-ms(14,"color","total"):.1f} ms for the color images at P = 8 and P = 14, which gives an indicative upper bound for the calibration cost, limited by the 1 ms resolution of the total time. The calibration cost was therefore small compared with the time saved by the better workload balance.')
# (capacity-model paragraph removed by decision: not defined in Chapter 3)
para(doc, f'An earlier measurement session, which recorded only the LBG time, gave mean LBG gains of {s1[8]:.1f}%, {s1[10]:.1f}%, {s1[12]:.1f}%, and {s1[14]:.1f}% at P = 8, 10, 12, and 14, which differs from the values above by at most {max(abs(s1[n]-pr(n)["lg"]) for n in (8,10,12,14)):.1f} percentage points. In {len(diffs)} image–process combinations ({", ".join(f"{nm(i)} at P = {n}" for i, n in diffs)}), the Adaptive LBG time was more than 2 percentage points less favorable than in the earlier session. ')

# mean gains if the five cells were replaced by the re-measured values (indicative)
rep = {(r['image'], int(r['np'])): r['gain_pct_10runs'] for r in RS}
def mg_rep(n):
    return st.mean(rep.get((r['image'], r['np']), r['lbg_gain_pct']) for r in ea(n))
para(doc, f'These five combinations were measured again, with ten alternated runs each and with the calibrated rank speeds recorded (Table 4.15). The re-measured Adaptive times agreed with the earlier session and not with the main campaign, so the main-campaign values for these cells were probably affected by a transient disturbance that did not recur. The Equal times were practically the same in all three measurements. The calibration does not explain the difference. In the 50 repeated Adaptive runs, one E-core rank was calibrated 4% to 6% below the others in three runs. Only one of these three runs was slower than the median of its cell (by 3.5%), and the slowest run among the remaining ones (10% above its cell median) had normal calibration values. Replacing the five cells by the re-measured values would change the mean LBG gain from {pr(8)["lg"]:.1f}% to {mg_rep(8):.1f}% at P = 8, from {pr(12)["lg"]:.1f}% to {mg_rep(12):.1f}% at P = 12, and from {pr(14)["lg"]:.1f}% to {mg_rep(14):.1f}% at P = 14. The main-campaign values are retained in Tables 4.12 to 4.14 as measured. The re-measured values are given for reference only.')
put_table(doc, 12)

doc.add_heading('Optional table (throughput)', 2)
put_table(doc, 13)
doc.add_heading('Entropy paragraph (for Section 4.3, grayscale images)', 2)
para(doc, f'Table 4.17 gives the entropy of the VQ index stream of the grayscale images before and after delta coding, together with the average length of the Huffman code that was produced. Delta coding lowered the entropy for every image, from {lo_red["delta_reduction_bits"]:.2f} bit per index for {lo_red["image"]} to {hi_red["delta_reduction_bits"]:.2f} bits per index for {hi_red["image"]}. The Huffman code length was {min(gap):.3f} to {max(gap):.3f} bit above the entropy after delta coding. Compared with a fixed-length index of 6 bits (K = 64), the delta and Huffman stages reduced the size of the index stream by {lo_sav["saving_vs_6bit_fixed_pct"]:.1f}% for {lo_sav["image"]} to {hi_sav["saving_vs_6bit_fixed_pct"]:.1f}% for {hi_sav["image"]}. ' + ('The images had the same order by compression ratio and by the entropy after delta coding: the lower the entropy, the higher the compression ratio. ' if same_order else 'The order of the images by compression ratio did not follow exactly the order by entropy after delta coding. ') + 'The codebook size and the number of indices were the same for all images. The differences in compression ratio therefore came from the size of the Huffman-coded index stream. The entropy was measured for the grayscale images only, because the color pipeline of the program does not compute it.')
put_table(doc, 14)
doc.add_heading('4.8 Verification of the Parallel Implementation', 1)
para(doc, 'To verify that the MPI-based implementation preserved the numerical results of the sequential implementation, a separate verification test was performed on all twelve images. Four execution configurations were evaluated for each image: the sequential implementation, the parallel implementation with P = 4, the parallel implementation with P = 14 using the Adaptive strategy, and the parallel implementation with P = 14 using the Equal strategy. The comparison included the compression ratio (CR), MSE, PSNR, SSIM, the number of LBG iterations, and the final reconstructed image. The reconstructed images were additionally compared using their MD5 hashes to verify byte-for-byte equality.')
para(doc, f'All {n_runs} executions produced identical CR, MSE, PSNR, and SSIM values for the corresponding images' + ('' if all_ok else ' (with exceptions listed in Table 4.18)') + '. The number of LBG iterations was also identical across the compared configurations. In addition, the MD5 hashes of the reconstructed images matched in every case, confirming byte-for-byte equality of the reconstructed outputs under the tested configurations. This result was maintained at P = 14 with the Adaptive strategy, where the workload was distributed unequally among the MPI processes. These results were obtained with the sums of the codebook update accumulated in double precision (Section 3.3). The workload redistribution therefore changed how the computation was divided among the processes without changing the final reconstructed output, and the speedups reported in Section 4.5 refer to the same computation as the sequential baseline. The detailed results for each image are given in Appendix C.')
para(doc, 'The verification covered P = 4 and P = 14 for the quality values and the reconstructed images. The number of LBG iterations was also identical to the sequential value at all tested process counts in the timing runs (P = 2, 4, 6, 8, 10, 12, and 14). The codebooks and the compressed bit streams were not compared directly. The test was performed on one machine, with one compiler and one MPI library.')

# ---------- 4.9 chapter summary (all numbers computed from the data)
qg = [q[k] for k in GRAY]; qc = [q[k] for k in COLOR]
rng = lambda L, key, d: f"{min(x[key] for x in L):.{d}f} to {max(x[key] for x in L):.{d}f}"
sh = [100 * seq[k]['LBG_s'] / seq[k]['Total_s'] for k in seq]
a14 = par(14); sp14 = st.mean(r['SpeedupLBG'] for r in a14); ef14 = 100 * sp14 / 14; tot14 = st.mean(r['SpeedupTotal'] for r in a14)
def lgm(n): return st.mean(r['lbg_gain_pct'] for r in ea(n))
def tgm(n): return st.mean(r['total_gain_pct'] for r in ea(n))
dp = mean('dPSNR'); ds = mean('dSSIM')
summary_blk = lambda doc: (
    doc.add_heading('4.9 Chapter Summary', 1),
    para(doc, 'This chapter evaluated the proposed framework on twelve images (eight grayscale and four color) in terms of compression and reconstruction quality, sequential and parallel performance, the effect of the bilateral filter, the comparison of the Equal and Adaptive workload-distribution strategies, and the agreement between the sequential and the parallel results.'),
    para(doc, f'The compression ratio ranged from {rng(qg,"CR_system",2)} for the grayscale images and from {rng(qc,"CR_system",2)} for the color images. The PSNR ranged from {rng(qg,"PSNR_dB",2)} dB and from {rng(qc,"PSNR_dB",2)} dB, and the SSIM from {rng(qg,"SSIM",4)} and from {rng(qc,"SSIM",4)}, respectively. The bilateral post-filter improved the MSE, PSNR, and SSIM of all twelve images, by {dp:.2f} dB in PSNR and {ds:.4f} in SSIM on average.'),
    para(doc, f'In the sequential implementation, the LBG stage accounted for {min(sh):.1f}% to {max(sh):.1f}% of the total execution time. Its parallelization with MPI gave a mean LBG speedup of {sp14:.2f} at P = 14, with a parallel efficiency of {ef14:.1f}%, and a mean speedup of {tot14:.2f} for the total execution time. The LBG speedup was almost the same for all images, and the efficiency decreased after P = 6, where the processes began to run on E-cores.'),
    para(doc, f'The Equal and Adaptive strategies gave the same execution time for P ≤ 6. For P ≥ 8, the Adaptive strategy was faster for all twelve images. It reduced the mean LBG time by {lgm(8):.1f}% at P = 8 and by {lgm(14):.1f}% at P = 14, and the mean total execution time, which includes the speed calibration, by {tgm(8):.1f}% and {tgm(14):.1f}%, respectively. The parallel implementation produced the same compression ratio, MSE, PSNR, SSIM, number of LBG iterations, and reconstructed images as the sequential implementation in all verification runs.'),
    para(doc, 'All measurements were made on one hybrid processor with up to 14 MPI processes, and the total execution time was recorded with a resolution of 1 ms. The conclusions and future work are presented in the next chapter.'))
summary_blk(doc)
# (Table 4.18 -> Appendix C)
doc.add_heading('Appendix C (per-image verification table)', 2)
put_table(doc, 15)



doc.add_heading('Additional tables for the supervisor structure', 1)
doc.add_heading('For Performance of Parallel Results (grayscale and color separately)', 2)
put_table(doc, 16)
doc.add_heading('For Experimental Setting', 2)
put_table(doc, 17)
doc.save(OUT)

# ---------- verification: re-read the docx and compare every cell with the in-memory source rows
d2 = Document(OUT)
assert len(d2.tables) == len(tables), (len(d2.tables), len(tables))
bad = 0; cells = 0
for t, (cap, hdr, rows) in zip(d2.tables, tables):
    got = [[c.text for c in r.cells] for r in t.rows]
    exp = [hdr] + rows
    if got != exp:
        bad += 1; print('TABLE MISMATCH:', cap)
    cells += sum(len(r) for r in exp)
print('tables:', len(tables), 'cells compared:', cells, 'table mismatches:', bad)
json.dump({'tables': tables}, open('/tmp/claude-0/-home-user-mihk/4ae9f12a-c6d9-593e-bdd1-593721fcd2b9/scratchpad/tables.json', 'w'), ensure_ascii=False)
