/*
 * ============================================================
 *  lbg_parallel_merged.c
 *
 *  MPI-PARALLEL LBG (Linde-Buzo-Gray) vector-quantization image
 *  compression. Merges the two previously separate parallel
 *  programs into ONE binary that handles both GRAYSCALE and
 *  COLOR input, selected at RUN TIME by an explicit flag or by
 *  auto-detection of the input file's pixel format (same
 *  convention as the sequential merged file, lbg_sequential_merged.c).
 *
 *  Source of the two original implementations:
 *      - grayscale parallel (MPI) : pag.c (1194 lines)
 *      - color parallel     (MPI) : pco.c (1104 lines)
 *
 *  Both modes use the SAME SPMD engine: rank 0 reads the image
 *  and builds training vectors; vectors are distributed across
 *  ranks (equal split for np<=4, speed-weighted split with a
 *  light calibrate_speed() self-benchmark for np>4, or forced
 *  via the VQ_STRATEGY=equal|adaptive environment variable,
 *  exactly as both originals did); each rank runs parallel_lbg()
 *  with MPI_Allreduce at every Lloyd iteration; labels are
 *  gathered back to rank 0 (MPI_Gatherv) for delta+Huffman
 *  coding, decompression and the post-compression bilateral
 *  filter; SSIM is computed IN PARALLEL across all ranks after
 *  broadcasting the two images (MPI_Bcast + MPI_Allreduce), as
 *  in both originals. Color mode runs that whole per-channel
 *  pipeline three times (R, then G, then B), with the vector
 *  distribution computed ONCE up front and reused for all three
 *  channels (pco.c's documented optimization, since num_vectors
 *  is identical for R/G/B).
 *
 *  ------------------------------------------------------------
 *  CLI convention (mirrors lbg_sequential_merged.c for consistency):
 *
 *      mpirun -np <N> ./lbg_par <image_path> [--gray|--color]
 *
 *      argv[1] = path to the image (same text formats as the
 *                sequential file: one int/pixel for grayscale,
 *                "R G B" ints/pixel for color). Default "img.txt".
 *      argv[2] = optional explicit "--gray" or "--color". If
 *                omitted, rank 0 auto-detects the mode by
 *                pre-scanning the file's token count exactly as
 *                the sequential file does, then MPI_Bcasts the
 *                resulting mode to every other rank (only rank 0
 *                touches the filesystem for this, matching how
 *                only rank 0 does all image I/O elsewhere in both
 *                originals).
 *
 *  Compile:
 *      mpicc -O2 -Wall -o lbg_par lbg_parallel_merged.c -lm
 *
 *  Run examples:
 *      mpirun -np 4 --allow-run-as-root ./lbg_par brain_512.txt --gray
 *      mpirun -np 4 --allow-run-as-root ./lbg_par parrot_512.txt --color
 *      mpirun -np 2 --allow-run-as-root ./lbg_par brain_512.txt        (auto-detected)
 *      VQ_STRATEGY=equal    mpirun -np 8 --allow-run-as-root ./lbg_par img.txt --gray
 *      VQ_STRATEGY=adaptive mpirun -np 8 --allow-run-as-root ./lbg_par img.txt --gray
 *
 *  ------------------------------------------------------------
 *  Judgment calls made while merging:
 *
 *   1) Mode selection needs one MPI_Bcast that has no equivalent
 *      in either original (each original binary only ever ran
 *      one mode): rank 0 resolves the --gray/--color flag or
 *      auto-detects it, then MPI_Bcast's a single int to all
 *      ranks before the SPMD pipeline starts. This is the only
 *      MPI collective added beyond what pag.c/pco.c already had.
 *
 *   2) decompress_image(): pag.c took `float **codebook` (array
 *      of per-codeword pointers, built solely so rank 0 could
 *      print codewords in a loop) while pco.c already used the
 *      flat contiguous `float *codebook_flat` coming straight out
 *      of parallel_lbg(). This merged file standardizes on the
 *      flat float* form everywhere (as pco.c and both sequential
 *      files already did) and drops pag.c's float** wrapper; the
 *      printed codeword values in grayscale mode are unchanged,
 *      only the C-level representation is unified, indexing
 *      codebook_flat[c*VLEN+j] directly in the print loop instead.
 *
 *   3) huffman_on_labels(): pag.c's copy had extra debug printf's
 *      ("CHECK before encode:", "DEBUG: used_symbols=...", "First
 *      10 labels after Huffman decode:") not present in pco.c or
 *      either sequential file. pco.c's clean version (no debug
 *      prints, same encode/decode logic and same return values)
 *      is kept here for both modes; this only removes stdout
 *      noise from grayscale-mode runs, changing no computed value.
 *
 *   4) parallel_lbg()/calibrate_speed()/distance16f(): byte-for-
 *      byte identical between pag.c and pco.c already (confirmed
 *      while reading both files function by function) except for
 *      an internal `enum { VLEN = 16 }` in pag.c vs. the top-level
 *      `#define VLEN (BLOCK_SIZE*BLOCK_SIZE)` macro pco.c relies
 *      on; both evaluate to 16, so the shared VLEN macro is used
 *      throughout with no behavior change.
 *
 *   5) build_training_vectors / read_image_from_txt / bilateral_preprocess
 *      / compute_mse / compute_psnr / compute_entropy / SSIM
 *      (gaussian window + parallel reduction): byte-for-byte
 *      identical between pag.c and pco.c already, kept once each.
 * ============================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <time.h>
#include <string.h>
#include <mpi.h>

#define WIDTH 512
#define HEIGHT 512
#define BLOCK_SIZE 4
#define DELTA 0.01f
#define EPSILON 0.0001f
#define CODEBOOK_SIZE 64
#define MAX_ITER 100
#define K1 0.01
#define K2 0.03
#define VLEN (BLOCK_SIZE * BLOCK_SIZE)   /* = 16 */

