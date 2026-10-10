#!/bin/bash
# FINAL campaign: 4 standard grayscale + 4 standard color images, programs WITHOUT the bilateral filter.
# Runs every measurement the thesis tables need, in order, from ONE build:
#   build        lbg_seq (sem_v3_nofilter.c) and lbg_par (pam_v4_nofilter.c)
#   correctness  seq vs parallel (P=4, 14, 14 forced Equal): CR, MSE, PSNR, SSIM, iterations, MD5  -> correctness.csv
#   timing       LBG + total time, speedup, efficiency, P = 2..14 (median of 5, seq pinned)        -> timing_final.csv
#   eqad         Equal vs Adaptive, LBG and total time (alternated, median of 5)                    -> eq_ad_total.csv
#   entropy      index entropy before/after delta + Huffman rate (gray)                             -> entropy.csv
#   param        block size / codebook size study (gray)                                           -> param_study_nf.csv
#   baselines    rate-matched JPEG / JPEG 2000 reference (gray), proposed values from correctness   -> baselines.csv
#   memory       peak RSS of seq and parallel (P=4, 14)                                            -> memory.csv
#
# usage (run from the working folder, e.g. ~/v4f; AC connected, governor = performance):
#   COLOR_IMGS="$HOME/lena_color.txt $HOME/<c2>.txt $HOME/<c3>.txt $HOME/<c4>.txt" ./run_final_campaign.sh
# optional:  SRC_DIR=~/mihk_ok   STEPS="build correctness timing eqad entropy param baselines memory"
# Each step logs to <step>.log. Compiler flags: -O2 (edit CFLAGS below if the thesis uses different flags).
SRC_DIR=${SRC_DIR:-$HOME/mihk_ok}; CFLAGS=${CFLAGS:--O2}
STEPS=${STEPS:-"build correctness timing eqad entropy param baselines memory"}
GRAY_IMGS=${GRAY_IMGS:-"$HOME/lbg_exp/gray.txt $HOME/boat_img.txt $HOME/cameraman_img.txt $HOME/peppers_img.txt"}
COLOR_IMGS=${COLOR_IMGS:-}
ALL_IMGS="$GRAY_IMGS $COLOR_IMGS"
NPS=${NPS:-"2 4 6 8 10 12 14"}

# ---- input checks ----
set -- $GRAY_IMGS; [ $# = 4 ] || { echo "ABORT: GRAY_IMGS must list exactly 4 files"; exit 1; }
set -- $COLOR_IMGS; [ $# = 4 ] || { echo "ABORT: set COLOR_IMGS to exactly 4 color image files (see ls ~/*color*.txt)"; exit 1; }
for f in $GRAY_IMGS; do [ "$(wc -w < "$f" 2>/dev/null)" = 262144 ] || { echo "ABORT: $f missing or not a 512x512 grayscale file"; exit 1; }; done
for f in $COLOR_IMGS; do [ "$(wc -w < "$f" 2>/dev/null)" = 786432 ] || { echo "ABORT: $f missing or not a 512x512 color file"; exit 1; }; done
for s in sem_v3_nofilter.c pam_v4_nofilter.c run_correctness_nofilter.sh run_all.sh run_eq_ad_total.sh run_entropy.sh run_param_study.sh run_baselines.py run_memory.sh; do
  [ -f "$SRC_DIR/$s" ] || { echo "ABORT: $SRC_DIR/$s not found (git pull first)"; exit 1; }
done
echo "gray : $GRAY_IMGS"; echo "color: $COLOR_IMGS"
echo "md5 : $(md5sum $SRC_DIR/sem_v3_nofilter.c $SRC_DIR/pam_v4_nofilter.c | tr '\n' ' ')"

want(){ case " $STEPS " in *" $1 "*) return 0;; *) return 1;; esac; }
run(){ # $1 = step name, rest = command ; output also saved to $1.log
  local n=$1; shift; echo "=== [$n] $(date +%T)"; "$@" 2>&1 | tee $n.log; echo "=== [$n] done $(date +%T)"; }

if want build; then
  gcc $CFLAGS -o lbg_seq "$SRC_DIR/sem_v3_nofilter.c" -lm || exit 1
  mpicc $CFLAGS -o lbg_par "$SRC_DIR/pam_v4_nofilter.c" -lm || exit 1
  echo "built with: $CFLAGS"
fi
[ -x ./lbg_seq ] && [ -x ./lbg_par ] || { echo "ABORT: ./lbg_seq ./lbg_par missing (run the build step)"; exit 1; }

want correctness && IMGS="$ALL_IMGS" OUT=correctness.csv run correctness "$SRC_DIR/run_correctness_nofilter.sh"
want timing      && NPS="$NPS" OUT=timing_final.csv run timing "$SRC_DIR/run_all.sh" $ALL_IMGS
want eqad        && IMGS="$ALL_IMGS" NPS="$NPS" OUT=eq_ad_total.csv RAW=eq_ad_total_raw.csv run eqad "$SRC_DIR/run_eq_ad_total.sh"
want entropy     && IMGS="$GRAY_IMGS" OUT=entropy.csv run entropy "$SRC_DIR/run_entropy.sh"
want param       && SRC="$SRC_DIR/sem_v3_nofilter.c" IMGS="$GRAY_IMGS" OUT=param_study_nf.csv run param "$SRC_DIR/run_param_study.sh"
if want baselines; then
  echo "=== [baselines] $(date +%T)"; python3 "$SRC_DIR/run_baselines.py" correctness.csv $GRAY_IMGS | tee baselines.csv
fi
if want memory; then
  set -- $GRAY_IMGS; G1=$1; G2=$2; set -- $COLOR_IMGS; C1=$1; C2=$2
  IMGS="gray:$G1 gray:$G2 color:$C1 color:$C2" OUT=memory.csv run memory "$SRC_DIR/run_memory.sh"
fi
echo "ALL DONE. Send these files: correctness.csv timing_final.csv eq_ad_total.csv entropy.csv param_study_nf.csv baselines.csv memory.csv"
