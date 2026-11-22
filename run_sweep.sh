#!/bin/bash
# Filter-parameter sweep with a train/test split on the thesis images (gray + color, natural + medical).
# Run from the folder holding ./sweep_filter.
D=/home/ibtihal
TUNE="$D/lbg_exp/gray.txt $D/boat_img.txt $D/chest_xray2_img.txt $D/brain_mri2_img.txt $D/brain_pet3_color.txt"
TEST="$D/cameraman_img.txt $D/peppers_img.txt $D/mammo2_img.txt $D/lung_ct2_img.txt $D/retina2_color.txt $D/brain_pet4_color.txt $D/histo2_color.txt $D/peppers_color.txt"
# lena_color.txt is deliberately NOT used: same scene as the gray Lena in the tuning set (leakage).
for f in $TUNE $TEST; do
  n=$(wc -w < "$f" 2>/dev/null)
  { [ "$n" = 262144 ] || [ "$n" = 786432 ]; } || { echo "ABORT: $f missing or not 512x512 gray/color"; exit 1; }
done
[ -x ./sweep_filter ] || { echo "ABORT: build sweep_filter first"; exit 1; }
./sweep_filter $TUNE -- $TEST 2>/dev/null | tee sweep_result2.txt
