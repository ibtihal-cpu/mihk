#!/bin/bash
# usage: ./check_cores.sh gray.txt   (needs ./lbg_seq in the same folder)
IMG=${1:-gray.txt}
med(){ sort -g | awk '{a[NR]=$1} END{print a[int((NR+1)/2)]}'; }
for c in 0 2 4 6; do
  L=()
  for r in 1 2 3 4 5; do
    L+=($(taskset -c $c ./lbg_seq $IMG --gray | awk '/LBG \(wall/{print $6}'))
  done
  echo "core $c LBG median: $(printf '%s\n' "${L[@]}" | med)"
done
