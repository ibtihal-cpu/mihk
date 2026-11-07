#!/usr/bin/env python3
"""Generate codes_stages.c / codep_stages.c from codes_min.c / codep_min.c.
Only adds extra timers and one extra output line "STAGES ..." (seconds).  Nothing else changes, so the
compressed output is identical.  Each anchor must occur exactly once or the script aborts.
usage: python3 stages/make_stages.py   (run from the repo root)"""
import sys

def patch(src, dst, edits):
    s = open(src).read()
    for old, new in edits:
        if s.count(old) != 1:
            sys.exit(f"{src}: anchor found {s.count(old)} times (need 1):\n{old}")
        s = s.replace(old, new)
    open(dst, "w").write(s)
    print("wrote", dst)

# ---------------- sequential ----------------
G = "static double g_t_delta = 0.0, g_t_huff = 0.0, g_t_dec = 0.0;   /* stage timers (colour path) */\n"
seq = [
 ("#define SEC(a,b)", G + "#define SEC(a,b)"),
 # grayscale: timers already exist, just print them
 ('    printf("LBG iterations: %d\\n", lbg_iters);\n    printf("LBG time: %.4f s\\n", tt_lbg);\n',
  '    printf("STAGES delta=%.6f huffman=%.6f decode=%.6f build=%.6f lbg=%.6f\\n", tt_delta, tt_huff, tt_rec, tt_build, tt_lbg);\n'
  '    printf("LBG iterations: %d\\n", lbg_iters);\n    printf("LBG time: %.4f s\\n", tt_lbg);\n'),
 # colour: accumulate per channel
 ("    res.proc_time += wtime() - tp_d;\n", "    res.proc_time += wtime() - tp_d;\n    g_t_delta += wtime() - tp_d;\n"),
 ("    res.proc_time += wtime() - tp_h;\n", "    res.proc_time += wtime() - tp_h;\n    g_t_huff += wtime() - tp_h;\n"),
 ("    res.proc_time += wtime() - tp_r;\n", "    res.proc_time += wtime() - tp_r;\n    g_t_dec += wtime() - tp_r;\n"),
 ('    printf("LBG time: %.4f s\\n", total_lbg_time);\n    printf("Total processing time: %.4f s\\n", res_r.proc_time',
  '    printf("STAGES delta=%.6f huffman=%.6f decode=%.6f\\n", g_t_delta, g_t_huff, g_t_dec);\n'
  '    printf("LBG time: %.4f s\\n", total_lbg_time);\n    printf("Total processing time: %.4f s\\n", res_r.proc_time'),
]
patch("codes_min.c", "stages/codes_stages.c", seq)

# ---------------- parallel ----------------
par = [
 ("#define SEC(a,b)" if False else "#include <mpi.h>\n",
  "#include <mpi.h>\nstatic double g_t_delta = 0.0, g_t_huff = 0.0, g_t_dec = 0.0;   /* stage timers (process 0) */\n"),
 # grayscale
 ("        t_proc += MPI_Wtime() - tpd0;\n", "        t_proc += MPI_Wtime() - tpd0;\n        g_t_delta += MPI_Wtime() - tpd0;\n"),
 ("        t_proc += time_huff;\n", "        t_proc += time_huff;\n        g_t_huff += time_huff;\n"),
 ("        int dec_rc = container_decode(container, container_bytes, reconstructed, K, vlen, BLOCK_SIZE, WIDTH, HEIGHT, NULL);\n        t_proc += MPI_Wtime() - tpr0;\n",
  "        int dec_rc = container_decode(container, container_bytes, reconstructed, K, vlen, BLOCK_SIZE, WIDTH, HEIGHT, NULL);\n        t_proc += MPI_Wtime() - tpr0;\n        g_t_dec += MPI_Wtime() - tpr0;\n"),
 # colour: split the single tpr0 block into delta / huffman(+8-bit codebook) / decode
 ("            uint8_t *cb_u8 = (uint8_t *)malloc((size_t)K * vlen);\n",
  "            g_t_delta += MPI_Wtime() - tpr0;\n            double _th0 = MPI_Wtime();\n            uint8_t *cb_u8 = (uint8_t *)malloc((size_t)K * vlen);\n"),
 ("            (void)huff_data_bytes; (void)header_bytes;\n            results[ch].compressed_bytes",
  "            (void)huff_data_bytes; (void)header_bytes;\n            g_t_huff += MPI_Wtime() - _th0;\n            results[ch].compressed_bytes"),
 ("            reconstructed = (uint8_t*)malloc(channel_bytes);\n            int dec_rc = container_decode(results[ch].container",
  "            double _tdc0 = MPI_Wtime();\n            reconstructed = (uint8_t*)malloc(channel_bytes);\n            int dec_rc = container_decode(results[ch].container"),
 ("                                          BLOCK_SIZE, WIDTH, HEIGHT, NULL);\n            t_proc += MPI_Wtime() - tpr0;\n",
  "                                          BLOCK_SIZE, WIDTH, HEIGHT, NULL);\n            g_t_dec += MPI_Wtime() - _tdc0;\n            t_proc += MPI_Wtime() - tpr0;\n"),
 # print (both paths end with the same block; there are two identical occurrences -> handled below)
]
patch("codep_min.c", "stages/codep_stages.c", par)
# the final print block occurs twice (gray and colour); patch both
p = open("stages/codep_stages.c").read()
old = '        printf("Total processing time: %.4f s\\n", t_proc);\n'
assert p.count(old) == 2, p.count(old)
p = p.replace(old, '        printf("STAGES delta=%.6f huffman=%.6f decode=%.6f\\n", g_t_delta, g_t_huff, g_t_dec);\n' + old)
open("stages/codep_stages.c", "w").write(p)
print("patched final print in codep_stages.c (2 places)")
