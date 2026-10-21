#!/usr/bin/env python3
"""يبني arabic_mpi.c من pam_v4_nofilter.c: الكود نفسه حرفياً، مع حذف كل التعليقات الإنكليزية وإضافة تعليقات عربية.
الاستخدام: python3 build_arabic_mpi.py pam_v4_nofilter.c arabic_mpi.c"""
import re, sys
from strip_check import strip_comments

src = open(sys.argv[1], encoding="utf-8").read()
code = strip_comments(src)
lines = [l.rstrip() for l in code.split("\n")]
# حذف الأسطر الفارغة المتكررة والبداية
clean = []
for l in lines:
    if not l.strip() and (not clean or not clean[-1].strip()):
        continue
    clean.append(l)
lines = clean

HEADER = r'''/*
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
'''

# (جزء من السطر، رقم التكرار، نص التعليق، 'before' أو 'eol')
A = []
def b(sub, nth, text): A.append((sub, nth, text, "before"))
def e(sub, nth, text): A.append((sub, nth, text, "eol"))

b("#define WIDTH 512", 1, """الثوابت الأساسية للبرنامج (لا تتغير أثناء التشغيل):
   WIDTH, HEIGHT : أبعاد الصورة 512×512 بكسل.
   BLOCK_SIZE    : طول ضلع البلوك (4×4 بكسل).
   DELTA         : عامل الانقسام في LBG (كل متجه ينقسم إلى متجهين (1+DELTA) و(1-DELTA)).
   EPSILON       : حد التوقف: نوقف التكرار عندما يصير التحسن النسبي أقل من هذا الرقم.
   CODEBOOK_SIZE : حجم القاموس النهائي (64 متجهاً).
   MAX_ITER      : أقصى عدد تكرارات لكل مرحلة انقسام.
   K1, K2        : ثوابت مقياس SSIM (0.01 و0.03).
   VLEN          : طول المتجه = 4×4 = 16 قيمة.""")

b("void save_bmp_gray(", 1, """حفظ صورة رمادية بصيغة BMP (8 بت لكل بكسل) لنتمكن من فتحها بأي برنامج عرض.
   المدخلات: اسم الملف، مصفوفة البكسلات، العرض، الارتفاع.""")
b("int row_padded = (width + 3) & ~3;", 1, "صيغة BMP تتطلب أن يكون طول كل صف من مضاعفات الـ 4 بايت، لذلك نضيف حشواً (padding) عند الحاجة.")
b("uint8_t header[54] = {0};", 1, "نبني رأس ملف BMP (54 بايت): نوع الملف 'BM'، حجم الملف، العرض، الارتفاع، وعدد البتات لكل بكسل.")
b("FILE *f = fopen(filename, \"wb\");", 1, "نفتح الملف للكتابة الثنائية؛ إذا فشل الفتح نطبع الخطأ ونخرج من الدالة.")
b("for (int i = 0; i < 256; i++) {", 1, "جدول الألوان (palette): 256 مستوى رمادي، كل مستوى يقابل (i,i,i) أي نفس القيمة للألوان الثلاثة.")
b("for (int y = height - 1; y >= 0; y--) {", 1, "BMP يخزن الصفوف من الأسفل إلى الأعلى، لذلك نكتب من آخر صف إلى الأول، ونضيف الحشو بعد كل صف.")

b("void save_bmp_color(", 1, "حفظ صورة ملونة بصيغة BMP (24 بت: 3 بايت لكل بكسل). نفس فكرة الدالة السابقة لكن بدون جدول ألوان.")
b("uint8_t pixel[3] = { B[idx], G[idx], R[idx] };", 1, "BMP يخزن ألوان البكسل بترتيب (أزرق، أخضر، أحمر) وليس (أحمر، أخضر، أزرق).")

b("int build_training_vectors(", 1, """تحويل الصورة إلى "متجهات تدريب": نقسم الصورة إلى بلوكات 4×4، وكل بلوك يصير متجهاً من 16 قيمة.
   عدد البلوكات = (512/4)×(512/4) = 16384 متجه. الدالة تُرجع عدد المتجهات.""")
