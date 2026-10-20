import math, heapq
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
INK="#1F1A33";DEEP="#2E2055";PURPLE="#6B4FA3";MAG="#E0457B";TEAL="#2A9D8F";GOLD="#F2B134";ORG="#E07B22";BLUE="#2F6DB5"
# ---------- figure 1: coloured flow ----------
fig,ax=plt.subplots(figsize=(13.33,2.6),dpi=200); ax.set_xlim(0,100); ax.set_ylim(0,20); ax.axis("off")
steps=[("Delta-coded\nsequence D",PURPLE),("Compute symbol\nfrequencies",BLUE),("Build Huffman tree\n(min-heap)",TEAL),("Assign canonical\ncodes\n(from code lengths)",ORG),("Compressed container:\nheader + code table (H),\ncodebook, bitstream (BS)",MAG)]
w=16.4;gap=3.0;x=0.6
for i,(t,c) in enumerate(steps):
    ww=w+(3.4 if i==4 else 0)
    ax.add_patch(FancyBboxPatch((x,3),ww,14,boxstyle="round,pad=0.2,rounding_size=1.2",fc=c,ec=c))
    ax.text(x+ww/2,10,t,ha="center",va="center",color="white",fontsize=11 if i<4 else 10,fontweight="bold",linespacing=1.35)
    if i<4: ax.add_patch(FancyArrowPatch((x+ww+0.4,10),(x+ww+gap-0.4,10),arrowstyle="-|>",mutation_scale=22,lw=2.6,color=INK))
    x+=ww+gap
plt.savefig("figs/huffman_flow.png",bbox_inches="tight",facecolor="white"); plt.close()
# ---------- figure 2: simple worked example (Cover & Thomas, Example 5.6.1) ----------
P=[0.25,0.25,0.20,0.15,0.15]; sym=[1,2,3,4,5]
h=[(p,i,[i]) for i,p in enumerate(P)]; heapq.heapify(h); L=[0]*5; cnt=10
while len(h)>1:
    a=heapq.heappop(h); b=heapq.heappop(h)
    for s in a[2]+b[2]: L[s]+=1
    heapq.heappush(h,(a[0]+b[0],cnt,a[2]+b[2])); cnt+=1
# canonical assignment
order=sorted(range(5),key=lambda i:(L[i],sym[i])); code={}; c=0; prev=L[order[0]]
for k,i in enumerate(order):
    if k>0: c=(c+1)<<(L[i]-prev)
    code[i]=format(c,"0%db"%L[i]); prev=L[i]
avg=sum(p*l for p,l in zip(P,L)); H=-sum(p*math.log2(p) for p in P)
print("lengths",L,"codes",[code[i] for i in range(5)],"avg",avg,"H",round(H,3))
fig,ax=plt.subplots(figsize=(9.5,4.2),dpi=200); ax.axis("off"); ax.set_xlim(0,10); ax.set_ylim(-0.7,5.4)
cols=["Symbol","Probability","Code length\n(Huffman)","Canonical\ncodeword"]; xs=[1.3,3.7,6.1,8.5]
for x_,t in zip(xs,cols):
    ax.add_patch(FancyBboxPatch((x_-1.05,4.1),2.1,0.95,boxstyle="round,pad=0.02,rounding_size=0.12",fc=TEAL,ec=TEAL))
    ax.text(x_,4.58,t,ha="center",va="center",color="white",fontsize=10.5,fontweight="bold",linespacing=1.2)
for r,i in enumerate(range(5)):
    y=3.55-r*0.62; f="#EAF6F4" if r%2==0 else "white"
    ax.add_patch(FancyBboxPatch((0.1,y-0.27),9.8,0.54,boxstyle="round,pad=0.01,rounding_size=0.08",fc=f,ec="none"))
    for x_,v,col in zip(xs,[str(sym[i]),f"{P[i]:.2f}",str(L[i]),code[i]],[INK,INK,INK,MAG]):
        ax.text(x_,y,v,ha="center",va="center",fontsize=12,color=col,fontweight="bold" if col==MAG else "normal",family="monospace" if col==MAG else None)
ax.text(5,0.38,f"Average length  L = Σ p·l = {avg:.2f} bits/symbol,   Entropy  H = {H:.3f} bits/symbol",ha="center",va="center",fontsize=10.5,color=DEEP,fontweight="bold")
ax.text(5,-0.08,"H ≤ L < H + 1",ha="center",va="center",fontsize=10.5,color=DEEP,fontweight="bold")
ax.text(5,-0.5,"Example: Cover and Thomas, Elements of Information Theory, Example 5.6.1 (canonical codewords added)",ha="center",va="center",fontsize=8.5,color="#5B6770",style="italic")
plt.savefig("figs/huffman_example.png",bbox_inches="tight",facecolor="white"); plt.close()
