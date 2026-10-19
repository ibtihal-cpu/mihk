"""Build sem_v7_proc.c / pam_v7_proc.c from the approved *_final.c files.
Adds ONE extra printed line ("Processing time (no I/O, no metrics)") and nothing else.
Included: training-vector construction, workload distribution (+ calibration), scatter, LBG, gather,
          codebook conversion, delta coding, Huffman, inverse delta, reconstruction.
Excluded: image reading, file output, console printing, entropy statistics, LBG-only decompress, MSE/PSNR/SSIM."""
import re, sys
def rep(t, a, b, count=1):
    assert t.count(a) >= 1, "missing: " + a[:70]
    if count == 1: assert t.count(a) == 1, ("not unique (%d): " % t.count(a)) + a[:70]
    return t.replace(a, b)

# ---------------- parallel ----------------
p = open("pam_v4_nofilter_final.c").read()
g0 = p.index("static int run_gray_parallel"); c0 = p.index("static int run_color_parallel"); m0 = p.index("MAIN — picks mode")
head, gray, color, tail = p[:g0], p[g0:c0], p[c0:m0], p[m0:]

# gray
gray = rep(gray, "double t_total0 = MPI_Wtime();", "double t_total0 = MPI_Wtime();\n    double t_proc = 0.0;   /* v7: processing time (no I/O, no metrics) */")
gray = rep(gray, "        num_vectors = build_training_vectors(image, &training_set);",
           "        double tpa = MPI_Wtime();\n        num_vectors = build_training_vectors(image, &training_set);\n        t_proc += MPI_Wtime() - tpa;")
gray = rep(gray, "    MPI_Bcast(&num_vectors, 1, MPI_INT, 0, MPI_COMM_WORLD);", "    double tpb0 = MPI_Wtime();\n    MPI_Bcast(&num_vectors, 1, MPI_INT, 0, MPI_COMM_WORLD);")
gray = rep(gray, "    MPI_Gatherv(local_labels, local_n,                MPI_UINT8_T,\n                labels,       vec_counts, vec_displs, MPI_UINT8_T,\n                0, MPI_COMM_WORLD);\n",
           "    MPI_Gatherv(local_labels, local_n,                MPI_UINT8_T,\n                labels,       vec_counts, vec_displs, MPI_UINT8_T,\n                0, MPI_COMM_WORLD);\n    t_proc += MPI_Wtime() - tpb0;\n")
gray = rep(gray, "        double td0 = MPI_Wtime();\n", "        double td0 = MPI_Wtime();\n        double tpd0 = td0;\n")
gray = rep(gray, "        double H_delta = compute_entropy(labels_delta_u, num_vectors, 256);", "        t_proc += MPI_Wtime() - tpd0;\n        double H_delta = compute_entropy(labels_delta_u, num_vectors, 256);")
gray = rep(gray, "        double time_huff = t_huff1 - t_huff0;", "        double time_huff = t_huff1 - t_huff0;\n        t_proc += time_huff;")
gray = rep(gray, "        labels[0] = labels_delta_u[0];\n", "        double tpr0 = MPI_Wtime();\n        labels[0] = labels_delta_u[0];\n")
gray = rep(gray, "        decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, labels);\n",
           "        decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, labels);\n        t_proc += MPI_Wtime() - tpr0;\n")
gray = rep(gray, '        printf("Total execution time: %.3f seconds\\n", time_taken);',
           '        printf("Total execution time: %.3f seconds\\n", time_taken);\n        printf("Processing time (no I/O, no metrics): %.4f seconds\\n", t_proc);')

# color
color = rep(color, "double t_total0 = MPI_Wtime();", "double t_total0 = MPI_Wtime();\n    double t_proc = 0.0;   /* v7: processing time (no I/O, no metrics) */")
color = rep(color, "    compute_vector_distribution(num_vectors, vlen, rank, size,\n                                 vec_counts, vec_displs, byte_counts, byte_displs);\n",
            "    double tpc0 = MPI_Wtime();\n    compute_vector_distribution(num_vectors, vlen, rank, size,\n                                 vec_counts, vec_displs, byte_counts, byte_displs);\n    t_proc += MPI_Wtime() - tpc0;\n")
color = rep(color, "            int nv = build_training_vectors(channels[ch], &training_set);",
            "            double tpa = MPI_Wtime();\n            int nv = build_training_vectors(channels[ch], &training_set);\n            t_proc += MPI_Wtime() - tpa;")
color = rep(color, "        MPI_Scatterv(training_set, byte_counts, byte_displs, MPI_UINT8_T,", "        double tpb0 = MPI_Wtime();\n        MPI_Scatterv(training_set, byte_counts, byte_displs, MPI_UINT8_T,")
color = rep(color, "        MPI_Gatherv(local_labels, local_n,                MPI_UINT8_T,\n                    labels,       vec_counts, vec_displs, MPI_UINT8_T,\n                    0, MPI_COMM_WORLD);\n",
            "        MPI_Gatherv(local_labels, local_n,                MPI_UINT8_T,\n                    labels,       vec_counts, vec_displs, MPI_UINT8_T,\n                    0, MPI_COMM_WORLD);\n        t_proc += MPI_Wtime() - tpb0;\n")
color = rep(color, "            labels_delta_u = (uint8_t*)malloc(num_vectors);\n", "            double tpr0 = MPI_Wtime();\n            labels_delta_u = (uint8_t*)malloc(num_vectors);\n")
color = rep(color, "            decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, labels);\n",
            "            decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, labels);\n            t_proc += MPI_Wtime() - tpr0;\n")