b("*training_set = (uint8_t *)malloc(num_vectors * vector_length);", 1, "نحجز ذاكرة لكل المتجهات (16384 × 16 بايت).")
b("for (int y = 0; y < HEIGHT; y += BLOCK_SIZE) {", 1, "نمر على الصورة بلوكاً بلوكاً (من اليسار لليمين ومن الأعلى للأسفل)، وننسخ بكسلات كل بلوك إلى متجه.")
b("(*training_set)[idx * vector_length + vec_index] = image[img_index];", 1, "بكسل الصورة (الصف y+r، العمود x+c) يذهب إلى الموضع (r*4+c) داخل متجه البلوك.")

b("int read_image_from_txt(", 1, "قراءة صورة رمادية من ملف نصي (رقم لكل بكسل). تُرجع 1 إذا قرأت 512×512 بكسل كاملة.")
b("if (val < 0) val = 0;", 1, "نحصر القيمة بين 0 و255 (أي قيمة خارج المدى تُقصّ إلى الحد).")
b("int read_color_image_from_txt(", 1, "قراءة صورة ملونة من ملف نصي: كل بكسل ثلاثة أرقام (R G B). نخزنها في ثلاث مصفوفات منفصلة.")

b("static inline float distance16f(", 1, """مربع المسافة الإقليدية بين متجهين طول كل منهما 16.
   هذه الدالة هي أكثر دالة تُستدعى في البرنامج (تُستدعى ملايين المرات داخل LBG).""")

b("static double calibrate_speed(void)", 1, """قياس سرعة هذه العملية (rank) بتجربة قصيرة تحاكي عمل LBG، وتُرجع "عدد المقارنات في الثانية".
   تُستخدم فقط في التوزيع Adaptive: العملية الأسرع (نواة P) تأخذ متجهات أكثر من الأبطأ (نواة E).""")
b("for (int i = 0; i < NV * CVLEN; i++)", 1, "نملأ بيانات تجريبية ثابتة (أرقام شبه عشوائية لكن متطابقة في كل مرة).")
b("enum { TRIALS = 3 };", 1, "نكرر القياس 3 مرات: المرة الأولى للتسخين (تُهمل)، ونأخذ أسرع زمن من الباقي حتى لا تتأثر النتيجة بتأخير عابر.")
b("if (trial > 0 && t < dt) dt = t;", 1, "نحتفظ بأقل زمن (أسرع محاولة) بعد تجاهل محاولة التسخين الأولى.")
b("return (double)REP * (double)NV * (double)NC / dt;", 1, "السرعة = عدد المقارنات المنفذة ÷ الزمن.")

b("int parallel_lbg(", 1, """خوارزمية LBG المتوازية: تبني القاموس (codebook) من المتجهات الموزعة على العمليات.
   المدخلات: local_vf (متجهات هذه العملية فقط)، local_n (عددها)، num_vectors (العدد الكلي)،
   K (حجم القاموس المطلوب)، codebook (القاموس: يبدأ بمتجه واحد ويكبر)،
   local_labels (رقم أقرب متجه لكل متجه محلي)، rank (رقم العملية)، size (عدد العمليات).
   المخرج: مجموع عدد تكرارات Lloyd في كل مراحل الانقسام (متساوٍ في كل العمليات).""")
b("int buf_capacity = K * VLEN + K + 1;", 1, """مخزن مؤقت واحد يحمل ثلاثة أشياء لكل مرحلة: (1) مجاميع القيم لكل متجه في القاموس،
   (2) عدد المتجهات في كل عنقود، (3) مجموع التشويه. نجمعها كلها بعملية MPI_Allreduce واحدة.
   نستخدم double لأن مجاميع القيم الصحيحة تكون دقيقة تماماً ولا تعتمد على ترتيب الجمع، فتخرج
   نتيجة LBG ونفس عدد التكرارات بغض النظر عن عدد العمليات.""")
