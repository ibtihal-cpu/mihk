#!/bin/bash
# ONE complete measurement session for the thesis and the seminar (run once; nothing else needs to be re-run).
# Programs : codes_min.c (sequential) and codep_min.c (parallel), in the same folder as this script.
# Protocol : AC power, governor = performance, sequential pinned to one P-core, mpirun --bind-to core,
#            5 repetitions; the repetitions are the OUTER loop, so slow drifts of the machine are spread over all cases.
# Cases    : sequential; parallel with the Equal and the Adaptive distribution for every P in NPS.
# Output   : <OUTDIR>/raw.csv   every single run: image,mode,strategy,np,rep,LBG_s,Total_s,ok,md5
#            <OUTDIR>/logs/     full console output of the first sequential run of each image (CR, MSE, PSNR, SSIM, entropy)
#            <OUTDIR>/env.txt   machine, compiler, MPI, governor, md5 of the sources
# usage    : ./run_all_once.sh ~/final8/*.txt
NPS=${NPS:-"2 4 5 6 7 8 10 12 14"}; REPS=${REPS:-5}; SEQ_CPU=${SEQ_CPU:-6}; OUTDIR=${OUTDIR:-RUN1}
BIND=${BIND:-"--bind-to core"}; SRC_DIR=${SRC_DIR:-$(cd "$(dirname "$0")" && pwd)}
[ $# -gt 0 ] || { echo "usage: $0 image1.txt image2.txt ..."; exit 1; }
if [ -z "$SKIP_GUARD" ]; then
  [ "$(cat /sys/class/power_supply/AC*/online 2>/dev/null | head -1)" = "1" ] || { echo "ABORT: AC charger not connected"; exit 1; }
  [ "$(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u)" = "performance" ] || { echo "ABORT: governor is not performance on all CPUs"; exit 1; }
fi
taskset -c $SEQ_CPU true 2>/dev/null || { echo "ABORT: cannot pin to CPU $SEQ_CPU (set SEQ_CPU)"; exit 1; }
for IMG in "$@"; do [ -f "$IMG" ] || { echo "ABORT: $IMG not found"; exit 1; }; done

mkdir -p "$OUTDIR/logs" "$OUTDIR/work"; OUTDIR=$(cd "$OUTDIR" && pwd); WORK="$OUTDIR/work"
gcc   -O2 -Wall -o "$OUTDIR/lbg_seq" "$SRC_DIR/codes_min.c" -lm || exit 1
mpicc -O2 -Wall -o "$OUTDIR/lbg_par" "$SRC_DIR/codep_min.c" -lm || exit 1
{ echo "date      : $(date -Is)"; echo "cpu       : $(lscpu | awk -F: '/Model name/{gsub(/^ +/,"",$2); print $2}')"
  echo "kernel    : $(uname -sr)"; echo "gcc       : $(gcc --version | head -1)"; echo "mpi       : $(mpirun --version | head -1)"
  echo "governor  : $(cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null | sort -u | tr '\n' ' ')"
  echo "AC online : $(cat /sys/class/power_supply/AC*/online 2>/dev/null | head -1)"
  echo "NPS=$NPS REPS=$REPS SEQ_CPU=$SEQ_CPU BIND=$BIND"
  echo "md5       : $(cd "$SRC_DIR" && md5sum codes_min.c codep_min.c | awk '{print substr($1,1,8)" "$2}' | tr '\n' ' ')"
  for IMG in "$@"; do echo "image     : $(basename "$IMG") $(md5sum "$IMG" | cut -c1-8)"; done; } > "$OUTDIR/env.txt"
cat "$OUTDIR/env.txt"

RAW="$OUTDIR/raw.csv"; echo "image,mode,strategy,np,rep,LBG_s,Total_s,ok,md5" > "$RAW"
lbgt(){ awk -F': ' '/^LBG time/{print $2+0}'; }
tott(){ awk -F': ' '/^Total processing time/{print $2+0}'; }
mode_of(){ n=$(wc -w < "$1"); if [ "$n" = 262144 ]; then echo gray; elif [ "$n" = 786432 ]; then echo color; else echo unknown; fi; }
# record one run: image mode strategy np rep, console output in $out
record(){
  local ok=1; echo "$out" | grep -q "ERROR" && ok=0
  echo "$out" | grep -q "Container decode check: OK" || ok=0
  local h=$(md5sum "$WORK"/compressed*.bin 2>/dev/null | cut -c1-8 | tr '\n' '+' | sed 's/+$//')
  echo "$1,$2,$3,$4,$5,$(echo "$out" | lbgt),$(echo "$out" | tott),$ok,$h" | tee -a "$RAW"
}
for rep in $(seq $REPS); do
  for IMG in "$@"; do
    NAME=$(basename "$IMG" .txt); M=$(mode_of "$IMG")
    [ "$M" = unknown ] && { echo "$NAME: unknown size, skipped"; continue; }
    rm -f "$WORK"/compressed*.bin
    out=$(cd "$WORK" && taskset -c $SEQ_CPU "$OUTDIR/lbg_seq" "$IMG" --$M)
    [ "$rep" = 1 ] && echo "$out" > "$OUTDIR/logs/${NAME}_seq.txt"
    record "$NAME" $M seq 1 $rep
    for np in $NPS; do
      for st in equal adaptive; do
        rm -f "$WORK"/compressed*.bin
        out=$(cd "$WORK" && VQ_STRATEGY=$st mpirun $BIND -np $np "$OUTDIR/lbg_par" "$IMG" --$M)
        record "$NAME" $M $st $np $rep
      done
    done
  done
done
echo "DONE. Send me: $RAW  $OUTDIR/env.txt  and  $OUTDIR/logs/*"
