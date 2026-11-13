#!/usr/bin/env python3
"""Ready-to-paste text for Sections 4.5.5 and 4.5.6 (stage times of the final program and the side experiment)."""
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

d = Document()
st = d.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
for s in d.sections: s.left_margin = s.right_margin = Cm(2.5); s.top_margin = s.bottom_margin = Cm(2.5)

def H(text, lvl=2):
    h = d.add_heading(text, level=lvl)
    for r in h.runs: r.font.name = 'Times New Roman'; r.font.color.rgb = None
def P(text, italic=False, size=None, align=None):
    p = d.add_paragraph(); r = p.add_run(text); r.italic = italic
    if size: r.font.size = Pt(size)
    p.paragraph_format.space_after = Pt(8)
    if align == 'j': p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p
def CAP(text):
    p = d.add_paragraph(); r = p.add_run(text); r.bold = True; r.font.size = Pt(11)
    p.paragraph_format.keep_with_next = True; p.paragraph_format.space_after = Pt(4)
def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr(); sh = OxmlElement('w:shd')
    sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), fill); tcPr.append(sh)
def TABLE(rows, widths, bold_rows=(), size=10):
    t = d.add_table(rows=len(rows), cols=len(rows[0])); t.style = 'Table Grid'; t.autofit = False; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, w in enumerate(widths): t.columns[j].width = Cm(w)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j); c.width = Cm(widths[j]); c.text = ''
            p = c.paragraphs[0]; r = p.add_run(str(val)); r.font.size = Pt(size)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 or (len(row) > 6 and j == 1) else WD_ALIGN_PARAGRAPH.CENTER
            if i == 0 or i in bold_rows: r.bold = True
            if i == 0: shade(c, 'D9E2F3')
    d.add_paragraph().paragraph_format.space_after = Pt(2)
    return t

# ------------------------------------------------------------------ 4.5.5
H('4.5.5 Execution Time of the Post-Training Stages')
P('After the codebook has been trained, three stages remain: delta coding of the index sequence, Huffman encoding '
  'into the compressed container, and decoding of the container. In the parallel program these stages are executed by '
  'Process 0 only. Their execution time was measured separately with instrumented copies of the sequential and the '
  'parallel programs, which produce exactly the same compressed file as the final programs (identical MD5 checksum), '
  'using the same measurement protocol as the timing experiments (median of five runs). Table 4.x reports the mean '
  'over the images of each type: the LBG time and the Total processing time come from the main measurement session '
  '(in seconds), and the times of the three post-training stages come from the instrumented programs (in milliseconds).', align='j')
CAP('Table 4.x: Execution time of each stage and its share of the Total processing time (LBG and Total in seconds; the other stages in milliseconds).')
TABLE([
 ['Image type', 'P', 'LBG (s)', 'Delta (ms)', 'Huffman (ms)', 'Decoding (ms)', 'Total (s)', 'LBG share (%)', 'Delta + Huffman + decoding (%)'],
 ['Grayscale', '1 (sequential)', '0.2531', '0.006', '0.181', '0.340', '0.2541', '99.63', '0.21'],
 ['Grayscale', '4', '0.0666', '0.007', '0.206', '0.387', '0.0675', '98.59', '0.89'],
 ['Grayscale', '8', '0.0404', '0.008', '0.214', '0.397', '0.0425', '95.03', '1.46'],
 ['Grayscale', '14', '0.0276', '0.009', '0.216', '0.391', '0.0298', '92.75', '2.07'],
 ['Color', '1 (sequential)', '0.7724', '0.017', '0.548', '0.939', '0.7750', '99.66', '0.19'],
 ['Color', '4', '0.2034', '0.015', '0.642', '1.160', '0.2060', '98.75', '0.88'],
 ['Color', '8', '0.1236', '0.020', '0.663', '1.201', '0.1273', '97.07', '1.48'],
 ['Color', '14', '0.0840', '0.019', '0.671', '1.172', '0.0878', '95.73', '2.12'],
], [1.9, 2.4, 1.6, 1.6, 1.8, 1.8, 1.6, 1.7, 2.6], size=9)
P('Note: the values may not add up exactly because of rounding. For the color images the stages are summed over the '
  'three channels, and the Huffman time includes the conversion of the codebook to 8 bits. The remaining part of the '
  'Total processing time (for example, building the training vectors) is not listed separately.', italic=True, size=10)
P('Delta coding was the cheapest stage (0.006–0.009 ms for the grayscale images and 0.015–0.020 ms for the color '
  'images), followed by Huffman encoding (about 0.18–0.22 ms and 0.55–0.67 ms, respectively). Container decoding was '
  'the longest of the three (about 0.34–0.40 ms and 0.94–1.20 ms). Because these stages are not parallelized, their '
  'time remained almost unchanged as P increased, and their combined share of the Total processing time grew from '
  'about 0.2% in the sequential program to about 2.1% at P = 14.', align='j')
P('This growth contributes to the gap between the Total processing speedup and the LBG speedup, but it does not explain '
  'it alone. At P = 14, the Total processing time of the grayscale images exceeded the LBG time by about 2.2 ms, of '
  'which the three stages account for about 0.6 ms. The remainder belongs to the other stages included in the Total '
  'processing time, such as building the training vectors, work distribution, computation-rate calibration, and the gathering of '
  'results.', align='j')