b("while (k < K) {", 1, "حلقة المراحل: نبدأ بمتجه واحد (k=1) ونضاعف k في كل مرحلة (1→2→4→…→64).")
b("for (int i = k - 1; i >= 0; i--)", 1, "خطوة الانقسام: كل متجه في القاموس ينقسم إلى متجهين متقاربين: (1+DELTA)×المتجه و(1−DELTA)×المتجه.")
b("k = (k * 2 > K) ? K : k * 2;", 1, "نضاعف عدد المتجهات في القاموس (ولا نتجاوز K).")
b("const int sum_off  = 0;", 1, "تحديد مواضع الأقسام الثلاثة داخل المخزن المؤقت: المجاميع، ثم العدادات، ثم مجموع التشويه.")
b("do {", 1, "حلقة تكرار Lloyd: (تعيين المتجهات لأقرب متجه قاموس) ثم (تحديث القاموس) حتى يستقر التشويه.")
b("memset(buf, 0, active * sizeof(double));", 1, "نصفّر المخزن المؤقت قبل كل تكرار.")
b("for (int i = 0; i < local_n; i++) {", 1, "الخطوة (أ) التعيين: كل عملية تمر على متجهاتها المحلية فقط (وهذا هو الجزء المتوازي).")
b("for (int c = 0; c < k; c++) {", 1, "نبحث عن أقرب متجه في القاموس (أصغر مسافة) للمتجه الحالي.")
b("local_labels[i]    = (uint8_t)bi;", 1, "نسجل رقم أقرب متجه، ونضيف مسافته للتشويه، ونزيد عداد ذلك العنقود، ونجمع قيم المتجه إلى مجموع عنقوده.")
b("MPI_Allreduce(MPI_IN_PLACE, buf, active,", 1, """الخطوة (ب) الجمع: كل العمليات تجمع مخازنها الجزئية، فتحصل كل عملية على المجاميع الكلية لكل الصورة.
   هذه هي نقطة التواصل الوحيدة في كل تكرار.""")
b("double global_dist = buf[dist_off] / (double)num_vectors;", 1, "متوسط التشويه الكلي لكل الصورة (نفس القيمة في كل العمليات).")
b("for (int c = 0; c < k; c++) {", 2, "الخطوة (ج) التحديث: كل متجه قاموس يصير متوسط المتجهات المنتمية لعنقوده (المجموع ÷ العدد).")
b("improvement = fabs(prev_dist - global_dist) / (global_dist + 1e-9);", 1, "نحسب التحسن النسبي في التشويه مقارنة بالتكرار السابق؛ إذا صار صغيراً (أقل من EPSILON) نتوقف.")
b("} while (iter < MAX_ITER && improvement > (double)EPSILON);", 1, "شرط الاستمرار: لم نصل لأقصى عدد تكرارات، وما زال التحسن أكبر من EPSILON.")
b("total_iters += iter;", 1, "نضيف عدد تكرارات هذه المرحلة للمجموع الكلي.")

b("void decompress_image(", 1, """إعادة بناء الصورة: لكل بلوك نأخذ رقمه (label) ونجلب متجه القاموس المقابل له
   (16 قيمة) ونضعها في مكان البلوك بالصورة. هذه هي خطوة "فك الضغط" في VQ.""")
b("int code_idx = labels[vec_idx];", 1, "رقم متجه القاموس الخاص بهذا البلوك.")
b("reconstructed[img_idx] =", 1, "نقرّب قيمة القاموس إلى أقرب عدد صحيح (0..255) ونضعها في مكانها بالصورة.")

b("double compute_mse(", 1, "متوسط مربع الخطأ MSE بين الصورة الأصلية والمعاد بناؤها (كلما قل كانت الجودة أعلى).")
b("double compute_psnr(", 1, "نسبة الإشارة إلى الضجيج PSNR بالديسيبل: 10·log10(255² / MSE). كلما زادت كانت الجودة أعلى.")
b("double compute_entropy(", 1, "الإنتروبي (بالبت لكل رمز): الحد النظري الأدنى لعدد البتات اللازمة لتمثيل كل رقم، بحسب تكرارات الأرقام.")

