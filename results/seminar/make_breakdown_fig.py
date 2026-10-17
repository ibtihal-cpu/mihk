import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
PURPLE="#6B4FA3"; ORG="#E07B22"; INK="#1F1A33"
# LBG share of the total time (mean of the 4 images of each type), from timing_final.csv
lbg={("Grayscale","Sequential"):77.0,("Grayscale","P = 14"):42.0,("Color","Sequential"):81.2,("Color","P = 14"):60.2}
fig,ax=plt.subplots(figsize=(13.49,8.21),dpi=150)
xs=[0,1,2.6,3.6]; labs=[("Grayscale","Sequential"),("Grayscale","P = 14"),("Color","Sequential"),("Color","P = 14")]
for x,k in zip(xs,labs):
    a=lbg[k]; b=100-a
    ax.bar(x,a,width=0.8,color=PURPLE,zorder=3); ax.bar(x,b,width=0.8,bottom=a,color=ORG,zorder=3)
    ax.text(x,a/2,f"{a:.0f}%",ha="center",va="center",color="white",fontsize=26,fontweight="bold")
    ax.text(x,a+b/2,f"{b:.0f}%",ha="center",va="center",color="white",fontsize=26,fontweight="bold")
ax.set_xticks(xs); ax.set_xticklabels(["Sequential","P = 14","Sequential","P = 14"],fontsize=20)
ax.text(0.5,-17,"Grayscale",ha="center",fontsize=24,fontweight="bold",color=INK)
ax.text(3.1,-17,"Color",ha="center",fontsize=24,fontweight="bold",color=INK)
ax.set_ylim(0,100); ax.set_xlim(-0.7,4.3); ax.set_yticks(range(0,101,20)); ax.set_yticklabels([f"{v}%" for v in range(0,101,20)],fontsize=18)
ax.set_ylabel("Share of the total run time",fontsize=21)
ax.grid(axis="y",alpha=.3,zorder=0)
for s in ("top","right"): ax.spines[s].set_visible(False)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=PURPLE,label="LBG training (parallel)"),Patch(color=ORG,label="All other stages (outside LBG)")],loc="upper center",bbox_to_anchor=(0.5,1.09),ncol=2,fontsize=19,frameon=False)
plt.subplots_adjust(bottom=0.2,top=0.9)
plt.savefig("assets/breakdown_chart.png",facecolor="white")
