#!/bin/bash
# Timing/speedup campaign for the 12 thesis images with ONE program version (run_all.sh does the protocol checks).
# Usage (in the folder with ./lbg_seq ./lbg_par run_all.sh):   NPS="2 4 6 8 10 12 14" ./run_timing_12.sh
D=/home/ibtihal
IMGS="$D/lbg_exp/gray.txt $D/boat_img.txt $D/cameraman_img.txt $D/peppers_img.txt $D/chest_xray2_img.txt $D/mammo2_img.txt $D/lung_ct2_img.txt $D/brain_mri2_img.txt $D/lena_color.txt $D/retina2_color.txt $D/brain_pet3_color.txt $D/brain_pet4_color.txt"
[ -x ./run_all.sh ] || { echo "ABORT: run_all.sh missing"; exit 1; }
NPS=${NPS:-"2 4 6 8 10 12 14"} OUT=${OUT:-timing_v3.csv} ./run_all.sh $IMGS