b("typedef struct HuffNode {", 1, "ترميز Huffman: نبني شجرة تعطي الأرقام الكثيرة التكرار رمزاً قصيراً والنادرة رمزاً طويلاً. هذا هيكل عقدة الشجرة.")
b("static MinHeap *heap_create(", 1, "أدوات الكومة الصغرى (min-heap): تُستخدم لاختيار العقدتين الأقل تكراراً بسرعة أثناء بناء الشجرة.")
b("static HuffNode *huff_build_tree(", 1, "بناء شجرة Huffman: ندمج في كل مرة أقل عقدتين تكراراً في عقدة أب (مجموع تكراريهما) حتى تبقى عقدة واحدة هي الجذر.")
b("static void huff_build_codes_rec(", 1, "استخراج رمز كل قيمة من الشجرة: الذهاب يساراً يضيف البت 0، ويميناً يضيف البت 1.")
b("static uint8_t *huff_encode(", 1, "الترميز: نستبدل كل رقم برمزه (بتات) ونرصّ كل البتات في بايتات متتالية. تُرجع البيانات المرمّزة وحجمها.")
b("current |= (uint8_t)(bit << (7 - bit_pos));", 1, "نضع البت في موضعه داخل البايت الحالي (من اليسار)، وعند اكتمال 8 بتات نخزن البايت ونبدأ بايتاً جديداً.")
b("static void huff_decode(", 1, "فك الترميز: نقرأ البتات واحداً واحداً ونمشي في الشجرة (0 يسار، 1 يمين) حتى نصل لورقة فنكتب قيمتها ونرجع للجذر.")
b("int huffman_on_labels(", 1, """ضغط سلسلة الأرقام بترميز Huffman وفحص صحة الفك. تُرجع الحجم الكلي (بيانات + جدول).
   الخطوات: (1) عدّ تكرار كل رقم، (2) بناء الشجرة والرموز، (3) الترميز، (4) حساب حجم الجدول،
   (5) الفك ومقارنته بالأصل للتأكد أنه مطابق تماماً (lossless).""")
b("int header_bytes = used_symbols * sizeof(uint32_t);", 1, """حجم جدول Huffman: نحسبه 4 بايت لكل رمز مستخدم (تكرار الرمز فقط).
   هذه اتفاقية حساب: البرنامج لا يكتب ملفاً مضغوطاً حقيقياً. ملف حقيقي قد يحتاج بايتاً إضافياً
   لكل رمز (لمعرفة هوية الرمز) وبعض المعلومات العامة، وهذا يغيّر نسبة الضغط بحدود 1% تقريباً.""")
b("huff_decode(enc, enc_bytes, root, num_labels, decoded);", 1, "نفك البيانات المرمّزة باستخدام الشجرة الموجودة في الذاكرة.")
b("int ok = 1;", 1, "فحص الصحة: كل رقم بعد الفك يجب أن يساوي الرقم الأصلي؛ وإلا نطبع ERROR.")

b("static const double (*ssim_gaussian_window(void))[11]", 1, "نافذة غاوس 11×11 (σ=1.5) المستخدمة في SSIM؛ نحسبها مرة واحدة ونطبّعها بحيث مجموع أوزانها = 1.")
b("double SSIM_window_based_parallel(", 1, """حساب مقياس SSIM (التشابه البنيوي) بين الصورتين بشكل متوازٍ: نقسم صفوف الصورة على العمليات،
   كل عملية تحسب SSIM لصفوفها، ثم نجمع النتائج بـ MPI_Allreduce ونأخذ المتوسط.""")
b("const int i_start = 5;", 1, "النافذة 11×11 تحتاج 5 بكسلات من كل جانب، لذلك نحسب فقط البكسلات البعيدة 5 عن الحافة. هنا نقسم الصفوف بين العمليات.")
b("double mu_x = 0, mu_y = 0;", 1, "لكل بكسل: نحسب المتوسط الموزون (mu) في النافذة للصورتين، ثم التباين والتباين المشترك.")
b("double C1 = (K1 * 255) * (K1 * 255);", 1, "ثوابت صغيرة لتجنب القسمة على صفر، ثم نحسب SSIM لهذا الموضع = (بسط) ÷ (مقام) حسب صيغة SSIM المعروفة.")
b("MPI_Allreduce(&local_total, &global_total, 1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);", 1, "نجمع المجموع والعدد من كل العمليات، ثم متوسط SSIM = المجموع ÷ العدد.")

