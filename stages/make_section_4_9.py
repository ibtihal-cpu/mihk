from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()
for s in doc.sections:
    s.left_margin = s.right_margin = Cm(2.5)
st = doc.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')

def para(text, bold=False, italic=False, align=None, size=None):
    p = doc.add_paragraph()
    r = p.add_run(text); r.bold = bold; r.italic = italic
    if size: r.font.size = Pt(size)
    if align == 'j': p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p

def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), color)
    tcPr.append(shd)

def table(rows, widths=None, bold_last=False):
    t = doc.add_table(rows=len(rows), cols=len(rows[0])); t.style = 'Table Grid'
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j); c.text = ''
            run = c.paragraphs[0].add_run(val); run.font.size = Pt(10.5)
            if i == 0: run.bold = True; shade(c, 'D9D9D9')
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER if j > 0 else WD_ALIGN_PARAGRAPH.LEFT
    return t

para('4.9 Comparison with Previous Studies', bold=True, size=14)
para('This section places the results in the context of previous work in two respects: compression ratio and quality on the common test images (Table 4.20), and parallel speedup for image compression (Table 4.21). The comparisons with the sequential program and with the Equal distribution, which corresponds to the equal partitioning of training vectors used in previous parallel LBG implementations, were obtained under identical conditions in Sections 4.5 and 4.6. The comparisons in this section use values reported in the cited studies and are given for reference only, because the studies differ in algorithm, implementation language, hardware, baseline, and the stages included in the measured time. The same image names do not guarantee identical image files, preprocessing, or compressed-size accounting.', align='j')

para('Table 4.20. Compression ratio and PSNR on the common 512 × 512 test images.', bold=True)
table([
 ['Image','Method','CR','PSNR (dB)'],
 ['Peppers','Li and U (2026)','21.10','31.43'],
 ['','This work','25.30','29.41'],
 ['Cameraman','Li and U (2026)','20.29','32.53'],
 ['','This work','29.60','29.75'],
])
doc.add_paragraph()
para('Table 4.21. Parallel speedup reported for image compression and in this work.', bold=True)
table([
 ['Study','Compression method','Platform','Baseline','Speedup'],
 ['Hernandez-Lopez and Muñiz-Pérez (2022)','Fractal, quadtree partition','Multi-core CPU (task parallelism)','Serial implementation','≈15×'],
 ['','','GPU (CUDA dynamic parallelism)','Serial implementation','≈25×'],
 ['Zangana (2025)','Bitplane, wavelet, predictive coding','Up to 16 GPUs','1 GPU','9.09×'],
 ['This work','LBG-VQ, delta, canonical Huffman','14 MPI processes (6 P-cores + 8 E-cores)','Sequential program','9.18× (LBG); 8.54× (Total, gray); 8.83× (Total, color)'],
])
doc.add_paragraph()
para('Discussion', bold=True)
para('Table 4.20 shows that the proposed method achieves higher compression ratios than Li and U (2026) for Peppers and Cameraman, while their method provides higher PSNR values. This indicates a difference in the trade-off between compression ratio and reconstruction quality. Since the two studies use different compression methods, these results should not be interpreted as a direct ranking of their overall performance.', align='j')
para('Table 4.21 presents reported parallel speedups from previous image compression studies alongside the results of the proposed method. Hernandez-Lopez and Muñiz-Pérez (2022) report approximate speedups of 15× on a multicore CPU and 25× on a GPU relative to a serial implementation. Zangana (2025) reports a speedup of 9.09× using 16 GPUs relative to a single GPU. In comparison, the proposed method achieves an LBG speedup of 9.18× at 14 MPI processes, with Total processing speedups of 8.54× and 8.83× for grayscale and color images, respectively.', align='j')
para('These values provide a reference for parallel performance rather than a direct comparison, as the studies differ in compression algorithms, hardware platforms, sequential baselines, and measured processing stages. The effectiveness of the proposed Adaptive distribution is therefore established primarily through the controlled experiments presented in Sections 4.5 and 4.6. Under the same experimental conditions, the Adaptive distribution increased the LBG speedup from 7.56× with Equal distribution to 9.18× at 14 processes.', align='j')

doc.add_page_break()
para('Checks before inserting (not part of the thesis text)', bold=True)
for s in [
 'Peppers and Cameraman values of this work match Table 4.5 (CR 25.30 / 29.60; PSNR 29.41 / 29.75).',
 'Li and U values are from their Table 3 (Electronics 2026, 15(5), 922). Their definition of CR (Eq. 20) has not been compared with the definition used here.',
 'Zangana: speedup from the scalability table (1 GPU: 1000 ms; 16 GPUs: 110 ms). Test images and GPU model are not specified in the paper.',
 'Hernandez-Lopez and Muñiz-Pérez: 15x and 25x are from the published abstract; the full results section has not been read, so image names and number of CPU cores are unknown.',
 'Add the three references in IEEE format and renumber tables 4.20 and 4.21 after the final numbering pass.']:
    doc.add_paragraph(s, style='List Bullet')
doc.save('Section_4_9_Comparison.docx')
print('ok')
