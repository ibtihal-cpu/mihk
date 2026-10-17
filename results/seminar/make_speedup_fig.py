import csv, collections, statistics as st
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
INK="#1F1A33";PURPLE="#6B4FA3";MAG="#E0457B";TEAL="#2A9D8F";ORG="#E07B22"
rows=[r for r in csv.DictReader(open("../final_campaign/timing_final.csv")) if r["np"]!="seq"]
d=collections.defaultdict(list)
for r in rows: d[int(r["np"])].append((float(r["SpeedupLBG"]),float(r["Eff%"])))
P=sorted(d); S=[st.mean(x[0] for x in d[p]) for p in P]; lo=[min(x[0] for x in d[p]) for p in P]; hi=[max(x[0] for x in d[p]) for p in P]
E=[st.mean(x[1] for x in d[p]) for p in P]
fig,(ax,ax2)=plt.subplots(1,2,figsize=(13.49,8.21),dpi=150)
ax.axvspan(0.9,6.5,color="#EFEAF8",zorder=0)
ax.text(1.2,14.4,"P-cores only",fontsize=19,color=PURPLE,fontweight="bold",va="center")
ax.text(7.2,14.4,"P + E cores",fontsize=19,color=ORG,fontweight="bold",va="center")
ax.plot([2,14],[2,14],ls=":",color="#555",lw=2.6,label="Ideal linear speedup")
ax.errorbar(P,S,yerr=[[s-l for s,l in zip(S,lo)],[h-s for s,h in zip(S,hi)]],color=PURPLE,lw=3.8,marker="o",ms=12,capsize=4,label="Measured (mean of 8 images)")
for p_,s in zip(P,S):
    ax.annotate(f"{s:.2f}×",(p_,s),textcoords="offset points",xytext=(20,-30),ha="center",fontsize=17,fontweight="bold",color=PURPLE)
ax.set_xlim(0.9,14.8);ax.set_ylim(0,15.5);ax.set_xticks(P)
ax.set_xlabel("Number of MPI processes (P)",fontsize=19);ax.set_ylabel("Speedup",fontsize=19)
ax.set_title("Speedup",fontsize=21,fontweight="bold",color=PURPLE)
ax.tick_params(labelsize=16);ax.grid(alpha=.3)
ax.legend(loc="upper left",bbox_to_anchor=(0.02,0.90),fontsize=14,frameon=False)
ax2.axvspan(0.9,6.5,color="#EFEAF8",zorder=0)
ax2.axhline(100,ls=":",color="#555",lw=2.6,label="Ideal efficiency (100%)")
ax2.plot(P,E,color=MAG,lw=3.8,marker="o",ms=12,label="Measured efficiency")
for p_,e in zip(P,E):
    ax2.annotate(f"{e:.0f}%",(p_,e),textcoords="offset points",xytext=(4,-32),ha="center",fontsize=17,fontweight="bold",color=MAG)
ax2.set_xlim(0.9,14.8);ax2.set_ylim(0,115);ax2.set_xticks(P);ax2.set_yticks(range(0,101,20))
ax2.set_xlabel("Number of MPI processes (P)",fontsize=19);ax2.set_ylabel("Efficiency (%)",fontsize=19)
ax2.set_title("Parallel efficiency  E = S / P",fontsize=21,fontweight="bold",color=MAG)
ax2.tick_params(labelsize=16);ax2.grid(alpha=.3)
ax2.legend(loc="lower left",fontsize=14,frameon=False)
for a_ in (ax,ax2):
    for s_ in ("top","right"): a_.spines[s_].set_visible(False)
plt.tight_layout();plt.savefig("assets/speedup_chart.png",facecolor="white")
