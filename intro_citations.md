# خريطة الاستشهادات للمقدمة 1.1 (الفقرات 2 إلى 7), النسخة 2

النص لم يُغيَّر. الأرقام هي أرقام قائمتج الحالية (تُعاد ترقيمتها حسب أول ظهور في النهاية).

مفتاح الحالة:
- **متحقق**: قرأت نص الـPDF ووجدت الادعاء (مع رقم الصفحة).
- **ملاحظاتج**: مدعوم بملاحظاتج فقط (غير متحقق من PDF المصدر).
- **ملخص**: مدعوم بملخص الورقة فقط.
- **غير متحقق**: لا أملك سنداً.

## ما تحققت منه من PDF [4] Bilal و[5] Severo

**[4] Bilal, Ullah, Mujahid, Fouzder, J. Imaging 2024, 10(5), 124**
- العنوان والمؤلفون يطابقون قائمة المراجع. (جدول Word عندج غلط: "Pre-Scaling" و"Mahmood" و"Faisal").
- ص 1 (الملخص): الخوارزمية تحسّن LBG "by reducing the total number of comparisons among the codebook and training vectors using a match function"، والـrescaling بالـbilinear interpolation (nearest neighborhood) لتقليل المقارنة؛ "reduces the computational complexity by 50.2% compared to LBG"، وتقليل الذاكرة 20%.
- ص 7 و11: يستخدم SSIM (جدول المقارنة بملفج "SSIM غير مستخدم" غلط). ص 9: يستخدم BPP وMSE وPSNR.
- ص 15: متوسط الزمن لحجم codebook = 16 عند 0.25 bpp: LBG = 9.07 s و FLBG = 4.02 s (تحسّن 55.65%).
- لا يذكر CR كنتيجة (ملاحظة "غير محسوب" صحيحة، والرقم 16 مشتق من bpp).
- ص 8: Intel Core i5-3210M وMATLAB R2019a وصور رمادية 512×512. لا ذكر لأي تنفيذ متوازٍ (بحث نصي).
- ص 13: "Increasing the codebook size enhances the image quality but also increases the total number of comparisons among codewords and training vectors, resulting in longer computation times".

**[5] Severo, Ferreira, Spencer, Nascimento, Madeiro, Sensors 2024, 24, 2606**
- ص 1: LBG "is the most popular VQ codebook design algorithm"؛ تهيئة LBG "directly influences VQ performance, as the convergence speed and codebook quality depend on the initial codebook"؛ العمل "evaluates the impacts of initialization strategies on swarm intelligence algorithms for codebook design" بجودة الصور المعاد بناؤها وسرعة التقارب (عدد التكرارات).
- ص 3: "the LBG algorithm stands out for being the most popular".
- ص 3 و4 (القسم 2.1): وصف LBG كخوارزمية تجميع تتحسن تكرارياً (تقسيم Voronoi بأقرب codevector، حساب التشويه، شرط توقف بنسبة تغيّر التشويه ≤ ε، تحديث المراكز). هذا يطابق كودج (شرط التوقف `|D_prev − D| / D ≤ ε`).
- لا ذكر لأي تنفيذ متوازٍ.

## الفقرة 2

| الجملة | الاستشهاد | الأساس | الحالة |
|---|---|---|---|
| transform-based methods such as DWT | [3] Ranjan | ملاحظاتج: PCA + 2D-DWT | ملاحظاتج |
| VQ is a lossy technique ... codebook | [21] Sayood | لم أقرأ الكتاب | غير متحقق |
| LBG is a widely used method for generating VQ codebooks | [5] (ص 1 و3: "most popular")، [4] (ص 1: "renowned") | | **متحقق** |
| iterative clustering: assign to nearest codeword, update codewords | [5] القسم 2.1 (ص 3 إلى 4) | | **متحقق** |
| the codebook influences distortion and quality | [4], [5] | [5] ص 1: تصميم الـcodebook ذو أهمية كبيرة لجودة الإشارات المكمّمة | **متحقق** |

## الفقرة 3

| الجملة | الاستشهاد | الأساس | الحالة |
|---|---|---|---|
| LBG training requires repeated distance calculations ... costly | [4] | ص 1 و13: خفض المقارنات بين الـcodebook ومتجهات التدريب يقلل التعقيد؛ زيادة حجم الـcodebook تزيد المقارنات والزمن | **متحقق** |
| execution time influenced by number of vectors, codebook size, convergence | [4] لحجم الـcodebook (ص 13)؛ [5] للتقارب (ص 1: سرعة التقارب تعتمد على التهيئة) | عدد متجهات التدريب: لا سند صريح | حجم الـcodebook والتقارب **متحقق**؛ عدد المتجهات غير متحقق |
| Bilal et al. [4] ... fast LBG based on rescaling to reduce the number of comparisons | [4] | ص 1 | **متحقق** (النص صحيح كما هو) |
| Severo et al. [5] ... initialization | [5] | ص 1. ملاحظة: الدراسة عن التهيئة **لخوارزميات swarm intelligence** | **متحقق** (يمكن إضافة "swarm-intelligence-based" للدقة) |

## الفقرة 4

| الجملة | الاستشهاد | الأساس | الحالة |
|---|---|---|---|
| Parallel computing ... reduce execution time | [26] Pousa | ص 111 | متحقق |
| MPI provides communication operations | [74] MPI Forum | | غير متحقق |
| Hu et al. [6] applied MPI ... | [6] | | غير متحقق (الأخطر) |

