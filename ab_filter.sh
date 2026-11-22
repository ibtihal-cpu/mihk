#!/bin/bash
# A/B test: filter distributed on all ranks (./lbg_par) versus filter on rank 0 only (./lbg_par_s).
# Interleaved runs (A,B,A,B,...) so that machine drift hits both equally; median of 5.
# usage:  NPS="2 4 8 14" ./ab_filter.sh image1.txt image2.txt ...
REPS=5; NPS=${NPS:-"2 4 8 14"}
med(){ sort -g | awk '{a[NR]=$1} END{print a[int((NR+1)/2)]}'; }
if [ -z "$SKIP_GUARD" ]; then
  [ "$(cat /sys/class/power_supply/AC*/online 2>/dev/null | head -1)" = "1" ] || { echo "ABORT: AC charger not connected"; exit 1; }
  [ "$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u)" = "performance" ] || { echo "ABORT: governor is not performance"; exit 1; }
fi
[ -x ./lbg_par ] && [ -x ./lbg_par_s ] || { echo "ABORT: need ./lbg_par and ./lbg_par_s"; exit 1; }
echo "image,np,Total_parallelFilter_s,Total_serialFilter_s,gain_of_parallel_%,filter_parallel_s,filter_serial_s"
for IMG in "$@"; do
  n=$(wc -w < "$IMG"); NAME=$(basename "$IMG" .txt)
  if [ "$n" = 262144 ]; then M=gray; elif [ "$n" = 786432 ]; then M=color; else echo "$NAME: skipped"; continue; fi
  for np in $NPS; do
    BIND="--bind-to core"; [ "$np" -gt 14 ] && BIND="--bind-to hwthread"
    A=(); B=(); FA=(); FB=()
    for r in $(seq $REPS); do
      oa=$(mpirun -np $np --allow-run-as-root $BIND ./lbg_par   "$IMG" --$M)
      ob=$(mpirun -np $np --allow-run-as-root $BIND ./lbg_par_s "$IMG" --$M)
      A+=($(echo "$oa" | awk '/Total execution time/{print $4}')); B+=($(echo "$ob" | awk '/Total execution time/{print $4}'))
      FA+=($(echo "$oa" | awk '/Bilateral-Post/{for(i=1;i<=NF;i++) if($i=="in") print $(i+1)}'))
      FB+=($(echo "$ob" | awk '/Bilateral-Post/{for(i=1;i<=NF;i++) if($i=="in") print $(i+1)}'))
    done
    ta=$(printf '%s\n' "${A[@]}" | med); tb=$(printf '%s\n' "${B[@]}" | med)
    fa="-"; fb="-"; [ "${#FA[@]}" -gt 0 ] && fa=$(printf '%s\n' "${FA[@]}" | med) && fb=$(printf '%s\n' "${FB[@]}" | med)
    awk -v n="$NAME" -v np=$np -v a=$ta -v b=$tb -v fa=$fa -v fb=$fb 'BEGIN{printf "%s,%d,%s,%s,%.1f,%s,%s\n",n,np,a,b,100*(b-a)/b,fa,fb}'
  done
done
