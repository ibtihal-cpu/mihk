// Seminar deck: parallel LBG vector-quantization image compression (MPI, heterogeneous CPU).
// All numbers come from results/final_campaign (see data.json, built from the final CSVs) and tables_final.md.
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const path = require("path");
const SKILL = "/root/.claude/skills/synced/c0fc71af-12b5-4fa7-af91-6a794fc62337_1bdfb022-a6b2-4409-ae7e-df32933d7451/pptx";
const { applyTheme } = require(path.join(SKILL, "scripts/apply_theme.js"));
const D = require("./data.json");
const A = (f) => path.join(__dirname, "assets", f);

// ---------- palette / theme ----------
const INK = "1F1A33", DEEP = "2E2055", PURPLE = "6B4FA3", LAV = "A794D6", MAG = "E0457B", TEAL = "2A9D8F", GOLD = "F2B134",
  SLATE = "8A8FA8", MIST = "F5F1FB", LINE = "DDD5EE", WHITE = "FFFFFF", MUTED = "5E5878";
const THEME = {
  name: "Seminar Plum", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: INK, lt1: WHITE, dk2: DEEP, lt2: MIST, accent1: PURPLE, accent2: MAG, accent3: TEAL, accent4: GOLD, accent5: LAV, accent6: SLATE, hlink: PURPLE, folHlink: SLATE },
};
const HF = "Cambria", BF = "Calibri";
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.theme = { headFontFace: HF, bodyFontFace: BF };
pres.title = "Parallel LBG vector-quantization image compression: MPI on a heterogeneous multicore CPU";
pres.author = "Ibtihal Hussien";

pres.defineSlideMaster({
  title: "TITLE_DARK", background: { color: DEEP }, objects: [],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: WHITE },
  objects: [
    { text: { text: "Parallel LBG vector-quantization image compression  ·  MSc seminar  ·  University of Babylon",
        options: { x: 0.6, y: 7.02, w: 9, h: 0.3, fontSize: 10, color: SLATE, fontFace: BF, margin: 0 } } },
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.62, w: 12.1, h: 0.8, fontFace: HF, fontSize: 30, bold: true, color: INK, margin: 0, valign: "middle" }, text: "" } },
  ],
  slideNumber: { x: 12.2, y: 7.02, w: 0.55, h: 0.3, fontSize: 10, color: SLATE, fontFace: BF, align: "right" },
});

// ---------- helpers ----------
let nSlide = 0;
function cs(tag, title, notes) {
  const s = pres.addSlide({ masterName: "CONTENT" }); nSlide++;
  s.addText(tag.toUpperCase(), { x: 0.6, y: 0.32, w: 9, h: 0.3, fontSize: 11, bold: true, color: MAG, charSpacing: 3, fontFace: BF, margin: 0, isTextBox: true, objectName: "Section tag" });
  s.addText(title, { placeholder: "title" });
  if (notes) s.addNotes(notes);
  return s;
}
async function icon(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
function card(s, x, y, w, h, fill = MIST, name = "Card") {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill, width: 0 }, rectRadius: 0.12, objectName: name });
}
function T(s, text, o) { s.addText(text, Object.assign({ fontFace: BF, color: INK, margin: 0, isTextBox: true, valign: "top" }, o)); }
function circleIcon(s, data, x, y, d, fill) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill, width: 0 }, objectName: "Icon circle" });
  s.addImage({ data, x: x + d * 0.25, y: y + d * 0.25, w: d * 0.5, h: d * 0.5, objectName: "Icon" });
}
function stat(s, x, y, w, big, label, color = PURPLE, fill = MIST) {
  card(s, x, y, w, 1.5, fill, "Stat card");
  T(s, big, { x: x + 0.2, y: y + 0.15, w: w - 0.4, h: 0.85, fontSize: 40, bold: true, color, fontFace: HF, valign: "middle" });
  T(s, label, { x: x + 0.2, y: y + 0.95, w: w - 0.4, h: 0.5, fontSize: 14, color: MUTED });
}
const AX = { catAxisLabelFontFace: BF, valAxisLabelFontFace: BF, catAxisLabelFontSize: 12, valAxisLabelFontSize: 12, catAxisLabelColor: MUTED, valAxisLabelColor: MUTED,
  valGridLine: { color: "E6E1F0", size: 0.75 }, catGridLine: { style: "none" }, dataLabelFontFace: BF, dataLabelFontSize: 11, dataLabelColor: INK,
  legendFontFace: BF, legendFontSize: 12, legendColor: MUTED, titleFontFace: BF, titleFontSize: 14, titleColor: INK };
function chart(s, type, data, o) { s.addChart(type, data, Object.assign({}, AX, o)); }
const f2 = (v) => (Math.round(v * 100) / 100).toFixed(2);
const nps = ["2", "4", "6", "8", "10", "12", "14"];
const M = D.timing.all, G = D.timing.gray, C = D.timing.color;

