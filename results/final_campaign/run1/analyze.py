import statistics as st, csv, math, collections
PS=[2,4,5,6,7,8,10,12,14]
MD5={'boat_gray':'c2ea58f4','cameraman_gray':'bf1cfba5','f16_color':'89e5893e','goldhill_color':'4759e062','lena_color':'4b404e9c','lena_gray':'d3507ac8','peppers_color2':'42b97bbd','peppers_gray':'a2e83676'}
raw=[]  # image,mode,strategy,np,rep,L,T
for l in open('data.txt'):
    if l.startswith('#') or not l.strip(): continue
    t=l.split(); im=t[0]; rep=int(t[1]); v=list(map(float,t[2:])); mode='gray' if 'gray' in im else 'color'
    raw.append((im,mode,'seq',1,rep,v[0],v[1]))
    for i,p in enumerate(PS):
        e=v[2+4*i:6+4*i]
        raw.append((im,mode,'equal',p,rep,e[0],e[1])); raw.append((im,mode,'adaptive',p,rep,e[2],e[3]))
with open('raw_reconstructed.csv','w') as f:
    f.write("image,mode,strategy,np,rep,LBG_s,Total_s,ok,md5\n")
    for r in raw: f.write(f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]},{r[5]},{r[6]},1,{MD5[r[0]]}\n")
print("rows",len(raw), "expected", 8*5*(1+2*len(PS)))
D=collections.defaultdict(list)
for im,mo,s,p,rep,L,T in raw: D[(im,s,p)].append((L,T))
def med(im,s,p,k): return st.median(x[k] for x in D[(im,s,p)])
def sd(im,s,p,k): return st.stdev(x[k] for x in D[(im,s,p)])
IM=sorted({r[0] for r in raw}); G=[i for i in IM if 'gray' in i]; C=[i for i in IM if 'color' in i]
# "auto" rule = Equal for P<=6, Adaptive for P>6 (the code used for the reported speedups)
def auto(p): return 'equal' if p<=6 else 'adaptive'
def S(im,p,k,strat=None):
    s=strat or auto(p); return med(im,'seq',1,k)/med(im,s,p,k)
def mean(xs): return sum(xs)/len(xs)
def KF(s,p): return (1/s-1/p)/(1-1/p)
out={}
print("\n=== TABLE A: mean speedup / efficiency / Karp-Flatt (rule: Equal P<=6, Adaptive P>6) ===")
for k,name in ((0,'LBG'),(1,'TOTAL')):
  for grp,ims in (('all 8',IM),('gray',G),('color',C)):
    print(f"-- {name} {grp}")
    for p in PS:
        ss=[S(i,p,k) for i in ims]; m=mean(ss); print(f"  P={p:2d}  S={m:5.2f} (min {min(ss):.2f} max {max(ss):.2f})  E={100*m/p:5.1f}%  KF={KF(m,p):.4f}")
print("\n=== TABLE B: seq medians (s) ===")
for i in IM: print(f"  {i:15s} LBG {med(i,'seq',1,0):.4f}  Total {med(i,'seq',1,1):.4f}  non-LBG {1000*(med(i,'seq',1,1)-med(i,'seq',1,0)):.2f} ms  LBG share {100*med(i,'seq',1,0)/med(i,'seq',1,1):.2f}%")
print("\n=== TABLE C: LBG share of Total at P=14 (Adaptive) ===")
for grp,ims in (('gray',G),('color',C)):
    print(grp, f"{mean([100*med(i,'adaptive',14,0)/med(i,'adaptive',14,1) for i in ims]):.1f}%", " seq:", f"{mean([100*med(i,'seq',1,0)/med(i,'seq',1,1) for i in ims]):.2f}%")
print("\n=== TABLE D: Equal vs Adaptive (LBG speedup, mean of 8 images) ===")
for p in PS:
    e=mean([S(i,p,0,'equal') for i in IM]); a=mean([S(i,p,0,'adaptive') for i in IM])
    te=mean([S(i,p,1,'equal') for i in IM]); ta=mean([S(i,p,1,'adaptive') for i in IM])
    print(f"  P={p:2d}  LBG Eq {e:5.2f} Ad {a:5.2f} diff {a-e:5.2f} | Total Eq {te:5.2f} Ad {ta:5.2f} diff {ta-te:5.2f}")
print("\n=== TABLE E: run-to-run sd of Total time at P=14 (Adaptive), ms; and of seq ===")
for i in IM: print(f"  {i:15s} seq sd {1000*sd(i,'seq',1,1):.2f} ms ({100*sd(i,'seq',1,1)/med(i,'seq',1,1):.2f}%)   P14 sd {1000*sd(i,'adaptive',14,1):.2f} ms ({100*sd(i,'adaptive',14,1)/med(i,'adaptive',14,1):.2f}%)")
print("\n=== TABLE F: speedup sd across images at P=14 (Total) ===")
for k,name in ((0,'LBG'),(1,'Total')):
    ss=[S(i,14,k) for i in IM]; print(name, f"mean {mean(ss):.2f} sd {st.stdev(ss):.3f}")
import json; json.dump({'ok':1},open('ok.json','w'))

print("\n=== MEDIANS CSV for Colab (rule: Equal P<=6, Adaptive P>6) ===")
lines=["image,mode,np,LBG_s,Total_s"]
for i in IM:
    m='gray' if 'gray' in i else 'color'
    lines.append(f"{i},{m},seq,{med(i,'seq',1,0):.4f},{med(i,'seq',1,1):.4f}")
    for p in [2,4,6,8,10,12,14]:
        s=auto(p); lines.append(f"{i},{m},{p},{med(i,s,p,0):.4f},{med(i,s,p,1):.4f}")
open('medians_auto.csv','w').write("\n".join(lines)+"\n"); print(len(lines)-1,"rows")
print("\nprecise Equal/Adaptive LBG (means):")
for p in [2,4,6,8,10,12,14]:
    e=mean([S(i,p,0,'equal') for i in IM]); a=mean([S(i,p,0,'adaptive') for i in IM]); print(p,f"{e:.4f} {a:.4f} {a-e:.4f}")
print("checksums:", f"{sum(r[5] for r in raw):.4f} {sum(r[6] for r in raw):.4f} {len(raw)}")
