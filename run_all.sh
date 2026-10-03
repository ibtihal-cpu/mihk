#!/bin/bash
# usage: NPS="2 4 6 8" ./run_all.sh img1.txt img2.txt ...
# Protocol: AC connected, governor=performance, median of 5, sequential pinned to a P-core,
# mpirun --bind-to core (np<=14) or --bind-to hwthread (np>14). Gray/color auto-detected.
NPS=${NPS:-"2 4 6 8"}; REPS=5; SEQ_CPU=${SEQ_CPU:-6}; OUT=${OUT:-results_all.csv}
med(){ sort -g | awk '{a[NR]=$1} END{print a[int((NR+1)/2)]}'; }

if [ -z "$SKIP_GUARD" ]; then
  [ "$(cat /sys/class/power_supply/AC*/online 2>/dev/null | head -1)" = "1" ] || { echo "ABORT: AC charger not connected"; exit 1; }
  [ "$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u)" = "performance" ] || { echo "ABORT: governor is not performance on all CPUs"; exit 1; }
fi
taskset -c $SEQ_CPU true 2>/dev/null || { echo "ABORT: cannot pin to CPU $SEQ_CPU (set SEQ_CPU)"; exit 1; }
[ -x ./lbg_seq ] && [ -x ./lbg_par ] || { echo "ABORT: build lbg_seq and lbg_par first"; exit 1; }

echo "image,mode,np,LBG_s,Total_s,iters,SpeedupLBG,SpeedupTotal,Eff%" | tee $OUT
for IMG in "$@"; do
  n=$(wc -w < "$IMG"); NAME=$(basename "$IMG" .txt)
  if   [ "$n" = 262144 ]; then M=gray
  elif [ "$n" = 786432 ]; then M=color
  else echo "$NAME: unknown size ($n tokens), skipped"; continue; fi

  L=();T=();IT=0
  for r in $(seq $REPS); do
    out=$(taskset -c $SEQ_CPU ./lbg_seq "$IMG" --$M)
    if [ $M = gray ]; then
      L+=($(echo "$out" | awk '/LBG \(wall/{print $6}'))
      T+=($(echo "$out" | awk '/Total \(measured\)/{print $4}'))
      IT=$(echo "$out" | awk '/LBG total iterations/{print $6}')
    else
      L+=($(echo "$out" | awk '/Total LBG time/{print $6}'))
      T+=($(echo "$out" | awk '/Total program time/{print $5}'))
      IT=$(echo "$out" | grep -o 'LBG iters=[0-9]*' | cut -d= -f2 | paste -sd+ | bc)
    fi
  done
  SL=$(printf '%s\n' "${L[@]}" | med); ST=$(printf '%s\n' "${T[@]}" | med)
  echo "$NAME,$M,seq,$SL,$ST,$IT,1.00,1.00,100" | tee -a $OUT

  for np in $NPS; do
    BIND="--bind-to core"; [ "$np" -gt 14 ] && BIND="--bind-to hwthread"
    L=();T=();IT=0
    for r in $(seq $REPS); do
      out=$(mpirun -np $np --allow-run-as-root $BIND ./lbg_par "$IMG" --$M)
      if [ $M = gray ]; then
        L+=($(echo "$out" | awk '/Time \(LBG only\)/{print $4}'))
        IT=$(echo "$out" | awk '/LBG total iterations/{print $4}')
      else
        L+=($(echo "$out" | awk '/Total LBG time/{print $6}'))
        IT=$(echo "$out" | grep -o 'LBG iters=[0-9]*' | cut -d= -f2 | paste -sd+ | bc)
      fi
      T+=($(echo "$out" | awk '/Total execution time/{print $4}'))
    done
    PL=$(printf '%s\n' "${L[@]}" | med); PT=$(printf '%s\n' "${T[@]}" | med)
    awk -v n="$NAME" -v m=$M -v np=$np -v pl=$PL -v pt=$PT -v sl=$SL -v st=$ST -v it=$IT \
      'BEGIN{printf "%s,%s,%d,%s,%s,%s,%.2f,%.2f,%.0f\n",n,m,np,pl,pt,it,sl/pl,st/pt,100*sl/pl/np}' | tee -a $OUT
  done
done
