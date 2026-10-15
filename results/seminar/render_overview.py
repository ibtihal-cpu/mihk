import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrow
spec=json.load(open("overview_spec.json"))
W,H=13.333,7.5
fig=plt.figure(figsize=(W,H),dpi=150); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,W); ax.set_ylim(H,0); ax.axis("off")
c=lambda h:"#"+h
ax.text(0.5,0.55,spec["title"],fontsize=26,fontweight="bold",color="#2E2055",va="center")
ax.add_patch(plt.Rectangle((0.5,0.92),12.33,0.04,color="#E0457B"))
top,rowH,gap,hx,hw,bx0,bw,arrow=1.15,1.2,0.32,0.5,2.35,3.05,2.05,0.4
for i,st in enumerate(spec["stages"]):
    y=top+i*(rowH+gap)
    ax.add_patch(FancyBboxPatch((hx-0.05,y-0.05),12.43,rowH+0.1,boxstyle="round,pad=0,rounding_size=0.1",fc=c(st["light"]),ec=c(st["color"]),lw=2.5 if st.get("hl") else 1,ls="--" if st.get("hl") else "-"))
    ax.add_patch(FancyBboxPatch((hx,y),hw,rowH,boxstyle="round,pad=0,rounding_size=0.08",fc=c(st["color"]),ec=c(st["color"])))
    ax.text(hx+hw/2,y+rowH/2-0.2,st["name"],ha="center",va="center",color="white",fontsize=15,fontweight="bold")
    ax.text(hx+hw/2,y+rowH/2+0.25,st["sub"],ha="center",va="center",color="white",fontsize=10.5,wrap=True)
    for j,t in enumerate(st["steps"]):
        x=bx0+j*(bw+arrow)
        ax.add_patch(FancyBboxPatch((x,y+0.1),bw,rowH-0.2,boxstyle="round,pad=0,rounding_size=0.08",fc="white",ec=c(st["color"]),lw=1.5))
        ax.text(x+bw/2,y+rowH/2-0.14,f"{j+1}. {t[0]}",ha="center",va="center",color=c(st["color"]),fontsize=11.5,fontweight="bold")
        ax.text(x+bw/2,y+rowH/2+0.22,t[1],ha="center",va="center",color="#1F1A33",fontsize=8.5)
        if j<len(st["steps"])-1:
            ax.add_patch(FancyArrow(x+bw+0.05,y+rowH/2,arrow-0.1,0,width=0.12,head_width=0.26,head_length=0.15,length_includes_head=True,color="#1F1A33"))
    if st.get("loop"):
        ax.text(bx0+bw+arrow,y+rowH-0.1,"↻ "+st["loop"],fontsize=8,style="italic",fontweight="bold",color=c(st["color"]),va="center")
    if i<len(spec["stages"])-1:
        ax.text(6.95,y+rowH+gap/2,spec["between"][i],fontsize=8.5,style="italic",fontweight="bold",color="#E0457B",va="center")
        ax.add_patch(FancyArrow(6.68,y+rowH+0.06,0,gap-0.12,width=0.1,head_width=0.26,head_length=0.12,length_includes_head=True,color="#1F1A33"))
ax.text(W/2,7.22,spec["footer"],ha="center",va="center",fontsize=10,style="italic",color="#6B4FA3")
fig.savefig("figs/overview_preview.png")
