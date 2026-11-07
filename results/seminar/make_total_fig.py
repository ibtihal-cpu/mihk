import csv, collections, statistics as st
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
PURPLE="#6B4FA3";ORG="#E07B22";TEAL="#2A9D8F"
rows=[r for r in csv.DictReader(open("../final_campaign/timing_final.csv")) if r["np"]!="seq"]
tot=collections.defaultdict(lambda:collections.defaultdict(list)); lbg=collections.defaultdict(list)
for r in rows:
    p=int(r["np"]); tot[r["mode"]][p].append(float(r["SpeedupTotal"])); lbg[p].append(float(r["SpeedupLBG"]))
P=sorted(lbg)
fig,ax=plt.subplots(figsize=(9.2,5.6),dpi=220)
ax.plot([2,14],[2,14],ls=":",color="#555",lw=2.2,label="Ideal linear speedup")
ax.plot(P,[st.mean(lbg[p]) for p in P],color=PURPLE,lw=2.6,ls="--",marker="o",ms=7,label="LBG stage (mean of 8 images)")
for mode,col,lab,mk in (("color",ORG,"Total, color images","s"),("gray",TEAL,"Total, grayscale images","o")):
    m=[st.mean(tot[mode][p]) for p in P]; lo=[min(tot[mode][p]) for p in P]; hi=[max(tot[mode][p]) for p in P]
    ax.fill_between(P,lo,hi,color=col,alpha=.15,lw=0)
    ax.plot(P,m,color=col,lw=3.2,marker=mk,ms=9,label=lab)
    for p,v in ((P[-1],m[-1]),):
        ax.annotate(f"{v:.2f}×",(p,v),textcoords="offset points",xytext=(0,13),ha="center",fontsize=13,fontweight="bold",color=col)
    print(mode,[round(x,2) for x in m])
ax.annotate(f"{st.mean(lbg[14]):.2f}×",(14,st.mean(lbg[14])),textcoords="offset points",xytext=(0,13),ha="center",fontsize=13,fontweight="bold",color=PURPLE)
ax.set_xticks(P);ax.set_xlim(1.5,14.6);ax.set_ylim(0,15)
ax.set_xlabel("Number of MPI processes (P)",fontsize=15);ax.set_ylabel("Speedup",fontsize=15)
ax.tick_params(labelsize=13);ax.grid(alpha=.3)
for s in ("top","right"): ax.spines[s].set_visible(False)
ax.legend(loc="upper left",fontsize=12.5,frameon=False)
plt.tight_layout();plt.savefig("assets/total_speedup_chart.png",facecolor="white")
