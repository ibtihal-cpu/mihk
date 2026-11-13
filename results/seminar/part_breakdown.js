module.exports = function (p) {
const INK = "1F1A33", DEEP = "2E2055", TEAL = "2A9D8F", MIST = "F5F1FB";
const s = p.addSlide(); s.background = { color: "FFFFFF" };
s.addShape(p.ShapeType.roundRect, { x: 0.5, y: 0.35, w: 1.9, h: 0.55, rectRadius: 0.1, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
s.addText("Results", { x: 0.5, y: 0.35, w: 1.9, h: 0.55, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 18, bold: true, color: "FFFFFF", margin: 0 });
s.addText("Where the Time Goes", { x: 2.6, y: 0.3, w: 10.2, h: 0.65, valign: "middle", fontFace: "Cambria", fontSize: 28, bold: true, color: DEEP, margin: 0 });
s.addShape(p.ShapeType.rect, { x: 0.5, y: 1.05, w: 12.33, h: 0.04, fill: { color: TEAL }, line: { color: TEAL, width: 0 } });
const r = Math.min(8.2 / 2023, 5.5 / 1231);
s.addShape(p.ShapeType.roundRect, { x: 0.5, y: 1.35, w: 8.2, h: 5.5, rectRadius: 0.08, fill: { color: "FFFFFF" }, line: { color: TEAL, width: 1.25 } });
s.addImage({ path: "assets/breakdown_chart.png", x: 0.5 + (8.2 - 2023 * r) / 2, y: 1.35 + (5.5 - 1231 * r) / 2, w: 2023 * r, h: 1231 * r });
const items = ["LBG training is 77% (gray) and 81% (color) of the sequential run time.",
  "At P = 14 it shrinks to 42% and 60% of the run time.",
  "The other stages do not shrink in the same way, so they become the larger part: about 58% (gray) and 40% (color).",
  "By Amdahl's law this limits the total speedup to 5.00× (gray) and 6.84× (color), against 9.19× for LBG alone."];
s.addShape(p.ShapeType.roundRect, { x: 8.95, y: 1.35, w: 3.9, h: 5.5, rectRadius: 0.08, fill: { color: MIST }, line: { color: MIST, width: 0 } });
s.addText(items.map((t, i) => ({ text: t, options: { bullet: { code: "25A0", color: TEAL }, breakLine: i < items.length - 1, paraSpaceAfter: 9 } })),
  { x: 9.05, y: 1.45, w: 3.7, h: 5.3, valign: "top", fontFace: "Calibri", fontSize: 16, color: INK, margin: 0.08 });
};
