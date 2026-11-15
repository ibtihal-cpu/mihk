# خريطة الاستشهادات للمقدمة 1.1 (الفقرات 2 إلى 7)

النص لم يُغيَّر. الأرقام هي أرقام قائمتج الحالية (تُعاد ترقيمتها حسب أول ظهور في النهاية).

مفتاح الحالة:
- **متحقق**: قرأت النص نفسه (PDF أو نص لصقتيه) والادعاء موجود.
- **ملاحظاتج**: مدعوم بملاحظاتج بملفي PAPER_AutoRecovered.docx وtabel_related.docx (قراءة ثانوية، غير متحقق من PDF المصدر).
- **ملخص**: مدعوم بملخص الورقة فقط.
- **غير متحقق**: لا أملك سنداً.

## الفقرة 2

| الجملة | الاستشهاد المقترح | الأساس | الحالة |
|---|---|---|---|
| transform-based methods such as DWT | [3] Ranjan | ملاحظاتج: PCA + 2D-DWT (Haar) + Hard Thresholding + Canonical Huffman | ملاحظاتج |
| VQ is a lossy technique ... codebook | [21] Sayood (يُضاف) | لا سند عندي للفصل والصفحة | غير متحقق (يحتاج صفحة) |
| LBG is a widely used method for generating VQ codebooks | [41] Ghadami، [42] Rahebi (بدل أو مع [4], [5]) | ملاحظاتج: [41] = VQ + LBG + ISCA؛ [42] = VQ-LBG محسّن بـ WOA | ملاحظاتج |
| iterative clustering: assign to nearest codeword, update codewords | [21] Sayood | النص الملصوق بآخر tabel_related.docx: "algorithm for the case where we have a training set ... looks very much like the k-means algorithm"، يُعرّف مناطق التكميم وإعادة حساب القيم كمتوسطات | متحقق (من نص ملصوق يبدو من Sayood؛ تأكدي من المصدر والصفحة) |
| the codebook influences distortion and image quality | [41], [42] (بدل [4], [5]) | ملاحظاتج: تحسين الـ codebook يحسّن جودة إعادة البناء | ملاحظاتج |

## الفقرة 3

| الجملة | الاستشهاد | الأساس | الحالة |
|---|---|---|---|
| LBG training is computationally costly | [4] Bilal (ويمكن [42]) | ملاحظاتج: الفجوة التي عالجها [4] هي الكلفة الزمنية العالية لتوليد الـ codebook في LBG؛ [42]: high computational cost | ملاحظاتج |
| execution time depends on number of vectors, codebook size, convergence | بدون استشهاد (أو إحالة لتحليل التعقيد بالفصل 3) | استنتاج ذاتي | لا يحتاج |
| Bilal et al. [4] ... fast LBG based on rescaling | [4] | ملاحظاتج: VQ + LBG + FLBG (Pre-Scaling)، هدفه تقليل زمن توليد الـ codebook (LBG ≈ 9.07 s مقابل FLBG ≈ 4.02 s) | ملاحظاتج. **عبارة "to reduce the number of comparisons" غير موجودة بملاحظاتج** |
| Severo et al. [5] ... initialization | [5] | لا شي بملفاتج | غير متحقق |

## الفقرة 4

| الجملة | الاستشهاد | الأساس | الحالة |
|---|---|---|---|
| Parallel computing ... reduce execution time | [26] Pousa | ص 111: خوارزميات متوازية على معماريات متوازية لتقليل زمن التنفيذ | متحقق |
| MPI provides communication operations | [74] MPI Forum | لم أقرأه | غير متحقق |
| Hu et al. [6] applied MPI ... | [6] | لا شي بملفاتج | غير متحقق (**الأخطر**) |
| MPI processes can distribute distance calculations ... | بدون استشهاد (تصميمج، الفصل 3) | | لا يحتاج |

## الفقرة 5

