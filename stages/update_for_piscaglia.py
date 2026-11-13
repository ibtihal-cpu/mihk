import re,copy
from docx import Document
UP1='/root/.claude/uploads/4ae9f12a-c6d9-593e-bdd1-593721fcd2b9/ce61ec04-Chapter_1_updated.docx'
SRC2='/home/user/mihk/stages/thesis_chapters/Chapter_2_updated_v2.docx'
OUT1='/home/user/mihk/stages/thesis_chapters/Chapter_1_updated_v2.docx'
OUT2='/home/user/mihk/stages/thesis_chapters/Chapter_2_updated_v3.docx'
MD='/home/user/mihk/stages/literature/References_Ch1_Ch2.md'
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def rep_span(p,i,j,new):
    runs=p.runs; pos=0; first=True
    for r in runs:
        a,b=pos,pos+len(r.text); pos=b
        if b<=i or a>=j: continue
        s=max(i,a)-a; e=min(j,b)-a
        if first: r.text=r.text[:s]+new+r.text[e:]; first=False
        else: r.text=r.text[:s]+r.text[e:]
def rep(p,old,new):
    full=''.join(r.text for r in p.runs); i=full.find(old)
    assert i>=0,(old,p.text[:60]); rep_span(p,i,i+len(old),new)
def remap(p):
    full=''.join(r.text for r in p.runs)
    ms=[m for m in re.finditer(r'\[(\d+)\]',full) if int(m.group(1))>=9]
    for m in reversed(ms): rep_span(p,m.start(),m.end(),'[%d]'%(int(m.group(1))+1))
    return len(ms)
def all_paras(doc):
    for p in doc.paragraphs: yield p
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                for p in c.paragraphs: yield p

# ---------- reference list ----------
lines=open(MD,encoding='utf8').read().split('\n')
ents={}
for l in lines:
    m=re.match(r'^\[(\d+)\] (.*)$',l)
    if m: ents[int(m.group(1))]=m.group(2)
assert len(ents)==77
pisc='P. Piscaglia, B. Macq, and P. Maes, "Distributed optimization of codebooks," Signal Processing: Image Communication, vol. 7, pp. 211-223, 1995, doi: 10.1016/0923-5965(94)00026-F.'
new={}
for n in range(1,9): new[n]=ents[n]
new[9]=pisc
for n in range(9,78): new[n+1]=ents[n]
assert len(new)==78
head=("# Unified reference list, Chapters 1 and 2 (IEEE, numbered by first appearance in the thesis)\n\n"
"Rule: [1]-[18] first appear in Chapter 1, [19]-[45] in Chapter 2 (Piscaglia et al. is [9]). A new reference in a later\n"
"chapter takes the next number ([79] onward); a reference already in the list keeps its number. [46]-[78] are sources of the\n"
"65-source list that are not yet cited; their numbers are provisional until first cited, and uncited ones must be deleted.\n\n"
"Status: entries marked (incomplete) lack volume/pages or authors; DOIs and details were not verified against the publishers.\n\n")
body='\n'.join('[%d] %s'%(n,new[n]) for n in sorted(new))
open(MD,'w',encoding='utf8').write(head+body+'\n')
# Word list
rd=Document(); rd.add_heading('References',level=1)
for n in range(1,46): rd.add_paragraph('[%d] %s'%(n,new[n].replace(' (incomplete)','')))
rd.add_paragraph('')
pp=rd.add_paragraph(); pp.add_run('Remaining sources (not yet cited; numbers provisional until first cited)').bold=True
for n in range(46,79): rd.add_paragraph('[%d] %s'%(n,new[n]))
rd.save('/home/user/mihk/stages/thesis_chapters/References_78.docx')

# ---------- Chapter 1 ----------
d=Document(UP1); cnt=0
for p in all_paras(d): cnt+=remap(p)
print('ch1 remapped',cnt)
def P(prefix):
    h=[p for p in d.paragraphs if p.text.strip().startswith(prefix)]; assert h,prefix; return h[0]
rep(P('Early research established'),'to parallel VQ codebook generation.',
 'to parallel VQ codebook generation. Piscaglia et al. [9] distributed the LBG algorithm over a network of workstations using the PVM library. Their design aimed to minimize the communication between the processors, and the load was balanced dynamically: the time of each processor was measured, and the training vectors were redistributed after every iteration so that all processors needed the same time. In tests on four workstations, the authors reported an efficiency of about 95% with the load balancing and a poor efficiency without it.')
rep(P('These studies established that LBG'),'The present thesis therefore focuses',
 'Piscaglia et al. [9] balanced the load dynamically on a network of workstations, whereas in this work the assignment of the training vectors is fixed after one measurement of the computation rate of each process, on a single hybrid processor. The present thesis therefore focuses')
rep(P('The reviewed studies have addressed'),'speed-aware workload partitioning','computation-rate-based workload distribution')
p=P('The present work addresses this combination')
rep(p,'equal distribution and adaptive speed-aware distribution','Equal distribution and computation-rate-based Adaptive distribution')
rep(p,"measured computational throughput","measured computation rate")
# Table 1.2: remap done; add Piscaglia row as first data row and renumber
t=d.tables[1]
tmpl=copy.deepcopy(t.rows[1]._tr)
t._tbl.insert(list(t._tbl).index(t.rows[1]._tr),tmpl)
vals=['1','[9]','Distributed LBG','PVM','Four workstations','Dynamic, after every iteration','Efficiency about 95% (4 processors)']
row=t.rows[1]
for c,v in zip(row.cells,vals):
    ps=c.paragraphs[0]; rs=[r for r in ps.runs]
    if rs:
        rs[0].text=v
        for r in rs[1:]: r.text=''
    else: ps.add_run(v)
for k,r in enumerate(t.rows[1:],start=1):
    c=r.cells[0].paragraphs[0]
    if c.runs:
        c.runs[0].text=str(k) if k<len(t.rows)-1 else '–'
        for x in c.runs[1:]: x.text=''
d.save(OUT1)
print('rows',[ [c.text for c in r.cells][:2] for r in Document(OUT1).tables[1].rows])

# ---------- Chapter 2 ----------
d2=Document(SRC2)
heads=[i for i,p in enumerate(d2.paragraphs) if p.text.strip()=='References']
hi=heads[0]
body_paras=d2.paragraphs[:hi]; ref_paras=d2.paragraphs[hi+1:]
cnt=0
for p in body_paras: cnt+=remap(p)
for t in d2.tables:
    for r in t.rows:
        for c in r.cells:
            for p in c.paragraphs: cnt+=remap(p)
print('ch2 remapped',cnt)
tmpl=copy.deepcopy(ref_paras[0]._p)
for p in ref_paras: p._p.getparent().remove(p._p)
anchor=d2.paragraphs[hi]._p
for n in range(1,46):
    nn=copy.deepcopy(tmpl)
    ts=list(nn.iter(W+'t'))
    for t_ in ts: t_.text=''
    ts[0].text='[%d] %s'%(n,new[n].replace(' (incomplete)',''))
    ts[0].set('{http://www.w3.org/XML/1998/namespace}space','preserve')
    anchor.addnext(nn); anchor=nn
d2.save(OUT2); print('saved')
