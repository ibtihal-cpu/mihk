#!/bin/bash
# Campaign for code1.c (parallel) / code2.c (sequential): LBG time, complete-program time and TOTAL PROCESSING time
# (no I/O, no console output, no quality metrics), sequential and parallel, median of 5.
# usage:  NPS="2 4 6 8 10 12 14" ./run_proc_time.sh img1.txt img2.txt ...      (same protocol as run_all.sh)
NPS=${NPS:-"2 4 6 8 10 12 14"}; REPS=5; SEQ_CPU=${SEQ_CPU:-6}; OUT=${OUT:-code12_results.csv}; SRC_DIR=${SRC_DIR:-$(dirname "$0")}
med(){ sort -g | awk '{a[NR]=$1} END{print a[int((NR+1)/2)]}'; }
if [ -z "$SKIP_GUARD" ]; then
  [ "$(cat /sys/class/power_supply/AC*/online 2>/dev/null | head -1)" = "1" ] || { echo "ABORT: AC charger not connected"; exit 1; }
  [ "$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u)" = "performance" ] || { echo "ABORT: governor is not performance on all CPUs"; exit 1; }
fi
taskset -c $SEQ_CPU true 2>/dev/null || { echo "ABORT: cannot pin to CPU $SEQ_CPU (set SEQ_CPU)"; exit 1; }
CFLAGS=${CFLAGS:-"-O2"}
gcc   $CFLAGS -o lbg_seq "$SRC_DIR/code2.c" -lm || exit 1
mpicc $CFLAGS -o lbg_par "$SRC_DIR/code1.c" -lm || exit 1
echo "md5 : $(md5sum "$SRC_DIR/code2.c" "$SRC_DIR/code1.c" | tr '\n' ' ')"

proc(){ awk -F': ' '/Total processing time/{print $2+0}'; }
totl(){ awk -F': ' '/Total \(measured|Total program time|Total execution time/{print $2+0; exit}'; }
echo "image,mode,np,LBG_s,Total_s,Proc_s,SpeedupLBG,SpeedupTotal,SpeedupProc,EffProc%" | tee $OUT
for IMG in "$@"; do
  n=$(wc -w < "$IMG"); NAME=$(basename "$IMG" .txt)
  if   [ "$n" = 262144 ]; then M=gray
  elif [ "$n" = 786432 ]; then M=color
  else echo "$NAME: unknown size ($n tokens), skipped"; continue; fi

  L=();T=();P=()
  for r in $(seq $REPS); do
    out=$(taskset -c $SEQ_CPU ./lbg_seq "$IMG" --$M)
    if [ $M = gray ]; then
      L+=($(echo "$out" | awk '/LBG \(wall/{print $6}')); T+=($(echo "$out" | totl))
    else
      L+=($(echo "$out" | awk '/Total LBG time/{print $6}')); T+=($(echo "$out" | totl))
    fi
    P+=($(echo "$out" | proc))
  done
  SL=$(printf '%s\n' "${L[@]}" | med); ST=$(printf '%s\n' "${T[@]}" | med); SP=$(printf '%s\n' "${P[@]}" | med)
  echo "$NAME,$M,seq,$SL,$ST,$SP,1.00,1.00,1.00,100" | tee -a $OUT

  for np in $NPS; do
    BIND="--bind-to core"; [ "$np" -gt 14 ] && BIND="--bind-to hwthread"
    L=();T=();P=()
    for r in $(seq $REPS); do
      out=$(mpirun -np $np --allow-run-as-root $BIND ./lbg_par "$IMG" --$M)
      if [ $M = gray ]; then L+=($(echo "$out" | awk '/Time \(LBG only\)/{print $4}'))
      else L+=($(echo "$out" | awk '/Total LBG time/{print $6}')); fi
      T+=($(echo "$out" | totl)); P+=($(echo "$out" | proc))
    done
    PL=$(printf '%s\n' "${L[@]}" | med); PT=$(printf '%s\n' "${T[@]}" | med); PP=$(printf '%s\n' "${P[@]}" | med)
    awk -v n="$NAME" -v m=$M -v np=$np -v pl=$PL -v pt=$PT -v pp=$PP -v sl=$SL -v st=$ST -v sp=$SP \
      'BEGIN{printf "%s,%s,%d,%s,%s,%s,%.2f,%.2f,%.2f,%.0f\n",n,m,np,pl,pt,pp,sl/pl,st/pt,sp/pp,100*sp/pp/np}' | tee -a $OUT
  done
done