#define BF_D            5
#define BF_SIGMA_COLOR  20.0f
#define BF_SIGMA_SPACE  20.0f
#define BF_ALPHA        0.8f

/* ============================================================
   ---------------------- SHARED HELPERS -----------------------
   (identical between pag.c and pco.c; kept once)
   ============================================================ */

void save_bmp_gray(const char *filename, uint8_t *data, int width, int height)
{
    int row_padded = (width + 3) & ~3;
    int img_size   = row_padded * height;
    int file_size  = 54 + 1024 + img_size;
    int data_offset = 54 + 1024;

    uint8_t header[54] = {0};
    header[0] = 'B'; header[1] = 'M';
    header[2] = file_size & 0xFF;
    header[3] = (file_size >> 8)  & 0xFF;
    header[4] = (file_size >> 16) & 0xFF;
    header[5] = (file_size >> 24) & 0xFF;
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
        uint8_t e[4] = {(uint8_t)i, (uint8_t)i, (uint8_t)i, 0};
        fwrite(e, 1, 4, f);
    }
    uint8_t pad[3] = {0};
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
            uint8_t pixel[3] = { B[idx], G[idx], R[idx] };
            fwrite(pixel, 1, 3, f);
        }
        if (row_padded - row_bytes > 0)
            fwrite(pad, 1, row_padded - row_bytes, f);
    }
    fclose(f);
}

static void __attribute__((unused)) bilateral_preprocess(const uint8_t *src, uint8_t *dst,
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

/* ============================================================
   [BFPAR] Distributed post-compression bilateral filter.
   bilateral_rows(): the SAME per-pixel arithmetic as bilateral_preprocess() (the original
   is kept untouched above), but computes only rows [y0,y1) and writes them to a band
   buffer (dst[(y-y0)*W + x]). src must hold the FULL image. Every output pixel depends
   only on src, so the result is bit-identical to the full-image call for ANY row split.
   ============================================================ */
static void bilateral_rows(const uint8_t *src, uint8_t *dst,
                           int W, int H, int y0, int y1,
                           int d, float sigmaColor, float sigmaSpace, float alpha)
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

    for (int y = y0; y < y1; y++) {
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
            dst[(y - y0) * W + x] = (uint8_t)(blended + 0.5f);
        }
    }
    free(gs);
}

/* Row boundaries y_start[0..size]: rank r filters rows [y_start[r], y_start[r+1]).
   Proportional to vec_counts, so the equal/adaptive (speed-weighted) distribution
   already chosen for LBG is reused for the filter as well. */
static void bf_row_bounds(int size, const int *vec_counts, int num_vectors, int *y_start)
{
    long long cum = 0;
    y_start[0] = 0;
    for (int r = 0; r < size; r++) {
        cum += vec_counts[r];
        long long e = ((long long)HEIGHT * cum + num_vectors / 2) / num_vectors;
        y_start[r + 1] = (r == size - 1) ? HEIGHT : (int)e;
    }
}

/* Collective (all ranks must call). img: valid input on rank 0, W*H buffer on the others.
   out: W*H output buffer on rank 0 only (ignored elsewhere). */