| الجملة | الاستشهاد | الأساس | الحالة |
|---|---|---|---|
| Heterogeneous multicore: P-cores and E-cores | لا مصدر | لا شي بملفاتج | غير متحقق |
| Velugoti et al. [7] ... hybrid CPU architectures | [7] | ملخص الورقة | ملخص |
| equal workloads on different cores → waiting | بدون استشهاد (استنتاج، يدعمه الفصل 4) | | |
| communication overhead can reduce parallel efficiency | [31] Schryen | ص 4: القيم بدون كلفة هي حدود عليا لما يتحقق عملياً | متحقق (يغطي الكلفة فقط، مو عدم التوازن) |
| Fernández-Fraga et al. [8] | [8] | ملخص الورقة | ملخص |

## الفقرة 6 (الجدة)

تعتمد على القسم 1.5 (لم أره). ملاحظاتج تدعم أن [4] و[42] لا يعتمدان التوازي (حسب ملاحظاتج)، لكن الجملة تحتاج أن يغطي 1.5 الأعمال المتوازية القريبة، منها [71] Manohar (VQ على GPU) و[11] Zangana.

## الفقرة 7

| الجملة | الاستشهاد | الأساس | الحالة |
|---|---|---|---|
| LBG vector quantization | [21] (+ LBG الأصلي غير موجود بقائمتج) | | انظري أعلاه |
| delta coding | [34] Zhu، [21]، وربما [19] Lin | [34]: متحقق من النص الكامل (معادلتا 3 و8). [19]: ملاحظاتج تقول "Difference/XOR على جدول المؤشرات" | [34] متحقق؛ [19] ملاحظاتج |
| Huffman coding (**لا canonical**) | [21] (+ Huffman 1952 غير موجود) | | غير متحقق |
| collective communication | [74] | | غير متحقق |

## تناقضات بملفاتج لازم تُحسم قبل الاستشهاد

1. **Bilal [4]: العنوان والمؤلفون.** جدولج: "Fast Codebook Generation Using Pre-Scaling for LBG-Based Image Compression" ومؤلفوه "O. Mahmood, T. Faisa...". قائمة المراجع: "Fast Linde–Buzo–Gray (FLBG) algorithm ... rescaling using bilinear interpolation" ومؤلفوه "O. Mujahid, T. Fouzder". افتحي الورقة وانسخي العنوان والأسماء الصحيحة.
2. **Bilal [4]: SSIM.** ملاحظة "القوة" تقول إن PSNR وSSIM قريبان من LBG، بينما جدول المقارنة يقول SSIM "غير مستخدم". واحدة خطأ.
3. **Bilal [4]: CR.** أول جدول يكتب CR = 16، وجدول المقارنة يقول "غير محسوب". الرقم 16 على الأرجح مشتق من bpp (8 ÷ 0.5) ولا تذكره الورقة.
4. **tabel_related.docx:** عدة صفوف فيها مؤلفون لا يطابقون العنوان (مثلاً عنوان Thomas et al. بمؤلفي WISE: Mao وWang وGuan وXue). جدول PAPER_AutoRecovered.docx متسق أكثر، فاعتمديه.
5. **Rahebi [42]:** السنة 2025 في tabel_related.docx، و2022 بقائمة المراجع وبالجدول الآخر. اعتمدي 2022 بعد التأكد.
6. **نص LBG الملصوق** بآخر tabel_related.docx يبدو منقولاً حرفياً من كتاب (يشير إلى [115] Lloyd و[125] LBG). لا تنسخينه، أعيدي صياغته بكلماتج واستشهدي بـ[21] مع الصفحة.

## مطلوب لإغلاق الباقي

- PDF لـ [4] و[5] و[6] (و[19] إذا تريدين استخدام Diff/XOR لدعم Delta).
- قرار: إضافة LBG الأصلي (1980) وHuffman (1952) أو الاكتفاء بـ[21].
- مصدر للأنوية الهجينة P/E (فقرة 5).
