import csv, collections, statistics as st
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
INK="#1F1A33";PURPLE="#6B4FA3";MAG="#E0457B";TEAL="#2A9D8F";ORG="#E07B22"
rows=[r for r in csv.DictReader(open("../final_campaign/timing_final.csv")) if r["np"]!="seq"]
d=collections.defaultdict(list)
for r in rows: d[int(r["np"])].append((float(r["SpeedupLBG"]),float(r["Eff%"])))
P=sorted(d); S=[st.mean(x[0] for x in d[p]) for p in P]; lo=[min(x[0] for x in d[p]) for p in P]; hi=[max(x[0] for x in d[p]) for p in P]
E=[st.mean(x[1] for x in d[p]) for p in P]
def base(ax,ylab,col):
    ax.axvspan(0.9,6.5,color="#EFEAF8",zorder=0)
    ax.set_xlim(0.9,14.8);ax.set_xticks(P)
    ax.set_xlabel("Number of MPI processes (P)",fontsize=20);ax.set_ylabel(ylab,fontsize=20)
    ax.tick_params(labelsize=17);ax.grid(alpha=.3)
    for s_ in ("top","right"): ax.spines[s_].set_visible(False)
# ---- speedup ----
fig,ax=plt.subplots(figsize=(13.49,8.21),dpi=150); base(ax,"Speedup",PURPLE)
ax.text(1.2,15.3,"P-cores only (P ≤ 6)",fontsize=20,color=PURPLE,fontweight="bold",va="center")
ax.text(7.2,15.3,"P + E cores (P > 6)",fontsize=20,color=ORG,fontweight="bold",va="center")
ax.plot([2,14],[2,14],ls=":",color="#555",lw=2.8,label="Ideal linear speedup")
ax.errorbar(P,S,yerr=[[s-l for s,l in zip(S,lo)],[h-s for s,h in zip(S,hi)]],color=PURPLE,lw=4.2,marker="o",ms=13,capsize=4,label="Measured speedup (mean of 8 images, min–max)")
for p_,s in zip(P,S):
    ax.annotate(f"{s:.2f}×",(p_,s),textcoords="offset points",xytext=({2:(36,-14),14:(-4,-36)}.get(p_,(18,-34))),ha="center",fontsize=20,fontweight="bold",color=PURPLE)
ax.set_ylim(0,16.5);ax.set_yticks(range(0,16,2));ax.legend(loc="lower right",bbox_to_anchor=(0.99,0.04),fontsize=16,frameon=False)
plt.tight_layout();plt.savefig("assets/speedup_chart.png",facecolor="white");plt.close()
# ---- efficiency ----
fig,ax=plt.subplots(figsize=(13.49,8.21),dpi=150); base(ax,"Parallel efficiency (%)",MAG)
ax.text(1.2,6,"P-cores only (P ≤ 6)",fontsize=20,color=PURPLE,fontweight="bold",va="center")
ax.text(7.2,6,"P + E cores (P > 6)",fontsize=20,color=ORG,fontweight="bold",va="center")
ax.axhline(100,ls=":",color="#555",lw=2.8,label="Ideal efficiency (100%)")
ax.plot(P,E,color=MAG,lw=4.2,marker="s",ms=12,label="Measured efficiency (mean of 8 images)")
for p_,e in zip(P,E):
    ax.annotate(f"{e:.0f}%",(p_,e),textcoords="offset points",xytext=(0,-38),ha="center",fontsize=20,fontweight="bold",color=MAG)
ax.set_ylim(0,115);ax.set_yticks(range(0,101,20));ax.legend(loc="lower right",bbox_to_anchor=(0.99,0.12),fontsize=16,frameon=False)
plt.tight_layout();plt.savefig("assets/efficiency_chart.png",facecolor="white")
