from docx import Document
SRC='/root/.claude/uploads/4ae9f12a-c6d9-593e-bdd1-593721fcd2b9/8e1f8f3c-chapter-1.docx'
OUT='/home/user/mihk/stages/thesis_chapters/Chapter_1_updated.docx'
d=Document(SRC)
def rep(p,old,new,nth=0):
    runs=p.runs; full=''.join(r.text for r in runs)
    i=-1
    for _ in range(nth+1):
        i=full.find(old,i+1)
        assert i>=0,(old,p.text[:60])
    j=i+len(old); pos=0; first=True
    for r in runs:
        a,b=pos,pos+len(r.text); pos=b
        if b<=i or a>=j: continue
        s=max(i,a)-a; e=min(j,b)-a
        if first: r.text=r.text[:s]+new+r.text[e:]; first=False
        else: r.text=r.text[:s]+r.text[e:]
def P(prefix):
    h=[p for p in d.paragraphs if p.text.strip().startswith(prefix)]
    assert h,prefix; return h[0]
rep(P('Image compression can be achieved'),'(DWT), as well as Vector Quantization (VQ) [3].','(DWT) [3], as well as Vector Quantization (VQ).')
rep(P('To the best of our knowledge, the studies reviewed in Section'),'Section 1.2','Section 1.5')
rep(P('Previous studies have investigated parallel LBG'),'Section 1.2','Section 1.5')
rep(P('1.4'),'Theses Contribution','Thesis Contributions')
for old,new in [('1.2.1','1.5.1'),('1.2.2','1.5.2'),('1.2.3','1.5.3'),('1.2.4','1.5.4'),('1.2.5','1.5.5')]:
    rep(P(old+' '),old,new)
p=P('Early research established several approaches'); rep(p,'[10]','[9]'); rep(p,'[11]','[10]')
rep(P('Wakatani [12]'),'[12]','[11]')
rep(P('Annaji and Rao [7]'),'[7]','[12]')
rep(P('Fernández-Fraga et al. [9]'),'[9]','[8]')
rep(P('Velugoti et al. [8]'),'[8]','[7]')
t=d.tables[1]; mp={'[12]':'[11]','[7]':'[12]','[9]':'[8]','[8]':'[7]'}
n=0
for r in t.rows[1:]:
    c=r.cells[1]; tx=c.text.strip()
    if tx in mp:
        rep(c.paragraphs[0],tx,mp[tx]); n+=1
assert n==4,n
d.save(OUT); print('saved')
