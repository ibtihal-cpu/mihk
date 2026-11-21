#!/usr/bin/env python3
from docx import Document
from docx.shared import Pt, Cm
from docx.oxml.ns import qn
EQ = [
 ('Squared Euclidean distance between a vector and a codeword', '(1)',
  'd(x, c_j) = Σ_{i=1}^{16} (x_i − c_{j,i})² = ‖x − c_j‖₂²',
  r'd(\mathbf{x},\mathbf{c}_j)=\sum_{i=1}^{16}(x_i-c_{j,i})^2=\lVert\mathbf{x}-\mathbf{c}_j\rVert_2^2'),
 ('Quantization operation and nearest-codeword rule', '(2)',
  'Q(x) = c_{j*},   j* = arg min_{1≤j≤K} d(x, c_j)',
  r'Q(\mathbf{x})=\mathbf{c}_{j^*},\quad j^*=\arg\min_{1\le j\le K} d(\mathbf{x},\mathbf{c}_j)'),
 ('Initial codeword (global mean of the N training vectors)', '(3)',
  'c_1 = (1/N) Σ_{n=1}^{N} x_n',
  r'\mathbf{c}_1=\frac{1}{N}\sum_{n=1}^{N}\mathbf{x}_n'),
 ('Codeword splitting (δ = 0.01); the codebook grows 1 → 2 → 4 → … → 64 (six stages)', '(4)',
  'c_j^(1) = (1 + δ) c_j,   c_j^(2) = (1 − δ) c_j',
  r'\mathbf{c}_j^{(1)}=(1+\delta)\mathbf{c}_j,\quad \mathbf{c}_j^{(2)}=(1-\delta)\mathbf{c}_j'),
 ('Cell of codeword j', '(5)',
  'S_j = { x_n : j*(x_n) = j }',
  r'S_j=\{\mathbf{x}_n : j^*(\mathbf{x}_n)=j\}'),
 ('Centroid update (a codeword with an empty cell is left unchanged)', '(6)',
  'c_j = (1/|S_j|) Σ_{x_n ∈ S_j} x_n',
  r'\mathbf{c}_j=\frac{1}{|S_j|}\sum_{\mathbf{x}_n\in S_j}\mathbf{x}_n'),
 ('Average distortion after iteration m', '(7)',
  'D_m = (1/N) Σ_{n=1}^{N} min_{1≤j≤K} d(x_n, c_j)',
  r'D_m=\frac{1}{N}\sum_{n=1}^{N}\min_{1\le j\le K} d(\mathbf{x}_n,\mathbf{c}_j)'),
 ('Stopping rule of one splitting stage (ε = 10⁻⁴, at most 100 iterations per stage)', '(8)',
  '(D_{m−1} − D_m) / D_m ≤ ε',
  r'\frac{D_{m-1}-D_m}{D_m}\le\varepsilon'),
]
d = Document(); st = d.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
for s in d.sections: s.left_margin = s.right_margin = Cm(2.3)
d.add_heading('LBG equations - plain text version (displays everywhere)', 1)
p = d.add_paragraph('x = a 4 × 4 block as a vector of 16 values; c_j = codeword j (K = 64); N = 16,384 blocks; subscripts are written with "_" and superscripts with "^" where needed. '
                    'Under each equation is the LaTeX form: in Word press Alt + = , paste it, and press Enter to get a real equation.')
p.runs[0].italic = True
for title, num, uni, tex in EQ:
    q = d.add_paragraph(); r = q.add_run(f'{num}  {title}'); r.bold = True; q.paragraph_format.space_before = Pt(8); q.paragraph_format.keep_with_next = True
    e = d.add_paragraph(); r = e.add_run(uni); r.font.name = 'Cambria Math'; r.font.size = Pt(13)
    e.paragraph_format.left_indent = Cm(1.0); e.paragraph_format.space_after = Pt(1)
    l = d.add_paragraph(); r = l.add_run(tex); r.font.name = 'Consolas'; r.font.size = Pt(9); l.paragraph_format.left_indent = Cm(1.0)
d.save('stages/LBG_equations_text.docx'); print('saved')
