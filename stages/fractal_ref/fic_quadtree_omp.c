/*
 * Reference fractal image compressor with quadtree partition, parallelized with OpenMP.
 *
 * PURPOSE: a reference implementation WRITTEN FROM THE PUBLISHED DESCRIPTIONS (not the authors' code) so that a
 * fractal-compression baseline can be run on the same machine and the same images as the LBG programs.
 * It follows the general scheme of quadtree fractal compression with task/loop parallelism over range blocks
 * (cf. Hernandez-Lopez and Muniz-Perez, J. Real-Time Image Proc. 2022).  It is NOT a reproduction of their code
 * and must be described as "our implementation based on the description in [ref]".
 *
 * Scheme
 *   - image 512x512 gray (plain-text file, one integer per pixel, same format as the LBG programs)
 *   - range blocks 16x16 -> split to 8x8 -> split to 4x4 (quadtree); a block is accepted when its RMS error <= tol
 *     (4x4 blocks are always accepted)
 *   - domain pool: the image averaged 2x2 (256x256); domain blocks of the same size as the range block on a
 *     non-overlapping grid (so a 16x16 range block searches 16*16 = 256 domain blocks, 8x8 -> 1024, 4x4 -> 4096)
 *   - 8 isometries; scale s quantized to 5 bits (s = q/32, 0..31/32), offset quantized to 7 bits over [-255,255]
 *   - cost per leaf = log2(#domains) + 3 + 5 + 7 bits, plus one split flag per quadtree node of size > 4
 *   - compression ratio = 262144 / (ceil(bits/8) + 4 header bytes)
 *   - decoding: 8 iterations from a constant 128 image
 *   - the search is deterministic (ties -> lowest domain/isometry index), so the result is identical for any
 *     number of threads; the printed checksum lets this be verified.
 *
 * Build : gcc -O2 -fopenmp fic_quadtree_omp.c -o fic -lm
 * Run   : OMP_NUM_THREADS=T ./fic image_gray.txt [tol]        (default tol = 10)
 * Prints: ET (encoding time), DT (decoding time), CR, PSNR, number of leaves, checksum.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <omp.h>

#define W 512
#define H 512
#define NMAX (W * H)

typedef struct { int x, y, r; int dom, iso, sq, oq; } Leaf;

static uint8_t img[NMAX];
static float   pool[(W / 2) * (H / 2)];      /* 2x2-averaged image (256 x 256) */

/* source index inside an r x r block for isometry t and target position (i,j) */
static inline int iso_src(int t, int i, int j, int r) {
    int a = i, b = j;
    switch (t) {
        case 0: a = i;         b = j;         break;
        case 1: a = i;         b = r - 1 - j; break;
        case 2: a = r - 1 - i; b = j;         break;
        case 3: a = r - 1 - i; b = r - 1 - j; break;
        case 4: a = j;         b = i;         break;
        case 5: a = j;         b = r - 1 - i; break;
        case 6: a = r - 1 - j; b = i;         break;
        default: a = r - 1 - j; b = r - 1 - i; break;
    }
    return a * r + b;
}

static void build_pool(const float *src, float *dst) {
    for (int y = 0; y < H / 2; y++)
        for (int x = 0; x < W / 2; x++)
            dst[y * (W / 2) + x] = 0.25f * (src[(2*y) * W + 2*x] + src[(2*y) * W + 2*x + 1] +
                                            src[(2*y+1) * W + 2*x] + src[(2*y+1) * W + 2*x + 1]);
}