(async () => {
  const ic = {};
  const need = { db: fa.FaDatabase, net: fa.FaNetworkWired, bolt: fa.FaBolt, chip: fa.FaMicrochip, check: fa.FaCheckCircle, img: fa.FaImage, cogs: fa.FaCogs,
    bal: fa.FaBalanceScale, flask: fa.FaFlask, book: fa.FaBookOpen, rocket: fa.FaRocket, search: fa.FaSearch, hash: fa.FaFingerprint, lock: fa.FaLock, clock: fa.FaClock, layer: fa.FaLayerGroup, sync: fa.FaSyncAlt };
  for (const [k, v] of Object.entries(need)) { ic[k] = await icon(v, WHITE); }

  // ================= 1. Title =================
  {
    const s = pres.addSlide({ masterName: "TITLE_DARK" }); nSlide++;
    s.addShape(pres.shapes.OVAL, { x: 8.9, y: -1.6, w: 6.2, h: 6.2, fill: { color: PURPLE, transparency: 55 }, line: { color: PURPLE, width: 0 }, objectName: "Decor circle 1" });
    s.addShape(pres.shapes.OVAL, { x: 10.6, y: 3.4, w: 4.4, h: 4.4, fill: { color: MAG, transparency: 70 }, line: { color: MAG, width: 0 }, objectName: "Decor circle 2" });
    s.addImage({ path: A("logo.png"), x: 0.7, y: 0.55, w: 1.05, h: 1.1, objectName: "University logo" });
    T(s, "MSc SEMINAR", { x: 2.0, y: 0.8, w: 6, h: 0.4, fontSize: 14, bold: true, color: GOLD, charSpacing: 4 });
    T(s, "University of Babylon", { x: 2.0, y: 1.15, w: 6, h: 0.4, fontSize: 16, color: "D9D2EE" });
    T(s, "Parallel image compression using high-performance computing strategies", { x: 0.7, y: 2.2, w: 9.6, h: 1.95, fontSize: 38, bold: true, color: WHITE, fontFace: HF, valign: "top" });
    T(s, "LBG vector quantization · delta coding · Huffman · speed-aware MPI on a hybrid P/E-core CPU", { x: 0.7, y: 4.4, w: 9.6, h: 0.8, fontSize: 18, color: "D9D2EE" });
    T(s, [{ text: "Presented by  ", options: { color: LAV } }, { text: "MSc. Student Ibtihal Hussien", options: { bold: true, color: WHITE, breakLine: true } },
          { text: "Supervised by  ", options: { color: LAV } }, { text: "Dr. Ahmed Badri  ·  Dr. Esraa Hadi", options: { bold: true, color: WHITE } }],
      { x: 0.7, y: 5.55, w: 9, h: 0.9, fontSize: 16, paraSpaceAfter: 6 });
    s.addNotes("Introduce the topic: a parallel (MPI) LBG vector-quantization image compressor, evaluated on a hybrid CPU with 6 performance and 8 efficiency cores.");
  }

  // ================= 2. Outline =================
  {
    const s = cs("Agenda", "Outline",
      "Eight parts: introduction, literature review, problem statement, thesis objectives, proposed work, experimental results, conclusion and future work.");
    const items = ["Introduction", "Literature Review", "Problem Statement", "Thesis Objectives", "Proposed work",
      "Experimental Results", "Conclusion", "Future work"];
    items.forEach((it, i) => {
      const col = i < 4 ? 0 : 1, row = i < 4 ? i : i - 4;
      const x = 0.6 + col * 6.2, y = 1.75 + row * 1.2;
      card(s, x, y, 5.9, 1.0, MIST, "Agenda card");
      s.addShape(pres.shapes.DIAMOND, { x: x + 0.25, y: y + 0.28, w: 0.44, h: 0.44, fill: { color: GOLD }, line: { color: GOLD, width: 0 }, objectName: "Gold diamond" });
      T(s, String(i + 1), { x: x + 0.78, y: y + 0.1, w: 0.5, h: 0.8, fontSize: 22, bold: true, color: i % 2 ? MAG : PURPLE, valign: "middle", fontFace: HF });
      T(s, it, { x: x + 1.3, y: y + 0.1, w: 4.4, h: 0.8, fontSize: 22, bold: true, color: INK, valign: "middle" });
    });
  }

  // ================= 3. Why compress =================
  {
    const s = cs("1 · Introduction", "Why compress images, and how?",
      "Compression reduces storage and bandwidth. VQ is lossy; in this work the compressed size includes the codebook and the Huffman table, so the reported ratio is the real ratio.");
    const cards = [[ic.db, "Storage", "Large image collections need less space.", PURPLE], [ic.net, "Transmission", "Smaller files reach the receiver sooner.", MAG], [ic.bolt, "Computation", "Compression itself must be fast enough to use.", TEAL]];
    cards.forEach((c, i) => {
      const x = 0.6 + i * 4.15;
      card(s, x, 1.7, 3.85, 2.3, MIST, "Benefit card");
      circleIcon(s, c[0], x + 0.3, 1.95, 0.8, c[3]);
      T(s, c[1], { x: x + 0.3, y: 2.9, w: 3.3, h: 0.4, fontSize: 20, bold: true });
      T(s, c[2], { x: x + 0.3, y: 3.3, w: 3.3, h: 0.6, fontSize: 14, color: MUTED });
    });
    card(s, 0.6, 4.25, 6.0, 2.5, WHITE, "Lossless card"); s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 4.25, w: 6.0, h: 2.5, fill: { color: WHITE }, line: { color: LINE, width: 1.25 }, rectRadius: 0.12, objectName: "Lossless frame" });
    T(s, "Lossless", { x: 0.9, y: 4.4, w: 5.4, h: 0.4, fontSize: 20, bold: true, color: PURPLE });
    T(s, "Perfect reconstruction. Used for documents and archives: RLE, Huffman, LZW, BWT.", { x: 0.9, y: 4.9, w: 5.4, h: 1.6, fontSize: 18, color: MUTED });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.8, y: 4.25, w: 5.93, h: 2.5, fill: { color: WHITE }, line: { color: MAG, width: 1.75 }, rectRadius: 0.12, objectName: "Lossy frame" });
    T(s, "Lossy  (this work)", { x: 7.1, y: 4.4, w: 5.3, h: 0.4, fontSize: 20, bold: true, color: MAG });
    T(s, "Some data is discarded for a much smaller file: VQ, DCT, DWT, DPCM. Here: vector quantization + delta + Huffman.", { x: 7.1, y: 4.9, w: 5.3, h: 1.7, fontSize: 18, color: MUTED });
  }

  // ================= 4. Why parallelize LBG =================
  {
    const s = cs("1 · Introduction", "Why parallelize LBG codebook training?",
      "LBG is iterative: every iteration compares every training vector with every codeword. This is the dominant cost of the sequential compressor (about 77% of the total time for grayscale images).");
    stat(s, 0.6, 1.7, 2.95, "16,384", "training vectors per 512×512 image (4×4 blocks)", PURPLE);
    stat(s, 3.75, 1.7, 2.95, "64", "codewords, 16 dimensions each", MAG);
    stat(s, 6.9, 1.7, 2.95, "≈ 150", "Lloyd iterations (132–186 per gray image)", TEAL);
    stat(s, 10.05, 1.7, 2.68, "1.05 M", "distance evaluations per iteration at K = 64", GOLD);
    card(s, 0.6, 3.5, 12.13, 3.25, WHITE, "Message");
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 3.5, w: 12.13, h: 3.25, fill: { color: WHITE }, line: { color: LINE, width: 1.25 }, rectRadius: 0.12, objectName: "Message frame" });
    T(s, [{ text: "The assignment step is data-parallel", options: { bold: true, breakLine: true, fontSize: 20, color: PURPLE } },
      { text: "Each training vector is assigned independently; only the per-cluster sums and counts must be combined (one MPI_Allreduce per iteration).", options: { breakLine: true } },
      { text: " ", options: { breakLine: true, fontSize: 8 } },
      { text: "Sequential LBG ≈ 77% (gray) and 81% (color) of the total time", options: { bold: true, color: MAG, breakLine: true } },
      { text: "So accelerating LBG is the highest-value target, and the remaining stages (I/O, delta, Huffman, reconstruction) set the limit on total speedup.", options: {} }],
      { x: 0.95, y: 3.75, w: 11.4, h: 2.8, fontSize: 18, color: INK, paraSpaceAfter: 6 });
  }

  // ================= 5. Metrics =================
  {
    const s = cs("1 · Introduction", "Evaluation metrics",
      "System CR includes the codebook (1,024 bytes) and the Huffman table, so it is the true compression ratio. PSNR and SSIM measure fidelity. Speedup, efficiency, Karp–Flatt and throughput measure the parallel performance.");
    const rows = [
      ["Compression ratio", "CR = original bytes / (codebook + Huffman table + Huffman data)", PURPLE],
      ["PSNR", "10·log10(255² / MSE),  in dB", PURPLE],
      ["SSIM", "11×11 Gaussian window, σ = 1.5;  color = mean of 3 channels", PURPLE],
      ["Speedup  S", "S = T_seq / T_P", MAG],
      ["Efficiency  E", "E = S / P", MAG],
      ["Karp–Flatt  e", "e = (1/S − 1/P) / (1 − 1/P):  serial fraction", MAG],
      ["Throughput  Θ", "Θ = N · I / T_LBG  (vector-iterations per second)", MAG],
    ];
    rows.forEach((r, i) => {
      const y = 1.65 + i * 0.74;
      card(s, 0.6, y, 12.13, 0.62, MIST, "Metric row");
      s.addShape(pres.shapes.OVAL, { x: 0.78, y: y + 0.18, w: 0.26, h: 0.26, fill: { color: r[2] }, line: { color: r[2], width: 0 }, objectName: "Dot" });
      T(s, r[0], { x: 1.25, y, w: 2.9, h: 0.62, fontSize: 16, bold: true, valign: "middle" });
      T(s, r[1], { x: 4.2, y, w: 8.4, h: 0.62, fontSize: 16, color: MUTED, valign: "middle" });
    });
  }

  // ================= 6. Related work: compression =================
  {
    const s = cs("2 · Literature Review", "Literature review: image-compression studies",
      "These studies work at very different operating points: from near-lossless (CR about 1.5) to high compression. Values are taken from the papers' tables.");
    const h = { bold: true, color: WHITE, fill: { color: DEEP }, fontSize: 13, fontFace: BF, valign: "middle" };
    const c = (t, o = {}) => ({ text: t, options: Object.assign({ fontSize: 14, fontFace: BF, color: INK, valign: "middle" }, o) });
    const rows = [
      [{ text: "Study", options: h }, { text: "Method", options: h }, { text: "Reported result", options: h }, { text: "Observation", options: h }],
      [c("Thomas et al., 2025", { bold: true }), c("Integer DWT + reduction + Huffman"), c("Lena: CR 1.52, PSNR 54.28 dB, SSIM 0.9985"), c("Near-lossless; low CR; sequential")],
      [c("Ranjan & Kumar, 2023", { bold: true }), c("2D DWT + PCA + canonical Huffman"), c("Lena 512: CR 4.41, PSNR 34.78 dB"), c("Moderate CR; no parallelism")],
      [c("Bilal et al., 2024", { bold: true }), c("Fast LBG (FLBG), rescaling"), c("50.2% less complexity, 20% less memory"), c("Algorithmic speedup; sequential")],
      [c("Paul et al., 2024", { bold: true }), c("K-means + DWT (K-DWT)"), c("Kodak: CR 15.39, PSNR 30.51 dB, SSIM 0.8978"), c("No timing values reported")],
    ];
    s.addTable(rows, { x: 0.6, y: 1.7, w: 12.13, colW: [2.4, 3.3, 3.5, 2.93], rowH: [0.45, 0.8, 0.8, 0.8, 0.8], border: { type: "solid", pt: 0.75, color: LINE },
      fill: { color: WHITE }, autoPage: false, margin: [0.05, 0.12, 0.05, 0.12] });
    card(s, 0.6, 5.85, 12.13, 0.95, MIST, "Takeaway");
    T(s, "Takeaway: published compression studies are sequential and span very different rate–distortion regimes (CR from 1.4 to 15).", { x: 0.9, y: 5.85, w: 11.5, h: 0.95, fontSize: 16, bold: true, color: PURPLE, valign: "middle" });
  }

  // ================= 7. Related work: parallel =================
  {
    const s = cs("2 · Literature Review", "Literature review: parallel studies",
      "Speedups come from different applications and baselines, so they are context, not a ranking. Papakyriakou uses the two-process run as baseline. Zangana's 9.09x is derived from the 1-GPU and 16-GPU times.");
    const h = { bold: true, color: WHITE, fill: { color: DEEP }, fontSize: 13, fontFace: BF, valign: "middle" };
    const c = (t, o = {}) => ({ text: t, options: Object.assign({ fontSize: 14, fontFace: BF, color: INK, valign: "middle" }, o) });
    const rows = [
      [{ text: "Study", options: h }, { text: "Application", options: h }, { text: "Resources", options: h }, { text: "Speedup (baseline)", options: h }],
      [c("Tanović et al., 2024", { bold: true }), c("Parallel k-means, image classification"), c("12 cores, OpenMP + MPI"), c("up to 10.2× (not stated in abstract)")],
      [c("Papakyriakou et al., 2025", { bold: true }), c("MPI k-means, 75 M synthetic points"), c("2–48 MPI processes, Raspberry Pi"), c("≈10.05× (vs 2 processes)")],
      [c("Bystrov et al., 2023", { bold: true }), c("Discrete-element simulation"), c("8 heterogeneous containers"), c("up to 6.0× (vs sequential)")],
      [c("Zangana, 2025", { bold: true }), c("Hybrid image compression (bitplane + DWT + predictive)"), c("1–16 GPUs, CUDA / OpenCL"), c("9.09× at 16 GPUs (vs 1 GPU)")],
    ];
    s.addTable(rows, { x: 0.6, y: 1.7, w: 12.13, colW: [2.7, 3.7, 3.0, 2.73], rowH: [0.45, 0.8, 0.8, 0.8, 0.8], border: { type: "solid", pt: 0.75, color: LINE },
      fill: { color: WHITE }, autoPage: false, margin: [0.05, 0.12, 0.05, 0.12] });
    card(s, 0.6, 5.85, 12.13, 0.95, MIST, "Takeaway");
    T(s, "Takeaway: reported speedups are 6–10×, but none parallelizes LBG codebook training for image compression with speed-aware distribution.", { x: 0.9, y: 5.85, w: 11.5, h: 0.95, fontSize: 16, bold: true, color: PURPLE, valign: "middle" });
  }

  // ================= Research problems =================
  {
    const s = cs("3 · Problem Statement", "Problem Statement",
      "Four problems motivate the work: delay in sending data, big data storage, the cost of obtaining a good compression ratio, and the need for acceptable quality.");
    const probs = [[ic.clock, "Delay in sending data", "Large images take a long time to transmit over a network.", PURPLE],
      [ic.db, "Big data storage", "Image collections need a large amount of storage.", MAG],
      [ic.cogs, "Complexity versus time", "A good compression ratio needs complex methods (here: iterative LBG training), so execution time becomes high.", TEAL],
      [ic.img, "Acceptable quality", "The reconstructed image must remain of acceptable quality (PSNR, SSIM).", GOLD]];
    probs.forEach((p, i) => {
      const x = 0.6 + (i % 2) * 6.15, y = 1.7 + Math.floor(i / 2) * 2.6;
      card(s, x, y, 5.95, 2.4, MIST, "Problem card");
      s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: y + 0.35, w: 0.85, h: 0.85, fill: { color: p[3] }, line: { color: p[3], width: 0 }, objectName: "Icon circle" });
      s.addImage({ data: p[0], x: x + 0.3 + 0.21, y: y + 0.35 + 0.21, w: 0.43, h: 0.43, objectName: "Icon" });
      T(s, (i + 1) + "  " + p[1], { x: x + 1.4, y: y + 0.3, w: 4.35, h: 0.6, fontSize: 20, bold: true });
      T(s, p[2], { x: x + 1.4, y: y + 0.95, w: 4.35, h: 1.3, fontSize: 16, color: MUTED });
    });
  }

  // ================= Research objective =================
  {
    const s = cs("4 · Thesis Objectives", "Thesis Objectives",
      "Two objectives: a good compression ratio with parallel speed, and preserved quality. The right-hand column shows how the work meets each one.");
    const objs = [["Develop an image-compression method with a good compression ratio, using parallel processing to reduce its execution time.",
        "LBG vector quantization + delta + Huffman coding, parallelized with MPI (Equal and speed-aware Adaptive distribution)."],
      ["Maintain the quality of the reconstructed image as much as possible.",
        "Quality measured by PSNR and SSIM; the parallel result is verified to be identical to the sequential one (MD5)."]];
    objs.forEach((o, i) => {
      const y = 1.7 + i * 2.6;
      card(s, 0.6, y, 6.6, 2.4, MIST, "Objective card");
      s.addShape(pres.shapes.OVAL, { x: 0.85, y: y + 0.35, w: 0.7, h: 0.7, fill: { color: i ? MAG : PURPLE }, line: { color: WHITE, width: 0 }, objectName: "Objective number" });
      T(s, String(i + 1), { x: 0.85, y: y + 0.35, w: 0.7, h: 0.7, fontSize: 24, bold: true, color: WHITE, align: "center", valign: "middle", fontFace: HF });
      T(s, "Objective", { x: 1.8, y: y + 0.3, w: 5.2, h: 0.4, fontSize: 14, bold: true, color: i ? MAG : PURPLE, charSpacing: 2 });
      T(s, o[0], { x: 1.8, y: y + 0.75, w: 5.2, h: 1.5, fontSize: 17, valign: "top" });
      s.addShape(pres.shapes.RIGHT_ARROW, { x: 7.35, y: y + 0.95, w: 0.5, h: 0.5, fill: { color: LAV }, line: { color: LAV, width: 0 }, objectName: "Arrow" });
      card(s, 8.0, y, 4.73, 2.4, WHITE, "How card");
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.0, y, w: 4.73, h: 2.4, fill: { color: WHITE }, line: { color: i ? MAG : PURPLE, width: 1.5 }, rectRadius: 0.12, objectName: "How frame" });
      T(s, "How this work meets it", { x: 8.25, y: y + 0.2, w: 4.3, h: 0.4, fontSize: 14, bold: true, color: i ? MAG : PURPLE });
      T(s, o[1], { x: 8.25, y: y + 0.7, w: 4.3, h: 1.6, fontSize: 15, color: INK });
    });
  }

  // ================= 9. Contributions =================
  {
    const s = cs("4 · Thesis Objectives", "What this work contributes",
      "Four contributions: the pipeline, the parallel implementation, the Adaptive distribution for hybrid CPUs, and the measurement and verification methodology.");
    const cc = [[ic.layer, "Compression pipeline", "4×4 blocks → LBG (K = 64) → delta → Huffman; system CR counts every byte.", PURPLE],
      [ic.net, "MPI parallel LBG", "Scatterv + Allreduce SPMD design, exact and independent of process count.", MAG],
      [ic.bal, "Speed-aware distribution", "Adaptive vector allocation for P-cores and E-cores; 17–28% faster LBG than Equal at P = 8–14.", TEAL],
      [ic.check, "Rigorous evaluation", "Median of 5, CPU binding, Karp–Flatt, throughput, and MD5-verified equivalence.", GOLD]];
    cc.forEach((c, i) => {
      const x = 0.6 + (i % 2) * 6.15, y = 1.7 + Math.floor(i / 2) * 2.6;
      card(s, x, y, 5.95, 2.4, MIST, "Contribution card");
      circleIcon(s, c[0], x + 0.3, y + 0.35, 0.85, c[3]);
      T(s, c[1], { x: x + 1.4, y: y + 0.3, w: 4.3, h: 0.5, fontSize: 20, bold: true });
      T(s, c[2], { x: x + 1.4, y: y + 0.85, w: 4.3, h: 1.4, fontSize: 15, color: MUTED });
    });
  }

  // ================= 10. Pipeline =================
  {
    const s = cs("5 · Proposed work", "Compression pipeline",
      "The image is split into 4x4 blocks, each block is a 16-dimensional vector. LBG builds a 64-vector codebook. Each block is replaced by an index, the index sequence is delta-coded and Huffman-coded.");
    const steps = [["Image", "512×512\n8-bit"], ["4×4 blocks", "16,384 vectors\n16-D"], ["LBG-VQ", "codebook K = 64"], ["Index map", "one label\nper block"], ["Delta coding", "offset 128"], ["Huffman", "entropy code"], ["Bitstream", "data + table\n+ codebook"]];
    const w = 1.62, gap = 0.13;
    steps.forEach((st, i) => {
      const x = 0.6 + i * (w + gap), col = i === 2 ? MAG : (i % 2 ? PURPLE : DEEP);
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 2.3, w, h: 1.9, fill: { color: col }, line: { color: col, width: 0 }, rectRadius: 0.12, objectName: "Pipeline step " + (i + 1) });
      T(s, st[0], { x: x + 0.08, y: 2.45, w: w - 0.16, h: 0.55, fontSize: 16, bold: true, color: WHITE, align: "center", valign: "middle" });
      T(s, st[1], { x: x + 0.08, y: 3.1, w: w - 0.16, h: 1.0, fontSize: 13, color: "E9E3F7", align: "center", valign: "top" });
    });
    card(s, 0.6, 4.7, 5.9, 2.05, MIST, "Encoder card");
    T(s, "Encoder", { x: 0.9, y: 4.85, w: 5.3, h: 0.4, fontSize: 18, bold: true, color: PURPLE });
    T(s, "The expensive step is LBG training: that is the stage parallelized with MPI. Delta and Huffman run on rank 0.", { x: 0.9, y: 5.3, w: 5.3, h: 1.3, fontSize: 15, color: MUTED });
    card(s, 6.83, 4.7, 5.9, 2.05, MIST, "Decoder card");
    T(s, "Decoder", { x: 7.13, y: 4.85, w: 5.3, h: 0.4, fontSize: 18, bold: true, color: MAG });
    T(s, "Huffman decode → undo delta → look up each index in the codebook → rebuild the 4×4 blocks.", { x: 7.13, y: 5.3, w: 5.3, h: 1.3, fontSize: 15, color: MUTED });
  }

  // ================= 11. Blocks and VQ (image) =================
  {
    const s = cs("5 · Proposed work", "From pixels to 16-dimensional vectors",
      "Zoom on a Cameraman region: the image is a grid of 4x4 blocks; each block becomes one vector and later one codeword index.");
    s.addImage({ path: A("cam_orig_zoom.png"), x: 0.6, y: 1.65, w: 4.6, h: 4.6, objectName: "Cameraman zoom" });
    // 4x4 block grid overlay: crop is 96 px -> 24 blocks across 4.6in => each block 0.1917in
    const bw = 4.6 / 24;
    for (let i = 0; i <= 24; i += 4) {
      s.addShape(pres.shapes.LINE, { x: 0.6 + i * bw, y: 1.65, w: 0, h: 4.6, line: { color: WHITE, width: 0.5, transparency: 40 }, objectName: "Grid v" });
      s.addShape(pres.shapes.LINE, { x: 0.6, y: 1.65 + i * bw, w: 4.6, h: 0, line: { color: WHITE, width: 0.5, transparency: 40 }, objectName: "Grid h" });
    }
    s.addShape(pres.shapes.RECTANGLE, { x: 0.6 + 8 * bw, y: 1.65 + 8 * bw, w: 4 * bw, h: 4 * bw, fill: { color: MAG, transparency: 100 }, line: { color: MAG, width: 2.5 }, objectName: "Highlighted block" });
    T(s, "96×96 region of Cameraman, with the 4×4 block grid", { x: 0.6, y: 6.32, w: 4.6, h: 0.5, fontSize: 12, color: MUTED });
    s.addShape(pres.shapes.RIGHT_ARROW, { x: 5.45, y: 3.6, w: 0.9, h: 0.55, fill: { color: LAV }, line: { color: LAV, width: 0 }, objectName: "Arrow" });
    card(s, 6.6, 1.65, 6.13, 2.35, MIST, "Vector card");
    T(s, "One block = one vector", { x: 6.9, y: 1.8, w: 5.5, h: 0.4, fontSize: 18, bold: true, color: MAG });
    T(s, "x = (p₁, p₂, …, p₁₆)  with 16 pixel values 0…255", { x: 6.9, y: 2.3, w: 5.5, h: 0.5, fontSize: 16 });
    T(s, "A 512×512 image gives 16,384 training vectors.", { x: 6.9, y: 2.9, w: 5.5, h: 0.9, fontSize: 15, color: MUTED });
    card(s, 6.6, 4.25, 6.13, 2.5, MIST, "Codebook card");
    T(s, "Vector quantization", { x: 6.9, y: 4.4, w: 5.5, h: 0.4, fontSize: 18, bold: true, color: PURPLE });
    T(s, "Each vector is replaced by the index of its nearest codeword. With K = 64 the codebook costs only 64 × 16 = 1,024 bytes, and each index needs at most 6 bits before entropy coding.", { x: 6.9, y: 4.9, w: 5.5, h: 1.7, fontSize: 15, color: MUTED });
  }

  // ================= 12. LBG algorithm =================
  {
    const s = cs("5 · Proposed work", "LBG: splitting + Lloyd iterations",
      "Start from the global mean; split every codeword by a factor (1 plus or minus delta), then run Lloyd iterations until the relative distortion change is below epsilon. Repeat until K = 64.");
    const ks = ["1", "2", "4", "8", "16", "32", "64"];
    ks.forEach((k, i) => {
      const x = 0.6 + i * 1.76, last = i === 6;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.75, w: 1.5, h: 1.0, fill: { color: last ? MAG : PURPLE }, line: { color: WHITE, width: 0 }, rectRadius: 0.1, objectName: "Codebook size " + k });
      T(s, "K = " + k, { x, y: 1.75, w: 1.5, h: 1.0, fontSize: 20, bold: true, color: WHITE, align: "center", valign: "middle", fontFace: HF });
      if (i < 6) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 1.52, y: 2.07, w: 0.24, h: 0.36, fill: { color: LAV }, line: { color: LAV, width: 0 }, objectName: "Split arrow" });
    });
    T(s, "split  ×2  →  Lloyd until convergence  →  split again", { x: 0.6, y: 2.85, w: 12, h: 0.35, fontSize: 14, color: MUTED, italic: true });
    const steps = [["1  Split", "Each codeword c → c(1+δ) and c(1−δ),  δ = 0.01"], ["2  Assign", "Every vector goes to its nearest codeword (squared Euclidean distance)"], ["3  Update", "Each codeword becomes the mean of its assigned vectors"], ["4  Test", "Stop when |ΔD| / D ≤ ε = 10⁻⁴ or after 100 iterations"]];
    steps.forEach((st, i) => {
      const x = 0.6 + (i % 2) * 6.15, y = 3.45 + Math.floor(i / 2) * 1.65;
      card(s, x, y, 5.95, 1.45, MIST, "Step card");
      T(s, st[0], { x: x + 0.3, y: y + 0.15, w: 5.3, h: 0.4, fontSize: 18, bold: true, color: i === 1 ? MAG : PURPLE });
      T(s, st[1], { x: x + 0.3, y: y + 0.6, w: 5.3, h: 0.8, fontSize: 15, color: MUTED });
    });
    T(s, "Typical run: about 150 Lloyd iterations in total over the six stages.", { x: 0.6, y: 6.72, w: 10, h: 0.3, fontSize: 12, color: MUTED });
  }

  // ================= 13. Delta + Huffman (entropy chart) =================
  {
    const s = cs("5 · Proposed work", "Delta coding lowers the entropy of the indices",
      "LBG orders codewords so that neighbouring blocks tend to have close indices; coding the difference between consecutive indices lowers the entropy. Huffman coding then reaches within about 0.04 bit of the entropy.");
    const lab = ["Lena", "Boat", "Cameraman", "Peppers"];
    chart(s, pres.charts.BAR, [{ name: "Entropy of indices", labels: lab, values: D.ent.map((e) => +e.H_index_bits) }, { name: "Entropy after delta", labels: lab, values: D.ent.map((e) => +e.H_delta_bits) }],
      { x: 0.6, y: 1.65, w: 7.6, h: 4.9, barDir: "col", chartColors: [LAV, MAG], showLegend: true, legendPos: "b", showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00",
        valAxisMinVal: 0, valAxisMaxVal: 6, valAxisTitle: "bits per index", showValAxisTitle: true, valAxisTitleFontSize: 12, valAxisTitleColor: MUTED, barGapWidthPct: 60 });
    card(s, 8.5, 1.65, 4.23, 2.3, MIST, "Mean card");
    T(s, "5.30 → 4.19", { x: 8.75, y: 1.8, w: 3.8, h: 0.9, fontSize: 36, bold: true, color: MAG, fontFace: HF });
    T(s, "mean entropy in bits per index (grayscale), a 1.1-bit reduction.", { x: 8.75, y: 2.75, w: 3.8, h: 1.1, fontSize: 15, color: MUTED });
    card(s, 8.5, 4.2, 4.23, 2.35, MIST, "Huffman card");
    T(s, "4.23 bits/index", { x: 8.75, y: 4.35, w: 3.8, h: 0.6, fontSize: 26, bold: true, color: PURPLE, fontFace: HF });
    T(s, "Huffman rate, only 0.039 bit above the entropy: 29.5% less than fixed 6-bit indices.", { x: 8.75, y: 5.0, w: 3.8, h: 1.45, fontSize: 15, color: MUTED });
  }

  // ================= 14. System CR accounting =================
  {
    const s = cs("5 · Proposed work", "System compression ratio: every byte counted",
      "The system CR divides the original bytes by codebook (1,024 bytes) + Huffman table + Huffman data. Delta + Huffman raises the ratio from 15.06 (8-bit indices) to 25.92 on average.");
    chart(s, pres.charts.BAR, [{ name: "System CR", labels: ["Fixed 8-bit indices", "Fixed 6-bit indices", "Delta + Huffman"], values: [15.06, 19.69, 25.92] }],
      { x: 0.6, y: 1.65, w: 6.9, h: 4.9, barDir: "col", chartColors: [LAV, PURPLE, MAG], showLegend: false, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelFontSize: 14, dataLabelFontBold: true,
        valAxisMinVal: 0, valAxisMaxVal: 30, barGapWidthPct: 50, showTitle: true, title: "Mean over the four grayscale images", titleFontSize: 14, valAxisTitle: "CR", showValAxisTitle: true, valAxisTitleColor: MUTED, valAxisTitleFontSize: 12 });
    stat(s, 7.85, 1.65, 4.88, "+31.6%", "gain of delta + Huffman over 6-bit indices", MAG);
    card(s, 7.85, 3.4, 4.88, 3.15, MIST, "Accounting");
    T(s, [{ text: "Compressed size counts:", options: { bold: true, color: PURPLE, breakLine: true } },
      { text: "codebook: 64 × 16 = 1,024 bytes", options: { bullet: true, breakLine: true } },
      { text: "Huffman table: 4 bytes per used symbol", options: { bullet: true, breakLine: true } },
      { text: "Huffman-coded index data", options: { bullet: true } }], { x: 8.1, y: 3.55, w: 4.4, h: 2.0, fontSize: 15, paraSpaceAfter: 6 });
    T(s, "CR is computed from these sizes; the program does not write a stored file. A 5-byte table entry would lower CR by about 1%.", { x: 8.1, y: 5.5, w: 4.4, h: 0.95, fontSize: 12, color: MUTED, italic: true });
  }

  // ================= 15. Test images and protocol =================
  {
    const s = cs("5 · Proposed work", "Test images",
      "Eight 512x512 images: four grayscale (Lena, Boat, Cameraman, Peppers) and four color (Lena, Peppers, F-16, Gold Hill). Color images are processed per R, G, B channel. Thumbnails shown here are the images available for this deck.");
    const th = [["t_lena.png", "Lena"], ["t_cam.png", "Cameraman"], ["t_pep.png", "Peppers"], ["t_f16.png", "F-16"], ["t_gold.png", "Gold Hill"]];
    th.forEach((t, i) => {
      const x = 0.6 + i * 2.45;
      s.addImage({ path: A(t[0]), x, y: 1.7, w: 2.25, h: 2.25, objectName: "Thumbnail " + t[1] });
      T(s, t[1], { x, y: 4.02, w: 2.25, h: 0.35, fontSize: 14, bold: true, align: "center" });
    });
    card(s, 0.6, 4.7, 5.95, 2.05, MIST, "Gray card");
    T(s, "Grayscale (4)", { x: 0.9, y: 4.85, w: 5.4, h: 0.4, fontSize: 18, bold: true, color: PURPLE });
    T(s, "Lena, Boat, Cameraman, Peppers: 1 byte per pixel, 16,384 vectors.", { x: 0.9, y: 5.3, w: 5.4, h: 1.3, fontSize: 15, color: MUTED });
    card(s, 6.78, 4.7, 5.95, 2.05, MIST, "Color card");
    T(s, "Color (4)", { x: 7.08, y: 4.85, w: 5.4, h: 0.4, fontSize: 18, bold: true, color: MAG });
    T(s, "Lena, Peppers, F-16, Gold Hill: R, G, B coded as three independent channels, CR and MSE pooled.", { x: 7.08, y: 5.3, w: 5.4, h: 1.3, fontSize: 15, color: MUTED });
  }

  // ================= 16. MPI design =================
  {
    const s = cs("5 · Proposed work", "MPI design: SPMD with one Allreduce per iteration",
      "Rank 0 reads the image and builds the vectors, then broadcasts parameters and scatters the vectors. Every iteration: assign locally, Allreduce the partial sums and counts, update the codebook. Finally the labels are gathered on rank 0 for delta and Huffman coding.");
    const boxes = [["Rank 0", "read image,\nbuild vectors", DEEP], ["Bcast + Scatterv", "parameters,\nvector blocks", PURPLE], ["Local assign", "nearest codeword,\npartial sums", MAG], ["Allreduce", "sums + counts\n(double)", TEAL], ["Update", "new codebook\non every rank", PURPLE], ["Gatherv", "labels to rank 0", DEEP]];
    const w = 1.85, gap = 0.2;
    boxes.forEach((b, i) => {
      const x = 0.6 + i * (w + gap);
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.85, w, h: 1.75, fill: { color: b[2] }, line: { color: b[2], width: 0 }, rectRadius: 0.12, objectName: "MPI step " + (i + 1) });
      T(s, b[0], { x: x + 0.05, y: 1.95, w: w - 0.1, h: 0.55, fontSize: 15, bold: true, color: WHITE, align: "center", valign: "middle" });
      T(s, b[1], { x: x + 0.05, y: 2.55, w: w - 0.1, h: 0.95, fontSize: 13, color: "E9E3F7", align: "center" });
      if (i < 5) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + w + 0.02, y: 2.55, w: 0.16, h: 0.3, fill: { color: LAV }, line: { color: LAV, width: 0 }, objectName: "Arrow" });
    });
    s.addShape(pres.shapes.RECTANGLE, { x: 5.9, y: 3.75, w: 3.95, h: 0.0, line: { color: MAG, width: 1.5, dashType: "dash" }, objectName: "Loop line" });
    T(s, "loop: repeat until converged", { x: 5.9, y: 3.8, w: 3.95, h: 0.35, fontSize: 13, color: MAG, bold: true, align: "center" });
    card(s, 0.6, 4.4, 5.95, 2.35, MIST, "Why exact");
    T(s, "Why the result does not depend on P", { x: 0.9, y: 4.55, w: 5.4, h: 0.4, fontSize: 18, bold: true, color: PURPLE });
    T(s, "Training vectors are integers 0…255, so sums and counts are exact in double precision and independent of summation order. The iteration count was the same for every P.", { x: 0.9, y: 5.05, w: 5.4, h: 1.6, fontSize: 15, color: MUTED });
    card(s, 6.78, 4.4, 5.95, 2.35, MIST, "Non-parallel");
    T(s, "What stays on rank 0", { x: 7.08, y: 4.55, w: 5.4, h: 0.4, fontSize: 18, bold: true, color: MAG });
    T(s, "Image I/O, delta coding, Huffman, reconstruction and metrics. These stages limit the total speedup (Amdahl).", { x: 7.08, y: 5.05, w: 5.4, h: 1.6, fontSize: 15, color: MUTED });
  }

  // ================= 17. Equal vs Adaptive =================
  {
    const s = cs("5 · Proposed work", "Equal vs Adaptive workload distribution",
      "On a hybrid CPU, equal shares make P-cores wait for the slower E-cores at every Allreduce. Adaptive measures each rank's speed with a micro-benchmark and gives faster ranks more vectors, so all ranks finish together.");
    // schematic bars
    const draw = (x0, title, shares, colr) => {
      T(s, title, { x: x0, y: 1.7, w: 5.9, h: 0.4, fontSize: 20, bold: true, color: colr });
      shares.forEach((sh, i) => {
        const y = 2.3 + i * 0.62, P = i < 2;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x0 + 1.2, y, w: sh, h: 0.44, fill: { color: P ? PURPLE : LAV }, line: { color: WHITE, width: 0 }, rectRadius: 0.06, objectName: "Share bar" });
        T(s, P ? "P-core rank" : "E-core rank", { x: x0, y, w: 1.15, h: 0.44, fontSize: 12, color: MUTED, valign: "middle" });
      });
    };
    draw(0.6, "Equal", [3.6, 3.6, 3.6, 3.6], MUTED);
    draw(6.83, "Adaptive (speed-weighted)", [4.2, 4.2, 3.0, 3.0], MAG);
    T(s, "schematic: share of training vectors per rank", { x: 0.6, y: 4.85, w: 6, h: 0.3, fontSize: 11, color: MUTED, italic: true });
    card(s, 0.6, 5.2, 5.95, 1.55, MIST, "Equal card");
    T(s, "Equal  (default for P ≤ 4)", { x: 0.9, y: 5.3, w: 5.4, h: 0.4, fontSize: 17, bold: true, color: MUTED });
    T(s, "Each rank gets N/P vectors. Simple, but the slowest rank sets the pace.", { x: 0.9, y: 5.75, w: 5.4, h: 0.9, fontSize: 14, color: MUTED });
    card(s, 6.83, 5.2, 5.9, 1.55, MIST, "Adaptive card");
    T(s, "Adaptive  (default for P > 4)", { x: 7.13, y: 5.3, w: 5.4, h: 0.4, fontSize: 17, bold: true, color: MAG });
    T(s, "calibrate_speed() times a short kernel on each rank; shares are proportional to measured speed.", { x: 7.13, y: 5.75, w: 5.4, h: 0.9, fontSize: 14, color: MUTED });
  }

  // ================= 18. Platform and protocol =================
  {
    const s = cs("5 · Proposed work", "Platform and measurement protocol",
      "All timings are medians of five runs under identical conditions. The sequential reference program is pinned to one core, so speedup is relative to a separate sequential implementation.");
    stat(s, 0.6, 1.7, 3.9, "6 P + 8 E", "Intel Core i7-13650HX: 14 cores, hybrid", PURPLE);
    stat(s, 4.7, 1.7, 3.9, "P = 2 … 14", "MPI processes, Open MPI, one per core", MAG);
    stat(s, 8.8, 1.7, 3.93, "Median of 5", "runs per configuration and image", TEAL);
    const rows = [[ic.chip, "CPU governor: performance, AC power", PURPLE], [ic.search, "mpirun --bind-to core: one rank per core", MAG], [ic.clock, "Sequential program pinned to CPU 6", TEAL], [ic.cogs, "gcc / mpicc -O2; LBG time excludes calibration, Total includes it", GOLD]];
    rows.forEach((r, i) => {
      const x = 0.6 + (i % 2) * 6.15, y = 3.6 + Math.floor(i / 2) * 1.6;
      card(s, x, y, 5.95, 1.4, MIST, "Protocol card");
      circleIcon(s, r[0], x + 0.25, y + 0.3, 0.8, r[2]);
      T(s, r[1], { x: x + 1.3, y: y + 0.1, w: 4.45, h: 1.2, fontSize: 16, valign: "middle" });
    });
  }

  // ================= 19. Verification =================
  {
    const s = cs("5 · Proposed work", "Verification: parallel = sequential",
      "For every image the sequential program and three parallel runs (P=4, P=14 Adaptive, P=14 Equal) give identical CR, MSE, PSNR, SSIM and iteration count, and the md5sum of the reconstructed BMP files is identical. md5sum is an external tool, not part of the algorithm. The check covers the reconstructed image and metrics, not the codebook or bitstream directly.");
    const g = (t) => ({ text: t, options: { bold: true, color: WHITE, fill: { color: DEEP }, fontSize: 13, align: "center", valign: "middle" } });
    const rows = [[g("Run"), g("Processes"), g("Strategy")],
      ...[["1  Sequential reference", "1", "–"], ["2  Parallel", "4", "Equal (default)"], ["3  Parallel", "14", "Adaptive (default)"], ["4  Parallel", "14", "Equal (forced)"]].map((r) => r.map((t, i) => ({ text: t, options: { fontSize: 14, align: i ? "center" : "left", valign: "middle", color: INK } })))];
    s.addTable(rows, { x: 0.6, y: 1.75, w: 6.5, colW: [3.3, 1.4, 1.8], rowH: [0.5, 0.6, 0.6, 0.6, 0.6], border: { type: "solid", pt: 0.75, color: LINE }, fill: { color: WHITE }, autoPage: false });
    stat(s, 7.5, 1.75, 5.23, "8 / 8", "images with identical metrics and identical MD5", MAG);
    stat(s, 7.5, 3.45, 5.23, "same iterations", "LBG iteration count constant for every P", TEAL);
    card(s, 0.6, 5.0, 12.13, 1.75, MIST, "Claim");
    T(s, [{ text: "Scope of the claim", options: { bold: true, color: PURPLE, breakLine: true, fontSize: 17 } },
      { text: "Compared: CR, MSE, PSNR, SSIM, iterations and the MD5 of the reconstructed BMP (external md5sum tool). The codebooks and bitstreams were not compared directly, so equivalence is stated for the tested configurations.", options: {} }],
      { x: 0.9, y: 5.1, w: 11.5, h: 1.55, fontSize: 15, color: MUTED, paraSpaceAfter: 4 });
  }

  // ================= 20. Parameter study =================
  {
    const s = cs("6 · Experimental Results", "Parameter study: block size and codebook size",
      "Mean over the four grayscale images. Larger blocks and smaller codebooks give higher compression and lower quality. 4x4 with K=64 is the chosen balance.");
    const order = ["2x2/K64", "4x4/K128", "4x4/K64", "4x4/K32", "8x8/K64"];
    const lab = order.map((k) => k.replace("/", " "));
    chart(s, pres.charts.BAR, [{ name: "CR", labels: lab, values: order.map((k) => D.param[k][0]) }],
      { x: 0.6, y: 1.65, w: 6.0, h: 4.4, barDir: "col", chartColors: [MAG], showLegend: false, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", valAxisMinVal: 0, valAxisMaxVal: 45,
        showTitle: true, title: "System compression ratio", barGapWidthPct: 45 });
    chart(s, pres.charts.BAR, [{ name: "PSNR", labels: lab, values: order.map((k) => D.param[k][1]) }],
      { x: 6.73, y: 1.65, w: 6.0, h: 4.4, barDir: "col", chartColors: [PURPLE], showLegend: false, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", valAxisMinVal: 20, valAxisMaxVal: 36,
        showTitle: true, title: "PSNR (dB)", barGapWidthPct: 45 });
    card(s, 0.6, 6.15, 12.13, 0.65, MIST, "Takeaway");
    T(s, "4×4 / K = 64: CR 25.9, PSNR 29.5 dB. The trade-off is monotonic: more compression, less fidelity.", { x: 0.9, y: 6.15, w: 11.5, h: 0.65, fontSize: 15, bold: true, color: PURPLE, valign: "middle" });
  }

  // ================= 21. Grayscale results =================
  {
    const s = cs("6 · Experimental Results", "Grayscale results (4×4 blocks, K = 64)",
      "Per-image system CR and PSNR for the four grayscale images; mean CR 25.92, PSNR 29.49 dB, SSIM 0.8266.");
    const g = D.corr.filter((r) => r.mode === "gray"); const lab = ["Lena", "Boat", "Cameraman", "Peppers"];
    chart(s, pres.charts.BAR, [{ name: "CR", labels: lab, values: g.map((r) => r.cr) }],
      { x: 0.6, y: 1.65, w: 4.0, h: 3.6, barDir: "col", chartColors: [MAG], showLegend: false, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", valAxisMinVal: 0, valAxisMaxVal: 35, showTitle: true, title: "CR", barGapWidthPct: 40 });
    chart(s, pres.charts.BAR, [{ name: "PSNR", labels: lab, values: g.map((r) => r.psnr) }],
      { x: 4.67, y: 1.65, w: 4.0, h: 3.6, barDir: "col", chartColors: [PURPLE], showLegend: false, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", valAxisMinVal: 20, valAxisMaxVal: 33, showTitle: true, title: "PSNR (dB)", barGapWidthPct: 40 });
    chart(s, pres.charts.BAR, [{ name: "SSIM", labels: lab, values: g.map((r) => r.ssim) }],
      { x: 8.74, y: 1.65, w: 4.0, h: 3.6, barDir: "col", chartColors: [TEAL], showLegend: false, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000", valAxisMinVal: 0.6, valAxisMaxVal: 1, showTitle: true, title: "SSIM", barGapWidthPct: 40 });
    stat(s, 0.6, 5.4, 3.9, "25.92", "mean system CR", MAG); stat(s, 4.7, 5.4, 3.9, "29.49 dB", "mean PSNR", PURPLE); stat(s, 8.8, 5.4, 3.93, "0.8266", "mean SSIM", TEAL);
  }

  // ================= 22. Color results =================
  {
    const s = cs("6 · Experimental Results", "Color results (R, G, B coded independently)",
      "Per-image values for the four color images; mean CR 24.47, PSNR 28.80 dB, SSIM 0.7654. CR and MSE are pooled over the three channels; SSIM is the mean of the three channel SSIMs.");
    const g = D.corr.filter((r) => r.mode === "color"); const lab = ["Lena", "Peppers", "F-16", "Gold Hill"];
    chart(s, pres.charts.BAR, [{ name: "CR", labels: lab, values: g.map((r) => r.cr) }],
      { x: 0.6, y: 1.65, w: 4.0, h: 3.6, barDir: "col", chartColors: [MAG], showLegend: false, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", valAxisMinVal: 0, valAxisMaxVal: 35, showTitle: true, title: "CR", barGapWidthPct: 40 });
    chart(s, pres.charts.BAR, [{ name: "PSNR", labels: lab, values: g.map((r) => r.psnr) }],
      { x: 4.67, y: 1.65, w: 4.0, h: 3.6, barDir: "col", chartColors: [PURPLE], showLegend: false, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", valAxisMinVal: 20, valAxisMaxVal: 33, showTitle: true, title: "PSNR (dB)", barGapWidthPct: 40 });
    chart(s, pres.charts.BAR, [{ name: "SSIM", labels: lab, values: g.map((r) => r.ssim) }],
      { x: 8.74, y: 1.65, w: 4.0, h: 3.6, barDir: "col", chartColors: [TEAL], showLegend: false, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000", valAxisMinVal: 0.5, valAxisMaxVal: 1, showTitle: true, title: "SSIM", barGapWidthPct: 40 });
    stat(s, 0.6, 5.4, 3.9, "24.47", "mean system CR", MAG); stat(s, 4.7, 5.4, 3.9, "28.80 dB", "mean PSNR", PURPLE); stat(s, 8.8, 5.4, 3.93, "0.7654", "mean SSIM", TEAL);
  }

  // ================= 23. Visual result =================
  {
    const s = cs("6 · Experimental Results", "Visual result: Cameraman",
      "Reconstruction by the sequential program: CR 28.88, MSE 68.84, PSNR 29.75 dB, SSIM 0.8855. The block structure of VQ is visible in the 4x zoom.");
    const imgs = [["cam_orig.png", "Original", 0.6], ["cam_rec.png", "Reconstructed (K = 64)", 4.83]];
    imgs.forEach((im) => { s.addImage({ path: A(im[0]), x: im[2], y: 1.65, w: 3.9, h: 3.9, objectName: im[1] }); T(s, im[1], { x: im[2], y: 5.6, w: 3.9, h: 0.35, fontSize: 14, bold: true, align: "center" }); });
    s.addImage({ path: A("cam_orig_zoom.png"), x: 9.06, y: 1.65, w: 1.8, h: 1.8, objectName: "Zoom original" });
    s.addImage({ path: A("cam_rec_zoom.png"), x: 10.93, y: 1.65, w: 1.8, h: 1.8, objectName: "Zoom reconstructed" });
    T(s, "original", { x: 9.06, y: 3.5, w: 1.8, h: 0.3, fontSize: 12, color: MUTED, align: "center" });
    T(s, "reconstructed", { x: 10.93, y: 3.5, w: 1.8, h: 0.3, fontSize: 12, color: MUTED, align: "center" });
    T(s, "4× zoom of the same 96×96 region", { x: 9.06, y: 3.8, w: 3.67, h: 0.3, fontSize: 12, color: MUTED, italic: true, align: "center" });
    stat(s, 9.06, 4.2, 1.8, "28.88", "CR", MAG); stat(s, 10.93, 4.2, 1.8, "29.75", "PSNR dB", PURPLE);
    T(s, "SSIM 0.8855  ·  MSE 68.84", { x: 9.06, y: 5.8, w: 3.67, h: 0.35, fontSize: 14, bold: true, color: INK, align: "center" });
    card(s, 0.6, 6.15, 12.13, 0.65, MIST, "Note");
    T(s, "At CR ≈ 29 the image remains recognisable; fine textures show the 4×4 block structure of VQ.", { x: 0.9, y: 6.15, w: 11.5, h: 0.65, fontSize: 15, bold: true, color: PURPLE, valign: "middle" });
  }

  // ================= 24. R-D vs baselines =================
  {
    const s = cs("6 · Experimental Results", "Quality at matched compression ratio",
      "At approximately the same CR, JPEG 2000 and JPEG reach higher PSNR than the proposed VQ codec, while the generic DWT+Huffman baseline developed in this work is lower. The proposed codec is not a quality leader; its contribution is the parallel framework. The DWT baseline is a generic, controlled implementation, not a published method.");
    const imgs = ["gray", "boat_img", "cameraman_img", "peppers_img"], lab = ["Lena", "Boat", "Cameraman", "Peppers"];
    const get = (m) => imgs.map((im) => +D.base.find((b) => b.image === im && b.method === m).PSNR_dB);
    const wav = imgs.map((im) => +D.wav.find((b) => b.image === im).PSNR_dB);
    chart(s, pres.charts.BAR, [{ name: "Proposed VQ", labels: lab, values: get("Proposed") }, { name: "DWT + Huffman", labels: lab, values: wav }, { name: "JPEG", labels: lab, values: get("JPEG") }, { name: "JPEG 2000", labels: lab, values: get("JPEG 2000") }],
      { x: 0.6, y: 1.65, w: 8.1, h: 4.9, barDir: "col", chartColors: [MAG, LAV, PURPLE, TEAL], showLegend: true, legendPos: "b", showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", dataLabelFontSize: 10,
        valAxisMinVal: 20, valAxisMaxVal: 40, valAxisTitle: "PSNR (dB)", showValAxisTitle: true, valAxisTitleColor: MUTED, valAxisTitleFontSize: 12, barGapWidthPct: 40, showTitle: true, title: "PSNR at approximately matched CR" });
    card(s, 8.95, 1.65, 3.78, 4.9, MIST, "Reading");
    T(s, [{ text: "How to read it", options: { bold: true, color: PURPLE, fontSize: 18, breakLine: true } },
      { text: "Each image: CR matched within ≈ 2%.", options: { bullet: true, breakLine: true } },
      { text: "JPEG 2000 > JPEG > proposed VQ > generic DWT+Huffman in PSNR.", options: { bullet: true, breakLine: true } },
      { text: "VQ gives a simple, parallelizable codec with a fast decoder.", options: { bullet: true } }],
      { x: 9.2, y: 1.8, w: 3.3, h: 4.6, fontSize: 15, color: INK, paraSpaceAfter: 8 });
  }

  // ================= 25. Sequential time breakdown (doughnut) =================
  {
    const s = cs("6 · Experimental Results", "Where the sequential time goes",
      "In the sequential program LBG is 77% of the total time for grayscale and 81% for color. The remaining stages (I/O, delta, Huffman, reconstruction, metrics) are the part that does not scale.");
    const mk = (x, title, a, b) => {
      chart(s, pres.charts.DOUGHNUT, [{ name: title, labels: ["LBG training", "Other stages"], values: [a, b] }],
        { x, y: 1.65, w: 5.2, h: 4.2, chartColors: [MAG, LAV], holeSize: 58, showLegend: true, legendPos: "b", showPercent: true, showValue: false, dataLabelColor: WHITE, dataLabelFontSize: 16, dataLabelFontBold: true, showTitle: true, title });
    };
    mk(0.6, "Grayscale (sequential)", 0.2557, 0.0761);
    mk(5.9, "Color (sequential)", 0.7827, 0.1817);
    stat(s, 11.15, 1.65, 1.58, "77%", "gray", MAG); stat(s, 11.15, 3.4, 1.58, "81%", "color", PURPLE);
    card(s, 0.6, 6.0, 12.13, 0.8, MIST, "Takeaway");
    T(s, "Mean sequential times: gray LBG 0.256 s of 0.332 s total; color LBG 0.783 s of 0.964 s.", { x: 0.9, y: 6.0, w: 11.5, h: 0.8, fontSize: 15, bold: true, color: PURPLE, valign: "middle" });
  }

  // ================= 26. LBG speedup =================
  {
    const s = cs("6 · Experimental Results", "LBG speedup versus number of processes",
      "Mean over the eight images. 9.19x at P=14, 65.7% efficiency. Speedup is almost linear up to P=6 (the P-cores) and then grows more slowly because E-cores are slower.");
    const ps = ["1", ...nps], sp = ["1", ...nps].map((p) => (p === "1" ? 1 : M[p].sl)), ideal = ps.map((p) => +p);
    chart(s, pres.charts.LINE, [{ name: "Ideal (S = P)", labels: ps, values: ideal }, { name: "Measured (mean of 8 images)", labels: ps, values: sp }],
      { x: 0.6, y: 1.65, w: 8.2, h: 5.0, chartColors: [LINE.replace("DDD5EE", "B8AED3"), MAG], lineSize: 3, lineDataSymbolSize: 9, showLegend: true, legendPos: "b", valAxisMinVal: 0, valAxisMaxVal: 14, valAxisMajorUnit: 2,
        catAxisTitle: "MPI processes P", showCatAxisTitle: true, catAxisTitleColor: MUTED, catAxisTitleFontSize: 12, valAxisTitle: "speedup (LBG stage)", showValAxisTitle: true, valAxisTitleColor: MUTED, valAxisTitleFontSize: 12 });
    stat(s, 9.1, 1.65, 3.63, "9.19×", "LBG speedup at P = 14 (range 9.10–9.24)", MAG);
    stat(s, 9.1, 3.35, 3.63, "65.7%", "parallel efficiency at P = 14", PURPLE);
    card(s, 9.1, 5.05, 3.63, 1.6, MIST, "Note");
    T(s, "Efficiency is high through the 6 P-cores, then limited by slower E-cores.", { x: 9.3, y: 5.15, w: 3.25, h: 1.4, fontSize: 14, color: MUTED });
  }

  // ================= 27. Efficiency + Karp-Flatt =================
  {
    const s = cs("6 · Experimental Results", "Efficiency and the Karp–Flatt metric",
      "Efficiency = S/P. It falls after P=6 where E-cores join. The Karp-Flatt serial fraction of the LBG stage stays about 0.04 for P>=8, so there is no growing parallel overhead; the Total stage has about 0.14 (gray) and 0.08 (color) because of the non-parallel stages.");
    const eff = nps.map((p) => +(M[p].sl / +p * 100).toFixed(1));
    chart(s, pres.charts.BAR, [{ name: "Efficiency", labels: nps, values: eff }],
      { x: 0.6, y: 1.65, w: 7.4, h: 4.2, barDir: "col", chartColors: [PURPLE], showLegend: false, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", valAxisMinVal: 0, valAxisMaxVal: 110, barGapWidthPct: 40, showTitle: true, title: "LBG parallel efficiency (%)",
        catAxisTitle: "MPI processes P", showCatAxisTitle: true, catAxisTitleColor: MUTED, catAxisTitleFontSize: 12 });
    const kfv = nps.map((p) => +D.kf[p].toFixed(3));
    chart(s, pres.charts.LINE, [{ name: "Karp–Flatt (LBG)", labels: nps, values: kfv }],
      { x: 8.2, y: 1.65, w: 4.53, h: 4.2, chartColors: [MAG], lineSize: 3, lineDataSymbolSize: 8, showLegend: false, valAxisMinVal: 0, valAxisMaxVal: 0.08, valAxisMajorUnit: 0.02, valAxisLabelFormatCode: "0.00", showTitle: true, title: "Karp–Flatt serial fraction (LBG)" });
    card(s, 0.6, 6.0, 12.13, 0.8, MIST, "Takeaway");
    T(s, "LBG serial fraction ≈ 0.04 for P ≥ 8: the loss is the E-core speed gap, not communication.", { x: 0.9, y: 6.0, w: 11.5, h: 0.8, fontSize: 15, bold: true, color: PURPLE, valign: "middle" });
  }

  // ================= 28. Throughput =================
  {
    const s = cs("6 · Experimental Results", "Throughput of the LBG stage",
      "Throughput = N*I/T_LBG in millions of vector-iterations per second (per channel for color). It grows from about 9.7-9.8 M/s sequentially to about 89-90 M/s at P=14, an increase of 9.2x.");
    const ps = ["seq", ...nps], lab = ["1", ...nps];
    chart(s, pres.charts.BAR, [{ name: "Grayscale", labels: lab, values: ps.map((p) => +D.thr.gray[p].toFixed(1)) }, { name: "Color (per channel)", labels: lab, values: ps.map((p) => +(D.thr.color[p] / 3).toFixed(1)) }],
      { x: 0.6, y: 1.65, w: 8.6, h: 5.0, barDir: "col", chartColors: [PURPLE, MAG], showLegend: true, legendPos: "b", showValue: false, valAxisMinVal: 0, valAxisMaxVal: 100, barGapWidthPct: 50,
        catAxisTitle: "MPI processes P (1 = sequential)", showCatAxisTitle: true, catAxisTitleColor: MUTED, catAxisTitleFontSize: 12, valAxisTitle: "million vector-iterations / s", showValAxisTitle: true, valAxisTitleColor: MUTED, valAxisTitleFontSize: 12 });
    stat(s, 9.5, 1.65, 3.23, "9.7 → 88.7", "M vec-it/s, gray (P = 1 → 14)", PURPLE);
    stat(s, 9.5, 3.35, 3.23, "9.8 → 90.3", "M vec-it/s, color per channel", MAG);
    card(s, 9.5, 5.05, 3.23, 1.6, MIST, "Note");
    T(s, "Throughput scales with P for both modes, as expected for a data-parallel kernel.", { x: 9.7, y: 5.15, w: 2.85, h: 1.4, fontSize: 14, color: MUTED });
  }

  // ================= 29. Total speedup =================
  {
    const s = cs("6 · Experimental Results", "Total speedup: Amdahl in action",
      "Total speedup includes I/O, delta, Huffman, reconstruction and metrics, which stay on rank 0. At P=14 the total speedup is 5.00x for grayscale and 6.84x for color, much lower than the 9.19x of the LBG stage.");
    const ps = ["1", ...nps];
    chart(s, pres.charts.LINE, [{ name: "LBG stage (mean)", labels: ps, values: ps.map((p) => (p === "1" ? 1 : M[p].sl)) }, { name: "Total, color", labels: ps, values: ps.map((p) => (p === "1" ? 1 : C[p].st)) }, { name: "Total, grayscale", labels: ps, values: ps.map((p) => (p === "1" ? 1 : G[p].st)) }],
      { x: 0.6, y: 1.65, w: 8.2, h: 5.0, chartColors: [MAG, TEAL, PURPLE], lineSize: 3, lineDataSymbolSize: 8, showLegend: true, legendPos: "b", valAxisMinVal: 0, valAxisMaxVal: 10, valAxisMajorUnit: 2,
        catAxisTitle: "MPI processes P", showCatAxisTitle: true, catAxisTitleColor: MUTED, catAxisTitleFontSize: 12, valAxisTitle: "speedup", showValAxisTitle: true, valAxisTitleColor: MUTED, valAxisTitleFontSize: 12 });
    stat(s, 9.1, 1.65, 3.63, "5.00×", "total speedup, gray (P = 14)", PURPLE);
    stat(s, 9.1, 3.35, 3.63, "6.84×", "total speedup, color (P = 14)", TEAL);
    card(s, 9.1, 5.05, 3.63, 1.6, MIST, "Note");
    T(s, "Karp–Flatt of Total ≈ 0.14 (gray) and 0.08 (color): the non-parallel stages.", { x: 9.3, y: 5.15, w: 3.25, h: 1.4, fontSize: 14, color: MUTED });
  }

  // ================= 30. Time breakdown P=1 vs 14 =================
  {
    const s = cs("6 · Experimental Results", "Time breakdown: sequential vs P = 14",
      "Mean stage times in seconds. At P=14 the LBG stage shrinks by 9.2x, but the other stages shrink only 2.0x (gray) and 3.2x (color), so their share of the total grows from 23% to 58% (gray) and from 19% to 40% (color).");
    const mk = (x, title, lab, lbg, oth) => {
      chart(s, pres.charts.BAR, [{ name: "LBG training", labels: lab, values: lbg }, { name: "Other stages", labels: lab, values: oth }],
        { x, y: 1.65, w: 6.0, h: 4.2, barDir: "col", chartColors: [MAG, LAV], showLegend: true, legendPos: "b", showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000", dataLabelFontBold: true, barGapWidthPct: 60, showTitle: true, title, valAxisLabelFormatCode: "0.0" });
    };
    mk(0.6, "Grayscale: mean time (s)", ["P = 1", "P = 14"], [0.2557, 0.0279], [0.0761, 0.0384]);
    mk(6.73, "Color: mean time (s)", ["P = 1", "P = 14"], [0.7827, 0.0850], [0.1817, 0.0561]);
    card(s, 0.6, 6.0, 12.13, 0.8, MIST, "Takeaway");
    T(s, "Share of non-LBG stages in the total: 23% → 58% (gray) and 19% → 40% (color).", { x: 0.9, y: 6.0, w: 11.5, h: 0.8, fontSize: 16, bold: true, color: PURPLE, valign: "middle" });
  }

  // ================= 31. Equal vs Adaptive LBG time =================
  {
    const s = cs("6 · Experimental Results", "Equal vs Adaptive: LBG execution time",
      "Mean LBG time in seconds. For P up to 6 the two strategies are equivalent (all ranks on P-cores). From P=8, when E-cores are used, Adaptive is clearly faster.");
    const mk = (x, mode, title) => {
      chart(s, pres.charts.BAR, [{ name: "Equal", labels: nps, values: nps.map((p) => +D.ea[mode][p].eq.toFixed(4)) }, { name: "Adaptive", labels: nps, values: nps.map((p) => +D.ea[mode][p].ad.toFixed(4)) }],
        { x, y: 1.65, w: 6.0, h: 4.6, barDir: "col", chartColors: [LAV, MAG], showLegend: true, legendPos: "b", showValue: false, barGapWidthPct: 40, showTitle: true, title, valAxisLabelFormatCode: "0.00",
          catAxisTitle: "MPI processes P", showCatAxisTitle: true, catAxisTitleColor: MUTED, catAxisTitleFontSize: 12, valAxisTitle: "seconds", showValAxisTitle: true, valAxisTitleColor: MUTED, valAxisTitleFontSize: 12 });
    };
    mk(0.6, "gray", "Grayscale: mean LBG time (s)"); mk(6.73, "color", "Color: mean LBG time (s)");
    card(s, 0.6, 6.35, 12.13, 0.5, MIST, "Takeaway");
    T(s, "Equal and Adaptive coincide for P ≤ 6; for P ≥ 8 Adaptive is faster on all 8 images.", { x: 0.9, y: 6.35, w: 11.5, h: 0.5, fontSize: 15, bold: true, color: PURPLE, valign: "middle" });
  }

  // ================= 32. Adaptive gain % =================
  {
    const s = cs("6 · Experimental Results", "Adaptive gain over Equal distribution",
      "Reduction of execution time with Adaptive relative to Equal, mean over the eight images (mean of per-image reductions). LBG: 28.3, 23.6, 19.8, 17.2 percent at P=8, 10, 12, 14. Total: 17.9, 13.7, 10.7, 8.8 percent.");
    const lbg = [-0.1, -0.2, -0.1, 28.3, 23.6, 19.8, 17.2], tot = [-0.3, -0.6, -0.6, 17.9, 13.7, 10.7, 8.8];
    chart(s, pres.charts.BAR, [{ name: "LBG time reduction (%)", labels: nps, values: lbg }, { name: "Total time reduction (%)", labels: nps, values: tot }],
      { x: 0.6, y: 1.65, w: 8.4, h: 5.0, barDir: "col", chartColors: [MAG, PURPLE], showLegend: true, legendPos: "b", showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", dataLabelFontSize: 10, valAxisMinVal: -5, valAxisMaxVal: 35, barGapWidthPct: 35,
        catAxisTitle: "MPI processes P", showCatAxisTitle: true, catAxisTitleColor: MUTED, catAxisTitleFontSize: 12, valAxisTitle: "reduction vs Equal (%)", showValAxisTitle: true, valAxisTitleColor: MUTED, valAxisTitleFontSize: 12 });
    stat(s, 9.3, 1.65, 3.43, "28.3%", "LBG time saved at P = 8", MAG);
    stat(s, 9.3, 3.35, 3.43, "17.2%", "LBG time saved at P = 14", PURPLE);
    card(s, 9.3, 5.05, 3.43, 1.6, MIST, "Note");
    T(s, "No difference for P ≤ 6 (±1%): only P-cores are used.", { x: 9.5, y: 5.15, w: 3.05, h: 1.4, fontSize: 14, color: MUTED });
  }

  // ================= 34. Compare with literature: compression =================
  {
    const s = cs("6 · Experimental Results", "Comparison with reported studies: compression",
      "A contextual comparison only. The studies operate at different compression ratios and use different images and size accounting; values are indicative. The time ratio is computed within each study: LBG/FLBG time in Bilal et al.; sequential/MPI LBG time at P=14 in this work.");
    const h = { bold: true, color: WHITE, fill: { color: DEEP }, fontSize: 13, align: "center", valign: "middle" };
    const c = (t, o = {}) => ({ text: t, options: Object.assign({ fontSize: 14, color: INK, align: "center", valign: "middle" }, o) });
    const me = (t) => c(t, { bold: true, color: MAG, fill: { color: MIST } });
    const rows = [[{ text: "Image", options: h }, { text: "Reference", options: h }, { text: "CR", options: h }, { text: "PSNR (dB)", options: h }, { text: "Time ratio", options: h }],
      [c("Lena", { bold: true }), c("Thomas et al. [6]"), c("1.52"), c("54.28"), c("–")],
      [c(""), c("Ranjan & Kumar [16]"), c("4.41"), c("34.78"), c("–")],
      [c(""), me("This work"), me("23.50"), me("29.67"), me("9.21×")],
      [c("Boat", { bold: true }), c("Thomas et al. [6]"), c("1.41"), c("54.07"), c("–")],
      [c(""), me("This work"), me("26.54"), me("29.11"), me("9.22×")],
      [c("Cameraman", { bold: true }), c("Bilal et al. [17]"), c("–"), c("25.3–26.8*"), c("2.61×")],
      [c(""), me("This work"), me("28.88"), me("29.75"), me("9.10×")]];
    s.addTable(rows, { x: 0.6, y: 1.65, w: 12.13, colW: [2.2, 3.7, 1.8, 2.4, 2.03], rowH: 0.5, border: { type: "solid", pt: 0.75, color: LINE }, fill: { color: WHITE }, autoPage: false });
    T(s, "* at ≤ 0.625 bpp. “–” = not reported. Time ratio is computed within each study (LBG/FLBG time vs sequential/MPI time at P = 14); the mechanisms and hardware differ.  Indicative only: images, implementations and size accounting differ.", { x: 0.6, y: 5.8, w: 12.13, h: 0.5, fontSize: 11, color: MUTED, italic: true });
    card(s, 0.6, 6.3, 12.13, 0.6, MIST, "Takeaway");
    T(s, "Different operating points: near-lossless wavelet methods vs a high-compression VQ codec (CR 23–29).", { x: 0.9, y: 6.3, w: 11.5, h: 0.6, fontSize: 15, bold: true, color: PURPLE, valign: "middle" });
  }

  // ================= 35. Compare with literature: parallel =================
  {
    const s = cs("6 · Experimental Results", "Comparison with reported studies: parallel speedup",
      "Contextual comparison. This work reports speedup against a separate sequential program. The 9.19x is the mean LBG-stage speedup over the eight images; the total speedup includes the non-parallel stages. The reported speedups are of the same order but are not a ranking.");
    const h = { bold: true, color: WHITE, fill: { color: DEEP }, fontSize: 13, valign: "middle" };
    const c = (t, o = {}) => ({ text: t, options: Object.assign({ fontSize: 14, color: INK, valign: "middle" }, o) });
    const me = (t) => c(t, { bold: true, color: MAG, fill: { color: MIST } });
    const rows = [[{ text: "Study", options: h }, { text: "Application", options: h }, { text: "Resources", options: h }, { text: "Baseline", options: h }, { text: "Speedup", options: h }],
      [c("Tanović 2024", { bold: true }), c("k-means, image classification"), c("12 cores"), c("not stated"), c("up to 10.2×")],
      [c("Papakyriakou 2025", { bold: true }), c("k-means, 75 M points"), c("2–48 MPI processes"), c("2 processes"), c("≈10.05×")],
      [c("Bystrov 2023", { bold: true }), c("DEM simulation"), c("8 heterogeneous containers"), c("sequential"), c("up to 6.0×")],
      [me("This work"), me("LBG image compression"), me("14 MPI processes (6 P + 8 E)"), me("sequential"), me("9.19× LBG; 5.00× / 6.84× total")]];
    s.addTable(rows, { x: 0.6, y: 1.65, w: 12.13, colW: [2.1, 2.9, 2.8, 1.6, 2.73], rowH: [0.5, 0.7, 0.7, 0.7, 0.8], border: { type: "solid", pt: 0.75, color: LINE }, fill: { color: WHITE }, autoPage: false, margin: [0.05, 0.12, 0.05, 0.12] });
    T(s, "Papakyriakou: 181.83 s → 18.09 s, efficiency 41.89% at 48 processes, relative to the two-process baseline. The studies differ in application, workload, hardware, process count and speedup baseline: contextual comparison, not a ranking.", { x: 0.6, y: 5.12, w: 12.13, h: 0.65, fontSize: 11, color: MUTED, italic: true });
    card(s, 0.6, 5.85, 12.13, 0.95, MIST, "Takeaway");
    T(s, "The speedup is of the same order as the reported 6–10×. The contribution is the speed-aware distribution on a hybrid CPU (17–28% faster LBG than Equal), not a higher absolute speedup.", { x: 0.9, y: 5.85, w: 11.5, h: 0.95, fontSize: 15, bold: true, color: PURPLE, valign: "middle" });
  }

  // ================= 36. Limitations =================
  {
    const s = cs("7 · Conclusion", "Limitations",
      "Be explicit about the limits: one CPU platform, a modest problem size, a non-parallel part, and quality below standard codecs at the same CR.");
    const L = [[ic.chip, "One platform", "A single hybrid CPU (i7-13650HX); results may differ on other CPUs."], [ic.img, "Small problem size", "512×512 images limit scalability at high P (≈ 1.5–2 ms per sequential iteration)."], [ic.layer, "Non-parallel stages", "I/O, delta, Huffman and reconstruction stay on rank 0: 58% of total time at P = 14 (gray)."], [ic.search, "Quality vs standards", "At matched CR, JPEG and JPEG 2000 reach higher PSNR than VQ with K = 64."]];
    L.forEach((l, i) => {
      const x = 0.6 + (i % 2) * 6.15, y = 1.7 + Math.floor(i / 2) * 2.6;
      card(s, x, y, 5.95, 2.4, MIST, "Limitation card");
      circleIcon(s, l[0], x + 0.3, y + 0.35, 0.8, i % 2 ? MAG : PURPLE);
      T(s, l[1], { x: x + 1.4, y: y + 0.3, w: 4.3, h: 0.5, fontSize: 20, bold: true });
      T(s, l[2], { x: x + 1.4, y: y + 0.85, w: 4.3, h: 1.4, fontSize: 15, color: MUTED });
    });
  }

  // ================= 37. Conclusion =================
  {
    const s = cs("7 · Conclusion", "Conclusion",
      "Summarize: the compressor, the exact parallelization, the speedup, the Adaptive gain, and the quality.");
    stat(s, 0.6, 1.7, 2.95, "25.92", "mean CR (gray), PSNR 29.5 dB", MAG);
    stat(s, 3.75, 1.7, 2.95, "9.19×", "LBG speedup at P = 14", PURPLE);
    stat(s, 6.9, 1.7, 2.95, "5.0 / 6.8×", "total speedup gray / color", TEAL);
    stat(s, 10.05, 1.7, 2.68, "17–28%", "less LBG time with Adaptive (P = 8–14)", GOLD);
    card(s, 0.6, 3.5, 12.13, 3.25, MIST, "Conclusions");
    T(s, [{ text: "A parallel LBG vector-quantization compressor (4×4 blocks, K = 64, delta + Huffman) reaches CR ≈ 24–26 at PSNR ≈ 29 dB.", options: { bullet: true, breakLine: true } },
      { text: "MPI parallelization preserves the results in all tested configurations and cuts LBG time 9.2× on 14 processes (65.7% efficiency).", options: { bullet: true, breakLine: true } },
      { text: "Speed-aware (Adaptive) distribution reduces LBG time by 17–28% against Equal on the hybrid P/E-core CPU.", options: { bullet: true, breakLine: true } },
      { text: "Total speedup (5.0× / 6.8×) is bounded by the non-parallel stages, as the Karp–Flatt analysis shows.", options: { bullet: true } }],
      { x: 0.9, y: 3.7, w: 11.5, h: 2.95, fontSize: 17, color: INK, paraSpaceAfter: 8 });
  }

  // ================= 38. Future work =================
  {
    const s = cs("8 · Future work", "Future work",
      "Natural extensions: parallelize the remaining stages, hybrid MPI+OpenMP, GPU, and entropy coding improvements.");
    const F = [[ic.layer, "Parallelize the remaining stages", "Delta, Huffman and reconstruction are 58% of total time at P = 14."], [ic.net, "Hybrid MPI + OpenMP", "Combine process- and thread-level parallelism on the hybrid CPU."], [ic.rocket, "GPU acceleration", "Offload the assignment step, the dominant kernel."], [ic.lock, "Better entropy coding", "Canonical Huffman and a 5-byte-per-symbol table accounting; larger images."]];
    F.forEach((f, i) => {
      const x = 0.6 + (i % 2) * 6.15, y = 1.7 + Math.floor(i / 2) * 2.6;
      card(s, x, y, 5.95, 2.4, MIST, "Future card");
      circleIcon(s, f[0], x + 0.3, y + 0.35, 0.8, i % 2 ? MAG : TEAL);
      T(s, f[1], { x: x + 1.4, y: y + 0.3, w: 4.3, h: 0.7, fontSize: 19, bold: true });
      T(s, f[2], { x: x + 1.4, y: y + 1.0, w: 4.3, h: 1.3, fontSize: 15, color: MUTED });
    });
  }

  // ================= 39. References =================
  {
    const s = cs("References", "References", "Core references used in the seminar.");
    const refs = [
      "H. M. Zangana (2025). Design and implementation of a novel parallel algorithm for efficient image compression in high-performance computing. EAI Endorsed Trans. AI and Robotics, 4.",
      "S. Thomas, A. Krishna, S. Govind, A. K. Sahu (2025). A novel image compression method using wavelet coefficients and Huffman coding. J. Eng. Res., 13, 361–370.",
      "R. Ranjan, P. Kumar (2023). An improved image compression algorithm using 2D DWT and PCA with canonical Huffman encoding. Entropy, 25, 1382.",
      "M. Bilal, Z. Ullah, O. Mujahid, T. Fouzder (2024). Fast Linde–Buzo–Gray (FLBG) algorithm for image compression through rescaling using bilinear interpolation. J. Imaging, 10, 124.",
      "R. K. Paul et al. (2024). Image compression scheme based on optimized K-means clustering and higher-level decomposed DWT. Procedia Comput. Sci., 235, 642–655.",
      "A. Tanović et al. (2024). Implementation of parallel K-means algorithm for image classification using OpenMP and MPI libraries. ZINC 2024.",
      "D. Papakyriakou, I. S. Barbounakis (2025). Parallel k-means benchmarking on a CPU-bound Beowulf cluster of Raspberry Pi nodes. Int. J. Comput. Appl., 187(32), 43–55.",
      "O. Bystrov et al. (2023). Hybrid parallelization of discrete element software for heterogeneous resources. Proc. PARENG 2023.",
      "Y. Linde, A. Buzo, R. M. Gray (1980). An algorithm for vector quantizer design. IEEE Trans. Commun., 28(1), 84–95.",
      "A. H. Karp, H. P. Flatt (1990). Measuring parallel processor performance. Commun. ACM, 33(5), 539–543.",
      "Z. Wang, A. C. Bovik, H. R. Sheikh, E. P. Simoncelli (2004). Image quality assessment: from error visibility to structural similarity. IEEE Trans. Image Process., 13(4), 600–612."];
    T(s, refs.map((r, i) => ({ text: `[${i + 1}] ${r}`, options: { breakLine: i < refs.length - 1 } })), { x: 0.6, y: 1.6, w: 12.13, h: 5.3, fontSize: 14, color: INK, paraSpaceAfter: 6 });
  }

  // ================= 40. Thank you =================
  {
    const s = pres.addSlide({ masterName: "TITLE_DARK" }); nSlide++;
    s.addShape(pres.shapes.OVAL, { x: 8.3, y: -1.2, w: 6.4, h: 6.4, fill: { color: PURPLE, transparency: 55 }, line: { color: PURPLE, width: 0 }, objectName: "Decor circle 1" });
    s.addShape(pres.shapes.OVAL, { x: 9.6, y: 4.0, w: 5.0, h: 5.0, fill: { color: MAG, transparency: 70 }, line: { color: MAG, width: 0 }, objectName: "Decor circle 2" });
    T(s, "Thank you", { x: 0.8, y: 2.3, w: 9, h: 1.4, fontSize: 64, bold: true, color: WHITE, fontFace: HF });
    T(s, "Questions and discussion", { x: 0.8, y: 3.8, w: 9, h: 0.6, fontSize: 24, color: "D9D2EE" });
    T(s, "Ibtihal Hussien  ·  Supervised by Dr. Ahmed Badri and Dr. Esraa Hadi  ·  University of Babylon", { x: 0.8, y: 5.6, w: 10, h: 0.5, fontSize: 15, color: LAV });
    s.addImage({ path: A("logo.png"), x: 0.8, y: 0.7, w: 1.05, h: 1.1, objectName: "University logo" });
  }

  await pres.writeFile({ fileName: path.join(__dirname, "seminar_v2.pptx") });
  await applyTheme(path.join(__dirname, "seminar_v2.pptx"), THEME);
  console.log("slides:", nSlide);
})();
