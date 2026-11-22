import copy
from docx import Document
SRC='/home/user/mihk/stages/thesis_chapters/Chapter_1_updated.docx'
OUT='/home/user/mihk/stages/thesis_chapters/Chapter_1_updated.docx'
d=Document(SRC)
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
def P(prefix):
    h=[p for p in d.paragraphs if p.text.strip().startswith(prefix)]
    assert h,prefix; return h[0]
def append(p,text):
    last=[r for r in p.runs if r.text][-1]
    last.text=last.text.rstrip()+text
# Table 1.1 intro sentence
append(P('These studies addressed the computational cost of codebook generation'),
 ' Table 1.1 summarizes the images, compression ratios, and PSNR values reported in the hybrid compression and VQ codebook design studies reviewed above.')
# Table 1.2 intro sentence
append(P('These studies examined heterogeneous processing'),
 ' Table 1.2 compares the parallel model, platform, workload distribution, and reported speedup of the studies reviewed in Sections 1.5.3 to 1.5.5 with the proposed work. The speedups were obtained with different algorithms, baselines, processor counts, and platforms; they describe previous findings and do not establish direct experimental comparisons.')
# Table 1.2 caption (copy of the Table 1.1 caption paragraph)
cap=P('Table 1.1.')
new=copy.deepcopy(cap._p)
ts=list(new.iter(W+'t'))
ts[0].text='Table 1.2. Comparison of parallel image compression and workload-balancing studies'
for t in ts[1:]: t.text=''
tbl2=d.tables[1]._tbl
tbl2.addprevious(new)
d.save(OUT); print('ok')
