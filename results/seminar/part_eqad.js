module.exports = function (p) {
const INK = "1F1A33", DEEP = "2E2055", TEAL = "2A9D8F", MIST = "F5F1FB";
const s = p.addSlide(); s.background = { color: "FFFFFF" };
s.addShape(p.ShapeType.roundRect, { x: 0.5, y: 0.35, w: 1.9, h: 0.55, rectRadius: 0.1, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
s.addText("Results", { x: 0.5, y: 0.35, w: 1.9, h: 0.55, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 18, bold: true, color: "FFFFFF", margin: 0 });
s.addText("Equal vs Adaptive Workload Distribution", { x: 2.6, y: 0.3, w: 10.2, h: 0.65, valign: "middle", fontFace: "Cambria", fontSize: 28, bold: true, color: DEEP, margin: 0 });
s.addShape(p.ShapeType.rect, { x: 0.5, y: 1.05, w: 12.33, h: 0.04, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
const r = Math.min(8.2 / 2024, 5.5 / 1232);
s.addShape(p.ShapeType.roundRect, { x: 0.5, y: 1.35, w: 8.2, h: 5.5, rectRadius: 0.08, fill: { color: "FFFFFF" }, line: { color: TEAL, width: 1.25 } });
s.addImage({ path: "assets/eqad_chart.png", x: 0.5 + (8.2 - 2024 * r) / 2, y: 1.35 + (5.5 - 1232 * r) / 2, w: 2024 * r, h: 1232 * r });
const items = ["With Equal distribution, the faster P-cores finish early and wait for the E-cores: 7.61× at P = 14.",
  "Adaptive distribution reaches 9.19× at P = 14.",
  "LBG time is reduced by 28.3%, 23.6%, 19.8% and 17.2% at P = 8, 10, 12 and 14.",
  "Total time is reduced by 17.9% to 8.8%.",
  "For P ≤ 6 (P-cores only) the two strategies are equivalent.",
  "The reconstructed images are identical in both cases."];
s.addShape(p.ShapeType.roundRect, { x: 8.95, y: 1.35, w: 3.9, h: 5.5, rectRadius: 0.08, fill: { color: MIST }, line: { color: MIST, width: 0 } });
s.addText(items.map((t, i) => ({ text: t, options: { bullet: { code: "25A0", color: TEAL }, breakLine: i < items.length - 1, paraSpaceAfter: 8 } })),
  { x: 9.05, y: 1.45, w: 3.7, h: 5.3, valign: "top", fontFace: "Calibri", fontSize: 15, color: INK, margin: 0.08 });
};