b("static void compute_vector_distribution(", 1, """توزيع المتجهات على العمليات (من يأخذ كم متجهاً؟). المخرجات:
   vec_counts/vec_displs : عدد المتجهات وبدايتها لكل عملية، byte_counts/byte_displs : نفسها بالبايت.
   استراتيجيتان: Equal (متساوٍ) و Adaptive (حسب سرعة كل عملية).""")
b("const char *strategy_env = getenv(\"VQ_STRATEGY\");", 1, "نقرأ متغير البيئة VQ_STRATEGY: equal أو adaptive. بدونه: متساوٍ إذا عدد العمليات ≤ 4، وإلا Adaptive.")
b("if (use_equal_split) {", 1, "التوزيع المتساوي: كل عملية تأخذ N/P متجه (والباقي يوزع على الأوائل بمتجه إضافي).")
b("double my_speed = calibrate_speed();", 1, "التوزيع Adaptive: كل عملية تقيس سرعتها، ثم تتبادل كل العمليات السرعات (Allgather).")
b("double ideal = (double)num_vectors * speeds[r] / sum_speed;", 1, "حصة كل عملية المثالية = العدد الكلي × (سرعتها ÷ مجموع السرعات). نأخذ الجزء الصحيح ونحتفظ بالكسر.")
b("int rem = num_vectors - assigned;", 1, "المتجهات المتبقية بسبب التقريب نعطيها للعمليات صاحبة أكبر كسر، متجهاً متجهاً، حتى يكتمل العدد الكلي بالضبط.")

b("typedef enum { MODE_UNKNOWN = 0, MODE_GRAY, MODE_COLOR } ImgMode;", 1, "نوع الصورة: غير معروف، رمادية، أو ملونة.")
b("static ImgMode detect_mode_from_file(", 1, "اكتشاف نوع الصورة تلقائياً بعدّ الأرقام في الملف: 262144 رقم = رمادية، و786432 = ملونة (RGB).")

b("static int run_gray_parallel(", 1, """مسار الصورة الرمادية كاملاً (كل العمليات تشغّل هذه الدالة). الخطوات بالترتيب:
   1) rank 0 يقرأ الصورة ويبني المتجهات.  2) توزيع المتجهات (Scatterv).
   3) حساب متجه القاموس الأول (المتوسط).  4) LBG المتوازي.
   5) تجميع الأرقام عند rank 0 (Gatherv).  6) على rank 0: delta ثم Huffman ثم فك وإعادة بناء الصورة.
   7) حساب MSE وPSNR وSSIM وطباعة النتائج.""")
