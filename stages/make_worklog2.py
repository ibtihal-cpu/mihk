#!/usr/bin/env python3
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
d = Document(); st = d.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
for s in d.sections: s.left_margin = s.right_margin = Cm(2.0); s.top_margin = s.bottom_margin = Cm(1.8)
def H(t, l=2):
    h = d.add_heading(t, level=l)
    for r in h.runs: r.font.name = 'Times New Roman'
def P(t, it=False):
    p = d.add_paragraph(); r = p.add_run(t); r.italic = it; p.paragraph_format.space_after = Pt(5)
def B(t):
    p = d.add_paragraph(t, style='List Bullet'); p.paragraph_format.space_after = Pt(2)
def T(rows, w, size=9.5):
    t = d.add_table(rows=len(rows), cols=len(rows[0])); t.style = 'Table Grid'; t.autofit = False; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, x in enumerate(w): t.columns[j].width = Cm(x)
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.cell(i, j); c.width = Cm(w[j]); c.text = ''; r = c.paragraphs[0].add_run(str(v)); r.font.size = Pt(size)
            if i == 0:
                r.bold = True; sh = OxmlElement('w:shd'); sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), 'D9E2F3'); c._tc.get_or_add_tcPr().append(sh)
    d.add_paragraph().paragraph_format.space_after = Pt(2)

H('Work log - 4 and 5 November 2026', 1)
P('Thesis editing session: Chapter 2 formulas, Chapter 3 review and corrections, figures redrawn from the code. Status "agreed" means the change was '
  'decided and the text was written in the session; apply it in the Word file and tick it off (this log does not know what is already applied).', it=True)

H('1. Chapter 3: corrections (only what was necessary)')
T([['#', 'Where', 'Change', 'Reason', 'Status'],
   ['1', 'Whole chapter, figures', 'Rank → Process (Process 0)', 'Supervisor; Chapter 4 already uses Process', 'Agreed'],
   ['2', '3.4.2 and Figure 3.6', 'Equal for P ≤ 6, Adaptive for P > 6 (was 4)', 'codep_min.c: use_equal_split = (size <= 6)', 'Agreed'],
   ['3', '3.4.1, 3.4.2, Algorithm, Figures 3.6/3.7', 'speed / speed-aware → computation rate (Mcmp/s); "time" is wrong because the weight is a rate', 'Supervisor; q_r needs a rate', 'Agreed'],
   ['4', '3.2.3 and Algorithm 3.3', 'Canonical Huffman: code lengths stored, container = header 14 B + code-length table + 8-bit codebook + bitstream', 'Huffman code was changed after the text was written', 'Agreed'],
   ['5', '3.2.2 and Algorithm 3.2', 'offset = 128 (difference stored as an unsigned byte)', 'Matches the program', 'Agreed'],
   ['6', '3.2.1.1', '"maximum of 100 iterations for that codebook size"', 'Examiner question; the limit is per stage', 'Agreed'],
   ['7', 'Parallel LBG algorithm', 'Splitting lines C_{k+c} ← C_c(1 − δ), C_c ← C_c(1 + δ); Allreduce line on one row; Rank → Process', 'Broken line 27; C+ and C- were not stored', 'Agreed (keep the original style, 41 lines)'],
   ['8', '3.4.1', 'Equation for n_r numbered; "rank" → "process"', 'Every equation is numbered and cited', 'Agreed'],
   ['9', '3.4.2', 'Equation q_r numbered (fraction bar), raw LaTeX removed', 'Formatting', 'Agreed'],
   ['10', 'Every figure and algorithm', 'One sentence in the text that cites it and says what it shows; renumber (Fig 3.7→3.6, 3.8→3.7; Alg 3.5→3.4, 3.6→3.5)', 'Supervisor comment; numbers 3.6 and 3.4 were missing', 'Agreed'],
   ['11', '3.6 (Total time)', 'Definition of LBG time and Total processing time (replaces "Total execution time ... output operations")', 'Contradicted Section 4.4', 'Agreed (text written)'],
   ['12', '3.5 and 3.6', 'Move to Chapter 4 as 4.1 Experimental Setup (4.1.1 datasets, 4.1.2 evaluation settings); keep the RGB-sequential paragraph at the end of 3.3', 'Supervisor', 'To do in Word'],
   ['13', '3.7 Summary', 'Becomes 3.5; "computation rate"; last sentence mentions the experimental setup', 'Consequence of 12', 'Agreed']],
  [0.9, 3.0, 6.0, 4.4, 2.7], size=9)

