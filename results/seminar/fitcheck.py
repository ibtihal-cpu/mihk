#!/usr/bin/env python3
"""Rough text-fit check for a pptx (no renderer available): estimates wrapped text height vs. box height."""
import sys, zipfile, re
from lxml import etree
from PIL import ImageFont
NS={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
R='/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'; B='/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
cache={}
def font(sz,b):
    k=(round(sz*4),b)
    if k not in cache: cache[k]=ImageFont.truetype(B if b else R, int(sz*4))
    return cache[k]
def width_in(text,sz,b,k=0.92):  # points -> inches, calibri ~0.92 of arial
    return font(sz,b).getlength(text)/4/72*k
def wrap_lines(runs,maxw):
    # runs: list of (text,sz,bold); greedy word wrap
    words=[]
    for t,sz,b in runs:
        for w in re.findall(r'\S+\s*|\s+',t): words.append((w,sz,b))
    lines=1; cur=0; 
    for w,sz,b in words:
        wl=width_in(w,sz,b)
        if cur+width_in(w.rstrip(),sz,b)>maxw and cur>0:
            lines+=1; cur=wl
        else: cur+=wl
    return lines
z=zipfile.ZipFile(sys.argv[1]); bad=0
for n in sorted([n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml',n)],key=lambda x:int(re.findall(r'\d+',x)[0])):
    root=etree.fromstring(z.read(n)); num=int(re.findall(r'\d+',n)[0])
    for sp in root.iterfind('.//p:sp',NS):
        tx=sp.find('p:txBody',NS)
        if tx is None: continue
        off=sp.find('.//a:xfrm/a:off',NS); ext=sp.find('.//a:xfrm/a:ext',NS)
        if off is None: continue
        w=int(ext.get('cx'))/914400; h=int(ext.get('cy'))/914400
        bp=tx.find('a:bodyPr',NS); li=int(bp.get('lIns',91440))/914400; ri=int(bp.get('rIns',91440))/914400; ti=int(bp.get('tIns',45720))/914400; bi=int(bp.get('bIns',45720))/914400
        need=0; txt=''
        for p in tx.iterfind('a:p',NS):
            runs=[]; sz0=18
            for r in p.iterfind('a:r',NS):
                rp=r.find('a:rPr',NS); sz=int(rp.get('sz','1800'))/100 if rp is not None else 18; b=(rp is not None and rp.get('b')=='1')
                runs.append((r.findtext('a:t',namespaces=NS) or '',sz,b)); sz0=sz; txt+=runs[-1][0]
            if not runs:
                need+=sz0*1.2/72; continue
            ppr=p.find('a:pPr',NS); ind=0.0
            if ppr is not None and ppr.find('a:buChar',NS) is not None: ind=0.3
            lines=wrap_lines(runs,max(0.2,w-li-ri-ind))
            mx=max(r[1] for r in runs)
            sa=0
            if ppr is not None:
                s=ppr.find('a:spcAft/a:spcPts',NS)
                if s is not None: sa=int(s.get('val'))/100/72
            need+=lines*mx*1.2/72+sa
        need+=ti+bi
        if need>h*1.04 and txt.strip():
            bad+=1; print(f'slide {num}: need {need:.2f}in > box {h:.2f}in  w={w:.2f} :: {txt[:70]!r}')
print('overflow candidates:',bad)
