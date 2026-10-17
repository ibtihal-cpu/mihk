const pptxgen = require("pptxgenjs");
const spec = require("./overview_spec.json");
const p = new pptxgen(); p.layout = "LAYOUT_WIDE";
const s = p.addSlide(); s.background = { color: "FFFFFF" };
const INK = "1F1A33";
const lines = (txt, opt) => txt.split("\n").map((t, i, a) => ({ text: t, options: Object.assign({ breakLine: i < a.length - 1 }, opt) }));
const PAR="E07B22", SEQ="5B6770";
const chip=(x,y,w,tag)=>{const c=tag==="par"?PAR:SEQ;s.addShape(p.ShapeType.roundRect,{x,y,w,h:0.28,rectRadius:0.14,fill:{color:c},line:{color:"FFFFFF",width:1}});s.addText(tag==="par"?"PARALLEL: all ranks":"SEQUENTIAL: Rank 0",{x,y,w,h:0.28,align:"center",valign:"middle",fontFace:"Calibri",fontSize:11,bold:true,color:"FFFFFF",margin:0});};
const top = 0.25, rowH = 1.45, gap = 0.33, hx = 0.4, hw = 2.45, bx0 = 3.05, bw = 2.2, arrow = 0.3;
spec.stages.forEach((st, i) => {
  const y = top + i * (rowH + gap);
  s.addShape(p.ShapeType.roundRect, { x: hx - 0.05, y: y - 0.05, w: 12.58, h: rowH + 0.1, rectRadius: 0.1, fill: { color: st.light }, line: { color: st.color, width: st.hl ? 2.5 : 1, dashType: st.hl ? "dash" : "solid" } });
  s.addShape(p.ShapeType.roundRect, { x: hx, y, w: hw, h: rowH, rectRadius: 0.08, fill: { color: st.color }, line: { color: st.color, width: 0 } });
  s.addText([{ text: st.name, options: { fontSize: 22, bold: true, breakLine: true } }].concat(lines(st.sub, { fontSize: 15 })),
    { x: hx, y, w: hw, h: rowH - 0.35, align: "center", valign: "middle", fontFace: "Calibri", color: "FFFFFF", margin: 0.06 });
  s.addShape(p.ShapeType.roundRect,{x:hx+0.12,y:y+rowH-0.4,w:hw-0.24,h:0.32,rectRadius:0.16,fill:{color:"FFFFFF"},line:{color:"FFFFFF",width:0}});
  s.addText(st.tag==="par"?"PARALLEL: all ranks":"SEQUENTIAL: Rank 0",{x:hx+0.12,y:y+rowH-0.4,w:hw-0.24,h:0.32,align:"center",valign:"middle",fontFace:"Calibri",fontSize:12,bold:true,color:st.tag==="par"?PAR:SEQ,margin:0});
  st.steps.forEach((t, j) => {
    const x = bx0 + j * (bw + arrow);
    s.addShape(p.ShapeType.roundRect, { x, y: y + 0.1, w: bw, h: rowH - 0.2, rectRadius: 0.08, fill: { color: st.parstep === j ? "FDEBD9" : "FFFFFF" }, line: { color: st.parstep === j ? PAR : st.color, width: st.parstep === j ? 2.5 : 1.5, dashType: st.parstep === j ? "dash" : "solid" } });
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
const lg=(x,tag,txt)=>{s.addShape(p.ShapeType.roundRect,{x,y:7.08,w:0.5,h:0.24,rectRadius:0.12,fill:{color:tag==="par"?PAR:SEQ},line:{color:"FFFFFF",width:0}});s.addText(txt,{x:x+0.6,y:7.06,w:4.2,h:0.28,fontFace:"Calibri",fontSize:13,bold:true,color:"1F1A33",margin:0,valign:"middle"});};
lg(2.6,"par","Parallel: all MPI ranks work together");lg(7.4,"seq","Sequential: executed on Rank 0 only");
p.writeFile({ fileName: "figs/overview.pptx" }).then(() => console.log("ok"));
