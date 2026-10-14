/*
 * ======================================================================
 *  arabic_mpi.c  —  ضغط الصور بطريقة VQ-LBG بشكل متوازٍ باستخدام MPI
 * ======================================================================
 *  هذا الملف هو نفس كود pam_v4_nofilter.c (النسخة المعتمدة) حرفياً،
 *  والفرق الوحيد أن كل التعليقات صارت بالعربي مع شرح كل خطوة.
 *  (لم يتغير أي سطر برمجي ولا أي نص يُطبع على الشاشة.)
 *
 *  فكرة البرنامج باختصار:
 *    1) نقسم الصورة (512×512) إلى بلوكات 4×4، كل بلوك = متجه من 16 قيمة.
 *    2) خوارزمية LBG تبني "قاموس" (codebook) من 64 متجهاً يمثل كل بلوكات الصورة.
 *    3) نستبدل كل بلوك برقم (index) أقرب متجه في القاموس.
 *    4) نحسب الفرق (delta) بين كل رقمين متتاليين، ثم نضغطها بترميز Huffman.
 *    5) نفك الضغط ونعيد بناء الصورة، ونحسب الجودة (MSE, PSNR, SSIM)
 *       ونسبة الضغط (CR).
 *
 *  الجزء المتوازي (MPI): الخطوة 2 (LBG) هي الأثقل، فنوزع المتجهات على
 *  العمليات (ranks)؛ كل عملية تعالج حصتها، ثم نجمع النتائج الجزئية بـ MPI_Allreduce.
 *
 *  كيف تُترجم وتُشغَّل:
 *      mpicc -O2 -Wall -Wextra -o lbg_par arabic_mpi.c -lm
 *      mpirun -np 4  ./lbg_par صورة.txt --gray      (صورة رمادية)
 *      mpirun -np 14 ./lbg_par صورة.txt --color     (صورة ملونة)
 *      VQ_STRATEGY=equal    mpirun -np 8 ./lbg_par صورة.txt --gray   (توزيع متساوٍ)
 *      VQ_STRATEGY=adaptive mpirun -np 8 ./lbg_par صورة.txt --gray   (توزيع حسب سرعة كل نواة)
 *  ملف الصورة نصي: بكسل واحد لكل رقم (رمادي) أو "R G B" لكل بكسل (ملون).
 *
 *  ملاحظة مهمة عن نسبة الضغط (CR):
 *    البرنامج لا يكتب ملفاً مضغوطاً على القرص؛ يحسب حجمه:
 *    حجم الـ codebook (1024 بايت) + بيانات Huffman + جدول Huffman
 *    (محسوب 4 بايت لكل رمز مستخدم). لذلك CR هنا "محسوب" بهذه الاتفاقية.
 *
 *  ملفات الإخراج: original.bmp و compressed.bmp (الصورة بعد الفك)،
 *  decompress.txt و lbg_decompress.txt (قيم الصورة المعاد بناؤها).
 * ======================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <time.h>
#include <string.h>
#include <mpi.h>

/* الثوابت الأساسية للبرنامج (لا تتغير أثناء التشغيل):
   WIDTH, HEIGHT : أبعاد الصورة 512×512 بكسل.
   BLOCK_SIZE    : طول ضلع البلوك (4×4 بكسل).
   DELTA         : عامل الانقسام في LBG (كل متجه ينقسم إلى متجهين (1+DELTA) و(1-DELTA)).
   EPSILON       : حد التوقف: نوقف التكرار عندما يصير التحسن النسبي أقل من هذا الرقم.
   CODEBOOK_SIZE : حجم القاموس النهائي (64 متجهاً).
   MAX_ITER      : أقصى عدد تكرارات لكل مرحلة انقسام.
   K1, K2        : ثوابت مقياس SSIM (0.01 و0.03).
   VLEN          : طول المتجه = 4×4 = 16 قيمة. */
#define WIDTH 512
#define HEIGHT 512
#define BLOCK_SIZE 4
#define DELTA 0.01f
#define EPSILON 0.0001f
#define CODEBOOK_SIZE 64
#define MAX_ITER 100
#define K1 0.01
#define K2 0.03
#define VLEN (BLOCK_SIZE * BLOCK_SIZE)

/* حفظ صورة رمادية بصيغة BMP (8 بت لكل بكسل) لنتمكن من فتحها بأي برنامج عرض.
   المدخلات: اسم الملف، مصفوفة البكسلات، العرض، الارتفاع. */
void save_bmp_gray(const char *filename, uint8_t *data, int width, int height)
{
    /* صيغة BMP تتطلب أن يكون طول كل صف من مضاعفات الـ 4 بايت، لذلك نضيف حشواً (padding) عند الحاجة. */
    int row_padded = (width + 3) & ~3;
    int img_size   = row_padded * height;
    int file_size  = 54 + 1024 + img_size;
    int data_offset = 54 + 1024;

    /* نبني رأس ملف BMP (54 بايت): نوع الملف 'BM'، حجم الملف، العرض، الارتفاع، وعدد البتات لكل بكسل. */
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

    /* نفتح الملف للكتابة الثنائية؛ إذا فشل الفتح نطبع الخطأ ونخرج من الدالة. */
    FILE *f = fopen(filename, "wb");
    if (!f) { perror(filename); return; }
    fwrite(header, 1, 54, f);
    /* جدول الألوان (palette): 256 مستوى رمادي، كل مستوى يقابل (i,i,i) أي نفس القيمة للألوان الثلاثة. */
    for (int i = 0; i < 256; i++) {
        uint8_t e[4] = {(uint8_t)i, (uint8_t)i, (uint8_t)i, 0};
        fwrite(e, 1, 4, f);
    }
    uint8_t pad[3] = {0};
    /* BMP يخزن الصفوف من الأسفل إلى الأعلى، لذلك نكتب من آخر صف إلى الأول، ونضيف الحشو بعد كل صف. */
    for (int y = height - 1; y >= 0; y--) {
        fwrite(&data[y * width], 1, width, f);
        if (row_padded - width > 0)
            fwrite(pad, 1, row_padded - width, f);
    }
    fclose(f);
}

