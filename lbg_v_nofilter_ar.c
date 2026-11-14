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
 *  coding and decompression; SSIM is computed IN PARALLEL across all ranks after
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
 *   5) build_training_vectors / read_image_from_txt
 *      / compute_mse / compute_psnr / compute_entropy / SSIM
 *      (gaussian window + parallel reduction): byte-for-byte
 *      identical between pag.c and pco.c already, kept once each.
 * ============================================================
 */

/* ═══════════════════════════════════════════════════════════════
   شرح بالعربي: هذا الملف هو نفسه lbg_v_nofilter.c تماماً، مع تعليقات عربية
   إضافية فقط. لم يتغير أي سطر برمجي. كل تعليق عربي يبدأ بكلمة (شرح).
   
   فكرة البرنامج: ضغط صورة 512×512 بالتكميم المتجهي LBG بصيغة متوازية (MPI):
     1) rank 0 يقرأ الصورة ويقسمها إلى كتل 4×4 فيصير 16384 متجه (16 قيمة لكل متجه).
     2) المتجهات توزع على العمليات (بالتساوي، أو حسب سرعة كل نواة).
     3) كل العمليات تبني codebook من 64 كلمة بخوارزمية LBG، وتتبادل المجاميع
        بـ MPI_Allreduce في كل تكرار.
     4) رقم أقرب كلمة لكل كتلة (label) يتجمع عند rank 0.
     5) على rank 0: Delta coding ثم Huffman (ترميز + فك + تحقق).
     6) تُعاد بناء الصورة من خرج مفكّك Huffman، ثم MSE و PSNR.
     7) الصورتان (الأصلية والمسترجعة) تُبثّان لكل العمليات و SSIM يُحسب بالتوازي.
     الرمادي: run_gray_parallel ، الملوّن: run_color_parallel (R ثم G ثم B).
   
   الترجمة والتشغيل:
     mpicc -O2 -Wall -o lbg_v lbg_v_nofilter_ar.c -lm
     mpirun -np 4 ./lbg_v image.txt --gray        (أو --color)
     متغير البيئة VQ_STRATEGY=equal أو adaptive يفرض طريقة توزيع المتجهات.
   ═══════════════════════════════════════════════════════════════
*/
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <time.h>
#include <string.h>
#include <mpi.h>

/* شرح: ثوابت البرنامج
     WIDTH, HEIGHT  : أبعاد الصورة (ثابتة 512×512، غيرها لا يعمل)
     BLOCK_SIZE     : ضلع الكتلة (4×4 بكسل)
     DELTA          : نسبة التشويش عند انشطار كل كلمة (±1%)
     EPSILON        : عتبة التوقف: أقل تحسن نسبي بالتشويه يستحق تكراراً آخر
     CODEBOOK_SIZE  : عدد كلمات الـ codebook (K = 64)
     MAX_ITER       : أقصى عدد تكرارات لكل مرحلة انشطار
     K1, K2         : ثوابت SSIM القياسية (0.01 و 0.03)
     VLEN           : طول المتجه = 4×4 = 16 قيمة
     عدد المتجهات = (512/4)² = 16384
*/
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

/* ============================================================
   ---------------------- SHARED HELPERS -----------------------
   (identical between pag.c and pco.c; kept once)
   ============================================================ */

/* شرح: حفظ صورة رمادية بصيغة BMP ذات 8 بت مع لوحة ألوان رمادية (256 درجة).
   الصفوف تُكتب من الأسفل للأعلى (طريقة BMP)، ويُضاف حشو حتى يصير عرض الصف من مضاعفات 4 بايت.
*/
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

/* شرح: حفظ صورة ملوّنة BMP ذات 24 بت. ترتيب البايتات داخل البكسل B ثم G ثم R،
   والصفوف من الأسفل للأعلى مع حشو لمضاعفات 4 بايت.
*/
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

/* شرح: بناء متجهات التدريب من الصورة. نمر على الصورة كتلة كتلة (من اليسار لليمين
   ثم من الأعلى للأسفل)، وكل كتلة 4×4 تتحول إلى متجه من 16 قيمة (صفاً صفاً).
   الناتج مصفوفة 16384×16 بايت، والدالة ترجع عدد المتجهات.
*/
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

/* شرح: القراءة السريعة للصور. بدل fscanf (بطيء لأنه يُستدعى 262144 مرة)، نقرأ الملف
   كله مرة وحدة بـ slurp_file ثم نحلل الأرقام بدالة next_int. النتيجة نفسها تماماً.
*/
/* [FASTIO] Whole-file read + hand-written integer parser. */
static char *slurp_file(const char *filename, size_t *len)
{
    FILE *f = fopen(filename, "rb");
    if (!f) { perror("Error opening image file"); return NULL; }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    char *buf = (char *)malloc((size_t)sz + 1);
    if (!buf) { fclose(f); return NULL; }
    size_t got = fread(buf, 1, (size_t)sz, f);
    fclose(f);
    buf[got] = '\0';
    *len = got;
    return buf;
}

/* شرح: تقرأ العدد الصحيح التالي من الذاكرة (تتجاوز المسافات وسطور جديدة، وتقبل + و -).
   ترجع 0 عند نهاية البيانات أو عند أول رمز غير رقمي (مثل سلوك fscanf).
*/
static int next_int(const char **pp, const char *end, int *out)
{
    const char *p = *pp;
    while (p < end && (*p == ' ' || *p == '\n' || *p == '\r' || *p == '\t')) p++;
    if (p >= end) { *pp = p; return 0; }
    int neg = 0;
    if (*p == '-') { neg = 1; p++; } else if (*p == '+') p++;
    if (p >= end || *p < '0' || *p > '9') { *pp = p; return 0; }
    long v = 0;
    while (p < end && *p >= '0' && *p <= '9') { if (v < 100000000L) v = v * 10 + (*p - '0'); p++; }
    *out = (int)(neg ? -v : v);
    *pp = p;
    return 1;
}

/* شرح: قراءة صورة رمادية من ملف نصي (قيمة لكل بكسل). كل قيمة تُقصّ للمدى 0..255.
   ترجع 1 فقط إذا قُرئ العدد المطلوب بالضبط (512×512 = 262144 قيمة).
*/
int read_image_from_txt(const char *filename, uint8_t *image, int width, int height) {
    size_t len; char *buf = slurp_file(filename, &len);
    if (!buf) return 0;
    const char *p = buf, *end = buf + len;
    int val, count = 0;
    while (count < width * height && next_int(&p, end, &val)) {
        if (val < 0) val = 0;
        if (val > 255) val = 255;
        image[count++] = (uint8_t)val;
    }
    free(buf);
    if (count != width * height) {
        fprintf(stderr, "Warning: Expected %d pixels, got %d\n", width * height, count);
    }
    return count == width * height;
}

