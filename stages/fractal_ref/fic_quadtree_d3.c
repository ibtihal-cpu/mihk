/*
 * Quadtree fractal image compressor following the description of Hernandez-Lopez and Munoz-Perez (J. Real-Time
 * Image Process. 19:391-402, 2022), with the experimental settings of their Table 3/4 for 512 x 512 images:
 *   - domain library D3 with lattice spacing l = 1 (every position, overlapping domains), taken from the four
 *     domain images g1..g4 obtained by averaging 2 x 2 pixel groups at the four odd/even locations (Algorithm 1);
 *   - minimum depth min_d = 4 and maximum depth max_d = 8, i.e. range blocks from 32 x 32 down to 2 x 2 pixels;
 *   - Fisher classification (72 major classes by the ordering of the quadrant means and variances) with both
 *     orientations of the scaling sign; a range is compared only with the domains of its class (Algorithm 2);
 *   - bit allocation: 1 split bit per node above max_d, 5 bits for the scaling, 7 bits for the offset, 3 bits for the
 *     isometry and ceil(log2(#domains of the level)) bits for the domain index; s = 0 stores only s and o.
 * Parallelization: OpenMP parallel loops over the classification of the domain library and over the range blocks of each
 * quadtree level (NOT the task-parallel scheme or the GPU version of the paper).
 *
 * Details that the paper does not give and that are chosen here (our assumptions): the quantization range of the scaling
 * (s = (q - 15) / 16, q = 0..31) and of the offset (7 bits over [-255, 510]); the definition of the canonical isometry used
 * in the classification; the decoding (8 iterations starting from a constant image); the border handling of the shifted
 * domain images (clamping). It is a reference implementation written for this work, NOT the code of the authors.
 * The search is deterministic, so the output is identical for any number of threads (checksum printed).
 *
 * Build : gcc -O2 -fopenmp fic_quadtree_d3.c -o fic_d3 -lm
 * Run   : OMP_NUM_THREADS=T ./fic_d3 image_gray.txt [tol]
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <omp.h>

#define W 512
#define H 512
#define G (W / 2)                 /* size of a domain image */
#define NMAX (W * H)
#define NCLS (24 * 24)
#define NLV 5                     /* ranges 32, 16, 8, 4, 2 */
#define RMAX 32

typedef struct { int x, y, r; int dom, iso, sq, oq; } Leaf;
typedef struct { int id; int ng; int g[2]; double Sa, Saa; } DEnt;

static uint8_t img[NMAX];
static float gimg[4][G * G];          /* the four domain images */
static int perm_tab[8][4];
static int comp_tab[8][8];
static int perm_idx[256];
static DEnt *dl[NLV][NCLS];
static int dl_n[NLV][NCLS];
static int nd_lv[NLV];

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

static int order_code(const double *v) {
    int p[4] = {0, 1, 2, 3};
    for (int i = 1; i < 4; i++) {
        int k = p[i], j = i - 1;
        while (j >= 0 && v[p[j]] < v[k]) { p[j + 1] = p[j]; j--; }
        p[j + 1] = k;
    }
    return ((p[0] * 4 + p[1]) * 4 + p[2]) * 4 + p[3];
}

/* classify a block blk[r*r]; fills up to two canonical isometries */
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

/* Algorithm 1, step 1: four domain images from 2x2 averages at the four odd/even locations */
static void build_domain_images(const float *src) {
    for (int k = 0; k < 4; k++) {
        int oy = k / 2, ox = k % 2;
        #pragma omp parallel for schedule(static)
        for (int y = 0; y < G; y++)
            for (int x = 0; x < G; x++) {
                int y0 = 2 * y + oy, x0 = 2 * x + ox;
                int y1 = y0 + 1 < H ? y0 + 1 : H - 1, x1 = x0 + 1 < W ? x0 + 1 : W - 1;
                if (y0 >= H) y0 = H - 1;
                if (x0 >= W) x0 = W - 1;
                gimg[k][y * G + x] = 0.25f * (src[y0 * W + x0] + src[y0 * W + x1] + src[y1 * W + x0] + src[y1 * W + x1]);
            }
    }
}

