/* ============================================================
 *  lbg_pure_mpi.c
 *  --------------------------------------------------------------
 *  LBG codebook compression + Delta encoding + Huffman coding.
 *  The Delta encode/decode and the Huffman stage are parallelised
 *  with PURE MPI.  LBG itself stays sequential on rank 0.
 *
 *  Build  :  mpicc -O3 -o lbg_pure_mpi_exec lbg_pure_mpi.c -lm
 *  Run    :  mpirun -np 4 ./lbg_pure_mpi_exec
 *  Output :  lbg_pure_mpi_results.txt  (auto-saved on rank 0)
 *            lbg_decompress.txt        (LBG-only reconstruction)
 *            decompress.txt            (final reconstruction)
 * ==========================================================*/

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <time.h>
#include <string.h>
#include <mpi.h>

#define WIDTH         512
#define HEIGHT        512
#define BLOCK_SIZE    4
#define DELTA         0.01f
#define EPSILON       0.0001f
#define CODEBOOK_SIZE 64
#define K1            0.01
#define K2            0.03

/* ============================================================
 *  Forward declarations
 * ==========================================================*/
void decompress_image(uint8_t *reconstructed, int width, int height,
                      int block_size, float **codebook, uint8_t *labels);
float distance(const float *a, const uint8_t *b, int len);
double compute_mse(uint8_t *original, uint8_t *reconstructed, int size);
double compute_psnr(uint8_t *original, uint8_t *reconstructed, int size);
double compute_entropy(uint8_t *labels, int num_labels, int codebook_size);

/* ============================================================
 *  Build training vectors from image
 * ==========================================================*/
