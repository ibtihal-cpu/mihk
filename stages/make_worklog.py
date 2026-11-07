#!/usr/bin/env python3
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

d = Document()
st = d.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
for s in d.sections: s.left_margin = s.right_margin = Cm(2.2); s.top_margin = s.bottom_margin = Cm(2.0)
def H(t, l=2):
    h = d.add_heading(t, level=l)
    for r in h.runs: r.font.name = 'Times New Roman'
def P(t, italic=False):
    p = d.add_paragraph(); r = p.add_run(t); r.italic = italic; p.paragraph_format.space_after = Pt(5); return p
def B(t):
    p = d.add_paragraph(t, style='List Bullet'); p.paragraph_format.space_after = Pt(2)
def shade(c, f):
    tc = c._tc.get_or_add_tcPr(); s = OxmlElement('w:shd'); s.set(qn('w:val'), 'clear'); s.set(qn('w:color'), 'auto'); s.set(qn('w:fill'), f); tc.append(s)
def T(rows, w, size=9.5):
    t = d.add_table(rows=len(rows), cols=len(rows[0])); t.style = 'Table Grid'; t.autofit = False; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, x in enumerate(w): t.columns[j].width = Cm(x)
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.cell(i, j); c.width = Cm(w[j]); c.text = ''; r = c.paragraphs[0].add_run(str(v)); r.font.size = Pt(size)
            if i == 0: r.bold = True; shade(c, 'D9E2F3')
    d.add_paragraph().paragraph_format.space_after = Pt(2)

H('Work log - 3 November 2026', 1)
P('MPI-parallel LBG image compression (4 x 4 blocks, K = 64). Measurement and documentation work done in this session. '
  'All numbers below come from the measurements listed; nothing is estimated unless stated.')

H('1. Summary of the day')
T([['Item', 'Result', 'Status'],
   ['Memory usage (peak RSS), sequential and MPI (P = 4, 14)', '3.4-3.5 MB (gray) and 5.4-5.6 MB (color) sequential; 21-23 MB per MPI process; sum about 290 MB at P = 14', 'Measured, Section 4.8 written'],
   ['Time of delta coding, Huffman encoding and container decoding (final program)', 'Together 0.53-0.62 ms gray, 1.5-1.9 ms color; 2.1% of Total processing time at P = 14', 'Measured, Section 4.5.5 written'],
   ['Preliminary experiment: parallel delta and Huffman (June version, found in the Trash folder)', 'Best Huffman speedup 1.26; delta became slower; best saving 0.08 ms (< 0.3% of Total)', 'Re-run and split into computation / communication, Section 4.5.6 written'],
   ['Storage cost of the Huffman side information', '248-262 bytes (2.3-2.8% of the file); net saving 2,384-4,456 bytes; CR +34.7% on average', 'Computed from program output, tables written'],
   ['Number of runs per image (RUN1)', '95 = 5 sequential + 9 values of P x 2 strategies x 5 repetitions; same MD5 in all 95', 'Clarified for the viva']],
  [5.2, 7.6, 4.0])

H('2. Memory usage (Section 4.8)')
P('Peak resident set size per process, /usr/bin/time (%M), same binaries, binding and strategies as RUN1 (P = 4 Equal, P = 14 Adaptive). '
  'Three repetitions on 4 gray and 4 color images (456 measurements; the file has 457 lines with the header).')
T([['Type', 'P', 'Process 0 (MB)', 'Other processes, max (MB)', 'Sum over processes (MB)'],
   ['Gray', '1', '3.4 to 3.5', 'N/A', '3.4 to 3.5'], ['Gray', '4', '21.4 to 21.9', '20.6', '81.7 to 83.1'], ['Gray', '14', '21.7 to 22.3', '20.9', '289.2 to 290.2'],
   ['Color', '1', '5.4 to 5.6', 'N/A', '5.4 to 5.6'], ['Color', '4', '22.3 to 22.7', '20.5', '82.8 to 83.7'], ['Color', '14', '22.9 to 23.4', '21.0', '289.7 to 291.4']],
  [2.0, 1.5, 3.8, 4.6, 4.9])
