#!/bin/bash
# Measured index-coding comparison on real files (fixed 6-bit / Huffman without delta / delta + Huffman).
# usage: ./run_index_modes.sh <gray image txt files...>     e.g. ./run_index_modes.sh ~/final8/*_gray.txt
# build: gcc -O2 -o codes_modes codes_modes.c -lm
[ -x ./codes_modes ] || gcc -O2 -o codes_modes codes_modes.c -lm || exit 1
echo "image,A_fixed6_file,B_nodelta_file,C_delta_huffman_file,A_CR,B_CR,C_CR,A_ok,B_ok"
for f in "$@"; do
  n=$(basename "$f" .txt)
  out=$(./codes_modes "$f" --gray 2>&1)
  echo "$out" | awk -v n="$n" '
    /IDX_A/ {split($0,a," "); for(i=1;i<=NF;i++){if($i ~ /^file=/){split($i,x,"=");af=x[2]} if($i ~ /^CR=/){split($i,y,"=");ac=y[2]} if($i ~ /^roundtrip=/){split($i,z,"=");ak=z[2]}}}
    /IDX_B/ {for(i=1;i<=NF;i++){if($i ~ /^file=/){split($i,x,"=");bf=x[2]} if($i ~ /^CR=/){split($i,y,"=");bc=y[2]} if($i ~ /^roundtrip=/){split($i,z,"=");bk=z[2]}}}
    /IDX_C/ {for(i=1;i<=NF;i++){if($i ~ /^file=/){split($i,x,"=");cf=x[2]} if($i ~ /^CR=/){split($i,y,"=");cc=y[2]}}}
    END {printf "%s,%s,%s,%s,%s,%s,%s,%s,%s\n", n,af,bf,cf,ac,bc,cc,ak,bk}'
done
