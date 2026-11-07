#!/bin/bash
# Every stage of the Total processing time, measured in ONE session, so that Total = the sum of the stages.
# Grayscale images only.  Same protocol as run_all_once.sh (AC power, performance governor, sequential pinned,
# mpirun --bind-to core, repetitions as the outer loop; Equal for P <= 6 and Adaptive for P > 6).
# usage (repository root): ./stages/run_allstages.sh ~/final8/lena_gray.txt ~/final8/boat_gray.txt ~/final8/cameraman_gray.txt ~/final8/peppers_gray.txt
NPS=${NPS:-"4 8 14"}; REPS=${REPS:-5}; SEQ_CPU=${SEQ_CPU:-6}; OUT=${OUT:-allstages_RUN}; BIND=${BIND:-"--bind-to core"}
[ $# -gt 0 ] || { echo "usage: $0 image1.txt ..."; exit 1; }
if [ -z "$SKIP_GUARD" ]; then
  [ "$(cat /sys/class/power_supply/AC*/online 2>/dev/null | head -1)" = "1" ] || { echo "ABORT: AC not connected"; exit 1; }
  [ "$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u)" = "performance" ] || { echo "ABORT: governor"; exit 1; }
fi
SRC=$(cd "$(dirname "$0")" && pwd); mkdir -p "$OUT/work"; OUT=$(cd "$OUT" && pwd); W="$OUT/work"
gcc   -O2 -Wall -o "$OUT/seq_all" "$SRC/codes_allstages.c" -lm || exit 1
mpicc -O2 -Wall -o "$OUT/par_all" "$SRC/codep_allstages.c" -lm || exit 1
RAW="$OUT/allstages_raw.txt"; : > "$RAW"
for rep in $(seq $REPS); do
  for IMG in "$@"; do
    N=$(basename "$IMG" .txt)
    out=$(cd "$W" && taskset -c $SEQ_CPU "$OUT/seq_all" "$IMG" --gray); echo "$out" | grep ALLSTAGES | sed "s/^/$N 1 $rep /" | tee -a "$RAW"
    for np in $NPS; do
      sg=equal; [ $np -gt 6 ] && sg=adaptive
      out=$(cd "$W" && VQ_STRATEGY=$sg mpirun $BIND -np $np "$OUT/par_all" "$IMG" --gray); echo "$out" | grep ALLSTAGES | sed "s/^/$N $np $rep /" | tee -a "$RAW"
    done
  done
done
python3 - "$RAW" <<'PY'
import sys, collections as C, statistics as S
d = C.defaultdict(lambda: C.defaultdict(list))
for line in open(sys.argv[1]):
    t = line.split()
    if len(t) < 5 or t[3] != 'ALLSTAGES': continue
    img, P = t[0], int(t[1]); vals = {k: float(v) for k, v in (x.split('=') for x in t[4:])}
    for k, v in vals.items(): d[(img, P)][k].append(v)
keys = ['build', 'prep', 'dist', 'scatter', 'mean', 'lbg', 'gather', 'cvt8', 'delta', 'huff', 'dec', 'total']
imgs = sorted({k[0] for k in d}); Ps = sorted({k[1] for k in d})
def mean_of_medians(P, k): return 1000 * S.mean(S.median(d[(i, P)][k]) for i in imgs)
print("\nMean over the images of the median of the repetitions (milliseconds)\nP,LBG,Delta,Huffman,Decoding,Other,Total,sum_of_columns")
for P in Ps:
    m = {k: mean_of_medians(P, k) for k in keys}
    other = m['build'] + m['prep'] + m['dist'] + m['scatter'] + m['mean'] + m['gather'] + m['cvt8']
    print(f"{P},{m['lbg']:.2f},{m['delta']:.3f},{m['huff']:.3f},{m['dec']:.3f},{other:.2f},{m['total']:.2f},{m['lbg']+m['delta']+m['huff']+m['dec']+other:.2f}")
print("\nComponents of 'Other' (ms)\nP,build,prep(float+barrier),distribution+calibration,scatter,initial_mean,gather,codebook_to_8bit")
for P in Ps:
    m = {k: mean_of_medians(P, k) for k in keys}
    print(f"{P},{m['build']:.3f},{m['prep']:.3f},{m['dist']:.3f},{m['scatter']:.3f},{m['mean']:.3f},{m['gather']:.3f},{m['cvt8']:.3f}")
PY