/* Algorithm 1, steps 2-8: classify every domain of the library D3 (spacing l = 1) of every level */
static void build_lists(void) {
    for (int lv = 0; lv < NLV; lv++) {
        int r = RMAX >> lv, np = G - r + 1;
        int nd = 4 * np * np; nd_lv[lv] = nd;
        int *cls = malloc(sizeof(int) * nd), *gg = malloc(sizeof(int) * nd * 2), *ngg = malloc(sizeof(int) * nd);
        double *Sa = malloc(sizeof(double) * nd), *Saa = malloc(sizeof(double) * nd);
        memset(dl_n[lv], 0, sizeof dl_n[lv]);
        #pragma omp parallel for schedule(static)
        for (int d = 0; d < nd; d++) {
            int k = d / (np * np), p = d % (np * np), gy = p / np, gx = p % np;
            double blk[RMAX * RMAX]; double s = 0, ss = 0;
            for (int i = 0; i < r; i++) for (int j = 0; j < r; j++) { double v = gimg[k][(gy + i) * G + gx + j]; blk[i * r + j] = v; s += v; ss += v * v; }
            Sa[d] = s; Saa[d] = ss;
            cls[d] = classify(blk, r, &gg[2 * d], &ngg[d]);
        }
        for (int d = 0; d < nd; d++) dl_n[lv][cls[d]]++;
        for (int c = 0; c < NCLS; c++) { dl[lv][c] = dl_n[lv][c] ? malloc(sizeof(DEnt) * dl_n[lv][c]) : NULL; dl_n[lv][c] = 0; }
        for (int d = 0; d < nd; d++) {
            DEnt *e = &dl[lv][cls[d]][dl_n[lv][cls[d]]++];
            e->id = d; e->ng = ngg[d]; e->g[0] = gg[2 * d]; e->g[1] = gg[2 * d + 1]; e->Sa = Sa[d]; e->Saa = Saa[d];
        }
        free(cls); free(gg); free(ngg); free(Sa); free(Saa);
    }
}

/* s = (q - 15) / 16 (q = 0..31); o over [-255, 510] with 7 bits */
static inline void quant(double s, double Sa, double Sb, int n, int *sq, int *oq, double *sv, double *ov) {
    int q = (int)floor(s * 16.0 + 15.0 + 0.5); if (q < 0) q = 0; if (q > 31) q = 31;
    *sq = q; *sv = (q - 15) / 16.0;
    double o = (Sb - *sv * Sa) / n;
    int p = (int)floor((o + 255.0) / 765.0 * 127.0 + 0.5); if (p < 0) p = 0; if (p > 127) p = 127;
    *oq = p; *ov = p * 765.0 / 127.0 - 255.0;
}

static inline double s_value(int q) { return (q - 15) / 16.0; }
static inline double o_value(int p) { return p * 765.0 / 127.0 - 255.0; }

