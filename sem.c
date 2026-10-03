/*
 * ============================================================
 *  lbg_sequential_merged.c
 *
 *  SEQUENTIAL (single-process, no MPI) LBG (Linde-Buzo-Gray)
 *  vector-quantization image compression. Merges the two
 *  previously separate sequential programs into ONE binary that
 *  handles both GRAYSCALE and COLOR input, selected at RUN TIME
 *  (not compile time) by an explicit flag or by auto-detection
 *  of the input file's pixel format.
 *
 *  Source of the two original implementations:
 *      - grayscale sequential : seg.c  (938 lines)
 *      - color sequential     : seco.c (761 lines)
 *
 *  Both modes run the SAME LBG splitting/Lloyd-iteration
 *  algorithm (build_training_vectors -> lbg -> decompress_image),
 *  the same delta+Huffman entropy coding on the labels, and the
 *  same post-compression bilateral filter, on the same 512x512
 *  block-4 codebook-64 setup. Color mode simply runs that whole
 *  per-channel pipeline three times (R, then G, then B) and
 *  aggregates the results, exactly as seco.c did.
 *
 *  ------------------------------------------------------------
 *  CLI convention (a single clean convention was picked; see the
 *  "Judgment calls" note below for why):
 *
 *      ./lbg_seq <image_path> [--gray|--color]
 *
 *      argv[1] = path to the image as a plain-text, whitespace-
 *                separated list of integers (512x512 image).
 *                  - grayscale : one integer per pixel (this is
 *                    exactly seg.c's img.txt format).
 *                  - color     : three integers "R G B" per
 *                    pixel (this is exactly seco.c's
 *                    color_img.txt format).
 *                Default if omitted: "img.txt".
 *
 *      argv[2] = optional explicit mode flag, "--gray" or
 *                "--color". When given, it is trusted outright
 *                and no auto-detection is performed.
 *
 *      If argv[2] is omitted, the mode is AUTO-DETECTED by
 *      pre-scanning the file and counting how many whitespace-
 *      separated integer tokens it contains:
 *          count == WIDTH*HEIGHT     (262144)  -> grayscale
 *          count == WIDTH*HEIGHT*3   (786432)  -> color
 *          anything else                        -> error, asks
 *              the user to pass --gray/--color explicitly.
 *      This works because WIDTH/HEIGHT are fixed compile-time
 *      constants (as they already were in all four original
 *      files) and grayscale vs. color text dumps differ in
 *      nothing BUT this token count, so it is a fully reliable
 *      discriminator for this file format (unlike, say, sniffing
 *      a PGM/PPM magic number, which these .txt inputs don't have).
 *
 *  Compile:
 *      gcc -O2 -Wall -o lbg_seq lbg_sequential_merged.c -lm
 *
 *  Run examples:
 *      ./lbg_seq brain_512.txt --gray
 *      ./lbg_seq parrot_512.txt --color
 *      ./lbg_seq brain_512.txt              (auto-detected)
 *
 *  ------------------------------------------------------------
 *  Judgment calls made while merging (documented per the task's
 *  reconciliation requirement):
 *
 *   1) argv convention: seg.c took only argv[1] (image path,
 *      default "img.txt"); seco.c took only argv[1] (image path,
 *      default "color_img.txt"). Neither original had a mode
 *      flag, because each binary only ever handled one mode.
 *      Since this merged file must pick ONE mode per run, an
 *      optional argv[2] flag was added (diverging from both
 *      originals, noted here as required) with auto-detection as
 *      the no-flag default so existing single-mode invocation
 *      habits (`./binary image.txt`) still work unchanged.
 *
 *   2) lbg(): identical splitting/Lloyd-iteration algorithm in
 *      both originals, but seco.c's copy additionally printf's
 *      "k=%3d iter=%3d distortion=%.4f (first/converged)" progress
 *      lines per split stage, while seg.c's copy is silent. Rather
 *      than silently dropping or silently adding those prints for
 *      one of the two original modes, a `verbose` parameter was
 *      added to the shared lbg(); the grayscale path calls it with
 *      verbose=0 (matching seg.c exactly) and the color path calls
 *      it with verbose=1 per channel (matching seco.c exactly). No
 *      numeric result changes either way.
 *
 *   3) compute_entropy(): only used by the grayscale path (seg.c
 *      prints "Entropy before/after Delta"); seco.c's color
 *      pipeline never computed or printed entropy. It is kept as
 *      a shared helper but only called from run_grayscale(), so
 *      color-mode output is unchanged from seco.c.
 *
 *   4) save_bmp(): seg.c's single grayscale save_bmp() and
 *      seco.c's save_bmp_gray() are byte-for-byte the same
 *      function under a different name. Kept once, as
 *      save_bmp_gray(), used by the grayscale path exactly as
 *      seg.c used its save_bmp().
 *
 *   5) Huffman / SSIM / bilateral_preprocess / build_training_vectors
 *      / distance16 / decompress_image / compute_mse / compute_psnr:
 *      byte-for-byte identical between seg.c and seco.c already
 *      (confirmed while reading both files function by function),
 *      so each is kept exactly once and shared by both modes.
 * ============================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <time.h>
#include <string.h>

/* ---------------- shared constants (identical in all 4 originals) --- */
#define WIDTH 512
#define HEIGHT 512
#define BLOCK_SIZE 4
#define DELTA 0.01f
#define EPSILON 0.0001f
#define CODEBOOK_SIZE 64
#define K1 0.01
#define K2 0.03
#define VLEN (BLOCK_SIZE * BLOCK_SIZE)   /* = 16 */

#define BF_D            5
#define BF_SIGMA_COLOR  20.0f
#define BF_SIGMA_SPACE  20.0f
#define BF_ALPHA        0.8f

#define SEC(a,b) ((double)((b) - (a)) / CLOCKS_PER_SEC)

