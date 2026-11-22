#!/bin/bash
# Test only: does the final-assignment variant keep sequential == parallel (same compressed container)?
# usage (from ~/mihk, after building lbg_fin and lbg_par_fin):  ./stages/run_finalassign_parallel_check.sh ~/final8
#   gcc  -O2 -o lbg_fin     stages/codes_finalassign.c -lm
#   mpicc -O2 -o lbg_par_fin stages/codep_finalassign.c -lm
D=${1:-$HOME/final8}; H=$(pwd)
W=$(mktemp -d)
for img in lena_gray boat_gray cameraman_gray peppers_gray; do
  mkdir -p $W/s $W/p4 $W/p14 $W/p14e
  (cd $W/s   && "$H"/lbg_fin "$D/$img.txt" --gray >/dev/null)
  (cd $W/p4  && mpirun -np 4  --bind-to core "$H"/lbg_par_fin "$D/$img.txt" --gray >/dev/null)
  (cd $W/p14 && mpirun -np 14 --bind-to core "$H"/lbg_par_fin "$D/$img.txt" --gray >/dev/null)
  (cd $W/p14e && VQ_STRATEGY=equal mpirun -np 14 --bind-to core "$H"/lbg_par_fin "$D/$img.txt" --gray >/dev/null)
  echo "== $img"
  for d in s p4 p14 p14e; do printf "  %-5s %s  %s bytes\n" $d "$(md5sum $W/$d/compressed.bin | cut -c1-12)" "$(stat -c %s $W/$d/compressed.bin)"; done
done
rm -rf $W
