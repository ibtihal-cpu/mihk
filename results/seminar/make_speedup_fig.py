import csv, collections, statistics as st
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
INK="#1F1A33";PURPLE="#6B4FA3";MAG="#E0457B";TEAL="#2A9D8F";ORG="#E07B22"
rows=[r for r in csv.DictReader(open("../final_campaign/timing_final.csv")) if r["np"]!="seq"]
d=collections.defaultdict(list)
for r in rows: d[int(r["np"])].append((float(r["SpeedupLBG"]),float(r["Eff%"])))
P=sorted(d); S=[st.mean(x[0] for x in d[p]) for p in P]; lo=[min(x[0] for x in d[p]) for p in P]; hi=[max(x[0] for x in d[p]) for p in P]
E=[st.mean(x[1] for x in d[p]) for p in P]
fig,ax=plt.subplots(figsize=(9.2,5.6),dpi=220)
ax.axvspan(1.5,6.5,color="#EFEAF8",zorder=0)
ax.text(2.0,14.2,"P-cores only (P ≤ 6)",fontsize=14,color=PURPLE,fontweight="bold",va="center")
ax.text(10.2,14.2,"P + E cores (P > 6)",fontsize=14,color=ORG,fontweight="bold",va="center")
ax.plot([2,14],[2,14],ls=":",color="#555",lw=2.2,label="Ideal linear speedup")
ax.errorbar(P,S,yerr=[[s-l for s,l in zip(S,lo)],[h-s for s,h in zip(S,hi)]],color=PURPLE,lw=3.2,marker="o",ms=10,capsize=4,label="Measured LBG speedup (mean of 8 images, min–max)")
for p,s,e in zip(P,S,E):
    ax.annotate(f"{s:.2f}×",(p,s),textcoords="offset points",xytext=(0,14),ha="center",fontsize=13,fontweight="bold",color=PURPLE)
    ax.annotate(f"{e:.0f}%",(p,s),textcoords="offset points",xytext=(0,-26),ha="center",fontsize=12,color=MAG,fontweight="bold")
ax.set_xlim(1.5,14.6);ax.set_ylim(0,15);ax.set_xticks(P)
ax.set_xlabel("Number of MPI processes (P)",fontsize=15);ax.set_ylabel("Speedup",fontsize=15)
ax.tick_params(labelsize=13);ax.grid(alpha=.3)
for s in ("top","right"): ax.spines[s].set_visible(False)
h,l=ax.get_legend_handles_labels();ax.legend(h,l,loc="lower right",fontsize=12,frameon=False)
ax.text(14.5,2.9,"pink % = parallel efficiency",fontsize=12,color=MAG,ha="right",fontweight="bold")
plt.tight_layout();plt.savefig("assets/speedup_chart.png",facecolor="white")
