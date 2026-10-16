#!/usr/bin/env python3
"""Appendix A (supplementary tables) and Appendix B (verification / campaign scripts). Output: results/Appendix_final.docx
All numbers come from results/final_campaign (tables_final.md, memory.csv); the script texts are copied verbatim from the repository."""
import re, csv, hashlib
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

R = "/home/user/mihk/"
d = Document()
st = d.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
for s in d.sections: s.left_margin = s.right_margin = Cm(2.5); s.top_margin = s.bottom_margin = Cm(2.5)

def para(t, bold=False, italic=False, size=None, align=None, space=6, keep=False):
    p = d.add_paragraph(); r = p.add_run(t); r.bold = bold; r.italic = italic
    if size: r.font.size = Pt(size)
    if align is not None: p.alignment = align
    p.paragraph_format.space_after = Pt(space)
    if keep: p.paragraph_format.keep_with_next = True
    return p

def borders(table):
    tblPr = table._tbl.tblPr; b = OxmlElement("w:tblBorders")
    for e in ("top", "bottom", "insideH"):
        x = OxmlElement("w:" + e); x.set(qn("w:val"), "single"); x.set(qn("w:sz"), "6"); x.set(qn("w:color"), "000000"); b.append(x)
    tblPr.append(b)

def table(head, rows, widths, size=9):
    t = d.add_table(rows=1, cols=len(head)); borders(t); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(head):
        c = t.rows[0].cells[i]; c.text = ""; r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(size)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""; r = cells[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(size)
            cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for row in t.rows:
        for i, w in enumerate(widths): row.cells[i].width = Cm(w)
    d.add_paragraph().paragraph_format.space_after = Pt(4)
    return t

def listing(path):
    for line in open(path, encoding="utf8").read().rstrip("\n").split("\n"):
        p = d.add_paragraph(); p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
        r = p.add_run(line if line else " "); r.font.name = "Courier New"; r.font.size = Pt(7.5)
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "Courier New")

# ---------------- Appendix A ----------------
para("Appendix A", bold=True, size=16, align=WD_ALIGN_PARAGRAPH.CENTER, space=2)
para("Supplementary Results", bold=True, size=14, align=WD_ALIGN_PARAGRAPH.CENTER, space=12)
para("A.1 Equal and Adaptive Workload Distribution by Image Type", bold=True)
para("Table A.1 reports the mean LBG and total execution times of the Equal and Adaptive strategies separately for the four grayscale and the four color images. "
     "Each time is the median of five runs, averaged over the images of the group. The reduction is the mean of the per-image relative reductions, "
     "R = (T_Equal − T_Adaptive) / T_Equal × 100, and negative values mean that the Adaptive strategy was slower. "
     "“Images faster” is the number of images for which the Adaptive time was lower than the Equal time.", space=8)

md = open(R + "results/final_campaign/tables_final.md", encoding="utf8").read()
i0 = md.index("### Equal vs Adaptive")
def block(tag):
    s = md.index(tag, i0); e = md.index("\n\n", s)
    rows = [l for l in md[s:e].split("\n")[1:] if l.startswith("|")][2:]
    return [[c.strip().replace("-", "−") if re.fullmatch(r"-\d+(\.\d+)?", c.strip()) else c.strip() for c in l.strip("|").split("|")] for l in rows]
head = ["P", "Equal LBG (s)", "Adaptive LBG (s)", "LBG reduction (%)", "Images faster", "Equal total (s)", "Adaptive total (s)", "Total reduction (%)", "Images faster"]
w = [1.0, 1.9, 1.9, 1.9, 1.6, 1.9, 1.9, 1.9, 1.6]
para("Table A.1. Mean execution times (s) of the Equal and Adaptive strategies and the relative reduction achieved by the Adaptive strategy: (a) grayscale images and (b) color images.", italic=True, space=4, keep=True)
para("(a) Grayscale images (four images)", bold=True, size=10, space=2, keep=True)
table(head, block("**grayscale (4)**"), w)
para("(b) Color images (four images)", bold=True, size=10, space=2, keep=True)
table(head, block("**color (4)**"), w)

