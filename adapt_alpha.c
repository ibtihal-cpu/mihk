/* adapt_alpha.c -- what if the ENCODER picked the post-filter strength alpha per image (1 byte side info)?
 * For each image: fixed tuned filter (d=3, sc=80, ss=5, alpha=0.2)  vs  best alpha from a small set,
 * chosen by the lowest RGB/gray MSE against the ORIGINAL image (the encoder has it; the decoder only
 * receives the chosen alpha). alpha=1.0 means "no filter", so the result can never be worse than none in MSE.
 * Build (sem1.c in the same folder):  gcc -O2 -Wall -Wextra -o adapt_alpha adapt_alpha.c -lm
 * Run:   ./adapt_alpha img1.txt img2.txt ...      (gray or color 512x512 text images) */
#define main sem1_main
#include "sem1.c"
#undef main

typedef struct { int np; uint8_t *orig[3], *rec[3]; } Img;

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
    ImgMode mode = detect_mode_from_file(path);
    if (mode == MODE_UNKNOWN) { fprintf(stderr, "%s: not 512x512 gray/color\n", path); return 0; }
    m->np = (mode == MODE_COLOR) ? 3 : 1;
    for (int p = 0; p < m->np; p++) { m->orig[p] = malloc(WIDTH * HEIGHT); m->rec[p] = malloc(WIDTH * HEIGHT); }
    if (mode == MODE_COLOR) { if (!read_color_image_from_txt(path, m->orig[0], m->orig[1], m->orig[2], WIDTH, HEIGHT)) return 0; }
    else if (!read_image_from_txt(path, m->orig[0], WIDTH, HEIGHT)) return 0;
    for (int p = 0; p < m->np; p++) code_plane(m->orig[p], m->rec[p]);
    return 1;
}

static void eval(const Img *m, int d, float sc, float ss, float a, double *psnr, double *ssim, double *mse_out)
{
    uint8_t *out = malloc(WIDTH * HEIGHT);
    double mse = 0, s = 0;
    for (int p = 0; p < m->np; p++) {
        bilateral_preprocess(m->rec[p], out, WIDTH, HEIGHT, d, sc, ss, a);
        mse += compute_mse(m->orig[p], out, WIDTH * HEIGHT);
        s += SSIM_window_based(m->orig[p], out, WIDTH, HEIGHT);
    }
    mse /= m->np;
    *mse_out = mse; *psnr = (mse == 0.0) ? 100.0 : 10.0 * log10(255.0 * 255.0 / mse); *ssim = s / m->np;
    free(out);
}

int main(int argc, char **argv)
{
    static const float AL[] = {0.0f, 0.2f, 0.4f, 0.6f, 0.8f, 1.0f};
    const int NA = (int)(sizeof AL / sizeof *AL);
    printf("%-22s | %-13s | %-13s | %-13s | %-19s\n", "image", "none", "current(d5 a.8)", "fixed a=0.2", "ADAPTIVE alpha (1 byte)");
    double sum[4] = {0}, sums[4] = {0}; int n = 0;
    for (int i = 1; i < argc; i++) {
        Img m;
        if (!load(argv[i], &m)) continue;
        double pn, sn, mn, pc, sc2, mc, pf, sf, mf;
        eval(&m, 3, 80, 5, 1.0f, &pn, &sn, &mn);
        eval(&m, 5, 20, 20, 0.8f, &pc, &sc2, &mc);
        eval(&m, 3, 80, 5, 0.2f, &pf, &sf, &mf);
        double best_mse = 1e30, pa = 0, sa = 0, aa = 1.0;
        for (int k = 0; k < NA; k++) {
            double p, s, ms; eval(&m, 3, 80, 5, AL[k], &p, &s, &ms);
            if (ms < best_mse) { best_mse = ms; pa = p; sa = s; aa = AL[k]; }
        }
        const char *nm = strrchr(argv[i], '/'); nm = nm ? nm + 1 : argv[i];
        printf("%-22.22s | %5.2f %.4f | %5.2f %.4f | %5.2f %.4f | %5.2f %.4f  a=%.1f\n", nm, pn, sn, pc, sc2, pf, sf, pa, sa, aa);
        double P[4] = {pn, pc, pf, pa}, S[4] = {sn, sc2, sf, sa};
        for (int k = 0; k < 4; k++) { sum[k] += P[k]; sums[k] += S[k]; }
        n++;
    }
    if (n) {
        printf("%-22s | %5.2f %.4f | %5.2f %.4f | %5.2f %.4f | %5.2f %.4f\n", "MEAN", sum[0]/n, sums[0]/n, sum[1]/n, sums[1]/n, sum[2]/n, sums[2]/n, sum[3]/n, sums[3]/n);
        printf("gain of adaptive over fixed a=0.2: %+.3f dB  |  over current: %+.3f dB  |  over none: %+.3f dB\n",
               (sum[3]-sum[2])/n, (sum[3]-sum[1])/n, (sum[3]-sum[0])/n);
    }
    return 0;
}
