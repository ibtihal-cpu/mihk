#!/bin/bash
# Per-stage times (delta coding, Huffman container encoding, container decoding) for the sequential and the
# parallel program.  Uses the *_stages.c copies (same compressed output as *_min.c, see make_stages.py).
# Same protocol as run_all_once.sh: AC power, governor = performance, sequential pinned to one P-core,
# mpirun --bind-to core, 5 repetitions (outer loop), Equal for P <= 6 and Adaptive for P > 6.
# usage: ./stages/run_stages.sh ~/final8/*.txt        (run from the repo root)
NPS=${NPS:-"4 8 14"}; REPS=${REPS:-5}; SEQ_CPU=${SEQ_CPU:-6}; OUT=${OUT:-stages_RUN}
BIND=${BIND:-"--bind-to core"}
[ $# -gt 0 ] || { echo "usage: $0 image1.txt ..."; exit 1; }
[ "$(cat /sys/class/power_supply/AC*/online 2>/dev/null | head -1)" = "1" ] || { echo "ABORT: AC not connected"; exit 1; }
[ "$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u)" = "performance" ] || { echo "ABORT: governor"; exit 1; }
SRC=$(cd "$(dirname "$0")" && pwd); mkdir -p "$OUT/work"; OUT=$(cd "$OUT" && pwd); W="$OUT/work"
gcc   -O2 -Wall -o "$OUT/seq_st" "$SRC/codes_stages.c" -lm || exit 1
mpicc -O2 -Wall -o "$OUT/par_st" "$SRC/codep_stages.c" -lm || exit 1
mode_of(){ n=$(wc -w < "$1"); if [ "$n" = 262144 ]; then echo gray; elif [ "$n" = 786432 ]; then echo color; else echo unknown; fi; }
st(){ awk '/^STAGES/{for(i=2;i<=NF;i++){split($i,a,"=");v[a[1]]=a[2]}} END{printf "%s,%s,%s", v["delta"],v["huffman"],v["decode"]}'; }
CSV="$OUT/stages_raw.csv"; echo "image,mode,np,rep,delta_s,huffman_s,decode_s" > "$CSV"
for rep in $(seq $REPS); do
  for IMG in "$@"; do
    N=$(basename "$IMG" .txt); M=$(mode_of "$IMG"); [ "$M" = unknown ] && continue
    out=$(cd "$W" && taskset -c $SEQ_CPU "$OUT/seq_st" "$IMG" --$M); echo "$N,$M,1,$rep,$(echo "$out" | st)" | tee -a "$CSV"
    for np in $NPS; do
      sg=equal; [ $np -gt 6 ] && sg=adaptive
      out=$(cd "$W" && VQ_STRATEGY=$sg mpirun $BIND -np $np "$OUT/par_st" "$IMG" --$M); echo "$N,$M,$np,$rep,$(echo "$out" | st)" | tee -a "$CSV"
    done
  done
done
python3 - "$CSV" <<'PY'
import csv, sys, statistics as S, collections as C
d = C.defaultdict(list)
for r in csv.DictReader(open(sys.argv[1])): d[(r['image'], r['mode'], int(r['np']))].append(r)
print("\nMedian over repetitions (milliseconds)\nimage,mode,P,delta_ms,huffman_ms,decode_ms")
for (img, m, p), rows in sorted(d.items(), key=lambda x: (x[0][1], x[0][0], x[0][2])):
    f = lambda k: 1000 * S.median(float(r[k]) for r in rows)
    print(f"{img},{m},{p},{f('delta_s'):.3f},{f('huffman_s'):.3f},{f('decode_s'):.3f}")
PY
