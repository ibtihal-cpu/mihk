#!/bin/bash
# Side experiment: MPI-parallel delta encode / Huffman / delta decode (lbg_pure_mpi.c, June 2026 version).
# LBG stays sequential in that program.  Median of REPS runs per image and P; P = 1 is the reference.
# usage: BIN=~/thesis_evidence/old_experiments/lbg_pure_mpi ./stages/run_old_parallel_stages.sh ~/final8/*_gray.txt
NPS=${NPS:-"1 2 4 8 14"}; REPS=${REPS:-5}; BIN=${BIN:-$HOME/thesis_evidence/old_experiments/lbg_pure_mpi}
OUT=${OUT:-$HOME/thesis_evidence/old_experiments}
[ -x "$BIN" ] || { echo "ABORT: $BIN not found (compile lbg_pure_mpi.c with mpicc first)"; exit 1; }
[ "$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u)" = "performance" ] || { echo "ABORT: governor"; exit 1; }
[ "$(cat /sys/class/power_supply/AC*/online 2>/dev/null | head -1)" = "1" ] || { echo "ABORT: AC not connected"; exit 1; }
W="$OUT/old_work"; mkdir -p "$W"; RAW="$OUT/old_parallel_raw.txt"; : > "$RAW"
for rep in $(seq $REPS); do
  for IMG in "$@"; do
    N=$(basename "$IMG" .txt)
    [ "$(wc -w < "$IMG")" = 262144 ] || { echo "skip $N (not 512x512 gray)"; continue; }
    cp "$IMG" "$W/img.txt"
    for np in $NPS; do
      out=$(cd "$W" && mpirun --bind-to core -np $np "$BIN" 2>&1)
      echo "$out" | grep -E "Time \(|Decode check" | sed "s/^/$N,$np,$rep,/" >> "$RAW"
    done
  done
done
python3 - "$RAW" <<'PY'
import sys, re, collections as C, statistics as S
d = C.defaultdict(list)
for line in open(sys.argv[1]):
    m = re.match(r"([^,]+),(\d+),(\d+),(.*)", line.strip())
    if not m: continue
    t = re.match(r"\s*Time \(([^)]*)\)\s*:\s*([0-9.]+)", m.group(4))
    if t: d[(m.group(1), int(m.group(2)), t.group(1).strip())].append(float(t.group(2)))
keys = sorted({k[2] for k in d}); nps = sorted({k[1] for k in d}); imgs = sorted({k[0] for k in d})
print("\nstages found:", keys)
print("\nMedian over repetitions, mean over images (milliseconds)")
print("P," + ",".join(keys))
for p in nps:
    row = []
    for k in keys:
        v = [S.median(d[(i, p, k)]) for i in imgs if d.get((i, p, k))]
        row.append(f"{1000*S.mean(v):.3f}" if v else "")
    print(f"{p}," + ",".join(row))
PY
