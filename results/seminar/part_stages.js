const spec = require("./overview_spec.json");
module.exports = function (p) {
const INK = "1F1A33", DEEP = "2E2055", MAG = "E0457B", MIST = "F5F1FB";
const COL = { 1: "2F6FB5", 2: "E07B22", 3: "2A9D8F", 4: "6B4FA3" };
const lines = (txt, opt) => txt.split("\n").map((t, i, a) => ({ text: t, options: Object.assign({ breakLine: i < a.length - 1 }, opt) }));

// ---------- slide 1: overview (same geometry as overview.pptx) ----------
(function () {
  const s = p.addSlide(); s.background = { color: "FFFFFF" };
  const PAR = "E07B22", SEQ = "5B6770";
  const top = 0.25, rowH = 1.45, gap = 0.33, hx = 0.4, hw = 2.45, bx0 = 3.05, bw = 2.2, arrow = 0.3;
  spec.stages.forEach((st, i) => {
    const y = top + i * (rowH + gap);
    s.addShape(p.ShapeType.roundRect, { x: hx - 0.05, y: y - 0.05, w: 12.58, h: rowH + 0.1, rectRadius: 0.1, fill: { color: st.light }, line: { color: st.color, width: st.hl ? 2.5 : 1, dashType: st.hl ? "dash" : "solid" } });
    s.addShape(p.ShapeType.roundRect, { x: hx, y, w: hw, h: rowH, rectRadius: 0.08, fill: { color: st.color }, line: { color: st.color, width: 0 } });
    s.addText([{ text: st.name, options: { fontSize: 22, bold: true, breakLine: true } }].concat(lines(st.sub, { fontSize: 15 })),
      { x: hx, y, w: hw, h: rowH - 0.35, align: "center", valign: "middle", fontFace: "Calibri", color: "FFFFFF", margin: 0.06 });
    s.addShape(p.ShapeType.roundRect, { x: hx + 0.12, y: y + rowH - 0.4, w: hw - 0.24, h: 0.32, rectRadius: 0.16, fill: { color: "FFFFFF" }, line: { color: "FFFFFF", width: 0 } });
    s.addText(st.tag === "par" ? "PARALLEL: all processes" : st.tag === "mix" ? "SEQUENTIAL: Process 0" : "SEQUENTIAL: Process 0", { x: hx + 0.12, y: y + rowH - 0.4, w: hw - 0.24, h: 0.32, align: "center", valign: "middle", fontFace: "Calibri", fontSize: st.tag === "mix" ? 11 : 12, bold: true, color: st.tag === "par" ? PAR : SEQ, margin: 0 });
    st.steps.forEach((t, j) => {
      const x = bx0 + j * (bw + arrow);
      s.addShape(p.ShapeType.roundRect, { x, y: y + 0.1, w: bw, h: rowH - 0.2, rectRadius: 0.08, fill: { color: st.parstep === j ? "FDEBD9" : "FFFFFF" }, line: { color: st.parstep === j ? PAR : st.color, width: st.parstep === j ? 2.5 : 1.5, dashType: st.parstep === j ? "dash" : "solid" } });
      s.addText([{ text: `${j + 1}. ${t[0]}`, options: { fontSize: 16, bold: true, color: st.color, breakLine: true } }].concat(lines(t[1], { fontSize: 13, color: INK })),
        { x, y: y + 0.1, w: bw, h: rowH - 0.2, align: "center", valign: "middle", fontFace: "Calibri", margin: 0.05 });
      if (j < st.steps.length - 1)
        s.addShape(p.ShapeType.rightArrow, { x: x + bw + 0.03, y: y + rowH / 2 - 0.13, w: arrow - 0.06, h: 0.26, fill: { color: INK }, line: { color: INK, width: 0 } });
    });
    if (i < spec.stages.length - 1) {
      s.addText(spec.between[i], { x: 6.95, y: y + rowH + 0.04, w: 5.9, h: gap - 0.08, fontFace: "Calibri", fontSize: 13, italic: true, bold: true, color: MAG, valign: "middle", margin: 0 });
      s.addShape(p.ShapeType.downArrow, { x: 6.55, y: y + rowH + 0.06, w: 0.26, h: gap - 0.12, fill: { color: INK }, line: { color: INK, width: 0 } });
    }
  });
  const lg = (x, c, t) => { s.addShape(p.ShapeType.roundRect, { x, y: 7.08, w: 0.5, h: 0.24, rectRadius: 0.12, fill: { color: c }, line: { color: "FFFFFF", width: 0 } }); s.addText(t, { x: x + 0.6, y: 7.06, w: 4.2, h: 0.28, fontFace: "Calibri", fontSize: 13, bold: true, color: INK, margin: 0, valign: "middle" }); };
  lg(2.6, PAR, "Parallel: all MPI processes work together"); lg(7.4, SEQ, "Sequential: executed on Process 0 only");
})();

// ---------- helpers for stage slides ----------
function header(s, stage, label, title) {
  s.background = { color: "FFFFFF" };
  s.addShape(p.ShapeType.roundRect, { x: 0.5, y: 0.35, w: 1.6, h: 0.55, rectRadius: 0.1, fill: { color: COL[stage] }, line: { color: COL[stage], width: 0 } });
  s.addText(label, { x: 0.5, y: 0.35, w: 1.6, h: 0.55, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 18, bold: true, color: "FFFFFF", margin: 0 });
  s.addText(title, { x: 2.3, y: 0.3, w: 10.5, h: 0.65, valign: "middle", fontFace: "Cambria", fontSize: 28, bold: true, color: DEEP, margin: 0 });
  s.addShape(p.ShapeType.rect, { x: 0.5, y: 1.05, w: 12.33, h: 0.04, fill: { color: COL[stage] }, line: { color: COL[stage], width: 0 } });
}
function fit(img, w, h, box) { // aspect-correct placement centred in box
  const r = Math.min(box.w / w, box.h / h), W = w * r, H = h * r;
  return { path: img, x: box.x + (box.w - W) / 2, y: box.y + (box.h - H) / 2, w: W, h: H };
}
function figure(s, stage, img, w, h, box, caption) {
  s.addShape(p.ShapeType.roundRect, { x: box.x, y: box.y, w: box.w, h: box.h, rectRadius: 0.08, fill: { color: "FFFFFF" }, line: { color: COL[stage], width: 1.25 } });
  s.addImage(fit(img, w, h, { x: box.x + 0.1, y: box.y + 0.1, w: box.w - 0.2, h: box.h - 0.2 }));
  if (caption) s.addText(caption, { x: box.x, y: box.y + box.h + 0.03, w: box.w, h: 0.3, align: "center", fontFace: "Calibri", fontSize: 12, italic: true, color: "6B4FA3", margin: 0 });
}
function bullets(s, stage, items, box, size) {
  s.addShape(p.ShapeType.roundRect, { x: box.x, y: box.y, w: box.w, h: box.h, rectRadius: 0.08, fill: { color: MIST }, line: { color: MIST, width: 0 } });
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: { code: "25A0", color: COL[stage] }, breakLine: i < items.length - 1, paraSpaceAfter: 10 } })),
    { x: box.x + 0.1, y: box.y + 0.1, w: box.w - 0.2, h: box.h - 0.2, valign: "top", fontFace: "Calibri", fontSize: size || 17, color: INK, margin: 0.08 });
}
const [PW, PH] = require("child_process").execSync("python3 -c \"from PIL import Image;print(*Image.open('figs/parallel_overview.png').size)\"").toString().trim().split(" ").map(Number);
const FIG = { x: 0.5, y: 1.35, w: 8.0, h: 5.45 }, TXT = { x: 8.75, y: 1.35, w: 4.1, h: 5.45 };

