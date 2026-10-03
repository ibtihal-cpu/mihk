/* view_compare.c -- one image file showing, side by side, the effect of the post-compression filter.
 * Top row (full 512x512):    ORIGINAL | BEFORE (reconstruction with the old filter) | AFTER (tuned filter)
 * Bottom row (crop x4 zoom): the same three panels, zoomed on a 128x128 region (default centre).
 * Gray (262144 values) and color (786432 values, "R G B" per pixel) 512x512 text images are accepted;
 * a color image is coded and filtered per channel and written as a 24-bit color BMP.
 * Build (sem1.c in the same folder):  gcc -O2 -Wall -Wextra -o view_compare view_compare.c -lm
 * Run:   ./view_compare image.txt out.bmp [crop_x crop_y]      then open out.bmp in any image viewer.
 * It also writes the three FULL-SIZE images separately: <out>_original.bmp, <out>_before.bmp, <out>_after.bmp
 * (open them with  eog <out>_original.bmp <out>_before.bmp <out>_after.bmp  and flip with the arrow keys).
 * Metrics are printed against the ORIGINAL image (color: RGB PSNR from the mean MSE, mean channel SSIM). */
#define main sem1_main
#include "sem1.c"
#undef main

#define PW 512
#define NPANEL 3

static void put_panel(uint8_t *canvas, int cw, int px, int py, const uint8_t *img)
{ for (int y = 0; y < PW; y++) memcpy(canvas + (size_t)(py + y) * cw + px, img + (size_t)y * PW, PW); }

static void zoom_panel(uint8_t *canvas, int cw, int px, int py, const uint8_t *img, int cx, int cy)
{
    for (int y = 0; y < PW; y++) for (int x = 0; x < PW; x++)
        canvas[(size_t)(py + y) * cw + px + x] = img[(size_t)(cy + y / 4) * WIDTH + (cx + x / 4)];
}

static void code_plane(const uint8_t *plane, uint8_t *rec)
{
    uint8_t *tr = NULL;
    int nv = build_training_vectors((uint8_t *)plane, &tr);
    float *tf = calloc((size_t)nv * VLEN, sizeof(float)), *cb = calloc((size_t)CODEBOOK_SIZE * VLEN, sizeof(float));
    uint8_t *lab = malloc(nv);
    for (int i = 0; i < nv * VLEN; i++) tf[i] = (float)tr[i];
    lbg(tf, nv, CODEBOOK_SIZE, lab, cb, 0);
    decompress_image(rec, WIDTH, HEIGHT, BLOCK_SIZE, cb, lab);
    free(tr); free(tf); free(cb); free(lab);
}

int main(int argc, char **argv)
{
    if (argc < 3) { fprintf(stderr, "usage: %s image.txt out.bmp [crop_x crop_y]\n", argv[0]); return 1; }
    int cx = argc > 4 ? atoi(argv[3]) : 192, cy = argc > 4 ? atoi(argv[4]) : 192;
    if (cx < 0 || cy < 0 || cx > WIDTH - 128 || cy > HEIGHT - 128) { fprintf(stderr, "crop must satisfy 0<=x,y<=384\n"); return 1; }

    ImgMode mode = detect_mode_from_file(argv[1]);
    if (mode == MODE_UNKNOWN) { fprintf(stderr, "%s: not a 512x512 gray or color text image\n", argv[1]); return 1; }
    int np = (mode == MODE_COLOR) ? 3 : 1;

    uint8_t *orig[3], *rec[3], *cur[3], *tun[3];
    for (int p = 0; p < np; p++) { orig[p] = malloc(WIDTH * HEIGHT); rec[p] = malloc(WIDTH * HEIGHT); cur[p] = malloc(WIDTH * HEIGHT); tun[p] = malloc(WIDTH * HEIGHT); }
    if (mode == MODE_COLOR) { if (!read_color_image_from_txt(argv[1], orig[0], orig[1], orig[2], WIDTH, HEIGHT)) return 1; }
    else if (!read_image_from_txt(argv[1], orig[0], WIDTH, HEIGHT)) return 1;

    int cw = PW * NPANEL, ch = PW * 2;
    uint8_t *canvas[3] = {NULL, NULL, NULL};
    for (int p = 0; p < np; p++) canvas[p] = calloc((size_t)cw * ch, 1);
    double mse[NPANEL] = {0}, ssim[NPANEL] = {0};
    for (int p = 0; p < np; p++) {
        code_plane(orig[p], rec[p]);
        bilateral_preprocess(rec[p], cur[p], WIDTH, HEIGHT, 5, 20.0f, 20.0f, 0.8f);   /* current published setting */
        bilateral_preprocess(rec[p], tun[p], WIDTH, HEIGHT, 3, 80.0f, 5.0f, 0.2f);    /* tuned setting (round 2)   */
        const uint8_t *pan[NPANEL] = {orig[p], cur[p], tun[p]};
        for (int i = 0; i < NPANEL; i++) {
            put_panel(canvas[p], cw, i * PW, 0, pan[i]);
            zoom_panel(canvas[p], cw, i * PW, PW, pan[i], cx, cy);
            mse[i]  += compute_mse(orig[p], (uint8_t *)pan[i], WIDTH * HEIGHT);
            ssim[i] += SSIM_window_based(orig[p], (uint8_t *)pan[i], WIDTH, HEIGHT);
        }
    }
    const char *name[NPANEL] = {"ORIGINAL", "BEFORE: old filter d5 sc20 ss20 a0.8", "AFTER: tuned filter d3 sc80 ss5 a0.2"};
    for (int i = 0; i < NPANEL; i++) {
        double m = mse[i] / np;
        printf("%-34s PSNR=%6.2f dB  SSIM=%.4f  MSE=%7.2f\n", name[i], m == 0.0 ? 100.0 : 10.0 * log10(255.0 * 255.0 / m), ssim[i] / np, m);
    }
    if (mode == MODE_COLOR) save_bmp_color(argv[2], canvas[0], canvas[1], canvas[2], cw, ch);
    else save_bmp_gray(argv[2], canvas[0], cw, ch);
    {   /* the three images at full size, one file each */
        char base[512], f[600]; snprintf(base, sizeof base, "%s", argv[2]);
        size_t L = strlen(base); if (L > 4 && !strcmp(base + L - 4, ".bmp")) base[L - 4] = 0;
        const char *tag[NPANEL] = {"original", "before", "after"};
        for (int i = 0; i < NPANEL; i++) {
            const uint8_t **src = (const uint8_t **)(i == 0 ? orig : i == 1 ? cur : tun);
            snprintf(f, sizeof f, "%s_%s.bmp", base, tag[i]);
            if (mode == MODE_COLOR) save_bmp_color(f, (uint8_t *)src[0], (uint8_t *)src[1], (uint8_t *)src[2], WIDTH, HEIGHT);
            else save_bmp_gray(f, (uint8_t *)src[0], WIDTH, HEIGHT);
        }
    }
    printf("wrote %s (%dx%d, %s): top = full images (original | before | after), bottom = 4x zoom of region x=%d..%d y=%d..%d\n", argv[2], cw, ch,
           mode == MODE_COLOR ? "color" : "gray", cx, cx + 127, cy, cy + 127);
    return 0;
}