H('2. Figures redrawn (files in the repository, folder stages/figures)')
T([['Figure', 'Content', 'File', 'Note'],
   ['3.1', 'General framework: sequential baseline (2A) and MPI-parallel LBG (2B) as independent paths, Stages 3 and 4', 'Figure_framework_sequential_vs_parallel (.png 300 dpi, .svg, .pdf)', 'Two-row layout so the text is readable at page width'],
   ['3.6', 'Workflow of the MPI-parallel LBG (9 steps, MPI operations by name)', 'Figure_parallel_LBG_workflow.png', 'Rebuilt from the code; epsilon = 10^-4 (the seminar figure had 10^-5); the side panels became text'],
   ['3.7', 'Equal and Adaptive workload distribution (computation rates)', 'Figure_workload_distribution.png', 'Approved'],
   ['3.5', 'Huffman coding process', 'edit in Word', 'Add the "Encode D with the codes" step; "code-length table"'],
   ['3.3', 'LBG training flowchart', 'keep', 'C0 → C1; the limit of 100 is per codebook size']],
  [1.3, 6.0, 5.2, 4.5], size=9)
P('Equation images with fraction bars: stages/eq_img (Karp-Flatt, Amdahl, workload q_r).')

H('3. Chapter 2 (formulas and sources)')
B('Section 2.3: Q(x) = arg min ‖x − c_j‖², c_j ∈ C (the raw LaTeX was removed); delta coding: Δ_i = L_i − L_(i−1), i = 2, …, N_b; entropy: I(s_i) = −log2 p_i and H = −Σ p_i log2 p_i (M or n: use one symbol everywhere).')
B('Karp-Flatt: e(P) = (P/S(P) − 1) / (P − 1), equal to (1/S − 1/P)/(1 − 1/P); computed from the mean speedup. Amdahl: S(P) = 1 / (f_s + (1 − f_s)/P). Reference for Karp-Flatt: Karp and Flatt, Commun. ACM, 33(5), 1990 (from memory, check it).')
B('Amdahl source: Amdahl (1967), AFIPS Spring Joint Computer Conference, pp. 483-485 (from memory); multicore context: Hill and Marty, IEEE Computer 41(7), 33-38, 2008, doi 10.1109/MC.2008.209 (record verified). No 2022-2024 source found; the wording of the thesis text is general and is not a quotation.')
B('LBG sources: Linde, Buzo, Gray (1980); Gersho and Gray (1992). Severo et al., Sensors 24(8), 2606 (2024) and Bilal et al., J. Imaging 10(5), 124 (2024) exist, but their full texts were not opened: check before citing a section or an equation.')
B('Supervisor comment applied to Chapter 2 too: every figure and table (Figures 2.1 and 2.2 included) is cited in the text and explained.')

H('4. Findings of the review (to remember)')
B('The seminar figure had epsilon = 10^-5; the program uses 10^-4. The old text and figure used P <= 4; the program uses P <= 6.')
B('The 100-iteration limit is per codebook size; no stage reached it (largest: 51 gray, 67 color; Iterations_per_stage.docx).')
B('In the preliminary experiment (parallel delta and Huffman) the program also performs a sequential decoding check inside the timed region; do not attribute the lack of gain to communication alone.')
B('Throughput in Chapter 4 (MiB/s of compression) is a different quantity from the computation rate of the calibration (Mcmp/s).')

H('5. Open items')
for t in ['Upload the latest Chapter_4.docx: final numbering, the new Section 4.1 (moved 3.5 and 3.6), merge with the existing setup text, update every reference to Section 3.5 or 3.6.',
          'Check that Chapter 2 defines speedup (mean of per-image values), efficiency, Karp-Flatt, throughput = I_size / T_total, and CR; put the section number in "Section 2.x" of the moved text.',
          'Insert the new Chapter 4 sections (Chapter4_new_sections.docx), the iteration tables, and the memory section.',
          'Optional: run results/final_campaign/run_baselines_real.sh for the JPEG / JPEG 2000 / DWT comparison with the real CR.',
          'Related-work numbers (Thomas, Ranjan, Zangana, Papakyriakou, Bystrov, Tanovic, Bilal) are still unverified against the papers.',
          'Final pass with Ctrl+F: "Rank", "speed", "~~", "\\(", "P ≤ 4", "Total execution time".']:
    B(t)

H('6. Where the files are')
T([['What', 'Where'],
   ['Figures (PNG, SVG, PDF) and their generator scripts', 'repository stages/figures and stages/make_fig_*.py'],
   ['Equation images', 'repository stages/eq_img'],
   ['Chapter 4 additions and the 3 November log', 'repository stages/*.docx (copies in ~/Downloads)'],
   ['This log', 'repository stages/Work_Log_2026-11-05.docx'],
   ['Evidence for the viva (data and scripts of 3 November)', '~/thesis_evidence, ~/run1/RUN1, ~/mihk_run/stages_RUN, ~/mihk_run/iters_RUN (back them up)']],
  [7.5, 9.5])
d.save('stages/Work_Log_2026-11-05.docx'); print('saved')
