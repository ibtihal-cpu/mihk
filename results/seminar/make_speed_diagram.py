import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrow
PUR="#6B4FA3"; ORG="#E07B22"; TEAL="#2A9D8F"; MAG="#E0457B"; DEEP="#2E2055"; INK="#1F1A33"
fig=plt.figure(figsize=(14,7.2),dpi=150); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,14); ax.set_ylim(7.2,0); ax.axis("off")
ax.text(7,0.45,"How the speed of each process is found (Adaptive distribution)",ha="center",fontsize=20,fontweight="bold",color=DEEP)
steps=[("1","Benchmark","each process times\nthe same small test",PUR),
       ("2","Allgather","everyone shares\nits speed",ORG),
       ("3","Shares","share = speed ÷\nsum of speeds",TEAL),
       ("4","Scatterv","blocks are sent\nby share",MAG),
       ("5","LBG","each process works\non its own share",DEEP)]
w=2.25; gap=0.45; x0=0.5
for i,(n,t,d,c) in enumerate(steps):
    x=x0+i*(w+gap)
    ax.add_patch(FancyBboxPatch((x,1.0),w,1.9,boxstyle="round,pad=0,rounding_size=0.15",fc=c,ec=c))
    ax.text(x+w/2,1.4,f"{n}. {t}",ha="center",va="center",color="white",fontsize=16,fontweight="bold")
    ax.text(x+w/2,2.2,d,ha="center",va="center",color="white",fontsize=12.5,linespacing=1.3)
    if i<4: ax.add_patch(FancyArrow(x+w+0.05,1.95,gap-0.1,0,width=0.1,head_width=0.3,head_length=0.18,length_includes_head=True,color=INK))
ax.text(7,3.45,"Example with two processes",ha="center",fontsize=16,fontweight="bold",color=INK)
rows=[("Rank 0","P-core","0.4 ms","2.5","67%",PUR),("Rank 1","E-core","0.8 ms","1.25","33%",TEAL)]
cols=[("Process",1.2),("Core",3.0),("Test time",4.9),("Speed = 1 ÷ time",7.2),("Share of blocks",10.0)]
for name,x in cols: ax.text(x,4.0,name,fontsize=13.5,fontweight="bold",color=DEEP,ha="left")
ax.plot([1.1,12.9],[4.2,4.2],color="#B8AED3",lw=1.5)
for j,(r,core,t,sp,sh,c) in enumerate(rows):
    y=4.8+j*0.95
    ax.add_patch(FancyBboxPatch((1.1,y-0.35),11.8,0.7,boxstyle="round,pad=0,rounding_size=0.1",fc="#F5F1FB",ec="none"))
    ax.text(1.2,y,r,fontsize=14,fontweight="bold",color=c,va="center")
    ax.text(3.0,y,core,fontsize=14,color=INK,va="center")
    ax.text(4.9,y,t,fontsize=14,color=INK,va="center")
    ax.text(7.2,y,sp,fontsize=14,color=INK,va="center")
    ax.add_patch(FancyBboxPatch((10.0,y-0.2),2.6*float(sh.strip('%'))/67,0.4,boxstyle="round,pad=0,rounding_size=0.08",fc=c,ec="none"))
    ax.text(10.1,y,sh,fontsize=13,fontweight="bold",color="white",va="center")
ax.text(7,6.85,"Faster process → shorter time → larger share.   (example numbers for illustration)",ha="center",fontsize=13,style="italic",color=MAG)
fig.savefig("figs/Speed_measurement_diagram.png",facecolor="white")