b("int original_image_bytes = WIDTH * HEIGHT;", 1, "حجم الصورة الأصلية بالبايت (262144) — يُستخدم لحساب نسبة الضغط.")
b("double t_total0 = MPI_Wtime();", 1, "نبدأ مؤقت الزمن الكلي (بعد مزامنة كل العمليات).")
b("image = (uint8_t *)malloc(WIDTH * HEIGHT);", 1, "فقط العملية 0 تقرأ ملف الصورة وتبني المتجهات (باقي العمليات تنتظر استلام حصتها).")
b("MPI_Bcast(&num_vectors, 1, MPI_INT, 0, MPI_COMM_WORLD);", 1, "العملية 0 تبلّغ كل العمليات بعدد المتجهات الكلي.")
b("compute_vector_distribution(num_vectors, vlen, rank, size,", 1, "نحدد حصة كل عملية (Equal أو Adaptive).")
b("int local_n = vec_counts[rank];", 1, "عدد المتجهات التي ستعالجها هذه العملية.")
b("MPI_Scatterv(training_set, byte_counts, byte_displs, MPI_UINT8_T,", 1, "العملية 0 توزّع المتجهات: كل عملية تستلم حصتها في local_v.")
b("float *codebook_flat = (float *)calloc(K * vlen, sizeof(float));", 1, "القاموس الابتدائي: متجه واحد = متوسط كل متجهات الصورة. كل عملية تجمع مجموع حصتها، ثم Allreduce يجمعها، ونقسم على العدد الكلي.")
b("float *local_vf = (float *)malloc((size_t)local_n * vlen * sizeof(float));", 1, "نحوّل متجهات الحصة من بايت إلى float لأن حسابات LBG تتم بالأعداد العشرية.")
b("uint8_t *labels       = NULL;", 1, "مصفوفة الأرقام (label) النهائية لكل البلوكات تُجمع عند العملية 0 فقط؛ وكل عملية تحتفظ بأرقام حصتها المحلية.")
b("double t0 = MPI_Wtime();", 2, "نقيس زمن LBG فقط: مزامنة (Barrier) ثم تشغيل LBG ثم مزامنة. هذا هو الزمن الذي نحسب منه التسريع.")
b("int lbg_iters = parallel_lbg(local_vf, local_n, num_vectors, vlen, K,", 1, "تشغيل LBG المتوازي (الجزء الأثقل في البرنامج).")
b("MPI_Gatherv(local_labels, local_n,", 1, "نجمع أرقام كل العمليات عند العملية 0 بترتيبها الأصلي.")
b("uint8_t *ssim_a = (uint8_t *)malloc((size_t)WIDTH * HEIGHT);", 1, "نسختان من الصورة (الأصلية والمعاد بناؤها) يحتاجهما كل المعالجات لحساب SSIM المتوازي.")
b("printf(\"\\nFinal codebook (%d codewords):\\n\", K);", 1, "من هنا حتى الخلاصة: عمل العملية 0 وحدها: طباعة أول 10 متجهات من القاموس، وزمن LBG، وعدد التكرارات.")
b("double H = compute_entropy(labels, num_vectors, K);", 1, "إنتروبي الأرقام قبل Delta (للمقارنة).")
b("codebook_data = malloc(K * vlen);", 1, "نحوّل القاموس إلى بايتات (0..255) كما سيُخزن في الملف المضغوط: حجمه 64×16 = 1024 بايت.")
b("reconstructed_lbg = malloc(WIDTH * HEIGHT);", 1, "إعادة بناء الصورة من الأرقام مباشرة (بدون Huffman) لنحفظها في lbg_decompress.txt.")
b("labels_delta_u = malloc(num_vectors);", 1, """ترميز Delta: نخزن أول رقم كما هو، وبعده نخزن الفرق بين كل رقم والذي قبله (+128 حتى لا تظهر قيم سالبة).
   الأرقام المتجاورة تكون غالباً متقاربة، فتتكرر الفروق الصغيرة أكثر، وهذا يقلل الإنتروبي ويحسّن ضغط Huffman.""")
b("double H_delta = compute_entropy(labels_delta_u, num_vectors, 256);", 1, "إنتروبي الفروقات بعد Delta (أقل من قبل).")
b("int huff_total = huffman_on_labels(labels_delta_u, num_vectors, 255,", 1, "ضغط الفروقات بترميز Huffman: ترجع الحجم الكلي (بيانات + جدول)، وحجم البيانات وحجم الجدول كلٌّ على حدة.")
b("double CR_huff_data  = (huff_data_bytes > 0)", 1, """حساب نسب الضغط الثلاث:
   CR_huff_data  : أرقام الصورة ÷ بيانات Huffman فقط،  CR_huff_total : ÷ (بيانات + جدول)،
   CR_system     : حجم الصورة الأصلية ÷ (القاموس + بيانات Huffman + الجدول) = نسبة ضغط النظام (المعتمدة).""")
