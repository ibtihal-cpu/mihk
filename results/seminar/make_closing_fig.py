import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrow, Circle
from PIL import Image
import numpy as np
DEEP="#2E2055"; MAG="#E0457B"; PUR="#9B7FE0"; ORG="#F2993A"
o=np.asarray(Image.open("assets/cam_orig.png").convert("L")); r=np.asarray(Image.open("assets/cam_rec.png").convert("L"))
fig=plt.figure(figsize=(8.2,6.2),dpi=200,facecolor=DEEP); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,8.2); ax.set_ylim(6.2,0); ax.axis("off"); ax.set_facecolor(DEEP)
def img(a,x,y,s=3.0,title="",col="white"):
    ax.add_patch(FancyBboxPatch((x-0.06,y-0.06),s+0.12,s+0.12,boxstyle="round,pad=0,rounding_size=0.08",fc="white",ec="white"))
    ax.imshow(a,cmap="gray",extent=(x,x+s,y+s,y),zorder=3,vmin=0,vmax=255)
    ax.text(x+s/2,y+s+0.38,title,ha="center",va="center",color=col,fontsize=15,fontweight="bold")
img(o,0.25,0.35,3.0,"Original")
img(r,4.95,0.35,3.0,"Reconstructed (29.75 dB)")
ax.add_patch(FancyArrow(3.55,1.85,1.1,0,width=0.16,head_width=0.5,head_length=0.35,length_includes_head=True,color=MAG,zorder=4))
ax.text(4.1,1.35,"LBG-VQ",ha="center",color="white",fontsize=13,fontweight="bold")
ax.set_xlim(0,8.2); ax.set_ylim(6.2,0)
# cores row
y=4.85
for i in range(14):
    x=0.97+i*0.5
    ax.add_patch(Circle((x,y),0.19,fc=PUR if i<6 else ORG,ec="white",lw=1.5,zorder=4))
ax.text(0.97+2.5*0.5,y+0.55,"6 P-cores",ha="center",color=PUR,fontsize=14,fontweight="bold")
ax.text(0.97+9.5*0.5,y+0.55,"8 E-cores",ha="center",color=ORG,fontsize=14,fontweight="bold")
fig.savefig("assets/closing.png",facecolor=DEEP)