// ---------- Stage 1 ----------
let s = p.addSlide(); header(s, 1, "Stage 1", "Block Formation");
figure(s, 1, "assets/ch3_fig32.png", 802, 359, FIG, "Block-based vector quantization (illustrative)");
bullets(s, 1, ["The image is divided into non-overlapping 4 × 4 blocks.", "Each block becomes a 16-dimensional vector.", "A 512 × 512 image gives N = 16,384 training vectors.", "Color images: the R, G and B channels are processed independently."], TXT);

// ---------- Stage 2a ----------
s = p.addSlide(); header(s, 2, "Stage 2", "LBG Codebook Training");
figure(s, 2, "assets/lbg_flow_color.png", 1510, 1077, FIG);
bullets(s, 2, ["Start from the global mean as the first codeword.", "Binary splitting (δ = 0.01) doubles the codebook size.", "Lloyd refinement: assign each vector to its nearest codeword, then update the centroids.", "Stop at ΔD ≤ ε or 100 iterations; repeat until K = 64."], TXT);

// ---------- Stage 2b ----------
s = p.addSlide(); header(s, 2, "Stage 2", "Parallel LBG Training (MPI)");
(function () {
  const im = { w: PW, h: PH };
  figure(s, 2, "figs/parallel_overview.png", PW, PH, { x: 0.5, y: 1.25, w: 12.33, h: 4.6 });
  const items = [["SPMD: every process runs the same program on its own chunk of vectors.", "Nearest-codeword assignment is local and is the main cost of LBG."],
                 ["Allreduce combines sums, counts and distortion; every process updates the same codebook.", "Gatherv collects the final indices on Process 0."]];
  items.forEach((col, k) => bullets(s, 2, col, { x: 0.5 + k * 6.25, y: 5.95, w: 6.08, h: 1.35 }, 14));
})();

