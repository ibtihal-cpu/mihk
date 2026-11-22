#!/bin/bash
# Parameter study with the FINAL sequential program (sem_v3.c): block size (2x2, 4x4, 8x8 at K=64) and
# codebook size (K = 32, 64, 128 at 4x4). Variants are built from sem_v3.c by changing the two #defines.
# Quality (PSNR, SSIM, system CR) is deterministic: taken from the first run. LBG time: median of REPS runs,
# sequential program pinned to one CPU (SEQ_CPU, default 6). Output: param_study.csv
# usage: SRC=~/mihk_ok/sem_v3.c ./run_param_study.sh            (default images: the 8 grayscale images)
SRC=${SRC:-$HOME/mihk_ok/sem_v3.c}; REPS=${REPS:-5}; SEQ_CPU=${SEQ_CPU:-6}; OUT=${OUT:-param_study.csv}
D=${D:-$HOME}
IMGS="${IMGS:-$D/lbg_exp/gray.txt $D/boat_img.txt $D/cameraman_img.txt $D/peppers_img.txt $D/chest_xray2_img.txt $D/mammo2_img.txt $D/lung_ct2_img.txt $D/brain_mri2_img.txt}"
[ -f "$SRC" ] || { echo "ABORT: $SRC not found"; exit 1; }
if [ -z "$SKIP_GUARD" ]; then
  [ "$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u)" = "performance" ] || { echo "ABORT: governor is not performance"; exit 1; }
fi
W=$(mktemp -d)
med(){ sort -g | awk '{a[NR]=$1} END{print a[int((NR+1)/2)]}'; }
build(){ # $1=block $2=K
  sed -e "s/^#define BLOCK_SIZE 4/#define BLOCK_SIZE $1/" -e "s/^#define CODEBOOK_SIZE 64/#define CODEBOOK_SIZE $2/" "$SRC" > $W/v_$1_$2.c
  grep -q "^#define BLOCK_SIZE $1" $W/v_$1_$2.c && grep -q "^#define CODEBOOK_SIZE $2" $W/v_$1_$2.c || { echo "ABORT: sed did not change the defines"; exit 1; }
  gcc -O2 -o $W/v_$1_$2 $W/v_$1_$2.c -lm || exit 1
}
echo "variant,block,K,image,PSNR_dB,SSIM,system_CR,LBG_iters,LBG_time_median_s" | tee $OUT
for v in "2 64" "4 64" "8 64" "4 32" "4 128"; do
  set -- $v; B=$1; K=$2; build $B $K
  for IMG in $IMGS; do
    [ -f "$IMG" ] || { echo "skip $IMG"; continue; }
    NAME=$(basename "$IMG" .txt); T=()
    for r in $(seq $REPS); do
      out=$(cd $W && taskset -c $SEQ_CPU ./v_${B}_${K} "$(readlink -f "$IMG")" --gray)
      T+=($(echo "$out" | awk '/LBG \(wall/{print $6}'))
      if [ $r = 1 ]; then
        Q=$(echo "$out" | awk '/^PSNR +=/{p=$3} /^SSIM/{for(i=1;i<=NF;i++) if($i=="="){s=$(i+1);break}} /System total/{c=$4} /LBG total iterations/{n=$NF} END{print p","s","c","n}')
      fi
    done
    M=$(printf '%s\n' "${T[@]}" | med)
    echo "${B}x${B}/K${K},$B,$K,$NAME,$Q,$M" | tee -a $OUT
  done
done
rm -rf $W
