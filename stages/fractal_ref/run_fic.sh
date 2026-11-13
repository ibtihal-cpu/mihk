#!/bin/bash
# Run a reference fractal compressor on the same gray images used for the LBG programs.
# usage:  ./run_fic.sh ~/final8 [tol] [program]       program: fic_class (default, with block classification, follows the
#                                                     published pseudo-code) or fic (exhaustive search over all domains)
# Output: one line per run (image, rep, threads, tol, leaves, bytes, CR, PSNR, ET, DT, checksum).
# The checksum must be identical for all thread counts of the same image (deterministic search).
D=${1:-$HOME/final8}; TOL=${2:-10}; PROG=${3:-fic_class}
cd "$(dirname "$0")" || exit 1
gcc -O2 -fopenmp fic_quadtree_omp.c   -o fic       -lm || exit 1
gcc -O2 -fopenmp fic_quadtree_class.c -o fic_class -lm || exit 1
export OMP_PROC_BIND=close OMP_PLACES=cores
for img in lena_gray boat_gray cameraman_gray peppers_gray; do
  for T in 1 2 4 6 8 10 12 14; do
    for rep in 1 2 3 4 5; do
      echo -n "$img rep=$rep "; OMP_NUM_THREADS=$T ./$PROG "$D/$img.txt" "$TOL"
    done
  done
done
