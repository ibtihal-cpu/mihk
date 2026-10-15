const pptxgen = require("pptxgenjs");
const p = new pptxgen(); p.layout = "LAYOUT_WIDE";
const INK = "1F1A33", DEEP = "2E2055", MAG = "E0457B", PURPLE = "6B4FA3", MIST = "F5F1FB", TEAL = "2A9D8F";
function header(s, chip, title, color) {
  s.background = { color: "FFFFFF" };
  s.addShape(p.ShapeType.roundRect, { x: 0.5, y: 0.35, w: 1.9, h: 0.55, rectRadius: 0.1, fill: { color }, line: { color, width: 0 } });
  s.addText(chip, { x: 0.5, y: 0.35, w: 1.9, h: 0.55, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 18, bold: true, color: "FFFFFF", margin: 0 });
  s.addText(title, { x: 2.6, y: 0.3, w: 10.2, h: 0.65, valign: "middle", fontFace: "Cambria", fontSize: 28, bold: true, color: DEEP, margin: 0 });
  s.addShape(p.ShapeType.rect, { x: 0.5, y: 1.05, w: 12.33, h: 0.04, fill: { color }, line: { color, width: 0 } });
}
function frame(s, x, y, w, h, label) {
  s.addShape(p.ShapeType.rect, { x, y, w, h, fill: { color: MIST }, line: { color: PURPLE, width: 1.5, dashType: "dash" } });
  s.addText(label, { x, y, w, h, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 14, color: PURPLE, italic: true, margin: 0.1 });
}
// ---- test images grid ----
let s = p.addSlide(); header(s, "Results", "Test Images", TEAL);
const names = [["Lena", "Cameraman", "Boat", "Peppers"], ["Lena", "Peppers", "F16", "Gold Hill"]];
const rows = ["Grayscale", "Color"];
for (let r = 0; r < 2; r++) {
  s.addText(rows[r], { x: 0.5, y: 1.25 + r * 3.0, w: 6, h: 0.35, fontFace: "Calibri", fontSize: 18, bold: true, color: TEAL, margin: 0 });
  for (let c = 0; c < 4; c++) {
    const x = 0.5 + c * 3.1, y = 1.65 + r * 3.0;
    frame(s, x, y, 2.5, 2.5, "Insert image");
    s.addText(names[r][c], { x, y: y + 2.52, w: 2.5, h: 0.3, align: "center", fontFace: "Calibri", fontSize: 14, bold: true, color: INK, margin: 0 });
  }
}
// ---- original vs reconstructed ----
const data = {
  gray: [["Lena", "29.67", "0.8190"], ["Boat", "29.11", "0.8394"], ["Cameraman", "29.75", "0.8855"], ["Peppers", "29.41", "0.7624"]],
  color: [["Lena", "28.91", "0.7594"], ["Peppers", "28.35", "0.6964"], ["F16", "29.47", "0.8539"], ["Gold Hill", "28.45", "0.7520"]]
};
function pairSlide(kind, i0) {
  const label = kind === "gray" ? "Grayscale" : "Color";
  const s = p.addSlide(); header(s, "Results", `Original vs Reconstructed: ${label}`, TEAL);
  [0, 1].forEach(k => {
    const [nm, psnr, ssim] = data[kind][i0 + k];
    const x0 = 0.5 + k * 6.3, y = 1.5, sz = 2.95;
    frame(s, x0, y, sz, sz, "Original");
    frame(s, x0 + sz + 0.1, y, sz, sz, "Reconstructed");
    s.addText(nm, { x: x0, y: y + sz + 0.12, w: 2 * sz + 0.1, h: 0.4, align: "center", fontFace: "Calibri", fontSize: 20, bold: true, color: DEEP, margin: 0 });
    s.addText([{ text: "CR = ___", options: { color: MAG, bold: true } }, { text: `   |   PSNR = ${psnr} dB   |   SSIM = ${ssim}`, options: { color: INK } }],
      { x: x0, y: y + sz + 0.55, w: 2 * sz + 0.1, h: 0.4, align: "center", fontFace: "Calibri", fontSize: 16, margin: 0 });
  });
  s.addText("Block size 4 × 4, K = 64. Same reconstruction for the sequential and parallel runs.", { x: 0.5, y: 6.75, w: 12.33, h: 0.35, align: "center", fontFace: "Calibri", fontSize: 13, italic: true, color: PURPLE, margin: 0 });
}
pairSlide("gray", 0); pairSlide("gray", 2); pairSlide("color", 0); pairSlide("color", 2);
p.writeFile({ fileName: "figs/results_images.pptx" }).then(() => console.log("ok"));
