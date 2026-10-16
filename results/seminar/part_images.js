module.exports = function (p) {
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
const names = [["Lena", "Boat", "Cameraman", "Peppers"], ["Lena", "Peppers", "F16", "Gold Hill"]];
const rows = ["Grayscale", "Color"];
for (let r = 0; r < 2; r++) {
  const ly = r === 0 ? 1.2 : 4.25, fy = r === 0 ? 1.55 : 4.6, sz = 2.3;
  s.addText(rows[r], { x: 0.5, y: ly, w: 6, h: 0.32, fontFace: "Calibri", fontSize: 18, bold: true, color: TEAL, margin: 0 });
  for (let c = 0; c < 4; c++) {
    const x = 0.5 + c * 3.1;
    frame(s, x, fy, sz, sz, "Insert image");
    s.addText(names[r][c], { x, y: fy + sz + 0.03, w: sz, h: 0.3, align: "center", fontFace: "Calibri", fontSize: 14, bold: true, color: INK, margin: 0 });
  }
}
// ---- original vs reconstructed ----
const data = {
  gray: [["Lena", "29.67", "0.8190"], ["Boat", "29.11", "0.8394"], ["Cameraman", "29.75", "0.8855"], ["Peppers", "29.41", "0.7624"]],
  color: [["Lena", "28.91", "0.7594"], ["Peppers", "28.35", "0.6964"], ["F16", "29.47", "0.8539"], ["Gold Hill", "28.45", "0.7520"]]
};
function gridSlide(kind) {
  const label = kind === "gray" ? "Grayscale Images" : "Color Images";
  const s = p.addSlide(); header(s, "Results", `Reconstruction Results: ${label}`, TEAL);
  const sz = 2.55, x0 = 1.75, gx = 0.15, yO = 1.55, yR = 4.2;
  s.addText("Original", { x: 0.45, y: yO, w: 1.2, h: sz, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 14, bold: true, color: DEEP, margin: 0 });
  s.addText("Reconstructed", { x: 0.35, y: yR, w: 1.35, h: sz, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 13, bold: true, color: DEEP, margin: 0 });
  data[kind].forEach(([nm, psnr, ssim], c) => {
    const x = x0 + c * (sz + gx);
    s.addText(nm, { x, y: 1.18, w: sz, h: 0.33, align: "center", fontFace: "Calibri", fontSize: 17, bold: true, color: TEAL, margin: 0 });
    frame(s, x, yO, sz, sz, "Original");
    frame(s, x, yR, sz, sz, "Reconstructed");
    s.addText([{ text: "CR = ___", options: { color: MAG, bold: true, breakLine: true } }, { text: `PSNR ${psnr} dB   SSIM ${ssim}`, options: { color: INK } }],
      { x: x - 0.1, y: yR + sz + 0.03, w: sz + 0.2, h: 0.5, align: "center", fontFace: "Calibri", fontSize: 13, margin: 0 });
  });
}
gridSlide("gray"); gridSlide("color");
};
