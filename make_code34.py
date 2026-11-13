"""code3.c (parallel) / code4.c (sequential) = code1.c / code2.c + a REAL compressed container (canonical Huffman).
The compressed size becomes the size of an actual byte buffer (also written to disk); the image is reconstructed
by DECODING that buffer.  LBG, Delta, quality metrics and the timers are unchanged except that the Huffman-size
model is replaced by the container encode/decode."""
def rep(t, a, b):
    assert t.count(a) == 1, ("expected exactly 1 occurrence (%d): " % t.count(a)) + a[:90]
    return t.replace(a, b)

HELPERS = r'''
/* ============================================================
   REAL COMPRESSED CONTAINER  (canonical Huffman; replaces the size model)
   Layout (all multi-byte fields little-endian):
     [ 2 B used_symbols ][ 4 B num_labels ][ 2 B width ][ 2 B height ][ 4 B coded_bytes ]      14 B header
     [ used_symbols x ( 1 B symbol , 1 B code_length ) ]                                       table (2 B/symbol)
     [ K x 16 B codebook, 8-bit rounded elements ]
     [ coded_bytes B canonical-Huffman bitstream of the delta-coded indices ]
   The decoder rebuilds the canonical codes from (symbol, length) pairs, so no frequencies are stored
   (canonical prefix codes: Schwartz and Kallick, CACM 1964).
   ============================================================ */
typedef struct { int sym; int len; } CanSym;
static int can_cmp(const void *a, const void *b)
{
    const CanSym *x = (const CanSym *)a, *y = (const CanSym *)b;
    if (x->len != y->len) return x->len - y->len;
    return x->sym - y->sym;
}
static void canonical_codes(const int *len, uint64_t *code)
{
    CanSym s[256]; int n = 0;
    for (int i = 0; i < 256; i++) { code[i] = 0; if (len[i] > 0) { s[n].sym = i; s[n].len = len[i]; n++; } }
    if (n == 0) return;
    qsort(s, n, sizeof(CanSym), can_cmp);
    uint64_t c = 0;
    code[s[0].sym] = 0;
    for (int i = 1; i < n; i++) {
        c = (c + 1) << (s[i].len - s[i-1].len);
        code[s[i].sym] = c;
    }
}
static void put16(uint8_t *p, unsigned v) { p[0] = (uint8_t)(v & 255u); p[1] = (uint8_t)((v >> 8) & 255u); }
static void put32(uint8_t *p, uint32_t v) { for (int i = 0; i < 4; i++) p[i] = (uint8_t)((v >> (8*i)) & 255u); }
static unsigned get16(const uint8_t *p) { return (unsigned)p[0] | ((unsigned)p[1] << 8); }
static uint32_t get32(const uint8_t *p) { uint32_t v = 0; for (int i = 0; i < 4; i++) v |= ((uint32_t)p[i]) << (8*i); return v; }

static size_t container_capacity(int n, int K, int vlen)
{
    return 14 + 512 + (size_t)K * vlen + (size_t)n * 9 + 16;
}

/* returns the number of bytes written (0 on failure); *out_data_bytes = coded bitstream bytes,
   *out_header_bytes = header + table bytes (everything except codebook and bitstream) */
static size_t container_encode(uint8_t *out, const uint8_t *delta, int n, const uint8_t *cb_u8,
                               int K, int vlen, int w, int h, int *out_data_bytes, int *out_header_bytes)
{
    uint32_t freq[256] = {0};
    for (int i = 0; i < n; i++) freq[delta[i]]++;
    HuffNode *root = huff_build_tree(freq, 255);
    if (!root) return 0;
    HuffCode tbl[256];
    huff_build_codes(root, tbl, 255);
    huff_free_tree(root);
    int len[256]; int used = 0;
    for (int i = 0; i < 256; i++) { len[i] = tbl[i].length; if (freq[i] > 0) used++; }
    uint64_t code[256];
    canonical_codes(len, code);

    size_t p = 0;
    put16(out + p, (unsigned)used); p += 2;
    put32(out + p, (uint32_t)n);    p += 4;
    put16(out + p, (unsigned)w);    p += 2;
    put16(out + p, (unsigned)h);    p += 2;
    size_t coded_field = p;         p += 4;
    for (int i = 0; i < 256; i++) if (len[i] > 0) { out[p++] = (uint8_t)i; out[p++] = (uint8_t)len[i]; }
    int header_bytes = (int)p;
    memcpy(out + p, cb_u8, (size_t)K * vlen); p += (size_t)K * vlen;

    size_t data_start = p;
    uint8_t cur = 0; int bit_pos = 0;
    for (int i = 0; i < n; i++) {
        int s = delta[i], L = len[s];
        uint64_t c = code[s];
        for (int b = L - 1; b >= 0; b--) {
            cur |= (uint8_t)(((c >> b) & 1u) << (7 - bit_pos));
            if (++bit_pos == 8) { out[p++] = cur; cur = 0; bit_pos = 0; }
        }
    }
    if (bit_pos > 0) out[p++] = cur;
    uint32_t coded = (uint32_t)(p - data_start);
    put32(out + coded_field, coded);
    if (out_data_bytes)   *out_data_bytes = (int)coded;
    if (out_header_bytes) *out_header_bytes = header_bytes;
    return p;
}

/* decodes one container: indices -> inverse delta -> codebook lookup -> image.  returns 0 on success */
static int container_decode(const uint8_t *buf, size_t buf_len, uint8_t *recon,
                            int K, int vlen, int block, int w, int h, size_t *consumed)
{
    if (buf_len < 14) return -1;
    unsigned used = get16(buf); uint32_t n = get32(buf + 2);
    unsigned w_ = get16(buf + 6), h_ = get16(buf + 8); uint32_t coded = get32(buf + 10);
    if ((int)w_ != w || (int)h_ != h || used == 0 || used > 256) return -2;
    size_t p = 14;
    if (p + 2 * (size_t)used + (size_t)K * vlen + coded > buf_len) return -3;
    int len[256] = {0};
    for (unsigned u = 0; u < used; u++) { int s = buf[p++]; len[s] = buf[p++]; }
    const uint8_t *cb = buf + p; p += (size_t)K * vlen;
    const uint8_t *data = buf + p;
    uint64_t code[256];
    canonical_codes(len, code);

    size_t maxnodes = 2; for (int i = 0; i < 256; i++) maxnodes += (size_t)len[i];
    int *child = (int *)malloc(maxnodes * 2 * sizeof(int));
    int *symof = (int *)malloc(maxnodes * sizeof(int));
    if (!child || !symof) { free(child); free(symof); return -4; }
    int nn = 1; child[0] = child[1] = -1; symof[0] = -1;
    for (int s = 0; s < 256; s++) if (len[s] > 0) {
        int node = 0;
        for (int b = len[s] - 1; b >= 0; b--) {
            int bit = (int)((code[s] >> b) & 1u);
            if (child[node * 2 + bit] < 0) { child[nn * 2] = child[nn * 2 + 1] = -1; symof[nn] = -1; child[node * 2 + bit] = nn++; }
            node = child[node * 2 + bit];
        }
        symof[node] = s;
    }
    uint8_t *lab = (uint8_t *)malloc(n);
    int rc = 0; uint32_t pos = 0; int node = 0;
    for (uint32_t i = 0; i < coded && pos < n && rc == 0; i++) {
        for (int b = 7; b >= 0 && pos < n; b--) {
            node = child[node * 2 + ((data[i] >> b) & 1)];
            if (node < 0) { rc = -5; break; }
            if (symof[node] >= 0) { lab[pos++] = (uint8_t)symof[node]; node = 0; }
        }
    }
    if (rc == 0 && pos != n) rc = -6;
    if (rc == 0) {
        for (uint32_t i = 1; i < n; i++) lab[i] = (uint8_t)(lab[i-1] + ((int)lab[i] - 128));   /* inverse delta (label 0 is stored as is) */
        int bpr = w / block, bpc = h / block; uint32_t v = 0;
        for (int by = 0; by < bpc; by++)
            for (int bx = 0; bx < bpr; bx++, v++)
                for (int r = 0; r < block; r++)
                    for (int c = 0; c < block; c++)
                        recon[(by * block + r) * w + (bx * block + c)] = cb[(size_t)lab[v] * vlen + r * block + c];
    }
    free(child); free(symof); free(lab);
    if (rc == 0 && consumed) *consumed = p + coded;
    return rc;
}
'''
# NOTE: the inverse delta above is in-place on lab[] where lab[] holds the DELTA values on entry.