// ---------- Stage 2c ----------
s = p.addSlide(); header(s, 2, "Stage 2", "Balanced and Unbalanced Workload Distribution");
figure(s, 2, "figs/Workload_distribution.png", 2000, 1362, FIG);
bullets(s, 2, ["Balanced (Equal), P ≤ 4: each process gets N/P training vectors.", "Unbalanced (Adaptive), P > 4: each process gets a share proportional to its measured speed.", "Share of process r: q_r = N · s_r / Σ s_j, where s_r is the speed of process r.", "Speed s_r is measured once by a short calibration run (3 trials, the first is a warm-up)."], TXT, 16);

// ---------- Stage 3a ----------
s = p.addSlide(); header(s, 3, "Stage 3", "Delta Coding");
figure(s, 3, "assets/ch3_fig34.png", 592, 267, FIG);
bullets(s, 3, ["Stores the difference between successive VQ indices (offset 128).", "Neighbouring blocks are correlated, so the differences cluster around the offset.", "Example (Lena): entropy falls from 5.39 to 4.67 bits per symbol."], TXT);

// ---------- Stage 3b ----------
s = p.addSlide(); header(s, 3, "Stage 3", "Huffman Coding");
figure(s, 3, "assets/ch3_fig35.png", 1145, 122, { x: 0.5, y: 1.4, w: 12.33, h: 1.7 });
bullets(s, 3, ["Frequent symbols receive shorter codewords, rare symbols longer ones (lossless).",
  "Output: the Huffman codes and the encoded bitstream.",
  "Accounted compressed size = codebook (K × 16 bytes, one byte per codeword element) + Huffman table + Huffman-coded data.",
  "The table is accounted as 5 bytes per used symbol (1 byte symbol + 4 bytes frequency) plus 10 bytes of fixed metadata. The program accounts this size; it does not write a stand-alone compressed file."], { x: 0.5, y: 3.45, w: 12.33, h: 3.35 }, 19);

// ---------- Stage 4 ----------
s = p.addSlide(); header(s, 4, "Stage 4", "Decoding and Evaluation");
const chips = [["1. Huffman decoding", "bit stream → delta values", "2A9D8F"], ["2. Inverse delta", "deltas → VQ indices", "2F6DB5"], ["3. Codebook lookup", "index → 4×4 block", "E07B22"], ["4. Reconstructed image", "blocks → 512×512 image", "6B4FA3"]];
chips.forEach((c, i) => {
  const x = 0.5 + i * 3.15;
  s.addShape(p.ShapeType.roundRect, { x, y: 1.25, w: 2.75, h: 1.05, rectRadius: 0.1, fill: { color: c[2] }, line: { color: c[2], width: 0 } });
  s.addText([{ text: c[0], options: { fontSize: 16, bold: true, breakLine: true } }, { text: c[1], options: { fontSize: 12.5 } }], { x, y: 1.25, w: 2.75, h: 1.05, align: "center", valign: "middle", fontFace: "Calibri", color: "FFFFFF", margin: 0.05 });
  if (i < 3) s.addShape(p.ShapeType.rightArrow, { x: x + 2.78, y: 1.65, w: 0.34, h: 0.26, fill: { color: INK }, line: { color: INK, width: 0 } });
});
s.addImage({ path: "assets/lena_color_orig.png", x: 0.5, y: 2.55, w: 3.2, h: 3.2 });
s.addImage({ path: "assets/lena_color_rec.png", x: 3.95, y: 2.55, w: 3.2, h: 3.2 });
s.addText("Original", { x: 0.5, y: 5.78, w: 3.2, h: 0.3, align: "center", fontFace: "Calibri", fontSize: 14, bold: true, color: INK, margin: 0 });
s.addText("Reconstructed", { x: 3.95, y: 5.78, w: 3.2, h: 0.3, align: "center", fontFace: "Calibri", fontSize: 14, bold: true, color: INK, margin: 0 });
s.addText("Lena (color): PSNR 28.91 dB, SSIM 0.7594", { x: 0.5, y: 6.15, w: 6.65, h: 0.3, align: "center", fontFace: "Calibri", fontSize: 13, italic: true, color: "6B4FA3", margin: 0 });
bullets(s, 4, ["Decoding and reconstruction run on Process 0.", "Quality: MSE, PSNR and SSIM (SSIM is computed in parallel); size: CR and BPP.", "Parallel performance: time, speedup, efficiency, throughput, Karp–Flatt.", "Verification: the reconstructed image (MD5) and the metrics are identical for the sequential run, P = 4, and P = 14 (Adaptive and Equal)."], { x: 7.5, y: 2.55, w: 5.35, h: 4.25 }, 16);

};