/* wall-clock timer -- same thing MPI_Wtime() measures in the parallel file */
static inline double wtime(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

/* ============================================================
   ---------------------- SHARED HELPERS -----------------------
   (identical between seg.c and seco.c; kept once)
   ============================================================ */

void save_bmp_gray(const char *filename, uint8_t *data, int width, int height)
{
    int row_padded = (width + 3) & ~3;
    int img_size   = row_padded * height;
    int file_size  = 54 + 1024 + img_size;

    uint8_t header[54] = {0};
    header[0] = 'B'; header[1] = 'M';
    header[2] = file_size & 0xFF;
    header[3] = (file_size >> 8)  & 0xFF;
    header[4] = (file_size >> 16) & 0xFF;
    header[5] = (file_size >> 24) & 0xFF;
    int data_offset = 54 + 1024;
    header[10] = data_offset & 0xFF;
    header[11] = (data_offset >> 8) & 0xFF;
    header[14] = 40;
    header[18] = width  & 0xFF; header[19] = (width  >> 8) & 0xFF;
    header[20] = (width  >> 16) & 0xFF; header[21] = (width  >> 24) & 0xFF;
    header[22] = height & 0xFF; header[23] = (height >> 8) & 0xFF;
    header[24] = (height >> 16) & 0xFF; header[25] = (height >> 24) & 0xFF;
    header[26] = 1;
    header[28] = 8;
    header[34] = img_size & 0xFF;
    header[35] = (img_size >> 8) & 0xFF;

    FILE *f = fopen(filename, "wb");
    if (!f) { perror(filename); return; }
    fwrite(header, 1, 54, f);
    for (int i = 0; i < 256; i++) {
        uint8_t entry[4] = {(uint8_t)i, (uint8_t)i, (uint8_t)i, 0};
        fwrite(entry, 1, 4, f);
    }
    uint8_t pad[3] = {0, 0, 0};
    for (int y = height - 1; y >= 0; y--) {
        fwrite(&data[y * width], 1, width, f);
        if (row_padded - width > 0)
            fwrite(pad, 1, row_padded - width, f);
    }
    fclose(f);
}

void save_bmp_color(const char *filename, uint8_t *R, uint8_t *G, uint8_t *B,
                     int width, int height)
{
    int row_bytes  = width * 3;
    int row_padded = (row_bytes + 3) & ~3;
    int img_size   = row_padded * height;
    int file_size  = 54 + img_size;

    uint8_t header[54] = {0};
    header[0] = 'B'; header[1] = 'M';
    header[2] = file_size & 0xFF;
    header[3] = (file_size >> 8)  & 0xFF;
    header[4] = (file_size >> 16) & 0xFF;
    header[5] = (file_size >> 24) & 0xFF;
    header[10] = 54;
    header[14] = 40;
    header[18] = width  & 0xFF; header[19] = (width  >> 8) & 0xFF;
    header[20] = (width  >> 16) & 0xFF; header[21] = (width  >> 24) & 0xFF;
    header[22] = height & 0xFF; header[23] = (height >> 8) & 0xFF;
    header[24] = (height >> 16) & 0xFF; header[25] = (height >> 24) & 0xFF;
    header[26] = 1;
    header[28] = 24;
    header[34] = img_size & 0xFF;
    header[35] = (img_size >> 8) & 0xFF;

    FILE *f = fopen(filename, "wb");
    if (!f) { perror(filename); return; }
    fwrite(header, 1, 54, f);

    uint8_t pad[3] = {0, 0, 0};
    for (int y = height - 1; y >= 0; y--) {
        for (int x = 0; x < width; x++) {
            int idx = y * width + x;
            uint8_t pixel[3] = { B[idx], G[idx], R[idx] };  /* BMP stores B,G,R */
            fwrite(pixel, 1, 3, f);
        }
        if (row_padded - row_bytes > 0)
            fwrite(pad, 1, row_padded - row_bytes, f);
    }
    fclose(f);
}

static void bilateral_preprocess(const uint8_t *src, uint8_t *dst,
                                  int W, int H,
                                  int d, float sigmaColor, float sigmaSpace,
                                  float alpha)
{
    int radius = d / 2;
    int diam   = 2 * radius + 1;

    float two_sc_sq = 2.0f * sigmaColor * sigmaColor;
    float two_ss_sq = 2.0f * sigmaSpace * sigmaSpace;

    float *gs = (float *)malloc((size_t)diam * diam * sizeof(float));
    for (int i = -radius; i <= radius; i++)
        for (int j = -radius; j <= radius; j++)
            gs[(i + radius) * diam + (j + radius)] =
                expf(-((float)(i * i + j * j)) / two_ss_sq);

    for (int y = 0; y < H; y++) {
        for (int x = 0; x < W; x++) {
            float center = (float)src[y * W + x];
            float sum  = 0.0f;
            float wsum = 0.0f;

            for (int i = -radius; i <= radius; i++) {
                int yy = y + i;
                if (yy < 0 || yy >= H) continue;
                for (int j = -radius; j <= radius; j++) {
                    int xx = x + j;
                    if (xx < 0 || xx >= W) continue;
                    float val  = (float)src[yy * W + xx];
                    float diff = val - center;
                    float gr   = expf(-(diff * diff) / two_sc_sq);
                    float w    = gs[(i + radius) * diam + (j + radius)] * gr;
                    sum  += w * val;
                    wsum += w;
                }
            }
            float bf = sum / wsum;
            float blended = alpha * center + (1.0f - alpha) * bf;
            if (blended < 0.0f)   blended = 0.0f;
            if (blended > 255.0f) blended = 255.0f;
            dst[y * W + x] = (uint8_t)(blended + 0.5f);
        }
    }
    free(gs);
}

int build_training_vectors(uint8_t *image, uint8_t **training_set)
{
    int num_blocks_x = WIDTH / BLOCK_SIZE;
    int num_blocks_y = HEIGHT / BLOCK_SIZE;
    int num_vectors = num_blocks_x * num_blocks_y;
    int vector_length = BLOCK_SIZE * BLOCK_SIZE;

    *training_set = (uint8_t *)malloc(num_vectors * vector_length);
    if (!*training_set) {
        fprintf(stderr, "Memory allocation failed\n");
        return -1;
    }

    int idx = 0;
    for (int y = 0; y < HEIGHT; y += BLOCK_SIZE) {
        for (int x = 0; x < WIDTH; x += BLOCK_SIZE) {
            for (int r = 0; r < BLOCK_SIZE; r++) {
                for (int c = 0; c < BLOCK_SIZE; c++) {
                    int img_index = (y + r) * WIDTH + (x + c);
                    int vec_index = r * BLOCK_SIZE + c;
                    (*training_set)[idx * vector_length + vec_index] = image[img_index];
                }
            }
            idx++;
        }
    }
    return num_vectors;
}

int read_image_from_txt(const char *filename, uint8_t *image, int width, int height) {
    FILE *f = fopen(filename, "r");
    if (!f) {
        perror("Error opening image file");
        return 0;
    }
    int val, count = 0;
    while (fscanf(f, "%d", &val) == 1 && count < width * height) {
        if (val < 0) val = 0;
        if (val > 255) val = 255;
        image[count++] = (uint8_t)val;
    }
    fclose(f);
    if (count != width * height) {
        fprintf(stderr, "Warning: Expected %d pixels, got %d\n", width * height, count);
    }
    return count == width * height;
}

int read_color_image_from_txt(const char *filename,
                               uint8_t *R, uint8_t *G, uint8_t *B,
                               int width, int height)
{
    FILE *f = fopen(filename, "r");
    if (!f) { perror("Error opening image file"); return 0; }

    int r, g, b, count = 0;
    while (fscanf(f, "%d %d %d", &r, &g, &b) == 3 && count < width * height) {
        if (r < 0) r = 0;
        if (r > 255) r = 255;
        if (g < 0) g = 0;
        if (g > 255) g = 255;
        if (b < 0) b = 0;
        if (b > 255) b = 255;
        R[count] = (uint8_t)r; G[count] = (uint8_t)g; B[count] = (uint8_t)b;
        count++;
    }
    fclose(f);
    if (count != width * height) {
        fprintf(stderr, "Warning: Expected %d pixels, got %d\n", width * height, count);
    }
    return count == width * height;
}

static inline float distance16(const float *a, const float *b) {
    float d = 0.0f;
    for (int i = 0; i < VLEN; i++) {
        float diff = a[i] - b[i];
        d += diff * diff;
    }
    return d;
}

/* verbose=1 reproduces seco.c's per-split "k=... (first/converged)"
   progress lines; verbose=0 reproduces seg.c's silence. See judgment
   call #2 in the header comment. */
void lbg(const float *training, int num_vectors, int target_K,
         uint8_t *labels, float *codebook, int verbose)
{
    for (int j = 0; j < VLEN; j++) {
        float s = 0.0f;
        for (int i = 0; i < num_vectors; i++)
            s += training[i * VLEN + j];
        codebook[0 * VLEN + j] = s / num_vectors;
    }

    int k = 1;
    float *sum   = NULL;
    int   *count = NULL;
    int allocated_k = 0;

    while (k < target_K) {
        for (int i = 0; i < k; i++) {
            for (int j = 0; j < VLEN; j++) {
                codebook[(k + i) * VLEN + j] = codebook[i * VLEN + j] * (1.0f - DELTA);
                codebook[i * VLEN + j]       = codebook[i * VLEN + j] * (1.0f + DELTA);
            }
        }
        k *= 2;

        float prev_distortion = 1e30f;
        int iterations = 0;
        float improvement = 1.0f;
        float distortion = 0.0f;

        do {
            if (sum == NULL || allocated_k < k) {
                free(sum); free(count);
                sum   = (float*)calloc((size_t)k * VLEN, sizeof(float));
                count = (int*)calloc(k, sizeof(int));
                allocated_k = k;
            }
            memset(sum, 0, (size_t)k * VLEN * sizeof(float));
            memset(count, 0, k * sizeof(int));
            distortion = 0.0f;

            for (int i = 0; i < num_vectors; i++) {
                float min_dist = 1e30f;
                int min_index = 0;
                const float *v = &training[i * VLEN];
                for (int c = 0; c < k; c++) {
                    float dd = distance16(&codebook[c * VLEN], v);
                    if (dd < min_dist) { min_dist = dd; min_index = c; }
                }
                labels[i] = (uint8_t)min_index;
                distortion += min_dist;
                count[min_index]++;
                float *s = &sum[min_index * VLEN];
                for (int j = 0; j < VLEN; j++) s[j] += v[j];
            }

            for (int c = 0; c < k; c++) {
                if (count[c] > 0) {
                    float inv = 1.0f / count[c];
                    float *s = &sum[c * VLEN];
                    for (int j = 0; j < VLEN; j++)
                        codebook[c * VLEN + j] = s[j] * inv;
                }
            }

            distortion /= num_vectors;
            improvement = fabs(prev_distortion - distortion) / (distortion + 1e-9f);
            prev_distortion = distortion;
            iterations++;

            if (verbose && iterations == 1)
                printf("k=%3d iter=%3d distortion=%.4f  (first)\n", k, iterations, distortion);

        } while (iterations < 100 && improvement > EPSILON);

        if (verbose)
            printf("k=%3d iter=%3d distortion=%.4f  (converged)\n", k, iterations, distortion);
    }
    free(sum); free(count);
}

void decompress_image(uint8_t *reconstructed, int width, int height,
                       int block_size, const float *codebook, uint8_t *labels)
{
    int blocks_per_row = width / block_size;
    int blocks_per_col = height / block_size;
    int vec_idx = 0;
    for (int by = 0; by < blocks_per_col; by++) {
        for (int bx = 0; bx < blocks_per_row; bx++) {
            int code_idx = labels[vec_idx];
            for (int r = 0; r < block_size; r++) {
                for (int c = 0; c < block_size; c++) {
                    int img_idx = (by*block_size+r)*width + (bx*block_size+c);
                    int code_idx_in_block = r*block_size + c;
                    reconstructed[img_idx] =
                        (uint8_t)roundf(codebook[code_idx * VLEN + code_idx_in_block]);
                }
            }
            vec_idx++;
        }
    }
}

double compute_mse(uint8_t *original, uint8_t *reconstructed, int size) {
    double mse = 0.0;
    for (int i = 0; i < size; i++) {
        double diff = (double)original[i] - (double)reconstructed[i];
        mse += diff*diff;
    }
    return mse/size;
}

double compute_psnr(uint8_t *original, uint8_t *reconstructed, int size) {
    double mse = compute_mse(original, reconstructed, size);
    if (mse == 0) return 100.0;
    return 10.0 * log10((255.0*255.0)/mse);
}

/* grayscale-path-only, see judgment call #3 */
double compute_entropy(uint8_t *labels, int num_labels, int codebook_size)
{
    int hist[256] = {0};
    for (int i = 0; i < num_labels; i++) hist[labels[i]]++;
    double H = 0.0;
    for (int i = 0; i < codebook_size; i++) {
        if (hist[i] > 0) {
            double p = (double)hist[i] / num_labels;
            H -= p * log2(p);
        }
    }
    return H;
}

/* ========================  HUFFMAN  (shared, identical in both) ===== */
typedef struct HuffNode {
    int value;
    uint32_t freq;
    struct HuffNode *left;
    struct HuffNode *right;
} HuffNode;

typedef struct { HuffNode **data; int size; int capacity; } MinHeap;
typedef struct { uint64_t bits; int length; } HuffCode;

static MinHeap *heap_create(int cap) {
    MinHeap *h = (MinHeap*)malloc(sizeof(MinHeap));
    h->data = (HuffNode**)malloc(sizeof(HuffNode*) * cap);
    h->size = 0; h->capacity = cap;
    return h;
}
static HuffNode *huff_new_node(int value, uint32_t freq) {
    HuffNode *n = (HuffNode*)malloc(sizeof(HuffNode));
    n->value = value; n->freq = freq; n->left = n->right = NULL;
    return n;
}
static void heap_swap(HuffNode **a, HuffNode **b) { HuffNode *t = *a; *a = *b; *b = t; }
static void heap_push(MinHeap *h, HuffNode *node) {
    int i = h->size++;
    h->data[i] = node;
    while (i > 0) {
        int p = (i - 1) / 2;
        if (h->data[p]->freq <= h->data[i]->freq) break;
        heap_swap(&h->data[p], &h->data[i]);
        i = p;
    }
}
static HuffNode *heap_pop(MinHeap *h) {
    if (h->size == 0) return NULL;
    HuffNode *root = h->data[0];
    h->data[0] = h->data[--h->size];
    int i = 0;
    while (1) {
        int l = 2*i+1, r = 2*i+2, smallest = i;
        if (l < h->size && h->data[l]->freq < h->data[smallest]->freq) smallest = l;
        if (r < h->size && h->data[r]->freq < h->data[smallest]->freq) smallest = r;
        if (smallest == i) break;
        heap_swap(&h->data[i], &h->data[smallest]);
        i = smallest;
    }
    return root;
}
static void huff_free_tree(HuffNode *node) {
    if (!node) return;
    huff_free_tree(node->left);
    huff_free_tree(node->right);
    free(node);
}
static HuffNode *huff_build_tree(uint32_t *freq, int max_symbol) {
    MinHeap *h = heap_create(max_symbol + 1);
    for (int i = 0; i <= max_symbol; i++)
        if (freq[i] > 0) heap_push(h, huff_new_node(i, freq[i]));
    if (h->size == 0) { free(h->data); free(h); return NULL; }
    if (h->size == 1) {
        HuffNode *only = heap_pop(h);
        HuffNode *root = huff_new_node(-1, only->freq);
        root->left = only;
        free(h->data); free(h);
        return root;
    }
    while (h->size > 1) {
        HuffNode *a = heap_pop(h);
        HuffNode *b = heap_pop(h);
        HuffNode *p = huff_new_node(-1, a->freq + b->freq);
        p->left = a; p->right = b;
        heap_push(h, p);
    }
    HuffNode *root = heap_pop(h);
    free(h->data); free(h);
    return root;
}
static void huff_build_codes_rec(HuffNode *node, HuffCode *table, uint64_t code, int length) {
    if (!node) return;
    if (node->value >= 0) { table[node->value].bits = code; table[node->value].length = length; return; }
    huff_build_codes_rec(node->left,  table, (code << 1),      length + 1);
    huff_build_codes_rec(node->right, table, (code << 1) | 1u, length + 1);
}
static void huff_build_codes(HuffNode *root, HuffCode *table, int max_symbol) {
    for (int i = 0; i <= max_symbol; ++i) { table[i].bits = 0; table[i].length = 0; }
    huff_build_codes_rec(root, table, 0, 0);
}
static uint8_t *huff_encode(uint8_t *data, int n, HuffCode *table, int *out_bytes) {
    int cap = n * 4;
    uint8_t *out = (uint8_t*)malloc(cap);
    int byte_pos = 0, bit_pos = 0;
    uint8_t current = 0;
    for (int i = 0; i < n; ++i) {
        HuffCode hc = table[data[i]];
        uint64_t bits = hc.bits;
        int len = hc.length;
        if (len == 0) continue;
        for (int b = len - 1; b >= 0; --b) {
            int bit = (int)((bits >> b) & 1u);
            current |= (uint8_t)(bit << (7 - bit_pos));
            bit_pos++;
            if (bit_pos == 8) {
                out[byte_pos++] = current;
                current = 0; bit_pos = 0;
                if (byte_pos >= cap) { cap *= 2; out = (uint8_t*)realloc(out, cap); }
            }
        }
    }
    if (bit_pos > 0) out[byte_pos++] = current;
    *out_bytes = byte_pos;
    return out;
}
static void huff_decode(uint8_t *encoded, int enc_bytes, HuffNode *root, int original_n, uint8_t *out) {
    HuffNode *node = root;
    int out_pos = 0;
    for (int i = 0; i < enc_bytes; ++i) {
        uint8_t byte = encoded[i];
        for (int b = 7; b >= 0; --b) {
            if (out_pos >= original_n) return;
            int bit = (byte >> b) & 1;
            node = bit ? node->right : node->left;
            if (!node) { node = root; continue; }   /* single-symbol tree: no right child, resync safely */
            if (node->value >= 0) { out[out_pos++] = (uint8_t)node->value; node = root; }
        }
    }
}
int huffman_on_labels(uint8_t *labels, int num_labels, int max_symbol,
                       int *out_huff_data, int *out_header)
{
    uint32_t *freq = (uint32_t*)calloc(max_symbol + 1, sizeof(uint32_t));
    for (int i = 0; i < num_labels; ++i) {
        int v = labels[i];
        if (v >= 0 && v <= max_symbol) freq[v]++;
    }
    int used_symbols = 0;
    for (int i = 0; i <= max_symbol; i++) if (freq[i] > 0) used_symbols++;

    HuffNode *root = huff_build_tree(freq, max_symbol);
    if (!root) { printf("Huffman: no symbols found!\n"); free(freq); return 0; }

    HuffCode *table = (HuffCode*)malloc((max_symbol + 1) * sizeof(HuffCode));
    huff_build_codes(root, table, max_symbol);

    int enc_bytes = 0;
    uint8_t *enc = huff_encode(labels, num_labels, table, &enc_bytes);

    int header_bytes = used_symbols * sizeof(uint32_t);
    int total_compressed = header_bytes + enc_bytes;

    uint8_t *decoded = (uint8_t*)malloc(num_labels);
    huff_decode(enc, enc_bytes, root, num_labels, decoded);

    int ok = 1;
    for (int i = 0; i < num_labels; ++i) if (labels[i] != decoded[i]) { ok = 0; break; }
    printf("  Decode check        : %s\n", ok ? "OK (labels identical, no distortion)" : "ERROR (mismatch!)");

    if (out_huff_data) *out_huff_data = enc_bytes;
    if (out_header)    *out_header    = header_bytes;

    free(freq); free(table); free(enc); free(decoded);
    huff_free_tree(root);
    return total_compressed;
}

/* ============================================================
   SSIM (11x11 Gaussian window, sigma=1.5, normalized) -- shared,
   identical between seg.c and seco.c.
   ============================================================ */
double SSIM_window_based(unsigned char *img1, unsigned char *img2, int W, int H)
{
    double win[11][11];
    const double sigma = 1.5;
    const double two_s2 = 2.0 * sigma * sigma;
    double wsum = 0.0;
    for (int u = -5; u <= 5; u++)
        for (int v = -5; v <= 5; v++) {
            double g = exp(-((double)(u*u + v*v)) / two_s2);
            win[u+5][v+5] = g;
            wsum += g;
        }
    for (int u = 0; u < 11; u++)
        for (int v = 0; v < 11; v++)
            win[u][v] /= wsum;

    double ssim_total = 0.0;
    int count = 0;
    for (int i = 5; i < H - 5; i++) {
        for (int j = 5; j < W - 5; j++) {
            double mu_x = 0, mu_y = 0;
            for (int u = -5; u <= 5; u++)
                for (int v = -5; v <= 5; v++) {
                    double w = win[u+5][v+5];
                    mu_x += w * img1[(i+u)*W + (j+v)];
                    mu_y += w * img2[(i+u)*W + (j+v)];
                }
            double sigma_x = 0, sigma_y = 0, sigma_xy = 0;
            for (int u = -5; u <= 5; u++)
                for (int v = -5; v <= 5; v++) {
                    double w = win[u+5][v+5];
                    double x = img1[(i+u)*W + (j+v)];
                    double y = img2[(i+u)*W + (j+v)];
                    sigma_x  += w * (x - mu_x) * (x - mu_x);
                    sigma_y  += w * (y - mu_y) * (y - mu_y);
                    sigma_xy += w * (x - mu_x) * (y - mu_y);
                }
            double C1 = (K1 * 255) * (K1 * 255);
            double C2 = (K2 * 255) * (K2 * 255);
            double num = (2 * mu_x * mu_y + C1) * (2 * sigma_xy + C2);
            double den = (mu_x * mu_x + mu_y * mu_y + C1) * (sigma_x + sigma_y + C2);
            ssim_total += num / den;
            count++;
        }
    }
    return ssim_total / count;
}

/* ============================================================
   ------------------- MODE AUTO-DETECTION -----------------------
   ============================================================ */
typedef enum { MODE_UNKNOWN = 0, MODE_GRAY, MODE_COLOR } ImgMode;

static ImgMode detect_mode_from_file(const char *path)
{
    FILE *f = fopen(path, "r");
    if (!f) { perror(path); return MODE_UNKNOWN; }
    long count = 0;
    int val;
    while (fscanf(f, "%d", &val) == 1) count++;
    fclose(f);

    long gray_expect  = (long)WIDTH * HEIGHT;
    long color_expect = (long)WIDTH * HEIGHT * 3;
    if (count == gray_expect)  return MODE_GRAY;
    if (count == color_expect) return MODE_COLOR;
    return MODE_UNKNOWN;
}

/* ============================================================
   ---------------------- GRAYSCALE PATH -------------------------
   Mirrors seg.c's main() body exactly, just wrapped as a function.
   ============================================================ */
static int run_grayscale(const char *image_path)
{
    int original_image_bytes = WIDTH * HEIGHT;

    float *codebook = (float*)calloc((size_t)CODEBOOK_SIZE * VLEN, sizeof(float));
    if (!codebook) { perror("malloc codebook"); return 1; }

    double t_total0 = wtime();

    uint8_t *image = malloc(WIDTH * HEIGHT);
    if (!image) return 1;

    double t_read0 = wtime();
    if (!read_image_from_txt(image_path, image, WIDTH, HEIGHT)) {
        fprintf(stderr, "Failed to read image from text file.\n");
        free(image);
        return 1;
    }
    double t_read1 = wtime();

    double t_bf0 = wtime();
    double t_bf1 = wtime();
    printf("[Bilateral] MOVED TO POST-COMPRESSION (lbgef variant)\n");

    double t_build0 = wtime();
    uint8_t *training_set = NULL;
    int num_vectors = build_training_vectors(image, &training_set);
    double t_build1 = wtime();
    printf("Built %d training vectors (each %d elements)\n", num_vectors, VLEN);

    uint8_t *labels = malloc(num_vectors);
    if (!labels) { perror("malloc labels"); exit(1); }

    float *training_f = (float*)malloc((size_t)num_vectors * VLEN * sizeof(float));
    if (!training_f) { perror("malloc training_f"); exit(1); }
    for (int i = 0; i < num_vectors * VLEN; i++)
        training_f[i] = (float)training_set[i];

    clock_t t_lbg0_cpu = clock();
    double  t_lbg0     = wtime();
    lbg(training_f, num_vectors, CODEBOOK_SIZE, labels, codebook, /*verbose=*/0);
    double  t_lbg1     = wtime();
    clock_t t_lbg1_cpu = clock();

    free(training_f);

    double t_ent0 = wtime();
    double H = compute_entropy(labels, num_vectors, CODEBOOK_SIZE);
    double t_ent1 = wtime();
    printf("Entropy before Huffman = %.3f bits/symbol\n", H);

    double t_cvt0 = wtime();
    uint8_t *codebook_data = malloc(CODEBOOK_SIZE * VLEN);
    for (int k = 0; k < CODEBOOK_SIZE; k++)
        for (int i = 0; i < VLEN; i++)
            codebook_data[k * VLEN + i] = (uint8_t)roundf(codebook[k * VLEN + i]);
    double t_cvt1 = wtime();

    double t_dec0 = wtime();
    uint8_t *reconstructed_lbg = malloc(WIDTH * HEIGHT);
    decompress_image(reconstructed_lbg, WIDTH, HEIGHT, BLOCK_SIZE, codebook, labels);
    double t_dec1 = wtime();

    double t_delta0 = wtime();
    uint8_t *labels_delta_u = malloc(num_vectors);
    labels_delta_u[0] = labels[0];
    for (int i = 1; i < num_vectors; i++)
        labels_delta_u[i] = (uint8_t)(labels[i] - labels[i-1] + 128);
    double t_delta1 = wtime();

    double H_delta = compute_entropy(labels_delta_u, num_vectors, 256);
    printf("Entropy after Delta   = %.3f bits/symbol\n", H_delta);

    int huff_data_bytes = 0;
    int header_bytes    = 0;
    double t_huff0 = wtime();
    int huff_total = huffman_on_labels(labels_delta_u, num_vectors, 255,
                                        &huff_data_bytes, &header_bytes);
    double t_huff1 = wtime();

    printf("Huffman data bytes  = %d\n", huff_data_bytes);
    printf("Huffman total bytes = %d\n", huff_total);
    printf("Header bytes        = %d\n", header_bytes);

    int original_labels = num_vectors;
    int codebook_bytes  = CODEBOOK_SIZE * VLEN;
    double CR_huff_data  = (huff_data_bytes > 0)
                       ? (double)original_labels / (double)huff_data_bytes : 0.0;
    double CR_huff_total = (huff_total > 0)
                       ? (double)original_labels / (double)huff_total : 0.0;
    double CR_system     = (double)original_image_bytes /
                           (double)(codebook_bytes + huff_total);

    printf("\n===== Huffman Compression Results =====\n");
    printf("Huffman data only      : %.2f X\n", CR_huff_data);
    printf("Huffman total          : %.2f X\n", CR_huff_total);
    printf("System total (LBG+Huff): %.2f X\n", CR_system);
    printf("BPP  = %.4f bits/pixel\n", 8.0 / CR_system);

    double t_dd0 = wtime();
    labels[0] = labels_delta_u[0];
    for (int i = 1; i < num_vectors; i++)
        labels[i] = labels[i-1] + ((int)labels_delta_u[i] - 128);
    double t_dd1 = wtime();

    double t_rec0 = wtime();
    uint8_t *reconstructed = malloc(WIDTH * HEIGHT);
    decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook, labels);
    double t_rec1 = wtime();

    double t_bf2_0 = wtime();
    uint8_t *reconstructed_filtered = malloc(WIDTH * HEIGHT);
    if (!reconstructed_filtered) { perror("malloc reconstructed_filtered"); return 1; }
    bilateral_preprocess(reconstructed, reconstructed_filtered, WIDTH, HEIGHT,
                         BF_D, BF_SIGMA_COLOR, BF_SIGMA_SPACE, BF_ALPHA);
    double t_bf2_1 = wtime();
    printf("[Bilateral-Post] d=%d sigmaColor=%.1f sigmaSpace=%.1f alpha=%.2f done\n",
           BF_D, BF_SIGMA_COLOR, BF_SIGMA_SPACE, BF_ALPHA);

    double t_mse0 = wtime();
    double mse  = compute_mse(image, reconstructed_filtered, WIDTH*HEIGHT);
    double t_mse1 = wtime();
    printf("MSE  = %.2f      (time %.4f s)\n", mse, t_mse1 - t_mse0);

    double t_psnr0 = wtime();
    double psnr = compute_psnr(image, reconstructed_filtered, WIDTH*HEIGHT);
    double t_psnr1 = wtime();
    printf("PSNR = %.2f dB   (time %.4f s)\n", psnr, t_psnr1 - t_psnr0);

    int indexes_bytes = num_vectors;
    double CR = (double)original_image_bytes / (codebook_bytes + indexes_bytes);
    printf("Compression Ratio (CR): %.2f\n", CR);

    double t_s0 = wtime();
    double ssim = SSIM_window_based(image, reconstructed_filtered, WIDTH, HEIGHT);
    double t_s1 = wtime();
    printf("SSIM = %.4f       (time %.4f s)\n", ssim, t_s1 - t_s0);

    double t_total1 = wtime();

    FILE *flbg = fopen("lbg_decompress.txt", "w");
    for (size_t i = 0; i < (size_t)WIDTH * HEIGHT; i++)
        fprintf(flbg, "%u\n", reconstructed_lbg[i]);
    fclose(flbg);

    FILE *file1 = fopen("decompress.txt", "w");
    for (size_t i = 0; i < (size_t)WIDTH*HEIGHT; i++)
        fprintf(file1, "%u\n", reconstructed_filtered[i]);
    fclose(file1);

    save_bmp_gray("original.bmp",            image,                  WIDTH, HEIGHT);
    save_bmp_gray("compressed_raw.bmp",      reconstructed,          WIDTH, HEIGHT);
    save_bmp_gray("compressed_filtered.bmp", reconstructed_filtered, WIDTH, HEIGHT);
    printf("Saved: original.bmp  compressed_raw.bmp  compressed_filtered.bmp\n");

    double tt_read   = t_read1  - t_read0;
    double tt_bf     = t_bf1    - t_bf0;
    double tt_build  = t_build1 - t_build0;
    double tt_lbg    = t_lbg1 - t_lbg0;
    double tt_lbg_cpu= SEC(t_lbg0_cpu, t_lbg1_cpu);
    double tt_ent    = t_ent1   - t_ent0;
    double tt_cvt    = t_cvt1   - t_cvt0;
    double tt_dec    = t_dec1   - t_dec0;
    double tt_delta  = t_delta1 - t_delta0;
    double tt_huff   = t_huff1  - t_huff0;
    double tt_dd     = t_dd1    - t_dd0;
    double tt_rec    = t_rec1   - t_rec0;
    double tt_bf2    = t_bf2_1  - t_bf2_0;
    double tt_mse    = t_mse1   - t_mse0;
    double tt_psnr   = t_psnr1  - t_psnr0;
    double tt_ssim   = t_s1     - t_s0;
    double tt_total  = t_total1 - t_total0;

    double tt_sum = tt_read + tt_bf + tt_build + tt_lbg + tt_ent + tt_cvt +
                    tt_dec + tt_delta + tt_huff + tt_dd + tt_rec + tt_bf2 +
                    tt_mse + tt_psnr + tt_ssim;

    printf("\n==================== TIMING BREAKDOWN ====================\n");
    printf("  1) Read image            : %.4f s\n", tt_read);
    printf("  2) Bilateral filter (pre): %.4f s  <- DISABLED (moved)\n", tt_bf);
    printf("  3) Build train vectors   : %.4f s\n", tt_build);
    printf("  4) LBG (wall time)       : %.4f s\n", tt_lbg);
    printf("  4) LBG (CPU  time)       : %.4f s\n", tt_lbg_cpu);
    printf("  5) Entropy (before)      : %.4f s\n", tt_ent);
    printf("  6) Codebook float->u8    : %.4f s\n", tt_cvt);
    printf("  7) Decompress (LBG only) : %.4f s\n", tt_dec);
    printf("  8) Delta encode          : %.4f s\n", tt_delta);
    printf("  9) Huffman               : %.4f s\n", tt_huff);
    printf(" 10) Delta decode          : %.4f s\n", tt_dd);
    printf(" 11) Reconstruct           : %.4f s\n", tt_rec);
    printf(" 11b) Bilateral filter(post): %.4f s\n", tt_bf2);
    printf(" 12) MSE                   : %.4f s\n", tt_mse);
    printf(" 12b) PSNR                 : %.4f s\n", tt_psnr);
    printf(" 13) SSIM                  : %.4f s\n", tt_ssim);
    printf("----------------------------------------------------------\n");
    printf("  Sum of steps             : %.4f s\n", tt_sum);
    printf("  Total (measured)         : %.4f s\n", tt_total);
    printf("  Unaccounted (I/O, printf): %.4f s\n", tt_total - tt_sum);
    printf("==========================================================\n");

    free(codebook);
    free(codebook_data);
    free(labels);
    free(labels_delta_u);
    free(training_set);
    free(image);
    free(reconstructed);
    free(reconstructed_filtered);
    free(reconstructed_lbg);

    return 0;
}