NOTE_ADD = '''
   (C) code3.c / code4.c only: the Huffman size MODEL is replaced by a REAL compressed container (canonical Huffman;
       see container_encode / container_decode).  The compressed size is the byte size of that container
       (14 B header + 2 B per used symbol + K*16 B codebook + coded bytes), the container is written to disk
       (compressed.bin / compressed_color.bin) and the image used for MSE/PSNR/SSIM is DECODED from it.
       Disk writing/reading of the container and the cross-checks are NOT part of the processing time.
'''

def common(t, par):
    t = rep(t, "int huffman_on_labels(", HELPERS + "\nint huffman_on_labels(")
    t = rep(t, "static void report_huffman_decode_check(void) {", "__attribute__((unused)) static void report_huffman_decode_check(void) {")
    t = rep(t, "(estimated compressed size)\\n\", CR_system);", "(actual container size)\\n\", CR_system);") if not par else t.replace("(estimated compressed size)\\n\", CR_system);", "(actual container size)\\n\", CR_system);")
    t = t.replace("(estimated compressed size)\\n\", rgb_cr);", "(actual container size)\\n\", rgb_cr);")
    t = rep(t, "   ============================================================ */\n\n#include <stdio.h>", NOTE_ADD.rstrip("\n") + "\n   ============================================================ */\n\n#include <stdio.h>") if False else t
    i = t.index("   (B) Timing.")
    j = t.index("   ============================================================ */", i)
    t = t[:j] + NOTE_ADD.lstrip("\n") + t[j:]
    return t