int build_training_vectors(uint8_t *image, uint8_t **training_set)
{
    int num_blocks_x = WIDTH  / BLOCK_SIZE;
    int num_blocks_y = HEIGHT / BLOCK_SIZE;
    int num_vectors  = num_blocks_x * num_blocks_y;
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

/* ============================================================
 *  Read image pixels from .txt file (one integer per pixel)
 * ==========================================================*/
int read_image_from_txt(const char *filename, uint8_t *image, int width, int height)
{
    FILE *f = fopen(filename, "r");
    if (!f) {
        perror("Error opening image file");
        return 0;
    }
    int val, count = 0;
    while (fscanf(f, "%d", &val) == 1 && count < width * height) {
        if (val < 0)   val = 0;
        if (val > 255) val = 255;
        image[count++] = (uint8_t)val;
    }
    fclose(f);
    if (count != width * height)
        fprintf(stderr, "Warning: expected %d pixels, got %d\n", width * height, count);
    return count == width * height;
}

/* ============================================================
 *  Euclidean distance (squared) between codebook entry and vec
 * ==========================================================*/
float distance(const float *a, const uint8_t *b, int len)
{
    float d = 0;
    for (int i = 0; i < len; i++) {
        float diff = a[i] - b[i];
        d += diff * diff;
    }
    return d;
}

/* ============================================================
 *  LBG (sequential -- runs only on rank 0)
 * ==========================================================*/
void lbg(uint8_t *training, int num_vectors, int vector_len,
         int target_K, uint8_t *labels, float **codebook)
{
    /* Global mean as the initial single codeword */
    for (int j = 0; j < vector_len; j++) {
        float s = 0.0f;
        for (int i = 0; i < num_vectors; i++)
            s += training[i * vector_len + j];
        codebook[0][j] = s / num_vectors;
    }

    int   k = 1;
    float prev_distortion = 1e30f;
    float *sum   = NULL;
    int   *count = NULL;
    int   allocated_k = 0, allocated_len = 0;

    while (k < target_K) {
        /* Split each codeword */
        for (int i = 0; i < k; i++) {
            for (int j = 0; j < vector_len; j++) {
                codebook[k + i][j] = codebook[i][j] * (1.0f - DELTA);
                codebook[i][j]     = codebook[i][j] * (1.0f + DELTA);
            }
        }
        k *= 2;

        int   iterations = 0;
        float improvement = 1.0f;
        float distortion  = 0.0f;

        do {
            if (sum == NULL || allocated_k < k || allocated_len < vector_len) {
                free(sum); free(count);
                sum   = (float*)calloc(k * vector_len, sizeof(float));
                count = (int*)calloc(k, sizeof(int));
                allocated_k   = k;
                allocated_len = vector_len;
            }
            memset(sum,   0, k * vector_len * sizeof(float));
            memset(count, 0, k * sizeof(int));
            distortion = 0.0f;

            for (int i = 0; i < num_vectors; i++) {
                float min_dist  = 1e30f;
                int   min_index = 0;
                uint8_t *v = &training[i * vector_len];

                for (int c = 0; c < k; c++) {
                    float d = distance(codebook[c], v, vector_len);
                    if (d < min_dist) { min_dist = d; min_index = c; }
                }
                labels[i]   = (uint8_t)min_index;
                distortion += min_dist;
                count[min_index]++;
                float *s = &sum[min_index * vector_len];
                for (int j = 0; j < vector_len; j++) s[j] += v[j];
            }

            for (int c = 0; c < k; c++) {
                if (count[c] > 0) {
                    float inv = 1.0f / count[c];
                    float *s  = &sum[c * vector_len];
                    for (int j = 0; j < vector_len; j++)
                        codebook[c][j] = s[j] * inv;
                }
            }
            distortion /= num_vectors;
            improvement = fabs(prev_distortion - distortion) / (distortion + 1e-9f);
            prev_distortion = distortion;
            iterations++;
        } while (iterations < 100 && improvement > EPSILON);
    }
    free(sum); free(count);
}

/* ============================================================
 *  Decompress image from codebook + labels
 * ==========================================================*/
void decompress_image(uint8_t *reconstructed, int width, int height,
                      int block_size, float **codebook, uint8_t *labels)
{
    int blocks_per_row = width  / block_size;
    int blocks_per_col = height / block_size;
    int vec_idx = 0;
    for (int by = 0; by < blocks_per_col; by++) {
        for (int bx = 0; bx < blocks_per_row; bx++) {
            int code_idx = labels[vec_idx];
            for (int r = 0; r < block_size; r++) {
                for (int c = 0; c < block_size; c++) {
                    int img_idx = (by * block_size + r) * width + (bx * block_size + c);
                    int code_block = r * block_size + c;
                    reconstructed[img_idx] = (uint8_t)roundf(codebook[code_idx][code_block]);
                }
            }
            vec_idx++;
        }
    }
}

/* ============================================================
 *  Quality metrics
 * ==========================================================*/
double compute_mse(uint8_t *original, uint8_t *reconstructed, int size)
{
    double mse = 0.0;
    for (int i = 0; i < size; i++) {
        double diff = (double)original[i] - (double)reconstructed[i];
        mse += diff * diff;
    }
    return mse / size;
}

double compute_psnr(uint8_t *original, uint8_t *reconstructed, int size)
{
    double mse = compute_mse(original, reconstructed, size);
    if (mse == 0) return 100.0;
    return 10.0 * log10((255.0 * 255.0) / mse);
}

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

/* ============================================================
 *  HUFFMAN data structures
 * ==========================================================*/
typedef struct HuffNode {
    int                value;
    uint32_t           freq;
    struct HuffNode   *left;
    struct HuffNode   *right;
} HuffNode;

typedef struct { HuffNode **data; int size; int capacity; } MinHeap;
typedef struct { uint64_t bits; int length; } HuffCode;

static MinHeap *heap_create(int cap)
{
    MinHeap *h = (MinHeap*)malloc(sizeof(MinHeap));
    h->data = (HuffNode**)malloc(sizeof(HuffNode*) * cap);
    h->size = 0; h->capacity = cap;
    return h;
}

static HuffNode *huff_new_node(int value, uint32_t freq)
{
    HuffNode *n = (HuffNode*)malloc(sizeof(HuffNode));
    n->value = value; n->freq = freq;
    n->left = n->right = NULL;
    return n;
}

static void heap_swap(HuffNode **a, HuffNode **b)
{
    HuffNode *t = *a; *a = *b; *b = t;
}

static void heap_push(MinHeap *h, HuffNode *node)
{
    int i = h->size++;
    h->data[i] = node;
    while (i > 0) {
        int p = (i - 1) / 2;
        if (h->data[p]->freq <= h->data[i]->freq) break;
        heap_swap(&h->data[p], &h->data[i]);
        i = p;
    }
}

static HuffNode *heap_pop(MinHeap *h)
{
    if (h->size == 0) return NULL;
    HuffNode *root = h->data[0];
    h->data[0] = h->data[--h->size];
    int i = 0;
    while (1) {
        int l = 2 * i + 1;
        int r = 2 * i + 2;
        int smallest = i;
        if (l < h->size && h->data[l]->freq < h->data[smallest]->freq) smallest = l;
        if (r < h->size && h->data[r]->freq < h->data[smallest]->freq) smallest = r;
        if (smallest == i) break;
        heap_swap(&h->data[i], &h->data[smallest]);
        i = smallest;
    }
    return root;
}

static void huff_free_tree(HuffNode *root)
{
    if (!root) return;
    huff_free_tree(root->left);
    huff_free_tree(root->right);
    free(root);
}

static HuffNode *huff_build_tree(uint32_t *freq, int max_symbol)
{
    MinHeap *h = heap_create(max_symbol + 1);
    for (int v = 0; v <= max_symbol; ++v)
        if (freq[v] > 0) heap_push(h, huff_new_node(v, freq[v]));

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

static void huff_build_codes_rec(HuffNode *node, HuffCode *table,
                                 uint64_t code, int length)
{
    if (!node) return;
    if (node->value >= 0) {
        table[node->value].bits   = code;
        table[node->value].length = length;
        return;
    }
    huff_build_codes_rec(node->left,  table,  code << 1,        length + 1);
    huff_build_codes_rec(node->right, table, (code << 1) | 1u,  length + 1);
}

static void huff_build_codes(HuffNode *root, HuffCode *table, int max_symbol)
{
    for (int i = 0; i <= max_symbol; ++i) {
        table[i].bits = 0;
        table[i].length = 0;
    }
    huff_build_codes_rec(root, table, 0, 0);
}

static void huff_decode(uint8_t *encoded, int enc_bytes,
                        HuffNode *root, int original_n, uint8_t *out)
{
    HuffNode *node = root;
    int out_pos = 0;
    for (int i = 0; i < enc_bytes; ++i) {
        uint8_t byte = encoded[i];
        for (int b = 7; b >= 0; --b) {
            if (out_pos >= original_n) return;
            int bit = (byte >> b) & 1;
            node = bit ? node->right : node->left;
            if (node->value >= 0) {
                out[out_pos++] = (uint8_t)node->value;
                node = root;
            }
        }
    }
}

/* ============================================================
 *  MPI-PARALLEL HUFFMAN
 *  - Local histogram + MPI_Allreduce (global freq)
 *  - All ranks build identical tree (deterministic from freq)
 *  - Local bit count + MPI_Exscan -> global bit offset
 *  - Each rank writes its bits at its global offset
 *  - MPI_Reduce(MPI_BOR) merges bitstreams on rank 0
 * ==========================================================*/
static int huffman_on_labels_mpi(uint8_t *labels, int num_labels, int max_symbol,
                                 int *out_huff_data, int *out_header,
                                 int rank, int size, MPI_Comm comm)
{
    int chunk = (num_labels + size - 1) / size;
    int start = rank * chunk;
    int end   = start + chunk;
    if (start > num_labels) start = num_labels;
    if (end   > num_labels) end   = num_labels;

    /* 1) local histogram */
    uint32_t *local_freq = (uint32_t*)calloc(max_symbol + 1, sizeof(uint32_t));
    for (int i = start; i < end; i++) local_freq[labels[i]]++;

    /* 2) global histogram */
    uint32_t *freq = (uint32_t*)calloc(max_symbol + 1, sizeof(uint32_t));
    MPI_Allreduce(local_freq, freq, max_symbol + 1, MPI_UINT32_T, MPI_SUM, comm);
    free(local_freq);

    int used_symbols = 0;
    for (int i = 0; i <= max_symbol; i++) if (freq[i] > 0) used_symbols++;

    /* 3) same Huffman tree on every rank */
    HuffNode *root = huff_build_tree(freq, max_symbol);
    if (!root) {
        if (rank == 0) printf("Huffman: no symbols found!\n");
        free(freq); return 0;
    }

    /* 4) code table */
    HuffCode *table = (HuffCode*)malloc((max_symbol + 1) * sizeof(HuffCode));
    huff_build_codes(root, table, max_symbol);

    /* 5) parallel encoding */
    int local_bits = 0;
    for (int i = start; i < end; i++) local_bits += table[labels[i]].length;

    int my_bit_offset = 0;
    MPI_Exscan(&local_bits, &my_bit_offset, 1, MPI_INT, MPI_SUM, comm);
    if (rank == 0) my_bit_offset = 0;

    int total_bits = 0;
    MPI_Allreduce(&local_bits, &total_bits, 1, MPI_INT, MPI_SUM, comm);
    int total_bytes = (total_bits + 7) / 8;

    /* every rank writes into its private buffer at the global bit offset */
    uint8_t *local_enc = (uint8_t*)calloc(total_bytes + 1, 1);
    int bit_pos = my_bit_offset;
    for (int i = start; i < end; i++) {
        HuffCode hc = table[labels[i]];
        int len = hc.length;
        if (len == 0) continue;
        uint64_t bits = hc.bits;
        for (int b = len - 1; b >= 0; b--) {
            int bit      = (int)((bits >> b) & 1u);
            int byte_idx = bit_pos / 8;
            int bit_idx  = 7 - (bit_pos % 8);
            local_enc[byte_idx] |= (uint8_t)(bit << bit_idx);
            bit_pos++;
        }
    }

    /* merge bitstreams: each bit position is set by exactly one rank,
     * but boundary bytes can be touched by two adjacent ranks ->
     * a bitwise-OR reduction merges them correctly. */
    uint8_t *enc = NULL;
    if (rank == 0) enc = (uint8_t*)calloc(total_bytes + 1, 1);
    MPI_Reduce(local_enc, enc, total_bytes, MPI_BYTE, MPI_BOR, 0, comm);
    free(local_enc);

    int enc_bytes        = total_bytes;
    int header_bytes     = used_symbols * (int)sizeof(uint32_t);
    int total_compressed = header_bytes + enc_bytes;

    if (rank == 0) {
        /* round-trip verification */
        uint8_t *decoded = (uint8_t*)malloc(num_labels);
        huff_decode(enc, enc_bytes, root, num_labels, decoded);
        int ok = 1;
        for (int i = 0; i < num_labels; i++)
            if (labels[i] != decoded[i]) { ok = 0; break; }
        printf("[MPI Huffman] Decode check : %s\n",
               ok ? "OK (labels identical, no distortion)"
                  : "ERROR (mismatch!)");
        free(decoded);
        free(enc);
    }

    if (out_huff_data) *out_huff_data = enc_bytes;
    if (out_header)    *out_header    = header_bytes;

    free(freq); free(table);
    huff_free_tree(root);
    return total_compressed;
}

/* ============================================================
 *  Window-based SSIM (Gaussian 9x9 weights, ignore borders)
 * ==========================================================*/
double gaussian11x11[11][11] = {
    {0.0003,0.0013,0.0034,0.0053,0.0062,0.0053,0.0034,0.0013,0.0003},
    {0.0013,0.0053,0.0133,0.0209,0.0245,0.0209,0.0133,0.0053,0.0013},
    {0.0034,0.0133,0.0334,0.0525,0.0616,0.0525,0.0334,0.0133,0.0034},
    {0.0053,0.0209,0.0525,0.0826,0.0970,0.0826,0.0525,0.0209,0.0053},
    {0.0062,0.0245,0.0616,0.0970,0.1139,0.0970,0.0616,0.0245,0.0062},
    {0.0053,0.0209,0.0525,0.0826,0.0970,0.0826,0.0525,0.0209,0.0053},
    {0.0034,0.0133,0.0334,0.0525,0.0616,0.0525,0.0334,0.0133,0.0034},
    {0.0013,0.0053,0.0133,0.0209,0.0245,0.0209,0.0133,0.0053,0.0013},
    {0.0003,0.0013,0.0034,0.0053,0.0062,0.0053,0.0034,0.0013,0.0003}
};

double SSIM_window_based(unsigned char *img1, unsigned char *img2, int W, int H)
{
    double ssim_total = 0.0;
    int count = 0;
    for (int i = 5; i < H - 5; i++) {
        for (int j = 5; j < W - 5; j++) {
            double mu_x = 0, mu_y = 0;
            for (int u = -5; u <= 5; u++)
                for (int v = -5; v <= 5; v++) {
                    double w = gaussian11x11[u+5][v+5];
                    mu_x += w * img1[(i+u)*W + (j+v)];
                    mu_y += w * img2[(i+u)*W + (j+v)];
                }
            double sigma_x = 0, sigma_y = 0, sigma_xy = 0;
            for (int u = -5; u <= 5; u++)
                for (int v = -5; v <= 5; v++) {
                    double w = gaussian11x11[u+5][v+5];
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
 *  MAIN  (MPI driver)
 * ==========================================================*/
int main(int argc, char **argv)
{
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    double t_wall_start = MPI_Wtime();
    int original_image_bytes = WIDTH * HEIGHT;

    float       **codebook        = NULL;
    uint8_t      *image           = NULL;
    uint8_t      *training_set    = NULL;
    uint8_t      *labels          = NULL;
    uint8_t      *labels_delta_u  = NULL;
    uint8_t      *reconstructed   = NULL;
    uint8_t      *reconstructed_lbg = NULL;
    uint8_t      *codebook_data   = NULL;
    int           num_vectors     = 0;
    double        time_lbg = 0.0;
    double        H = 0.0, H_delta = 0.0;

    /* ===== STEP A : rank 0 reads image, builds training, runs LBG ===== */
    if (rank == 0) {
        codebook = (float**)malloc(CODEBOOK_SIZE * sizeof(float*));
        for (int i = 0; i < CODEBOOK_SIZE; i++)
            codebook[i] = (float*)calloc(BLOCK_SIZE * BLOCK_SIZE, sizeof(float));

        image = (uint8_t*)malloc(WIDTH * HEIGHT);
        if (!image) { fprintf(stderr, "malloc image failed\n"); MPI_Abort(MPI_COMM_WORLD, 1); }
        if (!read_image_from_txt("img.txt", image, WIDTH, HEIGHT)) {
            fprintf(stderr, "Failed to read image from text file.\n");
            MPI_Abort(MPI_COMM_WORLD, 1);
        }

        num_vectors = build_training_vectors(image, &training_set);
        printf("[rank 0] Built %d training vectors (each %d elements)\n",
               num_vectors, BLOCK_SIZE * BLOCK_SIZE);

        labels = (uint8_t*)malloc(num_vectors);
        if (!labels) { perror("malloc labels"); MPI_Abort(MPI_COMM_WORLD, 1); }

        clock_t t1 = clock();
        lbg(training_set, num_vectors, BLOCK_SIZE * BLOCK_SIZE,
            CODEBOOK_SIZE, labels, codebook);
        clock_t t2 = clock();
        time_lbg = (double)(t2 - t1) / CLOCKS_PER_SEC;

        printf("\n[rank 0] Final codebook (first 10 codewords):\n");
        for (int c = 0; c < 10; c++) {
            printf("  Codeword %d: ", c);
            for (int j = 0; j < BLOCK_SIZE * BLOCK_SIZE; j++)
                printf("%.1f ", codebook[c][j]);
            printf("\n");
        }
        printf("==================================\n");
        printf("Time (LBG only)         : %.4f s\n", time_lbg);

        H = compute_entropy(labels, num_vectors, CODEBOOK_SIZE);
        printf("Entropy before Huffman  : %.3f bits/symbol\n", H);

        codebook_data = (uint8_t*)malloc(CODEBOOK_SIZE * BLOCK_SIZE * BLOCK_SIZE);
        for (int k = 0; k < CODEBOOK_SIZE; k++)
            for (int i = 0; i < BLOCK_SIZE * BLOCK_SIZE; i++)
                codebook_data[k * (BLOCK_SIZE * BLOCK_SIZE) + i] =
                    (uint8_t)roundf(codebook[k][i]);
        printf("Codebook -> uint8_t (%d bytes)\n",
               CODEBOOK_SIZE * BLOCK_SIZE * BLOCK_SIZE);

        reconstructed_lbg = (uint8_t*)malloc(WIDTH * HEIGHT);
        decompress_image(reconstructed_lbg, WIDTH, HEIGHT, BLOCK_SIZE, codebook, labels);
        FILE *flbg = fopen("lbg_decompress.txt", "w");
        for (size_t i = 0; i < (size_t)WIDTH * HEIGHT; i++)
            fprintf(flbg, "%u\n", reconstructed_lbg[i]);
        fclose(flbg);
    }

    /* ===== STEP B : broadcast num_vectors + labels ===== */
    MPI_Bcast(&num_vectors, 1, MPI_INT, 0, MPI_COMM_WORLD);
    if (rank != 0) labels = (uint8_t*)malloc(num_vectors);
    MPI_Bcast(labels, num_vectors, MPI_BYTE, 0, MPI_COMM_WORLD);

    /* per-rank chunk layout */
    int chunk = (num_vectors + size - 1) / size;
    int start = rank * chunk;
    int end   = start + chunk;
    if (start > num_vectors) start = num_vectors;
    if (end   > num_vectors) end   = num_vectors;
    int local_n = end - start;

    int *recvcounts = (int*)malloc(size * sizeof(int));
    int *displs     = (int*)malloc(size * sizeof(int));
    for (int r = 0; r < size; r++) {
        int s = r * chunk, e = s + chunk;
        if (s > num_vectors) s = num_vectors;
        if (e > num_vectors) e = num_vectors;
        recvcounts[r] = e - s;
        displs[r]     = s;
    }

    labels_delta_u = (uint8_t*)malloc(num_vectors);

    /* ===== STEP C : parallel DELTA ENCODE (MPI) ===== */
    MPI_Barrier(MPI_COMM_WORLD);
    double te1 = MPI_Wtime();

    uint8_t *local_delta = (uint8_t*)malloc(local_n > 0 ? local_n : 1);
    for (int i = start; i < end; i++) {
        if (i == 0)
            local_delta[i - start] = labels[0];
        else
            local_delta[i - start] = (uint8_t)((int)labels[i] - (int)labels[i-1] + 128);
    }
    MPI_Allgatherv(local_delta, local_n, MPI_BYTE,
                   labels_delta_u, recvcounts, displs, MPI_BYTE,
                   MPI_COMM_WORLD);
    free(local_delta);

    double te2 = MPI_Wtime();
    double time_delta_enc = te2 - te1;

    if (rank == 0) {
        H_delta = compute_entropy(labels_delta_u, num_vectors, 256);
        printf("Entropy after Delta     : %.3f bits/symbol\n", H_delta);
        printf("First 20 delta_u        : ");
        for (int i = 0; i < 20; i++) printf("%d ", labels_delta_u[i]);
        printf("\n");
        int zero_count = 0;
        for (int i = 0; i < num_vectors; i++)
            if (labels_delta_u[i] == 128) zero_count++;
        printf("Delta zero ratio        : %.2f %%\n",
               100.0 * zero_count / num_vectors);
        int min_d = 9999, max_d = -9999;
        for (int i = 0; i < num_vectors; i++) {
            int d = (int)labels_delta_u[i] - 128;
            if (d < min_d) min_d = d;
            if (d > max_d) max_d = d;
        }
        printf("Delta range             : [%d , %d]\n", min_d, max_d);
        int max_run = 1, run = 1;
        for (int i = 1; i < num_vectors; i++) {
            if (labels_delta_u[i] == labels_delta_u[i-1]) {
                run++;
                if (run > max_run) max_run = run;
            } else run = 1;
        }
        printf("Max delta run           : %d\n", max_run);
        printf("Time (Delta encode MPI) : %.6f s\n", time_delta_enc);
    }

    /* ===== STEP D : parallel HUFFMAN (MPI) ===== */
    int huff_data_bytes = 0;
    int header_bytes    = 0;

    MPI_Barrier(MPI_COMM_WORLD);
    double th1 = MPI_Wtime();
    int huff_total = huffman_on_labels_mpi(labels_delta_u, num_vectors, 255,
                                           &huff_data_bytes, &header_bytes,
                                           rank, size, MPI_COMM_WORLD);
    double th2 = MPI_Wtime();
    double time_huff = th2 - th1;

    if (rank == 0) {
        printf("Time (Huffman MPI)      : %.6f s\n", time_huff);
        printf("Huffman data bytes      : %d\n", huff_data_bytes);
        printf("Huffman total bytes     : %d\n", huff_total);
        printf("Header bytes            : %d\n", header_bytes);
    }

    /* ===== STEP E : parallel DELTA DECODE (MPI prefix sum) ===== */
    MPI_Barrier(MPI_COMM_WORLD);
    double td1 = MPI_Wtime();

    int local_sum = 0;
    for (int i = start; i < end; i++) {
        if (i == 0) continue;
        local_sum += (int)labels_delta_u[i] - 128;
    }
    int my_offset = 0;
    MPI_Exscan(&local_sum, &my_offset, 1, MPI_INT, MPI_SUM, MPI_COMM_WORLD);
    if (rank == 0) my_offset = 0;

    uint8_t *local_labels = (uint8_t*)malloc(local_n > 0 ? local_n : 1);
    int running = (int)labels_delta_u[0] + my_offset;
    for (int i = start; i < end; i++) {
        if (i == 0) {
            local_labels[0] = labels_delta_u[0];
        } else {
            running += (int)labels_delta_u[i] - 128;
            local_labels[i - start] = (uint8_t)(running & 0xFF);
        }
    }
    MPI_Allgatherv(local_labels, local_n, MPI_BYTE,
                   labels, recvcounts, displs, MPI_BYTE,
                   MPI_COMM_WORLD);
    free(local_labels);

    double td2 = MPI_Wtime();
    double time_delta_dec = td2 - td1;

    if (rank == 0)
        printf("Time (Delta dec MPI)    : %.6f s\n", time_delta_dec);

    /* ===== STEP F : reconstruct + metrics + tables + auto-save ===== */
    double mse = 0.0, psnr = 0.0, ssim = 0.0;
    double CR_huff_data = 0.0, CR_huff_total = 0.0, CR_system = 0.0;
    double bpp = 0.0;
    int    codebook_bytes = CODEBOOK_SIZE * BLOCK_SIZE * BLOCK_SIZE;

    if (rank == 0) {
        reconstructed = (uint8_t*)malloc(WIDTH * HEIGHT);
        decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook, labels);

        FILE *file1 = fopen("decompress.txt", "w");
        for (size_t i = 0; i < (size_t)WIDTH * HEIGHT; i++)
            fprintf(file1, "%u\n", reconstructed[i]);
        fclose(file1);

        mse  = compute_mse (image, reconstructed, WIDTH * HEIGHT);
        psnr = compute_psnr(image, reconstructed, WIDTH * HEIGHT);
        ssim = SSIM_window_based(image, reconstructed, WIDTH, HEIGHT);

        int original_labels = num_vectors;
        CR_huff_data  = (huff_data_bytes > 0) ? (double)original_labels / huff_data_bytes : 0.0;
        CR_huff_total = (huff_total      > 0) ? (double)original_labels / huff_total      : 0.0;
        CR_system     = (double)original_image_bytes / (double)(codebook_bytes + huff_total);
        bpp           = (CR_system > 0) ? 8.0 / CR_system : 0.0;

        double t_wall_end = MPI_Wtime();
        double total_time = t_wall_end - t_wall_start;

        printf("\n");
        printf("+====================================================+\n");
        printf("|         LBG + Delta + Huffman -- PURE MPI          |\n");
        printf("+====================================================+\n");

        printf("\n+----- TIMING TABLE (seconds) -----------------------+\n");
        printf("| %-34s | %13s |\n", "Phase", "Time (s)");
        printf("+------------------------------------+---------------+\n");
        printf("| %-34s | %13d |\n",  "MPI processes",            size);
        printf("| %-34s | %13.4f |\n", "LBG (sequential, rank 0)", time_lbg);
        printf("| %-34s | %13.6f |\n", "Delta encode (MPI)",       time_delta_enc);
        printf("| %-34s | %13.6f |\n", "Huffman (MPI)",            time_huff);
        printf("| %-34s | %13.6f |\n", "Delta decode (MPI scan)",  time_delta_dec);
        printf("| %-34s | %13.4f |\n", "Total wall time",          total_time);
        printf("+------------------------------------+---------------+\n");

        printf("\n+----- COMPRESSION TABLE ----------------------------+\n");
        printf("| %-34s | %13s |\n", "Metric", "Value");
        printf("+------------------------------------+---------------+\n");
        printf("| %-34s | %13d |\n",  "Original image bytes",     original_image_bytes);
        printf("| %-34s | %13d |\n",  "Codebook bytes",           codebook_bytes);
        printf("| %-34s | %13d |\n",  "Huffman data bytes",       huff_data_bytes);
        printf("| %-34s | %13d |\n",  "Huffman header bytes",     header_bytes);
        printf("| %-34s | %13d |\n",  "Huffman total bytes",      huff_total);
        printf("| %-34s | %13.4f |\n", "Entropy before delta",    H);
        printf("| %-34s | %13.4f |\n", "Entropy after delta",     H_delta);
        printf("| %-34s | %13.4f |\n", "CR (Huffman data only)",  CR_huff_data);
        printf("| %-34s | %13.4f |\n", "CR (Huffman total)",      CR_huff_total);
        printf("| %-34s | %13.4f |\n", "CR (System LBG+Huff)",    CR_system);
        printf("| %-34s | %13.4f |\n", "BPP (bits / pixel)",      bpp);
        printf("+------------------------------------+---------------+\n");

        printf("\n+----- QUALITY TABLE --------------------------------+\n");
        printf("| %-34s | %13s |\n", "Metric", "Value");
        printf("+------------------------------------+---------------+\n");
        printf("| %-34s | %13.4f |\n", "MSE",       mse);
        printf("| %-34s | %13.4f |\n", "PSNR (dB)", psnr);
        printf("| %-34s | %13.4f |\n", "SSIM",      ssim);
        printf("+------------------------------------+---------------+\n");

        /* ===== Auto-save full results to file ===== */
        FILE *fres = fopen("lbg_pure_mpi_results.txt", "w");
        if (fres) {
            fprintf(fres, "==========================================\n");
            fprintf(fres, "  LBG + Delta + Huffman -- PURE MPI RESULTS\n");
            fprintf(fres, "==========================================\n");
            fprintf(fres, "MPI processes              : %d\n",  size);
            fprintf(fres, "Image                      : %dx%d\n", WIDTH, HEIGHT);
            fprintf(fres, "Block size                 : %d\n",  BLOCK_SIZE);
            fprintf(fres, "Codebook size              : %d\n",  CODEBOOK_SIZE);
            fprintf(fres, "Number of vectors          : %d\n",  num_vectors);
            fprintf(fres, "\n--- Timing (seconds) ---\n");
            fprintf(fres, "LBG (sequential, rank 0)   : %.6f\n", time_lbg);
            fprintf(fres, "Delta encode (MPI)         : %.6f\n", time_delta_enc);
            fprintf(fres, "Huffman (MPI)              : %.6f\n", time_huff);
            fprintf(fres, "Delta decode (MPI scan)    : %.6f\n", time_delta_dec);
            fprintf(fres, "Total wall time            : %.6f\n", total_time);
            fprintf(fres, "\n--- Compression ---\n");
            fprintf(fres, "Original image bytes       : %d\n",  original_image_bytes);
            fprintf(fres, "Codebook bytes             : %d\n",  codebook_bytes);
            fprintf(fres, "Huffman data bytes         : %d\n",  huff_data_bytes);
            fprintf(fres, "Huffman header bytes       : %d\n",  header_bytes);
            fprintf(fres, "Huffman total bytes        : %d\n",  huff_total);
            fprintf(fres, "Entropy before delta       : %.4f\n", H);
            fprintf(fres, "Entropy after delta        : %.4f\n", H_delta);
            fprintf(fres, "CR (Huffman data only)     : %.4f\n", CR_huff_data);
            fprintf(fres, "CR (Huffman total)         : %.4f\n", CR_huff_total);
            fprintf(fres, "CR (System LBG+Huff)       : %.4f\n", CR_system);
            fprintf(fres, "BPP (bits/pixel)           : %.4f\n", bpp);
            fprintf(fres, "\n--- Quality ---\n");
            fprintf(fres, "MSE                        : %.4f\n", mse);
            fprintf(fres, "PSNR (dB)                  : %.4f\n", psnr);
            fprintf(fres, "SSIM                       : %.4f\n", ssim);
            fclose(fres);
            printf("\n[rank 0] Results auto-saved to: lbg_pure_mpi_results.txt\n");
            printf("[rank 0] Decompressed image    : decompress.txt\n");
            printf("[rank 0] LBG-only image        : lbg_decompress.txt\n");
        } else {
            fprintf(stderr, "[rank 0] WARNING: cannot open lbg_pure_mpi_results.txt\n");
        }
    }

    /* ===== Cleanup ===== */
    free(recvcounts);
    free(displs);
    free(labels);
    free(labels_delta_u);

    if (rank == 0) {
        for (int i = 0; i < CODEBOOK_SIZE; i++) free(codebook[i]);
        free(codebook);
        free(training_set);
        free(image);
        free(reconstructed);
        free(reconstructed_lbg);
        free(codebook_data);
    }

    MPI_Finalize();
    return 0;
}