static double encode_block(int x, int y, int r, int lv, Leaf *out) {
    const int n = r * r;
    double b[RMAX * RMAX], bb[RMAX * RMAX], Sb = 0, Sbb = 0;
    for (int i = 0; i < r; i++) for (int j = 0; j < r; j++) { double v = img[(y + i) * W + x + j]; b[i * r + j] = v; Sb += v; Sbb += v * v; }
    int sq0, oq0; double sv0, ov0;
    quant(0.0, 0.0, Sb, n, &sq0, &oq0, &sv0, &ov0);
    double best = Sbb + n * ov0 * ov0 - 2 * ov0 * Sb;      /* candidate s != 0 only if it is better; flat = quantized zero */
    int bd = 0, bt = 0, bsq = sq0, boq = oq0, flat = 1;
    const int np = G - r + 1;
    for (int mode = 0; mode < 2; mode++) {                  /* mode 1: orientation of the negative scaling */
        for (int i = 0; i < n; i++) bb[i] = mode ? 255.0 - b[i] : b[i];
        int gR[2], ngR, c = classify(bb, r, gR, &ngR);
        for (int kk = 0; kk < dl_n[lv][c]; kk++) {
            DEnt *e = &dl[lv][c][kk];
            int k = e->id / (np * np), p = e->id % (np * np), gy = p / np, gx = p % np;
            double a[RMAX * RMAX];
            for (int i = 0; i < r; i++) for (int j = 0; j < r; j++) a[i * r + j] = gimg[k][(gy + i) * G + gx + j];
            for (int gi = 0; gi < ngR; gi++) for (int di = 0; di < e->ng; di++) {
                int t = comp_tab[gR[gi]][e->g[di]];
                double Sab = 0;
                for (int i = 0; i < r; i++) for (int j = 0; j < r; j++) Sab += a[iso_src(t, i, j, r)] * b[i * r + j];
                double den = n * e->Saa - e->Sa * e->Sa, s = 0.0;
                if (den > 1e-9) s = (n * Sab - e->Sa * Sb) / den;
                int sq, oq; double sv, ov;
                quant(s, e->Sa, Sb, n, &sq, &oq, &sv, &ov);
                if (sq == 15) continue;                     /* quantized zero: same as the flat candidate */
                double err = Sbb + sv * sv * e->Saa + n * ov * ov - 2 * sv * Sab - 2 * ov * Sb + 2 * sv * ov * e->Sa;
                if (err < best) { best = err; bd = e->id; bt = t; bsq = sq; boq = oq; flat = 0; }
            }
        }
    }
    out->x = x; out->y = y; out->r = r; out->dom = bd; out->iso = bt; out->sq = bsq; out->oq = boq;
    (void)flat;
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

    int cap = (W / 2) * (H / 2);
    Leaf *leaves = malloc(sizeof(Leaf) * cap), *tmp = malloc(sizeof(Leaf) * cap);
    int *cur = malloc(sizeof(int) * 2 * cap), *nxt = malloc(sizeof(int) * 2 * cap);
    unsigned char *acc = malloc(cap);
    int nleaves = 0; long long bits = 0;

    double t0 = omp_get_wtime();
    {
        float *fimg = malloc(sizeof(float) * NMAX);
        for (int i = 0; i < NMAX; i++) fimg[i] = img[i];
        build_domain_images(fimg); free(fimg);
    }
    build_lists();                                           /* Algorithm 1 */
    int ncur = 0;
    for (int y = 0; y < H; y += RMAX) for (int x = 0; x < W; x += RMAX) { cur[2*ncur] = x; cur[2*ncur+1] = y; ncur++; }
    for (int lv = 0, r = RMAX; lv < NLV && ncur > 0; lv++, r /= 2) {
        int dbits = (int)ceil(log2((double)nd_lv[lv]));
        #pragma omp parallel for schedule(dynamic, 1)
        for (int k = 0; k < ncur; k++) {
            double e = encode_block(cur[2*k], cur[2*k+1], r, lv, &tmp[k]);
            acc[k] = (lv == NLV - 1 || e <= tol) ? 1 : 0;
        }
        int nn = 0;
        for (int k = 0; k < ncur; k++) {
            if (lv < NLV - 1) bits += 1;
            if (acc[k]) { leaves[nleaves++] = tmp[k]; bits += 5 + 7 + ((tmp[k].sq != 15) ? dbits + 3 : 0); }
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
    /* level of a leaf by its size, to decode the domain position */
    for (int it = 0; it < 8; it++) {
        build_domain_images(dec);
        #pragma omp parallel for schedule(static)
        for (int k = 0; k < nleaves; k++) {
            Leaf *L = &leaves[k];
            int r = L->r, np = G - r + 1;
            int dk = L->dom / (np * np), p = L->dom % (np * np), gy = p / np, gx = p % np;
            double sv = s_value(L->sq), ov = o_value(L->oq);
            for (int i = 0; i < r; i++) for (int j = 0; j < r; j++) {
                double val = ov;
                if (L->sq != 15) { int s = iso_src(L->iso, i, j, r); val += sv * gimg[dk][(gy + s / r) * G + gx + s % r]; }
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
    printf("threads=%d tol=%.1f leaves=%d bytes=%lld bpp=%.3f CR=%.2f PSNR=%.2f ET=%.4f DT=%.4f checksum=%016llx\n",
           omp_get_max_threads(), tol, nleaves, bytes, 8.0 * bytes / NMAX, (double)NMAX / bytes, psnr, ET, DT, h);
    return 0;
}
