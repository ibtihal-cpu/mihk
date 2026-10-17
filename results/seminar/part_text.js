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
    const rows = [[H("Ref.", PURPLE), H("Image", PURPLE), H("Study", PURPLE), H("CR", PURPLE), H("PSNR (dB)", PURPLE)]];
    const W = "FFFFFF", L = "F1ECF9";
    const add = (a, f) => rows.push([C(a[0], f), C(a[1], f, { bold: true }), C(a[2], f, { align: "left", bold: !!a[6] }), a[3] === "___" ? BL("___", f) : C(a[3], f), C(a[4], f)]);
    [["[6]", "Lena", "Thomas et al.", "1.52", "54.28", "–"], ["[16]", "", "Ranjan and Kumar", "4.41", "34.78", "–"], ["", "", "This work", "___", "29.67", "9.21×", 1],
     ["[6]", "Boat", "Thomas et al.", "1.41", "54.07", "–"], ["", "", "This work", "___", "29.11", "9.22×", 1],
     ["[17]", "Cameraman", "Bilal et al.", "–", "25.3–26.8*", "2.61×"], ["", "", "This work", "___", "29.75", "9.10×", 1]].forEach((a, i) => add(a, a[6] ? L : W));
    s.addTable(rows, { x: 0.7, y: 1.35, w: 11.9, colW: [1.2, 2.2, 4.2, 2.0, 2.3], rowH: 0.5, fontFace: "Calibri", border: { type: "solid", color: "E2D9F3", pt: 1 }, valign: "middle" });
    s.addText("* Bilal et al.: PSNR range at bit rates up to 0.625 bpp (CR not reported). Thomas et al. is a near-lossless scheme (CR ≈ 1.5).",
      { x: 0.7, y: 5.55, w: 11.9, h: 0.8, fontFace: "Calibri", fontSize: 12, italic: true, color: PURPLE, margin: 0 });
    s.addText("The proposed method provides substantially higher compression than the near-lossless method, with lower reconstruction fidelity.", { x: 0.7, y: 6.4, w: 11.9, h: 0.6, fontFace: "Cambria", fontSize: 18, bold: true, color: DEEP, margin: 0 });
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
    const mrows = [[H("Quality", TEAL), H("Formula", TEAL), H("Performance", ORG), H("Formula", ORG)],
      ["CR", "S_orig / S_comp", "Execution time", "T (median of 5 runs)"], ["BPP", "compressed bits / pixels", "Speedup", "S = T_seq / T_P"],
      ["MSE", "mean (I − Î)²", "Efficiency", "E = S / P"], ["PSNR", "10·log10(255² / MSE)  dB", "Throughput", "I_size / T_total  (MiB/s)"], ["SSIM", "11 × 11 Gaussian window, σ = 1.5", "Karp–Flatt", "e = (1/S − 1/P) / (1 − 1/P)"]];
    const body = mrows.slice(1).map((r, i) => { const f = i % 2 ? "FFFFFF" : "EEF8F6"; return [C(r[0], f, { bold: true, color: TEAL, fontSize: 17 }), C(r[1], f, { fontSize: 16 }), C(r[2], i % 2 ? "FFFFFF" : "FDF1E6", { bold: true, color: ORG, fontSize: 17 }), C(r[3], i % 2 ? "FFFFFF" : "FDF1E6", { fontSize: 16 })]; });
    s.addTable([mrows[0]].concat(body), { x: 0.7, y: 1.45, w: 11.95, colW: [1.6, 4.4, 2.1, 3.85], rowH: 0.7, fontFace: "Calibri", border: { type: "solid", color: "FFFFFF", pt: 1.5 }, valign: "middle" });
    s.addText("S_comp = codebook + Huffman table + Huffman-coded data (accounted size).",
      { x: 0.7, y: 5.75, w: 11.95, h: 0.4, fontFace: "Calibri", fontSize: 15, italic: true, color: PURPLE, margin: 0 });
  };

  // ================= BACK: conclusion, future, references =================
  const back = () => {
    let s = p.addSlide(); hdr(s, "Conclusion", "Conclusion", DEEP, 2.3);
    bullets(s, ["A hybrid image compression framework was implemented: LBG vector quantization, delta coding and Huffman coding.",
      "LBG training was parallelized with MPI: 9.19× speedup on 14 processes (efficiency ≈ 66%); total speedup 5.00× (gray) and 6.84× (color).",
      "The speed-aware (Adaptive) distribution reduced LBG time by 17.2–28.3% compared with Equal distribution (P = 8 to 14).",
      "The parallel results were identical to the sequential ones: same reconstructed images and quality metrics.",
      "Quality: mean PSNR 29.49 dB and SSIM 0.8266 (gray); 28.80 dB and 0.7654 (color), at a compression ratio of ___ (gray) and ___ (color).",
      "The total speedup is limited by the sequential coding and reconstruction stages."], { x: 0.7, y: 1.4, w: 11.95, h: 5.5 }, DEEP, 19);
    s = p.addSlide(); hdr(s, "Future Work", "Future Work", DEEP, 2.3);
    bullets(s, ["Parallelize the delta coding, Huffman coding and reconstruction stages.",
      "Evaluate other block sizes, codebook sizes and larger images.",
      "Define an efficiency measure that accounts for the different speeds of P-cores and E-cores.",
      "Implement a complete container file format (stored Huffman table and header) with a stand-alone decoder; the current program only accounts the compressed size.",
      "Extend the study to other hybrid CPUs and to hybrid MPI + OpenMP implementations."], { x: 0.7, y: 1.4, w: 11.95, h: 5.5 }, DEEP, 21);
    s = p.addSlide(); hdr(s, "References", "References", DEEP, 2.3);
    bullets(s, ["[6] Thomas, S., Krishna, A., Govind, S., Sahu, A.K. (2025). A novel image compression method using wavelet coefficients and Huffman coding. J. Eng. Res., 13(1): 361-370.",
      "[16] Ranjan, R., Kumar, P. (2023). An improved image compression algorithm using 2D DWT and PCA with canonical Huffman encoding. Entropy, 25(10): 1382.",
      "[17] Bilal, M., Ullah, Z., Mujahid, O., Fouzder, T. (2024). Fast Linde–Buzo–Gray (FLBG) algorithm for image compression through rescaling using bilinear interpolation. J. Imaging, 10(5): 124.",
      "Linde, Y., Buzo, A., Gray, R.M. (1980). An algorithm for vector quantizer design. IEEE Trans. Commun., 28(1): 84-95.",
      "Tanović, A. et al. (2024). ZINC 2024.  Papakyriakou, D. et al. (2025). Int. J. Comput. Appl.  Bystrov, O. et al. (2023). Proc. 7th Int. Conf. on Parallel, Distributed, GPU and Cloud Computing for Engineering.  Paul, R.K. et al. (2024).  Zangana, H.M. (2025)."], { x: 0.7, y: 1.4, w: 11.95, h: 5.5 }, DEEP, 16);
  };
  return { front, mid, back };
};
