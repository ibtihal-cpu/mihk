#!/usr/bin/env python3
"""One Word file with all new Chapter 4 pieces (ready to paste).  Reuses the helpers and the 4.5.5/4.5.6 text of
make_sections_docx.py; adds the Huffman storage-cost section, the memory section and the summary insertions."""
src = open("stages/make_sections_docx.py").read()
head, rest = src.split("# ------------------------------------------------------------------ 4.5.5", 1)
body = rest.split("d.save(")[0]
exec(head)                                   # Document + helpers (H, P, CAP, TABLE)

H('New Chapter 4 sections - ready to paste', 1)
P('Table and section numbers below are temporary (x, y, z, w). Final numbers are fixed in the last step, after '
  'the whole chapter has been renumbered. Where to paste each part:', align='j')
TABLE([
 ['Part', 'Where to paste', 'Notes'],
 ['A. Storage cost of the Huffman side information', 'After the compression-ratio results (Section 4.2 or 4.3)', 'Grayscale only; four images'],
 ['B. 4.5.5 Post-training stages', 'Section 4.5, after the execution time breakdown', 'Final program, instrumented copies'],
 ['C. 4.5.6 Parallelizing delta and Huffman', 'Section 4.5, directly after 4.5.5', 'Earlier program version'],
 ['D. 4.8 Memory Usage', 'Section 4.8 (replaces its content)', 'Table 4.16 (peak RSS)'],
 ['E. Summary insertions', 'Section 4.10 Chapter Summary', 'Replace the memory paragraph; add two sentences'],
], [5.2, 6.0, 4.8])

# ---------------- A ----------------
H('A. Storage Cost of the Huffman Side Information', 2)
P('Huffman coding reduces the size of the index sequence, but the decoder also needs additional information, so it '
  'must be verified that the reduction is worth this cost. The compressed container consists of a 14-byte header, a '
  'code-length table of 2 bytes per used symbol (canonical Huffman code, so that neither the tree nor the symbol '
  'frequencies are stored), the codebook of 64 × 16 = 1,024 bytes, and the coded bitstream. Table 4.z decomposes the '
  'container of each grayscale image, and Table 4.w compares it with fixed 6-bit indices, which require 12,288 bytes '
  'for the 16,384 indices of a 512 × 512 image (13,312 bytes with the codebook, a compression ratio of 19.69).', align='j')
CAP('Table 4.z: Composition of the compressed container of the grayscale images (bytes).')
TABLE([
 ['Image', 'Used symbols', 'Header + table', 'Codebook', 'Bitstream', 'Container', 'Header + table (% of file)', 'Codebook (% of file)'],
 ['Boat', '124', '262', '1,024', '8,359', '9,645', '2.72', '10.62'],
 ['Cameraman', '117', '248', '1,024', '7,584', '8,856', '2.80', '11.56'],
 ['Lena', '121', '256', '1,024', '9,648', '10,928', '2.34', '9.37'],
 ['Peppers', '122', '258', '1,024', '9,078', '10,360', '2.49', '9.88'],
 ['Mean', '', '256', '1,024', '', '9,947', '2.59', '10.36'],
], [2.2, 1.8, 2.0, 1.8, 1.8, 1.9, 2.4, 2.1], bold_rows=(5,), size=9)
P('Note: the number of used symbols follows from the container format (header and table = 14 + 2 × used symbols).',
  italic=True, size=10)
CAP('Table 4.w: Saving of delta coding with canonical Huffman coding relative to fixed 6-bit indices.')
TABLE([
 ['Image', 'Gross saving (bytes)', 'Side information (bytes)', 'Side information (% of gross saving)', 'Net saving (bytes)', 'CR gain over fixed 6-bit (%)'],
 ['Boat', '3,929', '262', '6.7', '3,667', '38.0'],
 ['Cameraman', '4,704', '248', '5.3', '4,456', '50.3'],
 ['Lena', '2,640', '256', '9.7', '2,384', '21.8'],
 ['Peppers', '3,210', '258', '8.0', '2,952', '28.5'],
 ['Mean', '3,621', '256', '7.4', '3,365', '34.7'],
], [2.4, 2.7, 2.7, 3.2, 2.6, 2.9], bold_rows=(5,), size=9)
P('Note: gross saving = 12,288 − bitstream; net saving = 12,288 − (header + table + bitstream). The fixed 6-bit '
  'reference has a compression ratio of 19.69 including the codebook.', italic=True, size=10)
P('The header and the code-length table occupied 248–262 bytes, i.e., 2.3–2.8% of the file, which corresponds to '
  '5.3–9.7% of the saving of the coded data. The net saving after paying for this side information was between 2,384 '
  'and 4,456 bytes per image, and the compression ratio increased by 34.7% on average, from 19.69 for fixed 6-bit '
  'indices to 26.52. The codebook accounts for about 10% of the file, and it is included in the reported compression '
  'ratio together with the header and the table.', align='j')

# ---------------- B + C ----------------
exec(body)

