/*
 * Quadtree fractal image compressor with block classification, parallelized with OpenMP.
 *
 * Follows the structure of the published pseudo-code (Algorithm 1 and 2 of the quadtree fractal compressor):
 *   Algorithm 1: downsample f -> g; for every depth, classify every domain block and store it in the list LD(c)
 *                of its class c together with its isometry set; then call quadtree(0,0,M,0).
 *   Algorithm 2: quadtree(x,y,M,d): below the minimum depth always subdivide (no flag); otherwise classify the range
 *                block R, compare it only with the domain blocks of the same class (LD(c)) using the isometries
 *                that bring both blocks to the canonical orientation; if best_rms > tol and d < max_d save flag 1 and
 *                subdivide, else save flag 0 (if d < max_d), then s and o, and (s, isometry, domain index) only if s != 0.
 *
 * Details NOT given in the pseudo-code and therefore chosen here (our assumptions):
 *   - classify(): Fisher-style classification on the four quadrants of the block. The isometry (among the 8) that gives the
 *     smallest ordering of the quadrant means defines the canonical orientation (1 or 2 isometries if tied); the class is
 *     (ordering of the means) x (ordering of the quadrant variances in the canonical orientation) -> up to 24 x 24 classes.
 *   - minimum block 16x16 (min_d), maximum depth 4x4 (max_d); domain pool = the 2x2-averaged image, domain blocks of the
 *     same size as the range block on a non-overlapping grid.
 *   - scale s quantized to 5 bits (s = q/32), offset to 7 bits over [-255,255]; flat block (s = 0) stores only s and o.
 *   - cost per leaf = 5 + 7 bits (+ log2(#domains) + 3 bits if s != 0); one split flag per node larger than 4x4.
 *   - compression ratio = 262144 / (ceil(bits/8) + 4 header bytes); decoding = 8 iterations from a constant image.
 * It is a reference implementation written for this work, NOT the authors' code, and does not reproduce their results.
 * The search is deterministic, so the output is identical for any number of threads (checksum printed).
 *
 * Build : gcc -O2 -fopenmp fic_quadtree_class.c -o fic_class -lm
 * Run   : OMP_NUM_THREADS=T ./fic_class image_gray.txt [tol]
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
#define NCLS (24 * 24)

typedef struct { int x, y, r; int dom, iso, sq, oq; } Leaf;
typedef struct { int d; int ng; int g[2]; double Sa, Saa; } DEnt;

static uint8_t img[NMAX];
static float pool[(W / 2) * (H / 2)];
static int perm_tab[8][4];        /* source quadrant of each target quadrant under isometry t */
static int comp_tab[8][8];        /* comp_tab[g][d] = tau with Iso(g)(Iso(tau) X) == Iso(d) X */
static int perm_idx[256];         /* code of a permutation of 0..3 -> 0..23 */
static DEnt *dl[3][NCLS];         /* domain lists per level (r = 16, 8, 4) and class */
static int dl_n[3][NCLS];

