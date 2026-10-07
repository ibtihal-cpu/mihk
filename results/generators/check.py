"""Internal-consistency checks of final_results.xlsx (detect transcription errors)."""
import math, csv
from openpyxl import load_workbook

wb = load_workbook('/home/user/mihk/results/final_results.xlsx')
def sheet(name):
    ws = wb[name]
    hdr = [c.value for c in ws[1]]
    out = []
    for r in ws.iter_rows(min_row=2):
        v = [c.value for c in r]
        if v[0] is None:
            continue
        out.append(dict(zip(hdr, v)))
    return out

bad = 0
def flag(msg):
    global bad
    bad += 1
    print('MISMATCH:', msg)

# 1) Quality: PSNR must equal 10*log10(255^2/MSE); BPP = 8/CR
Q = sheet('Quality')
for r in Q:
    p = 10 * math.log10(255 ** 2 / r['MSE'])
    if abs(p - r['PSNR_dB']) > 0.011:
        flag(f"Quality PSNR {r['image']}: table {r['PSNR_dB']} vs from MSE {p:.3f}")
    if abs(8 / r['CR_system'] - r['BPP']) > 0.00051:
        flag(f"Quality BPP {r['image']}: {r['BPP']} vs {8 / r['CR_system']:.4f}")
print('quality rows:', len(Q))

# 2) Ablation: PSNR from MSE (off and on), dPSNR, dSSIM
A = sheet('Filter ablation')
for r in A:
    for k_m, k_p in (('MSE_off', 'PSNR_off'), ('MSE_on', 'PSNR_on')):
        p = 10 * math.log10(255 ** 2 / r[k_m])
        if abs(p - r[k_p]) > 0.011:
            flag(f"Ablation {r['image']} {k_p}: {r[k_p]} vs {p:.3f}")
    if abs((r['PSNR_on'] - r['PSNR_off']) - r['dPSNR']) > 0.0101:
        flag(f"Ablation {r['image']} dPSNR")
    if abs((r['SSIM_on'] - r['SSIM_off']) - r['dSSIM']) > 0.00011:
        flag(f"Ablation {r['image']} dSSIM")
    q = [x for x in Q if x['image'] == r['image']][0]
    if abs(q['MSE'] - r['MSE_on']) > 0.001 or abs(q['PSNR_dB'] - r['PSNR_on']) > 0.001 or abs(q['SSIM'] - r['SSIM_on']) > 0.00001:
        flag(f"Ablation 'on' != Quality for {r['image']}")
print('ablation rows:', len(A))

# 3) Timing: speedups / efficiency / per-iter speedup recomputed (rounded values in sheet)
T = sheet('Timing (all)')
seq = {r['image']: r for r in T if str(r['np']) == 'seq'}
for r in T:
    if str(r['np']) == 'seq':
        continue
    s = seq[r['image']]
    n = int(r['np'])
    sl = s['LBG_s'] / r['LBG_s']
    st = s['Total_s'] / r['Total_s']
    ef = 100 * sl / n
    if abs(sl - r['SpeedupLBG']) > 0.011: flag(f"Timing SpeedupLBG {r['image']} P={n}: {r['SpeedupLBG']} vs {sl:.3f}")
    if abs(st - r['SpeedupTotal']) > 0.011: flag(f"Timing SpeedupTotal {r['image']} P={n}: {r['SpeedupTotal']} vs {st:.3f}")
    if abs(ef - r['Eff%']) > 0.51: flag(f"Timing Eff {r['image']} P={n}: {r['Eff%']} vs {ef:.2f}")
    if r['iters'] != s['iters']: flag(f"iterations differ {r['image']} P={n}")
print('timing rows:', len(T))

# 4) Equal/Adaptive unified: gain == 100*(eq-ad)/eq (rounded to .1; inputs rounded -> allow 0.35 for total, 0.2 for lbg)
E = sheet('EqAd unified (LBG+Total)')
for r in E:
    g = 100 * (r['equal_lbg_s'] - r['adaptive_lbg_s']) / r['equal_lbg_s']
    if abs(g - r['lbg_gain_pct']) > 0.3: flag(f"EqAd LBG gain {r['image']} P={r['np']}: {r['lbg_gain_pct']} vs {g:.2f}")
    gt = 100 * (r['equal_total_s'] - r['adaptive_total_s']) / r['equal_total_s']
    if abs(gt - r['total_gain_pct']) > 0.6: flag(f"EqAd Total gain {r['image']} P={r['np']}: {r['total_gain_pct']} vs {gt:.2f}")
print('eq/ad rows:', len(E))

# 5) unified sheet == pasted CSV
P = '/tmp/claude-0/-home-user-mihk/4ae9f12a-c6d9-593e-bdd1-593721fcd2b9/scratchpad/eqt.csv'
C = list(csv.DictReader(open(P)))
if len(C) != len(E): flag('row count differs from pasted csv')
for c, e in zip(C, E):
    if (c['image'], int(c['np'])) != (e['image'], int(e['np'])): flag(f"order {c['image']} {c['np']}")
    for k_c, k_e in (('eq_lbg', 'equal_lbg_s'), ('ad_lbg', 'adaptive_lbg_s'), ('lbg_gain_pct', 'lbg_gain_pct'),
                     ('eq_total', 'equal_total_s'), ('ad_total', 'adaptive_total_s'), ('total_gain_pct', 'total_gain_pct')):
        if abs(float(c[k_c]) - e[k_e]) > 1e-9: flag(f"csv vs sheet {c['image']} P={c['np']} {k_e}")

print('TOTAL MISMATCHES:', bad)