/* حفظ صورة ملونة بصيغة BMP (24 بت: 3 بايت لكل بكسل). نفس فكرة الدالة السابقة لكن بدون جدول ألوان. */
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
            /* BMP يخزن ألوان البكسل بترتيب (أزرق، أخضر، أحمر) وليس (أحمر، أخضر، أزرق). */
            uint8_t pixel[3] = { B[idx], G[idx], R[idx] };
            fwrite(pixel, 1, 3, f);
        }
        if (row_padded - row_bytes > 0)
            fwrite(pad, 1, row_padded - row_bytes, f);
    }
    fclose(f);
}

/* تحويل الصورة إلى "متجهات تدريب": نقسم الصورة إلى بلوكات 4×4، وكل بلوك يصير متجهاً من 16 قيمة.
   عدد البلوكات = (512/4)×(512/4) = 16384 متجه. الدالة تُرجع عدد المتجهات. */
int build_training_vectors(uint8_t *image, uint8_t **training_set)
{
    int num_blocks_x = WIDTH / BLOCK_SIZE;
    int num_blocks_y = HEIGHT / BLOCK_SIZE;
    int num_vectors = num_blocks_x * num_blocks_y;
    int vector_length = BLOCK_SIZE * BLOCK_SIZE;

    /* نحجز ذاكرة لكل المتجهات (16384 × 16 بايت). */
    *training_set = (uint8_t *)malloc(num_vectors * vector_length);
    if (!*training_set) {
        fprintf(stderr, "Memory allocation failed\n");
        return -1;
    }

    int idx = 0;
    /* نمر على الصورة بلوكاً بلوكاً (من اليسار لليمين ومن الأعلى للأسفل)، وننسخ بكسلات كل بلوك إلى متجه. */
    for (int y = 0; y < HEIGHT; y += BLOCK_SIZE) {
        for (int x = 0; x < WIDTH; x += BLOCK_SIZE) {
            for (int r = 0; r < BLOCK_SIZE; r++) {
                for (int c = 0; c < BLOCK_SIZE; c++) {
                    int img_index = (y + r) * WIDTH + (x + c);
                    int vec_index = r * BLOCK_SIZE + c;
                    /* بكسل الصورة (الصف y+r، العمود x+c) يذهب إلى الموضع (r*4+c) داخل متجه البلوك. */
                    (*training_set)[idx * vector_length + vec_index] = image[img_index];
                }
            }
            idx++;
        }
    }
    return num_vectors;
}

