#!/bin/bash
# Quick CR comparison (sequential programs, a few seconds per image; no timing protocol needed):
#   original (sem_v3_nofilter.c, 4 B/symbol table model)  |  code2.c (5 B/symbol + 10 B model)  |  code4.c (REAL container)
# usage:  ./run_code34_compare.sh img1.txt img2.txt ...      (run from the folder that contains the .c files)
SRC=${SRC_DIR:-$(dirname "$0")}; W=$(mktemp -d)
gcc -O2 -o $W/orig  "$SRC/sem_v3_nofilter.c" -lm || exit 1
gcc -O2 -o $W/code2 "$SRC/code2.c" -lm || exit 1
gcc -O2 -o $W/code4 "$SRC/code4.c" -lm || exit 1
printf "%-16s %-6s %9s %9s %9s %8s %10s %-6s %-6s %s\n" image mode CR_orig CR_code2 CR_real "real_vs_c2" file_bytes decode rtrip recon_same
for IMG in "$@"; do
  n=$(wc -w < "$IMG"); NAME=$(basename "$IMG" .txt)
  if [ "$n" = 262144 ]; then M=gray; elif [ "$n" = 786432 ]; then M=color; else echo "$NAME skipped"; continue; fi
  for P in orig code2 code4; do mkdir -p $W/$P.d; (cd $W/$P.d && rm -f * && $W/$P "$IMG" --$M > out.txt 2>&1); done
  cr(){ if [ $M = gray ]; then awk '/System total \(LBG\+Huff\)/{print $4; exit}' $1; else awk '/RGB CR \(system\)/{print $5; exit}' $1; fi; }
  c0=$(cr $W/orig.d/out.txt); c2=$(cr $W/code2.d/out.txt); c4=$(cr $W/code4.d/out.txt)
  fb=$(ls -l $W/code4.d/*.bin | awk '{print $5}')
  dc=$(grep -c "Container decode check: OK" $W/code4.d/out.txt); rt=$(grep -c "File round-trip check.*: OK" $W/code4.d/out.txt)
  if [ $M = gray ]; then a=$(md5sum < $W/orig.d/decompress.txt); b=$(md5sum < $W/code4.d/decompress.txt); else a=$(md5sum < $W/orig.d/compressed_color.bmp); b=$(md5sum < $W/code4.d/compressed_color.bmp); fi
  same=no; [ "$a" = "$b" ] && same=yes
  awk -v n="$NAME" -v m=$M -v c0=$c0 -v c2=$c2 -v c4=$c4 -v fb=$fb -v dc=$dc -v rt=$rt -v s=$same 'BEGIN{printf "%-16s %-6s %9.2f %9.2f %9.2f %+7.1f%% %10d %-6s %-6s %s\n",n,m,c0,c2,c4,100*(c4-c2)/c2,fb,(dc>=1?"OK":"FAIL"),(rt>=1?"OK":"FAIL"),s}'
done
rm -rf $W
