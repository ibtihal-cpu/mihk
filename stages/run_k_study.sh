#!/bin/bash
# Effect of the codebook size K (32, 64, 128) with 4x4 blocks on the grayscale images, measured with the FINAL
# program (real container size) in ONE session.  The only change to the program is the value of CODEBOOK_SIZE,
# applied to a temporary copy of codes_min.c.
# usage (repository root):  ./stages/run_k_study.sh ~/final8/lena_gray.txt ~/final8/boat_gray.txt ~/final8/cameraman_gray.txt ~/final8/peppers_gray.txt
KS=${KS:-"32 64 128"}; REPS=${REPS:-5}; SEQ_CPU=${SEQ_CPU:-6}; OUT=${OUT:-kstudy_RUN}
[ $# -gt 0 ] || { echo "usage: $0 image1.txt ..."; exit 1; }
if [ -z "$SKIP_GUARD" ]; then
  [ "$(cat /sys/class/power_supply/AC*/online 2>/dev/null | head -1)" = "1" ] || { echo "ABORT: AC not connected"; exit 1; }
  [ "$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u)" = "performance" ] || { echo "ABORT: governor"; exit 1; }
fi
mkdir -p "$OUT/work"; OUT=$(cd "$OUT" && pwd); SRC=$(cd "$(dirname "$0")/.." && pwd)/codes_min.c
CSV="$OUT/kstudy_raw.csv"; echo "K,image,rep,CR,PSNR,SSIM,iters,LBG_s" > "$CSV"
for K in $KS; do
  sed "s/^#define CODEBOOK_SIZE 64/#define CODEBOOK_SIZE $K/" "$SRC" > "$OUT/codes_K$K.c"
  grep -q "^#define CODEBOOK_SIZE $K" "$OUT/codes_K$K.c" || { echo "ABORT: K patch failed"; exit 1; }
  gcc -O2 -Wall -o "$OUT/seq_K$K" "$OUT/codes_K$K.c" -lm || exit 1
done
for rep in $(seq $REPS); do
  for IMG in "$@"; do
    N=$(basename "$IMG" .txt)
    for K in $KS; do
      out=$(cd "$OUT/work" && taskset -c $SEQ_CPU "$OUT/seq_K$K" "$IMG" --gray)
      cr=$(echo "$out" | awk '/System total/{print $4}'); ps=$(echo "$out" | awk '/^PSNR/{print $3}'); ss=$(echo "$out" | awk '/^SSIM/{print $3}')
      it=$(echo "$out" | awk -F': ' '/LBG iterations/{print $2}'); lt=$(echo "$out" | awk -F': ' '/^LBG time/{print $2+0}')
      echo "$K,$N,$rep,$cr,$ps,$ss,$it,$lt" | tee -a "$CSV"
    done
  done
done
python3 - "$CSV" <<'PY'
import csv, sys, statistics as S, collections as C
d = C.defaultdict(list)
for r in csv.DictReader(open(sys.argv[1])): d[(int(r['K']), r['image'])].append(r)
print("\nPer-image values (LBG time = median of the repetitions), then the mean over the images")
print("K,PSNR_dB,SSIM,CR,LBG_iterations,LBG_time_s")
for K in sorted({k[0] for k in d}):
    rows = []
    for (k, img), v in d.items():
        if k != K: continue
        rows.append((float(v[0]['PSNR']), float(v[0]['SSIM']), float(v[0]['CR']), float(v[0]['iters']), S.median(float(x['LBG_s']) for x in v)))
    m = lambda i: sum(r[i] for r in rows) / len(rows)
    print(f"{K},{m(0):.2f},{m(1):.4f},{m(2):.2f},{m(3):.1f},{m(4):.4f}")
PY
