#!/usr/bin/env python3
"""Approximate slide renderer (no LibreOffice available): draws shapes, text, pictures, tables; charts as labelled frames."""
import sys, zipfile, re, io
from lxml import etree
from PIL import Image, ImageDraw, ImageFont
NS={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','c':'http://schemas.openxmlformats.org/drawingml/2006/chart'}
PX=100  # px per inch
RF='/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'; BF='/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
fc={}
def font(pt,b):
    k=(round(pt,1),b)
    if k not in fc: fc[k]=ImageFont.truetype(BF if b else RF, max(6,int(pt*PX/72*0.92)))
    return fc[k]
def hexc(e):
    if e is None: return None
    c=e.find('a:srgbClr',NS)
    return '#'+c.get('val') if c is not None else None
def parse_shape_fill(sp):
    sppr=sp.find('p:spPr',NS)
    if sppr is None: return None,None,0
    fill=None; tr=0
    sf=sppr.find('a:solidFill',NS)
    if sf is not None:
        fill=hexc(sf); a=sf.find('a:srgbClr/a:alpha',NS)
        if a is not None: tr=1-int(a.get('val'))/100000
    ln=sppr.find('a:ln',NS); lc=None; lw=0
    if ln is not None:
        lsf=ln.find('a:solidFill',NS); lc=hexc(lsf) if lsf is not None else None; lw=int(ln.get('w','12700'))/12700
    return fill,(lc,lw),tr
def draw_text(d,x,y,w,h,tx,anchor,defcolor='#1F1A33'):
    bp=tx.find('a:bodyPr',NS)
    li=int(bp.get('lIns',91440))/914400; ri=int(bp.get('rIns',91440))/914400; ti=int(bp.get('tIns',45720))/914400; bi=int(bp.get('bIns',45720))/914400
    anchor=bp.get('anchor','t')
    paras=[]
    total=0
    for p in tx.iterfind('a:p',NS):
        ppr=p.find('a:pPr',NS); algn=ppr.get('algn','l') if ppr is not None else 'l'
        bullet=ppr is not None and ppr.find('a:buChar',NS) is not None
        sa=0
        if ppr is not None:
            s=ppr.find('a:spcAft/a:spcPts',NS)
            if s is not None: sa=int(s.get('val'))/100
        runs=[]
        for r in p.iterfind('a:r',NS):
            rp=r.find('a:rPr',NS)
            sz=int(rp.get('sz','1800'))/100 if rp is not None else 18
            b=rp is not None and rp.get('b')=='1'
            col=hexc(rp.find('a:solidFill',NS)) if rp is not None and rp.find('a:solidFill',NS) is not None else defcolor
            runs.append((r.findtext('a:t',namespaces=NS) or '',sz,b,col))
        if not runs: paras.append(([],algn,bullet,sa,12)); total+=12*1.2*PX/72; continue
        maxw=(w-li-ri-(0.3 if bullet else 0))*PX
        lines=[[]]; cur=0
        for t,sz,b,col in runs:
            for wd in re.findall(r'\S+\s*|\s+',t):
                ww=font(sz,b).getlength(wd.rstrip()); wl=font(sz,b).getlength(wd)
                if cur+ww>maxw and cur>0: lines.append([]); cur=0
                lines[-1].append((wd,sz,b,col)); cur+=wl
        mx=max(r[1] for r in runs)
        paras.append((lines,algn,bullet,sa,mx)); total+=len(lines)*mx*1.2*PX/72+sa*PX/72
    avail=(h-ti-bi)*PX
    y0=y*PX+ti*PX
    if anchor=='ctr': y0+=(avail-total)/2
    elif anchor=='b': y0+=avail-total
    for lines,algn,bullet,sa,mx in paras:
        if not lines: y0+=12*1.2*PX/72; continue
        for ln in lines:
            lw=sum(font(s_,b).getlength(t) for t,s_,b,c in ln)
            x0=x*PX+li*PX+(0.3*PX if bullet else 0)
            if algn=='ctr': x0=x*PX+(w*PX-lw)/2
            elif algn=='r': x0=x*PX+w*PX-ri*PX-lw
            if bullet and ln is lines[0]: d.ellipse([x0-0.2*PX,y0+mx*0.5*PX/72*1.2-3,x0-0.2*PX+6,y0+mx*0.5*PX/72*1.2+3],fill='#444')
            for t,s_,b,c in ln:
                d.text((x0,y0),t,font=font(s_,b),fill=c)
                x0+=font(s_,b).getlength(t)
            y0+=mx*1.2*PX/72
        y0+=sa*PX/72
def render(pptx,outprefix):
    z=zipfile.ZipFile(pptx)
    names=sorted([n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml',n)],key=lambda x:int(re.findall(r'\d+',x)[0]))
    for n in names:
        num=int(re.findall(r'\d+',n)[0])
        root=etree.fromstring(z.read(n))
        rels=etree.fromstring(z.read(f'ppt/slides/_rels/slide{num}.xml.rels'))
        rmap={r.get('Id'):r.get('Target') for r in rels}
        # layout background
        lay=[v for v in rmap.values() if 'slideLayout' in v][0]
        layname=lay.split('/')[-1]
        lroot=etree.fromstring(z.read('ppt/slideLayouts/'+layname))
        bg='#FFFFFF'
        bgc=lroot.find('.//p:bg//a:srgbClr',NS)
        if bgc is not None: bg='#'+bgc.get('val')
        img=Image.new('RGB',(1333,750),bg); d=ImageDraw.Draw(img,'RGBA')
        # layout shapes (footer text)
        for sp in lroot.iterfind('.//p:sp',NS):
            tx=sp.find('p:txBody',NS); off=sp.find('.//a:xfrm/a:off',NS); ext=sp.find('.//a:xfrm/a:ext',NS)
            if tx is not None and off is not None and tx.findtext('.//a:t',namespaces=NS):
                draw_text(d,int(off.get('x'))/914400,int(off.get('y'))/914400,int(ext.get('cx'))/914400,int(ext.get('cy'))/914400,tx,'t','#8A8FA8')
        tree=root.find('p:cSld/p:spTree',NS)
        for el in tree:
            tag=etree.QName(el).localname
            if tag=='sp':
                off=el.find('.//a:xfrm/a:off',NS); ext=el.find('.//a:xfrm/a:ext',NS)
                if off is None: continue
                x=int(off.get('x'))/914400; y=int(off.get('y'))/914400; w=int(ext.get('cx'))/914400; h=int(ext.get('cy'))/914400
                geom=el.find('.//a:prstGeom',NS); g=geom.get('prst') if geom is not None else 'rect'
                fill,ln,tr=parse_shape_fill(el)
                box=[x*PX,y*PX,(x+w)*PX,(y+h)*PX]
                fcol=None
                if fill: 
                    a=int(255*(1-tr)); fcol=fill+('%02x'%a)
                lcol=ln[0] if ln and ln[0] else None; lw=max(1,int(ln[1])) if ln and ln[0] else 0
                if g=='ellipse': d.ellipse(box,fill=fcol,outline=lcol,width=lw)
                elif g=='roundRect': d.rounded_rectangle(box,radius=10,fill=fcol,outline=lcol,width=lw)
                elif g=='rightArrow': d.polygon([(box[0],box[1]+h*PX*0.25),(box[0]+w*PX*0.6,box[1]+h*PX*0.25),(box[0]+w*PX*0.6,box[1]),(box[2],box[1]+h*PX/2),(box[0]+w*PX*0.6,box[3]),(box[0]+w*PX*0.6,box[3]-h*PX*0.25),(box[0],box[3]-h*PX*0.25)],fill=fcol)
                elif g=='line': d.line([box[0],box[1],box[2],box[3]],fill=lcol or '#999',width=max(1,lw))
                else: d.rectangle(box,fill=fcol,outline=lcol,width=lw)
                tx=el.find('p:txBody',NS)
                if tx is not None and ''.join(tx.itertext()).strip():
                    draw_text(d,x,y,w,h,tx,'t')
            elif tag=='pic':
                off=el.find('.//a:xfrm/a:off',NS); ext=el.find('.//a:xfrm/a:ext',NS)
                x=int(off.get('x'))/914400; y=int(off.get('y'))/914400; w=int(ext.get('cx'))/914400; h=int(ext.get('cy'))/914400
                rid=el.find('.//a:blip',NS).get('{%s}embed'%NS['r']); tgt=rmap[rid]
                try:
                    im=Image.open(io.BytesIO(z.read('ppt/'+tgt.replace('../','')))).convert('RGBA').resize((max(1,int(w*PX)),max(1,int(h*PX))))
                    img.paste(im,(int(x*PX),int(y*PX)),im)
                except Exception as e: d.rectangle([x*PX,y*PX,(x+w)*PX,(y+h)*PX],outline='red')
            elif tag=='graphicFrame':
                off=el.find('p:xfrm/a:off',NS); ext=el.find('p:xfrm/a:ext',NS)
                x=int(off.get('x'))/914400; y=int(off.get('y'))/914400; w=int(ext.get('cx'))/914400; h=int(ext.get('cy'))/914400
                tbl=el.find('.//a:tbl',NS)
                if tbl is not None:
                    cols=[int(c.get('w'))/914400 for c in tbl.iterfind('a:tblGrid/a:gridCol',NS)]
                    yy=y
                    for tr_ in tbl.iterfind('a:tr',NS):
                        rh=int(tr_.get('h'))/914400; xx=x; need=rh
                        for ci,tc in enumerate(tr_.iterfind('a:tc',NS)):
                            tp=tc.find('a:tcPr',NS); f=tp.find('a:solidFill',NS) if tp is not None else None
                            d.rectangle([xx*PX,yy*PX,(xx+cols[ci])*PX,(yy+rh)*PX],fill=hexc(f) if f is not None else '#FFFFFF',outline='#DDD5EE')
                            tx=tc.find('a:txBody',NS)
                            if tx is not None:
                                tmp=etree.SubElement(tx,'{%s}bodyPr'%NS['a']) if tx.find('a:bodyPr',NS) is None else None
                                draw_text(d,xx,yy,cols[ci],rh,tx,'ctr')
                            xx+=cols[ci]
                        yy+=rh
                else:
                    cref=el.find('.//c:chart',NS)
                    ct=''
                    if cref is not None:
                        rid=cref.get('{%s}id'%NS['r']); cp=('ppt/'+rmap[rid].replace('../','')).replace('ppt//ppt/','ppt/').replace('ppt/ppt/','ppt/')
                        cx=etree.fromstring(z.read(cp))
                        kind=[etree.QName(e).localname for e in cx.find('.//c:plotArea',NS) if etree.QName(e).localname.endswith('Chart')]
                        ttl=''.join(t.text or '' for t in cx.iterfind('.//c:title//a:t',NS))
                        sers=[ ''.join(t.text or '' for t in s.iterfind('.//c:tx//c:v',NS)) for s in cx.iterfind('.//c:ser',NS)]
                        ct=f"[{','.join(kind)}] {ttl} | series: {'; '.join(sers)}"
                    d.rectangle([x*PX,y*PX,(x+w)*PX,(y+h)*PX],fill='#FBFAFE',outline='#B8AED3')
                    d.text((x*PX+8,y*PX+8),ct,font=font(10,False),fill='#6B4FA3')
        img.save(f'{outprefix}-{num:02d}.png')
    return len(names)
if __name__=='__main__': print(render(sys.argv[1],sys.argv[2]),'slides')
