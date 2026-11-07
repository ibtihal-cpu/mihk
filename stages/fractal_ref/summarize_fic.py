#!/usr/bin/env python3
"""Summarize run_fic.sh output: median ET/DT over repetitions, speedup and efficiency per image and thread count.
usage: python3 summarize_fic.py fic_tol16.txt"""
import re, sys, statistics as st, collections
d = collections.defaultdict(list)
for line in open(sys.argv[1]):
    m = re.match(r"(\S+) rep=\d+ threads=(\d+) tol=([\d.]+) leaves=(\d+) bytes=(\d+) CR=([\d.]+) PSNR=([\d.]+) ET=([\d.]+) DT=([\d.]+) checksum=(\w+)", line)
    if m:
        img, T = m.group(1), int(m.group(2))
        d[(img, T)].append(dict(cr=float(m.group(6)), psnr=float(m.group(7)), et=float(m.group(8)), dt=float(m.group(9)), ck=m.group(10)))
imgs = sorted({k[0] for k in d})
for img in imgs:
    ts = sorted(t for (i, t) in d if i == img)
    base = st.median(r["et"] for r in d[(img, 1)])
    cks = {r["ck"] for t in ts for r in d[(img, t)]}
    r1 = d[(img, 1)][0]
    print(f"\n{img}: CR={r1['cr']:.2f}  PSNR={r1['psnr']:.2f} dB  identical output for all thread counts: {'yes' if len(cks)==1 else 'NO'}")
    print(f"{'T':>3} {'ET(s)':>8} {'DT(s)':>8} {'Speedup':>8} {'Eff(%)':>7}")
    for t in ts:
        et = st.median(r["et"] for r in d[(img, t)]); dt = st.median(r["dt"] for r in d[(img, t)])
        print(f"{t:>3} {et:>8.4f} {dt:>8.4f} {base/et:>8.2f} {100*base/et/t:>7.1f}")