/* قراءة صورة رمادية من ملف نصي (رقم لكل بكسل). تُرجع 1 إذا قرأت 512×512 بكسل كاملة. */
int read_image_from_txt(const char *filename, uint8_t *image, int width, int height) {
    FILE *f = fopen(filename, "r");
    if (!f) { perror("Error opening image file"); return 0; }
    int val, count = 0;
    while (fscanf(f, "%d", &val) == 1 && count < width * height) {
        /* نحصر القيمة بين 0 و255 (أي قيمة خارج المدى تُقصّ إلى الحد). */
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

/* قراءة صورة ملونة من ملف نصي: كل بكسل ثلاثة أرقام (R G B). نخزنها في ثلاث مصفوفات منفصلة. */
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

/* مربع المسافة الإقليدية بين متجهين طول كل منهما 16.
   هذه الدالة هي أكثر دالة تُستدعى في البرنامج (تُستدعى ملايين المرات داخل LBG). */
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

/* قياس سرعة هذه العملية (rank) بتجربة قصيرة تحاكي عمل LBG، وتُرجع "عدد المقارنات في الثانية".
   تُستخدم فقط في التوزيع Adaptive: العملية الأسرع (نواة P) تأخذ متجهات أكثر من الأبطأ (نواة E). */
static double calibrate_speed(void)
{
    enum { NV = 512, NC = 64, REP = 2, CVLEN = 16 };
    float *v  = (float *)malloc((size_t)NV * CVLEN * sizeof(float));
    float *cb = (float *)malloc((size_t)NC * CVLEN * sizeof(float));
    if (!v || !cb) { free(v); free(cb); return 1.0; }

    /* نملأ بيانات تجريبية ثابتة (أرقام شبه عشوائية لكن متطابقة في كل مرة). */
    for (int i = 0; i < NV * CVLEN; i++)
        v[i]  = (float)(((unsigned)i * 1103515245u + 12345u) & 255u);
    for (int i = 0; i < NC * CVLEN; i++)
        cb[i] = (float)(((unsigned)i * 22695477u + 1u) & 255u);

    /* نكرر القياس 3 مرات: المرة الأولى للتسخين (تُهمل)، ونأخذ أسرع زمن من الباقي حتى لا تتأثر النتيجة بتأخير عابر. */
    enum { TRIALS = 3 };
    volatile float sink = 0.0f;
    double dt = 1e30;
    for (int trial = 0; trial < TRIALS; trial++) {
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
        /* نحتفظ بأقل زمن (أسرع محاولة) بعد تجاهل محاولة التسخين الأولى. */
        if (trial > 0 && t < dt) dt = t;
    }
    free(v); free(cb);
    (void)sink;
    if (dt <= 0.0 || dt > 1e29) dt = 1e-6;
    /* السرعة = عدد المقارنات المنفذة ÷ الزمن. */
    return (double)REP * (double)NV * (double)NC / dt;
}

/* خوارزمية LBG المتوازية: تبني القاموس (codebook) من المتجهات الموزعة على العمليات.
   المدخلات: local_vf (متجهات هذه العملية فقط)، local_n (عددها)، num_vectors (العدد الكلي)،
   K (حجم القاموس المطلوب)، codebook (القاموس: يبدأ بمتجه واحد ويكبر)،
   local_labels (رقم أقرب متجه لكل متجه محلي)، rank (رقم العملية)، size (عدد العمليات).
   المخرج: مجموع عدد تكرارات Lloyd في كل مراحل الانقسام (متساوٍ في كل العمليات). */
int parallel_lbg(const float *local_vf, int local_n, int num_vectors,
                   int vlen, int K, float *codebook, uint8_t *local_labels,
                   int rank, int size, int verbose)
{

    (void)size; (void)vlen;

    /* مخزن مؤقت واحد يحمل ثلاثة أشياء لكل مرحلة: (1) مجاميع القيم لكل متجه في القاموس،
       (2) عدد المتجهات في كل عنقود، (3) مجموع التشويه. نجمعها كلها بعملية MPI_Allreduce واحدة.
       نستخدم double لأن مجاميع القيم الصحيحة تكون دقيقة تماماً ولا تعتمد على ترتيب الجمع، فتخرج
       نتيجة LBG ونفس عدد التكرارات بغض النظر عن عدد العمليات. */
    int buf_capacity = K * VLEN + K + 1;
    double *buf = (double *)calloc(buf_capacity, sizeof(double));

    int k = 1;
    int total_iters = 0;
    /* حلقة المراحل: نبدأ بمتجه واحد (k=1) ونضاعف k في كل مرحلة (1→2→4→…→64). */
    while (k < K) {
        /* خطوة الانقسام: كل متجه في القاموس ينقسم إلى متجهين متقاربين: (1+DELTA)×المتجه و(1−DELTA)×المتجه. */
        for (int i = k - 1; i >= 0; i--)
            for (int j = 0; j < VLEN; j++) {
                float v = codebook[i * VLEN + j];
                codebook[(k + i) * VLEN + j] = v * (1.0f - DELTA);
                codebook[i        * VLEN + j] = v * (1.0f + DELTA);
            }
        /* نضاعف عدد المتجهات في القاموس (ولا نتجاوز K). */
        k = (k * 2 > K) ? K : k * 2;

        /* تحديد مواضع الأقسام الثلاثة داخل المخزن المؤقت: المجاميع، ثم العدادات، ثم مجموع التشويه. */
        const int sum_off  = 0;
        const int cnt_off  = k * VLEN;
        const int dist_off = cnt_off + k;
        const int active   = dist_off + 1;

        double prev_dist   = 1e30;
        double improvement = 1.0;
        int   iter        = 0;

        /* حلقة تكرار Lloyd: (تعيين المتجهات لأقرب متجه قاموس) ثم (تحديث القاموس) حتى يستقر التشويه. */
        do {
            /* نصفّر المخزن المؤقت قبل كل تكرار. */
            memset(buf, 0, active * sizeof(double));

            /* الخطوة (أ) التعيين: كل عملية تمر على متجهاتها المحلية فقط (وهذا هو الجزء المتوازي). */
            for (int i = 0; i < local_n; i++) {
                const float *v = local_vf + i * VLEN;
                float best = 1e30f;
                int   bi   = 0;
                /* نبحث عن أقرب متجه في القاموس (أصغر مسافة) للمتجه الحالي. */
                for (int c = 0; c < k; c++) {
                    float d = distance16f(codebook + c * VLEN, v);
                    if (d < best) { best = d; bi = c; }
                }
                /* نسجل رقم أقرب متجه، ونضيف مسافته للتشويه، ونزيد عداد ذلك العنقود، ونجمع قيم المتجه إلى مجموع عنقوده. */
                local_labels[i]    = (uint8_t)bi;
                buf[dist_off]     += best;
                buf[cnt_off + bi] += 1.0;
                double *s = buf + sum_off + bi * VLEN;
                for (int j = 0; j < VLEN; j++)
                    s[j] += v[j];
            }

            /* الخطوة (ب) الجمع: كل العمليات تجمع مخازنها الجزئية، فتحصل كل عملية على المجاميع الكلية لكل الصورة.
               هذه هي نقطة التواصل الوحيدة في كل تكرار. */
            MPI_Allreduce(MPI_IN_PLACE, buf, active,
                          MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);

            /* متوسط التشويه الكلي لكل الصورة (نفس القيمة في كل العمليات). */
            double global_dist = buf[dist_off] / (double)num_vectors;

            /* الخطوة (ج) التحديث: كل متجه قاموس يصير متوسط المتجهات المنتمية لعنقوده (المجموع ÷ العدد). */
            for (int c = 0; c < k; c++) {
                double cnt = buf[cnt_off + c];
                if (cnt > 0.0) {
                    double *s  = buf + sum_off + c * VLEN;
                    for (int j = 0; j < VLEN; j++)
                        codebook[c * VLEN + j] = (float)(s[j] / cnt);
                }
            }

            /* نحسب التحسن النسبي في التشويه مقارنة بالتكرار السابق؛ إذا صار صغيراً (أقل من EPSILON) نتوقف. */
            improvement = fabs(prev_dist - global_dist) / (global_dist + 1e-9);
            prev_dist   = global_dist;
            iter++;

            if (rank == 0 && verbose && iter == 1)
                printf("k=%3d iter=%3d distortion=%.4f  (first)\n", k, iter, prev_dist);

        /* شرط الاستمرار: لم نصل لأقصى عدد تكرارات، وما زال التحسن أكبر من EPSILON. */
        } while (iter < MAX_ITER && improvement > (double)EPSILON);
        /* نضيف عدد تكرارات هذه المرحلة للمجموع الكلي. */
        total_iters += iter;

        if (rank == 0 && verbose)
            printf("k=%3d iter=%3d distortion=%.4f  (converged)\n", k, iter, prev_dist);
    }
    free(buf);
    return total_iters;
}

/* إعادة بناء الصورة: لكل بلوك نأخذ رقمه (label) ونجلب متجه القاموس المقابل له
   (16 قيمة) ونضعها في مكان البلوك بالصورة. هذه هي خطوة "فك الضغط" في VQ. */
void decompress_image(uint8_t *reconstructed, int width, int height,
                       int block_size, const float *codebook, uint8_t *labels)
{
    int blocks_per_row = width / block_size;
    int blocks_per_col = height / block_size;
    int vec_idx = 0;
    for (int by = 0; by < blocks_per_col; by++) {
        for (int bx = 0; bx < blocks_per_row; bx++) {
            /* رقم متجه القاموس الخاص بهذا البلوك. */
            int code_idx = labels[vec_idx];
            for (int r = 0; r < block_size; r++) {
                for (int c = 0; c < block_size; c++) {
                    int img_idx = (by*block_size+r)*width + (bx*block_size+c);
                    int pos = r*block_size + c;
                    /* نقرّب قيمة القاموس إلى أقرب عدد صحيح (0..255) ونضعها في مكانها بالصورة. */
                    reconstructed[img_idx] =
                        (uint8_t)roundf(codebook[code_idx * VLEN + pos]);
                }
            }
            vec_idx++;
        }
    }
}

/* متوسط مربع الخطأ MSE بين الصورة الأصلية والمعاد بناؤها (كلما قل كانت الجودة أعلى). */
double compute_mse(uint8_t *original, uint8_t *reconstructed, int size) {
    double mse = 0.0;
    for (int i = 0; i < size; i++) {
        double diff = (double)original[i] - (double)reconstructed[i];
        mse += diff*diff;
    }
    return mse/size;
}

/* نسبة الإشارة إلى الضجيج PSNR بالديسيبل: 10·log10(255² / MSE). كلما زادت كانت الجودة أعلى. */
double compute_psnr(uint8_t *original, uint8_t *reconstructed, int size) {
    double mse = compute_mse(original, reconstructed, size);
    if (mse == 0) return 100.0;
    return 10.0 * log10((255.0*255.0)/mse);
}

/* الإنتروبي (بالبت لكل رمز): الحد النظري الأدنى لعدد البتات اللازمة لتمثيل كل رقم، بحسب تكرارات الأرقام. */
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

/* ترميز Huffman: نبني شجرة تعطي الأرقام الكثيرة التكرار رمزاً قصيراً والنادرة رمزاً طويلاً. هذا هيكل عقدة الشجرة. */
typedef struct HuffNode {
    int value;
    uint32_t freq;
    struct HuffNode *left;
    struct HuffNode *right;
} HuffNode;

typedef struct { HuffNode **data; int size; int capacity; } MinHeap;
/* HuffCode: رمز Huffman لقيمة معينة = البتات وعددها. */
typedef struct { uint64_t bits; int length; } HuffCode;

/* أدوات الكومة الصغرى (min-heap): تُستخدم لاختيار العقدتين الأقل تكراراً بسرعة أثناء بناء الشجرة. */
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
/* بناء شجرة Huffman: ندمج في كل مرة أقل عقدتين تكراراً في عقدة أب (مجموع تكراريهما) حتى تبقى عقدة واحدة هي الجذر. */
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
/* استخراج رمز كل قيمة من الشجرة: الذهاب يساراً يضيف البت 0، ويميناً يضيف البت 1. */
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
/* الترميز: نستبدل كل رقم برمزه (بتات) ونرصّ كل البتات في بايتات متتالية. تُرجع البيانات المرمّزة وحجمها. */
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
            /* نضع البت في موضعه داخل البايت الحالي (من اليسار)، وعند اكتمال 8 بتات نخزن البايت ونبدأ بايتاً جديداً. */
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
/* فك الترميز: نقرأ البتات واحداً واحداً ونمشي في الشجرة (0 يسار، 1 يمين) حتى نصل لورقة فنكتب قيمتها ونرجع للجذر. */
static void huff_decode(uint8_t *encoded, int enc_bytes, HuffNode *root, int original_n, uint8_t *out) {
    HuffNode *node = root;
    int out_pos = 0;
    for (int i = 0; i < enc_bytes; ++i) {
        uint8_t byte = encoded[i];
        for (int b = 7; b >= 0; --b) {
            if (out_pos >= original_n) return;
            int bit = (byte >> b) & 1;
            node = bit ? node->right : node->left;
            if (!node) { node = root; continue; }
            if (node->value >= 0) { out[out_pos++] = (uint8_t)node->value; node = root; }
        }
    }
}
/* ضغط سلسلة الأرقام بترميز Huffman وفحص صحة الفك. تُرجع الحجم الكلي (بيانات + جدول).
   الخطوات: (1) عدّ تكرار كل رقم، (2) بناء الشجرة والرموز، (3) الترميز، (4) حساب حجم الجدول،
   (5) الفك ومقارنته بالأصل للتأكد أنه مطابق تماماً (lossless). */
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

    /* حجم جدول Huffman: نحسبه 4 بايت لكل رمز مستخدم (تكرار الرمز فقط).
       هذه اتفاقية حساب: البرنامج لا يكتب ملفاً مضغوطاً حقيقياً. ملف حقيقي قد يحتاج بايتاً إضافياً
       لكل رمز (لمعرفة هوية الرمز) وبعض المعلومات العامة، وهذا يغيّر نسبة الضغط بحدود 1% تقريباً. */
    int header_bytes = used_symbols * sizeof(uint32_t);
    int total_compressed = header_bytes + enc_bytes;

    uint8_t *decoded = (uint8_t*)malloc(num_labels);
    /* نفك البيانات المرمّزة باستخدام الشجرة الموجودة في الذاكرة. */
    huff_decode(enc, enc_bytes, root, num_labels, decoded);

    /* فحص الصحة: كل رقم بعد الفك يجب أن يساوي الرقم الأصلي؛ وإلا نطبع ERROR. */
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

/* نافذة غاوس 11×11 (σ=1.5) المستخدمة في SSIM؛ نحسبها مرة واحدة ونطبّعها بحيث مجموع أوزانها = 1. */
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

/* حساب مقياس SSIM (التشابه البنيوي) بين الصورتين بشكل متوازٍ: نقسم صفوف الصورة على العمليات،
   كل عملية تحسب SSIM لصفوفها، ثم نجمع النتائج بـ MPI_Allreduce ونأخذ المتوسط. */
double SSIM_window_based_parallel(unsigned char *img1, unsigned char *img2,
                                   int W, int H, int rank, int size)
{
    const double (*gaussian11x11)[11] = ssim_gaussian_window();

    double local_total = 0.0;
    long   local_count = 0;

    /* النافذة 11×11 تحتاج 5 بكسلات من كل جانب، لذلك نحسب فقط البكسلات البعيدة 5 عن الحافة. هنا نقسم الصفوف بين العمليات. */
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
            /* لكل بكسل: نحسب المتوسط الموزون (mu) في النافذة للصورتين، ثم التباين والتباين المشترك. */
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
            /* ثوابت صغيرة لتجنب القسمة على صفر، ثم نحسب SSIM لهذا الموضع = (بسط) ÷ (مقام) حسب صيغة SSIM المعروفة. */
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
    /* نجمع المجموع والعدد من كل العمليات، ثم متوسط SSIM = المجموع ÷ العدد. */
    MPI_Allreduce(&local_total, &global_total, 1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
    MPI_Allreduce(&local_count, &global_count, 1, MPI_LONG,   MPI_SUM, MPI_COMM_WORLD);

    return (global_count > 0) ? global_total / (double)global_count : 0.0;
}

/* توزيع المتجهات على العمليات (من يأخذ كم متجهاً؟). المخرجات:
   vec_counts/vec_displs : عدد المتجهات وبدايتها لكل عملية، byte_counts/byte_displs : نفسها بالبايت.
   استراتيجيتان: Equal (متساوٍ) و Adaptive (حسب سرعة كل عملية). */
static void compute_vector_distribution(int num_vectors, int vlen, int rank, int size,
                                         int *vec_counts, int *vec_displs,
                                         int *byte_counts, int *byte_displs)
{
    /* نقرأ متغير البيئة VQ_STRATEGY: equal أو adaptive. بدونه: متساوٍ إذا عدد العمليات ≤ 4، وإلا Adaptive. */
    const char *strategy_env = getenv("VQ_STRATEGY");
    int use_equal_split;
    if (strategy_env && strcmp(strategy_env, "equal") == 0)
        use_equal_split = 1;
    else if (strategy_env && strcmp(strategy_env, "adaptive") == 0)
        use_equal_split = 0;
    else
        use_equal_split = (size <= 4);

    /* التوزيع المتساوي: كل عملية تأخذ N/P متجه (والباقي يوزع على الأوائل بمتجه إضافي). */
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
        /* التوزيع Adaptive: كل عملية تقيس سرعتها، ثم تتبادل كل العمليات السرعات (Allgather). */
        double my_speed = calibrate_speed();

        double *speeds = (double *)malloc(size * sizeof(double));
        MPI_Allgather(&my_speed, 1, MPI_DOUBLE, speeds, 1, MPI_DOUBLE, MPI_COMM_WORLD);

        double sum_speed = 0.0;
        for (int r = 0; r < size; r++) sum_speed += speeds[r];
        if (sum_speed <= 0.0) { for (int r = 0; r < size; r++) speeds[r] = 1.0; sum_speed = size; }

        double *frac = (double *)malloc(size * sizeof(double));
        int assigned = 0;
        for (int r = 0; r < size; r++) {
            /* حصة كل عملية المثالية = العدد الكلي × (سرعتها ÷ مجموع السرعات). نأخذ الجزء الصحيح ونحتفظ بالكسر. */
            double ideal = (double)num_vectors * speeds[r] / sum_speed;
            vec_counts[r] = (int)ideal;
            frac[r]       = ideal - (double)vec_counts[r];
            assigned     += vec_counts[r];
        }
        /* المتجهات المتبقية بسبب التقريب نعطيها للعمليات صاحبة أكبر كسر، متجهاً متجهاً، حتى يكتمل العدد الكلي بالضبط. */
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

/* نوع الصورة: غير معروف، رمادية، أو ملونة. */
typedef enum { MODE_UNKNOWN = 0, MODE_GRAY, MODE_COLOR } ImgMode;

/* اكتشاف نوع الصورة تلقائياً بعدّ الأرقام في الملف: 262144 رقم = رمادية، و786432 = ملونة (RGB). */
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

/* مسار الصورة الرمادية كاملاً (كل العمليات تشغّل هذه الدالة). الخطوات بالترتيب:
   1) rank 0 يقرأ الصورة ويبني المتجهات.  2) توزيع المتجهات (Scatterv).
   3) حساب متجه القاموس الأول (المتوسط).  4) LBG المتوازي.
   5) تجميع الأرقام عند rank 0 (Gatherv).  6) على rank 0: delta ثم Huffman ثم فك وإعادة بناء الصورة.
   7) حساب MSE وPSNR وSSIM وطباعة النتائج. */
static int run_gray_parallel(int argc, char *argv[], int rank, int size, const char *image_path)
{
    (void)argc; (void)argv;

    const int K    = CODEBOOK_SIZE;
    const int vlen = BLOCK_SIZE * BLOCK_SIZE;

    /* حجم الصورة الأصلية بالبايت (262144) — يُستخدم لحساب نسبة الضغط. */
    int original_image_bytes = WIDTH * HEIGHT;

    uint8_t *image       = NULL;
    uint8_t *training_set = NULL;
    int      num_vectors  = 0;

    MPI_Barrier(MPI_COMM_WORLD);
    /* نبدأ مؤقت الزمن الكلي (بعد مزامنة كل العمليات). */
    double t_total0 = MPI_Wtime();

    if (rank == 0) {
        /* فقط العملية 0 تقرأ ملف الصورة وتبني المتجهات (باقي العمليات تنتظر استلام حصتها). */
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

    /* العملية 0 تبلّغ كل العمليات بعدد المتجهات الكلي. */
    MPI_Bcast(&num_vectors, 1, MPI_INT, 0, MPI_COMM_WORLD);

    int *vec_counts  = (int *)calloc(size, sizeof(int));
    int *vec_displs  = (int *)malloc(size * sizeof(int));
    int *byte_counts = (int *)malloc(size * sizeof(int));
    int *byte_displs = (int *)malloc(size * sizeof(int));

    /* نحدد حصة كل عملية (Equal أو Adaptive). */
    compute_vector_distribution(num_vectors, vlen, rank, size,
                                 vec_counts, vec_displs, byte_counts, byte_displs);

    /* عدد المتجهات التي ستعالجها هذه العملية. */
    int local_n = vec_counts[rank];

    uint8_t *local_v = (uint8_t *)malloc((size_t)local_n * vlen);
    /* العملية 0 توزّع المتجهات: كل عملية تستلم حصتها في local_v. */
    MPI_Scatterv(training_set, byte_counts, byte_displs, MPI_UINT8_T,
                 local_v,      local_n * vlen,           MPI_UINT8_T,
                 0, MPI_COMM_WORLD);

    /* القاموس الابتدائي: متجه واحد = متوسط كل متجهات الصورة. كل عملية تجمع مجموع حصتها، ثم Allreduce يجمعها، ونقسم على العدد الكلي. */
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

    /* نحوّل متجهات الحصة من بايت إلى float لأن حسابات LBG تتم بالأعداد العشرية. */
    float *local_vf = (float *)malloc((size_t)local_n * vlen * sizeof(float));
    for (int i = 0; i < local_n * vlen; i++)
        local_vf[i] = (float)local_v[i];

    /* مصفوفة الأرقام (label) النهائية لكل البلوكات تُجمع عند العملية 0 فقط؛ وكل عملية تحتفظ بأرقام حصتها المحلية. */
    uint8_t *labels       = NULL;
    if (rank == 0) labels = (uint8_t *)calloc(num_vectors, sizeof(uint8_t));
    uint8_t *local_labels = (uint8_t *)calloc(local_n, sizeof(uint8_t));

    MPI_Barrier(MPI_COMM_WORLD);
    /* نقيس زمن LBG فقط: مزامنة (Barrier) ثم تشغيل LBG ثم مزامنة. هذا هو الزمن الذي نحسب منه التسريع. */
    double t0 = MPI_Wtime();
    /* تشغيل LBG المتوازي (الجزء الأثقل في البرنامج). */
    int lbg_iters = parallel_lbg(local_vf, local_n, num_vectors, vlen, K,
                 codebook_flat, local_labels, rank, size, 0);
    MPI_Barrier(MPI_COMM_WORLD);
    double t1 = MPI_Wtime();
    double time_lbg = t1 - t0;

    /* نجمع أرقام كل العمليات عند العملية 0 بترتيبها الأصلي. */
    MPI_Gatherv(local_labels, local_n,                MPI_UINT8_T,
                labels,       vec_counts, vec_displs, MPI_UINT8_T,
                0, MPI_COMM_WORLD);

    /* نسختان من الصورة (الأصلية والمعاد بناؤها) يحتاجهما كل المعالجات لحساب SSIM المتوازي. */
    uint8_t *ssim_a = (uint8_t *)malloc((size_t)WIDTH * HEIGHT);
    uint8_t *ssim_b = (uint8_t *)malloc((size_t)WIDTH * HEIGHT);

    uint8_t *codebook_data = NULL, *reconstructed_lbg = NULL, *labels_delta_u = NULL;
    uint8_t *reconstructed = NULL;
    int codebook_bytes = 0;

    if (rank == 0) {
        /* من هنا حتى الخلاصة: عمل العملية 0 وحدها: طباعة أول 10 متجهات من القاموس، وزمن LBG، وعدد التكرارات. */
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

        /* إنتروبي الأرقام قبل Delta (للمقارنة). */
        double H = compute_entropy(labels, num_vectors, K);
        printf("Entropy before Huffman = %.3f bits/symbol\n", H);

        /* نحوّل القاموس إلى بايتات (0..255) كما سيُخزن في الملف المضغوط: حجمه 64×16 = 1024 بايت. */
        codebook_data = malloc(K * vlen);
        for (int k = 0; k < K; k++)
            for (int i = 0; i < vlen; i++)
                codebook_data[k * vlen + i] = (uint8_t) roundf(codebook_flat[k * vlen + i]);
        printf("Codebook converted to uint8_t (size = %d bytes)\n", K * vlen);

        /* إعادة بناء الصورة من الأرقام مباشرة (بدون Huffman) لنحفظها في lbg_decompress.txt. */
        reconstructed_lbg = malloc(WIDTH * HEIGHT);
        decompress_image(reconstructed_lbg, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, labels);

        FILE *flbg = fopen("lbg_decompress.txt", "w");
        for (size_t i = 0; i < (size_t)(WIDTH*HEIGHT); i++)
            fprintf(flbg, "%u\n", reconstructed_lbg[i]);
        fclose(flbg);

        double td0 = MPI_Wtime();
        /* ترميز Delta: نخزن أول رقم كما هو، وبعده نخزن الفرق بين كل رقم والذي قبله (+128 حتى لا تظهر قيم سالبة).
           الأرقام المتجاورة تكون غالباً متقاربة، فتتكرر الفروق الصغيرة أكثر، وهذا يقلل الإنتروبي ويحسّن ضغط Huffman. */
        labels_delta_u = malloc(num_vectors);
        labels_delta_u[0] = labels[0];
        for (int i = 1; i < num_vectors; i++)
            labels_delta_u[i] = (uint8_t)(labels[i] - labels[i-1] + 128);

        /* إنتروبي الفروقات بعد Delta (أقل من قبل). */
        double H_delta = compute_entropy(labels_delta_u, num_vectors, 256);
        double td1 = MPI_Wtime();
        printf("[Delta Encode] Done in %.6f seconds\n", td1 - td0);
        printf("Entropy after Delta   = %.3f bits/symbol\n", H_delta);

        int huff_data_bytes = 0;
        int header_bytes    = 0;
        double t_huff0 = MPI_Wtime();
        /* ضغط الفروقات بترميز Huffman: ترجع الحجم الكلي (بيانات + جدول)، وحجم البيانات وحجم الجدول كلٌّ على حدة. */
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
        /* حساب نسب الضغط الثلاث:
           CR_huff_data  : أرقام الصورة ÷ بيانات Huffman فقط،  CR_huff_total : ÷ (بيانات + جدول)،
           CR_system     : حجم الصورة الأصلية ÷ (القاموس + بيانات Huffman + الجدول) = نسبة ضغط النظام (المعتمدة). */
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
        /* عدد البتات لكل بكسل (BPP) = 8 ÷ نسبة الضغط. */
        printf("\nBPP  = %.4f bits/pixel\n", 8.0 / CR_system);

        /* فك Delta: نعيد الأرقام الأصلية (الرقم الأول كما هو، وكل رقم = السابق + الفرق − 128). */
        labels[0] = labels_delta_u[0];
        for (int i = 1; i < num_vectors; i++)
            labels[i] = labels[i-1] + ((int)labels_delta_u[i] - 128);

        reconstructed = malloc(WIDTH * HEIGHT);
        /* نعيد بناء الصورة النهائية من الأرقام ومن القاموس. */
        decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, labels);

    }

    if (rank == 0) {
        /* نحفظ الصورة المعاد بناؤها كملف نصي، وكـ BMP (الأصلية والمعاد بناؤها) لنراها بالعين. */
        FILE *file1 = fopen("decompress.txt", "w");
        for (size_t i = 0; i < (size_t)(WIDTH*HEIGHT); i++)
            fprintf(file1, "%u\n", reconstructed[i]);
        fclose(file1);

        save_bmp_gray("original.bmp",   image,                  WIDTH, HEIGHT);
        save_bmp_gray("compressed.bmp", reconstructed, WIDTH, HEIGHT);
        printf("Saved: original.bmp  compressed.bmp\n");

        /* حساب جودة الصورة: MSE ثم PSNR. */
        double mse  = compute_mse(image, reconstructed, WIDTH*HEIGHT);
        double psnr = compute_psnr(image, reconstructed, WIDTH*HEIGHT);
        printf("MSE = %.2f\n", mse);
        printf("PSNR = %.2f dB\n", psnr);

        /* نسبة الضغط بالأرقام الثابتة (بايت واحد لكل بلوك، بدون Huffman): الأصلية ÷ (القاموس + الأرقام). هي ليست نسبة ضغط النظام. */
        int indexes_bytes = num_vectors;
        int original_bytes = WIDTH * HEIGHT;
        double CR = (double)original_bytes / (codebook_bytes + indexes_bytes);
        printf("Compression Ratio (CR): %.2f\n", CR);

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

    /* العملية 0 ترسل الصورتين لكل العمليات لتقسيم حساب SSIM بينها. */
    MPI_Bcast(ssim_a, WIDTH * HEIGHT, MPI_UINT8_T, 0, MPI_COMM_WORLD);
    MPI_Bcast(ssim_b, WIDTH * HEIGHT, MPI_UINT8_T, 0, MPI_COMM_WORLD);

    MPI_Barrier(MPI_COMM_WORLD);
    double sp0 = MPI_Wtime();
    /* حساب SSIM المتوازي (وقته لا يدخل في زمن LBG). */
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
        /* الزمن الكلي للبرنامج (من القراءة حتى النهاية). */
        printf("Total execution time: %.3f seconds\n", time_taken);
    }

    return 0;
}

/* هيكل لحفظ نتائج كل قناة لونية (أحمر/أخضر/أزرق): MSE وPSNR وSSIM وزمن LBG وحجم الضغط والصورة المعاد بناؤها. */
typedef struct {
    double mse, psnr, ssim;
    double lbg_time;
    int compressed_bytes;
    uint8_t *reconstructed;
} ChannelResult;

/* مسار الصورة الملونة: نفس خطوات الرمادية لكن ثلاث مرات (قناة R ثم G ثم B)،
   ثم نجمع النتائج: MSE وCR على القنوات الثلاث معاً، وSSIM = متوسط SSIM القنوات الثلاث. */
static int run_color_parallel(int argc, char *argv[], int rank, int size, const char *image_path)
{
    (void)argc; (void)argv;

    const int K    = CODEBOOK_SIZE;
    const int vlen = BLOCK_SIZE * BLOCK_SIZE;
    /* عدد المتجهات في كل قناة (16384). */
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

        /* العملية 0 تقرأ الصورة الملونة وتفصلها إلى ثلاث قنوات. */
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

    /* حصص العمليات تُحسب مرة واحدة وتُستعمل للقنوات الثلاث. */
    compute_vector_distribution(num_vectors, vlen, rank, size,
                                 vec_counts, vec_displs, byte_counts, byte_displs);

    int local_n = vec_counts[rank];

    uint8_t *ssim_a = (uint8_t *)malloc((size_t)channel_bytes);
    uint8_t *ssim_b = (uint8_t *)malloc((size_t)channel_bytes);

    ChannelResult results[3];
    memset(results, 0, sizeof(results));

    /* حلقة القنوات: نعالج كل قناة كصورة رمادية مستقلة (توزيع، LBG، Delta، Huffman، فك، جودة). */
    for (int ch = 0; ch < 3; ch++) {

        uint8_t *training_set = NULL;
        if (rank == 0) {
            /* بناء متجهات هذه القناة. */
            int nv = build_training_vectors(channels[ch], &training_set);
            if (nv != num_vectors) {
                fprintf(stderr, "Unexpected vector count for %s channel.\n", channel_names[ch]);
                MPI_Abort(MPI_COMM_WORLD, 1);
            }
        }

        uint8_t *local_v = (uint8_t *)malloc((size_t)local_n * vlen);
        /* توزيع متجهات هذه القناة على العمليات (نفس حصص الرمادي). */
        MPI_Scatterv(training_set, byte_counts, byte_displs, MPI_UINT8_T,
                     local_v,      local_n * vlen,           MPI_UINT8_T,
                     0, MPI_COMM_WORLD);

        /* القاموس الابتدائي لهذه القناة = متوسط متجهاتها (Allreduce يجمع حصص العمليات). */
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

        /* تحويل متجهات الحصة إلى float. */
        float *local_vf = (float *)malloc((size_t)local_n * vlen * sizeof(float));
        for (int i = 0; i < local_n * vlen; i++)
            local_vf[i] = (float)local_v[i];

        uint8_t *labels = NULL;
        if (rank == 0) labels = (uint8_t *)calloc(num_vectors, sizeof(uint8_t));
        uint8_t *local_labels = (uint8_t *)calloc(local_n, sizeof(uint8_t));

        MPI_Barrier(MPI_COMM_WORLD);
        /* نقيس زمن LBG لهذه القناة (بين مزامنتين). */
        double t0 = MPI_Wtime();
        /* تشغيل LBG المتوازي على هذه القناة. */
        int lbg_iters = parallel_lbg(local_vf, local_n, num_vectors, vlen, K,
                    codebook_flat, local_labels, rank, size, 0);
        MPI_Barrier(MPI_COMM_WORLD);
        double t1 = MPI_Wtime();
        double lbg_time = t1 - t0;

        /* تجميع أرقام هذه القناة عند العملية 0. */
        MPI_Gatherv(local_labels, local_n,                MPI_UINT8_T,
                    labels,       vec_counts, vec_displs, MPI_UINT8_T,
                    0, MPI_COMM_WORLD);

        uint8_t *labels_delta_u = NULL, *reconstructed = NULL;

        if (rank == 0) {
            printf("\n  [%s channel] LBG time=%.4fs  LBG iters=%d\n", channel_names[ch], lbg_time, lbg_iters);

            /* العملية 0: ترميز Delta لأرقام هذه القناة (نفس فكرة الرمادي)، ثم Huffman، ثم فك Delta وإعادة بناء القناة. */
            labels_delta_u = (uint8_t*)malloc(num_vectors);
            labels_delta_u[0] = labels[0];
            for (int i = 1; i < num_vectors; i++)
                labels_delta_u[i] = (uint8_t)(labels[i] - labels[i-1] + 128);

            int huff_data_bytes = 0, header_bytes = 0;
            /* ضغط Huffman لهذه القناة (نفس الدالة المستخدمة في الرمادي). */
            int huff_total = huffman_on_labels(labels_delta_u, num_vectors, 255,
                                               &huff_data_bytes, &header_bytes);
            (void)huff_data_bytes; (void)header_bytes;

            int codebook_bytes = K * vlen;
            /* حجم هذه القناة المضغوط = القاموس + (بيانات Huffman + الجدول). */
            results[ch].compressed_bytes = codebook_bytes + huff_total;
            results[ch].lbg_time = lbg_time;

            /* فك Delta لإعادة الأرقام الأصلية لهذه القناة. */
            labels[0] = labels_delta_u[0];
            for (int i = 1; i < num_vectors; i++)
                labels[i] = labels[i-1] + ((int)labels_delta_u[i] - 128);

            reconstructed = (uint8_t*)malloc(channel_bytes);
            /* إعادة بناء هذه القناة من الأرقام والقاموس. */
            decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, labels);

        }

        if (rank == 0) {

            /* جودة هذه القناة: MSE وPSNR (وبعدها SSIM بشكل متوازٍ). */
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

        /* نرسل نسختي القناة (الأصلية والمعاد بناؤها) لكل العمليات لحساب SSIM المتوازي. */
        MPI_Bcast(ssim_a, channel_bytes, MPI_UINT8_T, 0, MPI_COMM_WORLD);
        MPI_Bcast(ssim_b, channel_bytes, MPI_UINT8_T, 0, MPI_COMM_WORLD);

        MPI_Barrier(MPI_COMM_WORLD);
        double sp0 = MPI_Wtime();
        /* حساب SSIM لهذه القناة. */
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
        /* النتائج الإجمالية للصورة الملونة: MSE الكلي = متوسط MSE القنوات (بنفس العدد)، وPSNR منه،
           وCR = الحجم الأصلي لكل القنوات ÷ مجموع أحجامها المضغوطة، وSSIM = متوسط SSIM القنوات الثلاث. */
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

        /* نحفظ الصورة الأصلية والمعاد بناؤها بصيغة BMP. */
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

/* نقطة البداية. الأمر: ./lbg_par ملف_الصورة [--gray|--color]
   الخطوات: تهيئة MPI، معرفة رقم العملية وعدد العمليات، تحديد نوع الصورة (رمادي/ملون)، تشغيل المسار المناسب. */
int main(int argc, char *argv[])
{
    /* تهيئة MPI (يجب أن تكون أول استدعاء MPI). */
    MPI_Init(&argc, &argv);

    int rank, size;
    /* رقم هذه العملية (rank) وعدد كل العمليات (size). */
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    const char *image_path = (argc > 1) ? argv[1] : "img.txt";
    int mode_int = MODE_UNKNOWN;

    if (rank == 0) {
        ImgMode mode = MODE_UNKNOWN;
        /* العملية 0 تقرر نوع الصورة: من الوسيط (--gray أو --color) إن وُجد، وإلا بالاكتشاف التلقائي من عدد الأرقام. */
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

    /* نبلّغ كل العمليات بنوع الصورة؛ إذا كان غير معروف ننهي البرنامج. */
    MPI_Bcast(&mode_int, 1, MPI_INT, 0, MPI_COMM_WORLD);

    if (mode_int == MODE_UNKNOWN) {
        MPI_Finalize();
        return 1;
    }

    int rc;
    /* نشغّل المسار المناسب: الرمادي أو الملون، ثم ننهي MPI ونرجع رمز النتيجة. */
    if (mode_int == MODE_GRAY)
        rc = run_gray_parallel(argc, argv, rank, size, image_path);
    else
        rc = run_color_parallel(argc, argv, rank, size, image_path);

    MPI_Finalize();
    return rc;
}