static void parallel_bilateral(uint8_t *img, uint8_t *out, int rank, int size,
                               const int *vec_counts, int num_vectors)
{
    MPI_Bcast(img, WIDTH * HEIGHT, MPI_UINT8_T, 0, MPI_COMM_WORLD);

    int *ys  = (int *)malloc((size_t)(size + 1) * sizeof(int));
    int *cnt = (int *)malloc((size_t)size * sizeof(int));
    int *dsp = (int *)malloc((size_t)size * sizeof(int));
    bf_row_bounds(size, vec_counts, num_vectors, ys);
    for (int r = 0; r < size; r++) {
        cnt[r] = (ys[r + 1] - ys[r]) * WIDTH;
        dsp[r] = ys[r] * WIDTH;
    }

    uint8_t *band = (uint8_t *)malloc((size_t)cnt[rank] + 1);
    bilateral_rows(img, band, WIDTH, HEIGHT, ys[rank], ys[rank + 1],
                   BF_D, BF_SIGMA_COLOR, BF_SIGMA_SPACE, BF_ALPHA);
    MPI_Gatherv(band, cnt[rank], MPI_UINT8_T,
                out, cnt, dsp, MPI_UINT8_T, 0, MPI_COMM_WORLD);

    free(band); free(ys); free(cnt); free(dsp);
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
    if (!f) { perror("Error opening image file"); return 0; }
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

static inline float distance16f(const float * __restrict__ a,
                                 const float * __restrict__ b)
{
    float d = 0.0f;
    for (int i = 0; i < 16; i++) {
        float diff = a[i] - b[i];
        d += diff * diff;
    }
    return d;
}

/* micro-benchmark mirroring the LBG assignment kernel; returns this
   rank's throughput in "distance comparisons per second" so vectors
   can be handed out proportional to measured speed (np>4 path). */
static double calibrate_speed(void)
{
    enum { NV = 512, NC = 64, REP = 2, CVLEN = 16 };
    float *v  = (float *)malloc((size_t)NV * CVLEN * sizeof(float));
    float *cb = (float *)malloc((size_t)NC * CVLEN * sizeof(float));
    if (!v || !cb) { free(v); free(cb); return 1.0; }

    for (int i = 0; i < NV * CVLEN; i++)
        v[i]  = (float)(((unsigned)i * 1103515245u + 12345u) & 255u);
    for (int i = 0; i < NC * CVLEN; i++)
        cb[i] = (float)(((unsigned)i * 22695477u + 1u) & 255u);

    volatile float sink = 0.0f;
    double t0 = MPI_Wtime();
    for (int r = 0; r < REP; r++) {
        for (int i = 0; i < NV; i++) {
            const float *x = v + i * CVLEN;
            float best = 1e30f;
            for (int c = 0; c < NC; c++) {
                float d = distance16f(cb + c * CVLEN, x);
                if (d < best) best = d;
            }
            sink += best;
        }
    }
    double dt = MPI_Wtime() - t0;
    free(v); free(cb);
    (void)sink;
    if (dt <= 0.0) dt = 1e-6;
    return (double)REP * (double)NV * (double)NC / dt;
}

/* Returns the TOTAL number of Lloyd iterations summed over all split stages
   (identical on every rank, since the stopping test uses the Allreduce'd
   distortion). Mirrors the return value of sequential lbg() in sem1.c. */
int parallel_lbg(const float *local_vf, int local_n, int num_vectors,
                   int vlen, int K, float *codebook, uint8_t *local_labels,
                   int rank, int size, int verbose)
{
    /* [TIMERFIX2] The last parameter was previously named cb_chunk and was
       completely unused ((void)cb_chunk; discarded it) -- the printf lines
       below ran UNCONDITIONALLY on rank 0 regardless of what was passed in,
       unlike the sequential lbg() in sem/sem1, whose printf lines ARE gated
       by a real verbose flag (verbose=0 at every call site -> silent).
       This made parallel LBG time include ~10-12 printf() calls on rank 0
       that the sequential LBG time never included -- a real (if numerically
       tiny, <0.5%) asymmetry in the one metric meant to be a clean,
       apples-to-apples comparison. Fixed here: the parameter is reused as a
       genuine verbose flag and both printf calls are gated on it, matching
       sequential lbg()'s behavior exactly. All call sites in this file pass
       0, so by default NO printing happens during the timed LBG region on
       either path now. */
    (void)size; (void)vlen;

    int buf_capacity = K * VLEN + K + 1;
    float *buf = (float *)calloc(buf_capacity, sizeof(float));

    int k = 1;
    int total_iters = 0;
    while (k < K) {
        for (int i = k - 1; i >= 0; i--)
            for (int j = 0; j < VLEN; j++) {
                float v = codebook[i * VLEN + j];
                codebook[(k + i) * VLEN + j] = v * (1.0f - DELTA);
                codebook[i        * VLEN + j] = v * (1.0f + DELTA);
            }
        k = (k * 2 > K) ? K : k * 2;

        const int sum_off  = 0;
        const int cnt_off  = k * VLEN;
        const int dist_off = cnt_off + k;
        const int active   = dist_off + 1;

        float prev_dist   = 1e30f;
        float improvement = 1.0f;
        int   iter        = 0;

        do {
            memset(buf, 0, active * sizeof(float));

            for (int i = 0; i < local_n; i++) {
                const float *v = local_vf + i * VLEN;
                float best = 1e30f;
                int   bi   = 0;
                for (int c = 0; c < k; c++) {
                    float d = distance16f(codebook + c * VLEN, v);
                    if (d < best) { best = d; bi = c; }
                }
                local_labels[i]    = (uint8_t)bi;
                buf[dist_off]     += best;
                buf[cnt_off + bi] += 1.0f;
                float *s = buf + sum_off + bi * VLEN;
                for (int j = 0; j < VLEN; j++)
                    s[j] += v[j];
            }

            MPI_Allreduce(MPI_IN_PLACE, buf, active,
                          MPI_FLOAT, MPI_SUM, MPI_COMM_WORLD);

            float global_dist = buf[dist_off] / (float)num_vectors;

            for (int c = 0; c < k; c++) {
                float cnt = buf[cnt_off + c];
                if (cnt > 0.0f) {
                    float inv = 1.0f / cnt;
                    float *s  = buf + sum_off + c * VLEN;
                    for (int j = 0; j < VLEN; j++)
                        codebook[c * VLEN + j] = s[j] * inv;
                }
            }

            improvement = fabsf(prev_dist - global_dist) / (global_dist + 1e-9f);
            prev_dist   = global_dist;
            iter++;

            if (rank == 0 && verbose && iter == 1)
                printf("k=%3d iter=%3d distortion=%.4f  (first)\n", k, iter, prev_dist);

        } while (iter < MAX_ITER && improvement > EPSILON);
        total_iters += iter;

        if (rank == 0 && verbose)
            printf("k=%3d iter=%3d distortion=%.4f  (converged)\n", k, iter, prev_dist);
    }
    free(buf);
    return total_iters;
}

/* flat float* codebook everywhere (see judgment call #2) */
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
                    int pos = r*block_size + c;
                    reconstructed[img_idx] =
                        (uint8_t)roundf(codebook[code_idx * VLEN + pos]);
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

/* ========================  HUFFMAN  (shared, clean version — see
   judgment call #3: pag.c's debug prints were dropped) ========== */
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
    for (int i = 0; i < num_labels; ++i)
        if (labels[i] != decoded[i]) { ok = 0; break; }
    printf("Decode check: %s\n",
           ok ? "OK (labels identical, no distortion)" : "ERROR (mismatch!)");

    if (out_huff_data) *out_huff_data = enc_bytes;
    if (out_header)    *out_header    = header_bytes;

    free(freq); free(table); free(enc); free(decoded);
    huff_free_tree(root);
    return total_compressed;
}

/* ============================================================
   SSIM — parallel version, identical between pag.c and pco.c
   ============================================================ */