/* شرح: قراءة صورة ملوّنة (ثلاث قيم R G B لكل بكسل) وتوزيعها على ثلاث مصفوفات R و G و B.
*/
int read_color_image_from_txt(const char *filename,
                               uint8_t *R, uint8_t *G, uint8_t *B,
                               int width, int height)
{
    size_t len; char *buf = slurp_file(filename, &len);
    if (!buf) return 0;
    const char *p = buf, *end = buf + len;
    int r, g, b, count = 0;
    while (count < width * height &&
           next_int(&p, end, &r) && next_int(&p, end, &g) && next_int(&p, end, &b)) {
        if (r < 0) r = 0;
        if (r > 255) r = 255;
        if (g < 0) g = 0;
        if (g > 255) g = 255;
        if (b < 0) b = 0;
        if (b > 255) b = 255;
        R[count] = (uint8_t)r; G[count] = (uint8_t)g; B[count] = (uint8_t)b;
        count++;
    }
    free(buf);
    if (count != width * height) {
        fprintf(stderr, "Warning: Expected %d pixels, got %d\n", width * height, count);
    }
    return count == width * height;
}

/* شرح: كتابة قيمة لكل سطر في ملف نصي بعملية كتابة واحدة بدل 262144 fprintf.
   الملف الناتج مطابق بالبايت للطريقة القديمة (جرّبنا ذلك بـ cmp).
*/
/* [FASTIO] one buffered write instead of 262144 fprintf calls; output bytes identical */
static void write_u8_lines(const char *filename, const uint8_t *d, size_t n)
{
    FILE *f = fopen(filename, "w");
    if (!f) { perror(filename); return; }
    char *buf = (char *)malloc(n * 4 + 1);
    size_t q = 0;
    if (buf) {
        for (size_t i = 0; i < n; i++) {
            unsigned v = d[i];
            if (v >= 100) { buf[q++] = (char)('0' + v / 100); buf[q++] = (char)('0' + (v / 10) % 10); buf[q++] = (char)('0' + v % 10); }
            else if (v >= 10) { buf[q++] = (char)('0' + v / 10); buf[q++] = (char)('0' + v % 10); }
            else buf[q++] = (char)('0' + v);
            buf[q++] = '\n';
        }
        fwrite(buf, 1, q, f);
        free(buf);
    }
    fclose(f);
}

/* شرح: مربع المسافة الإقليدية بين متجهين طول كل منهما 16 (بدون جذر تربيعي، لأن
   مقارنة المسافات لا تحتاج الجذر). هذه الدالة هي أكثر ما يُستدعى في البرنامج.
*/
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

/* شرح: قياس سرعة نواة الحساب (يُستخدم فقط عند التوزيع المتكيف np>4).
   كل عملية تنفذ معياراً صغيراً يحاكي حساب المسافات (512 متجه × 64 كلمة)، 3 محاولات:
   الأولى تُهمل (إحماء)، ويُؤخذ أسرع زمن من الباقي. الناتج: عدد المقارنات بالثانية.
*/
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

    /* [V4] The benchmark lasts well under 1 ms, so a single timed pass measures a transient state (clock
       ramp-up of an idle core, especially an E-core) and gave unstable weights between runs/builds
       (E-core speed measured anywhere between ~95 and ~172 Mcmp/s). Pass 0 is a discarded warm-up; of the
       remaining passes the FASTEST is kept (robust against interference). Cost: ~1 ms, only when np > 4. */
    enum { TRIALS = 3 };
    volatile float sink = 0.0f;
    double dt = 1e30;
    for (int trial = 0; trial < TRIALS; trial++) {
        /* شرح (الخطوة 6): تشغيل LBG المتوازي، وقياس زمنه بين Barrier قبله وبعده
           (Time (LBG only) = زمن أبطأ عملية، ولا يشمل التوزيع ولا التجميع).
        */
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
        double t = MPI_Wtime() - t0;
        if (trial > 0 && t < dt) dt = t;
    }
    free(v); free(cb);
    (void)sink;
    if (dt <= 0.0 || dt > 1e29) dt = 1e-6;
    return (double)REP * (double)NV * (double)NC / dt;
}

