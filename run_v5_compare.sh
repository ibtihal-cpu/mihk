#!/bin/bash
# Optional experiment (NOT part of the approved results): fast-I/O build (v5) against the approved final build.
# 1) builds both versions in separate folders, 2) checks that every output file is byte-identical,
# 3) times the v5 build with the same protocol as the thesis (run_all.sh, median of 5, same P values).
# usage (same machine and conditions as the final campaign: AC connected, governor = performance):
#   SRC_DIR=$HOME/mihk GRAY_IMGS="g1.txt g2.txt g3.txt g4.txt" COLOR_IMGS="c1.txt c2.txt c3.txt c4.txt" ./run_v5_compare.sh
# result: ~/v5run/timing_v5.csv  (compare with results/final_campaign/timing_final.csv)
SRC_DIR=${SRC_DIR:-$HOME/mihk}; W=${W:-$HOME/v5run}; CFLAGS=${CFLAGS:--O2}; NPS=${NPS:-"2 4 6 8 10 12 14"}
ALL="$GRAY_IMGS $COLOR_IMGS"
[ -n "$GRAY_IMGS" ] && [ -n "$COLOR_IMGS" ] || { echo "set GRAY_IMGS and COLOR_IMGS (4 files each)"; exit 1; }
mkdir -p $W/old $W/new; cd $W || exit 1
gcc   $CFLAGS -o old/lbg_seq $SRC_DIR/sem_v3_nofilter_final.c -lm && mpicc $CFLAGS -o old/lbg_par $SRC_DIR/pam_v4_nofilter_final.c -lm || exit 1
gcc   $CFLAGS -o new/lbg_seq $SRC_DIR/sem_v5_fastio.c         -lm && mpicc $CFLAGS -o new/lbg_par $SRC_DIR/pam_v5_fastio.c         -lm || exit 1

echo "=== byte-identity check (sequential and P=14) ==="
bad=0
for IMG in $ALL; do
  n=$(wc -w < "$IMG"); M=gray; [ "$n" = 786432 ] && M=color
  for V in old new; do
    mkdir -p chk_$V; ( cd chk_$V; rm -f *.txt *.bmp
      ../$V/lbg_seq "$IMG" --$M > seq.out 2>&1; md5sum *.txt *.bmp 2>/dev/null > seq.md5; rm -f *.txt *.bmp
      mpirun --bind-to core -np 14 ../$V/lbg_par "$IMG" --$M > par.out 2>&1; md5sum *.txt *.bmp 2>/dev/null > par.md5 )
  done
  for k in seq par; do
    if cmp -s chk_old/$k.md5 chk_new/$k.md5; then echo "same   $(basename $IMG) $k"; else echo "DIFF   $(basename $IMG) $k"; bad=1; fi
  done
done
[ $bad = 0 ] || { echo "ABORT: outputs differ, do not use v5"; exit 1; }

echo "=== timing of the v5 build ==="
cd new && SKIP_GUARD=${SKIP_GUARD:-} NPS="$NPS" OUT=../timing_v5.csv $SRC_DIR/run_all.sh $ALL
echo "done: $W/timing_v5.csv"