/* ============================================================
   ------------------------ COLOR PATH -----------------------------
   Mirrors seco.c's process_channel() + main() exactly, wrapped as
   functions.
   ============================================================ */
typedef struct {
    double psnr, ssim, mse, cr_system;
    double lbg_time;
    int compressed_bytes;
    uint8_t *original;
    uint8_t *reconstructed;
} ChannelResult;

static ChannelResult process_channel(uint8_t *channel_image, const char *channel_name)
{
    ChannelResult res;
    int original_image_bytes = WIDTH * HEIGHT;

    float *codebook = (float*)calloc((size_t)CODEBOOK_SIZE * VLEN, sizeof(float));
    if (!codebook) { fprintf(stderr, "malloc failed: codebook\n"); exit(EXIT_FAILURE); }

    uint8_t *original_channel = malloc(WIDTH * HEIGHT);
    if (!original_channel) { fprintf(stderr, "malloc failed: original_channel\n"); exit(EXIT_FAILURE); }
    memcpy(original_channel, channel_image, WIDTH * HEIGHT);

    uint8_t *training_set = NULL;
    int num_vectors = build_training_vectors(channel_image, &training_set);
    if (num_vectors <= 0 || !training_set) {
        fprintf(stderr, "Failed to build training vectors.\n");
        exit(EXIT_FAILURE);
    }

    uint8_t *labels = malloc(num_vectors);
    if (!labels) { fprintf(stderr, "malloc failed: labels\n"); exit(EXIT_FAILURE); }
    float *training_f = (float*)malloc((size_t)num_vectors * VLEN * sizeof(float));
    if (!training_f) { fprintf(stderr, "malloc failed: training_f\n"); exit(EXIT_FAILURE); }
    for (int i = 0; i < num_vectors * VLEN; i++)
        training_f[i] = (float)training_set[i];

    double t_lbg0 = wtime();
    lbg(training_f, num_vectors, CODEBOOK_SIZE, labels, codebook, /*verbose=*/1);
    double t_lbg1 = wtime();
    res.lbg_time = t_lbg1 - t_lbg0;
    free(training_f);

    uint8_t *labels_delta_u = malloc(num_vectors);
    if (!labels_delta_u) { fprintf(stderr, "malloc failed: labels_delta_u\n"); exit(EXIT_FAILURE); }
    labels_delta_u[0] = labels[0];
    for (int i = 1; i < num_vectors; i++)
        labels_delta_u[i] = (uint8_t)(labels[i] - labels[i-1] + 128);

    int huff_data_bytes = 0, header_bytes = 0;
    printf("  [%s channel] ", channel_name);
    int huff_total = huffman_on_labels(labels_delta_u, num_vectors, 255,
                                        &huff_data_bytes, &header_bytes);

    int codebook_bytes = CODEBOOK_SIZE * VLEN;
    res.compressed_bytes = codebook_bytes + huff_total;
    res.cr_system = (double)original_image_bytes / (double)res.compressed_bytes;

    labels[0] = labels_delta_u[0];
    for (int i = 1; i < num_vectors; i++)
        labels[i] = labels[i-1] + ((int)labels_delta_u[i] - 128);

    uint8_t *reconstructed = malloc(WIDTH * HEIGHT);
    if (!reconstructed) { fprintf(stderr, "malloc failed: reconstructed\n"); exit(EXIT_FAILURE); }
    decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook, labels);

    uint8_t *reconstructed_filtered = malloc(WIDTH * HEIGHT);
    if (!reconstructed_filtered) { fprintf(stderr, "malloc failed: reconstructed_filtered\n"); exit(EXIT_FAILURE); }
    bilateral_preprocess(reconstructed, reconstructed_filtered, WIDTH, HEIGHT,
                         BF_D, BF_SIGMA_COLOR, BF_SIGMA_SPACE, BF_ALPHA);

    res.mse  = compute_mse(original_channel, reconstructed_filtered, WIDTH*HEIGHT);
    res.psnr = compute_psnr(original_channel, reconstructed_filtered, WIDTH*HEIGHT);
    res.ssim = SSIM_window_based(original_channel, reconstructed_filtered, WIDTH, HEIGHT);
    res.original       = original_channel;
    res.reconstructed  = reconstructed_filtered;
    free(reconstructed);

    printf("PSNR=%.2f dB  SSIM=%.4f  CR(system)=%.2fX  LBG time=%.4fs\n",
           res.psnr, res.ssim, res.cr_system, res.lbg_time);

    free(codebook);
    free(labels);
    free(labels_delta_u);
    free(training_set);
    return res;
}

