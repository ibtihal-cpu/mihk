# Project state (handoff) — read this first when resuming

Branch: claude/timing-measurement-unification-laglpl (repo ibtihal-cpu/mihk)

## Final configuration (decisions taken)
- Post-compression bilateral filter REMOVED everywhere. Final programs: sem_v3_nofilter.c (md5 26fac71b...), pam_v4_nofilter.c (md5 934c7359...).
  Old versions with the filter (sem_v3.c, pam_v4.c) are kept only for reference; all old 12-image/filtered results are obsolete.
- Images: 4 standard gray (Lena, Boat, Cameraman, Peppers) + 4 standard color (Lena, Peppers [peppers_color2], F16, Gold Hill). Medical images dropped.
- 4x4 blocks, K=64, delta+Huffman, double-precision accumulation (seq == par byte-identical, verified: 32 runs, MD5 equal).
- Protocol: median of 5, governor=performance, AC power, --bind-to core, seq pinned (cpu 6). Platform: i7-13650HX, Ubuntu 24.04.4, GCC 13.3.0 -O2, Open MPI 4.1.6, 23 GiB.
- pam_v4 (old, with filter) ran the filter SERIALLY on rank 0 (the [BFPAR] "distributed" comment was stale); irrelevant now.

## Data (final campaign) — results/final_campaign/
CSVs (transcribed from the pasted terminal output; originals + eq_ad_total_raw.csv + logs are in ~/v4n on the thesis PC — keep them),
tables_final.md (all thesis tables computed from the CSVs), make_tables.py, README.md (md5 of programs/images).
Scripts: run_final_campaign.sh (runs everything), run_correctness_nofilter.sh, run_all.sh, run_eq_ad_total.sh, run_entropy.sh,
run_param_study.sh, run_baselines.py (JPEG/JPEG2000 rate-matched, proposed values read from correctness.csv), run_memory.sh, img2txt.py.

## Key results (no filter)
gray CR 23.50-28.88 (mean 25.92), PSNR 29.11-29.75 (29.49), SSIM 0.7624-0.8855 (0.8266); color CR 23.54-26.44 (24.47), PSNR 28.35-29.47 (28.80).
LBG share of seq total: gray 75.4-78.9%, color 80.7-81.7%. LBG speedup P=14: gray 9.18, color 9.21 (eff. ~65.5-65.8%, KF ~0.040).
Total speedup P=14: gray 5.00, color 6.84. Adaptive vs Equal (P>=8): LBG -28.3% (P=8) ... -17.2% (P=14); Total -17.9% ... -8.8% (all 8 images); P<=6 no difference.
JPEG / JPEG2000 at the same CR (mean of 4 gray): PSNR 32.69 / 34.93 dB vs 29.49 dB proposed (+3.20 / +5.44 dB), SSIM 0.8687 / 0.8967 vs 0.8266 (reference only; no claim of superiority).

## Chapter 4 (new draft built from the final data)
results/Chapter_4_final.docx (generator: results/generators/build_ch4_final.py, figures in results/figures_final/). Every number is computed from results/final_campaign/*.csv.
Highlighted (yellow) placeholders to fill: Table 4.2 image sources, Figure 4.1 (Lena original/reconstructed, no filter), Section 4.9 (related studies, verify cited values first).
Chapter 3 must define throughput (Section 3.6) because 4.5.3 cites it. The docx could not be rendered/visually checked here (LibreOffice failed to open any docx in the sandbox): open it in Word/OnlyOffice and check layout.

## PENDING (not done yet)
1. results/CH4_TABLES.docx and results/final_results.xlsx still contain OLD 12-image/filtered data — do not use (superseded by Chapter_4_final.docx); rebuild the xlsx from results/final_campaign if needed.
2. Chapter 4: review Chapter_4_final.docx, fill the highlighted placeholders (see above).
3. Chapter 3: add double-precision sentence in 3.3, define throughput (Θ = N*I/T_LBG) and system CR in 3.6; flowchart arrow fixed (NO -> iteration block).
4. Image sources (dataset/source names for the 8 images) — author must supply. Verify old peppers_color.txt vs peppers_color2.txt (cmp).
5. Related-work table: re-verify every cited number against the original papers (Francisco et al. 2012 supports decoder-side post-processing only; filter is removed now, so it is background only).
6. Chapter 1 review and Chapter 5 (conclusions).
