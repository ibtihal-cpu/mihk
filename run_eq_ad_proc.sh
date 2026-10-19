#!/bin/bash
# Equal vs Adaptive with the PROCESSING time (OPTIONAL, separate from the approved campaign).
# Builds lbg_par from pam_v7_proc.c (= pam_v4_nofilter_final.c + one extra printed line) and, for every image and P,
# forces each strategy via VQ_STRATEGY (alternating order, median of 5) and records LBG, Processing and Total time.
# usage:  NPS="2 4 6 8 10 12 14" ./run_eq_ad_proc.sh img1.txt ... img8.txt          (same protocol as run_eq_ad_total.sh)
NPS=${NPS:-"2 4 6 8 10 12 14"}; REPS=5; OUT=${OUT:-eq_ad_proc.csv}; RAW=${RAW:-eq_ad_proc_raw.csv}; SRC_DIR=${SRC_DIR:-$(dirname "$0")}
med(){ sort -g | awk '{a[NR]=$1} END{print a[int((NR+1)/2)]}'; }
if [ -z "$SKIP_GUARD" ]; then
  [ "$(cat /sys/class/power_supply/AC*/online 2>/dev/null | head -1)" = "1" ] || { echo "ABORT: charger not connected"; exit 1; }
  [ "$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u)" = "performance" ] || { echo "ABORT: governor is not performance"; exit 1; }
fi
mpicc ${CFLAGS:--O2} -o lbg_par "$SRC_DIR/pam_v7_proc.c" -lm || exit 1
echo "md5 : $(md5sum "$SRC_DIR/pam_v7_proc.c")"
lbgt(){ if [ $1 = gray ]; then awk '/Time \(LBG only\)/{print $4}'; else awk '/Total LBG time/{print $6}'; fi; }
tott(){ awk '/Total execution time/{print $4}'; }
proct(){ awk -F': ' '/Processing time/{print $2+0}'; }
echo "image,np,strategy,run,LBG_s,Proc_s,Total_s" > $RAW
echo "image,mode,np,eq_lbg,ad_lbg,lbg_gain_pct,eq_proc,ad_proc,proc_gain_pct,eq_total,ad_total,total_gain_pct" | tee $OUT
for IMG in "$@"; do
  n=$(wc -w < "$IMG"); NAME=$(basename "$IMG" .txt)
  if [ "$n" = 262144 ]; then M=gray; elif [ "$n" = 786432 ]; then M=color; else echo "$NAME skipped (size $n)"; continue; fi
  for np in $NPS; do
    EL=();AL=();EP=();AP=();ET=();AT=()
    for r in $(seq $REPS); do
      if [ $((r % 2)) -eq 1 ]; then
        oe=$(VQ_STRATEGY=equal    mpirun -np $np --allow-run-as-root --bind-to core ./lbg_par "$IMG" --$M)
        oa=$(VQ_STRATEGY=adaptive mpirun -np $np --allow-run-as-root --bind-to core ./lbg_par "$IMG" --$M)
      else
        oa=$(VQ_STRATEGY=adaptive mpirun -np $np --allow-run-as-root --bind-to core ./lbg_par "$IMG" --$M)
        oe=$(VQ_STRATEGY=equal    mpirun -np $np --allow-run-as-root --bind-to core ./lbg_par "$IMG" --$M)
      fi
      el=$(echo "$oe" | lbgt $M); ep=$(echo "$oe" | proct); et=$(echo "$oe" | tott)
      al=$(echo "$oa" | lbgt $M); ap=$(echo "$oa" | proct); at=$(echo "$oa" | tott)
      EL+=($el);EP+=($ep);ET+=($et);AL+=($al);AP+=($ap);AT+=($at)
      echo "$NAME,$np,equal,$r,$el,$ep,$et" >> $RAW; echo "$NAME,$np,adaptive,$r,$al,$ap,$at" >> $RAW
    done
    m(){ printf '%s\n' "$@" | med; }
    mel=$(m "${EL[@]}"); mal=$(m "${AL[@]}"); mep=$(m "${EP[@]}"); map=$(m "${AP[@]}"); met=$(m "${ET[@]}"); mat=$(m "${AT[@]}")
    awk -v n="$NAME" -v mo=$M -v np=$np -v el=$mel -v al=$mal -v ep=$mep -v ap=$map -v et=$met -v at=$mat \
      'BEGIN{printf "%s,%s,%d,%s,%s,%.1f,%s,%s,%.1f,%s,%s,%.1f\n",n,mo,np,el,al,100*(el-al)/el,ep,ap,100*(ep-ap)/ep,et,at,100*(et-at)/et}' | tee -a $OUT
  done
done
