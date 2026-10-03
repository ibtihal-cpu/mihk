#!/bin/bash
# usage: ./compare_outputs.sh image.txt [np]      (needs ./lbg_seq ./lbg_par ./lbg_par_bf in this folder)
# Runs the sequential, parallel and parallel-with-distributed-filter programs on one gray image
# and reports quality, LBG iterations and whether the output images are byte-identical.
HERE=$PWD; NP=${2:-4}; W=$(mktemp -d)
[ -f "$1" ] || { echo "usage: $0 image.txt [np]"; exit 1; }
IMG=$(readlink -f "$1")
for b in lbg_seq lbg_par lbg_par_bf; do [ -x ./$b ] || { echo "ABORT: ./$b missing"; exit 1; }; done
mkdir -p $W/seq $W/par $W/bf
(cd $W/seq && "$HERE"/lbg_seq "$IMG" --gray > out.txt)
(cd $W/par && mpirun -np $NP --allow-run-as-root --bind-to core "$HERE"/lbg_par "$IMG" --gray > out.txt)
(cd $W/bf  && mpirun -np $NP --allow-run-as-root --bind-to core "$HERE"/lbg_par_bf "$IMG" --gray > out.txt)
show(){ awk -v n="$1" '/^MSE +=/{m=$3} /^PSNR +=/{p=$3} /^SSIM/{for(i=1;i<=NF;i++) if($i=="="){s=$(i+1);break}} /LBG total iterations/{t=$NF} END{printf "%-9s MSE=%s PSNR=%s SSIM=%s iters=%s\n",n,m,p,s,t}' "$2"; }
echo "image: $IMG   np=$NP"
show seq $W/seq/out.txt; show par $W/par/out.txt; show par_bf $W/bf/out.txt
f1=$W/seq/compressed_filtered.bmp; f2=$W/par/compressed.bmp; f3=$W/bf/compressed.bmp
cmp -s $f2 $f3 && echo "par    vs par_bf : IDENTICAL" || echo "par    vs par_bf : DIFFERENT ($(cmp -l $f2 $f3 | wc -l) bytes)"
cmp -s $f1 $f2 && echo "seq    vs par    : IDENTICAL" || echo "seq    vs par    : DIFFERENT ($(cmp -l $f1 $f2 | wc -l) bytes of $(stat -c %s $f1))"
cmp -s $W/seq/original.bmp $W/par/original.bmp && echo "original vs original : IDENTICAL"
echo "images kept in: $W   (open with: eog $W/seq/original.bmp $f1 $f2 $f3)"
