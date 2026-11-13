"""Build one Word file: Section 4.9 (portrait) followed by the literature summary table (landscape)."""
import re
from docx.enum.section import WD_SECTION

ns = {}
src49 = open('make_section_4_9.py').read()
src49 = src49.replace("doc.save('Section_4_9_Comparison.docx')", "").replace("print('ok')", "")
exec(compile(src49, 'sec49', 'exec'), ns)
doc = ns['doc']

srcl = open('literature/make_literature_table.py').read()
# reuse the same document: new landscape section instead of a new Document
srcl = srcl.replace("doc = Document()\nsec = doc.sections[0]; sec.orientation = WD_ORIENT.LANDSCAPE\nsec.page_width, sec.page_height = sec.page_height, sec.page_width",
                    "sec = doc.add_section(WD_SECTION.NEW_PAGE); sec.orientation = WD_ORIENT.LANDSCAPE\nsec.page_width, sec.page_height = sec.page_height, sec.page_width")
srcl = srcl.replace("st = doc.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(8)", "")
srcl = srcl.replace("doc.save('Literature_Summary.docx')", "")
srcl = srcl[:srcl.index("with open('Literature_Summary.md'")]
ns2 = dict(ns); ns2['doc'] = doc; ns2['WD_SECTION'] = WD_SECTION
exec(compile(srcl, 'lit', 'exec'), ns2)
ns2['doc'].save('Chapter4_Comparison_and_Literature.docx')
print('saved')
