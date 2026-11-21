from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_BREAK
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_font(style, size, bold=False, italic=False):
    style.font.name = 'Times New Roman'; style.font.size = Pt(size)
    style.font.bold = bold; style.font.italic = italic; style.font.color.rgb = RGBColor(0, 0, 0)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')

def add_field(run, code):
    for t, txt in (('begin', None), (None, code), ('end', None)):
        if t:
            el = OxmlElement('w:fldChar'); el.set(qn('w:fldCharType'), t); run._r.append(el)
        else:
            it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = txt; run._r.append(it)

doc = Document()
s = doc.sections[0]
s.page_width, s.page_height = Cm(21.0), Cm(29.7)            # A4 (210 x 297 mm)
s.left_margin = Cm(4.0)                                      # binding side (English thesis: left)
s.right_margin = s.top_margin = s.bottom_margin = Cm(2.0)

n = doc.styles['Normal']; set_font(n, 12)
pf = n.paragraph_format
pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE        # line spacing 1.5
pf.first_line_indent = Cm(2.0)                               # paragraph indent 2 cm
pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
pf.space_after = Pt(0)

for name, size in (('Heading 1', 16), ('Heading 2', 14), ('Heading 3', 12)):
    h = doc.styles[name]; set_font(h, size, bold=True)
    h.paragraph_format.first_line_indent = Cm(0); h.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    h.paragraph_format.keep_with_next = True
cap = doc.styles['Caption']; set_font(cap, 11, bold=True)
cap.paragraph_format.first_line_indent = Cm(0); cap.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
cap.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

# page number at the top right of every page (continuous numbering of the whole thesis)
hp = s.header.paragraphs[0]; hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
hp.paragraph_format.first_line_indent = Cm(0)
add_field(hp.add_run(), 'PAGE')

def para(text, style='Normal', align=None, single=False, bold=False, indent=None):
    p = doc.add_paragraph(style=style)
    r = p.add_run(text); r.bold = bold
    if align is not None: p.alignment = align
    if single: p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    if indent is not None: p.paragraph_format.first_line_indent = indent
    return p

def page_break():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

C = WD_ALIGN_PARAGRAPH.CENTER
front = [
 ('1. Title page', ['University of Babylon (logo at the top right, university name below it)', 'THESIS TITLE (bold, centered)', 'A thesis submitted by: [student name]', 'Department / College', 'In partial fulfilment of the requirements for the degree of Master of Science in [specialization]', 'Supervisors: [names]', 'Month and year, Hijri and Gregorian']),
 ('2. Supervisor citation', ['[Supervisor certification text]']),
 ('3. Examination committee signatures, head of department, and dean approval', ['[Signature page]']),
 ('4. Dedication (optional)', ['[Text]']),
 ('5. Acknowledgments', ['[Text]']),
 ('6. Abstract (maximum 250 words)', ['[Abstract in English]']),
 ('7. Table of contents', ['[Insert > Reference > Table of Contents]']),
 ('8. List of symbols and abbreviations', ['[Symbols]']),
]
for title, lines in front:
    para(title, style='Heading 2')
    for l in lines: para(l, single=True, indent=Cm(0))
    page_break()

para('CHAPTER ONE', style='Heading 1', align=C)
para('INTRODUCTION', style='Heading 1', align=C)
para('1.1 Introduction', style='Heading 2')
para('Body text starts here. Paragraphs use Times New Roman 12 pt, black, justified, 1.5 line spacing, and a 2 cm first-line indent.')
para('Table 1.1. Example caption (single spacing, above the table).', style='Caption')
t = doc.add_table(rows=2, cols=3); t.style = 'Table Grid'
for i, row in enumerate([['Column A', 'Column B', 'Column C'], ['0.00', '0.00', '0.00']]):
    for j, v in enumerate(row):
        c = t.cell(i, j); c.text = ''; r = c.paragraphs[0].add_run(v); r.font.size = Pt(10); r.bold = (i == 0)
        c.paragraphs[0].paragraph_format.first_line_indent = Cm(0)
        c.paragraphs[0].paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        c.paragraphs[0].alignment = C