para("A.2 Memory Usage", bold=True)
para("Table A.2 reports the peak resident set size (RSS) of the sequential program and of the MPI program at P = 4 and P = 14. "
     "The measurement was performed for two grayscale and two color images. For the MPI runs, the table gives the largest value among the ranks "
     "and the sum over all ranks.", space=8)
para("Table A.2. Peak resident memory of the sequential and MPI programs (MB).", italic=True, space=4, keep=True)
names = {"gray": "Lena (gray)", "boat_img": "Boat (gray)", "lena_color": "Lena (color)", "peppers_color2": "Peppers (color)"}
rows = []
for r in csv.DictReader(open(R + "results/final_campaign/memory.csv")):
    p = r["P"]
    rows.append([names[r["image"]], "Sequential" if p == "1" else f"MPI, P = {p}", r["peak_rss_max_rank_MB"], r["peak_rss_sum_all_ranks_MB"]])
table(["Image", "Program", "Peak RSS of the largest rank (MB)", "Sum over all ranks (MB)"], rows, [4.0, 3.6, 4.6, 3.8], size=10)
para("The sequential program required about 3.1–3.2 MB for the grayscale images and 4.9–5.0 MB for the color images. "
     "Each MPI process required about 21–23 MB, so the total memory grew with the number of processes (about 248 MB for grayscale and 290 MB for color images at P = 14).", space=6)

d.add_page_break()
# ---------------- Appendix B ----------------
para("Appendix B", bold=True, size=16, align=WD_ALIGN_PARAGRAPH.CENTER, space=2)
para("Verification and Measurement Scripts", bold=True, size=14, align=WD_ALIGN_PARAGRAPH.CENTER, space=12)
para("B.1 Verification Script", bold=True)
para("The script below was used for the verification described in Section 4.7. For every image it runs the sequential program, the MPI program with P = 4 (default Equal strategy), "
     "the MPI program with P = 14 (default Adaptive strategy) and the MPI program with P = 14 forced to the Equal strategy (VQ_STRATEGY=equal). "
     "It extracts the CR, MSE, PSNR, SSIM and the number of LBG iterations from the output of each run, compares them with the sequential reference, "
     "and compares the MD5 hashes of the reconstructed BMP files computed with the GNU md5sum utility. The default image list in the script is overridden by the IMGS "
     "variable, which the campaign script of Section B.2 sets to the eight images of this study. The output is written to correctness.csv.", space=6)
para("Listing B.1. run_correctness_nofilter.sh", italic=True, space=2, keep=True)
listing(R + "run_correctness_nofilter.sh")

para("", space=6)
para("B.2 Campaign Script", bold=True, keep=True)
para("The script below runs all measurements of Chapter Four from one build of the sequential and the MPI programs: verification, timing (median of five runs), "
     "Equal-versus-Adaptive comparison, entropy analysis, parameter study, the JPEG and JPEG 2000 reference, and memory usage. It checks that the AC power is connected "
     "and that the CPU governor is set to performance before the run starts.", space=6)
para("Listing B.2. run_final_campaign.sh", italic=True, space=2, keep=True)
listing(R + "run_final_campaign.sh")

para("", space=6)
para("B.3 Source Files", bold=True, keep=True)
para("Table B.1 lists the source files compiled for the reported results and their MD5 hashes.", space=4, keep=True)
para("Table B.1. Source files used for the reported results.", italic=True, space=4, keep=True)
def md5(f): return hashlib.md5(open(R + f, "rb").read()).hexdigest()
table(["Program", "Source file", "MD5"], [["Sequential (lbg_seq)", "sem_v3_nofilter_final.c", md5("sem_v3_nofilter_final.c")],
                                         ["MPI (lbg_par)", "pam_v4_nofilter_final.c", md5("pam_v4_nofilter_final.c")]], [4.0, 5.0, 7.0], size=10)
d.save(R + "results/Appendix_final.docx")
print("saved")