b("printf(\"\\nBPP  = %.4f bits/pixel\\n\", 8.0 / CR_system);", 1, "عدد البتات لكل بكسل (BPP) = 8 ÷ نسبة الضغط.")
b("labels[0] = labels_delta_u[0];", 1, "فك Delta: نعيد الأرقام الأصلية (الرقم الأول كما هو، وكل رقم = السابق + الفرق − 128).")
b("decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, labels);", 1, "نعيد بناء الصورة النهائية من الأرقام ومن القاموس.")
b("FILE *file1 = fopen(\"decompress.txt\", \"w\");", 1, "نحفظ الصورة المعاد بناؤها كملف نصي، وكـ BMP (الأصلية والمعاد بناؤها) لنراها بالعين.")
b("double mse  = compute_mse(image, reconstructed, WIDTH*HEIGHT);", 1, "حساب جودة الصورة: MSE ثم PSNR.")
b("int indexes_bytes = num_vectors;", 1, "نسبة الضغط بالأرقام الثابتة (بايت واحد لكل بلوك، بدون Huffman): الأصلية ÷ (القاموس + الأرقام). هي ليست نسبة ضغط النظام.")
b("MPI_Bcast(ssim_a, WIDTH * HEIGHT, MPI_UINT8_T, 0, MPI_COMM_WORLD);", 1, "العملية 0 ترسل الصورتين لكل العمليات لتقسيم حساب SSIM بينها.")
b("double ssim_par_val = SSIM_window_based_parallel(", 1, "حساب SSIM المتوازي (وقته لا يدخل في زمن LBG).")
b("printf(\"Total execution time: %.3f seconds\\n\", time_taken);", 1, "الزمن الكلي للبرنامج (من القراءة حتى النهاية).")

b("==typedef struct {", 1, "هيكل لحفظ نتائج كل قناة لونية (أحمر/أخضر/أزرق): MSE وPSNR وSSIM وزمن LBG وحجم الضغط والصورة المعاد بناؤها.")
b("static int run_color_parallel(", 1, """مسار الصورة الملونة: نفس خطوات الرمادية لكن ثلاث مرات (قناة R ثم G ثم B)،
   ثم نجمع النتائج: MSE وCR على القنوات الثلاث معاً، وSSIM = متوسط SSIM القنوات الثلاث.""")
b("const int num_vectors = (WIDTH / BLOCK_SIZE) * (HEIGHT / BLOCK_SIZE);", 1, "عدد المتجهات في كل قناة (16384).")
b("if (!read_color_image_from_txt(image_path, R, G, B, WIDTH, HEIGHT)) {", 1, "العملية 0 تقرأ الصورة الملونة وتفصلها إلى ثلاث قنوات.")
b("compute_vector_distribution(num_vectors, vlen, rank, size,", 2, "حصص العمليات تُحسب مرة واحدة وتُستعمل للقنوات الثلاث.")
b("for (int ch = 0; ch < 3; ch++) {", 1, "حلقة القنوات: نعالج كل قناة كصورة رمادية مستقلة (توزيع، LBG، Delta، Huffman، فك، جودة).")
b("int nv = build_training_vectors(channels[ch], &training_set);", 1, "بناء متجهات هذه القناة.")
b("results[ch].compressed_bytes = codebook_bytes + huff_total;", 1, "حجم هذه القناة المضغوط = القاموس + (بيانات Huffman + الجدول).")
b("results[ch].mse  = compute_mse(channels[ch], reconstructed, channel_bytes);", 1, "جودة هذه القناة: MSE وPSNR (وبعدها SSIM بشكل متوازٍ).")
b("double rgb_mse = (results[0].mse * channel_bytes +", 1, """النتائج الإجمالية للصورة الملونة: MSE الكلي = متوسط MSE القنوات (بنفس العدد)، وPSNR منه،
   وCR = الحجم الأصلي لكل القنوات ÷ مجموع أحجامها المضغوطة، وSSIM = متوسط SSIM القنوات الثلاث.""")
b("save_bmp_color(\"original_color.bmp\", R, G, B, WIDTH, HEIGHT);", 1, "نحفظ الصورة الأصلية والمعاد بناؤها بصيغة BMP.")

b("int main(int argc, char *argv[])", 1, """نقطة البداية. الأمر: ./lbg_par ملف_الصورة [--gray|--color]
   الخطوات: تهيئة MPI، معرفة رقم العملية وعدد العمليات، تحديد نوع الصورة (رمادي/ملون)، تشغيل المسار المناسب.""")