para('Block quotations, footnotes, and table text use single spacing.', single=True, indent=Cm(0))
page_break()
for title in ('References', 'Appendices', 'Abstract in Arabic (maximum 250 words)'):
    para(title, style='Heading 1')
    page_break()
doc.save('Thesis_Template_UoBabylon.docx')

# compliance checklist
rows = [
 ('Structure', 'Title and Arabic abstract, introduction (problem and objectives), literature review, methods, results and discussion, conclusions and recommendations, abstract in a foreign language', 'Chapters 1 to 4 exist. Still needed: Conclusions and Recommendations chapter, Arabic abstract, English abstract (each at most 250 words)'),
 ('Research plan items', 'Title, importance, research problem, previous studies, hypotheses, method, definition of concepts', 'Check Chapter 1 has: problem statement, objectives, a hypotheses section (for example, Adaptive distribution reduces LBG time compared with Equal without changing the compressed output), and definitions of key concepts'),
 ('Previous studies', 'For each study: problem, hypotheses, method and tools, results, and your own opinion and evaluation', 'Section 1.2 gives method, platform, and results. Still needed: one evaluation sentence per study (strengths and weaknesses), not only limitation relative to this work'),
 ('Source attribution', 'Copied text without attribution leads to rejection or withdrawal of the degree', 'All studies are paraphrased with citations. Run a similarity check before submission and rewrite any passage close to a source'),
 ('Length', 'Scientific master thesis: 120 pages', 'Count pages after Chapter 5 is added; move detail to appendices if needed'),
 ('Page', 'A4 (210 x 297 mm), single paper type', 'Template set'),
 ('Margins', '4 cm on the binding side, 2 cm on the other sides', 'Template set (left 4 cm, others 2 cm)'),
 ('Line spacing', '1.5 for text; single for footnotes and quotations', 'Template set; tables and captions single'),
 ('Paragraph', 'First line indent 2 cm', 'Template set'),
 ('Font and colour', 'Clear print, uniform characters, black', 'Times New Roman 12 pt, black'),
 ('Numbering', 'Continuous across the whole thesis, including front matter and indexes; page number at the top', 'Template: field at the top right of every page'),
 ('Cover page', 'Logo top right and university name below; bold title; thesis statement; student name; department; degree sentence; Hijri and Gregorian date', 'To prepare'),
 ('Front matter order', 'Title page, supervisor citation, committee signatures and approvals, dedication, acknowledgments, abstract, contents, list of symbols, body, references, appendices, foreign abstract', 'Template lists them in this order'),
 ('Figures and tables', 'Unrelated figures numbered separately; supervisor rules: cite each figure, table, algorithm, and equation in the text before it appears, with a sentence on its idea', 'Check at the final numbering pass'),
 ('Terminology (supervisor)', 'Use Process 0, not rank; Adaptive and computation rate, not speed-aware', 'Check all chapters (Chapter 3 still contains Rank)'),
 ('Defence', 'Within the legal study period', 'Check the dates with the department'),
]
d = Document()
sec = d.sections[0]; sec.left_margin = sec.right_margin = Cm(2)
d.add_heading('Compliance checklist: University of Babylon thesis regulations', level=1)
tb = d.add_table(rows=1, cols=3); tb.style = 'Table Grid'
for j, h in enumerate(('Requirement', 'Regulation', 'Status in this thesis / action')):
    c = tb.rows[0].cells[j]; c.text = ''; r = c.paragraphs[0].add_run(h); r.bold = True
for a, b, c_ in rows:
    cells = tb.add_row().cells
    for j, v in enumerate((a, b, c_)): cells[j].text = v
for row in tb.rows:
    for c in row.cells:
        for p in c.paragraphs:
            for r in p.runs: r.font.size = Pt(9)
d.save('Thesis_Compliance_Checklist.docx')
print('ok')
