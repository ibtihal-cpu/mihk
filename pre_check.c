/* pre_check.c -- decides pre-filter vs post-filter with ONE consistent, pristine reference.
 * Build (needs sem1.c in the same folder):  gcc -O2 -Wall -Wextra -o pre_check pre_check.c -lm
 * Run:                                      ./pre_check gray.txt
 * For each configuration it prints PSNR/SSIM/MSE against the ORIGINAL image and, for the
 * pre-filter case, ALSO against the filtered image (the metric a buggy pipeline would report). */
#define main sem1_main
#include "sem1.c"
#undef main

static void evaluate(const char *name, const uint8_t *train_img, const uint8_t *orig, int post)
{
    uint8_t *tr = NULL;
    int nv = build_training_vectors((uint8_t *)train_img, &tr);
    float *tf = calloc((size_t)nv * VLEN, sizeof(float));
    float *cb = calloc((size_t)CODEBOOK_SIZE * VLEN, sizeof(float));
    uint8_t *lab = malloc(nv), *ld = malloc(nv), *rec = malloc(WIDTH * HEIGHT), *out = malloc(WIDTH * HEIGHT);
    for (int i = 0; i < nv * VLEN; i++) tf[i] = (float)tr[i];
    lbg(tf, nv, CODEBOOK_SIZE, lab, cb, 0);

    ld[0] = lab[0];
    for (int i = 1; i < nv; i++) ld[i] = (uint8_t)(lab[i] - lab[i - 1] + 128);
    int hd = 0, hh = 0;
    int huff = huffman_on_labels(ld, nv, 255, &hd, &hh);
    double cr = (double)(WIDTH * HEIGHT) / (double)(CODEBOOK_SIZE * VLEN + huff);

    decompress_image(rec, WIDTH, HEIGHT, BLOCK_SIZE, cb, lab);
    if (post) bilateral_preprocess(rec, out, WIDTH, HEIGHT, BF_D, BF_SIGMA_COLOR, BF_SIGMA_SPACE, BF_ALPHA);
    else      memcpy(out, rec, WIDTH * HEIGHT);

    printf("%-34s CR=%6.2f | vs ORIGINAL: PSNR=%.2f SSIM=%.4f MSE=%.2f",
           name, cr, compute_psnr((uint8_t *)orig, out, WIDTH * HEIGHT),
           SSIM_window_based((uint8_t *)orig, out, WIDTH, HEIGHT),
           compute_mse((uint8_t *)orig, out, WIDTH * HEIGHT));
    if (train_img != orig)
        printf(" | vs FILTERED: PSNR=%.2f SSIM=%.4f MSE=%.2f",
               compute_psnr((uint8_t *)train_img, out, WIDTH * HEIGHT),
               SSIM_window_based((uint8_t *)train_img, out, WIDTH, HEIGHT),
               compute_mse((uint8_t *)train_img, out, WIDTH * HEIGHT));
    printf("\n");
    free(tr); free(tf); free(cb); free(lab); free(ld); free(rec); free(out);
}

int main(int argc, char **argv)
{
    const char *path = argc > 1 ? argv[1] : "gray.txt";
    uint8_t *img = malloc(WIDTH * HEIGHT), *flt = malloc(WIDTH * HEIGHT);
    if (!read_image_from_txt(path, img, WIDTH, HEIGHT)) return 1;
    bilateral_preprocess(img, flt, WIDTH, HEIGHT, BF_D, BF_SIGMA_COLOR, BF_SIGMA_SPACE, BF_ALPHA);

    printf("\n=== A) no filter ===\n");
    evaluate("LBG only", img, img, 0);
    printf("=== B) PRE-filter (filter -> LBG)  [published papers' pipeline] ===\n");
    evaluate("filter -> LBG", flt, img, 0);
    printf("=== C) POST-filter (LBG -> filter) [thesis pipeline] ===\n");
    evaluate("LBG -> filter", img, img, 1);
    free(img); free(flt);
    return 0;
}
