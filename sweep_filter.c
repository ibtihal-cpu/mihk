/* sweep_filter.c -- tune the POST-compression bilateral filter (d, sigma_color, sigma_space, alpha)
 * with a train/test protocol. LBG runs ONCE per image (the filter acts on the decoded image only,
 * so it changes neither CR nor the codebook). All metrics are against the pristine original.
 *
 * Build (sem1.c in the same folder):  gcc -O2 -Wall -Wextra -o sweep_filter sweep_filter.c -lm
 * Gray (262144 values) and color (786432 values, "R G B" per pixel) text images are both accepted; for a
 * color image each channel is coded and filtered independently, PSNR comes from the MSE averaged over
 * R,G,B (the RGB PSNR of the thesis protocol) and SSIM is the mean channel-wise SSIM.
 * Run:   ./sweep_filter tune1.txt tune2.txt -- test1.txt test2.txt test3.txt
 *        images before "--" are used to CHOOSE the parameters, images after it only to EVALUATE.
 * Selection rule: among the top-10 configs by mean tuning PSNR, take the best one whose mean tuning
 * SSIM is not lower than the current default (d=5, sc=20, ss=20, alpha=0.8); else keep the default. */
#define main sem1_main
#include "sem1.c"
#undef main

typedef struct { int np; uint8_t *orig[3], *rec[3]; char name[256]; } Img;

static void code_plane(const uint8_t *plane, uint8_t *rec)
{
    uint8_t *tr = NULL;
    int nv = build_training_vectors((uint8_t *)plane, &tr);
    float *tf = calloc((size_t)nv * VLEN, sizeof(float));
    float *cb = calloc((size_t)CODEBOOK_SIZE * VLEN, sizeof(float));
    uint8_t *lab = malloc(nv);
    for (int i = 0; i < nv * VLEN; i++) tf[i] = (float)tr[i];
    lbg(tf, nv, CODEBOOK_SIZE, lab, cb, 0);
    decompress_image(rec, WIDTH, HEIGHT, BLOCK_SIZE, cb, lab);
    free(tr); free(tf); free(cb); free(lab);
}

static int load(const char *path, Img *m)
{
    snprintf(m->name, sizeof m->name, "%s", path);
    ImgMode mode = detect_mode_from_file(path);
    if (mode == MODE_UNKNOWN) { fprintf(stderr, "%s: not 512x512 gray or color text image\n", path); return 0; }
    m->np = (mode == MODE_COLOR) ? 3 : 1;
    for (int p = 0; p < m->np; p++) { m->orig[p] = malloc(WIDTH * HEIGHT); m->rec[p] = malloc(WIDTH * HEIGHT); }
    if (mode == MODE_COLOR) {
        if (!read_color_image_from_txt(path, m->orig[0], m->orig[1], m->orig[2], WIDTH, HEIGHT)) return 0;
    } else {
        if (!read_image_from_txt(path, m->orig[0], WIDTH, HEIGHT)) return 0;
    }
    for (int p = 0; p < m->np; p++) code_plane(m->orig[p], m->rec[p]);
    return 1;
}

typedef struct { int d; float sc, ss, a; double psnr, ssim; } Cfg;
/* Round 2 grid: round 1 put the optimum on the grid edge (alpha=0.2, sigma_color=45), so it is
   extended (alpha down to 0 = pure filter output, sigma_color up to 120). sigma_space was
   insensitive for d=3 in round 1, so it is fixed. */
static const int   GD[]  = {3, 5};
static const float GSC[] = {20, 30, 45, 60, 80, 120};
static const float GSS[] = {5};
static const float GA[]  = {0.0f, 0.05f, 0.1f, 0.15f, 0.2f, 0.3f, 0.4f};
#define NGD  ((int)(sizeof GD  / sizeof *GD))
#define NGSC ((int)(sizeof GSC / sizeof *GSC))
#define NGSS ((int)(sizeof GSS / sizeof *GSS))
#define NGA  ((int)(sizeof GA  / sizeof *GA))
#define NCFG (NGD * NGSC * NGSS * NGA)

static int cmp_psnr(const void *x, const void *y)
{ double a = ((const Cfg *)x)->psnr, b = ((const Cfg *)y)->psnr; return (a < b) - (a > b); }

static void apply(const Img *m, const Cfg *c, double *psnr, double *ssim, int want_ssim)
{
    uint8_t *out = malloc(WIDTH * HEIGHT);
    double mse = 0, ss = 0;
    for (int p = 0; p < m->np; p++) {
        bilateral_preprocess(m->rec[p], out, WIDTH, HEIGHT, c->d, c->sc, c->ss, c->a);
        mse += compute_mse(m->orig[p], out, WIDTH * HEIGHT);
        if (want_ssim) ss += SSIM_window_based(m->orig[p], out, WIDTH, HEIGHT);
    }
    mse /= m->np;
    *psnr = (mse == 0.0) ? 100.0 : 10.0 * log10((255.0 * 255.0) / mse);
    *ssim = want_ssim ? ss / m->np : 0.0;
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
        fprintf(stderr, "loaded %s (%s, %s)\n", argv[i], after ? "test" : "tune", m->np == 3 ? "color" : "gray");
    }
    if (nt == 0) { fprintf(stderr, "usage: %s tune... -- test...\n", argv[0]); return 1; }

    Cfg def = {5, 20.0f, 20.0f, 0.8f, 0, 0};
    Cfg *g = calloc(NCFG, sizeof(Cfg)); int n = 0;
    for (int a = 0; a < NGD; a++) for (int b = 0; b < NGSC; b++)
      for (int c = 0; c < NGSS; c++) for (int e = 0; e < NGA; e++)
        g[n++] = (Cfg){GD[a], GSC[b], GSS[c], GA[e], 0, 0};

    /* 1. PSNR of every config on the tuning images (mean) */
    for (int k = 0; k < n; k++) {
        double s = 0;
        for (int i = 0; i < nt; i++) { double p, q; apply(&tune[i], &g[k], &p, &q, 0); s += p; }
        g[k].psnr = s / nt;
        if (k % 20 == 0) fprintf(stderr, "grid %d/%d\n", k, n);
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