/* شرح: قلب البرنامج، خوارزمية LBG المتوازية.
     local_vf : المتجهات التي تخص هذه العملية فقط (float)   local_n : عددها
     num_vectors : العدد الكلي للمتجهات   K : عدد الكلمات المطلوب   codebook : الـ codebook
     local_labels : (خرج) رقم أقرب كلمة لكل متجه محلي
   الخوارزمية: نبدأ بكلمة واحدة، ثم نكرر: انشطار (كل كلمة تتضاعف) ثم تكرارات Lloyd
   حتى تقارب التشويه، حتى نصل K كلمة. ترجع مجموع كل التكرارات (نفسه عند كل العمليات).
*/
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

    /* [V3] double accumulators + double Allreduce: sums of integer-valued vectors are exact, so the codebook
       and the iteration count no longer depend on np or on the order of the additions (see sem_v3.c). */
    /* شرح: مصفوفة التجميع buf (double). ترتيبها: [مجموع متجهات كل كلمة: K×16] ثم
       [عدد متجهات كل كلمة: K] ثم [مجموع التشويه: 1]. هذه تُجمع بـ MPI_Allreduce كل تكرار.
       استخدام double يجعل مجاميع الأعداد الصحيحة دقيقة، فلا تتأثر النتيجة بعدد العمليات.
    */
    int buf_capacity = K * VLEN + K + 1;
    double *buf = (double *)calloc(buf_capacity, sizeof(double));

    /* شرح: نبدأ بكلمة واحدة (codebook[0] = متوسط كل المتجهات، حُسب قبل استدعاء الدالة).
       k = عدد الكلمات الحالي ويتضاعف حتى K: 2 ثم 4 ثم 8 ثم 16 ثم 32 ثم 64 (6 مراحل).
    */
    int k = 1;
    int total_iters = 0;
    while (k < K) {
        /* شرح (الانشطار): كل كلمة تنقسم إلى كلمتين: الأولى ×(1+DELTA) والثانية ×(1−DELTA).
           الحلقة تمشي من الأعلى للأسفل حتى لا تُكتب الكلمات الجديدة فوق كلمات لم تنقسم بعد.
        */
        for (int i = k - 1; i >= 0; i--)
            for (int j = 0; j < VLEN; j++) {
                float v = codebook[i * VLEN + j];
                codebook[(k + i) * VLEN + j] = v * (1.0f - DELTA);
                codebook[i        * VLEN + j] = v * (1.0f + DELTA);
            }
        k = (k * 2 > K) ? K : k * 2;

        /* شرح: مواقع أجزاء buf في هذه المرحلة (تعتمد على عدد الكلمات الحالي k).
           active = عدد العناصر المستخدمة فعلاً، وهو المُرسل إلى Allreduce.
        */
        const int sum_off  = 0;
        const int cnt_off  = k * VLEN;
        const int dist_off = cnt_off + k;
        const int active   = dist_off + 1;

        /* شرح: prev_dist = التشويه السابق (قيمة ضخمة بالبداية حتى لا تتوقف المرحلة بعد أول تكرار).
        */
        double prev_dist   = 1e30;
        double improvement = 1.0;
        int   iter        = 0;

        /* شرح: تكرارات Lloyd لهذه المرحلة. كل تكرار أربع خطوات: (أ) تعيين كل متجه لأقرب كلمة،
           (ب) جمع النتائج من كل العمليات، (ج) تحديث الكلمات، (د) اختبار التقارب.
        */
        do {
            /* شرح (أ) التعيين: نصفّر buf، ثم لكل متجه من حصة هذه العملية نحسب مسافته لكل الكلمات
               ونختار الأقرب (عند التساوي تفوز الكلمة ذات الرقم الأصغر).
            */
            memset(buf, 0, active * sizeof(double));

            for (int i = 0; i < local_n; i++) {
                const float *v = local_vf + i * VLEN;
                float best = 1e30f;
                int   bi   = 0;
                for (int c = 0; c < k; c++) {
                    float d = distance16f(codebook + c * VLEN, v);
                    if (d < best) { best = d; bi = c; }
                }
                /* شرح: نسجّل رقم أقرب كلمة للمتجه، ونضيف للتجميع المحلي: مسافته (للتشويه)،
                   و +1 لعدد متجهات تلك الكلمة، ومتجهه نفسه لمجموع متجهات تلك الكلمة.
                */
                local_labels[i]    = (uint8_t)bi;
                buf[dist_off]     += best;
                buf[cnt_off + bi] += 1.0;
                double *s = buf + sum_off + bi * VLEN;
                for (int j = 0; j < VLEN; j++)
                    s[j] += v[j];
            }

            /* شرح (ب) الجمع العالمي: بعد هذا السطر كل العمليات تملك المجاميع الكلية لكل المتجهات
               (مجاميع الكلمات وأعدادها والتشويه)، وهذا هو الاتصال الوحيد بكل تكرار.
            */
            MPI_Allreduce(MPI_IN_PLACE, buf, active,
                          MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);

            /* شرح: متوسط التشويه (مربع المسافة) على كل المتجهات.
            */
            double global_dist = buf[dist_off] / (double)num_vectors;

            for (int c = 0; c < k; c++) {
                /* شرح (ج) التحديث: الكلمة الجديدة = مجموع متجهاتها ÷ عددها (مركز المجموعة).
                   إذا لم يقع أي متجه عليها (cnt = 0) تبقى كلمتها كما هي بدون تغيير.
                */
                double cnt = buf[cnt_off + c];
                if (cnt > 0.0) {
                    double *s  = buf + sum_off + c * VLEN;
                    for (int j = 0; j < VLEN; j++)
                        codebook[c * VLEN + j] = (float)(s[j] / cnt);
                }
            }

            /* شرح (د) التقارب: التحسن النسبي = |التشويه السابق − الحالي| ÷ الحالي.
            */
            improvement = fabs(prev_dist - global_dist) / (global_dist + 1e-9);
            prev_dist   = global_dist;
            iter++;

            if (rank == 0 && verbose && iter == 1)
                printf("k=%3d iter=%3d distortion=%.4f  (first)\n", k, iter, prev_dist);

        /* شرح: نكرر ما دام التحسن النسبي أكبر من EPSILON وعدد التكرارات أقل من MAX_ITER.
        */
        } while (iter < MAX_ITER && improvement > (double)EPSILON);
        total_iters += iter;

        if (rank == 0 && verbose)
            printf("k=%3d iter=%3d distortion=%.4f  (converged)\n", k, iter, prev_dist);
    }
    free(buf);
    /* شرح: نرجع مجموع التكرارات عبر كل مراحل الانشطار (يُطبع لاحقاً: LBG total iterations).
    */
    return total_iters;
}

/* شرح: إعادة بناء الصورة من المؤشرات والـ codebook. لكل كتلة (بنفس ترتيب بنائها) نأخذ
   كلمتها من الـ codebook، ونقرّب كل قيمة لأقرب عدد صحيح بـ roundf، ونضعها مكان بكسلات الكتلة.
*/
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

/* شرح: MSE = متوسط مربع الفرق بين الصورة الأصلية والمسترجعة.
*/
double compute_mse(uint8_t *original, uint8_t *reconstructed, int size) {
    double mse = 0.0;
    for (int i = 0; i < size; i++) {
        double diff = (double)original[i] - (double)reconstructed[i];
        mse += diff*diff;
    }
    return mse/size;
}

/* شرح: PSNR = 10·log10(255² ÷ MSE) بالديسيبل. إذا MSE = 0 (تطابق تام) نرجع 100.
*/
double compute_psnr(uint8_t *original, uint8_t *reconstructed, int size) {
    double mse = compute_mse(original, reconstructed, size);
    if (mse == 0) return 100.0;
    return 10.0 * log10((255.0*255.0)/mse);
}

