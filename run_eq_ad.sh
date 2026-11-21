#!/bin/bash
# Equal vs Adaptive (forced via VQ_STRATEGY) with ONE build (./lbg_par = pam_v4.c), 12 images.
# Interleaved runs (equal, adaptive, equal, ...) -> median of 5; raw runs saved in eq_ad_raw.csv.
# usage (in the folder with ./lbg_par and run_all.sh): NPS="2 4 6 8 10 12 14" ./run_eq_ad.sh
D=/home/ibtihal
IMGS="${IMGS:-$D/lbg_exp/gray.txt $D/boat_img.txt $D/cameraman_img.txt $D/peppers_img.txt $D/chest_xray2_img.txt $D/mammo2_img.txt $D/lung_ct2_img.txt $D/brain_mri2_img.txt $D/lena_color.txt $D/retina2_color.txt $D/brain_pet3_color.txt $D/brain_pet4_color.txt}"
NPS=${NPS:-"2 4 6 8 10 12 14"}; REPS=5; OUT=${OUT:-eq_ad.csv}; RAW=${RAW:-eq_ad_raw.csv}
med(){ sort -g | awk '{a[NR]=$1} END{print a[int((NR+1)/2)]}'; }
[ "$(cat /sys/class/power_supply/AC*/online 2>/dev/null | head -1)" = "1" ] || { echo "ABORT: charger not connected"; exit 1; }
[ "$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u)" = "performance" ] || { echo "ABORT: governor is not performance"; exit 1; }
[ -x ./lbg_par ] || { echo "ABORT: ./lbg_par missing"; exit 1; }
lbgt(){ if [ $1 = gray ]; then awk '/Time \(LBG only\)/{print $4}'; else awk '/Total LBG time/{print $6}'; fi; }
echo "image,np,strategy,run,LBG_s" > $RAW
echo "image,mode,np,equal_s,adaptive_s,adaptive_gain_pct" | tee $OUT
for IMG in $IMGS; do
  n=$(wc -w < "$IMG"); NAME=$(basename "$IMG" .txt)
  if [ "$n" = 262144 ]; then M=gray; elif [ "$n" = 786432 ]; then M=color; else echo "$NAME skipped"; continue; fi
  for np in $NPS; do
    E=(); A=()
    for r in $(seq $REPS); do
      e=$(VQ_STRATEGY=equal    mpirun -np $np --allow-run-as-root --bind-to core ./lbg_par "$IMG" --$M | lbgt $M)
      a=$(VQ_STRATEGY=adaptive mpirun -np $np --allow-run-as-root --bind-to core ./lbg_par "$IMG" --$M | lbgt $M)
      E+=($e); A+=($a); echo "$NAME,$np,equal,$r,$e" >> $RAW; echo "$NAME,$np,adaptive,$r,$a" >> $RAW
    done
    me=$(printf '%s\n' "${E[@]}" | med); ma=$(printf '%s\n' "${A[@]}" | med)
    awk -v n="$NAME" -v m=$M -v np=$np -v e=$me -v a=$ma 'BEGIN{printf "%s,%s,%d,%s,%s,%.1f\n",n,m,np,e,a,100*(e-a)/e}' | tee -a $OUT
  done
done