# ------------------------------------------------------------------ parallel
t = open("code1.c").read()
t = common(t, True)
old = """        codebook_data = malloc(K * vlen);
        for (int k = 0; k < K; k++)
            for (int i = 0; i < vlen; i++)
                codebook_data[k * vlen + i] = (uint8_t) roundf(codebook_flat[k * vlen + i]);
        printf("Codebook converted to uint8_t (size = %d bytes)\\n", K * vlen);
"""
new = """        double tpc_c = MPI_Wtime();   /* 8-bit codebook = part of the container (timed here, as in the colour path) */
        codebook_data = malloc(K * vlen);
        for (int k = 0; k < K; k++)
            for (int i = 0; i < vlen; i++)
                codebook_data[k * vlen + i] = (uint8_t) roundf(codebook_flat[k * vlen + i]);
        t_proc += MPI_Wtime() - tpc_c;
        printf("Codebook converted to uint8_t (size = %d bytes)\\n", K * vlen);
"""
t = rep(t, old, new)
t = rep(t, "    uint8_t *reconstructed = NULL;\n    int codebook_bytes = 0;\n", "    uint8_t *reconstructed = NULL;\n    int codebook_bytes = 0;\n    uint8_t *container = NULL; size_t container_bytes = 0;\n")
old = """        int huff_data_bytes = 0;
        int header_bytes    = 0;
        double t_huff0 = MPI_Wtime();
        int huff_total = huffman_on_labels(labels_delta_u, num_vectors, 255,
                                            &huff_data_bytes, &header_bytes);
        double t_huff1 = MPI_Wtime();
        double time_huff = t_huff1 - t_huff0;
        t_proc += time_huff;
        report_huffman_decode_check();
        printf("Time (Huffman only): %.4f seconds\\n\\n", time_huff);
"""
new = """        int huff_data_bytes = 0;
        int header_bytes    = 0;
        container = (uint8_t *)malloc(container_capacity(num_vectors, K, vlen));
        double t_huff0 = MPI_Wtime();
        container_bytes = container_encode(container, labels_delta_u, num_vectors, codebook_data, K, vlen,
                                           WIDTH, HEIGHT, &huff_data_bytes, &header_bytes);
        double t_huff1 = MPI_Wtime();
        double time_huff = t_huff1 - t_huff0;
        t_proc += time_huff;
        int huff_total = (int)container_bytes - K * vlen;   /* header + table + coded bytes */
        printf("Time (container encode only): %.4f seconds\\n\\n", time_huff);
"""
t = rep(t, old, new)
old = """        double tpr0 = MPI_Wtime();
        labels[0] = labels_delta_u[0];
        for (int i = 1; i < num_vectors; i++)
            labels[i] = labels[i-1] + ((int)labels_delta_u[i] - 128);

        reconstructed = malloc(WIDTH * HEIGHT);
        decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, labels);
        t_proc += MPI_Wtime() - tpr0;
"""
new = """        double tpr0 = MPI_Wtime();
        reconstructed = malloc(WIDTH * HEIGHT);
        int dec_rc = container_decode(container, container_bytes, reconstructed, K, vlen, BLOCK_SIZE, WIDTH, HEIGHT, NULL);
        t_proc += MPI_Wtime() - tpr0;

        {   /* untimed cross-check: the image decoded from the container must equal the encoder-side reconstruction */
            uint8_t *chk_lab = (uint8_t *)malloc(num_vectors);
            chk_lab[0] = labels_delta_u[0];
            for (int i = 1; i < num_vectors; i++) chk_lab[i] = chk_lab[i-1] + ((int)labels_delta_u[i] - 128);
            uint8_t *chk_img = (uint8_t *)malloc(WIDTH * HEIGHT);
            decompress_image(chk_img, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, chk_lab);
            printf("Container decode check: %s\\n", (dec_rc == 0 && memcmp(chk_img, reconstructed, (size_t)WIDTH * HEIGHT) == 0)
                   ? "OK (image decoded from the container is identical to the encoder-side reconstruction)" : "ERROR (mismatch!)");
            free(chk_lab); free(chk_img);
        }
"""
t = rep(t, old, new)
old = "        fclose(file1);\n"
new = """        fclose(file1);

        {   /* write the real compressed file and verify it by reading it back (not timed) */
            FILE *fc = fopen("compressed.bin", "wb");
            fwrite(container, 1, container_bytes, fc);
            fclose(fc);
            FILE *fr = fopen("compressed.bin", "rb");
            uint8_t *rb = (uint8_t *)malloc(container_bytes); size_t got = fread(rb, 1, container_bytes, fr); fclose(fr);
            uint8_t *rimg = (uint8_t *)malloc(WIDTH * HEIGHT);
            int rrc = container_decode(rb, got, rimg, K, vlen, BLOCK_SIZE, WIDTH, HEIGHT, NULL);
            printf("File round-trip check (compressed.bin, %zu bytes): %s\\n", container_bytes,
                   (rrc == 0 && memcmp(rimg, reconstructed, (size_t)WIDTH * HEIGHT) == 0) ? "OK" : "ERROR (mismatch!)");
            free(rb); free(rimg);
        }
"""
t = rep(t, old, new)
t = rep(t, "        free(codebook_data);\n", "        free(codebook_data);\n        free(container);\n")
# color
t = rep(t, "    int compressed_bytes;\n    uint8_t *reconstructed;\n} ChannelResult;", "    int compressed_bytes;\n    uint8_t *reconstructed;\n    uint8_t *container; size_t container_bytes;\n} ChannelResult;")
old = """            double tpr0 = MPI_Wtime();
            labels_delta_u = (uint8_t*)malloc(num_vectors);
            labels_delta_u[0] = labels[0];
            for (int i = 1; i < num_vectors; i++)
                labels_delta_u[i] = (uint8_t)(labels[i] - labels[i-1] + 128);

            int huff_data_bytes = 0, header_bytes = 0;
            int huff_total = huffman_on_labels(labels_delta_u, num_vectors, 255,
                                               &huff_data_bytes, &header_bytes);
            (void)huff_data_bytes; (void)header_bytes;

            int codebook_bytes = K * vlen;
            results[ch].compressed_bytes = codebook_bytes + huff_total;
            results[ch].lbg_time = lbg_time;

            labels[0] = labels_delta_u[0];
            for (int i = 1; i < num_vectors; i++)
                labels[i] = labels[i-1] + ((int)labels_delta_u[i] - 128);

            reconstructed = (uint8_t*)malloc(channel_bytes);
            decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, labels);
            t_proc += MPI_Wtime() - tpr0;
            report_huffman_decode_check();
"""
new = """            double tpr0 = MPI_Wtime();
            labels_delta_u = (uint8_t*)malloc(num_vectors);
            labels_delta_u[0] = labels[0];
            for (int i = 1; i < num_vectors; i++)
                labels_delta_u[i] = (uint8_t)(labels[i] - labels[i-1] + 128);

            uint8_t *cb_u8 = (uint8_t *)malloc((size_t)K * vlen);
            for (int i = 0; i < K * vlen; i++) cb_u8[i] = (uint8_t)roundf(codebook_flat[i]);
            int huff_data_bytes = 0, header_bytes = 0;
            results[ch].container = (uint8_t *)malloc(container_capacity(num_vectors, K, vlen));
            results[ch].container_bytes = container_encode(results[ch].container, labels_delta_u, num_vectors, cb_u8, K, vlen,
                                                           WIDTH, HEIGHT, &huff_data_bytes, &header_bytes);
            (void)huff_data_bytes; (void)header_bytes;
            results[ch].compressed_bytes = (int)results[ch].container_bytes;
            results[ch].lbg_time = lbg_time;

            reconstructed = (uint8_t*)malloc(channel_bytes);
            int dec_rc = container_decode(results[ch].container, results[ch].container_bytes, reconstructed, K, vlen,
                                          BLOCK_SIZE, WIDTH, HEIGHT, NULL);
            t_proc += MPI_Wtime() - tpr0;

            {   /* untimed cross-check against the encoder-side reconstruction */
                uint8_t *chk_lab = (uint8_t *)malloc(num_vectors);
                chk_lab[0] = labels_delta_u[0];
                for (int i = 1; i < num_vectors; i++) chk_lab[i] = chk_lab[i-1] + ((int)labels_delta_u[i] - 128);
                uint8_t *chk_img = (uint8_t *)malloc(channel_bytes);
                decompress_image(chk_img, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, chk_lab);
                printf("  [%s channel] Container decode check: %s\\n", channel_names[ch],
                       (dec_rc == 0 && memcmp(chk_img, reconstructed, (size_t)channel_bytes) == 0) ? "OK" : "ERROR (mismatch!)");
                free(chk_lab); free(chk_img);
            }
            free(cb_u8);
"""
t = rep(t, old, new)
old = """        save_bmp_color("compressed_color.bmp",
                       results[0].reconstructed,
                       results[1].reconstructed,
                       results[2].reconstructed,
                       WIDTH, HEIGHT);
"""
new = old + """
        {   /* write the real compressed file (3 containers back to back) and verify it by reading it back (not timed) */
            size_t tot = results[0].container_bytes + results[1].container_bytes + results[2].container_bytes;
            FILE *fc = fopen("compressed_color.bin", "wb");
            for (int c = 0; c < 3; c++) fwrite(results[c].container, 1, results[c].container_bytes, fc);
            fclose(fc);
            FILE *fr = fopen("compressed_color.bin", "rb");
            uint8_t *rb = (uint8_t *)malloc(tot); size_t got = fread(rb, 1, tot, fr); fclose(fr);
            uint8_t *rimg = (uint8_t *)malloc(channel_bytes);
            int ok = 1; size_t off = 0;
            for (int c = 0; c < 3 && ok; c++) {
                size_t used_bytes = 0;
                int rrc = container_decode(rb + off, got - off, rimg, K, vlen, BLOCK_SIZE, WIDTH, HEIGHT, &used_bytes);
                if (rrc != 0 || memcmp(rimg, results[c].reconstructed, (size_t)channel_bytes) != 0) ok = 0;
                off += used_bytes;
            }
            printf("File round-trip check (compressed_color.bin, %zu bytes): %s\\n", tot, ok ? "OK" : "ERROR (mismatch!)");
            free(rb); free(rimg);
        }
"""
t = rep(t, old, new)
t = rep(t, "        free(results[2].reconstructed);\n", "        free(results[2].reconstructed);\n        for (int c = 0; c < 3; c++) free(results[c].container);\n")
open("code3.c", "w").write(t)

