#!/bin/bash
# Run the reference fractal compressor (fic_quadtree_omp.c) on the same gray images used for the LBG programs.
# usage:  ./run_fic.sh ~/final8 [tol]        (default tol = 10; try 6, 8, 10, 14 to reach CR near 20-30)
# Output: one line per run (image, threads, rep, tol, leaves, bytes, CR, PSNR, ET, DT, checksum).
# The checksum must be identical for all thread counts of the same image (deterministic search).
D=${1:-$HOME/final8}; TOL=${2:-10}
cd "$(dirname "$0")" && gcc -O2 -fopenmp fic_quadtree_omp.c -o fic -lm || exit 1
export OMP_PROC_BIND=close OMP_PLACES=cores
for img in lena_gray boat_gray cameraman_gray peppers_gray; do
  for T in 1 2 4 6 8 10 12 14; do
    for rep in 1 2 3 4 5; do
      echo -n "$img rep=$rep "; OMP_NUM_THREADS=$T ./fic "$D/$img.txt" "$TOL"
    done
  done
done
