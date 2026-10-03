#!/bin/bash
# Same-session, interleaved comparison of LBG time at np = 8 and 14:
#   v3-auto  : ./lbg_par   (pam_v3.c, default strategy)      v3s-auto : ./lbg_par_s (pam_v3s.c, default strategy)
#   v3s-equal / v3s-adaptive : ./lbg_par_s with VQ_STRATEGY forced
# Sequential baseline = ./lbg_seq pinned to a P-core. Median of 7. usage: ./ab_lbg.sh img1.txt [img2.txt ...]
REPS=7; SEQ_CPU=${SEQ_CPU:-6}; NPS=${NPS:-"8 14"}
med(){ sort -g | awk '{a[NR]=$1} END{print a[int((NR+1)/2)]}'; }
if [ -z "$SKIP_GUARD" ]; then
  [ "$(cat /sys/class/power_supply/AC*/online 2>/dev/null | head -1)" = "1" ] || { echo "ABORT: AC charger not connected"; exit 1; }
  [ "$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u)" = "performance" ] || { echo "ABORT: governor is not performance"; exit 1; }
fi
for b in lbg_seq lbg_par lbg_par_s; do [ -x ./$b ] || { echo "ABORT: ./$b missing"; exit 1; }; done
lbgt(){ awk '/Time \(LBG only\)/{print $4}'; }
echo "image,np,variant,LBG_median_s,speedup_vs_seq,seq_LBG_s"
for IMG in "$@"; do
  NAME=$(basename "$IMG" .txt)
  S=(); for r in $(seq $REPS); do S+=($(taskset -c $SEQ_CPU ./lbg_seq "$IMG" --gray | awk '/LBG \(wall/{print $6}')); done
  SL=$(printf '%s\n' "${S[@]}" | med)
  for np in $NPS; do
    A=(); B=(); E=(); D=()
    for r in $(seq $REPS); do
      A+=($(VQ_STRATEGY=auto     mpirun -np $np --allow-run-as-root --bind-to core ./lbg_par   "$IMG" --gray | lbgt))
      B+=($(VQ_STRATEGY=auto     mpirun -np $np --allow-run-as-root --bind-to core ./lbg_par_s "$IMG" --gray | lbgt))
      E+=($(VQ_STRATEGY=equal    mpirun -np $np --allow-run-as-root --bind-to core ./lbg_par_s "$IMG" --gray | lbgt))
      D+=($(VQ_STRATEGY=adaptive mpirun -np $np --allow-run-as-root --bind-to core ./lbg_par_s "$IMG" --gray | lbgt))
    done
    for v in "v3-auto:A" "v3s-auto:B" "v3s-equal:E" "v3s-adaptive:D"; do
      name=${v%%:*}; arr=${v##*:}; eval "vals=(\"\${$arr[@]}\")"
      m=$(printf '%s\n' "${vals[@]}" | med)
      awk -v n="$NAME" -v np=$np -v v=$name -v m=$m -v s=$SL 'BEGIN{printf "%s,%d,%s,%s,%.2f,%s\n",n,np,v,m,s/m,s}'
    done
  done
done
