/* view_compare.c -- one image file showing, side by side, the effect of the post-compression filter.
 * Top row (full 512x512):    ORIGINAL | LBG only (no filter) | CURRENT filter | TUNED filter
 * Bottom row (crop x4 zoom): the same four panels, zoomed on a 128x128 region (default centre).
 * Build (sem1.c in the same folder):  gcc -O2 -Wall -Wextra -o view_compare view_compare.c -lm
 * Run:   ./view_compare gray.txt out.bmp [crop_x crop_y]      then open out.bmp in any image viewer.
 * Metrics are printed against the ORIGINAL image. */
#define main sem1_main
#include "sem1.c"
#undef main

#define PW 512
#define NPANEL 4

static void put_panel(uint8_t *canvas, int cw, int px, int py, const uint8_t *img)
{ for (int y = 0; y < PW; y++) memcpy(canvas + (size_t)(py + y) * cw + px, img + (size_t)y * PW, PW); }

static void zoom_panel(uint8_t *canvas, int cw, int px, int py, const uint8_t *img, int cx, int cy)
{
    for (int y = 0; y < PW; y++) for (int x = 0; x < PW; x++)
        canvas[(size_t)(py + y) * cw + px + x] = img[(size_t)(cy + y / 4) * WIDTH + (cx + x / 4)];
}

int main(int argc, char **argv)
{
    if (argc < 3) { fprintf(stderr, "usage: %s image.txt out.bmp [crop_x crop_y]\n", argv[0]); return 1; }
    int cx = argc > 4 ? atoi(argv[3]) : 192, cy = argc > 4 ? atoi(argv[4]) : 192;
    if (cx < 0 || cy < 0 || cx > WIDTH - 128 || cy > HEIGHT - 128) { fprintf(stderr, "crop must satisfy 0<=x,y<=384\n"); return 1; }

    uint8_t *orig = malloc(WIDTH * HEIGHT), *rec = malloc(WIDTH * HEIGHT);
    if (!read_image_from_txt(argv[1], orig, WIDTH, HEIGHT)) return 1;
    uint8_t *tr = NULL;
    int nv = build_training_vectors(orig, &tr);
    float *tf = calloc((size_t)nv * VLEN, sizeof(float)), *cb = calloc((size_t)CODEBOOK_SIZE * VLEN, sizeof(float));
    uint8_t *lab = malloc(nv);
    for (int i = 0; i < nv * VLEN; i++) tf[i] = (float)tr[i];
    lbg(tf, nv, CODEBOOK_SIZE, lab, cb, 0);
    decompress_image(rec, WIDTH, HEIGHT, BLOCK_SIZE, cb, lab);

    uint8_t *cur = malloc(WIDTH * HEIGHT), *tun = malloc(WIDTH * HEIGHT);
    bilateral_preprocess(rec, cur, WIDTH, HEIGHT, 5, 20.0f, 20.0f, 0.8f);   /* current published setting */
    bilateral_preprocess(rec, tun, WIDTH, HEIGHT, 3, 80.0f, 5.0f, 0.2f);    /* tuned setting (round 2)   */

    const uint8_t *p[NPANEL] = {orig, rec, cur, tun};
    const char *name[NPANEL] = {"ORIGINAL", "LBG only (no filter)", "CURRENT filter d5 sc20 ss20 a0.8", "TUNED filter d3 sc80 ss5 a0.2"};
    int cw = PW * NPANEL, ch = PW * 2;
    uint8_t *canvas = calloc((size_t)cw * ch, 1);
    for (int i = 0; i < NPANEL; i++) {
        put_panel(canvas, cw, i * PW, 0, p[i]);
        zoom_panel(canvas, cw, i * PW, PW, p[i], cx, cy);
        printf("%-34s PSNR=%6.2f dB  SSIM=%.4f  MSE=%7.2f\n", name[i],
               compute_psnr(orig, (uint8_t *)p[i], WIDTH * HEIGHT), SSIM_window_based(orig, (uint8_t *)p[i], WIDTH, HEIGHT),
               compute_mse(orig, (uint8_t *)p[i], WIDTH * HEIGHT));
    }
    save_bmp_gray(argv[2], canvas, cw, ch);
    printf("wrote %s (%dx%d): top = full images, bottom = 4x zoom of region x=%d..%d y=%d..%d\n", argv[2], cw, ch, cx, cx + 127, cy, cy + 127);
    return 0;
}