color = rep(color, '        printf("Total execution time: %.3f seconds\\n", time_taken);',
            '        printf("Total execution time: %.3f seconds\\n", time_taken);\n        printf("Processing time (no I/O, no metrics): %.4f seconds\\n", t_proc);')
open("pam_v7_proc.c", "w").write(head + gray + color + tail)

# ---------------- sequential ----------------
s = open("sem_v3_nofilter_final.c").read()
s = rep(s, "    double tt_total  = t_total1 - t_total0;\n",
        "    double tt_total  = t_total1 - t_total0;\n    double tt_proc   = tt_build + tt_lbg + tt_cvt + tt_delta + tt_huff + tt_dd + tt_rec;   /* v7 */\n")
s = rep(s, '    printf("  Total (measured)         : %.4f s\\n", tt_total);\n',
        '    printf("  Total (measured)         : %.4f s\\n", tt_total);\n    printf("  Processing time (no I/O, no metrics): %.4f s\\n", tt_proc);\n')
s = rep(s, "    double lbg_time;\n    int lbg_iters;\n    int compressed_bytes;", "    double lbg_time;\n    double proc_time;   /* v7 */\n    int lbg_iters;\n    int compressed_bytes;")
s = rep(s, "    ChannelResult res;\n    int original_image_bytes = WIDTH * HEIGHT;", "    ChannelResult res;\n    res.proc_time = 0.0;\n    int original_image_bytes = WIDTH * HEIGHT;")
s = rep(s, "    uint8_t *training_set = NULL;\n    int num_vectors = build_training_vectors(channel_image, &training_set);",
        "    uint8_t *training_set = NULL;\n    double tp_a = wtime();\n    int num_vectors = build_training_vectors(channel_image, &training_set);")
s = rep(s, "    double t_lbg0 = wtime();\n    res.lbg_iters = lbg(training_f, num_vectors, CODEBOOK_SIZE, labels, codebook, /*verbose=*/0);",
        "    res.proc_time += wtime() - tp_a;\n    double t_lbg0 = wtime();\n    res.lbg_iters = lbg(training_f, num_vectors, CODEBOOK_SIZE, labels, codebook, /*verbose=*/0);")
s = rep(s, "    res.lbg_time = t_lbg1 - t_lbg0;\n    free(training_f);", "    res.lbg_time = t_lbg1 - t_lbg0;\n    res.proc_time += res.lbg_time;\n    free(training_f);")
s = rep(s, "    uint8_t *labels_delta_u = malloc(num_vectors);\n    if (!labels_delta_u) { fprintf(stderr, \"malloc failed: labels_delta_u\\n\"); exit(EXIT_FAILURE); }\n    labels_delta_u[0] = labels[0];\n    for (int i = 1; i < num_vectors; i++)\n        labels_delta_u[i] = (uint8_t)(labels[i] - labels[i-1] + 128);\n",
        "    double tp_d = wtime();\n    uint8_t *labels_delta_u = malloc(num_vectors);\n    if (!labels_delta_u) { fprintf(stderr, \"malloc failed: labels_delta_u\\n\"); exit(EXIT_FAILURE); }\n    labels_delta_u[0] = labels[0];\n    for (int i = 1; i < num_vectors; i++)\n        labels_delta_u[i] = (uint8_t)(labels[i] - labels[i-1] + 128);\n    res.proc_time += wtime() - tp_d;\n")
s = rep(s, "    int huff_total = huffman_on_labels(labels_delta_u, num_vectors, 255,\n                                        &huff_data_bytes, &header_bytes);\n\n    int codebook_bytes = CODEBOOK_SIZE * VLEN;",
        "    double tp_h = wtime();\n    int huff_total = huffman_on_labels(labels_delta_u, num_vectors, 255,\n                                        &huff_data_bytes, &header_bytes);\n    res.proc_time += wtime() - tp_h;\n\n    int codebook_bytes = CODEBOOK_SIZE * VLEN;")
s = rep(s, "    labels[0] = labels_delta_u[0];\n    for (int i = 1; i < num_vectors; i++)\n        labels[i] = labels[i-1] + ((int)labels_delta_u[i] - 128);\n\n    uint8_t *reconstructed = malloc(WIDTH * HEIGHT);\n    if (!reconstructed) { fprintf(stderr, \"malloc failed: reconstructed\\n\"); exit(EXIT_FAILURE); }\n    decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook, labels);\n",
        "    double tp_r = wtime();\n    labels[0] = labels_delta_u[0];\n    for (int i = 1; i < num_vectors; i++)\n        labels[i] = labels[i-1] + ((int)labels_delta_u[i] - 128);\n\n    uint8_t *reconstructed = malloc(WIDTH * HEIGHT);\n    if (!reconstructed) { fprintf(stderr, \"malloc failed: reconstructed\\n\"); exit(EXIT_FAILURE); }\n    decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook, labels);\n    res.proc_time += wtime() - tp_r;\n")
s = rep(s, '    printf("Total program time        : %.4f s\\n", t_program1 - t_program0);\n',
        '    printf("Total program time        : %.4f s\\n", t_program1 - t_program0);\n    printf("Processing time (no I/O, no metrics): %.4f s\\n", res_r.proc_time + res_g.proc_time + res_b.proc_time);\n')
open("sem_v7_proc.c", "w").write(s)
print("ok")
