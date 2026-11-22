import csv
from decimal import Decimal as D, ROUND_HALF_UP
def rd(x,dp): return str(D(x).quantize(D(1).scaleb(-dp),rounding=ROUND_HALF_UP))
def mean(vals): vals=[D(v) for v in vals]; return sum(vals)/len(vals)
def mq(vals,dp): return rd(mean(vals),dp)
def rows(f): return list(csv.DictReader(open(f)))
def md(h,r):
    print("| "+" | ".join(h)+" |"); print("|"+"|".join(["---"]*len(h))+"|")
    for x in r: print("| "+" | ".join(str(c) for c in x)+" |")
    print()
NM={'gray':'Lena','boat_img':'Boat','cameraman_img':'Cameraman','peppers_img':'Peppers','lena_color':'Lena (color)','peppers_color2':'Peppers (color)','f16_color':'F16','goldhill_color':'Gold Hill'}
GRAY=['gray','boat_img','cameraman_img','peppers_img']; COL=['lena_color','peppers_color2','f16_color','goldhill_color']
# --- param
P=rows('param.csv')
def prow(var,label):
    R=[r for r in P if r['variant']==var]
    return [label,mq([r['PSNR_dB'] for r in R],2),mq([r['SSIM'] for r in R],4),mq([r['system_CR'] for r in R],2),mq([r['LBG_iters'] for r in R],1),mq([r['LBG_time_median_s'] for r in R],4)]
H=['','PSNR (dB)','SSIM','CR','LBG iterations','LBG time (s)']
print("### Table 4.3 – block size (K=64), mean of 4 grayscale images"); md(['Block size']+H[1:],[prow('2x2/K64','2×2'),prow('4x4/K64','4×4'),prow('8x8/K64','8×8')])
print("### Table 4.4 – codebook size (4×4), mean of 4 grayscale images"); md(['K']+H[1:],[prow('4x4/K32','32'),prow('4x4/K64','64'),prow('4x4/K128','128')])
# --- quality
C=rows('corr.csv'); q={r['image']:r['seq'].split() for r in C}
print("### Table 4.5 – quality, grayscale (no post-filter)")
md(['Image','CR','MSE','PSNR (dB)','SSIM','LBG iterations'],[[NM[i]]+[q[i][0],q[i][1],q[i][2],q[i][3],q[i][4]] for i in GRAY]+[['Mean',mq([q[i][0] for i in GRAY],2),mq([q[i][1] for i in GRAY],2),mq([q[i][2] for i in GRAY],2),mq([q[i][3] for i in GRAY],4),mq([q[i][4] for i in GRAY],1)]])
print("### Table 4.6 – quality, color (RGB, no post-filter)")
md(['Image','RGB CR','RGB MSE','RGB PSNR (dB)','Mean SSIM','LBG iterations (R+G+B)'],[[NM[i]]+q[i] for i in COL]+[['Mean',mq([q[i][0] for i in COL],2),mq([q[i][1] for i in COL],2),mq([q[i][2] for i in COL],2),mq([q[i][3] for i in COL],4),mq([q[i][4] for i in COL],1)]])
# --- entropy
E={r['image']:r for r in rows('entropy.csv')}
er=[]
for i in GRAY:
    r=E[i]; red=D(r['H_index_bits'])-D(r['H_delta_bits']); gap=D(r['huffman_bits_per_index'])-D(r['H_delta_bits']); sav=(1-D(r['huffman_bits_per_index'])/6)*100
    er.append([NM[i],r['H_index_bits'],r['H_delta_bits'],rd(red,3),r['huffman_bits_per_index'],rd(gap,3),rd(sav,1)])
def mc(k): return [D(x[k]) for x in er]
er.append(['Mean']+[rd(sum(mc(k))/4,3) for k in (1,2,3,4,5)]+[rd(sum(mc(6))/4,1)])
print("### Table 4.7 – entropy and Huffman rate (bits per index), grayscale, K=64"); md(['Image','H before delta','H after delta','Reduction','Huffman bits/index','Huffman − H(delta)','Saving vs 6-bit (%)'],er)
# --- index coding CR
cr8=D(262144)/(1024+16384); cr6=D(262144)/(1024+12288)
ic=[]; 
for i in GRAY:
    c=D(E[i]['system_CR']); ic.append([NM[i],rd(cr8,2),rd(cr6,2),E[i]['system_CR'],rd((c/cr6-1)*100,1)])
