import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
W,H=8.0,5.45
fig=plt.figure(figsize=(W,H),dpi=250); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,W); ax.set_ylim(H,0); ax.axis("off")
INK="#1F1A33"; BLUE="#2F6DB5"; ORG="#E07B22"; TEAL="#2A9D8F"; PUR="#6B4FA3"
def box(x,y,w,h,fc,ec,lw=1.6,r=0.06,ls="-"):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle=f"round,pad=0,rounding_size={r}",fc=fc,ec=ec,lw=lw,ls=ls))
def arrow(x1,y1,x2,y2,col=INK,lw=1.4):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle="-|>",mutation_scale=11,lw=lw,color=col,shrinkA=0,shrinkB=0))
# top
box(2.2,0.1,3.6,0.5,"#E4EEFA",BLUE,2)
ax.text(4,0.35,"Training vectors (N = 16,384)",ha="center",va="center",fontsize=11.5,fontweight="bold",color=BLUE)
panels=[(0.1,"Equal Vector Distribution","Same number of vectors per process (N/P)","#EAF3FB",BLUE,[0.78]*4,
         "Same chunk size on heterogeneous cores (P and E):\nload imbalance, the P-cores finish first and wait."),
        (4.1,"Speed-Aware (Adaptive) Distribution","Vectors proportional to the measured process speed","#FDF0E3",ORG,[0.95,0.95,0.5,0.5],
         "Chunk size follows the core speed (heterogeneity-aware):\nbalanced load, all processes finish at about the same time.")]
cores=[("P-core",BLUE),("P-core",BLUE),None,("E-core",TEAL),("E-core",TEAL)]
for px,title,sub,fc,ec,sizes,note in panels:
    sizes=[sizes[0],sizes[1],None,sizes[2],sizes[3]]
    pw=3.8
    box(px,0.95,pw,4.1,fc,ec,2,0.1,"--")
    ax.text(px+pw/2,1.25,title,ha="center",va="center",fontsize=11.6,fontweight="bold",color=ec)
    ax.text(px+pw/2,1.58,sub,ha="center",va="center",fontsize=8.6,color=INK,style="italic")
    arrow(4,0.6,px+pw/2,0.95,INK,1.6)
    colw=pw/5
    for i,(sz,cc_) in enumerate(zip(sizes,cores)):
        cx=px+colw*(i+0.5)
        if sz is None:
            ax.text(cx,2.45,"· · ·",ha="center",va="center",fontsize=15,fontweight="bold",color=INK)
            ax.text(cx,3.57,"· · ·",ha="center",va="center",fontsize=15,fontweight="bold",color=INK)
            continue
        cn,cc=cc_
        s_=sz*0.66
        cy=2.45
        box(cx-s_/2,cy-s_/2,s_,s_,"white",ec,1.8,0.04)
        ax.plot([cx-s_/2,cx+s_/2],[cy,cy],color=ec,lw=0.8,alpha=.6); ax.plot([cx,cx],[cy-s_/2,cy+s_/2],color=ec,lw=0.8,alpha=.6)
        ax.text(cx,2.95,"chunk",ha="center",va="center",fontsize=6.6,color=INK)
        arrow(cx,3.07,cx,3.3)
        box(cx-0.31,3.32,0.62,0.5,"white",cc,2,0.05)
        ax.text(cx,3.57,cn,ha="center",va="center",fontsize=7.6,fontweight="bold",color=cc)
        arrow(cx,3.82,px+pw/2+(cx-px-pw/2)*0.55,4.14,PUR,1.2)
    box(px+pw/2-1.2,4.15,2.4,0.36,PUR,PUR,1,0.05)
    ax.text(px+pw/2,4.33,"MPI_Allreduce (all processes)",ha="center",va="center",fontsize=8.6,fontweight="bold",color="white")
    ax.text(px+pw/2,4.78,note,ha="center",va="center",fontsize=7.8,color=INK,linespacing=1.25)
ax.text(4,5.3,"Heterogeneous cores (P and E) cause load imbalance under equal distribution (illustrative chunk sizes)",ha="center",va="center",fontsize=7.4,color="#5B6770",style="italic")
fig.savefig("figs/Workload_distribution.png")