static int run_color(const char *image_path)
{
    double t_program0 = wtime();

    uint8_t *R = malloc(WIDTH * HEIGHT);
    uint8_t *G = malloc(WIDTH * HEIGHT);
    uint8_t *B = malloc(WIDTH * HEIGHT);
    if (!R || !G || !B) { perror("malloc RGB"); return 1; }

    if (!read_color_image_from_txt(image_path, R, G, B, WIDTH, HEIGHT)) {
        fprintf(stderr, "Failed to read color image from text file.\n");
        return 1;
    }

    printf("===== Processing color image: %s (%dx%d) =====\n", image_path, WIDTH, HEIGHT);

    ChannelResult res_r = process_channel(R, "Red");
    ChannelResult res_g = process_channel(G, "Green");
    ChannelResult res_b = process_channel(B, "Blue");

    int total_samples = 3 * WIDTH * HEIGHT;
    double rgb_mse = (res_r.mse * (WIDTH*HEIGHT) +
                       res_g.mse * (WIDTH*HEIGHT) +
                       res_b.mse * (WIDTH*HEIGHT)) / total_samples;
    double rgb_psnr = (rgb_mse == 0.0) ? 100.0 : 10.0 * log10((255.0*255.0) / rgb_mse);

    int total_original_bytes   = total_samples;
    int total_compressed_bytes = res_r.compressed_bytes + res_g.compressed_bytes + res_b.compressed_bytes;
    double rgb_cr = (double)total_original_bytes / (double)total_compressed_bytes;

    double mean_channelwise_ssim = (res_r.ssim + res_g.ssim + res_b.ssim) / 3.0;
    double total_lbg_time = res_r.lbg_time + res_g.lbg_time + res_b.lbg_time;

    save_bmp_color("original_color.bmp", R, G, B, WIDTH, HEIGHT);
    save_bmp_color("compressed_color.bmp",
                   res_r.reconstructed, res_g.reconstructed, res_b.reconstructed,
                   WIDTH, HEIGHT);

    double t_program1 = wtime();

    printf("\n===== COLOR IMAGE — AGGREGATE RESULTS =====\n");
    printf("RGB PSNR                  : %.2f dB\n", rgb_psnr);
    printf("Mean Channel-wise SSIM    : %.4f\n", mean_channelwise_ssim);
    printf("RGB MSE                   : %.2f\n", rgb_mse);
    printf("RGB CR (system)           : %.2f X\n", rgb_cr);
    printf("Total LBG time (R+G+B)    : %.4f s\n", total_lbg_time);
    printf("Total program time        : %.4f s\n", t_program1 - t_program0);
    printf("Saved: original_color.bmp  compressed_color.bmp\n");
    printf("====================================================================\n");

    free(R); free(G); free(B);
    free(res_r.original); free(res_g.original); free(res_b.original);
    free(res_r.reconstructed); free(res_g.reconstructed); free(res_b.reconstructed);
    return 0;
}