b("MPI_Init(&argc, &argv);", 1, "تهيئة MPI (يجب أن تكون أول استدعاء MPI).")
b("MPI_Comm_rank(MPI_COMM_WORLD, &rank);", 1, "رقم هذه العملية (rank) وعدد كل العمليات (size).")
b("if (argc > 2) {", 1, "العملية 0 تقرر نوع الصورة: من الوسيط (--gray أو --color) إن وُجد، وإلا بالاكتشاف التلقائي من عدد الأرقام.")
b("MPI_Bcast(&mode_int, 1, MPI_INT, 0, MPI_COMM_WORLD);", 1, "نبلّغ كل العمليات بنوع الصورة؛ إذا كان غير معروف ننهي البرنامج.")
b("if (mode_int == MODE_GRAY)", 1, "نشغّل المسار المناسب: الرمادي أو الملون، ثم ننهي MPI ونرجع رمز النتيجة.")


# ----- مسار الملون: شرح الخطوات داخل حلقة القنوات -----
b("MPI_Scatterv(training_set, byte_counts, byte_displs, MPI_UINT8_T,", 2, "توزيع متجهات هذه القناة على العمليات (نفس حصص الرمادي).")
b("float *codebook_flat = (float *)calloc((size_t)K * vlen, sizeof(float));", 1, "القاموس الابتدائي لهذه القناة = متوسط متجهاتها (Allreduce يجمع حصص العمليات).")
b("float *local_vf = (float *)malloc((size_t)local_n * vlen * sizeof(float));", 2, "تحويل متجهات الحصة إلى float.")
b("double t0 = MPI_Wtime();", 3, "نقيس زمن LBG لهذه القناة (بين مزامنتين).")
b("int lbg_iters = parallel_lbg(local_vf, local_n, num_vectors, vlen, K,", 2, "تشغيل LBG المتوازي على هذه القناة.")
b("MPI_Gatherv(local_labels, local_n,", 2, "تجميع أرقام هذه القناة عند العملية 0.")
b("labels_delta_u = (uint8_t*)malloc(num_vectors);", 1, "العملية 0: ترميز Delta لأرقام هذه القناة (نفس فكرة الرمادي)، ثم Huffman، ثم فك Delta وإعادة بناء القناة.")
b("int huff_total = huffman_on_labels(labels_delta_u, num_vectors, 255,", 2, "ضغط Huffman لهذه القناة (نفس الدالة المستخدمة في الرمادي).")
b("labels[0] = labels_delta_u[0];", 2, "فك Delta لإعادة الأرقام الأصلية لهذه القناة.")
b("decompress_image(reconstructed, WIDTH, HEIGHT, BLOCK_SIZE, codebook_flat, labels);", 2, "إعادة بناء هذه القناة من الأرقام والقاموس.")
b("MPI_Bcast(ssim_a, channel_bytes, MPI_UINT8_T, 0, MPI_COMM_WORLD);", 1, "نرسل نسختي القناة (الأصلية والمعاد بناؤها) لكل العمليات لحساب SSIM المتوازي.")
b("double ssim_val = SSIM_window_based_parallel(", 1, "حساب SSIM لهذه القناة.")
b("typedef struct { uint64_t bits; int length; } HuffCode;", 1, "HuffCode: رمز Huffman لقيمة معينة = البتات وعددها.")

# ---------------- التنفيذ ----------------
def find_line(sub, nth):
    cnt = 0
    for i, l in enumerate(lines):
        if (l.strip() == sub[2:]) if sub.startswith("==") else (sub in l):
            cnt += 1
            if cnt == nth:
                return i
    raise SystemExit("لم أجد: %r (المرة %d)" % (sub, nth))

ins = {}   # index -> list of comments (before)
for sub, nth, text, kind in A:
    i = find_line(sub, nth)
    ins.setdefault(i, []).append((kind, text))

out = []
for i, l in enumerate(lines):
    indent = re.match(r"\s*", l).group(0)
    for kind, text in ins.get(i, []):
        if kind == "before":
            tl = text.split("\n")
            if len(tl) == 1:
                out.append(indent + "/* " + tl[0] + " */")
            else:
                out.append(indent + "/* " + tl[0])
                for t in tl[1:]:
                    out.append(indent + "   " + t.strip())
                out[-1] += " */"
    out.append(l)

body = "\n".join(out) + "\n"
open(sys.argv[2], "w", encoding="utf-8").write(HEADER + "\n" + body)
print("تم:", sys.argv[2], "| تعليقات:", len(A))
