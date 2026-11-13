import re,copy
from docx import Document
SRC='/home/user/mihk/stages/thesis_chapters/Chapter_2_updated_v3.docx'
OUT='/home/user/mihk/stages/thesis_chapters/Chapter_2_updated_v3.docx'
MD='/home/user/mihk/stages/literature/References_Ch1_Ch2.md'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
def rep_span(p,i,j,new):
    pos=0; first=True
    for r in p.runs:
        a,b=pos,pos+len(r.text); pos=b
        if b<=i or a>=j: continue
        s=max(i,a)-a; e=min(j,b)-a
        if first: r.text=r.text[:s]+new+r.text[e:]; first=False
        else: r.text=r.text[:s]+r.text[e:]
d=Document(SRC)
hi=[i for i,p in enumerate(d.paragraphs) if p.text.strip()=='References'][0]
body=d.paragraphs[:hi]
# document order of body elements incl. tables
seen=[]
for ch in d.element.body:
    if ch.tag==W+'p':
        t=''.join(x.text or '' for x in ch.iter(W+'t'))
        if t.strip()=='References': break
    else: t=''.join(x.text or '' for x in ch.iter(W+'t'))
    for m in re.finditer(r'\[(\d+)\]',t):
        n=int(m.group(1))
        if n>=19 and n not in seen: seen.append(n)
mp={old:19+k for k,old in enumerate(seen)}
print('mapping',{o:n for o,n in mp.items() if o!=n})
def remap(p):
    full=''.join(r.text for r in p.runs)
    ms=[m for m in re.finditer(r'\[(\d+)\]',full) if int(m.group(1)) in mp]
    for m in reversed(ms): rep_span(p,m.start(),m.end(),'[%d]'%mp[int(m.group(1))])
for p in body: remap(p)
for t in d.tables:
    for r in t.rows:
        for c in r.cells:
            for p in c.paragraphs: remap(p)
# reference list
lines=open(MD,encoding='utf8').read().split('\n')
ents={}
for l in lines:
    m=re.match(r'^\[(\d+)\] (.*)$',l)
    if m: ents[int(m.group(1))]=m.group(2)
new=dict(ents)
for o,n in mp.items(): new[n]=ents[o]
assert sorted(new)==sorted(ents)
head=open(MD,encoding='utf8').read().split('\n[1] ')[0]
open(MD,'w',encoding='utf8').write(head+'\n[1] '+'\n'.join('[%d] %s'%(n,new[n]) for n in sorted(new)).split('[1] ',1)[1]+'\n')
refs=d.paragraphs[hi+1:]
tmpl=copy.deepcopy(refs[0]._p)
for p in refs: p._p.getparent().remove(p._p)
anchor=d.paragraphs[hi]._p
for n in range(1,46):
    nn=copy.deepcopy(tmpl); ts=list(nn.iter(W+'t'))
    for t_ in ts: t_.text=''
    ts[0].text='[%d] %s'%(n,new[n].replace(' (incomplete)',''))
    ts[0].set('{http://www.w3.org/XML/1998/namespace}space','preserve')
    anchor.addnext(nn); anchor=nn
d.save(OUT)
rd=Document(); rd.add_heading('References',level=1)
for n in range(1,46): rd.add_paragraph('[%d] %s'%(n,new[n].replace(' (incomplete)','')))
rd.add_paragraph(''); pp=rd.add_paragraph(); pp.add_run('Remaining sources (not yet cited; numbers provisional until first cited)').bold=True
for n in range(46,79): rd.add_paragraph('[%d] %s'%(n,new[n]))
rd.save('/home/user/mihk/stages/thesis_chapters/References_78.docx')
