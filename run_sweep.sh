#!/bin/bash
# Filter-parameter sweep with a train/test split. Run from the folder holding ./sweep_filter.
D=/home/ibtihal
TUNE="$D/lbg_exp/gray.txt $D/boat_img.txt $D/chest_xray2_img.txt $D/brain_mri2_img.txt"
TEST="$D/cameraman_img.txt $D/peppers_img.txt $D/mammo2_img.txt $D/lung_ct2_img.txt $D/Desktop/dataset/baboon.txt $D/Desktop/dataset/barbara.txt $D/Desktop/dataset/house.txt"
for f in $TUNE $TEST; do [ "$(wc -w < "$f")" = 262144 ] || { echo "ABORT: $f missing or not 512x512 gray"; exit 1; }; done
[ -x ./sweep_filter ] || { echo "ABORT: build sweep_filter first"; exit 1; }
./sweep_filter $TUNE -- $TEST 2>/dev/null | tee sweep_result.txt
