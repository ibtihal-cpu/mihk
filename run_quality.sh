#!/bin/bash
# Quality table (CR, BPP, MSE, PSNR, SSIM, LBG iterations) for the 12 thesis images with ONE program version.
# Uses ./lbg_seq (build sem_v2.c as lbg_seq in this folder). Optional override: name=path arguments.
D=/home/ibtihal
DEFAULT="Lena=$D/lbg_exp/gray.txt Boat=$D/boat_img.txt Cameraman=$D/cameraman_img.txt Peppers=$D/peppers_img.txt Chest_X-ray=$D/chest_xray2_img.txt Mammogram=$D/mammo2_img.txt Lung_CT=$D/lung_ct2_img.txt Brain_MRI=$D/brain_mri2_img.txt Lena_Color=$D/lena_color.txt Retina=$D/retina2_color.txt PET_Axial=$D/brain_pet3_color.txt PET_Sagittal=$D/brain_pet4_color.txt"
LIST=${@:-$DEFAULT}; OUT=${OUT:-quality_v2.csv}
[ -x ./lbg_seq ] || { echo "ABORT: ./lbg_seq missing"; exit 1; }
echo "image,mode,CR_system,BPP,MSE,PSNR_dB,SSIM,LBG_iters" | tee $OUT
for item in $LIST; do
  name=${item%%=*}; path=${item#*=}
  n=$({ wc -w < "$path"; } 2>/dev/null)
  if   [ "$n" = 262144 ]; then M=gray
  elif [ "$n" = 786432 ]; then M=color
  else echo "$name: missing or not 512x512 ($path)"; continue; fi
  out=$(./lbg_seq "$path" --$M)
  if [ $M = gray ]; then
    echo "$out" | awk -v n="$name" '/^MSE +=/{m=$3} /^PSNR +=/{p=$3} /^SSIM +=/{s=$3} /System total/{c=$4} /LBG total iterations/{t=$NF}
      END{printf "%s,gray,%s,%.4f,%s,%s,%s,%s\n",n,c,8.0/c,m,p,s,t}' | tee -a $OUT
  else
    it=$(echo "$out" | grep -o 'LBG iters=[0-9]*' | cut -d= -f2 | paste -sd+ | bc)
    echo "$out" | awk -v n="$name" -v it="$it" '/RGB PSNR/{p=$4} /Mean Channel-wise SSIM/{s=$5} /RGB MSE/{m=$4} /RGB CR/{c=$5}
      END{printf "%s,color,%s,%.4f,%s,%s,%s,%s\n",n,c,8.0/c,m,p,s,it}' | tee -a $OUT
  fi
done
