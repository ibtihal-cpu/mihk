#!/bin/bash
# Iterations of every splitting stage (k = 2, 4, ..., 64) of the sequential LBG, per image and channel.
# The per-stage limit is 100 iterations; this shows whether any stage reached it.
# usage: ./stages/run_iters.sh ~/final8/*.txt        (run from the repo root)
SEQ_CPU=${SEQ_CPU:-6}; OUT=${OUT:-iters_RUN}
[ $# -gt 0 ] || { echo "usage: $0 image1.txt ..."; exit 1; }
SRC=$(cd "$(dirname "$0")" && pwd); mkdir -p "$OUT/work"; OUT=$(cd "$OUT" && pwd)
gcc -O2 -Wall -o "$OUT/seq_it" "$SRC/codes_iters.c" -lm || exit 1
mode_of(){ n=$(wc -w < "$1"); if [ "$n" = 262144 ]; then echo gray; elif [ "$n" = 786432 ]; then echo color; else echo unknown; fi; }
CSV="$OUT/iters.csv"; echo "image,mode,channel,k2,k4,k8,k16,k32,k64,total,max_stage,reached_100" > "$CSV"
for IMG in "$@"; do
  N=$(basename "$IMG" .txt); M=$(mode_of "$IMG"); [ "$M" = unknown ] && continue
  out=$(cd "$OUT/work" && taskset -c $SEQ_CPU "$OUT/seq_it" "$IMG" --$M)
  echo "$out" | grep "(converged)" | sed -E 's/.*iter= *([0-9]+).*/\1/' | paste -sd, - | python3 -c "
import sys
v = [int(x) for x in sys.stdin.read().strip().split(',')]
name, mode = '$N', '$M'
ch = ['gray'] if mode == 'gray' else ['R', 'G', 'B']
assert len(v) == 6 * len(ch), len(v)
for i, c in enumerate(ch):
    s = v[6*i:6*i+6]
    print(f'{name},{mode},{c},' + ','.join(map(str, s)) + f',{sum(s)},{max(s)},' + ('YES' if max(s) >= 100 else 'no'))
" | tee -a "$CSV"
  [ "$M" = gray ] && echo "   printed by the program: $(echo "$out" | grep 'LBG iterations')" || true
done
echo; echo "stage limit = 100; stages that reached it: $(grep -c ',YES$' "$CSV")"