B('Per-process memory is almost independent of P; the sum grows about linearly with P (290 / 83 = 3.5 = 14 / 4).')
B('Not stated as a fact: the cause of the fixed 21-23 MB (MPI runtime is a likely explanation; an empty MPI program was not measured). The sum of RSS overestimates physical memory (shared pages).')
B('The older values (3.1-3.2 MB, 4.9-5.0 MB) are replaced everywhere by the new ones.')

H('3. Time of the post-training stages (Section 4.5.5)')
P('Instrumented copies (codes_stages.c, codep_stages.c) generated from codes_min.c / codep_min.c by stages/make_stages.py; only timers added. '
  'Check: the compressed file has the same MD5 as the final program (Lena gray: d3507ac8). Protocol of RUN1 (AC power, performance governor, sequential pinned to CPU 6, --bind-to core, 5 repetitions, median).')
T([['Type', 'P', 'Delta (ms)', 'Huffman (ms)', 'Decoding (ms)', 'Sum (ms)', 'Share of Total (%)'],
   ['Gray', '1', '0.006', '0.181', '0.340', '0.527', '0.21'], ['Gray', '4', '0.007', '0.206', '0.387', '0.600', '0.89'],
   ['Gray', '8', '0.008', '0.214', '0.397', '0.619', '1.46'], ['Gray', '14', '0.009', '0.216', '0.391', '0.615', '2.07'],
   ['Color', '1', '0.017', '0.548', '0.939', '1.503', '0.19'], ['Color', '4', '0.015', '0.642', '1.160', '1.817', '0.88'],
   ['Color', '8', '0.020', '0.663', '1.201', '1.884', '1.48'], ['Color', '14', '0.019', '0.671', '1.172', '1.862', '2.12']],
  [2.0, 1.4, 2.3, 2.6, 2.7, 2.2, 3.6])
B('The stages run on Process 0 only, so their time is almost constant and their share of Total grows with P.')
B('At P = 14 (gray) they explain about 0.6 ms of the 2.2 ms gap between Total processing time and LBG time; the rest is distribution, calibration, gathering, and the other stages.')
B('Limitation: stage times come from a separate session; the shares combine them with the Total of RUN1.')

H('4. Preliminary experiment: parallel delta and Huffman (Section 4.5.6)')
P('Program found: lbg_pure_mpi.c (7 June 2026, from the Trash folder; copied to ~/thesis_evidence/old_experiments/ and to the repository). '
  'LBG stays sequential in it. Delta encode (Allgatherv), Huffman (Allreduce, Exscan, Reduce with OR), delta decode (prefix sum) are parallel. '
  'No earlier results file existed, so the experiment was re-run (4 gray images, 5 repetitions, P = 1, 2, 4, 8, 14).')
T([['Stage', 'Component', 'P = 1', 'P = 2', 'P = 4', 'P = 8', 'P = 14'],
   ['Delta encoding', 'Computation / Communication', '0.011 / 0.006', '0.005 / 0.014', '0.003 / 0.023', '0.002 / 0.042', '0.001 / 0.074'],
   ['Huffman', 'Computation', '0.189', '0.097', '0.057', '0.040', '0.032'],
   ['', 'Communication', '0.002', '0.033', '0.053', '0.071', '0.104'],
   ['', 'Sequential verification', '0.191', '0.188', '0.192', '0.199', '0.191'],
   ['', 'Total (with other 0.004)', '0.387', '0.322', '0.307', '0.314', '0.332'],
   ['Delta decoding', 'Computation / Communication', '0.011 / 0.000', '0.007 / 0.003', '0.005 / 0.014', '0.004 / 0.017', '0.003 / 0.026']],
  [2.6, 4.2, 2.2, 2.2, 2.2, 2.2, 2.2], size=9)
B('Computation scales with P; communication and synchronization grow with P and exceed it; the program also performs a sequential decoding check on Process 0 inside the timed region (about 0.19 ms).')
B('Huffman: 0.387 ms to 0.307 ms at P = 4 (speedup 1.26), 0.332 ms at P = 14. Delta encoding 0.017 to 0.075 ms; delta decoding 0.011 to 0.030 ms.')
B('Largest saving about 0.08 ms (0.27% of 29.8 ms, the Total at P = 14, gray). Upper bound without any cost: about 2%. Decision: keep these stages sequential.')
B('Open: LBG-only time rose from 508 to 531 ms at P = 8 and 14 although LBG is sequential there; not investigated, not to be explained in the thesis. Container decoding was not parallelized in this experiment.')
B('The first run (Huffman 0.378 / 0.297 / 0.328 ms) was replaced by the second run in the text; do not mix the two.')

