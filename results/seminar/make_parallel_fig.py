import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import numpy as np

INK="#1F1A33";DEEP="#2E2055";PURPLE="#6B4FA3";LAV="#A794D6";MAG="#E0457B";TEAL="#2A9D8F";GOLD="#F2B134";MIST="#F5F1FB"
fig,ax=plt.subplots(figsize=(13.33,5.3),dpi=200)
ax.set_xlim(0,100);ax.set_ylim(7,48);ax.axis("off")
fig.patch.set_facecolor("white")

def box(x,y,w,h,fc,txt,tc="white",fs=12,bold=True,ec=None):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.2,rounding_size=1.2",fc=fc,ec=ec or fc,lw=1.5))
    ax.text(x+w/2,y+h/2,txt,ha="center",va="center",color=tc,fontsize=fs,fontweight="bold" if bold else "normal",linespacing=1.3)
def arrow(x1,y1,x2,y2,c=INK):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle="-|>",mutation_scale=22,lw=2.4,color=c))

# 1 image
rng=np.random.default_rng(3)
ax.add_patch(Rectangle((2,18),12,12,fc=LAV,ec=INK,lw=1.5))
for i in range(1,4):
    ax.plot([2+3*i,2+3*i],[18,30],color="white",lw=1);ax.plot([2,14],[18+3*i,18+3*i],color="white",lw=1)
ax.text(8,32.5,"Input image",ha="center",fontsize=12,fontweight="bold",color=INK)
ax.text(8,15.5,"512×512",ha="center",fontsize=11,color=INK)
ax.text(8,13,"16,384 blocks\n(4×4 pixels)",ha="center",va="top",fontsize=10.5,color=PURPLE,fontweight="bold")

arrow(15,24,20.4,24)
ax.plot([21.3,21.3],[15.5,37.8],color=INK,lw=2.6,solid_capstyle="round")
for yy in [36,29,22,15]:
    ax.add_patch(FancyArrowPatch((21.3,yy+1.25),(22.9,yy+1.25),arrowstyle="-|>",mutation_scale=13,lw=2.2,color=INK))
ax.text(17.7,25.6,"Scatterv",ha="center",fontsize=9,color=MAG,fontweight="bold")

# 2 ranks
cols=[PURPLE,PURPLE,TEAL,TEAL]
labs=["Process 0\nP-core","Process 1\nP-core","Process 2\nE-core","Process P−1\nE-core"]
shares=["larger share","larger share","smaller share","smaller share"]
ys=[36,29,22,15]
for y,c,l,s in zip(ys,cols,labs,shares):
    box(23,y-1.5,16,5.5,c,l+"\n"+s,fs=10)
ax.text(31,44.5,"Each process gets a chunk (Adaptive shown)",ha="center",fontsize=12,fontweight="bold",color=INK)
ax.text(31,9.6,"Adaptive: chunk size ∝ core speed",ha="center",fontsize=10,color=INK,style="italic")

# 3 local assignment
box(52,17,16,14,GOLD,"Local step:\nnearest codeword\nfor each block\n(main cost of LBG)",tc=INK,fs=10.5)
for y,ty in zip(ys,[29.0,25.7,22.3,19.0]): arrow(39.6,y+1.25,51.6,ty,c="#4A4A4A")
ax.text(56,33.2,"in parallel",ha="center",fontsize=12,fontweight="bold",color=MAG)

arrow(68.5,24,77.5,24)
ax.text(73,26.4,"Allreduce",ha="center",fontsize=11,color=MAG,fontweight="bold")
ax.text(73,21.4,"sums from all\nprocesses",ha="center",va="top",fontsize=8.5,color=INK)

# 4 codebook
box(78,17,11,14,MAG,"New\ncodebook\nK = 64",fs=12)
arrow(89.5,24,92.3,24)
box(92.8,19.5,6.4,9,DEEP,"Repeat\nuntil\nconverged",fs=8.5)
# loop arrow back
ax.plot([96,96,64],[29.2,40.2,40.2],color=DEEP,lw=2.4,ls="--",solid_capstyle="round")
ax.add_patch(FancyArrowPatch((64,40.2),(64,31.6),arrowstyle="-|>",mutation_scale=22,lw=2.4,color=DEEP,linestyle="--"))
ax.text(80,41.2,"next iteration (new codebook sent to all processes)",ha="center",fontsize=9.5,color=DEEP,style="italic")

plt.savefig("/home/user/mihk/results/seminar/figs/parallel_overview.png",bbox_inches="tight",facecolor="white")
