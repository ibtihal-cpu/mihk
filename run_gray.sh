#!/bin/bash
IMG=${1:-gray.txt}; REPS=5
med(){ sort -g | awk '{a[NR]=$1} END{print a[int((NR+1)/2)]}'; }

# ---- sequential, pinned to core 0 ----
L=();T=()
for r in $(seq $REPS); do
  out=$(taskset -c 0 ./lbg_seq $IMG --gray)
  L+=($(echo "$out" | awk '/LBG \(wall/{print $6}'))
  T+=($(echo "$out" | awk '/Total \(measured\)/{print $4}'))
  IT=$(echo "$out" | awk '/LBG total iterations/{print $6}')
done
SL=$(printf '%s\n' "${L[@]}" | med); ST=$(printf '%s\n' "${T[@]}" | med)
echo "np,LBG_s,Total_s,iters,SpeedupLBG,SpeedupTotal,Eff%"
echo "seq,$SL,$ST,$IT,1.00,1.00,100"

# ---- parallel, bound to cores ----
for np in 2 4 8; do
  L=();T=()
  for r in $(seq $REPS); do
    out=$(mpirun -np $np --allow-run-as-root --bind-to core --map-by core ./lbg_par $IMG --gray)
    L+=($(echo "$out" | awk '/Time \(LBG only\)/{print $4}'))
    T+=($(echo "$out" | awk '/Total execution time/{print $4}'))
    IT=$(echo "$out" | awk '/LBG total iterations/{print $4}')
  done
  PL=$(printf '%s\n' "${L[@]}" | med); PT=$(printf '%s\n' "${T[@]}" | med)
  awk -v np=$np -v pl=$PL -v pt=$PT -v sl=$SL -v st=$ST -v it=$IT \
    'BEGIN{printf "%d,%s,%s,%s,%.2f,%.2f,%.0f\n",np,pl,pt,it,sl/pl,st/pt,100*sl/pl/np}'
done
