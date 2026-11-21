"""Build code1.c (parallel) and code2.c (sequential) from the approved pam_v4_nofilter.c / sem_v3_nofilter.c.
Only two things change:  (A) Huffman-table size accounting,  (B) the time measures (new 'Total processing time').
Everything else (algorithm, LBG, distribution, Delta, Huffman, quality metrics) is untouched."""
def rep(t, a, b):
    assert t.count(a) == 1, ("expected exactly 1 occurrence (%d): " % t.count(a)) + a[:80]
    return t.replace(a, b)

NOTE = '''/* ============================================================
   %(name)s  =  %(base)s  +  TWO controlled changes (nothing else):

   (A) Huffman-table size accounting.  The program does not write a stand-alone compressed file; the compressed
       size is  codebook (K*16 B) + Huffman table + Huffman-coded data.  The table is accounted as 5 bytes per used
       symbol (1 B symbol + 4 B frequency) + 10 B fixed metadata (before: 4 B per used symbol).  Affects CR and BPP
       only; LBG, the indices and the reconstructed image are unchanged.  The CR print labels were made explicit.

   (B) Timing.  "Time (LBG only)" is unchanged.  New line "Total processing time" covers: training-vector
       construction, workload distribution (+ speed calibration for Adaptive), scatter, LBG, gather, delta coding,
       Huffman coding (+ its internal decode check), inverse delta and image reconstruction.  It EXCLUDES image
       reading, console output, output-file writing, entropy statistics, LBG-only reconstruction, and MSE/PSNR/SSIM.
       The old end-to-end time is still printed, labelled "complete program".
       The Huffman decode-check message is now printed AFTER the timed Huffman call (same text as before).
   ============================================================ */
'''
def build(src, dst, name, base, par):
    t = open(src).read()
    # print the Huffman decode-check message outside the timed region
    if par:
        t = rep(t, 'static HuffNode *huff_build_tree', 'static int g_huff_decode_ok = 1;   /* result of the Huffman decode check */\nstatic void report_huffman_decode_check(void) {\n    printf("Decode check: %s\\n", g_huff_decode_ok ? "OK (labels identical, no distortion)" : "ERROR (mismatch!)");\n}\nstatic HuffNode *huff_build_tree')
        t = rep(t, '    printf("Decode check: %s\\n",\n           ok ? "OK (labels identical, no distortion)" : "ERROR (mismatch!)");\n', '    g_huff_decode_ok = ok;\n')
        t = rep(t, "        double t_huff1 = MPI_Wtime();\n        double time_huff = t_huff1 - t_huff0;\n        t_proc += time_huff;\n",
                   "        double t_huff1 = MPI_Wtime();\n        double time_huff = t_huff1 - t_huff0;\n        t_proc += time_huff;\n        report_huffman_decode_check();\n")
        t = rep(t, "            t_proc += MPI_Wtime() - tpr0;\n", "            t_proc += MPI_Wtime() - tpr0;\n            report_huffman_decode_check();\n")
        t = rep(t, 'printf("Processing time (no I/O, no metrics): %.4f seconds\\n", t_proc);', 'printf("Total processing time (no I/O, no console output, no quality metrics): %.4f seconds\\n", t_proc);') if t.count('printf("Processing time (no I/O, no metrics)') == 1 else t.replace('printf("Processing time (no I/O, no metrics): %.4f seconds\\n", t_proc);', 'printf("Total processing time (no I/O, no console output, no quality metrics): %.4f seconds\\n", t_proc);')
        t = t.replace('printf("Total execution time: %.3f seconds\\n", time_taken);', 'printf("Total execution time (complete program, incl. I/O and metrics): %.3f seconds\\n", time_taken);')
    else:
        t = rep(t, 'int huffman_on_labels(', 'static int g_huff_decode_ok = 1;   /* result of the Huffman decode check */\nstatic void report_huffman_decode_check(void) {\n    printf("  Decode check        : %s\\n", g_huff_decode_ok ? "OK (labels identical, no distortion)" : "ERROR (mismatch!)");\n}\nint huffman_on_labels(')
        t = rep(t, '    printf("  Decode check        : %s\\n", ok ? "OK (labels identical, no distortion)" : "ERROR (mismatch!)");\n', '    g_huff_decode_ok = ok;\n')
        t = rep(t, "    double t_huff1 = wtime();\n", "    double t_huff1 = wtime();\n    report_huffman_decode_check();\n")
        t = rep(t, "    res.proc_time += wtime() - tp_h;\n", "    res.proc_time += wtime() - tp_h;\n    report_huffman_decode_check();\n")
        t = rep(t, 'printf("  Processing time (no I/O, no metrics): %.4f s\\n", tt_proc);', 'printf("  Total processing time (no I/O, no console output, no quality metrics): %.4f s\\n", tt_proc);')
        t = rep(t, 'printf("Processing time (no I/O, no metrics): %.4f s\\n", res_r.proc_time + res_g.proc_time + res_b.proc_time);', 'printf("Total processing time (no I/O, no console output, no quality metrics): %.4f s\\n", res_r.proc_time + res_g.proc_time + res_b.proc_time);')
        t = rep(t, 'printf("  Total (measured)         : %.4f s\\n", tt_total);', 'printf("  Total (measured, complete program, incl. I/O and metrics): %.4f s\\n", tt_total);')
        t = rep(t, 'printf("Total program time        : %.4f s\\n", t_program1 - t_program0);', 'printf("Total program time (complete program, incl. I/O and metrics): %.4f s\\n", t_program1 - t_program0);')
    t = t.replace("/* v7: processing time (no I/O, no metrics) */", "/* total processing time accumulator */")
    t = t.replace("   /* v7: same stages as the parallel/colour paths (no codebook u8 conversion) */", "   /* same stages as the parallel and colour paths */")
    t = t.replace("   /* v7 */", "")
    t = t.replace("   /* v7 */\n", "\n")
    # insert the change note right before the first #include
    i = t.index("#include <stdio.h>")
    t = t[:i] + NOTE % dict(name=name, base=base) + "\n" + t[i:]
    open(dst, "w").write(t)
build("pam_v7_proc.c", "code1.c", "code1.c (parallel, MPI)", "pam_v4_nofilter.c", True)
build("sem_v7_proc.c", "code2.c", "code2.c (sequential)", "sem_v3_nofilter.c", False)
print("ok")