static inline int iso_src(int t, int i, int j, int r) {
    int a, b;
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

static void init_tables(void) {
    for (int t = 0; t < 8; t++)
        for (int q = 0; q < 4; q++) {
            int r = 8, i = (q / 2) * 4, j = (q % 2) * 4;
            int s = iso_src(t, i, j, r);
            perm_tab[t][q] = ((s / r) >= 4) * 2 + ((s % r) >= 4);
        }
    int n = 0;
    memset(perm_idx, -1, sizeof perm_idx);
    for (int a = 0; a < 4; a++) for (int b = 0; b < 4; b++) for (int c = 0; c < 4; c++) for (int d = 0; d < 4; d++) {
        if (a == b || a == c || a == d || b == c || b == d || c == d) continue;
        perm_idx[((a * 4 + b) * 4 + c) * 4 + d] = n++;
    }
    int X[16], Y[16], Z[16], U[16];
    for (int i = 0; i < 16; i++) X[i] = i * 7 + 3;
    for (int g = 0; g < 8; g++) for (int d = 0; d < 8; d++) {
        for (int i = 0; i < 4; i++) for (int j = 0; j < 4; j++) Y[i * 4 + j] = X[iso_src(d, i, j, 4)];
        int found = -1;
        for (int t = 0; t < 8 && found < 0; t++) {
            for (int i = 0; i < 4; i++) for (int j = 0; j < 4; j++) Z[i * 4 + j] = X[iso_src(t, i, j, 4)];
            for (int i = 0; i < 4; i++) for (int j = 0; j < 4; j++) U[i * 4 + j] = Z[iso_src(g, i, j, 4)];
            if (memcmp(U, Y, sizeof U) == 0) found = t;
        }
        comp_tab[g][d] = found;
    }
}

/* descending order of 4 values (ties by index) encoded as a permutation code */
static int order_code(const double *v) {
    int p[4] = {0, 1, 2, 3};
    for (int i = 1; i < 4; i++) {
        int k = p[i], j = i - 1;
        while (j >= 0 && v[p[j]] < v[k]) { p[j + 1] = p[j]; j--; }
        p[j + 1] = k;
    }
    return ((p[0] * 4 + p[1]) * 4 + p[2]) * 4 + p[3];
}

/* classify a block (values blk[r*r]); returns class, fills up to two canonical isometries */
static int classify(const double *blk, int r, int *g, int *ng) {
    double mu[4] = {0}, va[4] = {0};
    int h = r / 2;
    for (int q = 0; q < 4; q++) {
        int y0 = (q / 2) * h, x0 = (q % 2) * h;
        double s = 0, ss = 0;
        for (int i = 0; i < h; i++) for (int j = 0; j < h; j++) { double v = blk[(y0 + i) * r + x0 + j]; s += v; ss += v * v; }
        mu[q] = s / (h * h); va[q] = ss / (h * h) - mu[q] * mu[q];
    }
    int code[8], best = 1 << 30;
    for (int t = 0; t < 8; t++) {
        double m2[4];
        for (int q = 0; q < 4; q++) m2[q] = mu[perm_tab[t][q]];
        code[t] = order_code(m2);
        if (code[t] < best) best = code[t];
    }
    *ng = 0;
    for (int t = 0; t < 8 && *ng < 2; t++) if (code[t] == best) g[(*ng)++] = t;
    double v2[4];
    for (int q = 0; q < 4; q++) v2[q] = va[perm_tab[g[0]][q]];
    return perm_idx[best] * 24 + perm_idx[order_code(v2)];
}

static void build_pool(const float *src, float *dst) {
    for (int y = 0; y < H / 2; y++)
        for (int x = 0; x < W / 2; x++)
            dst[y * (W / 2) + x] = 0.25f * (src[(2*y) * W + 2*x] + src[(2*y) * W + 2*x + 1] +
                                            src[(2*y+1) * W + 2*x] + src[(2*y+1) * W + 2*x + 1]);
}

static void build_lists(void) {
    for (int lv = 0; lv < 3; lv++) {
        int r = 16 >> lv, dpr = (W / 2) / r, nd = dpr * dpr;
        int *cls = malloc(sizeof(int) * nd), *gg = malloc(sizeof(int) * nd * 2), *ngg = malloc(sizeof(int) * nd);
        double *Sa = malloc(sizeof(double) * nd), *Saa = malloc(sizeof(double) * nd);
        memset(dl_n[lv], 0, sizeof dl_n[lv]);
        for (int d = 0; d < nd; d++) {
            double blk[256]; int dy = (d / dpr) * r, dx = (d % dpr) * r; double s = 0, ss = 0;
            for (int i = 0; i < r; i++) for (int j = 0; j < r; j++) { double v = pool[(dy + i) * (W / 2) + dx + j]; blk[i * r + j] = v; s += v; ss += v * v; }
            Sa[d] = s; Saa[d] = ss;
            cls[d] = classify(blk, r, &gg[2 * d], &ngg[d]);
            dl_n[lv][cls[d]]++;
        }
        for (int c = 0; c < NCLS; c++) { dl[lv][c] = dl_n[lv][c] ? malloc(sizeof(DEnt) * dl_n[lv][c]) : NULL; dl_n[lv][c] = 0; }
        for (int d = 0; d < nd; d++) {
            DEnt *e = &dl[lv][cls[d]][dl_n[lv][cls[d]]++];
            e->d = d; e->ng = ngg[d]; e->g[0] = gg[2 * d]; e->g[1] = gg[2 * d + 1]; e->Sa = Sa[d]; e->Saa = Saa[d];
        }
        free(cls); free(gg); free(ngg); free(Sa); free(Saa);
    }
}

static inline void quant(double s, double Sa, double Sb, int n, int *sq, int *oq, double *sv, double *ov) {
    int q = (int)floor(s * 32.0 + 0.5); if (q < 0) q = 0; if (q > 31) q = 31;
    *sq = q; *sv = q / 32.0;
    double o = (Sb - *sv * Sa) / n;
    int p = (int)floor((o + 255.0) / 510.0 * 127.0 + 0.5); if (p < 0) p = 0; if (p > 127) p = 127;
    *oq = p; *ov = p * 510.0 / 127.0 - 255.0;
}

static double encode_block(int x, int y, int r, int lv, Leaf *out) {
    const int n = r * r;
    double b[256], Sb = 0, Sbb = 0;
    for (int i = 0; i < r; i++) for (int j = 0; j < r; j++) { double v = img[(y + i) * W + x + j]; b[i * r + j] = v; Sb += v; Sbb += v * v; }
    int gR[2], ngR, c = classify(b, r, gR, &ngR);
    /* flat candidate (s = 0) */
    int sq0, oq0; double sv0, ov0;
    quant(0.0, 0.0, Sb, n, &sq0, &oq0, &sv0, &ov0);
    double best = Sbb + n * ov0 * ov0 - 2 * ov0 * Sb;
    int bd = 0, bt = 0, bsq = 0, boq = oq0;
    const int dpr = (W / 2) / r;
    for (int k = 0; k < dl_n[lv][c]; k++) {
        DEnt *e = &dl[lv][c][k];
        int dy = (e->d / dpr) * r, dx = (e->d % dpr) * r;
        double a[256];
        for (int i = 0; i < r; i++) for (int j = 0; j < r; j++) a[i * r + j] = pool[(dy + i) * (W / 2) + dx + j];
        for (int gi = 0; gi < ngR; gi++) for (int di = 0; di < e->ng; di++) {
            int t = comp_tab[gR[gi]][e->g[di]];
            double Sab = 0;
            for (int i = 0; i < r; i++) for (int j = 0; j < r; j++) Sab += a[iso_src(t, i, j, r)] * b[i * r + j];
            double den = n * e->Saa - e->Sa * e->Sa, s = 0.0;
            if (den > 1e-9) s = (n * Sab - e->Sa * Sb) / den;
            int sq, oq; double sv, ov;
            quant(s, e->Sa, Sb, n, &sq, &oq, &sv, &ov);
            double err = Sbb + sv * sv * e->Saa + n * ov * ov - 2 * sv * Sab - 2 * ov * Sb + 2 * sv * ov * e->Sa;
            if (err < best) { best = err; bd = e->d; bt = t; bsq = sq; boq = oq; }
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
    while (cnt < NMAX && fscanf(f, "%d", &v) == 1) img[cnt++] = (uint8_t)(v < 0 ? 0 : v > 255 ? 255 : v);
    fclose(f);
    if (cnt != NMAX) { fprintf(stderr, "expected %d pixels, got %d\n", NMAX, cnt); return 1; }
    init_tables();

    int cap = (W / 4) * (H / 4);
    Leaf *leaves = malloc(sizeof(Leaf) * cap), *tmp = malloc(sizeof(Leaf) * cap);
    int *cur = malloc(sizeof(int) * 2 * cap), *nxt = malloc(sizeof(int) * 2 * cap);
    unsigned char *acc = malloc(cap);
    int nleaves = 0; long long bits = 0;

    double t0 = omp_get_wtime();
    {
        float *fimg = malloc(sizeof(float) * NMAX);
        for (int i = 0; i < NMAX; i++) fimg[i] = img[i];
        build_pool(fimg, pool); free(fimg);
    }
    build_lists();                                           /* Algorithm 1: classify all domain blocks */
    int ncur = 0;
    for (int y = 0; y < H; y += 16) for (int x = 0; x < W; x += 16) { cur[2*ncur] = x; cur[2*ncur+1] = y; ncur++; }
    for (int lv = 0, r = 16; r >= 4 && ncur > 0; lv++, r /= 2) {
        int dpr = (W / 2) / r, dbits = (int)ceil(log2((double)(dpr * dpr)));
        #pragma omp parallel for schedule(dynamic, 1)
        for (int k = 0; k < ncur; k++) {
            double e = encode_block(cur[2*k], cur[2*k+1], r, lv, &tmp[k]);
            acc[k] = (r == 4 || e <= tol) ? 1 : 0;
        }
        int nn = 0;
        for (int k = 0; k < ncur; k++) {
            if (r > 4) bits += 1;
            if (acc[k]) { leaves[nleaves++] = tmp[k]; bits += 5 + 7 + (tmp[k].sq ? dbits + 3 : 0); }
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
            for (int i = 0; i < r; i++) for (int j = 0; j < r; j++) {
                double val = ov;
                if (L->sq) { int s = iso_src(L->iso, i, j, r); val += sv * pool[(dy + s / r) * (W / 2) + dx + s % r]; }
                if (val < 0) val = 0;
                if (val > 255) val = 255;
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
