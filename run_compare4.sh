#!/bin/bash
# Build and run ALL FOUR programs under the performance protocol and compare them:
#   code2 (sequential) / code1 (parallel)  = estimated Huffman-table size
#   code4 (sequential) / code3 (parallel)  = REAL compressed container (canonical Huffman)
# Protocol: AC power, governor=performance, sequential pinned to one P-core, mpirun --bind-to core,
#           median of REPS (default 5), the two programs of a pair alternate inside every repetition.
# usage:   NPS="2 4 8 14" ./run_compare4.sh img1.txt img2.txt ...     (run it in the folder that holds code1.c .. code4.c)
# output:  compare4.csv (medians) and a readable table on screen.
NPS=${NPS:-"2 4 6 8 10 12 14"}; REPS=${REPS:-5}; SEQ_CPU=${SEQ_CPU:-6}; OUT=${OUT:-compare4.csv}; SRC=${SRC_DIR:-$(cd "$(dirname "$0")" && pwd)}
med(){ sort -g | awk '{a[NR]=$1} END{print a[int((NR+1)/2)]}'; }
if [ -z "$SKIP_GUARD" ]; then
  [ "$(cat /sys/class/power_supply/AC*/online 2>/dev/null | head -1)" = "1" ] || { echo "ABORT: AC charger not connected"; exit 1; }
  [ "$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u)" = "performance" ] || { echo "ABORT: governor is not 'performance' on all CPUs"; exit 1; }
fi
taskset -c $SEQ_CPU true 2>/dev/null || { echo "ABORT: cannot pin to CPU $SEQ_CPU (set SEQ_CPU=<a P-core number>)"; exit 1; }
for f in code1.c code2.c code3.c code4.c; do [ -f "$SRC/$f" ] || { echo "ABORT: $SRC/$f missing"; exit 1; }; done
B=$(mktemp -d); CF=${CFLAGS:--O2}
gcc   $CF -o $B/code2 "$SRC/code2.c" -lm || exit 1
gcc   $CF -o $B/code4 "$SRC/code4.c" -lm || exit 1
mpicc $CF -o $B/code1 "$SRC/code1.c" -lm || exit 1
mpicc $CF -o $B/code3 "$SRC/code3.c" -lm || exit 1
echo "md5 : $(cd "$SRC" && md5sum code1.c code2.c code3.c code4.c | awk '{print substr($1,1,8)" "$2}' | tr '\n' ' ')"
IMGS=(); for f in "$@"; do [ -f "$f" ] || { echo "ABORT: $f not found"; exit 1; }; IMGS+=("$(readlink -f "$f")"); done

