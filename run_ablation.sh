#!/bin/bash
# Filter ablation on the 12 images: ./lbg_seq must be built from sem_v3f.c.
# Runs run_quality.sh twice (APPLY_FILTER=0 and default) and writes ablation.csv.
[ -x ./lbg_seq ] || { echo "ABORT: ./lbg_seq missing (build sem_v3f.c)"; exit 1; }
OUT=abl_off.csv APPLY_FILTER=0 ./run_quality.sh > /dev/null
OUT=abl_on.csv  ./run_quality.sh > /dev/null
echo "image,mode,CR,MSE_off,MSE_on,PSNR_off,PSNR_on,dPSNR,SSIM_off,SSIM_on,dSSIM" | tee ablation.csv
paste -d, <(tail -n +2 abl_off.csv) <(tail -n +2 abl_on.csv) | awk -F, '{
  printf "%s,%s,%s,%s,%s,%s,%s,%.2f,%s,%s,%.4f\n",$1,$2,$3,$5,$13,$6,$14,$14-$6,$7,$15,$15-$7}' | tee -a ablation.csv