/* best domain/isometry/scale/offset for the range block (x,y,r); returns RMS error */
static double encode_block(int x, int y, int r, Leaf *out) {
    const int n = r * r;
    double b[256];
    double Sb = 0, Sbb = 0;
    for (int i = 0; i < r; i++)
        for (int j = 0; j < r; j++) {
            double v = img[(y + i) * W + (x + j)];
            b[i * r + j] = v; Sb += v; Sbb += v * v;
        }
    const int dpr = (W / 2) / r;             /* domains per row/column */
    double best = 1e300; int bd = 0, bt = 0, bsq = 0, boq = 0;
    for (int d = 0; d < dpr * dpr; d++) {
        int dy = (d / dpr) * r, dx = (d % dpr) * r;
        double a[256], Sa = 0, Saa = 0;
        for (int i = 0; i < r; i++)
            for (int j = 0; j < r; j++) {
                double v = pool[(dy + i) * (W / 2) + dx + j];
                a[i * r + j] = v; Sa += v; Saa += v * v;
            }
        for (int t = 0; t < 8; t++) {
            double Sab = 0;
            for (int i = 0; i < r; i++)
                for (int j = 0; j < r; j++)
                    Sab += a[iso_src(t, i, j, r)] * b[i * r + j];
            double den = n * Saa - Sa * Sa, s = 0.0;
            if (den > 1e-9) s = (n * Sab - Sa * Sb) / den;
            int sq = (int)floor(s * 32.0 + 0.5);
            if (sq < 0) sq = 0; if (sq > 31) sq = 31;
            double sv = sq / 32.0;
            double o = (Sb - sv * Sa) / n;
            int oq = (int)floor((o + 255.0) / 510.0 * 127.0 + 0.5);
            if (oq < 0) oq = 0; if (oq > 127) oq = 127;
            double ov = oq * 510.0 / 127.0 - 255.0;
            double err = Sbb + sv * sv * Saa + n * ov * ov - 2 * sv * Sab - 2 * ov * Sb + 2 * sv * ov * Sa;
            if (err < best) { best = err; bd = d; bt = t; bsq = sq; boq = oq; }
        }
    }
    out->x = x; out->y = y; out->r = r; out->dom = bd; out->iso = bt; out->sq = bsq; out->oq = boq;
    return sqrt(best > 0 ? best / n : 0.0);
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: %s image_gray.txt [tol]\n", argv[0]); return 1; }
    double tol = (argc > 2) ? atof(argv[2]) : 10.0;
    FILE *f = fopen(argv[1], "r");
    if (!f) { perror("image"); return 1; }
    int v, cnt = 0;
    while (cnt < NMAX && fscanf(f, "%d", &v) == 1) { img[cnt++] = (uint8_t)(v < 0 ? 0 : v > 255 ? 255 : v); }
    fclose(f);
    if (cnt != NMAX) { fprintf(stderr, "expected %d pixels, got %d\n", NMAX, cnt); return 1; }

    /* ---------------- encoding ---------------- */
    int cap = (W / 4) * (H / 4);
    Leaf *leaves = malloc(sizeof(Leaf) * cap);
    int nleaves = 0;
    long long bits = 0;
    int *cur = malloc(sizeof(int) * 2 * cap), *nxt = malloc(sizeof(int) * 2 * cap);   /* x,y pairs */
    Leaf *tmp = malloc(sizeof(Leaf) * cap);
    unsigned char *acc = malloc(cap);

    double t0 = omp_get_wtime();
    {
        float *fimg = malloc(sizeof(float) * NMAX);
        for (int i = 0; i < NMAX; i++) fimg[i] = img[i];
        build_pool(fimg, pool);
        free(fimg);
    }
    int ncur = 0;
    for (int y = 0; y < H; y += 16) for (int x = 0; x < W; x += 16) { cur[2*ncur] = x; cur[2*ncur+1] = y; ncur++; }
    for (int r = 16; r >= 4 && ncur > 0; r /= 2) {
        int dpr = (W / 2) / r, ndom = dpr * dpr;
        int dbits = (int)ceil(log2((double)ndom));
        #pragma omp parallel for schedule(dynamic, 1)
        for (int k = 0; k < ncur; k++) {
            double e = encode_block(cur[2*k], cur[2*k+1], r, &tmp[k]);
            acc[k] = (r == 4 || e <= tol) ? 1 : 0;
        }
        int nn = 0;
        for (int k = 0; k < ncur; k++) {                    /* sequential, deterministic order */
            if (r > 4) bits += 1;                           /* split flag */
            if (acc[k]) { leaves[nleaves++] = tmp[k]; bits += dbits + 3 + 5 + 7; }
            else {
                int x = cur[2*k], y = cur[2*k+1], h = r / 2;
                nxt[2*nn] = x;     nxt[2*nn+1] = y;     nn++;
                nxt[2*nn] = x + h; nxt[2*nn+1] = y;     nn++;
                nxt[2*nn] = x;     nxt[2*nn+1] = y + h; nn++;
                nxt[2*nn] = x + h; nxt[2*nn+1] = y + h; nn++;
            }
        }
        int *sw = cur; cur = nxt; nxt = sw; ncur = nn;
    }
    double ET = omp_get_wtime() - t0;

    /* ---------------- decoding ---------------- */
    float *dec = malloc(sizeof(float) * NMAX), *nw = malloc(sizeof(float) * NMAX);
    double t1 = omp_get_wtime();
    for (int i = 0; i < NMAX; i++) dec[i] = 128.0f;
    for (int it = 0; it < 8; it++) {
        build_pool(dec, pool);
        #pragma omp parallel for schedule(static)
        for (int k = 0; k < nleaves; k++) {
            Leaf *L = &leaves[k];
            int r = L->r, dpr = (W / 2) / r;
            int dy = (L->dom / dpr) * r, dx = (L->dom % dpr) * r;
            double sv = L->sq / 32.0, ov = L->oq * 510.0 / 127.0 - 255.0;
            for (int i = 0; i < r; i++)
                for (int j = 0; j < r; j++) {
                    int s = iso_src(L->iso, i, j, r);
                    double val = sv * pool[(dy + s / r) * (W / 2) + dx + s % r] + ov;
                    if (val < 0) val = 0; if (val > 255) val = 255;
                    nw[(L->y + i) * W + L->x + j] = (float)val;
                }
        }
        float *sw = dec; dec = nw; nw = sw;
    }
    double DT = omp_get_wtime() - t1;

    double mse = 0;
    for (int i = 0; i < NMAX; i++) { double d = img[i] - floor(dec[i] + 0.5); mse += d * d; }
    mse /= NMAX;
    double psnr = mse > 0 ? 10.0 * log10(255.0 * 255.0 / mse) : 99.0;
    long long bytes = (bits + 7) / 8 + 4;
    unsigned long long h = 1469598103934665603ULL;
    for (int k = 0; k < nleaves; k++) {
        unsigned long long z = ((unsigned long long)leaves[k].x << 40) ^ ((unsigned long long)leaves[k].y << 28) ^
                               ((unsigned long long)leaves[k].r << 20) ^ ((unsigned long long)leaves[k].dom << 8) ^
                               ((unsigned long long)leaves[k].iso << 5) ^ (unsigned long long)leaves[k].sq ^
                               ((unsigned long long)leaves[k].oq << 52);
        h = (h ^ z) * 1099511628211ULL;
    }
    printf("threads=%d tol=%.1f leaves=%d bytes=%lld CR=%.2f PSNR=%.2f ET=%.4f DT=%.4f checksum=%016llx\n",
           omp_get_max_threads(), tol, nleaves, bytes, (double)NMAX / bytes, psnr, ET, DT, h);
    return 0;
}
