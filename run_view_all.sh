#!/bin/bash
# Builds one side-by-side comparison (original | LBG only | current filter | tuned filter) per image
# into ~/view_all/, then opens them all in one viewer (arrow keys to flip). Extra images can be given
# as arguments:  ./run_view_all.sh /path/to/other.txt
D=/home/ibtihal; OUT=$HOME/view_all; mkdir -p "$OUT"
IMGS="$D/lbg_exp/gray.txt $D/boat_img.txt $D/cameraman_img.txt $D/peppers_img.txt $D/chest_xray2_img.txt $D/mammo2_img.txt $D/lung_ct2_img.txt $D/brain_mri2_img.txt $D/lena_color.txt $D/retina2_color.txt $D/brain_pet3_color.txt $D/brain_pet4_color.txt $D/peppers_color.txt"
[ -x ./view_compare ] || { echo "ABORT: build view_compare first"; exit 1; }
for f in $IMGS "$@"; do
  [ -f "$f" ] || { echo "skip (missing): $f"; continue; }
  n=$(basename "$f" .txt); [ "$n" = gray ] && n=lena
  echo "== $n"; ./view_compare "$f" "$OUT/$n.bmp" | sed -n '2,4p'
done
echo; ls "$OUT"/*.bmp | wc -l; echo "images in $OUT  ->  eog $OUT/*.bmp"
command -v eog >/dev/null && eog "$OUT"/*.bmp &
