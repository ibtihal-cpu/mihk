module.exports = function (p) {
const INK = "1F1A33", DEEP = "2E2055", TEAL = "2A9D8F", PURPLE = "6B4FA3", GREEN = "1E8449";
const s = p.addSlide(); s.background = { color: "FFFFFF" };
s.addShape(p.ShapeType.roundRect, { x: 0.5, y: 0.35, w: 1.9, h: 0.55, rectRadius: 0.1, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
s.addText("Results", { x: 0.5, y: 0.35, w: 1.9, h: 0.55, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 18, bold: true, color: "FFFFFF", margin: 0 });
s.addText("Verification: Parallel Results Equal Sequential", { x: 2.6, y: 0.3, w: 10.2, h: 0.65, valign: "middle", fontFace: "Cambria", fontSize: 28, bold: true, color: DEEP, margin: 0 });
s.addShape(p.ShapeType.rect, { x: 0.5, y: 1.05, w: 12.33, h: 0.04, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
const H = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: TEAL }, align: "center", fontSize: 15 } });
const C = (t, f, o) => ({ text: t, options: Object.assign({ align: "center", fontSize: 15, color: INK, fill: { color: f } }, o || {}) });
const Y = (f) => C("Yes", f, { bold: true, color: GREEN });
const data = [["Lena", "Gray", "29.67", "0.8190", "160"], ["Boat", "Gray", "29.11", "0.8394", "151"], ["Cameraman", "Gray", "29.75", "0.8855", "155"], ["Peppers", "Gray", "29.41", "0.7624", "132"],
  ["Lena", "Color", "28.91", "0.7594", "476"], ["Peppers", "Color", "28.35", "0.6964", "438"], ["F16", "Color", "29.47", "0.8539", "479"], ["Gold Hill", "Color", "28.45", "0.7520", "479"]];
const rows = [[H("Image"), H("Type"), H("PSNR (dB)"), H("SSIM"), H("LBG iterations"), H("Metrics identical"), H("MD5 identical")]];
data.forEach((d, i) => { const f = i < 4 ? "EAF6F4" : "F1ECF9"; rows.push([C(d[0], f, { align: "left", bold: true }), C(d[1], f), C(d[2], f), C(d[3], f), C(d[4], f), Y(f), Y(f)]); });
s.addTable(rows, { x: 0.7, y: 1.4, w: 11.9, colW: [2.1, 1.1, 1.5, 1.4, 1.9, 2.0, 1.9], rowH: 0.5, fontFace: "Calibri", border: { type: "solid", color: "FFFFFF", pt: 1.5 }, valign: "middle" });
s.addText("Compared with the sequential run: parallel P = 4 (automatic), P = 14 (Adaptive) and P = 14 (forced Equal). Metrics: compression ratio, MSE, PSNR, SSIM and iteration count. MD5: checksum of the reconstructed image. Values shown are identical in all four runs.",
  { x: 0.7, y: 6.1, w: 11.9, h: 0.8, fontFace: "Calibri", fontSize: 14, italic: true, color: PURPLE, margin: 0 });
};
