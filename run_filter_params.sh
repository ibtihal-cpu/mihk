#!/bin/bash
# Earlier vs final post-compression bilateral-filter parameters, same program (sem_v3.c), same images.
#   earlier (published pipeline, sem.c): d=5, sigma_color=20, sigma_space=20, alpha=0.8
#   final   (sem_v3.c)                 : d=3, sigma_color=80, sigma_space=5,  alpha=0.4
# Only the four #defines change; LBG, delta + Huffman, CR are identical. Quality values are deterministic (one run).
# Each image is marked TUNE (used by the train/test sweep to choose the final parameters) or TEST (held out).
# usage: SRC=~/mihk_ok/sem_v3.c ./run_filter_params.sh     -> filter_params.csv
SRC=${SRC:-$HOME/mihk_ok/sem_v3.c}; OUT=${OUT:-filter_params.csv}; D=${D:-$HOME}
[ -f "$SRC" ] || { echo "ABORT: $SRC not found"; exit 1; }
# name  file  mode  set
LIST="Lena lbg_exp/gray.txt gray TUNE
Boat boat_img.txt gray TUNE
Cameraman cameraman_img.txt gray TEST
Peppers peppers_img.txt gray TEST
Chest_X-ray chest_xray2_img.txt gray TUNE
Mammogram mammo2_img.txt gray TEST
Lung_CT lung_ct2_img.txt gray TEST
Brain_MRI brain_mri2_img.txt gray TUNE
Lena_Color lena_color.txt color EXCLUDED
Retina retina2_color.txt color TEST
PET_Axial brain_pet3_color.txt color TUNE
PET_Sagittal brain_pet4_color.txt color TEST"
W=$(mktemp -d)
mk(){ # $1 name $2 d $3 sc $4 ss $5 alpha
  sed -e "s/^#define BF_D .*/#define BF_D            $2/" -e "s/^#define BF_SIGMA_COLOR .*/#define BF_SIGMA_COLOR  $3/" \
      -e "s/^#define BF_SIGMA_SPACE .*/#define BF_SIGMA_SPACE  $4/" -e "s/^#define BF_ALPHA .*/#define BF_ALPHA        $5/" "$SRC" > $W/$1.c
  grep -q "^#define BF_D            $2" $W/$1.c && grep -q "^#define BF_ALPHA        $5" $W/$1.c || { echo "ABORT: sed failed"; exit 1; }
  gcc -O2 -o $W/$1 $W/$1.c -lm || exit 1
}
mk earlier 5 20.0f 20.0f 0.8f
mk final   3 80.0f 5.0f   0.4f
ext(){ # $1 mode ; stdin = program output -> "CR MSE PSNR SSIM"
  if [ "$1" = gray ]; then
    awk '/^MSE +=/{m=$3} /^PSNR +=/{p=$3} /^SSIM/{for(i=1;i<=NF;i++) if($i=="="){s=$(i+1);break}} /System total/{c=$4} END{print c","m","p","s}'
  else
    awk '/RGB CR/{c=$5} /RGB MSE/{m=$4} /RGB PSNR/{p=$4} /Mean Channel-wise SSIM/{s=$5} END{print c","m","p","s}'
  fi
}
echo "image,mode,set,config,CR,MSE,PSNR_dB,SSIM" | tee $OUT
echo "$LIST" | while read NAME REL MODE SET; do
  IMG="$D/$REL"; [ -f "$IMG" ] || { echo "skip $NAME ($IMG)"; continue; }
  for C in earlier final; do
    mkdir -p $W/run_$C; r=$(cd $W/run_$C && $W/$C "$(readlink -f "$IMG")" --$MODE | ext $MODE)
    echo "$NAME,$MODE,$SET,$C,$r" | tee -a $OUT
  done
done
rm -rf $W
