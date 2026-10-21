#!/bin/bash
# Peak resident memory (RSS) of the sequential program and of the MPI program (P = 4, 14).
#   ./lbg_seq = sem_v3.c      ./lbg_par = pam_v4.c      (build both in this folder, as for run_correctness.sh)
# Every process is wrapped by /usr/bin/time, so each MPI rank reports its OWN peak RSS (kB).
# Reported per run: max over ranks, and sum over ranks (total resident memory of the whole job).
# Needs GNU time:  sudo apt install time      Output: memory.csv  (median of REPS runs)
D=${D:-$HOME}; REPS=${REPS:-3}; OUT=${OUT:-memory.csv}
IMGS="${IMGS:-gray:$D/lbg_exp/gray.txt gray:$D/mammo2_img.txt color:$D/lena_color.txt color:$D/retina2_color.txt}"
[ -x /usr/bin/time ] || { echo "ABORT: /usr/bin/time missing (sudo apt install time)"; exit 1; }
for b in lbg_seq lbg_par; do [ -x ./$b ] || { echo "ABORT: ./$b missing"; exit 1; }; done
W=$(mktemp -d)
med(){ sort -g | awk '{a[NR]=$1} END{print a[int((NR+1)/2)]}'; }
echo "image,mode,P,peak_rss_max_rank_MB,peak_rss_sum_all_ranks_MB" | tee $OUT
for spec in $IMGS; do
  M=${spec%%:*}; IMG=${spec#*:}; NAME=$(basename "$IMG" .txt)
  [ -f "$IMG" ] || { echo "skip $IMG"; continue; }
  IMGABS=$(readlink -f "$IMG")
  for P in 1 4 14; do
    MX=(); SM=()
    for r in $(seq $REPS); do
      if [ $P = 1 ]; then
        o=$(cd $W && /usr/bin/time -f "MAXRSS %M" "$OLDPWD"/lbg_seq "$IMGABS" --$M 2>&1 >/dev/null)
      else
        o=$(cd $W && mpirun -np $P --bind-to core /usr/bin/time -f "MAXRSS %M" "$OLDPWD"/lbg_par "$IMGABS" --$M 2>&1 >/dev/null)
      fi
      v=$(echo "$o" | awk '/^MAXRSS/{print $2}')
      MX+=($(echo "$v" | sort -g | tail -1)); SM+=($(echo "$v" | awk '{s+=$1} END{print s}'))
    done
    mx=$(printf '%s\n' "${MX[@]}" | med); sm=$(printf '%s\n' "${SM[@]}" | med)
    echo "$NAME,$M,$P,$(awk -v x=$mx 'BEGIN{printf "%.1f", x/1024}'),$(awk -v x=$sm 'BEGIN{printf "%.1f", x/1024}')" | tee -a $OUT
  done
done
rm -rf $W
