/* sweep_filter.c -- tune the POST-compression bilateral filter (d, sigma_color, sigma_space, alpha)
 * with a train/test protocol. LBG runs ONCE per image (the filter acts on the decoded image only,
 * so it changes neither CR nor the codebook). All metrics are against the pristine original.
 *
 * Build (sem1.c in the same folder):  gcc -O2 -Wall -Wextra -o sweep_filter sweep_filter.c -lm
 * Run:   ./sweep_filter tune1.txt tune2.txt -- test1.txt test2.txt test3.txt
 *        images before "--" are used to CHOOSE the parameters, images after it only to EVALUATE.
 * Selection rule: among the top-10 configs by mean tuning PSNR, take the best one whose mean tuning
 * SSIM is not lower than the current default (d=5, sc=20, ss=20, alpha=0.8); else keep the default. */
#define main sem1_main
#include "sem1.c"
#undef main

typedef struct { uint8_t *orig, *rec; char name[256]; } Img;

static int load(const char *path, Img *m)
{
    m->orig = malloc(WIDTH * HEIGHT); m->rec = malloc(WIDTH * HEIGHT);
    snprintf(m->name, sizeof m->name, "%s", path);
    if (!read_image_from_txt(path, m->orig, WIDTH, HEIGHT)) return 0;
    uint8_t *tr = NULL;
    int nv = build_training_vectors(m->orig, &tr);
    float *tf = calloc((size_t)nv * VLEN, sizeof(float));
    float *cb = calloc((size_t)CODEBOOK_SIZE * VLEN, sizeof(float));
    uint8_t *lab = malloc(nv);
    for (int i = 0; i < nv * VLEN; i++) tf[i] = (float)tr[i];
    lbg(tf, nv, CODEBOOK_SIZE, lab, cb, 0);
    decompress_image(m->rec, WIDTH, HEIGHT, BLOCK_SIZE, cb, lab);
    free(tr); free(tf); free(cb); free(lab);
    return 1;
}

typedef struct { int d; float sc, ss, a; double psnr, ssim; } Cfg;
static const int   GD[]  = {3, 5, 7};
static const float GSC[] = {10, 15, 20, 30, 45};
static const float GSS[] = {1, 2, 5, 20};
static const float GA[]  = {0.2f, 0.4f, 0.5f, 0.6f, 0.7f, 0.8f, 0.9f};
#define NCFG (3 * 5 * 4 * 7)

static int cmp_psnr(const void *x, const void *y)
{ double a = ((const Cfg *)x)->psnr, b = ((const Cfg *)y)->psnr; return (a < b) - (a > b); }

static void apply(const Img *m, const Cfg *c, double *psnr, double *ssim, int want_ssim)
{
    uint8_t *out = malloc(WIDTH * HEIGHT);
    bilateral_preprocess(m->rec, out, WIDTH, HEIGHT, c->d, c->sc, c->ss, c->a);
    *psnr = compute_psnr(m->orig, out, WIDTH * HEIGHT);
    *ssim = want_ssim ? SSIM_window_based(m->orig, out, WIDTH, HEIGHT) : 0.0;
    free(out);
}

