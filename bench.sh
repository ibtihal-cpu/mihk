#!/usr/bin/env bash
# bench.sh -- performance table for the MPI LBG program (gray or color).
#
# usage:  ./bench.sh <binary> <image.txt> <--gray|--color> [reps=5] ["1 2 4 8"] [seq_lbg_seconds]
#
#   reps             runs per np; the MEDIAN is reported (robust against one noisy run)
#   seq_lbg_seconds  LBG time of the real SEQUENTIAL program (the "Time (LBG only)" line,
#                    or "Total LBG time" in color). If given, speedup is computed against it
#                    (correct definition). If omitted, np=1 of the parallel binary is the base.
#   MPIRUN_OPTS      extra mpirun flags, e.g.  MPIRUN_OPTS="--bind-to core"
#
# Each run happens in its own temp dir, so decompress.txt / *.bmp never overwrite each other.
# Full logs are kept in ./bench_logs/np<N>_run<R>.log

set -u
BIN=$(realpath "$1"); IMG=$(realpath "$2"); MODE=$3
REPS=${4:-5}; NPS=${5:-"1 2 4 8"}; SEQ=${6:-}
OPTS=${MPIRUN_OPTS:-}
LOGDIR=$(pwd)/bench_logs; mkdir -p "$LOGDIR"

median() { sort -g | awk '{a[NR]=$1} END{ if(NR==0){print "nan"} else if(NR%2) print a[(NR+1)/2]; else print (a[NR/2]+a[NR/2+1])/2 }'; }

# ---- metric extraction from one log (prints: lbg iters ssim total psnr cr) ----
extract() {
  local f=$1
  if [ "$MODE" = "--gray" ]; then
    lbg=$(grep -m1 "Time (LBG only)" "$f" | awk '{print $4}')
    it=$(grep -m1 "LBG total iterations" "$f" | awk '{print $4}')
    ss=$(grep -m1 "SSIM (parallel)" "$f" | sed 's/.*time = *\([0-9.]*\) s.*/\1/')
    psnr=$(grep -m1 "^PSNR" "$f" | awk '{print $3}')
    cr=$(grep -m1 "System total" "$f" | awk '{print $4}')
  else
    lbg=$(grep -m1 "Total LBG time" "$f" | awk '{print $(NF-1)}')
    it=$(grep "LBG iters=" "$f" | sed 's/.*LBG iters=\([0-9]*\).*/\1/' | awk '{s+=$1} END{print s}')
    ss=$(grep "SSIM time=" "$f" | sed 's/.*SSIM time=\([0-9.]*\)s.*/\1/' | awk '{s+=$1} END{print s}')
    psnr=$(grep -m1 "^RGB PSNR" "$f" | awk '{print $4}')
    cr=$(grep -m1 "^RGB CR" "$f" | awk '{print $5}')
  fi
  tot=$(grep -m1 "Total execution time" "$f" | awk '{print $4}')
  echo "$lbg $it $ss $tot $psnr $cr"
}

declare -A LBG SSIM TOT IT PSNR CR
for np in $NPS; do
  lbgs=""; sss=""; tots=""
  for r in $(seq 1 "$REPS"); do
    tmp=$(mktemp -d); log="$LOGDIR/np${np}_run${r}.log"
    ( cd "$tmp" && mpirun -np "$np" --allow-run-as-root $OPTS "$BIN" "$IMG" "$MODE" ) > "$log" 2>&1
    rm -rf "$tmp"
    read -r l i s t p c <<<"$(extract "$log")"
    if [ -z "$l" ] || [ -z "$t" ]; then echo "np=$np run=$r: FAILED (see $log)"; continue; fi
    lbgs+="$l"$'\n'; sss+="$s"$'\n'; tots+="$t"$'\n'
    IT[$np,$r]=$i; PSNR[$np,$r]=$p; CR[$np,$r]=$c
  done
  LBG[$np]=$(printf "%s" "$lbgs" | median); SSIM[$np]=$(printf "%s" "$sss" | median); TOT[$np]=$(printf "%s" "$tots" | median)
done

# ---- consistency check: iterations / PSNR / CR must be identical for every np and run ----
ref_i=""; ref_p=""; ref_c=""; ok=1
for k in "${!IT[@]}"; do
  [ -z "$ref_i" ] && { ref_i=${IT[$k]}; ref_p=${PSNR[$k]}; ref_c=${CR[$k]}; }
  [ "${IT[$k]}" != "$ref_i" ] || [ "${PSNR[$k]}" != "$ref_p" ] || [ "${CR[$k]}" != "$ref_c" ] && ok=0
done

first=$(echo $NPS | awk '{print $1}')
if [ -n "$SEQ" ]; then BASE=$SEQ; BASEDESC="sequential program (${SEQ}s)"; else BASE=${LBG[$first]}; BASEDESC="parallel binary at np=$first"; fi

echo
echo "image=$IMG mode=$MODE reps=$REPS (median)   speedup base: $BASEDESC"
printf "%4s | %9s | %8s | %10s | %9s | %9s | %9s\n" np "LBG(s)" speedup "efficiency" "SSIM(s)" "total(s)" iters
for np in $NPS; do
  awk -v np="$np" -v l="${LBG[$np]}" -v b="$BASE" -v s="${SSIM[$np]}" -v t="${TOT[$np]}" -v i="${IT[$np,1]:-?}" \
      'BEGIN{ sp=(l>0)? b/l : 0; printf "%4d | %9.4f | %8.2f | %9.1f%% | %9.4f | %9.3f | %9s\n", np,l,sp,100*sp/np,s,t,i }'
done
echo
if [ $ok -eq 1 ]; then echo "CONSISTENCY: OK  (iterations=$ref_i  PSNR=$ref_p  CR=$ref_c identical for all np/runs)"
else echo "CONSISTENCY: MISMATCH -- iterations/PSNR/CR differ between runs; results are NOT comparable, check bench_logs/"; fi