ic.append(['Mean',rd(cr8,2),rd(cr6,2),mq([E[i]['system_CR'] for i in GRAY],2),rd(sum((D(E[i]['system_CR'])/cr6-1)*100 for i in GRAY)/4,1)])
print("### Table 4.8 – effect of index coding on system CR (codebook 1024 B included)"); md(['Image','Fixed 8-bit','Fixed 6-bit','Delta+Huffman','Gain over 6-bit (%)'],ic)
# --- timing
T=rows('timing.csv'); TI={}
for r in T: TI.setdefault(r['image'],{})[r['np']]=r
print("### Table 4.9/4.10 – sequential times")
for g,names in (('grayscale',GRAY),('color',COL)):
    sr=[]
    for i in names:
        s=TI[i]['seq']; sh=D(s['LBG_s'])/D(s['Total_s'])*100
        sr.append([NM[i],s['LBG_s'],s['Total_s'],rd(sh,1),s['iters']])
    shs=[D(TI[i]['seq']['LBG_s'])/D(TI[i]['seq']['Total_s'])*100 for i in names]
    sr.append(['Mean',mq([TI[i]['seq']['LBG_s'] for i in names],4),mq([TI[i]['seq']['Total_s'] for i in names],4),rd(sum(shs)/len(shs),1),mq([TI[i]['seq']['iters'] for i in names],1)])
    print(f"**{g}** (LBG share range {rd(min(shs),1)}–{rd(max(shs),1)}%)"); md(['Image','LBG time (s)','Total time (s)','LBG share (%)','LBG iterations'],sr)
NPS=['2','4','6','8','10','12','14']
def sp_table(key,title):
    print(f"### {title}")
    for g,names in (('grayscale (4)',GRAY),('color (4)',COL),('all 8',GRAY+COL)):
        out=[]
        for p in NPS:
            v=[TI[i][p][key] for i in names]; m=mean(v); n=D(p)
            kf=(1/m-1/n)/(1-1/n)
            out.append([p,rd(m,2),min(v,key=D),max(v,key=D),rd(m/n*100,1),rd(kf,3)])
        print(f"**{g}**"); md(['P','Mean speedup','Min','Max','Efficiency (%)','Karp–Flatt'],out)
sp_table('SpeedupLBG','LBG speedup (mean of per-image speedups)')
sp_table('SpeedupTotal','Total-time speedup')
# --- throughput
print("### Throughput (million vector-iterations per second) = N*I/T_LBG; N=16384 (x3 channels, I summed over channels for color)")
for g,names in (('grayscale',GRAY),('color',COL)):
    out=[]
    for p in ['seq']+NPS:
        th=[D(16384)*D(TI[i][p]['iters'])/D(TI[i][p]['LBG_s'])/D(10**6) for i in names]
        out.append([p,rd(sum(th)/len(th),3),rd(min(th),3),rd(max(th),3)])
    print(f"**{g}**"); md(['P','Mean Θ','Min','Max'],out)
# --- equal vs adaptive
EA=rows('eqad.csv'); 
print("### Equal vs Adaptive (mean of per-image values; gain = mean of per-image reductions)")
for g,names in (('grayscale (4)',GRAY),('color (4)',COL)):
    out=[]
    for p in NPS:
        R=[r for r in EA if r['image'] in names and r['np']==p]; assert len(R)==4
        nl=sum(1 for r in R if D(r['lbg_gain_pct'])>0); nt=sum(1 for r in R if D(r['total_gain_pct'])>0)
        out.append([p,mq([r['eq_lbg'] for r in R],4),mq([r['ad_lbg'] for r in R],4),mq([r['lbg_gain_pct'] for r in R],1),f"{nl}/4",mq([r['eq_total'] for r in R],4),mq([r['ad_total'] for r in R],4),mq([r['total_gain_pct'] for r in R],1),f"{nt}/4"])
    print(f"**{g}**"); md(['P','Equal LBG (s)','Adaptive LBG (s)','LBG reduction (%)','imgs faster','Equal Total (s)','Adaptive Total (s)','Total reduction (%)','imgs faster'],out)
out=[]
for p in NPS:
    R=[r for r in EA if r['np']==p]
    out.append([p,mq([r['lbg_gain_pct'] for r in R],1),mq([r['total_gain_pct'] for r in R],1)])
print("**all 8 images**"); md(['P','LBG reduction (%)','Total reduction (%)'],out)
# --- verification
print("### Table A.1 – verification (seq = P4 auto = P14 auto = P14 Equal; MD5 of reconstruction identical)")
md(['Image','Mode','CR','MSE','PSNR','SSIM','LBG iters','Metrics identical','MD5 identical'],[[NM[i],'gray' if i in GRAY else 'color']+q[i]+['yes','yes'] for i in GRAY+COL])
# --- jpeg
B=rows('base.csv'); print("### Table 4.D – JPEG / JPEG 2000 rate-matched (grayscale)")
md(['Image','Method','CR','PSNR (dB)','SSIM'],[[NM[r['image']],r['method'],r['CR'],r['PSNR_dB'],r['SSIM']] for r in B])
mm=[]
for m in ('Proposed','JPEG','JPEG 2000'):
    R=[r for r in B if r['method']==m]; mm.append([m,mq([r['CR'] for r in R],2),mq([r['PSNR_dB'] for r in R],2),mq([r['SSIM'] for r in R],4)])
print("**Mean of 4 images**"); md(['Method','CR','PSNR (dB)','SSIM'],mm)
# --- memory
M=rows('mem.csv'); print("### Memory (peak RSS, MB; median of 3)")
md(['Image','P','Max per process','Sum over processes'],[[NM[r['image']],r['P'],r['peak_rss_max_rank_MB'],r['peak_rss_sum_all_ranks_MB']] for r in M])
