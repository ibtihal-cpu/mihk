import csv, collections, statistics as st
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
PURPLE="#6B4FA3";ORG="#E07B22";MAG="#E0457B";TEAL="#2A9D8F"
seq={r["image"]:float(r["LBG_s"]) for r in csv.DictReader(open("../final_campaign/timing_final.csv")) if r["np"]=="seq"}
d=collections.defaultdict(lambda:[[],[],[]])
for r in csv.DictReader(open("../final_campaign/eq_ad_total.csv")):
    p=int(r["np"]);s=seq[r["image"]]
    d[p][0].append(s/float(r["eq_lbg"]));d[p][1].append(s/float(r["ad_lbg"]));d[p][2].append(float(r["lbg_gain_pct"]))
P=sorted(d);EQ=[st.mean(d[p][0]) for p in P];AD=[st.mean(d[p][1]) for p in P];G=[st.mean(d[p][2]) for p in P]
fig,ax=plt.subplots(figsize=(9.2,5.6),dpi=220)
ax.axvspan(1.5,6.5,color="#EFEAF8",zorder=0)
ax.text(2.0,14.2,"P-cores only: no difference",fontsize=13,color=PURPLE,fontweight="bold",va="center")
ax.plot([2,14],[2,14],ls=":",color="#555",lw=2.2,label="Ideal linear speedup")
ax.plot(P,EQ,color=ORG,lw=3.2,marker="s",ms=9,label="Equal distribution")
ax.plot(P,AD,color=PURPLE,lw=3.2,marker="o",ms=10,label="Adaptive (speed-aware) distribution")
for p,e,a,g in zip(P,EQ,AD,G):
    if p>=8:
        ax.annotate(f"{a:.2f}×",(p,a),textcoords="offset points",xytext=(0,12),ha="center",fontsize=12.5,fontweight="bold",color=PURPLE)
        ax.annotate(f"{e:.2f}×",(p,e),textcoords="offset points",xytext=(0,-24),ha="center",fontsize=12.5,fontweight="bold",color=ORG)
        ax.annotate("",xy=(p+0.33,a),xytext=(p+0.33,e),arrowprops=dict(arrowstyle="<->",color=MAG,lw=1.8))
        ax.text(p+0.42,(a+e)/2,f"−{g:.1f}%",fontsize=11.5,color=MAG,fontweight="bold",va="center")
ax.set_xlim(1.5,15.2);ax.set_ylim(0,15);ax.set_xticks(P)
ax.set_xlabel("Number of MPI processes (P)",fontsize=15);ax.set_ylabel("LBG speedup",fontsize=15)
ax.tick_params(labelsize=13);ax.grid(alpha=.3)
for s in ("top","right"): ax.spines[s].set_visible(False)
ax.text(15.1,1.0,"pink = LBG time reduction (Adaptive vs Equal)",fontsize=12,color=MAG,ha="right",fontweight="bold")
ax.legend(loc="upper left",bbox_to_anchor=(0.0,0.9),fontsize=12.5,frameon=False)
plt.tight_layout();plt.savefig("assets/eqad_chart.png",facecolor="white")
