import math, heapq
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
INK="#1F1A33";DEEP="#2E2055";PURPLE="#6B4FA3";MAG="#E0457B";TEAL="#2A9D8F";GOLD="#F2B134";ORG="#E07B22";BLUE="#2F6DB5"
# ---------- figure 1: coloured flow ----------
fig,ax=plt.subplots(figsize=(13.33,2.6),dpi=200); ax.set_xlim(0,100); ax.set_ylim(0,20); ax.axis("off")
steps=[("Delta-coded\nsequence D",TEAL),("Compute symbol\nfrequencies",TEAL),("Build Huffman tree\n(min-heap)",TEAL),("Assign canonical\ncodes\n(from code lengths)",TEAL),("Compressed container:\nheader + code table (H),\ncodebook, bitstream (BS)",TEAL)]
w=16.4;gap=3.0;x=0.6
for i,(t,c) in enumerate(steps):
    ww=w+(3.4 if i==4 else 0)
    ax.add_patch(FancyBboxPatch((x,3),ww,14,boxstyle="round,pad=0.2,rounding_size=1.2",fc=c,ec=c))
    ax.text(x+ww/2,10,t,ha="center",va="center",color="white",fontsize=11 if i<4 else 10,fontweight="bold",linespacing=1.35)
    if i<4: ax.add_patch(FancyArrowPatch((x+ww+0.4,10),(x+ww+gap-0.4,10),arrowstyle="-|>",mutation_scale=22,lw=2.6,color=INK))
    x+=ww+gap
plt.savefig("figs/huffman_flow.png",bbox_inches="tight",facecolor="white"); plt.close()
