import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, FancyArrowPatch
INK="#1F1A33";ORG="#E07B22";GOLD="#F2B134";MAG="#E0457B";TEAL="#2A9D8F";DEEP="#2E2055"
fig,ax=plt.subplots(figsize=(8.6,6.1),dpi=220)
ax.set_xlim(0,100);ax.set_ylim(-2,72);ax.axis("off")
def box(cx,cy,w,h,txt,fc,tc="white",fs=13):
    ax.add_patch(FancyBboxPatch((cx-w/2,cy-h/2),w,h,boxstyle="round,pad=0.2,rounding_size=1.2",fc=fc,ec=fc))
    ax.text(cx,cy,txt,ha="center",va="center",color=tc,fontsize=fs,fontweight="bold",linespacing=1.25)
def dia(cx,cy,w,h,txt,fc,fs=11.5):
    ax.add_patch(Polygon([(cx,cy+h/2),(cx+w/2,cy),(cx,cy-h/2),(cx-w/2,cy)],fc=fc,ec=fc))
    ax.text(cx,cy,txt,ha="center",va="center",color=INK,fontsize=fs,fontweight="bold",linespacing=1.25)
def arr(p,q,c=INK):
    ax.add_patch(FancyArrowPatch(p,q,arrowstyle="-|>",mutation_scale=20,lw=2.2,color=c,shrinkA=0,shrinkB=0))
def line(xs,ys,c=INK):
    ax.plot(xs,ys,color=c,lw=2.2,solid_capstyle="round")
X=24
box(X,66,36,9,"Initial codeword C0\n(global mean)",DEEP)
box(X,53,36,9,"Binary split\nδ = 0.01  (k → 2k)",ORG)
box(X,40,36,9,"Nearest-codeword\nassignment",ORG)
box(X,27,36,9,"Centroid update",ORG)
arr((X,61.4),(X,57.6));arr((X,48.4),(X,44.6));arr((X,35.4),(X,31.6))
dia(64,27,36,19,"Converged?\nΔD ≤ ε  or\niter ≥ 100",GOLD,11)
arr((42.4,27),(45.8,27))
line([64,64],[36.5,40]);arr((64,40),(42.4,40))
ax.text(66,37.2,"No",color=MAG,fontsize=14,fontweight="bold")
dia(64,6,32,12,"k < K ?",GOLD,13)
arr((64,17.5),(64,12.2))
ax.text(66,14.3,"Yes",color=TEAL,fontsize=14,fontweight="bold")
line([48,2],[6,6]);line([2,2],[6,53]);arr((2,53),(5.7,53))
ax.text(22,8.0,"Yes",color=TEAL,fontsize=14,fontweight="bold")
arr((80,6),(84.2,6))
ax.text(78.2,9.4,"No",color=MAG,fontsize=14,fontweight="bold")
box(92,6,15,14,"Final\ncodebook\nK = 64",MAG,fs=11.5)
plt.savefig("assets/lbg_flow_color.png",bbox_inches="tight",facecolor="white",pad_inches=0.1)
