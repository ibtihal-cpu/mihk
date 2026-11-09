import copy,re,sys
from docx import Document
SRC='/root/.claude/uploads/4ae9f12a-c6d9-593e-bdd1-593721fcd2b9/c6fcdf92-chapter-2.docx'
OUT='/home/user/mihk/stages/thesis_chapters/Chapter_2_updated_citations.docx'
REFS='/home/user/mihk/stages/literature/References_Ch1_Ch2.md'
doc=Document(SRC)
paras=doc.paragraphs
log=[]
def find(prefix,nth=0):
    hits=[p for p in doc.paragraphs if p.text.strip().startswith(prefix)]
    if len(hits)<=nth: raise SystemExit('NOT FOUND: '+prefix)
    return hits[nth]
def rep(p,old,new,count=1):
    """replace first occurrence of old in paragraph (run-aware)"""
    done=0
    while done<count:
        runs=p.runs; full=''.join(r.text for r in runs)
        i=full.find(old)
        if i<0: raise SystemExit('TEXT NOT FOUND: %r in %r'%(old,p.text[:60]))
        j=i+len(old); pos=0; first=True
        for r in runs:
            a,b=pos,pos+len(r.text); pos=b
            if b<=i or a>=j: continue
            s=max(i,a)-a; e=min(j,b)-a
            if first:
                r.text=r.text[:s]+new+r.text[e:]; first=False
            else:
                r.text=r.text[:s]+r.text[e:]
        done+=1
        log.append((p.text[:40],old,new))
def R(prefix,pairs,nth=0):
    p=find(prefix,nth)
    for o,n in pairs: rep(p,o,n)
R('The rapid development of digital imaging',[('[1],[3]','[18], [19]'),('[1], [4], [6]','[18], [20], [21]'),('[5], [7], [8]','[4], [22], [23]'),('[9], [10]','[24], [25]')])
R('Image compression techniques are generally',[('[11]','[2]')])
R('Vector quantization (VQ) is a lossy',[('[12]','[26]')])
R('The quantization operation can be expressed as',[('expressed as','expressed as [26], [27]')])
R('The Linde',[('[5], [12],[15]','[4], [26], [27]')])
R('The algorithm begins with an initial codebook',[('distance:','distance [26]:')])
R('After all vectors have been assigned',[('cluster:','cluster [26]:')])
R('Where,',[('calculated as:','calculated as [26]:')])
R('The assignment and centroid-update operations continue',[('[15]','[27]')])
R('The codebook may be expanded through binary splitting',[('codewords.','codewords [26].')])
R('here δ denotes',[('[12]','[26]')])
R('Although LBG provides',[('[12], [14]','[4], [12]')])
R('Delta coding, also known as',[('[30]','[27], [28]')])
R('Huffman coding is a lossless coding technique',[('probability model.','probability model [29].'),('[15]','[27]')] ) if False else None
p=find('Huffman coding is a lossless coding technique'); rep(p,'probability model.','probability model [29].')
if '[15]' in p.text: rep(p,'[15]','[27]')
R('The Huffman code is constructed',[('[15]','[27]')])
R('The information content and entropy',[('[15]','[27]')])
R('Huffman coding has been employed',[('[21]','[30]'),('[9]','[24]')])
R('The compression ratio measures',[('defined as:','defined as [27]:')])
R('The maximum peak signal-to-noise',[('as follows:','as follows [27]:')])
R('difference:',[('difference:','difference [27]:')])
R('SSIM is a well-known',[('similarity :','similarity [31]:')])
R('Speedup measures the performance',[('[13]','[34], [41]')])
R('The Karp',[('[14]','[33]')])
R('Parallel computing is a computational approach',[('[16], [17]','[34], [35]')])
for pre in ('Parallel hardware provides','Parallel architectures can also be classified'):
    R(pre,[('[16]','[34]')])
R('Figure 2.1.',[('[16]','[34]')])
R('Parallel architectures are commonly classified',[('[16]','[34]'),('[16]','[34]')])
R('Multicore processors may be homogeneous',[('processor [20]','processor [7], [36]'),('[20]','[36]')])
R('Parallel software organizes',[('[17]','[35]')])
R('Work can be decomposed',[('[18]','[37]')])
R('Parallel programming models provide',[('[19]','[38]'),('[13], [14]','[32], [39]')])
R('Figure 2.2.',[('[16]','[34]')])
R('Amdahl',[('parallel program.','parallel program [40].')])
R('As P increases',[('[#]','[40], [41]')])
R('The Message Passing Interface (MPI) is a standardized',[('[16], [25]','[34], [42]')])
R('MPI organizes processes into groups',[('[16], [25]','[34], [42]')])
R('This study classifies MPI communication',[('[25]','[42]')])
R('Point-to-point communication transfers',[('[16], [25]','[34], [42]')])
R('All processes within a communicator',[('[25]','[42]')])
R('MPI_Bcast distributes',[('[62]','[42]')])
R('MPI_Scatterv distributes',[('[62]','[42]')])
R('Conversely, MPI_Gatherv',[('[62]','[42]')])
R('MPI_Allgather collects',[('[25]','[42]')])
R('MPI_Allreduce combines',[('[25]','[42]')])
R('MPI_Barrier is a collective',[('[25]','[42]')])
R('Load balancing distributes',[('[26]','[43]')])
R('Load imbalance occurs',[('[27]','[44]')])
R('The objective of load balancing',[('[26], [27]','[43], [44]')])
# references: delete old, insert unified
sch=find('[#] G. Schryen'); 
start=find('References')
body=start._p.getparent()
# collect old reference paragraphs after heading 'References'
allp=doc.paragraphs; idx=[i for i,p in enumerate(allp) if p._p is start._p][0]
old=allp[idx+1:]
tmpl=copy.deepcopy(old[0]._p)
for p in old: p._p.getparent().remove(p._p)
sch._p.getparent().remove(sch._p)
entries=[l.strip() for l in open(REFS,encoding='utf8') if re.match(r'^\[\d+\] ',l)]
assert len(entries)==44,len(entries)
anchor=start._p
for e in entries:
    n=copy.deepcopy(tmpl)
    for t in n.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'): t.text=''
    ts=list(n.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
    ts[0].text=e.replace(' (incomplete)','')
    ts[0].set('{http://www.w3.org/XML/1998/namespace}space','preserve')
    anchor.addnext(n); anchor=n
doc.save(OUT)
print('edits',len(log)); print('saved',OUT)