static const double (*ssim_gaussian_window(void))[11]
{
    static double gw[11][11];
    static int initialized = 0;
    if (!initialized) {
        const double sigma = 1.5;
        const double two_s2 = 2.0 * sigma * sigma;
        double sum = 0.0;
        for (int u = -5; u <= 5; u++)
            for (int v = -5; v <= 5; v++) {
                double g = exp(-((double)(u*u + v*v)) / two_s2);
                gw[u+5][v+5] = g;
                sum += g;
            }
        for (int a = 0; a < 11; a++)
            for (int b = 0; b < 11; b++)
                gw[a][b] /= sum;
        initialized = 1;
    }
    return gw;
}

double SSIM_window_based_parallel(unsigned char *img1, unsigned char *img2,
                                   int W, int H, int rank, int size)
{
    const double (*gaussian11x11)[11] = ssim_gaussian_window();

    double local_total = 0.0;
    long   local_count = 0;

    const int i_start = 5;
    const int i_end   = H - 5;
    const int rows    = (i_end > i_start) ? (i_end - i_start) : 0;
    const int base    = (size > 0) ? rows / size : 0;
    const int rem     = (size > 0) ? rows % size : 0;
    const int my_first = i_start + rank * base + (rank < rem ? rank : rem);
    const int my_rows  = base + (rank < rem ? 1 : 0);
    const int my_last  = my_first + my_rows;

    for (int i = my_first; i < my_last; i++) {
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
            local_total += num / den;
            local_count++;
        }
    }

    double global_total = 0.0;
    long   global_count = 0;
    MPI_Allreduce(&local_total, &global_total, 1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
    MPI_Allreduce(&local_count, &global_count, 1, MPI_LONG,   MPI_SUM, MPI_COMM_WORLD);

    return (global_count > 0) ? global_total / (double)global_count : 0.0;
}

/* ============================================================
   -------------- shared vector-distribution helper ---------------
   Computes vec_counts/vec_displs/byte_counts/byte_displs exactly
   as both pag.c's single-channel path and pco.c's "computed once
   for all channels" path did (identical logic in both).
   ============================================================ */
static void compute_vector_distribution(int num_vectors, int vlen, int rank, int size,
                                         int *vec_counts, int *vec_displs,
                                         int *byte_counts, int *byte_displs)
{
    const char *strategy_env = getenv("VQ_STRATEGY");
    int use_equal_split;
    if (strategy_env && strcmp(strategy_env, "equal") == 0)
        use_equal_split = 1;
    else if (strategy_env && strcmp(strategy_env, "adaptive") == 0)
        use_equal_split = 0;
    else
        use_equal_split = (size <= 4);

    if (use_equal_split) {
        int acc = 0;
        int vec_base = num_vectors / size;
        int vec_rem  = num_vectors % size;
        for (int r = 0; r < size; r++) {
            vec_counts[r]  = vec_base + (r < vec_rem ? 1 : 0);
            vec_displs[r]  = acc;
            byte_counts[r] = vec_counts[r] * vlen;
            byte_displs[r] = acc * vlen;
            acc += vec_counts[r];
        }
        if (rank == 0)
            printf("[Equal split] np=%d strategy=%s: calibration skipped, equal decomposition.\n",
                   size, strategy_env ? strategy_env : "auto");
    } else {
        MPI_Barrier(MPI_COMM_WORLD);
        double my_speed = calibrate_speed();

        double *speeds = (double *)malloc(size * sizeof(double));
        MPI_Allgather(&my_speed, 1, MPI_DOUBLE, speeds, 1, MPI_DOUBLE, MPI_COMM_WORLD);

        double sum_speed = 0.0;
        for (int r = 0; r < size; r++) sum_speed += speeds[r];
        if (sum_speed <= 0.0) { for (int r = 0; r < size; r++) speeds[r] = 1.0; sum_speed = size; }

        double *frac = (double *)malloc(size * sizeof(double));
        int assigned = 0;
        for (int r = 0; r < size; r++) {
            double ideal = (double)num_vectors * speeds[r] / sum_speed;
            vec_counts[r] = (int)ideal;
            frac[r]       = ideal - (double)vec_counts[r];
            assigned     += vec_counts[r];
        }
        int rem = num_vectors - assigned;
        for (int kk = 0; kk < rem; kk++) {
            int best = -1; double bestf = -1.0;
            for (int r = 0; r < size; r++)
                if (frac[r] > bestf) { bestf = frac[r]; best = r; }
            vec_counts[best] += 1;
            frac[best] = -1.0;
        }

        int acc = 0;
        for (int r = 0; r < size; r++) {
            vec_displs[r]  = acc;
            byte_counts[r] = vec_counts[r] * vlen;
            byte_displs[r] = acc * vlen;
            acc += vec_counts[r];
        }

        if (rank == 0) {
            printf("[Weighted split] speed-based vector distribution:\n");
            for (int r = 0; r < size; r++)
                printf("  rank %2d : speed=%.2f Mcmp/s  ->  %d vectors (%.1f%%)\n",
                       r, speeds[r] / 1e6, vec_counts[r],
                       100.0 * vec_counts[r] / num_vectors);
        }
        free(speeds); free(frac);
    }
}

/* ============================================================
   ------------------- MODE AUTO-DETECTION -----------------------
   (rank 0 only; result is MPI_Bcast to the rest — see judgment
   call #1)
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
   Mirrors pag.c's main() body exactly, wrapped as a function.
   ============================================================ */
