const pptxgen = require("pptxgenjs");
const spec = require("./overview_spec.json");
const p = new pptxgen(); p.layout = "LAYOUT_WIDE";
const s = p.addSlide(); s.background = { color: "FFFFFF" };
const INK = "1F1A33";
const lines = (txt, opt) => txt.split("\n").map((t, i, a) => ({ text: t, options: Object.assign({ breakLine: i < a.length - 1 }, opt) }));
const top = 0.25, rowH = 1.45, gap = 0.33, hx = 0.4, hw = 2.45, bx0 = 3.05, bw = 2.2, arrow = 0.3;
spec.stages.forEach((st, i) => {
  const y = top + i * (rowH + gap);
  s.addShape(p.ShapeType.roundRect, { x: hx - 0.05, y: y - 0.05, w: 12.58, h: rowH + 0.1, rectRadius: 0.1, fill: { color: st.light }, line: { color: st.color, width: st.hl ? 2.5 : 1, dashType: st.hl ? "dash" : "solid" } });
  s.addShape(p.ShapeType.roundRect, { x: hx, y, w: hw, h: rowH, rectRadius: 0.08, fill: { color: st.color }, line: { color: st.color, width: 0 } });
  s.addText([{ text: st.name, options: { fontSize: 22, bold: true, breakLine: true } }].concat(lines(st.sub, { fontSize: 15 })),
    { x: hx, y, w: hw, h: rowH, align: "center", valign: "middle", fontFace: "Calibri", color: "FFFFFF", margin: 0.06 });
  st.steps.forEach((t, j) => {
    const x = bx0 + j * (bw + arrow);
    s.addShape(p.ShapeType.roundRect, { x, y: y + 0.1, w: bw, h: rowH - 0.2, rectRadius: 0.08, fill: { color: "FFFFFF" }, line: { color: st.color, width: 1.5 } });
    s.addText([{ text: `${j + 1}. ${t[0]}`, options: { fontSize: 16, bold: true, color: st.color, breakLine: true } }].concat(lines(t[1], { fontSize: 13, color: INK })),
      { x, y: y + 0.1, w: bw, h: rowH - 0.2, align: "center", valign: "middle", fontFace: "Calibri", margin: 0.05 });
    if (j < st.steps.length - 1)
      s.addShape(p.ShapeType.rightArrow, { x: x + bw + 0.03, y: y + rowH / 2 - 0.13, w: arrow - 0.06, h: 0.26, fill: { color: INK }, line: { color: INK, width: 0 } });
  });
  if (i < spec.stages.length - 1) {
    s.addText(spec.between[i], { x: 6.95, y: y + rowH + 0.04, w: 5.9, h: gap - 0.08, fontFace: "Calibri", fontSize: 13, italic: true, bold: true, color: "E0457B", valign: "middle", margin: 0 });
    s.addShape(p.ShapeType.downArrow, { x: 6.55, y: y + rowH + 0.06, w: 0.26, h: gap - 0.12, fill: { color: INK }, line: { color: INK, width: 0 } });
  }
});
s.addText(spec.footer, { x: 0.4, y: 7.1, w: 12.5, h: 0.3, align: "center", fontFace: "Calibri", fontSize: 13, italic: true, color: "6B4FA3", margin: 0 });
p.writeFile({ fileName: "figs/overview.pptx" }).then(() => console.log("ok"));
