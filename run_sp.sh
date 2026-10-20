#!/bin/bash
# codes.c (sequential) and codep.c (parallel).  Reports ONLY two times:
#   LBG_s   = LBG training time
#   Total_s = TOTAL PROCESSING time (training vectors, workload distribution, LBG, delta + Huffman container, decoding,
#             reconstruction; no image reading, no console output, no file writing, no quality metrics)
# Protocol: AC power, governor=performance, sequential pinned to one P-core, mpirun --bind-to core, median of 5.
# usage:  NPS="2 4 6 8 10 12 14" ./run_sp.sh img1.txt img2.txt ...
NPS=${NPS:-"2 4 6 8 10 12 14"}; REPS=5; SEQ_CPU=${SEQ_CPU:-6}; OUT=${OUT:-sp_results.csv}; SRC_DIR=${SRC_DIR:-$(dirname "$0")}
med(){ sort -g | awk '{a[NR]=$1} END{print a[int((NR+1)/2)]}'; }
if [ -z "$SKIP_GUARD" ]; then
  [ "$(cat /sys/class/power_supply/AC*/online 2>/dev/null | head -1)" = "1" ] || { echo "ABORT: AC charger not connected"; exit 1; }
  [ "$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u)" = "performance" ] || { echo "ABORT: governor is not performance on all CPUs"; exit 1; }
fi
taskset -c $SEQ_CPU true 2>/dev/null || { echo "ABORT: cannot pin to CPU $SEQ_CPU (set SEQ_CPU)"; exit 1; }
CFLAGS=${CFLAGS:-"-O2"}
gcc   $CFLAGS -o lbg_seq "$SRC_DIR/codes.c" -lm || exit 1
mpicc $CFLAGS -o lbg_par "$SRC_DIR/codep.c" -lm || exit 1
echo "md5 : $(cd "$SRC_DIR" && md5sum codes.c codep.c | awk '{print substr($1,1,8)" "$2}' | tr '\n' ' ')"

total(){ awk -F': ' '/Total processing time/{print $2+0}'; }     # "Total processing time (...): X s|seconds"
echo "image,mode,np,LBG_s,Total_s,SpeedupLBG,SpeedupTotal,EffTotal%" | tee $OUT
for IMG in "$@"; do
  [ -f "$IMG" ] || { echo "ABORT: $IMG not found"; exit 1; }
  n=$(wc -w < "$IMG"); NAME=$(basename "$IMG" .txt)
  if   [ "$n" = 262144 ]; then M=gray
  elif [ "$n" = 786432 ]; then M=color
  else echo "$NAME: unknown size ($n tokens), skipped"; continue; fi

  L=();T=()
  for r in $(seq $REPS); do
    out=$(taskset -c $SEQ_CPU ./lbg_seq "$IMG" --$M)
    if [ $M = gray ]; then L+=($(echo "$out" | awk '/LBG \(wall/{print $6}')); else L+=($(echo "$out" | awk '/Total LBG time/{print $6}')); fi
    T+=($(echo "$out" | total))
  done
  SL=$(printf '%s\n' "${L[@]}" | med); ST=$(printf '%s\n' "${T[@]}" | med)
  echo "$NAME,$M,seq,$SL,$ST,1.00,1.00,100" | tee -a $OUT

  for np in $NPS; do
    BIND="--bind-to core"; [ "$np" -gt 14 ] && BIND="--bind-to hwthread"
    L=();T=()
    for r in $(seq $REPS); do
      out=$(mpirun -np $np --allow-run-as-root $BIND ./lbg_par "$IMG" --$M)
      if [ $M = gray ]; then L+=($(echo "$out" | awk '/Time \(LBG only\)/{print $4}')); else L+=($(echo "$out" | awk '/Total LBG time/{print $6}')); fi
      T+=($(echo "$out" | total))
    done
    PL=$(printf '%s\n' "${L[@]}" | med); PT=$(printf '%s\n' "${T[@]}" | med)
    awk -v n="$NAME" -v m=$M -v np=$np -v pl=$PL -v pt=$PT -v sl=$SL -v st=$ST \
      'BEGIN{printf "%s,%s,%d,%s,%s,%.2f,%.2f,%.0f\n",n,m,np,pl,pt,sl/pl,st/pt,100*st/pt/np}' | tee -a $OUT
  done
done
