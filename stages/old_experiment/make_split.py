#!/usr/bin/env python3
"""Generate lbg_pure_mpi_split.c from lbg_pure_mpi.c (June 2026 side experiment).
Adds timers only: it separates local computation from MPI communication/synchronization (and, for Huffman,
the sequential round-trip verification decode that the original program performs inside the timed region).
The computation and the output files are unchanged.  Each anchor must occur exactly once."""
import sys
s = open("lbg_pure_mpi.c").read()

def rep(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"anchor found {s.count(old)} times (need 1):\n{old}")
    s = s.replace(old, new)

def timed(call):          # wrap one MPI call and add its time to <acc>
    return call

rep("#define K2            0.03\n",
    "#define K2            0.03\n\n"
    "/* split timers (seconds, rank 0 view): local computation vs communication / synchronization */\n"
    "static double g_h_comm = 0.0, g_h_comp = 0.0, g_h_verify = 0.0;\n")

# ---- Huffman function ----
rep("    int chunk = (num_labels + size - 1) / size;\n    int start = rank * chunk;\n    int end   = start + chunk;\n    if (start > num_labels) start = num_labels;\n    if (end   > num_labels) end   = num_labels;\n",
    "    double _f0 = MPI_Wtime(), _comm0 = g_h_comm;\n"
    "    int chunk = (num_labels + size - 1) / size;\n    int start = rank * chunk;\n    int end   = start + chunk;\n    if (start > num_labels) start = num_labels;\n    if (end   > num_labels) end   = num_labels;\n")
for call in ["MPI_Allreduce(local_freq, freq, max_symbol + 1, MPI_UINT32_T, MPI_SUM, comm);",
             "MPI_Exscan(&local_bits, &my_bit_offset, 1, MPI_INT, MPI_SUM, comm);",
             "MPI_Allreduce(&local_bits, &total_bits, 1, MPI_INT, MPI_SUM, comm);",
             "MPI_Reduce(local_enc, enc, total_bytes, MPI_BYTE, MPI_BOR, 0, comm);"]:
    rep("    " + call + "\n",
        "    { double _b = MPI_Wtime(); " + call + " g_h_comm += MPI_Wtime() - _b; }\n")
rep("    if (rank == 0) {\n        /* round-trip verification */\n",
    "    g_h_comp += (MPI_Wtime() - _f0) - (g_h_comm - _comm0);\n    double _v0 = MPI_Wtime();\n"
    "    if (rank == 0) {\n        /* round-trip verification */\n")
rep("        free(decoded);\n        free(enc);\n    }\n",
    "        free(decoded);\n        free(enc);\n    }\n    g_h_verify += MPI_Wtime() - _v0;\n")
rep('        printf("Time (Huffman MPI)      : %.6f s\\n", time_huff);\n',
    '        printf("Time (Huffman MPI)      : %.6f s\\n", time_huff);\n'
    '        printf("Time (Huffman computation)   : %.6f s\\n", g_h_comp);\n'
    '        printf("Time (Huffman communication) : %.6f s\\n", g_h_comm);\n'
    '        printf("Time (Huffman verification)  : %.6f s\\n", g_h_verify);\n'
    '        printf("Time (Huffman other)         : %.6f s\\n", time_huff - g_h_comp - g_h_comm - g_h_verify);\n')

# ---- Delta encode ----
rep("    MPI_Allgatherv(local_delta, local_n, MPI_BYTE,\n                   labels_delta_u, recvcounts, displs, MPI_BYTE,\n                   MPI_COMM_WORLD);\n    free(local_delta);\n",
    "    double _te_m = MPI_Wtime();\n"
    "    MPI_Allgatherv(local_delta, local_n, MPI_BYTE,\n                   labels_delta_u, recvcounts, displs, MPI_BYTE,\n                   MPI_COMM_WORLD);\n"
    "    double time_delta_enc_comm = MPI_Wtime() - _te_m;\n    free(local_delta);\n")
rep('        printf("Time (Delta encode MPI) : %.6f s\\n", time_delta_enc);\n',
    '        printf("Time (Delta encode MPI) : %.6f s\\n", time_delta_enc);\n'
    '        printf("Time (Delta encode computation)   : %.6f s\\n", time_delta_enc - time_delta_enc_comm);\n'
    '        printf("Time (Delta encode communication) : %.6f s\\n", time_delta_enc_comm);\n')

# ---- Delta decode ----
rep("    int local_sum = 0;\n", "    double dd_comm = 0.0;\n    int local_sum = 0;\n")
rep("    MPI_Exscan(&local_sum, &my_offset, 1, MPI_INT, MPI_SUM, MPI_COMM_WORLD);\n",
    "    { double _b = MPI_Wtime(); MPI_Exscan(&local_sum, &my_offset, 1, MPI_INT, MPI_SUM, MPI_COMM_WORLD); dd_comm += MPI_Wtime() - _b; }\n")
rep("    MPI_Allgatherv(local_labels, local_n, MPI_BYTE,\n                   labels, recvcounts, displs, MPI_BYTE,\n                   MPI_COMM_WORLD);\n",
    "    { double _b = MPI_Wtime();\n    MPI_Allgatherv(local_labels, local_n, MPI_BYTE,\n                   labels, recvcounts, displs, MPI_BYTE,\n                   MPI_COMM_WORLD);\n      dd_comm += MPI_Wtime() - _b; }\n")
rep('    if (rank == 0)\n        printf("Time (Delta dec MPI)    : %.6f s\\n", time_delta_dec);\n',
    '    if (rank == 0) {\n        printf("Time (Delta dec MPI)    : %.6f s\\n", time_delta_dec);\n'
    '        printf("Time (Delta decode computation)   : %.6f s\\n", time_delta_dec - dd_comm);\n'
    '        printf("Time (Delta decode communication) : %.6f s\\n", dd_comm);\n    }\n')
open("lbg_pure_mpi_split.c", "w").write(s)
print("wrote lbg_pure_mpi_split.c")