H('5. Storage cost of the Huffman side information')
T([['Image', 'Symbols', 'Header + table (B)', 'Codebook (B)', 'Bitstream (B)', 'Container (B)', 'Net saving vs 6-bit (B)', 'CR'],
   ['Boat', '124', '262', '1,024', '8,359', '9,645', '3,667', '27.18'], ['Cameraman', '117', '248', '1,024', '7,584', '8,856', '4,456', '29.60'],
   ['Lena', '121', '256', '1,024', '9,648', '10,928', '2,384', '23.99'], ['Peppers', '122', '258', '1,024', '9,078', '10,360', '2,952', '25.30']],
  [2.2, 1.6, 2.6, 2.1, 2.2, 2.2, 2.9, 1.4], size=9)
B('Fixed 6-bit reference: 12,288 + 1,024 = 13,312 bytes, CR 19.69. Mean CR gain with delta + canonical Huffman: +34.7% (19.69 to 26.52).')
B('Side information is 5.3-9.7% of the gross saving of the coded data; the codebook is about 10% of the file and is counted in CR.')
B('Gray images only; the color breakdown was not measured.')

H('6. Decisions and clarifications')
B('Keep Section 4.8 Memory Usage (measured in this session); the summary memory paragraph uses the new numbers.')
B('Table 4.14 stays at P = 8-14; P = 5 and 7 stay in Table 4.13 without separate comment.')
B('The number 95 is runs per image (not repetitions): 5 + 9 x 2 x 5; total 760 runs for 8 images.')
B('Word choice: "Process 0" (not "Rank 0"); "communication and synchronization" (not "communication" alone).')
B('Summary: mean CR 26.52 / 25.00, mean PSNR 29.48 / 28.80 dB, mean SSIM 0.8266 / 0.7654 (gray / color). Check that the Mean row of the quality table shows 29.48.')

H('7. Open items')
for t in ['Upload the latest Chapter_4.docx for the final numbering of sections, tables, figures and cross-references.',
          'Chapter 3, Section 3.6: Throughput = I_size / T_total with T_total = Total processing time; same definitions of speedup and Karp-Flatt.',
          'Related-work numbers (Thomas, Ranjan, Zangana, Papakyriakou, Bystrov, Tanovic, Bilal) are still not verified against the papers.',
          'Optional: Huffman container breakdown for the color images (run the sequential program with --color and record the Huffman lines).',
          'Seminar slides: the PowerPoint fixes listed earlier (slide 9, 18/20, 21, 22, 24, 28, 30, 32, typos).']:
    B(t)

H('8. Files')
T([['What', 'Where'],
   ['Memory measurement script and data', '~/run1/mem_run1.sh, ~/run1/RUN1/memory_RUN1.csv, ~/run1/mem_summary.py (your machine)'],
   ['Stage timing sources and runner', 'repository: stages/make_stages.py, codes_stages.c, codep_stages.c, run_stages.sh'],
   ['Stage timing results', '~/mihk_run/stages_RUN/stages_raw.csv, ~/mihk_run/stages_log.txt (your machine)'],
   ['Preliminary experiment', 'repository: stages/old_experiment/ (lbg_pure_mpi.c, lbg_pure_mpi_split.c, make_split.py); runner stages/run_old_parallel_stages.sh'],
   ['Preliminary experiment results', '~/thesis_evidence/old_experiments/split/old_parallel_raw.txt, old_split_log.txt (your machine)'],
   ['Ready-to-paste Chapter 4 text', 'repository: stages/Chapter4_new_sections.docx, stages/Sections_4_5_5_and_4_5_6.docx'],
   ['Commits (branch claude/timing-measurement-unification-laglpl)', '888d21e, 960e9d2, 005a9f7, 22b4155, ec0b7b8']],
  [5.6, 11.2])
P('Back up ~/thesis_evidence/, ~/run1/RUN1/ and ~/mihk_run/stages_RUN/ to a USB drive or cloud storage before the viva.', italic=True)
d.save('stages/Work_Log_2026-11-03.docx'); print('saved')