# ------------------------------------------------------------------ sequential
t = open("code2.c").read()
t = common(t, False)
t = rep(t, "double tt_proc   = tt_build + tt_f32 + tt_lbg + tt_delta + tt_huff + tt_dd + tt_rec;", "double tt_proc   = tt_build + tt_f32 + tt_lbg + tt_cvt + tt_delta + tt_huff + tt_dd + tt_rec;")
old = """    int huff_data_bytes = 0;
    int header_bytes    = 0;
    double t_huff0 = wtime();
    int huff_total = huffman_on_labels(labels_delta_u, num_vectors, 255,
                                        &huff_data_bytes, &header_bytes);
    double t_huff1 = wtime();
    report_huffman_decode_check();
"""
new = """    int huff_data_bytes = 0;
    int header_bytes    = 0;
    uint8_t *container = (uint8_t *)malloc(container_capacity(num_vectors, CODEBOOK_SIZE, VLEN));
    double t_huff0 = wtime();
    size_t container_bytes = container_encode(container, labels_delta_u, num_vectors, codebook_data, CODEBOOK_SIZE, VLEN,
                                              WIDTH, HEIGHT, &huff_data_bytes, &header_bytes);
    double t_huff1 = wtime();
    int huff_total = (int)container_bytes - CODEBOOK_SIZE * VLEN;   /* header + table + coded bytes */
"""
t = rep(t, old, new)
old = """    double t_dd0 = wtime();
    labels[0] = labels_delta_u[0];
    for (int i = 1; i < num_vectors; i++)
        labels[i] = labels[i-1] + ((int)labels_delta_u[i] - 128);
    double t_dd1 = wtime();

    double t_rec0 = wtime();
    uint8_t *reconstructed = malloc(WIDTH * HEIGHT);
    decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook, labels);
    double t_rec1 = wtime();
"""
new = """    double t_dd0 = wtime();
    double t_dd1 = t_dd0;   /* the inverse delta is part of the container decode below */

    double t_rec0 = wtime();
    uint8_t *reconstructed = malloc(WIDTH * HEIGHT);
    int dec_rc = container_decode(container, container_bytes, reconstructed, CODEBOOK_SIZE, VLEN, BLOCK_SIZE, WIDTH, HEIGHT, NULL);
    double t_rec1 = wtime();

    {   /* untimed cross-check: the image decoded from the container must equal the encoder-side reconstruction */
        labels[0] = labels_delta_u[0];
        for (int i = 1; i < num_vectors; i++)
            labels[i] = labels[i-1] + ((int)labels_delta_u[i] - 128);
        uint8_t *chk_img = (uint8_t *)malloc(WIDTH * HEIGHT);
        decompress_image(chk_img, WIDTH, HEIGHT, BLOCK_SIZE, codebook, labels);
        printf("Container decode check: %s\\n", (dec_rc == 0 && memcmp(chk_img, reconstructed, (size_t)WIDTH * HEIGHT) == 0)
               ? "OK (image decoded from the container is identical to the encoder-side reconstruction)" : "ERROR (mismatch!)");
        free(chk_img);
    }
"""
t = rep(t, old, new)
old = "    fclose(file1);\n"
new = """    fclose(file1);

    {   /* write the real compressed file and verify it by reading it back (not timed) */
        FILE *fc = fopen("compressed.bin", "wb");
        fwrite(container, 1, container_bytes, fc);
        fclose(fc);
        FILE *fr = fopen("compressed.bin", "rb");
        uint8_t *rb = (uint8_t *)malloc(container_bytes); size_t got = fread(rb, 1, container_bytes, fr); fclose(fr);
        uint8_t *rimg = (uint8_t *)malloc(WIDTH * HEIGHT);
        int rrc = container_decode(rb, got, rimg, CODEBOOK_SIZE, VLEN, BLOCK_SIZE, WIDTH, HEIGHT, NULL);
        printf("File round-trip check (compressed.bin, %zu bytes): %s\\n", container_bytes,
               (rrc == 0 && memcmp(rimg, reconstructed, (size_t)WIDTH * HEIGHT) == 0) ? "OK" : "ERROR (mismatch!)");
        free(rb); free(rimg);
    }
"""
t = rep(t, old, new)
t = rep(t, "    free(codebook_data);\n", "    free(codebook_data);\n    free(container);\n")
t = rep(t, "    int compressed_bytes;\n    uint8_t *original;\n    uint8_t *reconstructed;\n} ChannelResult;", "    int compressed_bytes;\n    uint8_t *original;\n    uint8_t *reconstructed;\n    uint8_t *container; size_t container_bytes;\n} ChannelResult;")
old = """    int huff_data_bytes = 0, header_bytes = 0;
    printf("  [%s channel] ", channel_name);
    double tp_h = wtime();
    int huff_total = huffman_on_labels(labels_delta_u, num_vectors, 255,
                                        &huff_data_bytes, &header_bytes);
    res.proc_time += wtime() - tp_h;
    report_huffman_decode_check();

    int codebook_bytes = CODEBOOK_SIZE * VLEN;
    res.compressed_bytes = codebook_bytes + huff_total;
    res.cr_system = (double)original_image_bytes / (double)res.compressed_bytes;

    double tp_r = wtime();
    labels[0] = labels_delta_u[0];
    for (int i = 1; i < num_vectors; i++)
        labels[i] = labels[i-1] + ((int)labels_delta_u[i] - 128);

    uint8_t *reconstructed = malloc(WIDTH * HEIGHT);
    if (!reconstructed) { fprintf(stderr, "malloc failed: reconstructed\\n"); exit(EXIT_FAILURE); }
    decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook, labels);
    res.proc_time += wtime() - tp_r;
"""
new = """    int huff_data_bytes = 0, header_bytes = 0;
    printf("  [%s channel] ", channel_name);
    double tp_h = wtime();
    uint8_t *cb_u8 = (uint8_t *)malloc((size_t)CODEBOOK_SIZE * VLEN);
    for (int i = 0; i < CODEBOOK_SIZE * VLEN; i++) cb_u8[i] = (uint8_t)roundf(codebook[i]);
    res.container = (uint8_t *)malloc(container_capacity(num_vectors, CODEBOOK_SIZE, VLEN));
    res.container_bytes = container_encode(res.container, labels_delta_u, num_vectors, cb_u8, CODEBOOK_SIZE, VLEN,
                                           WIDTH, HEIGHT, &huff_data_bytes, &header_bytes);
    res.proc_time += wtime() - tp_h;
    (void)huff_data_bytes; (void)header_bytes;

    res.compressed_bytes = (int)res.container_bytes;
    res.cr_system = (double)original_image_bytes / (double)res.compressed_bytes;

    double tp_r = wtime();
    uint8_t *reconstructed = malloc(WIDTH * HEIGHT);
    if (!reconstructed) { fprintf(stderr, "malloc failed: reconstructed\\n"); exit(EXIT_FAILURE); }
    int dec_rc = container_decode(res.container, res.container_bytes, reconstructed, CODEBOOK_SIZE, VLEN, BLOCK_SIZE, WIDTH, HEIGHT, NULL);
    res.proc_time += wtime() - tp_r;

    {   /* untimed cross-check against the encoder-side reconstruction */
        labels[0] = labels_delta_u[0];
        for (int i = 1; i < num_vectors; i++)
            labels[i] = labels[i-1] + ((int)labels_delta_u[i] - 128);
        uint8_t *chk_img = (uint8_t *)malloc(WIDTH * HEIGHT);
        decompress_image(chk_img, WIDTH, HEIGHT, BLOCK_SIZE, codebook, labels);
        printf("Container decode check: %s\\n", (dec_rc == 0 && memcmp(chk_img, reconstructed, (size_t)WIDTH * HEIGHT) == 0) ? "OK" : "ERROR (mismatch!)");
        free(chk_img);
    }
    free(cb_u8);
"""
t = rep(t, old, new)
old = """    save_bmp_color("compressed_color.bmp",
                   res_r.reconstructed, res_g.reconstructed, res_b.reconstructed,
                   WIDTH, HEIGHT);
"""
new = old + """
    {   /* write the real compressed file (3 containers back to back) and verify it by reading it back (not timed) */
        ChannelResult *rs[3] = { &res_r, &res_g, &res_b };
        size_t tot = res_r.container_bytes + res_g.container_bytes + res_b.container_bytes;
        FILE *fc = fopen("compressed_color.bin", "wb");
        for (int c = 0; c < 3; c++) fwrite(rs[c]->container, 1, rs[c]->container_bytes, fc);
        fclose(fc);
        FILE *fr = fopen("compressed_color.bin", "rb");
        uint8_t *rb = (uint8_t *)malloc(tot); size_t got = fread(rb, 1, tot, fr); fclose(fr);
        uint8_t *rimg = (uint8_t *)malloc(WIDTH * HEIGHT);
        int ok = 1; size_t off = 0;
        for (int c = 0; c < 3 && ok; c++) {
            size_t used_bytes = 0;
            int rrc = container_decode(rb + off, got - off, rimg, CODEBOOK_SIZE, VLEN, BLOCK_SIZE, WIDTH, HEIGHT, &used_bytes);
            if (rrc != 0 || memcmp(rimg, rs[c]->reconstructed, (size_t)WIDTH * HEIGHT) != 0) ok = 0;
            off += used_bytes;
        }
        printf("File round-trip check (compressed_color.bin, %zu bytes): %s\\n", tot, ok ? "OK" : "ERROR (mismatch!)");
        free(rb); free(rimg);
    }
"""
t = rep(t, old, new)
t = rep(t, "    free(res_r.reconstructed); free(res_g.reconstructed); free(res_b.reconstructed);\n", "    free(res_r.reconstructed); free(res_g.reconstructed); free(res_b.reconstructed);\n    free(res_r.container); free(res_g.container); free(res_b.container);\n")
open("code4.c", "w").write(t)
print("ok")
