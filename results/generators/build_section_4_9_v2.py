#!/usr/bin/env python3
"""Builds results/Section_4_9_v2.docx : section 4.9 'Comparison with Previous Studies' (text, two tables, references)."""
import os
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = os.path.join(os.path.dirname(__file__), "..", "Section_4_9_v2.docx")
doc = Document()
for s in doc.sections:
    s.left_margin = s.right_margin = Cm(2.2); s.top_margin = s.bottom_margin = Cm(2.2)
st = doc.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")

def H(t, lvl=2):
    p = doc.add_paragraph(); r = p.add_run(t); r.bold = True; r.font.size = Pt(14 if lvl == 2 else 12.5); p.paragraph_format.space_before = Pt(10); return p
def P(t):
    p = doc.add_paragraph(t); p.paragraph_format.space_after = Pt(6); p.paragraph_format.line_spacing = 1.15; p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; return p
def CAP(t):
    p = doc.add_paragraph(); r = p.add_run(t); r.bold = True; r.font.size = Pt(11); p.paragraph_format.space_before = Pt(8); p.paragraph_format.keep_with_next = True; return p
def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr(); sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), color); tcPr.append(sh)
def TABLE(head, rows, widths, bold_last=True):
    t = doc.add_table(rows=1, cols=len(head)); t.style = "Table Grid"
    for i, h in enumerate(head):
        c = t.rows[0].cells[i]; c.text = ""; r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(9.5); shade(c, "D9E2F3")
    for k, row in enumerate(rows):
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""; r = cells[i].paragraphs[0].add_run(v); r.font.size = Pt(9.5)
            if bold_last and k == len(rows) - 1: r.bold = True
        if bold_last and k == len(rows) - 1:
            for c in cells: shade(c, "F2F2F2")
    for row in t.rows:
        for i, w in enumerate(widths): row.cells[i].width = Cm(w)
    doc.add_paragraph()

H("4.9 Comparison with Previous Studies")
P("This section compares the proposed framework with previous studies published between 2023 and 2026 that are related to its two main aspects: the MPI-based parallelization of clustering, whose assignment and centroid-update steps are the same as those of the LBG training, and the distribution of workload on heterogeneous processors. Because the studies differ in algorithm, data, hardware platform, and number of processes, their reported results are used to place the present work in context and not as a controlled performance comparison. Only values reported in the cited studies are given, and the efficiencies marked as derived were calculated here from the published speedup and the number of processes; none of the studies was re-measured.")

CAP("Table 4.X. Comparison with previous studies on MPI-based parallel clustering (2023–2026).")
TABLE(["Study", "Parallel approach", "Platform", "Reported speedup", "Efficiency (derived)", "Relation to this work"], [
    ["Saklani et al. [R1], 2023", "MPI k-means (MPICH2)", "Multicore processors and hybrid cluster", "Not stated in the abstract", "Not derivable", "Reports that communication time is significant and that processors of different speed take different times"],
    ["Tanović et al. [R2], 2024", "OpenMP + MPI k-means; scheduling methods varied", "Several computers; 12 processor cores", "Up to 10.2×", "About 85% (10.2 / 12), if 12 processes", "Parallel clustering for image classification on a similar number of cores"],
    ["Papakyriakou et al. [R3], 2025", "MPI k-means; strong scaling", "Raspberry Pi cluster; 2 to 48 processes", "Runtime reduced by almost 10× from 2 to 48 processes", "About 42% relative to 2 processes (10 / 24)", "Distance computation dominates; MPI_Allreduce synchronization stays manageable"],
    ["This work", "MPI-based LBG training; Equal and Adaptive distribution", "Hybrid CPU: 6 P-cores and 8 E-cores; 14 processes", "LBG speedup 9.19× at P = 14", "65.7% (9.19 / 14)", "Heterogeneous cores; result identical to the sequential one"],
], [2.8, 3.0, 3.0, 2.8, 2.6, 3.8])

CAP("Table 4.Y. Comparison with previous studies on workload distribution and scheduling on heterogeneous processors (2023–2026).")
TABLE(["Study", "Platform", "Approach", "Reported finding", "Relation to this work"], [
    ["Bystrov et al. [R4], 2023", "Heterogeneous containers (MPI and OpenCL)", "Resource-aware weighted partitioning", "Up to 32.6% less execution time than unweighted partitioning", "Similar objective; different application"],
    ["Bilbao et al. [R5], 2023", "Intel Alder Lake (asymmetric multicore)", "Asymmetry-aware operating-system scheduling (PMCSched framework)", "Framework for developing scheduling policies; case studies on Alder Lake", "Scheduling at system level, whereas this work balances at application level"],
    ["Żytko et al. [R6], 2025", "Intel 12th and 13th generation processors", "Comparison of P-cores and E-cores", "P-cores 1.3 to 3.2 times faster than E-cores", "Supports the existence of a speed difference to be compensated"],
    ["Moori et al. [R7], 2025", "Intel Alder Lake; NAS benchmarks", "Genetic search of thread count and CPU frequency", "Energy-delay product 66.36% lower than the default Linux configuration", "Configuration tuning for energy, not workload distribution"],
    ["Velugoti et al. [R8], 2026", "Hybrid CPU (Alder Lake)", "Study of parallel HPC workloads on hybrid cores", "Applications with imbalanced work scale better across hybrid cores when thread affinity is disabled", "Relevant to the choice of pinning the processes in this work"],
    ["Galante et al. [R9], 2025", "Hybrid CPU", "Study of CPU pinning", "No universal answer; the benefit of pinning depends on the application", "The pinning used in this work is a methodological choice"],
    ["This work", "Hybrid CPU: 6 P-cores and 8 E-cores", "Speed-weighted distribution (Adaptive) against equal distribution, processes pinned", "LBG time 28.3% to 17.2% lower (1.39× to 1.21×) for P ≥ 8; total time 17.9% to 8.8% lower", "Equal and Adaptive differ by at most 1.3% for P ≤ 6"],
], [2.8, 3.0, 3.6, 4.0, 3.8])

