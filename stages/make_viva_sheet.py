#!/usr/bin/env python3
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
d = Document(); st = d.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
for s in d.sections: s.left_margin = s.right_margin = Cm(2.0); s.top_margin = s.bottom_margin = Cm(1.8)
def H(t, l=2):
    h = d.add_heading(t, level=l)
    for r in h.runs: r.font.name = 'Times New Roman'
def P(t, it=False, j=True, sz=None):
    p = d.add_paragraph(); r = p.add_run(t); r.italic = it
    if sz: r.font.size = Pt(sz)
    if j: p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(6)
def T(rows, w):
    t = d.add_table(rows=len(rows), cols=len(rows[0])); t.style = 'Table Grid'; t.autofit = False; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, x in enumerate(w): t.columns[j].width = Cm(x)
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.cell(i, j); c.width = Cm(w[j]); c.text = ''; r = c.paragraphs[0].add_run(v); r.font.size = Pt(9.5)
            if i == 0:
                r.bold = True; sh = OxmlElement('w:shd'); sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), 'D9E2F3'); c._tc.get_or_add_tcPr().append(sh)
    d.add_paragraph().paragraph_format.space_after = Pt(2)

H('Viva preparation sheet', 1)
P('Likely questions with short answers. Every number comes from the measurements of this work (RUN1 unified session, stage timings, memory, '
  'iteration and container analysis). Say "measured on one machine (i7-13650HX, 6 P-cores + 8 E-cores, Open MPI 4.1.6, GCC 13.3 -O2)" when asked about generality.', it=True)
Q = [
 ['Question', 'Short answer', 'Where it is shown'],
 ['What exactly is timed?', 'Two times. LBG time = the lbg() call only. Total processing time = training vectors, float conversion, [parallel: distribution, calibration, scatter, initial mean, gather], LBG, 8-bit codebook, delta, Huffman container, decoding. Excluded: image reading, console output, file writing, entropy statistics, MSE/PSNR/SSIM.', 'Section 4.4'],
 ['How reliable are the timings?', 'Median of 5 runs per case, AC power, performance governor, sequential run pinned to one P-core, mpirun --bind-to core, repetitions as the outer loop. Speedup is computed per image and then averaged over the images.', 'Section 4.3 / 4.5'],
 ['Is the parallel result identical to the sequential one?', 'Yes. Per image, 95 runs (5 sequential + 9 values of P x 2 strategies x 5 repetitions) produced the same compressed file (same MD5). The sums are accumulated in double on integer data, so they are exact and independent of the order. The container is decoded and compared inside the program.', 'Section 4.7'],
 ['What speedup did you obtain?', 'LBG: mean speedup 9.18 at P = 14 (efficiency 65.6%); 9.17 gray, 9.19 color. Total processing time: 8.54 gray, 8.83 color at P = 14.', 'Section 4.5'],
 ['Why is the efficiency not 100%?', 'Up to P = 6 only P-cores are used (efficiency about 90% or more). Beyond P = 6 the E-cores are slower and the Karp-Flatt serial fraction is about 0.04. For the Total time, the sequential post-training stages add to this.', 'Section 4.5, 4.6'],
 ['Why two distribution strategies?', 'Equal is enough for P <= 6 (identical cores). For P > 6 Adaptive (speed calibration) reduced the mean LBG time by 28.2% at P = 8 and by 17.7% at P = 14 (Total: 26.5% and 15.1%). At P <= 6 the difference is below 0.3%.', 'Table 4.13, 4.14'],
 ['Why was Huffman/delta not parallelized?', 'They run on Process 0 and together take 0.5-0.6 ms (gray), about 2.1% of the Total time at P = 14, so a cost-free parallelization would gain about 2% at most. A preliminary experiment: Huffman speedup 1.26 at best, delta became slower; best saving 0.08 ms (< 0.3% of the Total).', 'Section 4.5.5, 4.5.6'],
 ['Is the Huffman side information worth its storage?', 'The header and the code-length table take 248-262 bytes (2.3-2.8% of the file), 5.3-9.7% of the saving of the coded data. Net saving 2,384-4,456 bytes per image; CR rises by 34.7% on average (19.69 with fixed 6-bit indices to 26.52). The codebook (1,024 bytes, about 10%) is included in the CR.', 'Tables 4.z, 4.w'],
 ['Why do the iterations exceed 100?', 'The limit of 100 applies to each splitting stage; the reported number is the total over the six stages (and three channels for color). No stage reached the limit: maximum 51 (gray) and 67 (color).', 'Tables 4.u, 4.v'],
 ['How much memory is used?', 'Peak RSS: 3.4-3.5 MB (gray) and 5.4-5.6 MB (color) sequential; about 21-23 MB per MPI process, almost independent of P; the sum over processes grows linearly with P (about 290 MB at P = 14; shared pages are counted per process, so this overestimates).', 'Table 4.16'],
 ['Why does the Total speedup lag behind the LBG speedup?', 'LBG is more than 99% of the sequential time, but at P = 14 the other stages are about 7% of the Total time (gray): the sequential stages (about 2%) plus preparation, distribution, calibration and gathering.', 'Section 4.5.2, 4.5.5'],
 ['How good is the reconstruction?', 'Mean PSNR 29.48 dB (gray) and 28.80 dB (color); mean SSIM 0.8266 and 0.7654; mean CR 26.52 and 25.00. Reference codecs at the same CR are better in quality (see the baseline table); the aim of this work is the parallel acceleration of VQ training, not to compete with JPEG.', 'Section 4.2'],
 ['Does it generalize?', 'Not shown: eight 512 x 512 images, one machine, K = 64, 4 x 4 blocks. Larger images or other hardware were not tested.', 'Limitations'],
]
T(Q, [3.6, 10.6, 2.8])

H('Limitations and Future Work (text for the thesis)', 2)
P('This work has the following limitations. The experiments were carried out on one machine with a hybrid processor (6 P-cores and 8 E-cores) and on eight '
  '512 x 512 images with 4 x 4 blocks and a codebook of 64 codewords; larger images, other block sizes, other codebook sizes, and other hardware were not evaluated. '
  'Memory was measured only for P = 4 and P = 14, and the decomposition of the compressed container was computed only for the grayscale images. '
  'The stages after the codebook training (delta coding, Huffman encoding, and container decoding) were kept sequential because they account for about 2% of the Total '
  'processing time at P = 14; the container decoding was not part of the preliminary parallelization experiment. For much larger images or higher numbers of processes, '
  'their share would grow and their parallelization should be reconsidered. The comparison with JPEG and JPEG 2000 is given at the same compression ratio as a reference only.')
P('Future work includes evaluating larger images and more processes, parallelizing the post-training stages with a communication-aware design, using the speed calibration '
  'of the Adaptive strategy for these stages, and evaluating other vector quantization training algorithms with the same measurement protocol.')
H('Evidence to bring', 2)
for t in ['~/thesis_evidence/ (memory, stage timings, preliminary experiment, iteration tables) and ~/run1/RUN1/ (raw.csv, env.txt, md5 of the sources).',
          'The repository (branch claude/timing-measurement-unification-laglpl): stages/, results/final_campaign/run1/.',
          'The programs codes_min.c and codep_min.c and the scripts run_all_once.sh, stages/run_stages.sh, stages/run_iters.sh (each runs in minutes).',
          'A short demo on one image: sequential, P = 4, P = 14 (Adaptive), and md5sum of compressed.bin.']:
    d.add_paragraph(t, style='List Bullet').paragraph_format.space_after = Pt(2)
d.save('stages/Viva_Preparation_Sheet.docx'); print('saved')