/* ============================================================
   MAIN — picks mode via --gray/--color or auto-detection
   ============================================================ */
int main(int argc, char *argv[])
{
    const char *image_path = (argc > 1) ? argv[1] : "img.txt";
    ImgMode mode = MODE_UNKNOWN;

    if (argc > 2) {
        if      (strcmp(argv[2], "--gray")  == 0) mode = MODE_GRAY;
        else if (strcmp(argv[2], "--color") == 0) mode = MODE_COLOR;
        else {
            fprintf(stderr, "Unknown flag '%s' (expected --gray or --color)\n", argv[2]);
            return 1;
        }
    } else {
        mode = detect_mode_from_file(image_path);
        if (mode == MODE_UNKNOWN) {
            fprintf(stderr,
                "Could not auto-detect image mode for '%s' (token count did not match\n"
                "WIDTH*HEIGHT=%d or WIDTH*HEIGHT*3=%d). Pass --gray or --color explicitly:\n"
                "  %s %s --gray\n  %s %s --color\n",
                image_path, WIDTH*HEIGHT, WIDTH*HEIGHT*3, argv[0], image_path, argv[0], image_path);
            return 1;
        }
        printf("[Mode] auto-detected: %s\n", mode == MODE_GRAY ? "grayscale" : "color");
    }

    if (mode == MODE_GRAY)  return run_grayscale(image_path);
    else                    return run_color(image_path);
}
