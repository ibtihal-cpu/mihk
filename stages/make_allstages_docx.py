#!/usr/bin/env python3
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
d = Document(); st = d.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
for s in d.sections: s.left_margin = s.right_margin = Cm(2.2); s.top_margin = s.bottom_margin = Cm(2.0)
def P(t, it=False, sz=None):
    p = d.add_paragraph(); r = p.add_run(t); r.italic = it
    if sz: r.font.size = Pt(sz)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; p.paragraph_format.space_after = Pt(8)
def CAP(t):
    p = d.add_paragraph(); r = p.add_run(t); r.bold = True; r.font.size = Pt(11); p.paragraph_format.keep_with_next = True; p.paragraph_format.space_after = Pt(4)
def T(rows, w, size=10):
    t = d.add_table(rows=len(rows), cols=len(rows[0])); t.style = 'Table Grid'; t.autofit = False; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, x in enumerate(w): t.columns[j].width = Cm(x)
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.cell(i, j); c.width = Cm(w[j]); c.text = ''; r = c.paragraphs[0].add_run(str(v)); r.font.size = Pt(size)
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            if i == 0:
                r.bold = True; sh = OxmlElement('w:shd'); sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), 'D9E2F3'); c._tc.get_or_add_tcPr().append(sh)
    d.add_paragraph().paragraph_format.space_after = Pt(2)
h = d.add_heading('Execution time of every stage (Section 4.5.5) - ready to paste', 1)
for r in h.runs: r.font.name = 'Times New Roman'
P('Measured in one session with instrumented copies of the programs (identical compressed output), four grayscale images, five repetitions, '
  'mean over the images of the median. Equal distribution for P ≤ 6 and Adaptive for P > 6.', it=True, sz=10)
P('Table 4.x reports the mean execution time of each stage for the four grayscale images at P = 1 (sequential), 4, 8, and 14. Other is the sum of the '
  'remaining stages of the Total processing time (Table 4.y). The stages add up to the Total processing time within 0.03 ms.')
CAP('Table 4.x. Execution time of each stage for the grayscale images (ms).')
T([['P', 'LBG', 'Delta', 'Huffman', 'Decoding', 'Other', 'Total'],
   ['1', '251.04', '0.006', '0.181', '0.316', '0.36', '251.90'],
   ['4', '66.68', '0.007', '0.185', '0.382', '0.36', '67.64'],
   ['8', '40.50', '0.008', '0.191', '0.389', '1.49', '42.57'],
   ['14', '27.63', '0.008', '0.195', '0.387', '1.57', '29.79']], [1.5, 2.4, 2.1, 2.3, 2.4, 2.1, 2.4])
P('The LBG training accounted for 99.7% of the sequential Total processing time and for 92.8% at P = 14. Delta coding, Huffman encoding, and decoding '
  'together took about 0.5–0.6 ms at every P, i.e., 0.2% of the Total processing time in the sequential program and 2.0% at P = 14.')
P('Table 4.y shows what the remaining stages contain.')
CAP('Table 4.y. Components of Other in Table 4.x (ms).')
T([['P', 'Building the vectors', 'Float conversion and synchronization', 'Distribution and calibration', 'Scatter', 'Initial mean', 'Gather', 'Codebook to 8 bits', 'Other'],
   ['1', '0.123', '0.233', '0', '0', '0', '0', '0.002', '0.36'],
   ['4', '0.130', '0.095', '0.003', '0.107', '0.022', '0.005', '0.003', '0.36'],
   ['8', '0.136', '0.057', '1.177', '0.075', '0.011', '0.029', '0.003', '1.49'],
   ['14', '0.136', '0.043', '1.217', '0.123', '0.010', '0.037', '0.003', '1.57']], [1.0, 2.1, 2.6, 2.4, 1.5, 1.6, 1.4, 2.0, 1.4], size=9)
P('For P ≤ 6, where the Equal distribution is used, the work distribution took only 0.003 ms. For P = 8 and 14, where the Adaptive distribution is used, the '
  'distribution including the computation-rate calibration took 1.18 and 1.22 ms, which is about 4% of the Total processing time at P = 14. Together with '
  'the scattering and gathering of the data and the three post-training stages, these stages explain why the speedup of the Total processing time is lower '
  'than the speedup of the LBG training alone.')
P('Notes: the three post-training stages are executed by Process 0 and their time is almost independent of P; the calibration is the main cost that the '
  'Adaptive strategy adds. The speedups reported in Section 4.5 come from the main measurement session.', it=True, sz=10)
d.save('stages/Table_all_stages.docx'); print('saved')