static int run_gray_parallel(int argc, char *argv[], int rank, int size, const char *image_path)
{
    (void)argc; (void)argv;

    const int K    = CODEBOOK_SIZE;
    const int vlen = BLOCK_SIZE * BLOCK_SIZE;

    int original_image_bytes = WIDTH * HEIGHT;

    uint8_t *image       = NULL;
    uint8_t *training_set = NULL;
    int      num_vectors  = 0;

    MPI_Barrier(MPI_COMM_WORLD);
    double t_total0 = MPI_Wtime();

    if (rank == 0) {
        image = (uint8_t *)malloc(WIDTH * HEIGHT);
        if (!image) { fprintf(stderr, "malloc image failed\n"); MPI_Abort(MPI_COMM_WORLD,1); }

        if (!read_image_from_txt(image_path, image, WIDTH, HEIGHT)) {
            fprintf(stderr, "Failed to read image from text file.\n");
            free(image);
            MPI_Abort(MPI_COMM_WORLD, 1);
        }

        num_vectors = build_training_vectors(image, &training_set);
        printf("Built %d training vectors (each %d elements)\n", num_vectors, vlen);
    }

    MPI_Bcast(&num_vectors, 1, MPI_INT, 0, MPI_COMM_WORLD);

    int *vec_counts  = (int *)calloc(size, sizeof(int));
    int *vec_displs  = (int *)malloc(size * sizeof(int));
    int *byte_counts = (int *)malloc(size * sizeof(int));
    int *byte_displs = (int *)malloc(size * sizeof(int));

    compute_vector_distribution(num_vectors, vlen, rank, size,
                                 vec_counts, vec_displs, byte_counts, byte_displs);

    int local_n = vec_counts[rank];

    uint8_t *local_v = (uint8_t *)malloc((size_t)local_n * vlen);
    MPI_Scatterv(training_set, byte_counts, byte_displs, MPI_UINT8_T,
                 local_v,      local_n * vlen,           MPI_UINT8_T,
                 0, MPI_COMM_WORLD);

    float *codebook_flat = (float *)calloc(K * vlen, sizeof(float));
    {
        double *local_mean = (double *)calloc(vlen, sizeof(double));
        for (int i = 0; i < local_n; i++)
            for (int j = 0; j < vlen; j++)
                local_mean[j] += (double)local_v[i * vlen + j];
        MPI_Allreduce(MPI_IN_PLACE, local_mean, vlen,
                      MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
        for (int j = 0; j < vlen; j++)
            codebook_flat[j] = (float)(local_mean[j] / (double)num_vectors);
        free(local_mean);
    }

    float *local_vf = (float *)malloc((size_t)local_n * vlen * sizeof(float));
    for (int i = 0; i < local_n * vlen; i++)
        local_vf[i] = (float)local_v[i];

    uint8_t *labels       = NULL;
    if (rank == 0) labels = (uint8_t *)calloc(num_vectors, sizeof(uint8_t));
    uint8_t *local_labels = (uint8_t *)calloc(local_n, sizeof(uint8_t));

    MPI_Barrier(MPI_COMM_WORLD);
    double t0 = MPI_Wtime();
    int lbg_iters = parallel_lbg(local_vf, local_n, num_vectors, vlen, K,
                 codebook_flat, local_labels, rank, size, 0);
    MPI_Barrier(MPI_COMM_WORLD);
    double t1 = MPI_Wtime();
    double time_lbg = t1 - t0;

    MPI_Gatherv(local_labels, local_n,                MPI_UINT8_T,
                labels,       vec_counts, vec_displs, MPI_UINT8_T,
                0, MPI_COMM_WORLD);

    uint8_t *ssim_a = (uint8_t *)malloc((size_t)WIDTH * HEIGHT);
    uint8_t *ssim_b = (uint8_t *)malloc((size_t)WIDTH * HEIGHT);

    /* [BFPAR] hoisted so the rank-0 section can be split around the collective filter */
    uint8_t *codebook_data = NULL, *reconstructed_lbg = NULL, *labels_delta_u = NULL;
    uint8_t *reconstructed = NULL, *reconstructed_filtered = NULL;
    int codebook_bytes = 0;

    if (rank == 0) {
        printf("\nFinal codebook (%d codewords):\n", K);
        for (int c = 0; c < 10; c++) {
            printf("Codeword %d: ", c);
            for (int j = 0; j < vlen; j++)
                printf("%.1f ", codebook_flat[c * vlen + j]);
            printf("\n");
        }

        printf("==================================\n");
        printf("Time (LBG only): %.4f seconds\n", time_lbg);
        printf("LBG total iterations: %d\n", lbg_iters);

        double H = compute_entropy(labels, num_vectors, K);
        printf("Entropy before Huffman = %.3f bits/symbol\n", H);

        codebook_data = malloc(K * vlen);
        for (int k = 0; k < K; k++)
            for (int i = 0; i < vlen; i++)
                codebook_data[k * vlen + i] = (uint8_t) roundf(codebook_flat[k * vlen + i]);
        printf("Codebook converted to uint8_t (size = %d bytes)\n", K * vlen);

        reconstructed_lbg = malloc(WIDTH * HEIGHT);
        decompress_image(reconstructed_lbg, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, labels);

        FILE *flbg = fopen("lbg_decompress.txt", "w");
        for (size_t i = 0; i < (size_t)(WIDTH*HEIGHT); i++)
            fprintf(flbg, "%u\n", reconstructed_lbg[i]);
        fclose(flbg);

        double td0 = MPI_Wtime();
        labels_delta_u = malloc(num_vectors);
        labels_delta_u[0] = labels[0];
        for (int i = 1; i < num_vectors; i++)
            labels_delta_u[i] = (uint8_t)(labels[i] - labels[i-1] + 128);

        double H_delta = compute_entropy(labels_delta_u, num_vectors, 256);
        double td1 = MPI_Wtime();
        printf("[Delta Encode] Done in %.6f seconds\n", td1 - td0);
        printf("Entropy after Delta   = %.3f bits/symbol\n", H_delta);

        int huff_data_bytes = 0;
        int header_bytes    = 0;
        double t_huff0 = MPI_Wtime();
        int huff_total = huffman_on_labels(labels_delta_u, num_vectors, 255,
                                            &huff_data_bytes, &header_bytes);
        double t_huff1 = MPI_Wtime();
        double time_huff = t_huff1 - t_huff0;
        printf("Time (Huffman only): %.4f seconds\n\n", time_huff);

        printf("Huffman data bytes  = %d\n", huff_data_bytes);
        printf("Huffman total bytes = %d\n", huff_total);
        printf("Header bytes        = %d\n", header_bytes);

        int original_labels = num_vectors;
        codebook_bytes  = K * vlen;
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
        printf("\nBPP  = %.4f bits/pixel\n", 8.0 / CR_system);

        labels[0] = labels_delta_u[0];
        for (int i = 1; i < num_vectors; i++)
            labels[i] = labels[i-1] + ((int)labels_delta_u[i] - 128);

        reconstructed = malloc(WIDTH * HEIGHT);
        decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, labels);

    }

    /* [BFPAR] post-compression bilateral filter, distributed over all ranks */
    double bf_t0 = MPI_Wtime();
    if (rank != 0) reconstructed = (uint8_t *)malloc((size_t)WIDTH * HEIGHT);
    if (rank == 0) {
        reconstructed_filtered = malloc(WIDTH * HEIGHT);
        if (!reconstructed_filtered) { fprintf(stderr, "malloc reconstructed_filtered failed\n"); MPI_Abort(MPI_COMM_WORLD,1); }
    }
    parallel_bilateral(reconstructed, reconstructed_filtered, rank, size, vec_counts, num_vectors);
    double bf_t1 = MPI_Wtime();
    if (rank != 0) free(reconstructed);

    if (rank == 0) {
        printf("[Bilateral-Post] d=%d sigmaColor=%.1f sigmaSpace=%.1f alpha=%.2f  done in %.6f s (parallel, np=%d)\n",
               BF_D, BF_SIGMA_COLOR, BF_SIGMA_SPACE, BF_ALPHA, bf_t1 - bf_t0, size);

        FILE *file1 = fopen("decompress.txt", "w");
        for (size_t i = 0; i < (size_t)(WIDTH*HEIGHT); i++)
            fprintf(file1, "%u\n", reconstructed_filtered[i]);
        fclose(file1);

        save_bmp_gray("original.bmp",   image,                  WIDTH, HEIGHT);
        save_bmp_gray("compressed.bmp", reconstructed_filtered, WIDTH, HEIGHT);
        printf("Saved: original.bmp  compressed.bmp\n");

        double mse  = compute_mse(image, reconstructed_filtered, WIDTH*HEIGHT);
        double psnr = compute_psnr(image, reconstructed_filtered, WIDTH*HEIGHT);
        printf("MSE = %.2f\n", mse);
        printf("PSNR = %.2f dB\n", psnr);

        int indexes_bytes = num_vectors;
        int original_bytes = WIDTH * HEIGHT;
        double CR = (double)original_bytes / (codebook_bytes + indexes_bytes);
        printf("Compression Ratio (CR): %.2f\n", CR);

        memcpy(ssim_a, image,                  (size_t)WIDTH * HEIGHT);
        memcpy(ssim_b, reconstructed_filtered, (size_t)WIDTH * HEIGHT);

        free(codebook_data);
        free(reconstructed_lbg);
        free(labels_delta_u);
        free(reconstructed);
        free(reconstructed_filtered);
        free(image);
        free(training_set);
        free(labels);
    }

    MPI_Bcast(ssim_a, WIDTH * HEIGHT, MPI_UINT8_T, 0, MPI_COMM_WORLD);
    MPI_Bcast(ssim_b, WIDTH * HEIGHT, MPI_UINT8_T, 0, MPI_COMM_WORLD);

    MPI_Barrier(MPI_COMM_WORLD);
    double sp0 = MPI_Wtime();
    double ssim_par_val = SSIM_window_based_parallel(ssim_a, ssim_b, WIDTH, HEIGHT, rank, size);
    MPI_Barrier(MPI_COMM_WORLD);
    double sp1 = MPI_Wtime();

    if (rank == 0) {
        double ssim_par_time = sp1 - sp0;
        printf("SSIM (parallel)   = %.4f  |  time = %.6f s  (np=%d)\n",
               ssim_par_val, ssim_par_time, size);
    }

    free(ssim_a);
    free(ssim_b);

    free(local_v);
    free(local_vf);
    free(codebook_flat);
    free(local_labels);
    free(vec_counts); free(vec_displs);
    free(byte_counts); free(byte_displs);

    MPI_Barrier(MPI_COMM_WORLD);
    if (rank == 0) {
        double time_taken = MPI_Wtime() - t_total0;
        printf("Total execution time: %.3f seconds\n", time_taken);
    }

    return 0;
}

