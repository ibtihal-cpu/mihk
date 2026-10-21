#!/bin/bash
# Equal-distribution timing for P > 6 with codep_min.c (forced with VQ_STRATEGY=equal).
# usage:  NPS="8 10 12 14" OUT=eq_MIN.csv ./run_eq_min.sh ~/final8/*.txt
# Output columns: image,mode,np,LBG_s,Total_s  (median of REPS runs, mpirun --bind-to core)
BIND=${BIND:-"--bind-to core"}; NPS=${NPS:-"8 10 12 14"}; REPS=${REPS:-5}; OUT=${OUT:-eq_MIN.csv}; SRC_DIR=${SRC_DIR:-$(dirname "$0")}
med(){ sort -g | awk '{a[NR]=$1} END{print a[int((NR+1)/2)]}'; }
if [ -z "$SKIP_GUARD" ]; then
  [ "$(cat /sys/class/power_supply/AC*/online 2>/dev/null | head -1)" = "1" ] || { echo "ABORT: AC charger not connected"; exit 1; }
  [ "$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u)" = "performance" ] || { echo "ABORT: governor is not performance on all CPUs"; exit 1; }
fi
mpicc -O2 -o lbg_par "$SRC_DIR/codep_min.c" -lm || exit 1
echo "md5 : $(md5sum "$SRC_DIR/codep_min.c" | cut -c1-8)"
echo "image,mode,np,LBG_s,Total_s" | tee $OUT
for IMG in "$@"; do
  [ -f "$IMG" ] || { echo "ABORT: $IMG not found"; exit 1; }
  n=$(wc -w < "$IMG"); NAME=$(basename "$IMG" .txt)
  if   [ "$n" = 262144 ]; then M=gray
  elif [ "$n" = 786432 ]; then M=color
  else echo "$NAME: unknown size ($n tokens), skipped"; continue; fi
  for np in $NPS; do
    L=(); T=()
    for r in $(seq $REPS); do
      out=$(VQ_STRATEGY=equal mpirun $BIND -np $np ./lbg_par "$IMG" --$M)
      L+=($(echo "$out" | awk -F': ' '/^LBG time/{print $2+0}'))
      T+=($(echo "$out" | awk -F': ' '/^Total processing time/{print $2+0}'))
    done
    echo "$NAME,$M,$np,$(printf '%s\n' "${L[@]}" | med),$(printf '%s\n' "${T[@]}" | med)" | tee -a $OUT
  done
done
