#!/usr/bin/env python3
"""Build the optional v5 (fast I/O) programs from the approved final sources.
Only file reading/writing is replaced; algorithm, results and every output file stay byte-identical."""
import re, sys

HELPERS = r'''
/* ===================== [V5] fast text I/O (outputs byte-identical) =====================
   The approved version reads the image with fscanf("%d") and writes the reconstruction with
   fprintf("%u\n") one value at a time, and writes colour BMP pixels with 786,432 tiny fwrite calls.
   These steps run on Rank 0 only, so they are the serial part (Amdahl) of the whole program.
   Here the file is read in one fread and parsed by hand; text/BMP output is formatted into one buffer
   and written with one fwrite. */
static char *v5_slurp(const char *filename, size_t *len)
{
    FILE *f = fopen(filename, "rb");
    if (!f) { perror("Error opening image file"); return NULL; }
    fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, 0, SEEK_SET);
    if (sz < 0) { fclose(f); return NULL; }
    char *buf = (char *)malloc((size_t)sz + 1);
    if (!buf) { fclose(f); return NULL; }
    size_t got = fread(buf, 1, (size_t)sz, f);
    fclose(f);
    buf[got] = '\0'; *len = got;
    return buf;
}
/* same token rule as fscanf("%d"): skip white space, optional sign, digits; returns 0 at end/non-number */
static int v5_next_int(const char **pp, const char *end, int *out)
{
    const char *p = *pp;
    while (p < end && (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t' || *p == '\v' || *p == '\f')) p++;
    if (p >= end) { *pp = p; return 0; }
    int neg = 0;
    if (*p == '-') { neg = 1; p++; } else if (*p == '+') p++;
    if (p >= end || *p < '0' || *p > '9') { *pp = p; return 0; }
    long v = 0;
    while (p < end && *p >= '0' && *p <= '9') { if (v < 100000000L) v = v * 10 + (*p - '0'); p++; }
    *pp = p; *out = neg ? (int)-v : (int)v;
    return 1;
}
static void v5_write_u8_txt(const char *filename, const uint8_t *a, size_t n)
{
    FILE *f = fopen(filename, "w");
    if (!f) { perror(filename); return; }
    char *buf = (char *)malloc(n * 4 + 1);
    if (!buf) { fclose(f); return; }
    size_t k = 0;
    for (size_t i = 0; i < n; i++) {
        unsigned v = a[i];
        if (v >= 100) { buf[k++] = (char)('0' + v / 100); buf[k++] = (char)('0' + (v / 10) % 10); buf[k++] = (char)('0' + v % 10); }
        else if (v >= 10) { buf[k++] = (char)('0' + v / 10); buf[k++] = (char)('0' + v % 10); }
        else buf[k++] = (char)('0' + v);
        buf[k++] = '\n';
    }
    fwrite(buf, 1, k, f);
    fclose(f); free(buf);
}
'''

READ_GRAY = r'''int read_image_from_txt(const char *filename, uint8_t *image, int width, int height) {
    size_t len = 0;
    char *buf = v5_slurp(filename, &len);
    if (!buf) return 0;
    const char *p = buf, *end = buf + len;
    int val, count = 0;
    while (count < width * height && v5_next_int(&p, end, &val)) {
        if (val < 0) val = 0;
        if (val > 255) val = 255;
        image[count++] = (uint8_t)val;
    }
    free(buf);
    if (count != width * height) {
        fprintf(stderr, "Warning: Expected %d pixels, got %d\n", width * height, count);
    }
    return count == width * height;
}
'''
READ_COLOR = r'''int read_color_image_from_txt(const char *filename,
                               uint8_t *R, uint8_t *G, uint8_t *B,
                               int width, int height)
{
    size_t len = 0;
    char *buf = v5_slurp(filename, &len);
    if (!buf) return 0;
    const char *p = buf, *end = buf + len;
    int r, g, b, count = 0;
    while (count < width * height && v5_next_int(&p, end, &r) && v5_next_int(&p, end, &g) && v5_next_int(&p, end, &b)) {
        if (r < 0) r = 0;
        if (r > 255) r = 255;
        if (g < 0) g = 0;
        if (g > 255) g = 255;
        if (b < 0) b = 0;
        if (b > 255) b = 255;
        R[count] = (uint8_t)r; G[count] = (uint8_t)g; B[count] = (uint8_t)b;
        count++;
    }
    free(buf);
    if (count != width * height) {
        fprintf(stderr, "Warning: Expected %d pixels, got %d\n", width * height, count);
    }
    return count == width * height;
}
'''
DETECT = r'''static ImgMode detect_mode_from_file(const char *path)
{
    size_t len = 0;
    char *buf = v5_slurp(path, &len);
    if (!buf) return MODE_UNKNOWN;
    const char *p = buf, *end = buf + len;
    long count = 0;
    int val;
    while (v5_next_int(&p, end, &val)) count++;
    free(buf);

    long gray_expect  = (long)WIDTH * HEIGHT;
    long color_expect = (long)WIDTH * HEIGHT * 3;
    if (count == gray_expect)  return MODE_GRAY;
    if (count == color_expect) return MODE_COLOR;
    return MODE_UNKNOWN;
}
'''
BMP_COLOR_LOOP_OLD = r'''    uint8_t pad[3] = {0, 0, 0};
    for (int y = height - 1; y >= 0; y--) {
        for (int x = 0; x < width; x++) {
            int idx = y * width + x;
            uint8_t pixel[3] = { B[idx], G[idx], R[idx] };
            fwrite(pixel, 1, 3, f);
        }
        if (row_padded - row_bytes > 0)
            fwrite(pad, 1, row_padded - row_bytes, f);
    }
    fclose(f);'''
