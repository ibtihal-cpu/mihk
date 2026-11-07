from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()
for s in doc.sections:
    s.left_margin = s.right_margin = Cm(2.2)
st = doc.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')

def para(text, bold=False, italic=False, justify=False, size=None):
    p = doc.add_paragraph(); r = p.add_run(text); r.bold = bold; r.italic = italic
    if size: r.font.size = Pt(size)
    if justify: p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p

def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr(); shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), color); tcPr.append(shd)

def table(rows, bold_rows=()):
    t = doc.add_table(rows=len(rows), cols=len(rows[0])); t.style = 'Table Grid'
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j); c.text = ''
            run = c.paragraphs[0].add_run(val); run.font.size = Pt(10)
            if i == 0: run.bold = True; shade(c, 'D9D9D9')
            if i in bold_rows: run.bold = True
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()

para('4.9 Comparison with Previous Studies', bold=True, size=14)
para('This section places the results in the context of previous work in two respects: compression ratio and quality on the common test images (Table 4.20), and parallel speedup for image compression (Table 4.21). The comparisons with the sequential program and with the Equal distribution, which corresponds to the equal partitioning of training vectors used in previous parallel LBG implementations, were obtained under identical conditions in Sections 4.5 and 4.6. In addition, a reference fractal compressor was implemented in this work following Algorithms 1 and 2 of the quadtree fractal compression scheme described in [ref] and was executed on the same images and the same machine as the proposed framework. The classification and quantization choices that the algorithm does not specify are stated in Section 3.x. This implementation is not the code of the cited authors and does not reproduce their results. The values taken from the cited studies are given for reference only, because the studies differ in algorithm, implementation language, hardware, baseline, and the stages included in the measured time. The same image names do not guarantee identical image files, preprocessing, or compressed-size accounting.', justify=True)

para('Table 4.20. Compression ratio and PSNR on the common 512 × 512 test images.', bold=True)
table([
 ['Image','Method','CR','PSNR (dB)'],
 ['Lena','Thomas et al. (2025)','1.52','54.28'],
 ['','Ranjan and Kumar (2023)','4.41','34.78'],
 ['','Reference fractal compressor (this work)','34.36','27.48'],
 ['','This work (LBG-VQ)','23.99','29.67'],
 ['Boat','Thomas et al. (2025)','1.41','54.07'],
 ['','Reference fractal compressor (this work)','28.29','27.01'],
 ['','This work (LBG-VQ)','27.18','29.11'],
 ['Cameraman','Li and U (2026)','20.29','32.53'],
 ['','Reference fractal compressor (this work)','30.61','28.72'],
 ['','This work (LBG-VQ)','29.60','29.75'],
 ['Peppers','Li and U (2026)','21.10','31.43'],
 ['','Reference fractal compressor (this work)','39.71','27.77'],
 ['','This work (LBG-VQ)','25.30','29.41'],
])
para('Note: the values of Thomas et al., Ranjan and Kumar, and Li and U are taken from the cited studies, with the image names and sizes as reported there. The reference fractal compressor uses a tolerance of 20 and was executed on the same images and machine as the proposed framework.', italic=True, size=10)

para('Table 4.21 compares the parallel speedup reported for image compression in previous studies with the speedup obtained in this work, including the reference fractal compressor executed on the same machine.', justify=True)
para('Table 4.21. Parallel speedup reported for image compression and in this work.', bold=True)
table([
 ['Study','Compression method','Platform','Baseline','Speedup'],
 ['Hernandez-Lopez and Muñiz-Pérez (2022)','Fractal, quadtree partition','Multi-core CPU (task parallelism)','Serial implementation','≈15×'],
 ['','','GPU (CUDA dynamic parallelism)','Serial implementation','≈25×'],
 ['Zangana (2025)','Bitplane, wavelet, predictive coding','Up to 16 GPUs','1 GPU','9.09×'],
 ['Reference fractal compressor (this work)','Fractal, quadtree, classification','14 OpenMP threads (6 P-cores + 8 E-cores)','Sequential run','3.4× to 4.0× (mean 3.68×)'],
 ['This work','LBG-VQ, delta, canonical Huffman','14 MPI processes (6 P-cores + 8 E-cores)','Sequential program','9.18× (LBG); 8.54× (Total, gray); 8.83× (Total, color)'],
])
para('Note: the speedup of the reference fractal compressor is the ratio of encoding plus decoding time with one thread to that with 14 threads (medians of five runs), over the four grayscale images.', italic=True, size=10)