# ------------------------------------------------------------------ 4.5.6
H('4.5.6 Parallelizing Delta and Huffman Coding: A Preliminary Experiment')
P('Since the stages of Section 4.5.5 run on Process 0 only, an earlier program version in which delta coding and '
  'Huffman coding were parallelized with MPI was evaluated before deciding to keep them sequential. In that version, '
  'each process computes the delta values of its part of the index sequence, which are then gathered with '
  'MPI_Allgatherv; the Huffman histogram is reduced with MPI_Allreduce, every process builds the same code tree, '
  'and the bit offset of each part of the bitstream is obtained with MPI_Exscan before the parts are merged with '
  'MPI_Reduce; the delta decoding uses a prefix sum. The LBG training remained sequential in that version, so that '
  'only these stages were affected. The program also decodes the encoded labels on Process 0 to verify the Huffman '
  'stage, and this check lies inside the timed region.', align='j')
P('Table 4.y reports the mean over the four grayscale images of the median of five runs, with the local computation '
  'separated from the communication and synchronization time. The container decoding of the final program was not '
  'part of this experiment.', align='j')
CAP('Table 4.y: Execution time of the parallelized delta and Huffman stages in the earlier program version (ms).')
TABLE([
 ['Stage', 'Component', 'P = 1', 'P = 2', 'P = 4', 'P = 8', 'P = 14'],
 ['Delta encoding', 'Computation', '0.011', '0.005', '0.003', '0.002', '0.001'],
 ['', 'Communication', '0.006', '0.014', '0.023', '0.042', '0.074'],
 ['', 'Total', '0.017', '0.019', '0.026', '0.043', '0.075'],
 ['Huffman encoding', 'Computation', '0.189', '0.097', '0.057', '0.040', '0.032'],
 ['', 'Communication', '0.002', '0.033', '0.053', '0.071', '0.104'],
 ['', 'Sequential verification', '0.191', '0.188', '0.192', '0.199', '0.191'],
 ['', 'Other', '0.004', '0.004', '0.004', '0.004', '0.004'],
 ['', 'Total', '0.387', '0.322', '0.307', '0.314', '0.332'],
 ['Delta decoding', 'Computation', '0.011', '0.007', '0.005', '0.004', '0.003'],
 ['', 'Communication', '0.000', '0.003', '0.014', '0.017', '0.026'],
 ['', 'Total', '0.011', '0.010', '0.019', '0.020', '0.030'],
], [3.0, 4.0, 1.75, 1.75, 1.75, 1.75, 1.75], bold_rows=(3, 8, 11))
P('Note: earlier program version, four grayscale images. The communication time includes the waiting time at '
  'synchronization points. The values may not add up exactly because of rounding. The absolute times are not '
  'comparable with those of the final program.', italic=True, size=10)
P('Table 4.z compares the sequential execution (P = 1) of this program with the parallel executions: it gives the speedup of '
  'each parallelized stage, that is, the time at P = 1 divided by the time at P. A value below 1 means that the parallel '
  'version was slower than the sequential one.', align='j')
CAP('Table 4.z: Speedup of the parallelized stages relative to the sequential execution (P = 1) of the same program.')
TABLE([
 ['Stage', 'P = 2', 'P = 4', 'P = 8', 'P = 14'],
 ['Delta encoding', '0.89', '0.65', '0.40', '0.23'],
 ['Huffman encoding', '1.20', '1.26', '1.23', '1.17'],
 ['Delta decoding', '1.10', '0.58', '0.55', '0.37'],
], [4.5, 2.4, 2.4, 2.4, 2.4])
P('Note: computed from the times of Table 4.y (earlier program version, grayscale images); the values are rounded.', italic=True, size=10)
P('The local computation scaled with the number of processes: the computation time of Huffman encoding decreased from '
  '0.189 ms at P = 1 to 0.032 ms at P = 14. However, the communication and synchronization time increased with P '
  '(from 0.002 to 0.104 ms for Huffman encoding), and the sequential verification on Process 0 (about 0.19 ms) did not '
  'depend on P. As a result, the total Huffman time decreased only from 0.387 ms at P = 1 to 0.307 ms at P = 4, a '
  'speedup of 1.26, and then increased again to 0.332 ms at P = 14. Delta encoding and decoding became slower as P '
  'grew (from 0.017 to 0.075 ms and from 0.011 to 0.030 ms, respectively), because their communication time exceeded '
  'their computation time already for small values of P.', align='j')
P('The largest saving observed in this experiment, about 0.08 ms, is below 0.3% of the Total processing time of the '
  'final program at P = 14 (about 29.8 ms for the grayscale images). Moreover, Section 4.5.5 gives an upper bound that '
  'does not depend on the implementation: the three post-training stages together account for about 2.1% of the Total '
  'processing time at P = 14, so even a parallelization without any cost would reduce the Total processing time by '
  'about 2% at most. For these reasons, delta coding, Huffman encoding, and container decoding were kept sequential in '
  'the final implementation, and the parallelization effort was concentrated on the LBG training, which accounts for '
  'more than 99% of the sequential execution time.', align='j')
d.save('stages/Sections_4_5_5_and_4_5_6.docx')
print('saved')
