#!/bin/bash
# Diagnose suspect Equal/Adaptive cells: repeats Equal and Adaptive runs on ONE image at ONE process count
# and records, for every Adaptive run, the calibrated rank speeds and the vector counts it produced.
# usage (folder with ./lbg_par):  ./diag_adaptive.sh <image.txt> <np> [reps=10]   -> prints CSV
IMG=$1; NP=$2; REPS=${3:-10}
[ -n "$IMG" ] && [ -n "$NP" ] || { echo "usage: $0 image.txt np [reps]"; exit 1; }
[ -x ./lbg_par ] || { echo "ABORT: ./lbg_par missing"; exit 1; }
[ "$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u)" = "performance" ] || { echo "ABORT: governor is not performance"; exit 1; }
echo "image,np,run,equal_lbg_s,adaptive_lbg_s,P_speed_mean,E_speed_mean,E_speed_min,P_vectors_rank0,E_vectors_lastrank"
NAME=$(basename "$IMG" .txt)
for r in $(seq $REPS); do
  oe=$(VQ_STRATEGY=equal    mpirun -np $NP --allow-run-as-root --bind-to core ./lbg_par "$IMG" --gray)
  oa=$(VQ_STRATEGY=adaptive mpirun -np $NP --allow-run-as-root --bind-to core ./lbg_par "$IMG" --gray)
  el=$(echo "$oe" | awk '/Time \(LBG only\)/{print $4}')
  al=$(echo "$oa" | awk '/Time \(LBG only\)/{print $4}')
  echo "$oa" | awk -v n="$NAME" -v np=$NP -v r=$r -v el=$el -v al=$al '
    /rank +[0-9]+ : speed=/ {
      match($0,/rank +[0-9]+/); rk=substr($0,RSTART+5,RLENGTH-5)+0
      match($0,/speed=[0-9.]+/); sp=substr($0,RSTART+6,RLENGTH-6)+0
      match($0,/-> +[0-9]+ vectors/); v=substr($0,RSTART+3,RLENGTH-3)+0
      if (rk<6) {ps+=sp; pc++; if (rk==0) v0=v} else {es+=sp; ec++; if (min==""||sp<min) min=sp; vl=v}
    }
    END { printf "%s,%d,%d,%s,%s,%.1f,%.1f,%.1f,%d,%d\n", n,np,r,el,al, (pc?ps/pc:0), (ec?es/ec:0), min, v0, vl }'
done
