module.exports = function (p) {
const INK = "1F1A33", DEEP = "2E2055", TEAL = "2A9D8F", MIST = "F5F1FB";
const s = p.addSlide(); s.background = { color: "FFFFFF" };
s.addShape(p.ShapeType.roundRect, { x: 0.5, y: 0.35, w: 1.9, h: 0.55, rectRadius: 0.1, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
s.addText("Results", { x: 0.5, y: 0.35, w: 1.9, h: 0.55, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 18, bold: true, color: "FFFFFF", margin: 0 });
s.addText("Parallel Efficiency of LBG Training", { x: 2.6, y: 0.3, w: 10.2, h: 0.65, valign: "middle", fontFace: "Cambria", fontSize: 28, bold: true, color: DEEP, margin: 0 });
s.addShape(p.ShapeType.rect, { x: 0.5, y: 1.05, w: 12.33, h: 0.04, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
  s.addShape(p.ShapeType.roundRect, { x: 0.5, y: 1.2, w: 8.2, h: 0.5, rectRadius: 0.08, fill: { color: "FDF1E6" }, line: { color: "E07B22", width: 1.25 } });
  s.addText([{ text: "E = S / P", options: { breakLine: false } }], { x: 0.5, y: 1.2, w: 8.2, h: 0.5, align: "center", valign: "middle", fontFace: "Cambria", fontSize: 20, bold: true, color: "2E2055", margin: 0.04 });
const r = Math.min(8.2 / 2024, 5.05 / 1232);
s.addShape(p.ShapeType.roundRect, { x: 0.5, y: 1.8, w: 8.2, h: 5.05, rectRadius: 0.08, fill: { color: "FFFFFF" }, line: { color: TEAL, width: 1.25 } });
s.addImage({ path: "assets/efficiency_chart.png", x: 0.5 + (8.2 - 2024 * r) / 2, y: 1.8 + (5.05 - 1232 * r) / 2, w: 2024 * r, h: 1232 * r });
s.addText("Workload distribution: Equal for P ≤ 4, Adaptive for P > 4.", { x: 0.5, y: 6.9, w: 8.2, h: 0.3, align: "center", fontFace: "Calibri", fontSize: 13, italic: true, color: "6B4FA3", margin: 0 });
const items = ["Efficiency is 97% at P = 2 and stays at 90% or more up to P = 6 (P-cores only).",
  "It drops to 79% at P = 8, where the E-cores start to be used, and reaches 66% at P = 14.",
  "The E-cores are slower than the P-cores, so each added process contributes less than a full core.",
  "Karp–Flatt stays near 0.04 for P ≥ 8: the serial fraction of LBG remains small.",
  "Mean of the 8 images."];
s.addShape(p.ShapeType.roundRect, { x: 8.95, y: 1.35, w: 3.9, h: 5.5, rectRadius: 0.08, fill: { color: MIST }, line: { color: MIST, width: 0 } });
s.addText(items.map((t, i) => ({ text: t, options: { bullet: { code: "25A0", color: TEAL }, breakLine: i < items.length - 1, paraSpaceAfter: 9 } })),
  { x: 9.05, y: 1.45, w: 3.7, h: 5.3, valign: "top", fontFace: "Calibri", fontSize: 16, color: INK, margin: 0.08 });
};
