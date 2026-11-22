#!/bin/bash
# Rate-matched comparison with JPEG, JPEG 2000 and the DWT + Huffman baseline, using the REAL container CR of the
# final program (23.99, 27.18, 29.60, 25.30) instead of the older size model (23.50, 26.54, 28.88, 24.75).
# usage (from the repository root):  ./results/final_campaign/run_baselines_real.sh ~/final8
# needs: python3 with numpy and Pillow (JPEG 2000 support)
D=${1:-$HOME/final8}; C=results/final_campaign/correctness_real_gray.csv; O=results/final_campaign
IMGS="$D/lena_gray.txt $D/boat_gray.txt $D/cameraman_gray.txt $D/peppers_gray.txt"
python3 run_baselines.py $C $IMGS > $O/baselines_real.csv && cat $O/baselines_real.csv
python3 run_wavelet_baseline.py $C $IMGS > $O/wavelet_baseline_real.csv && cat $O/wavelet_baseline_real.csv