# parse one program output ->  "LBG COMPLETE PROC CR PSNR SSIM"
getm(){ awk -v mode="$1" -v kind="$2" '
    function num(s){ sub(/^[^:=]*[:=][ ]*/,"",s); sub(/ *(s|seconds)$/,"",s); return s+0 }
    mode=="gray" && kind=="seq" && /LBG \(wall/ {l=$6}
    mode=="gray" && kind=="par" && /Time \(LBG only\)/ {l=$4}
    mode=="color" && /Total LBG time/ {l=$6}
    /Total \(measured|Total program time|Total execution time/ {c=num($0)}
    /Total processing time/ {p=num($0)}
    mode=="gray" && /System total \(LBG\+Huff\)/ {cr=$4}
    mode=="color" && /RGB CR \(system\)/ {cr=$5}
    mode=="gray" && /^PSNR =/ {ps=$3}
    mode=="color" && /RGB PSNR/ {ps=$4}
    mode=="gray" && kind=="seq" && /^SSIM =/ {ss=$3}
    mode=="gray" && kind=="par" && /SSIM \(parallel\)/ {ss=$4}
    mode=="color" && /Mean Channel-wise SSIM/ {ss=$5}
    END{printf "%s %s %s %s %s %s\n", l, c, p, cr, ps, ss}'; }

declare -A RL RC RP QCR QPS QSS QDC QRT QMD
run_one(){  # $1=code $2=seq|par $3=np   (uses $IMG, $M)
  local d=$B/run_$1_$3; mkdir -p $d
  ( cd $d && rm -f ./* ; if [ $2 = seq ]; then taskset -c $SEQ_CPU $B/$1 "$IMG" --$M > out.txt 2>&1
    else mpirun -np $3 --allow-run-as-root --bind-to core $B/$1 "$IMG" --$M > out.txt 2>&1; fi )
  local out; out=$(cat $d/out.txt)
  read l c p cr ps ss <<< "$(echo "$out" | getm $M $2)"
  RL[$1]+="$l "; RC[$1]+="$c "; RP[$1]+="$p "; QCR[$1]=$cr; QPS[$1]=$ps; QSS[$1]=$ss
  QDC[$1]=$(echo "$out" | grep -c "Container decode check: OK"); QRT[$1]=$(echo "$out" | grep -c "File round-trip check.*: OK")
  local f=decompress.txt; [ $M = color ] && f=compressed_color.bmp
  QMD[$1]=$( [ -f $d/$f ] && md5sum < $d/$f | cut -c1-8 || echo none )
}
run_pair(){  # $1=codeA $2=codeB $3=kind $4=np  -> medians into MLBG/MCOMP/MPROC arrays
  RL=(); RC=(); RP=(); QCR=(); QPS=(); QSS=(); QDC=(); QRT=(); QMD=()
  for r in $(seq $REPS); do
    if [ $((r%2)) -eq 1 ]; then run_one $1 $3 $4; run_one $2 $3 $4; else run_one $2 $3 $4; run_one $1 $3 $4; fi
  done
  for c in $1 $2; do
    MLBG[$c]=$(printf '%s\n' ${RL[$c]} | med); MCOMP[$c]=$(printf '%s\n' ${RC[$c]} | med); MPROC[$c]=$(printf '%s\n' ${RP[$c]} | med)
    local chk="-"; case $c in code3|code4) chk="decode_ok=${QDC[$c]} roundtrip_ok=${QRT[$c]}";; esac
    echo "$NAME,$M,$c,$4,${MLBG[$c]},${MCOMP[$c]},${MPROC[$c]},${QCR[$c]},${QPS[$c]},${QSS[$c]},${QDC[$c]},${QRT[$c]},${QMD[$c]}" >> $OUT
    printf "$FMT" $NAME $M $c $4 ${MLBG[$c]} ${MCOMP[$c]} ${MPROC[$c]} ${QCR[$c]} ${QPS[$c]} ${QSS[$c]} "$chk md5=${QMD[$c]}"
  done
}
declare -A MLBG MCOMP MPROC
echo "image,mode,code,np,LBG_s,Complete_s,Proc_s,CR,PSNR,SSIM,decode_ok,roundtrip_ok,recon_md5" > $OUT
FMT='%-15s %-5s %-6s %3s %8s %10s %9s %7s %7s %7s  %s\n'
printf "$FMT" image mode code np LBG_s Complete_s Proc_s CR PSNR SSIM checks
for IMG in "${IMGS[@]}"; do
  n=$(wc -w < "$IMG"); NAME=$(basename "$IMG" .txt)
  if [ "$n" = 262144 ]; then M=gray; elif [ "$n" = 786432 ]; then M=color; else echo "$NAME skipped (size $n)"; continue; fi
  run_pair code2 code4 seq 0
  S2L=${MLBG[code2]}; S2P=${MPROC[code2]}; S2C=${MCOMP[code2]}; S4L=${MLBG[code4]}; S4P=${MPROC[code4]}; S4C=${MCOMP[code4]}
  for np in $NPS; do
    run_pair code1 code3 par $np
    awk -v np=$np -v s2l=$S2L -v s2p=$S2P -v s2c=$S2C -v s4l=$S4L -v s4p=$S4P -v s4c=$S4C \
        -v l1=${MLBG[code1]} -v p1=${MPROC[code1]} -v c1=${MCOMP[code1]} -v l3=${MLBG[code3]} -v p3=${MPROC[code3]} -v c3=${MCOMP[code3]} \
      'BEGIN{printf "      speedup P=%s | code1/code2: LBG %.2f Proc %.2f Complete %.2f | code3/code4: LBG %.2f Proc %.2f Complete %.2f | Proc(code3)/Proc(code1)=%.3f\n", np, s2l/l1, s2p/p1, s2c/c1, s4l/l3, s4p/p3, s4c/c3, p3/p1}'
  done
done
rm -rf $B
echo "CSV: $OUT"
