from docx import Document
SRC='/home/user/mihk/stages/thesis_chapters/Chapter_2_updated_citations.docx'
OUT='/home/user/mihk/stages/thesis_chapters/Chapter_2_updated_v2.docx'
d=Document(SRC)
M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
def find(prefix):
    h=[p for p in d.paragraphs if p.text.strip().startswith(prefix)]
    assert h,prefix
    return h[0]
def rep(p,old,new):
    runs=p.runs; full=''.join(r.text for r in runs); i=full.find(old)
    assert i>=0,(old,p.text[:50]); j=i+len(old); pos=0; first=True
    for r in runs:
        a,b=pos,pos+len(r.text); pos=b
        if b<=i or a>=j: continue
        s=max(i,a)-a; e=min(j,b)-a
        if first: r.text=r.text[:s]+new+r.text[e:]; first=False
        else: r.text=r.text[:s]+r.text[e:]
rep(find('The dimensions of the original'),'The dimensions of the original and compressed images are denoted by B_compressed and B_original, respectively.','The sizes of the original and compressed images are denoted by B_original and B_compressed, respectively.')
# equation 2.8: denominator subscript 'compression' -> 'compressed'
eq=find('CR =')._p; n=0
for t in eq.iter(M+'t'):
    if t.text=='compression': t.text='compressed'; n+=1
assert n==1,n
rep(find('These variable-size collective operations'),'both equal and throughput-aware distribution','both Equal and Adaptive distribution')
rep(find('In the adaptive workload-distribution strategy'),'In the adaptive workload-distribution strategy, MPI_Allgather exchanges the computational throughput measured','In the Adaptive distribution strategy, MPI_Allgather exchanges the computation rate measured')
rep(find('Figure Figure 2.5.'),'Figure Figure 2.5.','Figure 2.5.')
rep(find('Figure2. 8.'),'Figure2. 8.','Figure 2.8.')
rep(find('Figure 2.10.'),'Figure 2.10.','Figure 2.9.')
rep(find('2.12 Summary'),'2.12 Summary','2.11 Summary')
d.save(OUT); print('saved')