/* شرح: الإنتروبي H = −Σ p·log2(p) بوحدة bit لكل رمز: p هو تكرار الرمز ÷ العدد الكلي.
   يمثل أقل عدد bits لكل رمز يمكن الوصول له نظرياً بترميز بدون خسارة.
*/
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
/* شرح: ترميز Huffman (ترميز بدون خسارة): الرموز الأكثر تكراراً تأخذ شفرات أقصر.
     HuffNode : عقدة الشجرة (value = الرمز، -1 للعقدة الداخلية؛ freq = التكرار؛ left/right)
     MinHeap  : كومة صغرى مرتبة حسب التكرار (لسحب أصغر عقدتين دائماً)
     HuffCode : شفرة الرمز (البتات وعددها)
*/
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
/* شرح: بناء الشجرة: نضع كل رمز مستخدم كعقدة في الكومة، ثم نكرر: نسحب أصغر عقدتين
   وندمجهما بعقدة أب تكرارها مجموعهما، حتى تبقى عقدة وحدة (الجذر).
   حالة رمز وحيد تُعالج بجذر له ابن واحد حتى يصير طول شفرته 1 bit.
*/
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
/* شرح: توليد الشفرات بالمشي على الشجرة: الذهاب لليسار يضيف 0 ولليمين يضيف 1،
   وعند الوصول لورقة نخزن شفرة الرمز وطولها (حتى 64 bit).
*/
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
/* شرح: الترميز: لكل رمز نكتب شفرته bit بعد bit (من الأعلى) داخل مصفوفة بايتات،
   وإذا بقي آخر بايت ناقصاً يُكتب كما هو. ترجع المصفوفة وعدد بايتاتها.
*/
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
/* شرح: فك الترميز: نمشي على الشجرة bit بعد bit (0 يسار، 1 يمين)، وعند الوصول لورقة
   نخرج رمزها ونعود للجذر، حتى نستعيد العدد الأصلي من الرموز.
*/
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
/* شرح: الدالة الرئيسية لـ Huffman. تأخذ المؤشرات بعد Delta (labels) وترجع الحجم المضغوط
   الكلي، وحجم بيانات Huffman وحجم الـ header، والمؤشرات المفكوكة في out_decoded.
   الخطوات: (1) التكرارات (2) الشجرة (3) الشفرات (4) الترميز (5) حجم الـ header
   (6) الفك والتحقق. مهم: البرنامج لا يكتب ملفاً مضغوطاً على القرص؛ يرمّز بالذاكرة
   ويفك ويقارن ويحسب الأحجام.
*/
/* [HUFFFIX] out_decoded (num_labels bytes, caller-owned) receives the output of the
   Huffman DECODER; the caller must rebuild the image from it, not from the encoder input. */
int huffman_on_labels(uint8_t *labels, int num_labels, int max_symbol,
                       int *out_huff_data, int *out_header, uint8_t *out_decoded)
{
    /* شرح (1): نعدّ كم مرة ظهر كل رمز (0..255)، ثم نحسب عدد الرموز المستخدمة فعلاً.
    */
    uint32_t *freq = (uint32_t*)calloc(max_symbol + 1, sizeof(uint32_t));
    for (int i = 0; i < num_labels; ++i) {
        int v = labels[i];
        if (v >= 0 && v <= max_symbol) freq[v]++;
    }
    int used_symbols = 0;
    for (int i = 0; i <= max_symbol; i++) if (freq[i] > 0) used_symbols++;

    /* شرح (2): بناء شجرة Huffman من التكرارات.
    */
    HuffNode *root = huff_build_tree(freq, max_symbol);
    if (!root) { printf("Huffman: no symbols found!\n"); free(freq); return 0; }

    /* شرح (3): استخراج شفرة كل رمز من الشجرة.
    */
    HuffCode *table = (HuffCode*)malloc((max_symbol + 1) * sizeof(HuffCode));
    huff_build_codes(root, table, max_symbol);

    /* شرح (4): ترميز كل المؤشرات؛ enc_bytes = حجم بيانات Huffman بالبايت.
    */
    int enc_bytes = 0;
    uint8_t *enc = huff_encode(labels, num_labels, table, &enc_bytes);

    /* شرح (5): حجم الـ header = لكل رمز مستخدم 5 بايت (بايت واحد للرمز و4 بايت لتكراره).
       هذا كل ما يحتاجه المستقبل لإعادة بناء الشجرة. الحجم الكلي = header + بيانات Huffman.
    */
    /* [HUFFFIX] To decode, the receiver needs, per used symbol, the symbol id (1 byte) and its
       frequency (4 bytes) to rebuild the tree; the old count (4 bytes/symbol) omitted the id. */
    int header_bytes = used_symbols * (1 + (int)sizeof(uint32_t));
    int total_compressed = header_bytes + enc_bytes;

    /* [HUFFFIX] Decode with a tree rebuilt ONLY from the header data (freq[]), not the encoder's tree. */
    HuffNode *dec_root = huff_build_tree(freq, max_symbol);
    uint8_t *decoded = (uint8_t*)malloc(num_labels);
    huff_decode(enc, enc_bytes, dec_root, num_labels, decoded);
    huff_free_tree(dec_root);

    /* شرح (6): التحقق: نفك البيانات بشجرة بُنيت من التكرارات فقط (مثل المستقبل) ونقارنها
       بالأصل رمزاً رمزاً. أي اختلاف يوقف البرنامج. الناتج المفكوك يُستخدم لإعادة البناء.
    */
    int ok = 1;
    for (int i = 0; i < num_labels; ++i)
        if (labels[i] != decoded[i]) { ok = 0; break; }
    printf("Decode check: %s\n",
           ok ? "OK (labels identical, no distortion)" : "ERROR (mismatch!)");

    if (!ok) { fprintf(stderr, "Huffman decode mismatch -- aborting.\n"); MPI_Abort(MPI_COMM_WORLD, 1); }
    if (out_decoded)   memcpy(out_decoded, decoded, (size_t)num_labels);

    if (out_huff_data) *out_huff_data = enc_bytes;
    if (out_header)    *out_header    = header_bytes;

    free(freq); free(table); free(enc); free(decoded);
    huff_free_tree(root);
    return total_compressed;
}

/* ============================================================
   SSIM — parallel version, identical between pag.c and pco.c
   ============================================================ */
/* شرح: نافذة غاوسية 11×11 (σ = 1.5) تُبنى مرة وحدة ثم تُطبّع بحيث مجموع أوزانها = 1.
*/
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