int main(int argc, char **argv)
{
    Img tune[64], test[64]; int nt = 0, ne = 0, after = 0;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--")) { after = 1; continue; }
        Img *m = after ? &test[ne] : &tune[nt];
        if (!load(argv[i], m)) { fprintf(stderr, "cannot load %s\n", argv[i]); return 1; }
        if (after) ne++; else nt++;
        fprintf(stderr, "loaded %s (%s)\n", argv[i], after ? "test" : "tune");
    }
    if (nt == 0) { fprintf(stderr, "usage: %s tune... -- test...\n", argv[0]); return 1; }

    Cfg def = {5, 20.0f, 20.0f, 0.8f, 0, 0};
    Cfg *g = calloc(NCFG, sizeof(Cfg)); int n = 0;
    for (unsigned a = 0; a < 3; a++) for (unsigned b = 0; b < 5; b++)
      for (unsigned c = 0; c < 4; c++) for (unsigned e = 0; e < 7; e++)
        g[n++] = (Cfg){GD[a], GSC[b], GSS[c], GA[e], 0, 0};

    /* 1. PSNR of every config on the tuning images (mean) */
    for (int k = 0; k < n; k++) {
        double s = 0;
        for (int i = 0; i < nt; i++) { double p, q; apply(&tune[i], &g[k], &p, &q, 0); s += p; }
        g[k].psnr = s / nt;
        if (k % 60 == 0) fprintf(stderr, "grid %d/%d\n", k, n);
    }
    qsort(g, n, sizeof(Cfg), cmp_psnr);

    /* 2. SSIM for the 10 finalists and for the default */
    double dp = 0, ds = 0;
    for (int i = 0; i < nt; i++) { double p, q; apply(&tune[i], &def, &p, &q, 1); dp += p; ds += q; }
    def.psnr = dp / nt; def.ssim = ds / nt;
    for (int k = 0; k < 10; k++) {
        double s = 0;
        for (int i = 0; i < nt; i++) { double p, q; apply(&tune[i], &g[k], &p, &q, 1); s += q; }
        g[k].ssim = s / nt;
    }
    printf("\n=== TUNING SET (%d images): mean PSNR / SSIM ===\n", nt);
    printf("no filter   : see per-image table below\n");
    printf("default     : d=%d sc=%.0f ss=%.0f a=%.1f  PSNR=%.3f SSIM=%.4f\n", def.d, def.sc, def.ss, def.a, def.psnr, def.ssim);
    printf("top-10 by PSNR:\n");
    int best = -1;
    for (int k = 0; k < 10; k++) {
        printf("  #%d d=%d sc=%-4.0f ss=%-3.0f a=%.1f  PSNR=%.3f SSIM=%.4f%s\n", k + 1, g[k].d, g[k].sc, g[k].ss, g[k].a,
               g[k].psnr, g[k].ssim, (g[k].ssim >= def.ssim && best < 0) ? "   <== selected" : "");
        if (g[k].ssim >= def.ssim && best < 0) best = k;
    }
    Cfg sel = (best >= 0) ? g[best] : def;
    if (best < 0) printf("no finalist keeps SSIM >= default: keeping the default\n");

    /* 3. evaluation on held-out images (and on tuning images, for reference) */
    printf("\n=== PER-IMAGE (vs ORIGINAL): none | default | selected ===\n");
    printf("%-28s %-6s %8s %8s %8s | %7s %7s %7s\n", "image", "set", "PSNRnone", "PSNRdef", "PSNRsel", "SSIMnone", "SSIMdef", "SSIMsel");
    Cfg none = {5, 20.0f, 20.0f, 1.0f, 0, 0};
    double gs = 0, gd2 = 0; int cnt = 0;
    for (int pass = 0; pass < 2; pass++) {
        int m = pass ? ne : nt; Img *arr = pass ? test : tune;
        for (int i = 0; i < m; i++) {
            double p0, s0, p1, s1, p2, s2;
            apply(&arr[i], &none, &p0, &s0, 1); apply(&arr[i], &def, &p1, &s1, 1); apply(&arr[i], &sel, &p2, &s2, 1);
            printf("%-28.28s %-6s %8.2f %8.2f %8.2f | %7.4f %7.4f %7.4f\n", arr[i].name, pass ? "TEST" : "tune", p0, p1, p2, s0, s1, s2);
            if (pass) { gs += p2 - p1; gd2 += s2 - s1; cnt++; }
        }
    }
    printf("\nselected: d=%d sigma_color=%.0f sigma_space=%.0f alpha=%.1f\n", sel.d, sel.sc, sel.ss, sel.a);
    if (cnt) printf("held-out gain over default: mean dPSNR=%+.3f dB  mean dSSIM=%+.4f  (%d test images)\n", gs / cnt, gd2 / cnt, cnt);
    return 0;
}
