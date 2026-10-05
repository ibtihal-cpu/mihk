#!/bin/bash
# Equal vs Adaptive: LBG time AND total time, ONE build (./lbg_par = pam_v4.c), 12 images.
# Strategies are forced via VQ_STRATEGY and alternated; median of 5. Raw runs go to RAW.
# usage (folder with ./lbg_par): NPS="8 14" ./run_eq_ad_total.sh      (default NPS="2 4 6 8 10 12 14")
D=/home/ibtihal
IMGS="${IMGS:-$D/lbg_exp/gray.txt $D/boat_img.txt $D/cameraman_img.txt $D/peppers_img.txt $D/chest_xray2_img.txt $D/mammo2_img.txt $D/lung_ct2_img.txt $D/brain_mri2_img.txt $D/lena_color.txt $D/retina2_color.txt $D/brain_pet3_color.txt $D/brain_pet4_color.txt}"
NPS=${NPS:-"2 4 6 8 10 12 14"}; REPS=5; OUT=${OUT:-eq_ad_total.csv}; RAW=${RAW:-eq_ad_total_raw.csv}
med(){ sort -g | awk '{a[NR]=$1} END{print a[int((NR+1)/2)]}'; }
[ "$(cat /sys/class/power_supply/AC*/online 2>/dev/null | head -1)" = "1" ] || { echo "ABORT: charger not connected"; exit 1; }
[ "$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u)" = "performance" ] || { echo "ABORT: governor is not performance"; exit 1; }
[ -x ./lbg_par ] || { echo "ABORT: ./lbg_par missing"; exit 1; }
lbgt(){ if [ $1 = gray ]; then awk '/Time \(LBG only\)/{print $4}'; else awk '/Total LBG time/{print $6}'; fi; }
tott(){ awk '/Total execution time/{print $4}'; }
echo "image,np,strategy,run,LBG_s,Total_s" > $RAW
echo "image,mode,np,eq_lbg,ad_lbg,lbg_gain_pct,eq_total,ad_total,total_gain_pct" | tee $OUT
for IMG in $IMGS; do
  n=$(wc -w < "$IMG"); NAME=$(basename "$IMG" .txt)
  if [ "$n" = 262144 ]; then M=gray; elif [ "$n" = 786432 ]; then M=color; else echo "$NAME skipped"; continue; fi
  for np in $NPS; do
    EL=(); AL=(); ET=(); AT=()
    for r in $(seq $REPS); do
      oe=$(VQ_STRATEGY=equal    mpirun -np $np --allow-run-as-root --bind-to core ./lbg_par "$IMG" --$M)
      oa=$(VQ_STRATEGY=adaptive mpirun -np $np --allow-run-as-root --bind-to core ./lbg_par "$IMG" --$M)
      el=$(echo "$oe" | lbgt $M); et=$(echo "$oe" | tott); al=$(echo "$oa" | lbgt $M); at=$(echo "$oa" | tott)
      EL+=($el); ET+=($et); AL+=($al); AT+=($at)
      echo "$NAME,$np,equal,$r,$el,$et" >> $RAW; echo "$NAME,$np,adaptive,$r,$al,$at" >> $RAW
    done
    mel=$(printf '%s\n' "${EL[@]}" | med); mal=$(printf '%s\n' "${AL[@]}" | med)
    met=$(printf '%s\n' "${ET[@]}" | med); mat=$(printf '%s\n' "${AT[@]}" | med)
    awk -v n="$NAME" -v m=$M -v np=$np -v el=$mel -v al=$mal -v et=$met -v at=$mat \
      'BEGIN{printf "%s,%s,%d,%s,%s,%.1f,%s,%s,%.1f\n",n,m,np,el,al,100*(el-al)/el,et,at,100*(et-at)/et}' | tee -a $OUT
  done
done
