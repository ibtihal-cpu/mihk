# Final campaign (no post-filter; 4 standard grayscale + 4 standard color images)

Run on the thesis machine (i7-13650HX, Ubuntu 24.04.4, GCC 13.3.0 -O2, Open MPI 4.1.6, governor=performance, AC power)
with `run_final_campaign.sh`, started 21:16 (log: ~/v4n/campaign.log on that machine).

Programs (md5):  sem_v3_nofilter.c 26fac71b2a3926926b7030490c8254bb   pam_v4_nofilter.c 934c73595f0cc9a4c9537175da1cdad1
Images: gray = lbg_exp/gray.txt (Lena), boat_img, cameraman_img, peppers_img;
        color = lena_color.txt, thesis_data/peppers_color2.txt, thesis_data/f16_color.txt, thesis_data/goldhill_color.txt
        md5: f16 8d0435d8d642c5b11cc37b9e578f9ad4, goldhill 310a2da87009e02a1cdee940b0702353, peppers_color2 21c4f111997fe41171c8c7b2e237ec7f

NOTE: the CSV files here are transcribed from the terminal output pasted by the author; the original files are in ~/v4n on
the thesis machine (also eq_ad_total_raw.csv and the per-step .log files, which are NOT stored here). Keep that folder.
tables_final.md = every table computed from these CSVs by make_tables.py (half-up rounding on exact decimals).
