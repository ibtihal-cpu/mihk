const pptxgen = require("pptxgenjs");
const p = new pptxgen(); p.layout = "LAYOUT_WIDE";
const INK = "1F1A33", DEEP = "2E2055", TEAL = "2A9D8F", MIST = "F5F1FB", MAG = "E0457B", PURPLE = "6B4FA3";
function header(s, title) {
  s.background = { color: "FFFFFF" };
  s.addShape(p.ShapeType.roundRect, { x: 0.5, y: 0.35, w: 1.9, h: 0.55, rectRadius: 0.1, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
  s.addText("Results", { x: 0.5, y: 0.35, w: 1.9, h: 0.55, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 18, bold: true, color: "FFFFFF", margin: 0 });
  s.addText(title, { x: 2.6, y: 0.3, w: 10.2, h: 0.65, valign: "middle", fontFace: "Cambria", fontSize: 28, bold: true, color: DEEP, margin: 0 });
  s.addShape(p.ShapeType.rect, { x: 0.5, y: 1.05, w: 12.33, h: 0.04, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
}
function bullets(s, items, box, size) {
  s.addShape(p.ShapeType.roundRect, { x: box.x, y: box.y, w: box.w, h: box.h, rectRadius: 0.08, fill: { color: MIST }, line: { color: MIST, width: 0 } });
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: { code: "25A0", color: TEAL }, breakLine: i < items.length - 1, paraSpaceAfter: 9 } })),
    { x: box.x + 0.1, y: box.y + 0.1, w: box.w - 0.2, h: box.h - 0.2, valign: "top", fontFace: "Calibri", fontSize: size, color: INK, margin: 0.08 });
}
// ---- throughput ----
let s = p.addSlide(); header(s, "Throughput");
const r = Math.min(8.2 / 865, 5.5 / 572);
s.addShape(p.ShapeType.roundRect, { x: 0.5, y: 1.35, w: 8.2, h: 5.5, rectRadius: 0.08, fill: { color: "FFFFFF" }, line: { color: TEAL, width: 1.25 } });
s.addImage({ path: "assets/throughput_ch4.png", x: 0.5 + (8.2 - 865 * r) / 2, y: 1.35 + (5.5 - 572 * r) / 2, w: 865 * r, h: 572 * r });
bullets(s, ["Throughput = original image size / total execution time (MiB/s).",
  "Grayscale: 1.30 → 3.35 MiB/s from P = 2 to P = 14.",
  "Color: 1.42 → 4.54 MiB/s.",
  "Color images hold three times more data, but their total time grows by only about 2.2× at P = 14, so their throughput is higher.",
  "Shaded bands: minimum to maximum over the images."], { x: 8.95, y: 1.35, w: 3.9, h: 5.5 }, 15);
// ---- Karp-Flatt ----
s = p.addSlide(); header(s, "Karp–Flatt Metric");
const H = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: TEAL }, align: "center", fontSize: 15 } });
const C = (t, f, o) => ({ text: t, options: Object.assign({ align: "center", fontSize: 15, color: INK, fill: { color: f } }, o || {}) });
const data = [[2, "0.033", "96.8", "0.101", "90.8"], [4, "0.018", "94.8", "0.081", "80.5"], [6, "0.022", "90.2", "0.084", "70.4"], [8, "0.038", "78.8", "0.110", "56.5"], [10, "0.040", "73.6", "0.109", "50.6"], [12, "0.042", "68.6", "0.107", "45.9"], [14, "0.040", "65.7", "0.105", "42.3"]];
const rows = [[H("P"), H("LBG: Karp–Flatt"), H("LBG: efficiency (%)"), H("Total: Karp–Flatt"), H("Total: efficiency (%)")]];
data.forEach((d, i) => { const f = i % 2 ? "FFFFFF" : "EAF6F4"; rows.push(d.map((v, j) => C(String(v), f, j === 0 ? { bold: true } : j === 1 || j === 3 ? { bold: true, color: j === 1 ? PURPLE : MAG } : {}))); });
s.addTable(rows, { x: 0.5, y: 1.4, w: 7.9, colW: [0.9, 1.7, 1.8, 1.8, 1.7], rowH: 0.55, fontFace: "Calibri", border: { type: "solid", color: "FFFFFF", pt: 1.5 }, valign: "middle" });
s.addText("Mean of all 8 images.", { x: 0.5, y: 6.1, w: 7.9, h: 0.3, fontFace: "Calibri", fontSize: 12, italic: true, color: PURPLE, margin: 0 });
bullets(s, ["Karp–Flatt estimates the serial fraction of the program from the measured speedup.",
  "LBG: about 0.04 for P ≥ 8; the serial fraction stays small and does not grow with P.",
  "Total: about 0.105 (gray ≈ 0.14, color ≈ 0.08); the sequential coding and reconstruction stages dominate.",
  "This explains why the total speedup (5.00× gray, 6.84× color) is lower than the LBG speedup (9.19×)."], { x: 8.65, y: 1.4, w: 4.2, h: 5.0 }, 15);
p.writeFile({ fileName: "figs/results_thr_kf.pptx" }).then(() => console.log("ok"));
