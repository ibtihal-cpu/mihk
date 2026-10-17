const INK = "1F1A33", DEEP = "2E2055", PURPLE = "6B4FA3", MAG = "E0457B", TEAL = "2A9D8F", ORG = "E07B22", MIST = "F5F1FB", GOLD = "F2B134";
module.exports.make = function (p) {
  const hdr = (s, chip, title, color, chipW) => {
    s.background = { color: "FFFFFF" };
    const w = chipW || 2.1;
    s.addShape(p.ShapeType.roundRect, { x: 0.5, y: 0.35, w, h: 0.55, rectRadius: 0.1, fill: { color }, line: { color, width: 0 } });
    s.addText(chip, { x: 0.5, y: 0.35, w, h: 0.55, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 16, bold: true, color: "FFFFFF", margin: 0 });
    s.addText(title, { x: 0.5 + w + 0.2, y: 0.3, w: 12.8 - w - 0.2, h: 0.65, valign: "middle", fontFace: "Cambria", fontSize: 28, bold: true, color: DEEP, margin: 0 });
    s.addShape(p.ShapeType.rect, { x: 0.5, y: 1.05, w: 12.33, h: 0.04, fill: { color }, line: { color, width: 0 } });
  };
  const card = (s, x, y, w, h, color, title, body, tsize, bsize) => {
    s.addShape(p.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.1, fill: { color: "FFFFFF" }, line: { color, width: 1.75 } });
    s.addShape(p.ShapeType.rect, { x: x + 0.02, y: y + 0.02, w: 0.12, h: h - 0.04, fill: { color }, line: { color, width: 0 } });
    s.addText([{ text: title, options: { fontSize: tsize || 20, bold: true, color, breakLine: true } }, { text: body, options: { fontSize: bsize || 16, color: INK } }],
      { x: x + 0.3, y: y + 0.05, w: w - 0.45, h: h - 0.1, valign: "middle", fontFace: "Calibri", margin: 0.05, paraSpaceAfter: 6 });
  };
  const bullets = (s, items, box, color, size) => {
    s.addShape(p.ShapeType.roundRect, { x: box.x, y: box.y, w: box.w, h: box.h, rectRadius: 0.08, fill: { color: MIST }, line: { color: MIST, width: 0 } });
    s.addText(items.map((t, i) => ({ text: t, options: { bullet: { code: "25A0", color }, breakLine: i < items.length - 1, paraSpaceAfter: 10 } })),
      { x: box.x + 0.15, y: box.y + 0.1, w: box.w - 0.3, h: box.h - 0.2, valign: "top", fontFace: "Calibri", fontSize: size, color: INK, margin: 0.08 });
  };
  const H = (t, c) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: c }, align: "center", fontSize: 14 } });
  const C = (t, f, o) => ({ text: t, options: Object.assign({ align: "center", fontSize: 13, color: INK, fill: { color: f } }, o || {}) });
  const BL = (t, f) => ({ text: t, options: { align: "center", fontSize: 13, bold: true, color: MAG, fill: { color: f } } });

  // ================= FRONT =================
  const front = () => {
    // 1 title
    let s = p.addSlide(); s.background = { color: DEEP };
    s.addShape(p.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: DEEP }, line: { color: DEEP, width: 0 } });
    s.addShape(p.ShapeType.rect, { x: 0, y: 0, w: 0.35, h: 7.5, fill: { color: MAG }, line: { color: MAG, width: 0 } });
    s.addText("MSc SEMINAR  |  University of Babylon", { x: 0.9, y: 0.7, w: 11.5, h: 0.5, fontFace: "Calibri", fontSize: 18, color: "C9BDE8", bold: true, margin: 0 });
    s.addText("Parallel Image Compression Using High-Performance Computing Strategies", { x: 0.9, y: 1.6, w: 11.5, h: 1.9, fontFace: "Cambria", fontSize: 40, bold: true, color: "FFFFFF", margin: 0, valign: "middle" });
    s.addText("LBG vector quantization, delta coding and Huffman coding with speed-aware MPI on a hybrid P/E-core CPU", { x: 0.9, y: 3.7, w: 11.5, h: 0.9, fontFace: "Calibri", fontSize: 20, color: "E8DFF7", margin: 0 });
    s.addText([{ text: "Presented by  ", options: { color: "C9BDE8" } }, { text: "MSc. Student Ibtihal Hussien", options: { bold: true, color: "FFFFFF", breakLine: true } },
      { text: "Supervised by  ", options: { color: "C9BDE8" } }, { text: "Dr. Ahmed Badri  ·  Dr. Esraa Hadi", options: { bold: true, color: "FFFFFF" } }],
      { x: 0.9, y: 5.3, w: 11.5, h: 1.2, fontFace: "Calibri", fontSize: 20, margin: 0, paraSpaceAfter: 8 });
    // 2 outline
    s = p.addSlide(); hdr(s, "Outline", "Outline", PURPLE);
    const items = ["Introduction", "Literature Review", "Problem Statement", "Thesis Objectives", "Proposed Work", "Experimental Results", "Conclusion", "Future Work"];
    const cols = [PURPLE, PURPLE, MAG, MAG, ORG, TEAL, DEEP, DEEP];
    items.forEach((t, i) => {
      const x = 0.7 + (i % 2) * 6.2, y = 1.45 + Math.floor(i / 2) * 1.4;
      s.addShape(p.ShapeType.roundRect, { x, y, w: 5.8, h: 1.1, rectRadius: 0.1, fill: { color: MIST }, line: { color: cols[i], width: 1.5 } });
      s.addShape(p.ShapeType.ellipse, { x: x + 0.2, y: y + 0.2, w: 0.7, h: 0.7, fill: { color: cols[i] }, line: { color: cols[i], width: 0 } });
      s.addText(String(i + 1), { x: x + 0.2, y: y + 0.2, w: 0.7, h: 0.7, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 22, bold: true, color: "FFFFFF", margin: 0 });
      s.addText(t, { x: x + 1.1, y, w: 4.5, h: 1.1, valign: "middle", fontFace: "Cambria", fontSize: 24, bold: true, color: DEEP, margin: 0 });
    });
    // 3 intro: why compress
    s = p.addSlide(); hdr(s, "Introduction", "Why Image Compression?", PURPLE);
    card(s, 0.7, 1.5, 3.85, 3.6, PURPLE, "Storage", "Large image collections require a large amount of storage space.", 24, 18);
    card(s, 4.75, 1.5, 3.85, 3.6, MAG, "Transmission", "Smaller images reach the receiver sooner and use less network bandwidth.", 24, 18);
    card(s, 8.8, 1.5, 3.85, 3.6, TEAL, "Computation", "A good compression ratio needs complex methods, so the compression itself must stay fast.", 24, 18);
    s.addText("Image compression reduces the amount of data needed to represent an image.", { x: 0.7, y: 5.55, w: 11.9, h: 0.7, align: "center", valign: "middle", fontFace: "Cambria", fontSize: 22, italic: true, color: DEEP, margin: 0 });
    // 4 lossy vs lossless
    s = p.addSlide(); hdr(s, "Introduction", "Lossless and Lossy Compression", PURPLE);
    card(s, 0.7, 1.5, 5.9, 3.3, TEAL, "Lossless", "The original image is recovered exactly. Examples: RLE, Huffman, LZW.", 26, 19);
    card(s, 6.75, 1.5, 5.9, 3.3, ORG, "Lossy", "Some information is discarded to reach a higher compression ratio. Examples: VQ, DCT, DWT.", 26, 19);
    s.addShape(p.ShapeType.roundRect, { x: 0.7, y: 5.15, w: 11.95, h: 1.3, rectRadius: 0.1, fill: { color: MIST }, line: { color: PURPLE, width: 1.5 } });
    s.addText([{ text: "This work: ", options: { bold: true, color: MAG } }, { text: "lossy LBG vector quantization, followed by lossless delta coding and Huffman coding.", options: { color: INK } }],
      { x: 0.9, y: 5.15, w: 11.55, h: 1.3, valign: "middle", fontFace: "Calibri", fontSize: 21, margin: 0 });
    // 5 parallel processing
    s = p.addSlide(); hdr(s, "Introduction", "Parallel Processing in Image Compression", PURPLE);
    s.addText("Parallel processing improves processing speed and efficiency when handling large data.", { x: 0.7, y: 1.4, w: 11.9, h: 1.0, valign: "middle", fontFace: "Cambria", fontSize: 24, italic: true, color: DEEP, margin: 0 });
    card(s, 0.7, 2.7, 3.85, 3.4, ORG, "LBG training dominates", "In the sequential program it takes about 77% (gray) and 81% (color) of the total time.", 22, 17);
    card(s, 4.75, 2.7, 3.85, 3.4, PURPLE, "Data-parallel", "Each training vector is assigned to its nearest codeword independently, so the work can be split across processes.", 22, 17);
    card(s, 8.8, 2.7, 3.85, 3.4, TEAL, "Hybrid CPU", "P-cores and E-cores have different speeds, so an equal split can leave fast cores waiting.", 22, 17);

    // 6 related work 1
    s = p.addSlide(); hdr(s, "Literature Review", "Related Work: Compression Quality", PURPLE, 2.6);
    const rows = [[H("Ref.", PURPLE), H("Image", PURPLE), H("Study", PURPLE), H("Algorithm", PURPLE), H("CR", PURPLE), H("PSNR (dB)", PURPLE)]];
    const W = "FFFFFF", L = "F1ECF9";
    const add = (a, f) => rows.push([C(a[0], f), C(a[1], f, { bold: true }), C(a[2], f, { align: "left", bold: !!a[6] }), C(a[7], f, { align: "left", bold: !!a[6], fontSize: 13 }), a[3] === "___" ? BL("___", f) : C(a[3], f, a[6] ? { bold: true } : {}), C(a[4], f, a[6] ? { bold: true } : {})]);
    [["[6]", "Lena", "Thomas et al.", "1.52", "54.28", "–", 0, "Wavelet coefficients + Huffman coding"], ["[16]", "Lena", "Ranjan and Kumar", "4.41", "34.78", "–", 0, "2D DWT + PCA + canonical Huffman"], ["", "", "This work", "23.50", "29.67", "9.21×", 1, "LBG-VQ + delta + Huffman"],
     ["[6]", "Boat", "Thomas et al.", "1.41", "54.07", "–", 0, "Wavelet coefficients + Huffman coding"], ["", "", "This work", "26.54", "29.11", "9.22×", 1, "LBG-VQ + delta + Huffman"],
     ["[17]", "Cameraman", "Bilal et al.", "–", "25.3–26.8*", "2.61×", 0, "FLBG (LBG with bilinear rescaling)"], ["", "", "This work", "28.88", "29.75", "9.10×", 1, "LBG-VQ + delta + Huffman"]].forEach((a, i) => add(a, a[6] ? L : W));
    s.addNotes("CR values of 'This work' come from the previous Huffman-table accounting. Replace them with the CR column of correctness.csv after the rerun (expected change about -1.2%). Source values checked against the papers: [6] Table 1 and Table 3; [16] Table 1; [17] Table 1 (Cameraman, FLBG).");
    s.addTable(rows, { x: 0.7, y: 1.35, w: 11.9, colW: [0.9, 1.5, 2.2, 4.0, 1.4, 1.9], rowH: 0.5, fontFace: "Calibri", border: { type: "solid", color: "E2D9F3", pt: 1 }, valign: "middle" });
    s.addText("[16]: Lena 512 × 512, Table 1 (CR 4.4058, PSNR 34.7809 dB). [6]: near-lossless scheme. * [17]: FLBG PSNR over 0.15–0.625 bpp (CR not reported).",
      { x: 0.7, y: 5.55, w: 11.9, h: 0.8, fontFace: "Calibri", fontSize: 12, italic: true, color: PURPLE, margin: 0 });
    s.addText("This work reaches a much higher compression ratio than [6] and [16], at a lower PSNR.", { x: 0.7, y: 6.4, w: 11.9, h: 0.6, fontFace: "Cambria", fontSize: 18, bold: true, color: DEEP, margin: 0 });
    // 7 related work 2
    s = p.addSlide(); hdr(s, "Literature Review", "Related Work: Parallel Speedup", PURPLE, 2.6);
    const r2 = [[H("Study", PURPLE), H("Application", PURPLE), H("Resources", PURPLE), H("Baseline", PURPLE), H("Speedup", PURPLE)]];
    [["Tanović et al. (2024)", "k-means, image classification", "12 cores (OpenMP + MPI)", "Not stated", "Up to 10.2×"], ["Papakyriakou et al. (2025)", "k-means, 75 M synthetic points", "2–48 MPI processes", "2 processes", "≈ 10.05×"], ["Bystrov et al. (2023)", "Discrete-element simulation", "8 heterogeneous containers", "Sequential", "Up to 6.0×"]]
      .forEach((a, i) => r2.push(a.map((v, j) => C(v, i % 2 ? W : "F7F3FC", { align: j < 3 ? "left" : "center", bold: j === 0 }))));
    r2.push(["This work", "LBG image compression", "14 MPI processes (6 P + 8 E cores)", "Sequential", "9.19× (LBG); 5.00× / 6.84× (total, gray / color)"].map((v, j) => C(v, "ECE6F6", { align: j < 3 ? "left" : "center", bold: true, color: MAG })));
    s.addTable(r2, { x: 0.7, y: 1.35, w: 11.9, colW: [2.6, 2.7, 2.9, 1.4, 2.3], rowH: 0.7, fontFace: "Calibri", border: { type: "solid", color: "E2D9F3", pt: 1 }, valign: "middle" });
    s.addShape(p.ShapeType.roundRect, { x: 0.7, y: 5.2, w: 11.9, h: 1.55, rectRadius: 0.1, fill: { color: MIST }, line: { color: MAG, width: 2 } });
    s.addText([{ text: "Research gap  ", options: { bold: true, color: MAG, breakLine: true } },
      { text: "Existing parallel studies target k-means or other applications. To our knowledge, none of the reviewed studies evaluates MPI-parallel LBG for image compression on a hybrid P/E-core CPU.", options: { color: INK } }],
      { x: 0.9, y: 5.2, w: 11.5, h: 1.55, valign: "middle", fontFace: "Calibri", fontSize: 18, margin: 0 });
    // 8 problem
    s = p.addSlide(); hdr(s, "Problem Statement", "Problem Statement", MAG, 2.5);
    const probs = ["Transmitting and storing uncompressed images consumes bandwidth and storage capacity.",
      "LBG vector quantization gives a compact representation, but codebook training is computationally expensive: it repeatedly computes distances between training vectors and codewords (about 77% of the sequential time, gray images).",
      "On a hybrid CPU, an equal distribution of training vectors causes workload imbalance: the faster P-cores finish early and wait for the slower E-cores at synchronization points."];
    probs.forEach((t, i) => {
      const y = 1.4 + i * 1.35;
      s.addShape(p.ShapeType.ellipse, { x: 0.7, y: y + 0.2, w: 0.75, h: 0.75, fill: { color: MAG }, line: { color: MAG, width: 0 } });
      s.addText(String(i + 1), { x: 0.7, y: y + 0.2, w: 0.75, h: 0.75, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 24, bold: true, color: "FFFFFF", margin: 0 });
      s.addText(t, { x: 1.7, y, w: 10.9, h: 1.2, valign: "middle", fontFace: "Calibri", fontSize: 18, color: INK, margin: 0 });
    });
    s.addShape(p.ShapeType.roundRect, { x: 0.7, y: 5.55, w: 11.95, h: 1.4, rectRadius: 0.1, fill: { color: MAG }, line: { color: MAG, width: 0 } });
    s.addText("Reduce LBG training and total compression time through speed-aware workload distribution, while preserving the compression ratio and the reconstruction quality of the sequential implementation.",
      { x: 0.95, y: 5.55, w: 11.45, h: 1.4, valign: "middle", fontFace: "Calibri", fontSize: 19, bold: true, color: "FFFFFF", margin: 0 });
    // 9 objectives
    s = p.addSlide(); hdr(s, "Objectives", "Thesis Objectives", MAG, 2.5);
    const obj = [["Image Compression Framework Development", "To compress grayscale and color images by combining LBG vector quantization, delta coding, and Huffman coding."],
      ["LBG Execution-Time Reduction", "To reduce codebook-training time by parallelizing the computationally intensive operations of LBG using MPI."],
      ["Workload Distribution Improvement", "To distribute the training vectors according to the measured throughput of each MPI process on the P-cores and E-cores, and to improve performance compared with equal distribution."],
      ["Performance Evaluation and Result Verification", "To evaluate compression, reconstruction quality and parallel performance, and to verify that the parallel results match the sequential implementation."]];
    obj.forEach((o, i) => card(s, 0.7, 1.35 + i * 1.4, 11.95, 1.25, [PURPLE, ORG, TEAL, MAG][i], `${i + 1}. ${o[0]}`, o[1], 19, 15));
  };

  // ================= MID: setup + metrics =================
  const mid = () => {
    let s = p.addSlide(); hdr(s, "Experimental Results", "Experimental Setup", TEAL, 3.3);
    const cards = [["Hardware", "Intel Core i7-13650HX: 6 P-cores and 8 E-cores (14 cores in total).", PURPLE], ["Software", "Ubuntu 24.04, GCC 13.3 (-O2), Open MPI 4.1.6, written in C.", ORG],
      ["Protocol", "Median of 5 runs; governor set to performance; processes bound to cores, P-cores first.", TEAL], ["Data", "8 standard 512 × 512 images: 4 grayscale and 4 color.", MAG],
      ["LBG settings", "4 × 4 blocks, K = 64 codewords, δ = 0.01, ε = 0.0001 (relative improvement in distortion), at most 100 iterations per level.", DEEP], ["Strategies", "Equal (default for P ≤ 4) and Adaptive speed-aware (P > 4).", GOLD]];
    cards.forEach((c, i) => card(s, 0.7 + (i % 2) * 6.05, 1.45 + Math.floor(i / 2) * 1.8, 5.9, 1.6, c[2], c[0], c[1], 20, 15));
    // metrics
    s = p.addSlide(); hdr(s, "Results", "Performance and Quality Evaluation Metrics", TEAL, 1.6);
    const L = [["Compression Quality", ["Compression Ratio (CR)", "Bits Per Pixel (BPP)", "MSE", "PSNR", "SSIM"], TEAL, "EEF8F6"], ["Parallel Performance", ["Execution Time", "Speedup", "Parallel Efficiency", "Throughput", "Karp–Flatt Metric"], ORG, "FDF1E6"]];
    L.forEach((c, i) => {
      const x = 0.9 + i * 6.0;
      s.addShape(p.ShapeType.roundRect, { x, y: 1.5, w: 5.5, h: 0.7, rectRadius: 0.08, fill: { color: c[2] }, line: { color: c[2], width: 0 } });
      s.addText(c[0], { x, y: 1.5, w: 5.5, h: 0.7, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 22, bold: true, color: "FFFFFF", margin: 0 });
      s.addShape(p.ShapeType.roundRect, { x, y: 2.3, w: 5.5, h: 3.6, rectRadius: 0.08, fill: { color: c[3] }, line: { color: c[2], width: 1.25 } });
      s.addText(c[1].map((t, k) => ({ text: t, options: { bullet: { code: "25A0", color: c[2] }, breakLine: k < c[1].length - 1, paraSpaceAfter: 10 } })), { x: x + 0.3, y: 2.4, w: 4.9, h: 3.4, valign: "middle", fontFace: "Calibri", fontSize: 22, color: "1F1A33", margin: 0.05 });
    });
    s.addText("Each formula is shown next to the result it measures.", { x: 0.9, y: 6.2, w: 11.5, h: 0.4, align: "center", fontFace: "Calibri", fontSize: 16, italic: true, color: PURPLE, margin: 0 });
  };

  // ================= BACK: conclusion, future, references =================
  const back = () => {
    let s = p.addSlide(); hdr(s, "Conclusion", "Conclusion", DEEP, 2.3);
    bullets(s, ["A hybrid image compression framework was implemented: LBG vector quantization, delta coding and Huffman coding.",
      "LBG training was parallelized with MPI: 9.19× speedup on 14 processes (efficiency ≈ 66%); total speedup 5.00× (gray) and 6.84× (color).",
      "The speed-aware (Adaptive) distribution reduced LBG time by 17.2–28.3% compared with Equal distribution (P = 8 to 14).",
      "The parallel results were identical to the sequential ones: same reconstructed images and quality metrics.",
      "Quality: mean PSNR 29.49 dB and SSIM 0.8266 (gray); 28.80 dB and 0.7654 (color), at a compression ratio of ___ (gray) and ___ (color).",
      "The total speedup is limited by the work that runs on Rank 0, mainly image reading and file output."], { x: 0.7, y: 1.4, w: 11.95, h: 5.5 }, DEEP, 19);
    s = p.addSlide(); hdr(s, "Future Work", "Future Work", DEEP, 2.3);
    bullets(s, ["Improve the rate–distortion performance: color transform (YCbCr instead of RGB), prediction or context modeling of the VQ indices, and variable block sizes.",
      "Accelerate the LBG assignment step, which dominates the run time, with GPUs (CUDA or OpenCL) combined with MPI.",
      "Scale to multi-node clusters, larger images and image sequences that share one codebook.",
      "Rebalance the workload during the run, using the measured compute time of each rank and a load-imbalance measure."], { x: 0.7, y: 1.4, w: 11.95, h: 5.5 }, DEEP, 22);
    s = p.addSlide(); hdr(s, "References", "References", DEEP, 2.3);
    bullets(s, ["[6] Thomas, S., Krishna, A., Govind, S., Sahu, A.K. (2025). A novel image compression method using wavelet coefficients and Huffman coding. J. Eng. Res., 13(1): 361-370.",
      "[16] Ranjan, R., Kumar, P. (2023). An improved image compression algorithm using 2D DWT and PCA with canonical Huffman encoding. Entropy, 25(10): 1382.",
      "[17] Bilal, M., Ullah, Z., Mujahid, O., Fouzder, T. (2024). Fast Linde–Buzo–Gray (FLBG) algorithm for image compression through rescaling using bilinear interpolation. J. Imaging, 10(5): 124.",
      "Linde, Y., Buzo, A., Gray, R.M. (1980). An algorithm for vector quantizer design. IEEE Trans. Commun., 28(1): 84-95.",
      "Tanović, A. et al. (2024). ZINC 2024.  Papakyriakou, D. et al. (2025). Int. J. Comput. Appl.  Bystrov, O. et al. (2023). Proc. 7th Int. Conf. on Parallel, Distributed, GPU and Cloud Computing for Engineering.  Paul, R.K. et al. (2024).  Zangana, H.M. (2025)."], { x: 0.7, y: 1.4, w: 11.95, h: 5.5 }, DEEP, 16);
    // closing
    s = p.addSlide(); s.background = { color: "FFF8EE" };
    s.addShape(p.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: "FFF8EE" }, line: { color: "FFF8EE", width: 0 } });
    const conf = [["triangle", 5.06, 0.47, 0.48, "FFC93C", 48], ["ellipse", 1.07, 0.77, 0.32, "2A9D8F", 30], ["ellipse", 5.13, 6.77, 0.36, "E0457B", 285], ["rect", 2.01, 0.96, 0.27, "F2993A", 286], ["rect", 7.39, 1.45, 0.21, "E0457B", 280], ["triangle", 10.15, 4.95, 0.28, "6B4FA3", 41], ["triangle", 11.1, 5.11, 0.35, "F2993A", 311], ["star5", 9.79, 1.03, 0.31, "6B4FA3", 203], ["triangle", 12.43, 4.75, 0.41, "2A9D8F", 118], ["rect", 6.71, 1.13, 0.48, "FFC93C", 13], ["rect", 6.72, 0.28, 0.35, "2A9D8F", 93], ["triangle", 11.3, 1.19, 0.43, "4DA3FF", 329], ["triangle", 9.24, 0.28, 0.28, "FFC93C", 234], ["triangle", 1.0, 6.85, 0.34, "6B4FA3", 53], ["ellipse", 1.73, 0.23, 0.26, "FFC93C", 213], ["ellipse", 10.49, 1.15, 0.21, "FFC93C", 21], ["triangle", 8.17, 0.45, 0.41, "4DA3FF", 262], ["ellipse", 5.84, 0.5, 0.3, "E0457B", 320], ["rect", 0.24, 5.59, 0.34, "4DA3FF", 257], ["star5", 10.64, 0.16, 0.38, "F2993A", 203], ["ellipse", 2.61, 0.23, 0.48, "4DA3FF", 148], ["star5", 3.25, 0.87, 0.54, "6B4FA3", 77], ["star5", 9.89, 0.16, 0.32, "6B4FA3", 119], ["ellipse", 3.97, 1.02, 0.39, "F2993A", 270], ["triangle", 11.42, 0.36, 0.3, "2A9D8F", 126], ["triangle", 3.5, 0.23, 0.31, "4DA3FF", 287], ["star5", 8.38, 1.35, 0.32, "E0457B", 133], ["ellipse", 9.53, 4.91, 0.46, "2A9D8F", 54], ["triangle", 8.98, 6.31, 0.26, "6B4FA3", 204], ["triangle", 9.16, 1.03, 0.24, "4DA3FF", 44], ["ellipse", 7.57, 6.86, 0.4, "4DA3FF", 79], ["ellipse", 8.65, 7.02, 0.18, "E0457B", 111], ["rect", 7.43, 0.21, 0.48, "2A9D8F", 235], ["triangle", 4.38, 6.81, 0.45, "2A9D8F", 42], ["ellipse", 12.29, 1.12, 0.45, "4DA3FF", 8], ["star5", 0.34, 0.88, 0.47, "6B4FA3", 35], ["ellipse", 0.33, 0.17, 0.4, "4DA3FF", 283], ["ellipse", 6.11, 6.97, 0.19, "2A9D8F", 42], ["rect", 0.23, 1.67, 0.35, "FFC93C", 75], ["ellipse", 2.89, 6.79, 0.29, "6B4FA3", 37], ["star5", 5.25, 1.22, 0.43, "F2993A", 22], ["star5", 1.84, 6.99, 0.31, "6B4FA3", 268], ["star5", 4.38, 0.23, 0.35, "E0457B", 28], ["rect", 6.06, 1.25, 0.27, "2A9D8F", 177], ["rect", 12.4, 0.33, 0.41, "F2993A", 163], ["star5", 3.59, 6.79, 0.32, "F2993A", 325], ["rect", 0.37, 3.38, 0.19, "E0457B", 271], ["rect", 11.73, 5.19, 0.21, "4DA3FF", 244]];
    conf.forEach(c => s.addShape(p.ShapeType[c[0]], { x: c[1], y: c[2], w: c[3], h: c[3], rotate: c[5], fill: { color: c[4] }, line: { color: c[4], width: 0 } }));
    s.addText([{ text: "Thank ", options: { color: "6B4FA3" } }, { text: "You!", options: { color: "E0457B" } }],
      { x: 0.8, y: 1.85, w: 11.7, h: 1.9, align: "center", valign: "middle", fontFace: "Cambria", fontSize: 88, bold: true, margin: 0 });
    s.addText("for your attention", { x: 0.8, y: 3.75, w: 11.7, h: 0.8, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 36, color: "F2993A", bold: true, margin: 0 });
    s.addShape(p.ShapeType.smileyFace, { x: 1.2, y: 5.05, w: 1.6, h: 1.6, fill: { color: "FFC93C" }, line: { color: "2E2055", width: 3 } });
    s.addShape(p.ShapeType.roundRect, { x: 3.2, y: 5.25, w: 5.6, h: 1.2, rectRadius: 0.3, fill: { color: "E0457B" }, line: { color: "E0457B", width: 0 } });
    s.addShape(p.ShapeType.triangle, { x: 2.85, y: 5.65, w: 0.45, h: 0.4, rotate: 270, fill: { color: "E0457B" }, line: { color: "E0457B", width: 0 } });
    s.addText("Any questions?", { x: 3.2, y: 5.25, w: 5.6, h: 1.2, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 36, bold: true, color: "FFFFFF", margin: 0 });
    s.addText([{ text: "Ibtihal Hussien", options: { bold: true, color: "2E2055", breakLine: true } }, { text: "University of Babylon", options: { color: "6B4FA3" } }],
      { x: 9.5, y: 5.85, w: 3.6, h: 1.0, align: "right", fontFace: "Calibri", fontSize: 18, margin: 0, paraSpaceAfter: 4 });
  };
  return { front, mid, back };
};
