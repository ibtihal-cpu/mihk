#!/bin/bash
# Entropy of the VQ index stream (before/after delta coding) and the actual Huffman rate,
# for the 8 grayscale images, from the final sequential program (./lbg_seq = sem_v3.c).
# The values are deterministic, so one run per image is enough. Color images: the program
# does not compute entropy for them. usage: ./run_entropy.sh   -> entropy.csv
D=/home/ibtihal
IMGS="${IMGS:-$D/lbg_exp/gray.txt $D/boat_img.txt $D/cameraman_img.txt $D/peppers_img.txt $D/chest_xray2_img.txt $D/mammo2_img.txt $D/lung_ct2_img.txt $D/brain_mri2_img.txt}"
OUT=${OUT:-entropy.csv}
[ -x ./lbg_seq ] || { echo "ABORT: ./lbg_seq missing"; exit 1; }
echo "image,H_index_bits,H_delta_bits,huffman_data_bytes,huffman_bits_per_index,system_CR" | tee $OUT
for IMG in $IMGS; do
  n=$(wc -w < "$IMG"); NAME=$(basename "$IMG" .txt)
  [ "$n" = 262144 ] || { echo "$NAME: not a 512x512 grayscale file, skipped"; continue; }
  out=$(./lbg_seq "$IMG" --gray)
  echo "$out" | awk -v n="$NAME" '
    /Entropy before Huffman/ {hb=$5}
    /Entropy after Delta/    {hd=$5}
    /Huffman data bytes/     {db=$5}
    /System total \(LBG\+Huff\)/ {cr=$4}
    END {printf "%s,%s,%s,%s,%.3f,%s\n", n, hb, hd, db, db*8/16384, cr}' | tee -a $OUT
done