para('Table 4.22. Comparison with the reference fractal compressor on the same images and machine.', bold=True)
table([
 ['Image','Method','CR','PSNR (dB)','Time, 1 unit (s)','Time, 14 units (s)','Speedup (14 units)'],
 ['Lena','Reference fractal compressor','34.36','27.48','0.0134','0.0039','3.44×'],
 ['','This work (LBG-VQ)','23.99','29.67','0.2652','0.0309','8.58×'],
 ['Boat','Reference fractal compressor','28.29','27.01','0.0171','0.0043','3.98×'],
 ['','This work (LBG-VQ)','27.18','29.11','0.2329','0.0274','8.50×'],
 ['Cameraman','Reference fractal compressor','30.61','28.72','0.0156','0.0041','3.80×'],
 ['','This work (LBG-VQ)','29.60','29.75','0.2372','0.0280','8.47×'],
 ['Peppers','Reference fractal compressor','39.71','27.77','0.0130','0.0037','3.51×'],
 ['','This work (LBG-VQ)','25.30','29.41','0.2809','0.0327','8.59×'],
 ['Mean of four images','Reference fractal compressor','33.24','27.75','0.0148','0.0040','3.68×'],
 ['','This work (LBG-VQ)','26.52','29.49','0.2541','0.0298','8.54×'],
], bold_rows=(9, 10))
para('Note: the time of the reference fractal compressor is encoding plus decoding with OpenMP threads; the time of this work is the Total processing time (Section 4.4) with MPI processes. A "unit" is an OpenMP thread or an MPI process (14 units = 6 P-cores + 8 E-cores). Times are medians of five runs. The mean speedup is the mean of the four individual speedups, not the ratio of the mean times (for example, 0.2541 / 0.0298 = 8.53 compared with 8.54). The two time definitions differ (the fractal time covers encoding and decoding only; the Total processing time of this work covers the stages listed in Section 4.4), so the times are compared descriptively.', italic=True, size=10)

para('Discussion', bold=True)
para('Table 4.20 shows that, at comparable compression ratios, the proposed LBG-VQ framework reached a higher PSNR than the reference fractal compressor: by 2.1 dB for Boat (29.11 dB at CR 27.18 compared with 27.01 dB at CR 28.29) and by 1.0 dB for Cameraman (29.75 dB at CR 29.60 compared with 28.72 dB at CR 30.61). For Lena and Peppers, the compression ratios of the two methods differ too much for a direct quality comparison. Li and U report higher PSNR values than this work for Peppers and Cameraman at lower compression ratios, and the studies of Thomas et al. and Ranjan and Kumar operate at much lower compression ratios with higher PSNR; these studies use different algorithms, so the values cannot be ranked.', justify=True)
para('Table 4.22 shows that the proposed framework achieved a higher parallel speedup than the reference fractal compressor under the tested configurations. At 14 processing units, the mean Total processing speedup of the proposed framework was 8.54×, compared with 3.68× for the reference fractal compressor. However, the reference fractal compressor required substantially less execution time, with mean times of 0.0148 s sequentially and 0.0040 s using 14 OpenMP threads, compared with 0.2541 s and 0.0298 s for the proposed framework. These results indicate that the proposed framework achieved a greater relative reduction in execution time, whereas the reference fractal compressor remained faster in absolute terms. The difference should be interpreted with caution because the two implementations use different algorithms, parallel programming models, and timing boundaries. A possible explanation is that the fractal encoding takes only about 10 ms sequentially, which leaves little work to hide the cost of parallel execution, but this was not measured separately.', justify=True)
para('The parallel speedups reported in previous studies (Table 4.21) are given for context rather than for ranking, since the studies differ in compression algorithms, hardware platforms, sequential baselines, and measured stages. The effectiveness of the proposed Adaptive distribution is therefore established primarily through the controlled experiments of Sections 4.5 and 4.6, where it increased the LBG speedup from 7.56× with Equal distribution to 9.18× at 14 processes.', justify=True)

doc.add_page_break()
para('Checks before inserting (not part of the thesis text)', bold=True)
for s in [
 'Numbers of this work are from Tables 4.5, 4.12, 4.14 and RUN1 medians; the reference fractal compressor numbers are from the runs of fic_class (tol = 20, medians of 5 runs): CR/PSNR Lena 34.36/27.48, Boat 28.29/27.01, Cameraman 30.61/28.72, Peppers 39.71/27.77.',
 'The fractal time is encoding + decoding (ET + DT). Lena: 0.0087 + 0.0047 = 0.0134 s (1 thread), 0.0025 + 0.0014 = 0.0039 s (14 threads); Boat: 0.0171 / 0.0043 s.',
 'The earlier exhaustive-search version (fic_quadtree_omp.c) is NOT used: it does not follow Algorithms 1 and 2.',
 'Section 3.x must describe the choices not given by the algorithm (classification by quadrant means and variances, 16x16 to 4x4 blocks, non-overlapping domain pool, 5-bit scale, 7-bit offset, 8 decoding iterations).',
 'Thomas et al. and Ranjan and Kumar: same image names and sizes were confirmed by the author from the papers; not verified here. Li and U CR definition (their Eq. 20) not compared with the definition used in this thesis.',
 'Add the references in IEEE format and renumber tables 4.20-4.22 after the final numbering pass.']:
    doc.add_paragraph(s, style='List Bullet')
doc.save('Section_4_9_Comparison.docx')
print('ok')