## الفقرة 5

| الجملة | الاستشهاد | الأساس | الحالة |
|---|---|---|---|
| Heterogeneous multicore: P-cores and E-cores | لا مصدر | | غير متحقق |
| Velugoti et al. [7] | [7] | ملخص | ملخص |
| communication overhead can reduce parallel efficiency | [31] Schryen | ص 4 | متحقق (للكلفة فقط) |
| Fernández-Fraga et al. [8] | [8] | ملخص | ملخص |

## الفقرة 6 (الجدة)

[4] و[5]: لا يتناولان التنفيذ المتوازي (بحث نصي بالـPDFين)، فيدعمان أنهما لا يعالجان توزيع العمل. الجملة كاملة تعتمد على القسم 1.5 (لم أره) ويجب أن يغطي الأعمال المتوازية القريبة، منها [71] Manohar و[11] Zangana.

## الفقرة 7

| الجملة | الاستشهاد | الأساس | الحالة |
|---|---|---|---|
| LBG vector quantization | [5] القسم 2.1، (و[21]) | | [5] متحقق |
| delta coding | [34] Zhu، [21]، وربما [19] Lin | [34]: متحقق (معادلتا 3 و8). [19]: ملاحظاتج "Difference/XOR على جدول المؤشرات" | [34] متحقق؛ [19] ملاحظاتج |
| Huffman coding (**لا canonical**) | [21] (+ Huffman 1952 غير موجود) | | غير متحقق |
| collective communication | [74] | | غير متحقق |

## تناقضات بملفاتج (بعد قراءة [4])

1. عنوان [4] ومؤلفوه: **قائمة المراجع صحيحة**، وجدول Word خطأ، فصحّحيه.
2. SSIM: **مستخدم** بالورقة (ص 7 و11). جدول المقارنة "غير مستخدم" خطأ.
3. CR: غير مذكور بالورقة، والرقم 16 مشتق من bpp (بقاؤه بجدولج كمشتق فقط).
4. صفوف `tabel_related.docx` ببعض الأحيان مؤلفوها لا يطابقون العنوان. اعتمدي جدول `PAPER_AutoRecovered.docx`.
5. Rahebi [42]: السنة 2022 (قائمة المراجع)، و2025 بأحد الملفين.
6. نص LBG بآخر `tabel_related.docx` يبدو منقولاً من كتاب، لا تنسخينه حرفياً.

## المتبقي

- **Sayood [21]:** PDF الفصول المطلوبة (فصل VQ، وHuffman، وDifferential Encoding، والأساسيات الرياضية للإنتروبي) لتحديد الصفحات.
- [6] Hu (هل يستخدم MPI؟)، [19] Lin (Diff/XOR؟)، [7] و[8] (نص كامل)، [74] MPI Forum، ومصدر الأنوية الهجينة P/E.
- قرار إضافة LBG الأصلي (1980) وHuffman (1952).
- جملة تصنيف lossless/lossy الصريحة من [2].

## مصادر محجوزة لأقسام لاحقة

- **[1] Thomas et al.**: محجوز لفقرة الضغط الهجين (hybrid compression) بالقسم 1.5. حُذف من الفقرة 1 لأنه ورقة طريقة ولا يدعم ادعاء التقييم بمقياسين. الأرقام عنه (PSNR/CR/SSIM) من ملاحظات الباحثة فقط، غير متحقق من PDF.
- فحص نهائي مطلوب: مصادر بالقائمة بلا استشهاد، واستشهادات بلا مصدر.

## تحقق إضافي (من PDFs رفعتها الباحثة)

- **[6] Hu et al. (BDMIP '23)**: **متحقق**. ص 1 (الملخص) وص 4 (الخاتمة): باستخدام MPI، عملية البحث والمطابقة بين blocks نطاق الصورة (domain/range blocks) تُوزَّع على عدة معالجات للتنفيذ المتزامن. تجاربهم: حاسبان Celeron 1.8 GHz بشبكة LAN مع MPICH على Windows XP.
- **[7] Velugoti et al. (arXiv:2608.23165, 24 Aug 2026)**: **متحقق**. ص 1: دراسة أثر المعماريات الهجينة (Alder Lake) على أداء أحمال HPC المتوازية وسلوك التوسع مع عدد الخيوط؛ P-cores أكثر قدرة (تردد تشغيل أعلى) من E-cores؛ التطبيقات ذات عدم توازن العمل تتوسع أفضل على الأنوية الهجينة عند تعطيل thread affinity. **ملاحظة:** الأحمال مبنية على OpenMP (خيوط) وليست MPI. ص 4: عند تثبيت الخيوط وعدم توازن العمل تبقى نواة خاملة.
- **[8] Fernández-Fraga et al. (SAC '24, Art. 4)**: **متحقق**. ص 1: load imbalance سبب شائع لتدهور الأداء؛ يقترحون موازنة ديناميكية بـ MPI RMA (اتصال أحادي الجانب) لتقليل التزامن بين العمليات.
- **[61] Mohammadi et al. (IEEE Access, vol. 14)**: **البيانات متحققة**: الصفحات 35651 إلى 35668 (18 صفحة)، DOI مطابق، نُشرت 2 مارس 2026. موجودة أصلاً بالقائمة ولا تُضاف مرة ثانية.