/* ============================================================
   ------------------------ COLOR PATH -----------------------------
   Mirrors pco.c's main() body exactly, wrapped as a function.
   ============================================================ */
typedef struct {
    double mse, psnr, ssim;
    double lbg_time;
    int compressed_bytes;
    uint8_t *reconstructed_filtered;
} ChannelResult;

static int run_color_parallel(int argc, char *argv[], int rank, int size, const char *image_path)
{
    (void)argc; (void)argv;

    const int K    = CODEBOOK_SIZE;
    const int vlen = BLOCK_SIZE * BLOCK_SIZE;
    const int num_vectors = (WIDTH / BLOCK_SIZE) * (HEIGHT / BLOCK_SIZE);
    const int channel_bytes = WIDTH * HEIGHT;

    MPI_Barrier(MPI_COMM_WORLD);
    double t_total0 = MPI_Wtime();

    uint8_t *R = NULL, *G = NULL, *B = NULL;
    uint8_t *channels[3] = {NULL, NULL, NULL};
    const char *channel_names[3] = {"Red", "Green", "Blue"};

    if (rank == 0) {
        R = (uint8_t*)malloc(channel_bytes);
        G = (uint8_t*)malloc(channel_bytes);
        B = (uint8_t*)malloc(channel_bytes);
        if (!R || !G || !B) { fprintf(stderr, "malloc RGB failed\n"); MPI_Abort(MPI_COMM_WORLD, 1); }

        if (!read_color_image_from_txt(image_path, R, G, B, WIDTH, HEIGHT)) {
            fprintf(stderr, "Failed to read color image from text file.\n");
            MPI_Abort(MPI_COMM_WORLD, 1);
        }
        printf("===== Processing color image: %s (%dx%d) — parallel, np=%d =====\n",
               image_path, WIDTH, HEIGHT, size);

        channels[0] = R; channels[1] = G; channels[2] = B;
    }

    int *vec_counts  = (int *)calloc(size, sizeof(int));
    int *vec_displs  = (int *)malloc(size * sizeof(int));
    int *byte_counts = (int *)malloc(size * sizeof(int));
    int *byte_displs = (int *)malloc(size * sizeof(int));

    /* computed ONCE for all 3 channels — see header comment / pco.c */
    compute_vector_distribution(num_vectors, vlen, rank, size,
                                 vec_counts, vec_displs, byte_counts, byte_displs);

    int local_n = vec_counts[rank];

    uint8_t *ssim_a = (uint8_t *)malloc((size_t)channel_bytes);
    uint8_t *ssim_b = (uint8_t *)malloc((size_t)channel_bytes);

    ChannelResult results[3];
    memset(results, 0, sizeof(results));

    for (int ch = 0; ch < 3; ch++) {

        uint8_t *training_set = NULL;
        if (rank == 0) {
            int nv = build_training_vectors(channels[ch], &training_set);
            if (nv != num_vectors) {
                fprintf(stderr, "Unexpected vector count for %s channel.\n", channel_names[ch]);
                MPI_Abort(MPI_COMM_WORLD, 1);
            }
        }

        uint8_t *local_v = (uint8_t *)malloc((size_t)local_n * vlen);
        MPI_Scatterv(training_set, byte_counts, byte_displs, MPI_UINT8_T,
                     local_v,      local_n * vlen,           MPI_UINT8_T,
                     0, MPI_COMM_WORLD);

        float *codebook_flat = (float *)calloc((size_t)K * vlen, sizeof(float));
        {
            double *local_mean = (double *)calloc(vlen, sizeof(double));
            for (int i = 0; i < local_n; i++)
                for (int j = 0; j < vlen; j++)
                    local_mean[j] += (double)local_v[i * vlen + j];
            MPI_Allreduce(MPI_IN_PLACE, local_mean, vlen,
                          MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
            for (int j = 0; j < vlen; j++)
                codebook_flat[j] = (float)(local_mean[j] / (double)num_vectors);
            free(local_mean);
        }

        float *local_vf = (float *)malloc((size_t)local_n * vlen * sizeof(float));
        for (int i = 0; i < local_n * vlen; i++)
            local_vf[i] = (float)local_v[i];

        uint8_t *labels = NULL;
        if (rank == 0) labels = (uint8_t *)calloc(num_vectors, sizeof(uint8_t));
        uint8_t *local_labels = (uint8_t *)calloc(local_n, sizeof(uint8_t));

        MPI_Barrier(MPI_COMM_WORLD);
        double t0 = MPI_Wtime();
        int lbg_iters = parallel_lbg(local_vf, local_n, num_vectors, vlen, K,
                    codebook_flat, local_labels, rank, size, 0);
        MPI_Barrier(MPI_COMM_WORLD);
        double t1 = MPI_Wtime();
        double lbg_time = t1 - t0;

        MPI_Gatherv(local_labels, local_n,                MPI_UINT8_T,
                    labels,       vec_counts, vec_displs, MPI_UINT8_T,
                    0, MPI_COMM_WORLD);

        /* [BFPAR] hoisted so the rank-0 section can be split around the collective filter */
        uint8_t *labels_delta_u = NULL, *reconstructed = NULL, *reconstructed_filtered = NULL;

        if (rank == 0) {
            printf("\n  [%s channel] LBG time=%.4fs  LBG iters=%d\n", channel_names[ch], lbg_time, lbg_iters);

            labels_delta_u = (uint8_t*)malloc(num_vectors);
            labels_delta_u[0] = labels[0];
            for (int i = 1; i < num_vectors; i++)
                labels_delta_u[i] = (uint8_t)(labels[i] - labels[i-1] + 128);

            int huff_data_bytes = 0, header_bytes = 0;
            int huff_total = huffman_on_labels(labels_delta_u, num_vectors, 255,
                                               &huff_data_bytes, &header_bytes);
            (void)huff_data_bytes; (void)header_bytes;

            int codebook_bytes = K * vlen;
            results[ch].compressed_bytes = codebook_bytes + huff_total;
            results[ch].lbg_time = lbg_time;

            labels[0] = labels_delta_u[0];
            for (int i = 1; i < num_vectors; i++)
                labels[i] = labels[i-1] + ((int)labels_delta_u[i] - 128);

            reconstructed = (uint8_t*)malloc(channel_bytes);
            decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, labels);

        }

        /* [BFPAR] post-compression bilateral filter, distributed over all ranks */
        if (rank != 0) reconstructed = (uint8_t *)malloc((size_t)channel_bytes);
        if (rank == 0) reconstructed_filtered = (uint8_t*)malloc(channel_bytes);
        parallel_bilateral(reconstructed, reconstructed_filtered, rank, size, vec_counts, num_vectors);
        if (rank != 0) free(reconstructed);

        if (rank == 0) {

            results[ch].mse  = compute_mse(channels[ch], reconstructed_filtered, channel_bytes);
            results[ch].psnr = compute_psnr(channels[ch], reconstructed_filtered, channel_bytes);
            results[ch].reconstructed_filtered = reconstructed_filtered;

            printf("  [%s channel] PSNR=%.2f dB  CR(system)=%.2fX\n",
                   channel_names[ch], results[ch].psnr,
                   (double)channel_bytes / (double)results[ch].compressed_bytes);

            memcpy(ssim_a, channels[ch],        channel_bytes);
            memcpy(ssim_b, reconstructed_filtered, channel_bytes);

            free(reconstructed);
            free(labels_delta_u);
            free(labels);
            free(training_set);
        }

        MPI_Bcast(ssim_a, channel_bytes, MPI_UINT8_T, 0, MPI_COMM_WORLD);
        MPI_Bcast(ssim_b, channel_bytes, MPI_UINT8_T, 0, MPI_COMM_WORLD);

        MPI_Barrier(MPI_COMM_WORLD);
        double sp0 = MPI_Wtime();
        double ssim_val = SSIM_window_based_parallel(ssim_a, ssim_b, WIDTH, HEIGHT, rank, size);
        MPI_Barrier(MPI_COMM_WORLD);
        double sp1 = MPI_Wtime();

        if (rank == 0) {
            results[ch].ssim = ssim_val;
            printf("  [%s channel] SSIM=%.4f  (SSIM time=%.4fs)\n",
                   channel_names[ch], ssim_val, sp1 - sp0);
        }

        free(local_v);
        free(local_vf);
        free(codebook_flat);
        free(local_labels);
    }

    if (rank == 0) {
        int total_samples = 3 * channel_bytes;
        double rgb_mse = (results[0].mse * channel_bytes +
                          results[1].mse * channel_bytes +
                          results[2].mse * channel_bytes) / total_samples;
        double rgb_psnr = (rgb_mse == 0.0) ? 100.0 : 10.0 * log10((255.0*255.0) / rgb_mse);

        int total_original_bytes   = total_samples;
        int total_compressed_bytes = results[0].compressed_bytes +
                                     results[1].compressed_bytes +
                                     results[2].compressed_bytes;
        double rgb_cr = (double)total_original_bytes / (double)total_compressed_bytes;

        double mean_channelwise_ssim = (results[0].ssim + results[1].ssim + results[2].ssim) / 3.0;
        double total_lbg_time = results[0].lbg_time + results[1].lbg_time + results[2].lbg_time;

        save_bmp_color("original_color.bmp", R, G, B, WIDTH, HEIGHT);
        save_bmp_color("compressed_color.bmp",
                       results[0].reconstructed_filtered,
                       results[1].reconstructed_filtered,
                       results[2].reconstructed_filtered,
                       WIDTH, HEIGHT);

        printf("\n===== COLOR IMAGE — AGGREGATE RESULTS (parallel, np=%d) =====\n", size);
        printf("RGB PSNR                  : %.2f dB\n", rgb_psnr);
        printf("Mean Channel-wise SSIM    : %.4f\n", mean_channelwise_ssim);
        printf("RGB MSE                   : %.2f\n", rgb_mse);
        printf("RGB CR (system)           : %.2f X\n", rgb_cr);
        printf("Total LBG time (R+G+B)    : %.4f s\n", total_lbg_time);
        printf("Saved: original_color.bmp  compressed_color.bmp\n");
        printf("====================================================================\n");

        free(R); free(G); free(B);
        free(results[0].reconstructed_filtered);
        free(results[1].reconstructed_filtered);
        free(results[2].reconstructed_filtered);
    }

    free(ssim_a); free(ssim_b);
    free(vec_counts); free(vec_displs);
    free(byte_counts); free(byte_displs);

    MPI_Barrier(MPI_COMM_WORLD);
    if (rank == 0) {
        double time_taken = MPI_Wtime() - t_total0;
        printf("Total execution time: %.3f seconds\n", time_taken);
    }

    return 0;
}

