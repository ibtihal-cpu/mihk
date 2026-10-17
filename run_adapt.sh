#!/bin/bash
# Per-image adaptive post-filter strength on all thesis images (8 gray + 5 color) plus peppers_color.
D=/home/ibtihal
IMGS="$D/lbg_exp/gray.txt $D/boat_img.txt $D/cameraman_img.txt $D/peppers_img.txt $D/chest_xray2_img.txt $D/mammo2_img.txt $D/lung_ct2_img.txt $D/brain_mri2_img.txt $D/lena_color.txt $D/retina2_color.txt $D/brain_pet3_color.txt $D/brain_pet4_color.txt $D/histo2_color.txt $D/peppers_color.txt"
for f in $IMGS; do
  n=$(wc -w < "$f" 2>/dev/null)
  { [ "$n" = 262144 ] || [ "$n" = 786432 ]; } || { echo "ABORT: $f missing or not 512x512 gray/color"; exit 1; }
done
[ -x ./adapt_alpha ] || { echo "ABORT: build adapt_alpha first"; exit 1; }
./adapt_alpha $IMGS | tee adapt_result.txt
