#!/bin/bash
# Regression guard for the LBG code. Run it after ANY change, before trusting any new timing.
#   ./regress.sh gray.txt --record      # once: store the reference (sequential) results
#   ./regress.sh gray.txt               # later: compare sequential (exact) and parallel (tolerance)
# Needs ./lbg_seq and ./lbg_par. NPS="2 4" selects the process counts to check.
IMG=${1:-gray.txt}; MODE=$2; NPS=${NPS:-"2 4"}; G="golden_$(basename "$IMG" .txt).txt"
ext(){ echo "$1" | awk '
  /^MSE +=/  {m=$3}
  /^PSNR +=/ {p=$3}
  /^SSIM/    {for(i=1;i<=NF;i++) if($i=="=") {s=$(i+1); break}}
  /System total/ {c=$4}
  /LBG total iterations/ {n=$NF}
  END{print m, p, s, c, n}'; }

S=$(ext "$(./lbg_seq "$IMG" --gray)")
if [ "$MODE" = "--record" ]; then echo "$S" > "$G"; echo "recorded $G: MSE PSNR SSIM CR iters = $S"; exit 0; fi
[ -f "$G" ] || { echo "no $G: run with --record first"; exit 1; }
R=$(cat "$G"); fail=0
if [ "$S" = "$R" ]; then echo "PASS  sequential  exact match   ($S)"; else echo "FAIL  sequential  got [$S]  expected [$R]"; fail=1; fi
for np in $NPS; do
  P=$(ext "$(mpirun -np $np --allow-run-as-root --bind-to core ./lbg_par "$IMG" --gray)")
  ok=$(awk -v a="$P" -v b="$R" 'BEGIN{split(a,x," ");split(b,y," ");
     d=(x[2]>y[2])?x[2]-y[2]:y[2]-x[2]; e=(x[3]>y[3])?x[3]-y[3]:y[3]-x[3];
     print (d<=0.02 && e<=0.001 && x[4]==y[4]) ? "ok":"bad"}')
  it=$(echo "$P" | awk '{print $5}'); itr=$(echo "$R" | awk '{print $5}')
  if [ "$ok" = ok ]; then echo "PASS  np=$np  quality within tolerance ($P)  iters par=$it seq=$itr"
  else echo "FAIL  np=$np  got [$P]  expected [$R]"; fail=1; fi
done
[ $fail = 0 ] && echo "ALL CHECKS PASSED" || { echo "REGRESSION DETECTED"; exit 1; }