/* ============================================================
   MAIN — picks mode via --gray/--color or auto-detection
   (rank 0 resolves it, then Bcasts to everyone — judgment call #1)
   ============================================================ */
int main(int argc, char *argv[])
{
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    const char *image_path = (argc > 1) ? argv[1] : "img.txt";
    int mode_int = MODE_UNKNOWN;

    if (rank == 0) {
        ImgMode mode = MODE_UNKNOWN;
        if (argc > 2) {
            if      (strcmp(argv[2], "--gray")  == 0) mode = MODE_GRAY;
            else if (strcmp(argv[2], "--color") == 0) mode = MODE_COLOR;
            else {
                fprintf(stderr, "Unknown flag '%s' (expected --gray or --color)\n", argv[2]);
                mode = MODE_UNKNOWN;
            }
        } else {
            mode = detect_mode_from_file(image_path);
            if (mode != MODE_UNKNOWN)
                printf("[Mode] auto-detected: %s\n", mode == MODE_GRAY ? "grayscale" : "color");
        }
        mode_int = (int)mode;
        if (mode_int == MODE_UNKNOWN) {
            fprintf(stderr,
                "Could not determine image mode for '%s'. Pass --gray or --color explicitly:\n"
                "  mpirun -np N %s %s --gray\n  mpirun -np N %s %s --color\n",
                image_path, argv[0], image_path, argv[0], image_path);
        }
    }

    MPI_Bcast(&mode_int, 1, MPI_INT, 0, MPI_COMM_WORLD);

    if (mode_int == MODE_UNKNOWN) {
        MPI_Finalize();
        return 1;
    }

    int rc;
    if (mode_int == MODE_GRAY)
        rc = run_gray_parallel(argc, argv, rank, size, image_path);
    else
        rc = run_color_parallel(argc, argv, rank, size, image_path);

    MPI_Finalize();
    return rc;
}