/* شرح: SSIM بين صورتين (مؤشر التشابه البنيوي، من 0 إلى 1). نحسبه لكل نافذة 11×11 ثم نأخذ
   المتوسط. الصفوف تُوزع على العمليات، وكل عملية تحسب حصتها ثم تُجمع النتائج بـ Allreduce.
*/
double SSIM_window_based_parallel(unsigned char *img1, unsigned char *img2,
                                   int W, int H, int rank, int size)
{
    const double (*gaussian11x11)[11] = ssim_gaussian_window();

    double local_total = 0.0;
    long   local_count = 0;

    /* شرح: توزيع الصفوف: نتجاهل 5 بكسل من كل حافة (لتكتمل النافذة داخل الصورة)،
       والصفوف المتبقية توزع بالتساوي على العمليات (والباقي على أول العمليات).
    */
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
            /* شرح: المتوسطان المرجّحان بالنافذة الغاوسية لنافذة الصورة الأولى (x) والثانية (y).
            */
            double mu_x = 0, mu_y = 0;
            for (int u = -5; u <= 5; u++)
                for (int v = -5; v <= 5; v++) {
                    double w = gaussian11x11[u+5][v+5];
                    mu_x += w * img1[(i+u)*W + (j+v)];
                    mu_y += w * img2[(i+u)*W + (j+v)];
                }
            /* شرح: التباينان (لكل صورة) والتباين المشترك بينهما، مرجّحة بنفس النافذة.
            */
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
            /* شرح: صيغة SSIM = [(2·μx·μy + C1)·(2·σxy + C2)] ÷ [(μx² + μy² + C1)·(σx + σy + C2)]
               حيث C1 و C2 ثوابت صغيرة لتجنب القسمة على صفر.
            */
            double C1 = (K1 * 255) * (K1 * 255);
            double C2 = (K2 * 255) * (K2 * 255);
            double num = (2 * mu_x * mu_y + C1) * (2 * sigma_xy + C2);
            double den = (mu_x * mu_x + mu_y * mu_y + C1) * (sigma_x + sigma_y + C2);
            local_total += num / den;
            local_count++;
        }
    }

    /* شرح: نجمع مجاميع كل العمليات وأعداد النوافذ، والنتيجة = المتوسط العام.
    */
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
/* شرح: توزيع المتجهات على العمليات. المخرجات: لكل عملية عدد المتجهات (vec_counts)
   وموقع بدايتها (vec_displs) وما يقابلهما بالبايت (×16) لاستخدامهما بـ Scatterv/Gatherv.
*/
static void compute_vector_distribution(int num_vectors, int vlen, int rank, int size,
                                         int *vec_counts, int *vec_displs,
                                         int *byte_counts, int *byte_displs)
{
    /* شرح: اختيار الطريقة: متغير البيئة VQ_STRATEGY = equal أو adaptive يفرضها،
       وإن لم يُحدد: متساوٍ عندما np ≤ 4 ومتكيّف عندما np > 4.
    */
    const char *strategy_env = getenv("VQ_STRATEGY");
    int use_equal_split;
    if (strategy_env && strcmp(strategy_env, "equal") == 0)
        use_equal_split = 1;
    else if (strategy_env && strcmp(strategy_env, "adaptive") == 0)
        use_equal_split = 0;
    else
        use_equal_split = (size <= 4);

    /* شرح (التوزيع المتساوي): كل عملية تأخذ العدد الكلي ÷ عدد العمليات، والباقي يُوزع
       واحداً واحداً على أول العمليات.
    */
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
        /* شرح (التوزيع المتكيّف): كل عملية تقيس سرعتها، ثم تُجمع السرعات عند الجميع،
           وكل عملية تأخذ حصة تتناسب مع سرعتها. مفيد على معالج غير متجانس (P-cores و E-cores).
        */
        double my_speed = calibrate_speed();

        double *speeds = (double *)malloc(size * sizeof(double));
        MPI_Allgather(&my_speed, 1, MPI_DOUBLE, speeds, 1, MPI_DOUBLE, MPI_COMM_WORLD);

        double sum_speed = 0.0;
        for (int r = 0; r < size; r++) sum_speed += speeds[r];
        if (sum_speed <= 0.0) { for (int r = 0; r < size; r++) speeds[r] = 1.0; sum_speed = size; }

        double *frac = (double *)malloc(size * sizeof(double));
        int assigned = 0;
        for (int r = 0; r < size; r++) {
            /* شرح: الحصة المثالية لكل عملية (عدد كسري)؛ نأخذ الجزء الصحيح أولاً.
            */
            double ideal = (double)num_vectors * speeds[r] / sum_speed;
            vec_counts[r] = (int)ideal;
            frac[r]       = ideal - (double)vec_counts[r];
            assigned     += vec_counts[r];
        }
        /* شرح: المتجهات الباقية بعد أخذ الأجزاء الصحيحة توزع على أصحاب أكبر الأجزاء الكسرية.
        */
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
/* شرح: نمط الصورة: غير معروف أو رمادي أو ملوّن.
*/
typedef enum { MODE_UNKNOWN = 0, MODE_GRAY, MODE_COLOR } ImgMode;

static ImgMode detect_mode_from_file(const char *path)
{
    size_t len; char *buf = slurp_file(path, &len);
    if (!buf) return MODE_UNKNOWN;
    const char *p = buf, *end = buf + len;
    long count = 0;
    int val;
    while (next_int(&p, end, &val)) count++;
    free(buf);

    /* شرح: نعدّ الأرقام في الملف: 262144 رقم يعني رمادي، و 786432 يعني ملوّن (ثلاثة لكل بكسل)،
       وغير ذلك نمط غير معروف.
    */
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
/* شرح: المسار الكامل للصورة الرمادية (تُنفّذه كل العمليات، وأجزاء منه على rank 0 فقط).
*/
static int run_gray_parallel(int argc, char *argv[], int rank, int size, const char *image_path)
{
    (void)argc; (void)argv;

    const int K    = CODEBOOK_SIZE;
    const int vlen = BLOCK_SIZE * BLOCK_SIZE;

    /* شرح: حجم الصورة الأصلية = 262144 بايت (بكسل واحد لكل بايت).
    */
    int original_image_bytes = WIDTH * HEIGHT;

    uint8_t *image       = NULL;
    uint8_t *training_set = NULL;
    int      num_vectors  = 0;

    MPI_Barrier(MPI_COMM_WORLD);
    /* شرح: بدء قياس الزمن الكلي (بعد Barrier حتى تبدأ كل العمليات معاً).
    */
    double t_total0 = MPI_Wtime();

    if (rank == 0) {
        /* شرح (الخطوة 1): rank 0 فقط يقرأ الصورة من الملف النصي. وإذا فشلت القراءة يُوقف الجميع.
        */
        image = (uint8_t *)malloc(WIDTH * HEIGHT);
        if (!image) { fprintf(stderr, "malloc image failed\n"); MPI_Abort(MPI_COMM_WORLD,1); }

        if (!read_image_from_txt(image_path, image, WIDTH, HEIGHT)) {
            fprintf(stderr, "Failed to read image from text file.\n");
            free(image);
            MPI_Abort(MPI_COMM_WORLD, 1);
        }

        /* شرح (الخطوة 2): تقسيم الصورة إلى متجهات تدريب (16384 متجه).
        */
        num_vectors = build_training_vectors(image, &training_set);
        printf("Built %d training vectors (each %d elements)\n", num_vectors, vlen);
    }

    /* شرح: rank 0 يرسل عدد المتجهات لكل العمليات (الباقية لا تعرفه لأنها لم تقرأ الصورة).
    */
    MPI_Bcast(&num_vectors, 1, MPI_INT, 0, MPI_COMM_WORLD);

    int *vec_counts  = (int *)calloc(size, sizeof(int));
    int *vec_displs  = (int *)malloc(size * sizeof(int));
    int *byte_counts = (int *)malloc(size * sizeof(int));
    int *byte_displs = (int *)malloc(size * sizeof(int));

    /* شرح (الخطوة 3): تحديد حصة كل عملية من المتجهات (متساوٍ أو متكيّف حسب السرعة).
    */
    compute_vector_distribution(num_vectors, vlen, rank, size,
                                 vec_counts, vec_displs, byte_counts, byte_displs);

    int local_n = vec_counts[rank];

    /* شرح (الخطوة 4): Scatterv يرسل لكل عملية حصتها من المتجهات من rank 0.
    */
    uint8_t *local_v = (uint8_t *)malloc((size_t)local_n * vlen);
    MPI_Scatterv(training_set, byte_counts, byte_displs, MPI_UINT8_T,
                 local_v,      local_n * vlen,           MPI_UINT8_T,
                 0, MPI_COMM_WORLD);

    /* شرح (الخطوة 5): الـ codebook الابتدائي = كلمة وحدة هي متوسط كل المتجهات:
       كل عملية تجمع متجهاتها المحلية (double) ثم Allreduce يجمع المجاميع من الجميع ونقسم على العدد الكلي.
    */
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

    /* شرح: نحوّل المتجهات المحلية من uint8 إلى float لحساب المسافات.
    */
    float *local_vf = (float *)malloc((size_t)local_n * vlen * sizeof(float));
    for (int i = 0; i < local_n * vlen; i++)
        local_vf[i] = (float)local_v[i];

    /* شرح: labels (الكلي) عند rank 0 فقط، و local_labels (المحلي) عند كل عملية.
    */
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

    /* شرح (الخطوة 7): تجميع أرقام الكلمات من كل العمليات عند rank 0 بنفس ترتيب المتجهات.
    */
    MPI_Gatherv(local_labels, local_n,                MPI_UINT8_T,
                labels,       vec_counts, vec_displs, MPI_UINT8_T,
                0, MPI_COMM_WORLD);

    /* شرح: مصفوفتان لتجهيز الصورتين لـ SSIM (الأصلية والمسترجعة) عند كل العمليات.
    */
    uint8_t *ssim_a = (uint8_t *)malloc((size_t)WIDTH * HEIGHT);
    uint8_t *ssim_b = (uint8_t *)malloc((size_t)WIDTH * HEIGHT);

    uint8_t *codebook_data = NULL, *reconstructed_lbg = NULL, *labels_delta_u = NULL;
    uint8_t *reconstructed = NULL;
    int codebook_bytes = 0;

    if (rank == 0) {
        /* شرح (الخطوة 8): من هنا حتى نهاية الكتلة تنفذه rank 0 فقط. أولاً طباعة أول 10 كلمات
           من الـ codebook (كل كلمة 16 قيمة)، ثم زمن LBG وعدد التكرارات.
        */
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

        /* شرح: الإنتروبي قبل Huffman: أقل عدد bits لكل مؤشر نظرياً (الحد الأدنى لترميز المؤشرات).
        */
        double H = compute_entropy(labels, num_vectors, K);
        printf("Entropy before Huffman = %.3f bits/symbol\n", H);

        /* شرح: تحويل الـ codebook إلى uint8 (بتقريب كل قيمة) لحساب حجمه: 64×16 = 1024 بايت.
        */
        codebook_data = malloc(K * vlen);
        for (int k = 0; k < K; k++)
            for (int i = 0; i < vlen; i++)
                codebook_data[k * vlen + i] = (uint8_t) roundf(codebook_flat[k * vlen + i]);
        printf("Codebook converted to uint8_t (size = %d bytes)\n", K * vlen);

        /* شرح: إعادة بناء مباشرة من LBG (قبل Delta و Huffman) وحفظها في lbg_decompress.txt
           للمقارنة والتحقق.
        */
        reconstructed_lbg = malloc(WIDTH * HEIGHT);
        decompress_image(reconstructed_lbg, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, labels);

        write_u8_lines("lbg_decompress.txt", reconstructed_lbg, (size_t)(WIDTH*HEIGHT));

        /* شرح (Delta coding): نخزن أول مؤشر كما هو، وللباقي: الفرق عن المؤشر السابق + 128
           (بباقي القسمة على 256 لأن النوع uint8). المؤشرات المتجاورة غالباً متقاربة، فيقل الإنتروبي.
        */
        double td0 = MPI_Wtime();
        labels_delta_u = malloc(num_vectors);
        labels_delta_u[0] = labels[0];
        for (int i = 1; i < num_vectors; i++)
            labels_delta_u[i] = (uint8_t)(labels[i] - labels[i-1] + 128);

        double H_delta = compute_entropy(labels_delta_u, num_vectors, 256);
        double td1 = MPI_Wtime();
        printf("[Delta Encode] Done in %.6f seconds\n", td1 - td0);
        printf("Entropy after Delta   = %.3f bits/symbol\n", H_delta);

        /* شرح (الخطوة: Huffman): نضغط مؤشرات Delta. labels_decoded = المؤشرات المفكوكة من خرج Huffman.
        */
        int huff_data_bytes = 0;
        int header_bytes    = 0;
        double t_huff0 = MPI_Wtime();
        uint8_t *labels_decoded = (uint8_t *)malloc(num_vectors);
        int huff_total = huffman_on_labels(labels_delta_u, num_vectors, 255,
                                            &huff_data_bytes, &header_bytes, labels_decoded);
        double t_huff1 = MPI_Wtime();
        double time_huff = t_huff1 - t_huff0;
        printf("Time (Huffman only): %.4f seconds\n\n", time_huff);

        printf("Huffman data bytes  = %d\n", huff_data_bytes);
        printf("Huffman total bytes = %d\n", huff_total);
        printf("Header bytes        = %d\n", header_bytes);

        /* شرح: الأحجام ونسب الضغط:
             CR (Huffman data only) = عدد المؤشرات ÷ حجم بيانات Huffman
             CR (Huffman total)     = عدد المؤشرات ÷ (header + بيانات Huffman)
             CR (system)            = حجم الصورة الأصلية ÷ (الـ codebook + header + بيانات Huffman)
             BPP = 8 ÷ CR(system) = عدد bits لكل بكسل
        */
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

        /* شرح: نعكس Delta على المؤشرات المفكوكة من Huffman (وليس الأصلية): أول مؤشر كما هو،
           وكل مؤشر = السابق + (القيمة المفكوكة − 128). ثم نعيد بناء الصورة النهائية منها.
        */
        labels[0] = labels_decoded[0];   /* [HUFFFIX] from the Huffman decoder output */
        for (int i = 1; i < num_vectors; i++)
            labels[i] = labels[i-1] + ((int)labels_decoded[i] - 128);
        free(labels_decoded);

        reconstructed = malloc(WIDTH * HEIGHT);
        decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, labels);

    }

    if (rank == 0) {
        /* شرح (الخطوة: الإخراج): rank 0 يحفظ الصورة المسترجعة نصاً (decompress.txt) وكصور BMP
           (original.bmp الأصلية و compressed.bmp المسترجعة)، ثم يحسب MSE و PSNR.
        */
        write_u8_lines("decompress.txt", reconstructed, (size_t)(WIDTH*HEIGHT));

        save_bmp_gray("original.bmp",   image,                  WIDTH, HEIGHT);
        save_bmp_gray("compressed.bmp", reconstructed, WIDTH, HEIGHT);
        printf("Saved: original.bmp  compressed.bmp\n");

        double mse  = compute_mse(image, reconstructed, WIDTH*HEIGHT);
        double psnr = compute_psnr(image, reconstructed, WIDTH*HEIGHT);
        printf("MSE = %.2f\n", mse);
        printf("PSNR = %.2f dB\n", psnr);

        /* شرح: نسبة الضغط البسيطة (CR) بافتراض بايت واحد لكل مؤشر: الأصلية ÷ (codebook + المؤشرات).
           ملاحظة: 64 كلمة تحتاج 6 bits فقط للمؤشر، فهذا خط أساس ضعيف (الأعدل 19.69).
        */
        int indexes_bytes = num_vectors;
        int original_bytes = WIDTH * HEIGHT;
        double CR = (double)original_bytes / (codebook_bytes + indexes_bytes);
        printf("Compression Ratio (CR): %.2f\n", CR);

        /* شرح: نجهّز الصورتين (الأصلية والمسترجعة) لإرسالهما لكل العمليات.
        */
        memcpy(ssim_a, image,                  (size_t)WIDTH * HEIGHT);
        memcpy(ssim_b, reconstructed, (size_t)WIDTH * HEIGHT);

        free(codebook_data);
        free(reconstructed_lbg);
        free(labels_delta_u);
        free(reconstructed);
        free(image);
        free(training_set);
        free(labels);
    }

    /* شرح (الخطوة: SSIM): rank 0 يبث الصورتين لكل العمليات حتى يحسب كل منها حصته من SSIM.
    */
    MPI_Bcast(ssim_a, WIDTH * HEIGHT, MPI_UINT8_T, 0, MPI_COMM_WORLD);
    MPI_Bcast(ssim_b, WIDTH * HEIGHT, MPI_UINT8_T, 0, MPI_COMM_WORLD);

    MPI_Barrier(MPI_COMM_WORLD);
    /* شرح: حساب SSIM بالتوازي وقياس زمنه (لا يشمل زمن البث).
    */
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
        /* شرح: الزمن الكلي = من بداية الدالة إلى نهايتها (يشمل القراءة والكتابة و LBG و SSIM).
        */
        double time_taken = MPI_Wtime() - t_total0;
        printf("Total execution time: %.3f seconds\n", time_taken);
    }

    return 0;
}

