#!/bin/bash
# Correctness check: sequential vs parallel results for the 12 images, with the FINAL programs.
#   ./lbg_seq = sem_v3.c      ./lbg_par = pam_v4.c      (build both in this folder)
# For every image it runs: sequential; parallel P=4 (default = Equal); parallel P=14 (default = Adaptive);
# parallel P=14 forced Equal. It compares CR, MSE, PSNR, SSIM and the LBG iteration count, and the MD5 of the
# saved reconstructed image. Output: correctness.csv  (one run per case; the values are deterministic).
D=/home/ibtihal
IMGS="${IMGS:-$D/lbg_exp/gray.txt $D/boat_img.txt $D/cameraman_img.txt $D/peppers_img.txt $D/chest_xray2_img.txt $D/mammo2_img.txt $D/lung_ct2_img.txt $D/brain_mri2_img.txt $D/lena_color.txt $D/retina2_color.txt $D/brain_pet3_color.txt $D/brain_pet4_color.txt}"
OUT=${OUT:-correctness.csv}; HERE=$PWD
for b in lbg_seq lbg_par; do [ -x ./$b ] || { echo "ABORT: ./$b missing"; exit 1; }; done
W=$(mktemp -d)
ext(){ # $1 = mode, stdin = program output  ->  "CR MSE PSNR SSIM iters"
  if [ "$1" = gray ]; then
    awk '/^MSE +=/{m=$3} /^PSNR +=/{p=$3} /^SSIM/{for(i=1;i<=NF;i++) if($i=="="){s=$(i+1);break}} /System total/{c=$4} /LBG total iterations/{n=$NF} END{print c, m, p, s, n}'
  else
    out=$(cat); it=$(echo "$out" | grep -o 'LBG iters=[0-9]*' | cut -d= -f2 | paste -sd+ | bc)
    echo "$out" | awk -v it="$it" '/RGB CR/{c=$5} /RGB MSE/{m=$4} /RGB PSNR/{p=$4} /Mean Channel-wise SSIM/{s=$5} END{print c, m, p, s, it}'
  fi
}
bmpname(){ [ "$1" = gray ] && echo "$2" || echo compressed_color.bmp; }
echo "image,mode,seq,par_P4_auto,par_P14_auto,par_P14_equal,metrics_identical,reconstruction_md5_identical" | tee $OUT
for IMG in $IMGS; do
  n=$(wc -w < "$IMG"); NAME=$(basename "$IMG" .txt)
  if [ "$n" = 262144 ]; then M=gray; elif [ "$n" = 786432 ]; then M=color; else echo "$NAME skipped"; continue; fi
  IMGABS=$(readlink -f "$IMG")
  for c in seq p4 p14 p14e; do rm -rf $W/$c; mkdir -p $W/$c; done
  S=$(cd $W/seq && "$HERE"/lbg_seq "$IMGABS" --$M | ext $M)
  A=$(cd $W/p4  && mpirun -np 4  --allow-run-as-root --bind-to core "$HERE"/lbg_par "$IMGABS" --$M | ext $M)
  B=$(cd $W/p14 && mpirun -np 14 --allow-run-as-root --bind-to core "$HERE"/lbg_par "$IMGABS" --$M | ext $M)
  E=$(cd $W/p14e && VQ_STRATEGY=equal mpirun -np 14 --allow-run-as-root --bind-to core "$HERE"/lbg_par "$IMGABS" --$M | ext $M)
  if [ "$S" = "$A" ] && [ "$S" = "$B" ] && [ "$S" = "$E" ]; then MI=yes; else MI=NO; fi
  if [ $M = gray ]; then FS=$W/seq/compressed_filtered.bmp; FP=compressed.bmp; else FS=$W/seq/compressed_color.bmp; FP=compressed_color.bmp; fi
  h0=$(md5sum < $FS); h1=$(md5sum < $W/p4/$FP); h2=$(md5sum < $W/p14/$FP); h3=$(md5sum < $W/p14e/$FP)
  if [ "$h0" = "$h1" ] && [ "$h0" = "$h2" ] && [ "$h0" = "$h3" ]; then HI=yes; else HI=NO; fi
  echo "$NAME,$M,\"$S\",\"$A\",\"$B\",\"$E\",$MI,$HI" | tee -a $OUT
done
rm -rf $W
