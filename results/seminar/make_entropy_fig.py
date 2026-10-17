import csv
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
PURPLE="#6B4FA3";TEAL="#2A9D8F";ORG="#E07B22"
rows=list(csv.DictReader(open("../final_campaign/entropy.csv")))
names={"gray":"Lena","boat_img":"Boat","cameraman_img":"Cameraman","peppers_img":"Peppers"}
lab=[names[r["image"]] for r in rows]+["Mean"]
a=[float(r["H_index_bits"]) for r in rows];b=[float(r["H_delta_bits"]) for r in rows];c=[float(r["huffman_bits_per_index"]) for r in rows]
for l in (a,b,c): l.append(sum(l)/4)
x=np.arange(len(lab));w=0.26
fig,ax=plt.subplots(figsize=(9.2,5.6),dpi=220)
bars=[(a,"Entropy of VQ indices",PURPLE),(b,"Entropy after delta coding",TEAL),(c,"Huffman average code length",ORG)]
for k,(v,l,col) in enumerate(bars):
    r=ax.bar(x+(k-1)*w,v,w,color=col,label=l)
    for rect,val in zip(r,v): ax.text(rect.get_x()+rect.get_width()/2,val+0.06,f"{val:.2f}",ha="center",fontsize=11,fontweight="bold",color=col)
ax.set_xticks(x);ax.set_xticklabels(lab,fontsize=14)
ax.set_ylim(0,6.6);ax.set_ylabel("Bits per index",fontsize=15);ax.tick_params(axis="y",labelsize=13)
ax.grid(axis="y",alpha=.3);ax.set_axisbelow(True)
for s in ("top","right"): ax.spines[s].set_visible(False)
ax.axvline(3.5,color="#999",lw=1,ls="--")
ax.legend(loc="upper center",bbox_to_anchor=(0.5,1.0),ncol=3,fontsize=11.5,frameon=False)
plt.tight_layout();plt.savefig("assets/entropy_chart.png",facecolor="white")
