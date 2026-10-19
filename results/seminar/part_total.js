module.exports = function (p) {
  const INK = "1F1A33", DEEP = "2E2055", TEAL = "2A9D8F", MIST = "F5F1FB";
  const s = p.addSlide(); s.background = { color: "FFFFFF" };
  s.addShape(p.ShapeType.roundRect, { x: 0.5, y: 0.35, w: 1.9, h: 0.55, rectRadius: 0.1, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
  s.addText("Results", { x: 0.5, y: 0.35, w: 1.9, h: 0.55, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 18, bold: true, color: "FFFFFF", margin: 0 });
  s.addText("Total Speedup: Grayscale and Color", { x: 2.6, y: 0.3, w: 10.2, h: 0.65, valign: "middle", fontFace: "Cambria", fontSize: 28, bold: true, color: DEEP, margin: 0 });
  s.addShape(p.ShapeType.rect, { x: 0.5, y: 1.05, w: 12.33, h: 0.04, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
  s.addShape(p.ShapeType.roundRect, { x: 0.5, y: 1.2, w: 8.2, h: 0.5, rectRadius: 0.08, fill: { color: "FDF1E6" }, line: { color: "E07B22", width: 1.25 } });
  s.addText([{ text: "S = T_seq / T_P", options: { breakLine: false } }], { x: 0.5, y: 1.2, w: 8.2, h: 0.5, align: "center", valign: "middle", fontFace: "Cambria", fontSize: 20, bold: true, color: "2E2055", margin: 0.04 });
  const r = Math.min(8.2 / 2024, 5.05 / 1232);
  s.addShape(p.ShapeType.roundRect, { x: 0.5, y: 1.8, w: 8.2, h: 5.05, rectRadius: 0.08, fill: { color: "FFFFFF" }, line: { color: TEAL, width: 1.25 } });
  s.addImage({ path: "assets/total_speedup_chart.png", x: 0.5 + (8.2 - 2024 * r) / 2, y: 1.8 + (5.05 - 1232 * r) / 2, w: 2024 * r, h: 1232 * r });
  const items = ["Total speedup at P = 14: 5.00× (grayscale) and 6.84× (color); efficiency 35.7% and 48.9%.",
    "It is lower than the LBG speedup (9.19×) because the work outside LBG (mainly image reading and file output) runs on Process 0.",
    "Color images gain more: LBG is 81% of their sequential time, against 77% for grayscale.",
    "Total time is the whole program execution; the shaded bands show the minimum to maximum over the images of each type."];
  s.addShape(p.ShapeType.roundRect, { x: 8.95, y: 1.35, w: 3.9, h: 5.5, rectRadius: 0.08, fill: { color: MIST }, line: { color: MIST, width: 0 } });
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: { code: "25A0", color: TEAL }, breakLine: i < items.length - 1, paraSpaceAfter: 10 } })),
    { x: 9.05, y: 1.45, w: 3.7, h: 5.3, valign: "top", fontFace: "Calibri", fontSize: 15, color: INK, margin: 0.08 });
};
