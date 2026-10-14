import re
s=open('build_seminar.js',encoding='utf-8').read()
lines=s.split('\n')
marks=[i for i,l in enumerate(lines) if l.startswith('  // =================')]
end=[i for i,l in enumerate(lines) if 'await pres.writeFile' in l][0]
head='\n'.join(lines[:marks[0]])
tail='\n'.join(lines[end:])
blocks={}
for k,(a,b) in enumerate(zip(marks,marks[1:]+[end])):
    blocks[k+1]='\n'.join(lines[a:b])

AGENDA='''  // ================= 2. Outline =================
  {
    const s = cs("Agenda", "Outline",
      "Nine parts, following the structure of the seminar: introduction, related work, problems, objectives, the proposed method, the parallel strategy, results, conclusion and references.");
    const items = ["Introduction", "Related work", "Research problems", "Research objective", "Proposed method",
      "Proposed parallel computing strategies", "Results and discussion", "Conclusion", "References"];
    items.forEach((it, i) => {
      const col = i < 5 ? 0 : 1, row = i < 5 ? i : i - 5;
      const x = 0.6 + col * 6.2, y = 1.6 + row * 1.02;
      card(s, x, y, 5.9, 0.88, MIST, "Agenda card");
      s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: y + 0.14, w: 0.6, h: 0.6, fill: { color: i % 2 ? MAG : PURPLE }, line: { color: WHITE, width: 0 }, objectName: "Number circle" });
      T(s, String(i + 1), { x: x + 0.2, y: y + 0.14, w: 0.6, h: 0.6, fontSize: 20, bold: true, color: WHITE, align: "center", valign: "middle", fontFace: HF });
      T(s, it, { x: x + 1.05, y: y + 0.04, w: 4.7, h: 0.8, fontSize: 19, bold: true, color: INK, valign: "middle" });
    });
  }
'''

PROB='''  // ================= Research problems =================
  {
    const s = cs("Research problems", "Research problems",
      "Four problems motivate the work: delay in sending data, big data storage, the cost of obtaining a good compression ratio, and the need for acceptable quality.");
    const probs = [[ic.clock, "Delay in sending data", "Large images take a long time to transmit over a network.", PURPLE],
      [ic.db, "Big data storage", "Image collections need a large amount of storage.", MAG],
      [ic.cogs, "Complexity versus time", "A good compression ratio needs complex methods (here: iterative LBG training), so execution time becomes high.", TEAL],
      [ic.img, "Acceptable quality", "The reconstructed image must remain of acceptable quality (PSNR, SSIM).", GOLD]];
    probs.forEach((p, i) => {
      const x = 0.6 + (i % 2) * 6.15, y = 1.7 + Math.floor(i / 2) * 2.6;
      card(s, x, y, 5.95, 2.4, MIST, "Problem card");
      s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: y + 0.35, w: 0.85, h: 0.85, fill: { color: p[3] }, line: { color: p[3], width: 0 }, objectName: "Icon circle" });
      s.addImage({ data: p[0], x: x + 0.3 + 0.21, y: y + 0.35 + 0.21, w: 0.43, h: 0.43, objectName: "Icon" });
      T(s, (i + 1) + "  " + p[1], { x: x + 1.4, y: y + 0.3, w: 4.35, h: 0.6, fontSize: 20, bold: true });
      T(s, p[2], { x: x + 1.4, y: y + 0.95, w: 4.35, h: 1.3, fontSize: 16, color: MUTED });
    });
  }
'''

OBJ='''  // ================= Research objective =================
  {
    const s = cs("Research objective", "Research objective",
      "Two objectives: a good compression ratio with parallel speed, and preserved quality. The right-hand column shows how the work meets each one.");
    const objs = [["Develop an image-compression method with a good compression ratio, using parallel processing to reduce its execution time.",
        "LBG vector quantization + delta + Huffman coding, parallelized with MPI (Equal and speed-aware Adaptive distribution)."],
      ["Maintain the quality of the reconstructed image as much as possible.",
        "Quality measured by PSNR and SSIM; the parallel result is verified to be identical to the sequential one (MD5)."]];
    objs.forEach((o, i) => {
      const y = 1.7 + i * 2.6;
      card(s, 0.6, y, 6.6, 2.4, MIST, "Objective card");
      s.addShape(pres.shapes.OVAL, { x: 0.85, y: y + 0.35, w: 0.7, h: 0.7, fill: { color: i ? MAG : PURPLE }, line: { color: WHITE, width: 0 }, objectName: "Objective number" });
      T(s, String(i + 1), { x: 0.85, y: y + 0.35, w: 0.7, h: 0.7, fontSize: 24, bold: true, color: WHITE, align: "center", valign: "middle", fontFace: HF });
      T(s, "Objective", { x: 1.8, y: y + 0.3, w: 5.2, h: 0.4, fontSize: 14, bold: true, color: i ? MAG : PURPLE, charSpacing: 2 });
      T(s, o[0], { x: 1.8, y: y + 0.75, w: 5.2, h: 1.5, fontSize: 17, valign: "top" });
      s.addShape(pres.shapes.RIGHT_ARROW, { x: 7.35, y: y + 0.95, w: 0.5, h: 0.5, fill: { color: LAV }, line: { color: LAV, width: 0 }, objectName: "Arrow" });
      card(s, 8.0, y, 4.73, 2.4, WHITE, "How card");
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.0, y, w: 4.73, h: 2.4, fill: { color: WHITE }, line: { color: i ? MAG : PURPLE, width: 1.5 }, rectRadius: 0.12, objectName: "How frame" });
      T(s, "How this work meets it", { x: 8.25, y: y + 0.2, w: 4.3, h: 0.4, fontSize: 14, bold: true, color: i ? MAG : PURPLE });
      T(s, o[1], { x: 8.25, y: y + 0.7, w: 4.3, h: 1.6, fontSize: 15, color: INK });
    });
  }
'''
order=[1,'AG',3,4,5,6,7,'P','O',9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,34,35,36,37,38,39,40]
tag={}
for n in (3,4,5): tag[n]="1 · Introduction"
for n in (6,7): tag[n]="2 · Related work"
tag['P']="3 · Research problems"
for n in ('O',9): tag[n]="4 · Research objective"
for n in range(10,16): tag[n]="5 · Proposed method"
for n in range(16,20): tag[n]="6 · Proposed parallel computing strategies"
for n in list(range(20,33))+[34,35]: tag[n]="7 · Results and discussion"
for n in (36,37,38): tag[n]="8 · Conclusion"
tag[39]="9 · References"
out=[head]
for n in order:
    if n=='AG': b=AGENDA
    elif n=='P': b=PROB
    elif n=='O': b=OBJ
    else: b=blocks[n]
    if n in tag:
        b=re.sub(r'cs\("[^"]*",','cs("%s",'%tag[n],b,count=1)
    out.append(b)
out.append(tail)
res='\n'.join(out)
# slide 14 note
a='T(s, "A 5-byte table entry would lower CR by about 1%.", { x: 8.1, y: 5.55, w: 4.4, h: 0.85, fontSize: 13, color: MUTED, italic: true });'
assert a in res
res=res.replace(a,'T(s, "CR is computed from these sizes; the program does not write a stored file. A 5-byte table entry would lower CR by about 1%.", { x: 8.1, y: 5.5, w: 4.4, h: 0.95, fontSize: 12, color: MUTED, italic: true });')
open('build_seminar_v2.js','w',encoding='utf-8').write(res)
print('blocks:',len(order))