P("The studies in Tables 4.X and 4.Y address two aspects related to the proposed framework: parallel clustering and the distribution of workload on heterogeneous computing platforms. MPI-based clustering studies distribute the distance computation and the centroid update, which are also the central operations of LBG codebook training, and report that the distance computation dominates the runtime while the synchronization by a collective reduction remains manageable [R3]. The efficiencies derived from the published speedups range from about 42% (relative to two processes) to about 85%, and the efficiency of 65.7% obtained here for 14 processes lies within this range; however, the studies differ in data, hardware, and the baseline of the speedup, and the cores of the cited studies are homogeneous, whereas the present result includes the efficiency loss caused by the efficiency cores of the processor. For these reasons the values indicate an order of magnitude and not a ranking.")
P("The second group of studies concerns the differences in processing capability. Performance cores were measured to be 1.3 to 3.2 times faster than efficiency cores [R6], weighted partitioning reduced the execution time by up to 32.6% in a heterogeneous environment [R4], and the benefit of thread pinning depends on the application [R8, R9]. In the proposed framework the Adaptive strategy assigns training vectors in proportion to the measured speed of each MPI process, and it reduced the mean LBG execution time by 17.2% to 28.3% compared with equal distribution for P = 8 to 14, while the two strategies differed by at most 1.3% for P ≤ 6. The MPI implementation reached a mean LBG speedup of 9.19× at 14 processes with a parallel efficiency of 65.7%. Every process was pinned to a core to separate the effect of the distribution strategy from that of operating-system scheduling; since the effect of pinning is application dependent [R8, R9], this choice is a limitation.")
P("Previous accelerations of the LBG algorithm itself, such as the fast LBG of [R10], reduce the computational complexity of a sequential program by modifying the training procedure. To our knowledge, none of the studies reviewed here parallelizes LBG codebook training with MPI while preserving the sequential result and compensating for the speed difference between performance and efficiency cores. In the present work the parallel implementation reproduces the sequential reconstruction exactly (Section 4.8). These findings indicate that adaptive workload distribution can improve the performance of MPI-based LBG when performance and efficiency cores are used together; however, the results are limited to the tested hybrid processor and to eight images, and they do not establish equivalent improvements on other hardware platforms.")

H("References of Section 4.9 (complete the bibliographic details from the original sources)", 3)
for r in [
    "[R1] Saklani R. et al., “Multicore implementation of K-means clustering algorithm,” 2nd International Conference on Applied Artificial Intelligence and Computing (ICAAIC), 2023.",
    "[R2] Tanović A. et al., “Implementation of parallel K-means algorithm for image classification using OpenMP and MPI libraries,” Zooming Innovation in Consumer Technologies Conference (ZINC), 2024.",
    "[R3] Papakyriakou D. et al., “Parallel k-means benchmarking on a CPU-bound Beowulf cluster of Raspberry Pi nodes: an MPI-based scaling analysis with CPU-centric performance evaluation,” International Journal of Computer Applications, 2025.",
    "[R4] Bystrov O. et al., “Hybrid parallelization of discrete element software for heterogeneous resources,” Proc. Seventh Int. Conf. on Parallel, Distributed, GPU and Cloud Computing for Engineering, 2023.",
    "[R5] Bilbao C. et al., “Flexible system software scheduling for asymmetric multicore systems with PMCSched: a case for Intel Alder Lake,” Concurrency and Computation: Practice and Experience, 2023.",
    "[R6] Żytko D. et al., “Analysis of performance and energy efficiency of processors with hybrid architecture,” Journal of Computer Sciences Institute, 2025.",
    "[R7] Moori M.K. et al., “Energy-efficient execution of parallel regions on heterogeneous multi-cores,” 38th SBC/SBMicro/IEEE Symposium on Integrated Circuits and Systems Design (SBCCI), 2025.",
    "[R8] Velugoti N. et al., “Effects of hybrid CPU and cache architectures on parallel HPC and cloud applications,” 2026.",
    "[R9] Galante G. et al., “To pin or not to pin: that is the question,” SSCAD 2025.",
    "[R10] Bilal M., Ullah Z., Mujahid O., Fouzder T., “Fast Linde–Buzo–Gray (FLBG) algorithm for image compression through rescaling using bilinear interpolation,” Journal of Imaging, 10(5):124, 2024. https://doi.org/10.3390/jimaging10050124"]:
    p = doc.add_paragraph(r); p.paragraph_format.left_indent = Cm(0.8); p.paragraph_format.first_line_indent = Cm(-0.8)
    for run in p.runs: run.font.size = Pt(10.5)
doc.save(OUT); print("saved", os.path.abspath(OUT))
