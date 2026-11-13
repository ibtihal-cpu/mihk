#!/usr/bin/env python3
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
gray = [('boat_gray', [6,14,34,34,29,34]), ('cameraman_gray', [6,9,30,42,39,29]), ('lena_gray', [6,14,23,47,29,41]), ('peppers_gray', [3,9,8,28,33,51])]
color = [('f16_color','R',[7,9,28,26,34,31]), ('f16_color','G',[7,22,33,38,42,38]), ('f16_color','B',[6,13,22,25,51,47]),
         ('goldhill_color','R',[9,7,15,37,28,36]), ('goldhill_color','G',[24,6,11,65,39,28]), ('goldhill_color','B',[9,13,10,67,40,35]),
         ('lena_color','R',[6,16,22,36,39,35]), ('lena_color','G',[7,13,21,52,29,25]), ('lena_color','B',[12,4,6,56,59,38]),
         ('peppers_color2','R',[6,15,8,43,43,37]), ('peppers_color2','G',[4,14,19,27,45,43]), ('peppers_color2','B',[5,8,16,35,39,31])]
d = Document(); st = d.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
for s in d.sections: s.left_margin = s.right_margin = Cm(2.5); s.top_margin = s.bottom_margin = Cm(2.2)
def P(t, it=False, sz=None, j=False):
    p = d.add_paragraph(); r = p.add_run(t); r.italic = it
    if sz: r.font.size = Pt(sz)
    if j: p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(8)
def CAP(t):
    p = d.add_paragraph(); r = p.add_run(t); r.bold = True; r.font.size = Pt(11); p.paragraph_format.keep_with_next = True; p.paragraph_format.space_after = Pt(4)
def T(rows, w, bold=()):
    t = d.add_table(rows=len(rows), cols=len(rows[0])); t.style = 'Table Grid'; t.autofit = False; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, x in enumerate(w): t.columns[j].width = Cm(x)
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.cell(i, j); c.width = Cm(w[j]); c.text = ''; r = c.paragraphs[0].add_run(str(v)); r.font.size = Pt(10)
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
            if i == 0 or i in bold: r.bold = True
            if i == 0:
                sh = OxmlElement('w:shd'); sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), 'D9E2F3'); c._tc.get_or_add_tcPr().append(sh)
    d.add_paragraph().paragraph_format.space_after = Pt(2)
h = d.add_heading('LBG iterations per splitting stage (ready to paste)', 1)
for r in h.runs: r.font.name = 'Times New Roman'
P('Place: Section 4.5 (sequential LBG), or where the number of LBG iterations is first reported. Table numbers are temporary.', it=True, sz=10)
P('The limit of 100 iterations applies to each splitting stage (each codebook size 2, 4, 8, 16, 32, and 64), not to the whole training. '
  'The number of LBG iterations reported in the result tables is the total over the six splitting stages, and for the color images over the three channels. '
  'The number of iterations of every stage was recorded for all eight images (Tables 4.u and 4.v). No stage reached the limit of 100: '
  'the largest number of iterations in a single stage was 51 for the grayscale images and 67 for the color images, so every stage stopped because the relative '
  'decrease of the distortion fell below ε = 0.0001. The total number of iterations ranged from 132 to 160 for the grayscale images (mean 149.5) '
  'and from 132 to 180 per channel for the color images (from 438 to 479 per image, mean 468).', j=True)
CAP('Table 4.u: Number of LBG iterations in each splitting stage, grayscale images (sequential program).')
rows = [['Image', 'k=2', 'k=4', 'k=8', 'k=16', 'k=32', 'k=64', 'Total', 'Largest stage']]
for n, v in gray: rows.append([n.replace('_gray', ''), *v, sum(v), max(v)])
rows.append(['Mean', *[f'{sum(x[1][i] for x in gray)/4:.1f}' for i in range(6)], '149.5', f'{sum(max(x[1]) for x in gray)/4:.1f}'])
T(rows, [2.9, 1.3, 1.3, 1.3, 1.4, 1.4, 1.4, 1.5, 2.3], bold=(5,))
CAP('Table 4.v: Number of LBG iterations in each splitting stage, color images (sequential program, per channel).')
rows = [['Image', 'Channel', 'k=2', 'k=4', 'k=8', 'k=16', 'k=32', 'k=64', 'Total', 'Largest stage']]
for n, c, v in color: rows.append([n.replace('_color2', '').replace('_color', ''), c, *v, sum(v), max(v)])
T(rows, [2.4, 1.9, 1.2, 1.2, 1.2, 1.3, 1.3, 1.3, 1.3, 1.9])
P('Note: in the verification experiments (Section 4.7) the iteration counts of the parallel runs were identical to those of the sequential program, so these counts also apply to the parallel program.', it=True, sz=10)
d.save('stages/Iterations_per_stage.docx'); print('saved')