BMP_COLOR_LOOP_NEW = r'''    uint8_t *rowbuf = (uint8_t *)calloc((size_t)row_padded, 1);
    for (int y = height - 1; y >= 0; y--) {
        for (int x = 0; x < width; x++) {
            int idx = y * width + x;
            rowbuf[3 * x] = B[idx]; rowbuf[3 * x + 1] = G[idx]; rowbuf[3 * x + 2] = R[idx];
        }
        fwrite(rowbuf, 1, (size_t)row_padded, f);
    }
    free(rowbuf);
    fclose(f);'''

def cut(src, start_pat, repl):
    """replace the C function that starts with start_pat (up to its closing brace at column 0)"""
    i = src.index(start_pat)
    j = src.index("\n}\n", i) + 3
    return src[:i] + repl + src[j:]

def build(inp, out, wr_old):
    s = open(inp).read()
    # helpers right before the first reader
    k = s.index("int read_image_from_txt")
    s = s[:k] + HELPERS + "\n" + s[k:]
    s = cut(s, "int read_image_from_txt", READ_GRAY)
    s = cut(s, "int read_color_image_from_txt", READ_COLOR)
    s = cut(s, "static ImgMode detect_mode_from_file", DETECT)
    old = BMP_COLOR_LOOP_OLD
    if old not in s:
        old = old.replace("fwrite(pixel, 1, 3, f);", "fwrite(pixel, 1, 3, f);").replace("{ B[idx], G[idx], R[idx] };", "{ B[idx], G[idx], R[idx] };  /* BMP stores B,G,R */")
    assert old in s
    s = s.replace(old, BMP_COLOR_LOOP_NEW)
    for old, new in wr_old:
        assert old in s, old
        s = s.replace(old, new)
    s = s.replace("/*", "/* [V5 fast-I/O build of the approved final program; see make_v5.py]\n *\n *", 1) if False else s
    open(out, "w").write(s)

WR_PAM = [
 ('''        FILE *flbg = fopen("lbg_decompress.txt", "w");
        for (size_t i = 0; i < (size_t)(WIDTH*HEIGHT); i++)
            fprintf(flbg, "%u\\n", reconstructed_lbg[i]);
        fclose(flbg);''', '''        v5_write_u8_txt("lbg_decompress.txt", reconstructed_lbg, (size_t)(WIDTH*HEIGHT));'''),
 ('''        FILE *file1 = fopen("decompress.txt", "w");
        for (size_t i = 0; i < (size_t)(WIDTH*HEIGHT); i++)
            fprintf(file1, "%u\\n", reconstructed[i]);
        fclose(file1);''', '''        v5_write_u8_txt("decompress.txt", reconstructed, (size_t)(WIDTH*HEIGHT));'''),
]
WR_SEM = [
 ("""    FILE *flbg = fopen("lbg_decompress.txt", "w");
    for (size_t i = 0; i < (size_t)WIDTH * HEIGHT; i++)
        fprintf(flbg, "%u\\n", reconstructed_lbg[i]);
    fclose(flbg);""", """    v5_write_u8_txt("lbg_decompress.txt", reconstructed_lbg, (size_t)WIDTH * HEIGHT);"""),
 ("""    FILE *file1 = fopen("decompress.txt", "w");
    for (size_t i = 0; i < (size_t)WIDTH*HEIGHT; i++)
        fprintf(file1, "%u\\n", reconstructed[i]);
    fclose(file1);""", """    v5_write_u8_txt("decompress.txt", reconstructed, (size_t)WIDTH*HEIGHT);"""),
]
if __name__ == "__main__":
    build("pam_v4_nofilter_final.c", "pam_v5_fastio.c", WR_PAM)
    build("sem_v3_nofilter_final.c", "sem_v5_fastio.c", WR_SEM)
    print("ok")