/* ============================================================
   ------------------------ COLOR PATH -----------------------------
   Mirrors pco.c's main() body exactly, wrapped as a function.
   ============================================================ */
/* شرح: نتائج كل قناة لوحدها (MSE و PSNR و SSIM و زمن LBG وحجمها المضغوط وصورتها المسترجعة).
*/
typedef struct {
    double mse, psnr, ssim;
    double lbg_time;
    int compressed_bytes;
    uint8_t *reconstructed;
} ChannelResult;

/* شرح: المسار الكامل للصورة الملوّنة. نفس مسار الرمادي لكن بثلاث قنوات: R ثم G ثم B،
   وكل قناة تُعامل كصورة رمادية مستقلة (بدون تحويل ألوان).
*/
static int run_color_parallel(int argc, char *argv[], int rank, int size, const char *image_path)
{
    (void)argc; (void)argv;

    const int K    = CODEBOOK_SIZE;
    const int vlen = BLOCK_SIZE * BLOCK_SIZE;
    /* شرح: عدد المتجهات معروف مسبقاً (نفسه لكل قناة) = 16384.
    */
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

        /* شرح: rank 0 يقرأ الصورة الملوّنة ويفصلها إلى قنواتها الثلاث.
        */
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
    /* شرح: توزيع المتجهات يُحسب مرة وحدة ويُستخدم للقنوات الثلاث (لأن عدد المتجهات نفسه).
    */
    compute_vector_distribution(num_vectors, vlen, rank, size,
                                 vec_counts, vec_displs, byte_counts, byte_displs);

    int local_n = vec_counts[rank];

    uint8_t *ssim_a = (uint8_t *)malloc((size_t)channel_bytes);
    uint8_t *ssim_b = (uint8_t *)malloc((size_t)channel_bytes);

    ChannelResult results[3];
    memset(results, 0, sizeof(results));

    /* شرح: حلقة القنوات: لكل قناة نفس خطوات الرمادي (متجهات، توزيع، LBG، تجميع،
       Delta، Huffman، إعادة بناء، MSE و PSNR، SSIM).
    */
    for (int ch = 0; ch < 3; ch++) {

        uint8_t *training_set = NULL;
        if (rank == 0) {
            /* شرح: بناء متجهات هذه القناة (rank 0).
            */
            int nv = build_training_vectors(channels[ch], &training_set);
            if (nv != num_vectors) {
                fprintf(stderr, "Unexpected vector count for %s channel.\n", channel_names[ch]);
                MPI_Abort(MPI_COMM_WORLD, 1);
            }
        }

        /* شرح: إرسال حصص متجهات هذه القناة، ثم الـ codebook الابتدائي (متوسط المتجهات)، ثم LBG.
        */
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
        /* شرح: LBG المتوازي لهذه القناة، وقياس زمنه.
        */
        int lbg_iters = parallel_lbg(local_vf, local_n, num_vectors, vlen, K,
                    codebook_flat, local_labels, rank, size, 0);
        MPI_Barrier(MPI_COMM_WORLD);
        double t1 = MPI_Wtime();
        double lbg_time = t1 - t0;

        /* شرح: تجميع مؤشرات هذه القناة عند rank 0.
        */
        MPI_Gatherv(local_labels, local_n,                MPI_UINT8_T,
                    labels,       vec_counts, vec_displs, MPI_UINT8_T,
                    0, MPI_COMM_WORLD);

        uint8_t *labels_delta_u = NULL, *reconstructed = NULL;

        if (rank == 0) {
            printf("\n  [%s channel] LBG time=%.4fs  LBG iters=%d\n", channel_names[ch], lbg_time, lbg_iters);

            labels_delta_u = (uint8_t*)malloc(num_vectors);
            labels_delta_u[0] = labels[0];
            for (int i = 1; i < num_vectors; i++)
                labels_delta_u[i] = (uint8_t)(labels[i] - labels[i-1] + 128);

            int huff_data_bytes = 0, header_bytes = 0;
            /* شرح: Delta ثم Huffman لهذه القناة، والمؤشرات المفكوكة تُستخدم لإعادة البناء.
            */
            uint8_t *labels_decoded = (uint8_t*)malloc(num_vectors);
            int huff_total = huffman_on_labels(labels_delta_u, num_vectors, 255,
                                               &huff_data_bytes, &header_bytes, labels_decoded);
            (void)huff_data_bytes; (void)header_bytes;

            int codebook_bytes = K * vlen;
            results[ch].compressed_bytes = codebook_bytes + huff_total;
            results[ch].lbg_time = lbg_time;

            labels[0] = labels_decoded[0];   /* [HUFFFIX] from the Huffman decoder output */
            for (int i = 1; i < num_vectors; i++)
                labels[i] = labels[i-1] + ((int)labels_decoded[i] - 128);
            free(labels_decoded);

            reconstructed = (uint8_t*)malloc(channel_bytes);
            decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, labels);

        }

        if (rank == 0) {

            /* شرح: MSE و PSNR لهذه القناة، وتُحفظ صورتها المسترجعة لاستخدامها بالحفظ النهائي.
            */
            results[ch].mse  = compute_mse(channels[ch], reconstructed, channel_bytes);
            results[ch].psnr = compute_psnr(channels[ch], reconstructed, channel_bytes);
            results[ch].reconstructed = reconstructed;

            printf("  [%s channel] PSNR=%.2f dB  CR(system)=%.2fX\n",
                   channel_names[ch], results[ch].psnr,
                   (double)channel_bytes / (double)results[ch].compressed_bytes);

            memcpy(ssim_a, channels[ch],        channel_bytes);
            memcpy(ssim_b, reconstructed, channel_bytes);

            free(labels_delta_u);
            free(labels);
            free(training_set);
        }

        /* شرح: بث الصورتين (الأصلية والمسترجعة لهذه القناة) لكل العمليات، ثم SSIM متوازي.
        */
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
        /* شرح: النتائج الإجمالية (rank 0):
             RGB MSE  = متوسط MSE القنوات الثلاث، و RGB PSNR محسوب منه
             RGB CR   = حجم الأصلية (3 قنوات) ÷ مجموع الأحجام المضغوطة (لكل قناة codebook خاص)
             SSIM     = متوسط SSIM القنوات الثلاث (ليس SSIM ملوّناً قياسياً)
             وقت LBG  = مجموع أزمنة القنوات الثلاث
        */
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

        /* شرح: حفظ الصورتين الملوّنتين (الأصلية والمسترجعة) كـ BMP. لا توجد ملفات نصية بالملوّن.
        */
        save_bmp_color("original_color.bmp", R, G, B, WIDTH, HEIGHT);
        save_bmp_color("compressed_color.bmp",
                       results[0].reconstructed,
                       results[1].reconstructed,
                       results[2].reconstructed,
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
        free(results[0].reconstructed);
        free(results[1].reconstructed);
        free(results[2].reconstructed);
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
/* شرح: نقطة البداية. كل عملية MPI تنفّذ main. الخطوات: تشغيل MPI، تحديد نمط الصورة
   (رمادي/ملوّن) عند rank 0 وبثه للجميع، ثم تنفيذ المسار المناسب، ثم إنهاء MPI.
*/
int main(int argc, char *argv[])
{
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    /* شرح: مسار الصورة هو الوسيط الأول (الافتراضي img.txt)، والوسيط الثاني اختياري: --gray أو --color.
    */
    const char *image_path = (argc > 1) ? argv[1] : "img.txt";
    int mode_int = MODE_UNKNOWN;

    if (rank == 0) {
        /* شرح: rank 0 فقط يحدد النمط: من الوسيط الثاني إن وُجد، وإلا بعدّ الأرقام في الملف.
        */
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

    /* شرح: rank 0 يرسل النمط لكل العمليات. إذا كان غير معروف تنتهي كل العمليات بخطأ.
    */
    MPI_Bcast(&mode_int, 1, MPI_INT, 0, MPI_COMM_WORLD);

    if (mode_int == MODE_UNKNOWN) {
        MPI_Finalize();
        return 1;
    }

    int rc;
    /* شرح: تنفيذ مسار الرمادي أو الملوّن حسب النمط.
    */
    if (mode_int == MODE_GRAY)
        rc = run_gray_parallel(argc, argv, rank, size, image_path);
    else
        rc = run_color_parallel(argc, argv, rank, size, image_path);

    MPI_Finalize();
    return rc;
}
