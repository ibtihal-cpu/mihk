#!/bin/bash
# Builds one side-by-side comparison (original | before: old filter | after: tuned filter) per image
# into ~/view_all/, then opens them all in one viewer (arrow keys to flip). Extra images can be given
# as arguments:  ./run_view_all.sh /path/to/other.txt
D=/home/ibtihal; OUT=$HOME/view_all; mkdir -p "$OUT"
IMGS="$D/lbg_exp/gray.txt $D/boat_img.txt $D/cameraman_img.txt $D/peppers_img.txt $D/chest_xray2_img.txt $D/mammo2_img.txt $D/lung_ct2_img.txt $D/brain_mri2_img.txt $D/lena_color.txt $D/retina2_color.txt $D/brain_pet3_color.txt $D/brain_pet4_color.txt $D/peppers_color.txt"
[ -x ./view_compare ] || { echo "ABORT: build view_compare first"; exit 1; }
for f in $IMGS "$@"; do
  [ -f "$f" ] || { echo "skip (missing): $f"; continue; }
  n=$(basename "$f" .txt); [ "$n" = gray ] && n=lena
  echo "== $n"; ./view_compare "$f" "$OUT/$n.bmp" | sed -n '2,3p'
done
echo; echo "montages: $OUT/<name>.bmp   |   full-size triples: $OUT/<name>_original.bmp  _before.bmp  _after.bmp"
echo "view one image (original, before, after; arrow keys to flip):   v(){ eog $OUT/$1_original.bmp $OUT/$1_before.bmp $OUT/$1_after.bmp; }; v lena"
echo "names: $(ls "$OUT"/*.bmp | grep -v -E '_(original|before|after)\.bmp$' | xargs -n1 basename | sed 's/\.bmp$//' | tr '\n' ' ')"
