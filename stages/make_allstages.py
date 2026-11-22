#!/usr/bin/env python3
"""Generate codes_allstages.c / codep_allstages.c from codes_min.c / codep_min.c.
They add timers only (same compressed output) and print one line  "ALLSTAGES name=value ..."  (seconds) with EVERY
stage that is part of the Total processing time, so that Total = sum of the printed stages (grayscale path).
usage: python3 stages/make_allstages.py   (run from the repository root)"""
import sys
def patch(src, dst, edits):
    s = open(src).read()
    for old, new in edits:
        if s.count(old) != 1: sys.exit(f"{src}: anchor found {s.count(old)} times (need 1):\n{old}")
        s = s.replace(old, new)
    open(dst, "w").write(s); print("wrote", dst); return s

# ---------------- sequential (grayscale path already has all timers) ----------------
patch("codes_min.c", "stages/codes_allstages.c", [
 ('    printf("LBG iterations: %d\\n", lbg_iters);\n    printf("LBG time: %.4f s\\n", tt_lbg);\n',
  '    printf("ALLSTAGES build=%.6f prep=%.6f dist=0 scatter=0 mean=0 lbg=%.6f gather=0 cvt8=%.6f delta=%.6f huff=%.6f dec=%.6f total=%.6f\\n",\n'
  '           tt_build, tt_f32, tt_lbg, tt_cvt, tt_delta, tt_huff, tt_rec, tt_proc);\n'
  '    printf("LBG iterations: %d\\n", lbg_iters);\n    printf("LBG time: %.4f s\\n", tt_lbg);\n')])

# ---------------- parallel (grayscale path) ----------------
G = ("static double g_build = 0, g_dist = 0, g_scatter = 0, g_mean = 0, g_prep = 0, g_lbg = 0, g_gather = 0, g_cvt8 = 0,\n"
     "              g_delta = 0, g_huff = 0, g_dec = 0;   /* stage timers (process 0) */\n")
patch("codep_min.c", "stages/codep_allstages.c", [
 ("#include <mpi.h>\n", "#include <mpi.h>\n" + G),
 ("        t_proc += MPI_Wtime() - tpa;\n        printf(\"Built %d training vectors",
  "        t_proc += MPI_Wtime() - tpa;\n        g_build = MPI_Wtime() - tpa;\n        printf(\"Built %d training vectors"),
 ("    MPI_Bcast(&num_vectors, 1, MPI_INT, 0, MPI_COMM_WORLD);\n\n    int *vec_counts  = (int *)calloc(size, sizeof(int));",
  "    MPI_Bcast(&num_vectors, 1, MPI_INT, 0, MPI_COMM_WORLD);\n\n    int *vec_counts  = (int *)calloc(size, sizeof(int));"),
 ("    int local_n = vec_counts[rank];\n\n    uint8_t *local_v = (uint8_t *)malloc((size_t)local_n * vlen);\n    MPI_Scatterv(training_set, byte_counts, byte_displs, MPI_UINT8_T,\n                 local_v,      local_n * vlen,           MPI_UINT8_T,\n                 0, MPI_COMM_WORLD);\n",
  "    int local_n = vec_counts[rank];\n    double _t_dist = MPI_Wtime();\n\n    uint8_t *local_v = (uint8_t *)malloc((size_t)local_n * vlen);\n    MPI_Scatterv(training_set, byte_counts, byte_displs, MPI_UINT8_T,\n                 local_v,      local_n * vlen,           MPI_UINT8_T,\n                 0, MPI_COMM_WORLD);\n    double _t_scat = MPI_Wtime();\n"),
 ("        free(local_mean);\n    }\n\n    float *local_vf = (float *)malloc((size_t)local_n * vlen * sizeof(float));\n    for (int i = 0; i < local_n * vlen; i++)\n        local_vf[i] = (float)local_v[i];\n",
  "        free(local_mean);\n    }\n    double _t_mean = MPI_Wtime();\n\n    float *local_vf = (float *)malloc((size_t)local_n * vlen * sizeof(float));\n    for (int i = 0; i < local_n * vlen; i++)\n        local_vf[i] = (float)local_v[i];\n"),
 ("    double time_lbg = t1 - t0;\n\n    MPI_Gatherv(local_labels, local_n,                MPI_UINT8_T,\n                labels,       vec_counts, vec_displs, MPI_UINT8_T,\n                0, MPI_COMM_WORLD);\n    t_proc += MPI_Wtime() - tpb0;\n",
  "    double time_lbg = t1 - t0;\n    g_lbg = time_lbg;\n\n    MPI_Gatherv(local_labels, local_n,                MPI_UINT8_T,\n                labels,       vec_counts, vec_displs, MPI_UINT8_T,\n                0, MPI_COMM_WORLD);\n    {   double _t_end = MPI_Wtime();\n        g_gather = _t_end - t1;\n        g_dist = _t_dist - tpb0; g_scatter = _t_scat - _t_dist; g_mean = _t_mean - _t_scat;\n        g_prep = t0 - _t_mean;   /* float conversion, allocations and the barrier before the LBG timer */\n    }\n    t_proc += MPI_Wtime() - tpb0;\n"),
 ("        t_proc += MPI_Wtime() - tpc_c;\n", "        t_proc += MPI_Wtime() - tpc_c;\n        g_cvt8 = MPI_Wtime() - tpc_c;\n"),
 ("        t_proc += MPI_Wtime() - tpd0;\n", "        t_proc += MPI_Wtime() - tpd0;\n        g_delta += MPI_Wtime() - tpd0;\n"),
 ("        t_proc += time_huff;\n", "        t_proc += time_huff;\n        g_huff += time_huff;\n"),
 ("        int dec_rc = container_decode(container, container_bytes, reconstructed, K, vlen, BLOCK_SIZE, WIDTH, HEIGHT, NULL);\n        t_proc += MPI_Wtime() - tpr0;\n",
  "        int dec_rc = container_decode(container, container_bytes, reconstructed, K, vlen, BLOCK_SIZE, WIDTH, HEIGHT, NULL);\n        t_proc += MPI_Wtime() - tpr0;\n        g_dec += MPI_Wtime() - tpr0;\n"),
])
p = open("stages/codep_allstages.c").read()
old = '        printf("Total processing time: %.4f s\\n", t_proc);\n'
assert p.count(old) == 2, p.count(old)
new = ('        printf("ALLSTAGES build=%.6f prep=%.6f dist=%.6f scatter=%.6f mean=%.6f lbg=%.6f gather=%.6f cvt8=%.6f delta=%.6f huff=%.6f dec=%.6f total=%.6f\\n",\n'
       '               g_build, g_prep, g_dist, g_scatter, g_mean, g_lbg, g_gather, g_cvt8, g_delta, g_huff, g_dec, t_proc);\n') + old
open("stages/codep_allstages.c", "w").write(p.replace(old, new)); print("patched final print (2 places; the colour path leaves most values 0)")