# ---------------- D ----------------
H('D. 4.8 Memory Usage', 2)
P('Memory consumption was measured as the peak resident set size (RSS) of each process using /usr/bin/time. The '
  'measurements used the final program versions, together with the same process-binding and workload-distribution '
  'configurations as in the timing experiments. Each configuration was executed three times for each of the four '
  'grayscale and the four color images, giving 12 runs per image group. Measurements were performed for the sequential '
  'implementation and for the MPI implementation with P = 4 (Equal distribution) and P = 14 (Adaptive distribution). '
  'Table 4.16 reports the minimum and maximum observed values.', align='j')
CAP('Table 4.16: Peak resident set size per process and the sum over all processes (MB). Values are the minimum to '
    'maximum over 12 runs; "Other processes" gives the largest value among the processes other than Process 0.')
TABLE([
 ['Image type', 'P', 'Process 0', 'Other processes (max)', 'Sum over processes'],
 ['Grayscale', '1 (sequential)', '3.4 to 3.5', 'N/A', '3.4 to 3.5'],
 ['Grayscale', '4', '21.4 to 21.9', '20.6', '81.7 to 83.1'],
 ['Grayscale', '14', '21.7 to 22.3', '20.9', '289.2 to 290.2'],
 ['Color', '1 (sequential)', '5.4 to 5.6', 'N/A', '5.4 to 5.6'],
 ['Color', '4', '22.3 to 22.7', '20.5', '82.8 to 83.7'],
 ['Color', '14', '22.9 to 23.4', '21.0', '289.7 to 291.4'],
], [2.6, 3.0, 3.0, 3.8, 3.6])
P('The sequential implementation required 3.4–3.5 MB for the grayscale images and 5.4–5.6 MB for the color images. In '
  'the parallel implementation, the peak memory consumption was approximately 21–23 MB per process and remained nearly '
  'constant between P = 4 and P = 14. Process 0 generally required slightly more memory (by about 1–2 MB) than the '
  'other processes, potentially because of its additional responsibilities for gathering results and handling output '
  'data.', align='j')
P('The sum of the per-process peak RSS values increased approximately linearly with the number of processes, from '
  '81.7–83.7 MB at P = 4 to 289.2–291.4 MB at P = 14. The nearly constant per-process consumption is consistent with a '
  'substantial fixed memory component, potentially associated with the MPI runtime. However, summing the RSS values '
  'across processes may overestimate the actual physical memory consumption, because shared pages can be counted more '
  'than once. Within the evaluated configurations, the summed peak RSS remained below 300 MB, indicating that memory '
  'consumption was not a practical limitation on the tested system.', align='j')

# ---------------- E ----------------
H('E. Insertions for Section 4.10 (Chapter Summary)', 2)
P('1) Compression paragraph (replace the second paragraph; adds the mean values):', italic=True)
P('Using 4 × 4 blocks and a codebook of 64 codewords, the compression ratio averaged 26.52 for the grayscale images '
  '(range 23.99 to 29.60) and 25.00 for the color images (range 24.03 to 27.07). The mean PSNR was 29.48 dB for '
  'grayscale images (range 29.11 to 29.75 dB) and 28.80 dB for color images (range 28.35 to 29.47 dB). The mean SSIM '
  'was 0.8266 (range 0.7624 to 0.8855) and 0.7654 (range 0.6964 to 0.8539), respectively. Delta coding reduced the '
  'entropy of the VQ index sequence. For the four grayscale images, delta coding with Huffman coding increased the '
  'compression ratio by 34.7% on average compared with fixed-length 6-bit indices. The Huffman side information '
  '(header and code-length table) occupied 2.3–2.8% of the compressed file.', align='j')
P('2) Sentence to add to the performance paragraph:', italic=True)
P('Delta coding, Huffman encoding, and container decoding, which are executed by Process 0 only, together accounted for '
  'about 2.1% of the Total processing time at P = 14, and a preliminary experiment showed that parallelizing them saved '
  'less than 0.3% of it; they were therefore kept sequential.', align='j')
P('3) Memory paragraph (replace the old one):', italic=True)
P('Regarding memory usage, the peak resident set size of the sequential program was 3.4–3.5 MB for the grayscale images '
  'and 5.4–5.6 MB for the color images. Each MPI process required approximately 21–23 MB, and this value remained nearly '
  'constant between P = 4 and P = 14, whereas the sum of the per-process peak values increased approximately linearly '
  'with the number of processes, reaching about 290 MB at P = 14.', align='j')

H('Checks before pasting', 2)
for t in ['Mean PSNR 29.48 dB (grayscale): make sure the Mean row of the quality table shows the same value.',
          'Tables 4.z and 4.w are for the four grayscale images only; the same breakdown for the color images was not measured.',
          'Container decoding was not parallelized in the preliminary experiment; it is covered only by the upper bound of Section 4.5.5.',
          'Do not explain the increase of the LBG-only time in the preliminary experiment; it was not investigated.',
          'Evidence folder: stages_RUN/stages_raw.csv, split/old_parallel_raw.txt, old_split_log.txt, memory_RUN1.csv, the stage-timing sources in the repository (stages/).']:
    p = d.add_paragraph(t, style='List Bullet'); p.paragraph_format.space_after = Pt(3)
d.save('stages/Chapter4_new_sections.docx')
print('saved')
