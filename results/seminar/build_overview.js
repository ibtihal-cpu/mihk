const pptxgen = require("pptxgenjs");
const spec = require("./overview_spec.json");
const p = new pptxgen(); p.layout = "LAYOUT_WIDE";
const s = p.addSlide(); s.background = { color: "FFFFFF" };
const INK = "1F1A33";
s.addText(spec.title, { x: 0.5, y: 0.2, w: 12.3, h: 0.7, fontFace: "Cambria", fontSize: 32, bold: true, color: "2E2055", margin: 0 });
s.addShape(p.ShapeType.rect, { x: 0.5, y: 0.92, w: 12.33, h: 0.04, fill: { color: "E0457B" }, line: { color: "E0457B", width: 0 } });
const top = 1.15, rowH = 1.2, gap = 0.32, hx = 0.5, hw = 2.35, bx0 = 3.05, bw = 2.05, arrow = 0.4;
spec.stages.forEach((st, i) => {
  const y = top + i * (rowH + gap);
  s.addShape(p.ShapeType.roundRect, { x: hx - 0.05, y: y - 0.05, w: 12.43, h: rowH + 0.1, rectRadius: 0.1, fill: { color: st.light }, line: { color: st.color, width: st.hl ? 2.5 : 1, dashType: st.hl ? "dash" : "solid" } });
  s.addShape(p.ShapeType.roundRect, { x: hx, y, w: hw, h: rowH, rectRadius: 0.08, fill: { color: st.color }, line: { color: st.color, width: 0 } });
  s.addText([{ text: st.name, options: { fontSize: 18, bold: true, breakLine: true } }, { text: st.sub, options: { fontSize: 13 } }],
    { x: hx, y, w: hw, h: rowH, align: "center", valign: "middle", fontFace: "Calibri", color: "FFFFFF", margin: 0.06 });
  st.steps.forEach((t, j) => {
    const x = bx0 + j * (bw + arrow);
    s.addShape(p.ShapeType.roundRect, { x, y: y + 0.1, w: bw, h: rowH - 0.2, rectRadius: 0.08, fill: { color: "FFFFFF" }, line: { color: st.color, width: 1.5 } });
    s.addText([{ text: `${j + 1}. ${t[0]}`, options: { fontSize: 14, bold: true, color: st.color, breakLine: true } }, { text: t[1], options: { fontSize: 11, color: INK } }],
      { x, y: y + 0.1, w: bw, h: rowH - 0.2, align: "center", valign: "middle", fontFace: "Calibri", margin: 0.06 });
    if (j < st.steps.length - 1)
      s.addShape(p.ShapeType.rightArrow, { x: x + bw + 0.05, y: y + rowH / 2 - 0.13, w: arrow - 0.1, h: 0.26, fill: { color: INK }, line: { color: INK, width: 0 } });
  });
  if (st.loop) s.addText("↻ " + st.loop, { x: bx0 + 1 * (bw + arrow), y: y + rowH - 0.2, w: 3 * bw, h: 0.2, align: "left", fontFace: "Calibri", fontSize: 10, italic: true, bold: true, color: st.color, margin: 0 });
  if (i < spec.stages.length - 1)
    s.addShape(p.ShapeType.downArrow, { x: 6.55, y: y + rowH + 0.06, w: 0.26, h: gap - 0.12, fill: { color: INK }, line: { color: INK, width: 0 } });
});
s.addText(spec.footer, { x: 0.5, y: 7.05, w: 12.33, h: 0.3, align: "center", fontFace: "Calibri", fontSize: 12, italic: true, color: "6B4FA3", margin: 0 });
p.writeFile({ fileName: "figs/overview.pptx" }).then(() => console.log("ok"));
