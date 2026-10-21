#!/usr/bin/env python3
"""Builds results/Section_4_9.docx : section 4.9 'Comparison with Previous Studies' (text, two tables, references)."""
import os
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = os.path.join(os.path.dirname(__file__), "..", "Section_4_9.docx")
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
P("Previous studies have reduced the cost of image compression through algorithmic simplification, parallelization on GPUs and multicore processors, and workload balancing on heterogeneous platforms. Table 4.x lists representative studies on image compression and its acceleration, Table 4.y lists studies on MPI-based parallel clustering, which is the closest parallel counterpart of the LBG training loop, and Table 4.z lists studies on workload distribution on heterogeneous platforms. Because these studies differ in the compression algorithm, the images, the hardware platform, and the reported metrics, their published results are used to place the present work in context and not as a controlled comparison. Only values reported in the cited studies are given; none of them was re-measured here.")

CAP("Table 4.x. Comparison with studies on image compression and its acceleration.")
TABLE(["Study", "Method", "Platform", "Computational performance", "Quality / compression", "Limitation"], [
    ["Bilal et al. [R1], 2024", "Fast LBG with bilinear-interpolation rescaling", "Sequential", "50.2% lower complexity than LBG; 20% lower memory", "No significant loss of quality relative to LBG", "Not parallel; training procedure modified"],
    ["Severo et al. [R2], 2024", "Initialization of swarm-based codebook design", "Sequential", "Up to 67.05% less design time", "Up to +4.43 dB PSNR", "Not parallel"],
    ["Ranjan and Kumar [R3], 2023", "PCA + 2D Haar DWT + canonical Huffman", "Sequential", "Not reported", "Up to 60% size reduction; PSNR gains of 5 dB (Lena 512 × 512) and 8 dB (Boat 256 × 256) over the reference methods", "Not parallel; gains relative to reference methods"],
    ["Vijaywargiya and Pandey [R4], 2025", "SVD + DWT", "Sequential", "Not reported", "PSNR rises with the SVD rank at the expense of compression", "Not parallel; depends on the rank"],
    ["Thomas et al. [R5], 2025", "DWT reduction + Huffman coding", "Sequential", "Not reported", "CR 1.61:1; PSNR 54.66 dB; SSIM 0.999 (mean)", "Low compression ratio; not parallel"],
    ["Pang et al. [R6], 2022", "Fractal compression with DCT block classification", "GPU (CUDA)", "About 107× over the basic fractal scheme", "PSNR decrease of about 0.4 dB", "Different algorithm (fractal)"],
    ["Alzeidi et al. [R7], 2019", "Parallel fractal compression (Fisher classification)", "GPU (CUDA)", "6.4× on some images (eight images, 512 × 512 to 2048 × 2048)", "Not reported", "Different algorithm (fractal)"],
    ["Hernandez-Lopez et al. [R8], 2022", "Parallel fractal compression, quadtree partition", "Multicore CPU and GPU", "About 15× (CPU) and 25× (GPU) over serial", "Not reported", "Different algorithm (fractal)"],
    ["This work", "LBG + delta + Huffman; MPI; adaptive workload distribution", "MPI; 14-core hybrid CPU", "LBG speedup 9.19× at P = 14 (efficiency 65.7%); total-time speedup 5.00× (grayscale) and 6.84× (color)", "Grayscale: CR 25.92, PSNR 29.49 dB, SSIM 0.8266; color: CR 24.47, PSNR 28.80 dB, SSIM 0.7654 (means)", "One CPU platform; eight images"],
], [2.6, 3.0, 2.0, 3.2, 3.6, 2.6])

CAP("Table 4.y. Comparison with studies on MPI-based parallel clustering (k-means), the closest parallel counterpart of LBG training.")
TABLE(["Study", "Platform", "Reported speedup", "Efficiency (derived)", "Main finding", "Relation to this work"], [
    ["Top et al. [R16], 2020", "MPI; HPC cluster, up to 128 cores", "About 104× clustering time (128 cores)", "About 81% (104 / 128)", "Parallel k-means for image segmentation with MPI; scalability up to 128 cores", "Same MPI scheme for an image-related clustering task; homogeneous cores"],
    ["Tanović et al. [R17], 2024", "OpenMP and MPI; several computers", "Up to 10.2× (12 processor cores)", "About 85% (10.2 / 12), if 12 processes", "Parallel k-means for image classification; scheduling methods varied", "Similar number of cores; different data (MNIST variants)"],
    ["Papakyriakou et al. [R18], 2025", "MPI; Raspberry Pi cluster, 2 to 48 processes", "Runtime reduced by almost 10× from 2 to 48 processes", "About 42% relative to 2 processes (10 / 24)", "Distance computation dominates; MPI_Allreduce synchronization stays manageable", "Same dominant stage and the same collective operation as in LBG training"],
    ["Bhimani et al. [R19], 2015", "OpenMP, MPI, and CUDA; images 300 × 300 to 1164 × 1200", "About 30× for each of the three approaches", "Not derivable", "Best results with OpenMP for smaller images and with CUDA for larger ones", "Shows that OpenMP is competitive for image clustering on shared memory"],
    ["Kwedlo and Czochanski [R20], 2019", "Hybrid MPI/OpenMP", "Strong scaling reported", "Not derivable", "Data divided evenly among MPI processes; hierarchical all-reduce for the centroid update", "Same equal data division as the Equal strategy of this work"],
    ["This work", "MPI; 14-core hybrid CPU (6 P-cores, 8 E-cores)", "LBG: 9.19× at P = 14", "65.7% (9.19 / 14)", "Speed-weighted (Adaptive) distribution reduces the LBG time by 17.2% to 28.3% against equal distribution for P ≥ 8", "Heterogeneous cores; result identical to the sequential one"],
], [2.6, 3.0, 2.8, 2.6, 3.6, 3.6])

P("K-means clustering follows the same iterative structure as the LBG training used here: each vector is assigned to the nearest centroid, and the centroids are then recomputed from the sums of the assigned vectors. MPI implementations of k-means therefore parallelize the same dominant step, the distance computation [R18], and combine the partial sums with a collective reduction [R18, R20]. The efficiencies derived from the published speedups in Table 4.y range from about 42% (relative to two processes) to about 85%, and the efficiency of 65.7% obtained here for 14 processes on a hybrid processor lies within this range. These values are derived from the published speedups and the numbers of processes, and the studies differ in data, hardware, and the baseline used for the speedup, so they indicate the order of magnitude and not a ranking. The efficiencies of [R16] and [R17] refer to homogeneous cores, whereas the present result includes the efficiency loss caused by the efficiency cores of the processor. Studies that compare programming models for image clustering report that shared-memory parallelization with OpenMP can be as effective as MPI on a single machine [R19]; the MPI implementation of this work was chosen for its explicit data distribution and its portability to several nodes, and a comparison with an OpenMP implementation of LBG on the same processor was not performed.")

CAP("Table 4.z. Comparison with studies on workload distribution on heterogeneous platforms.")
TABLE(["Study", "Platform", "Strategy", "Reported finding", "Relation to this work"], [
    ["Zhong et al. [R9], 2011", "MPI; heterogeneous multicore", "Core speed measured dynamically while running only the computational kernel; data partitioned in proportion to the observed speed", "Dynamic, speed-proportional partitioning between cores", "Same principle as the speed calibration of the Adaptive strategy"],
    ["Lastovetsky et al. [R10], 2007", "Heterogeneous processors", "Speed modeled as a function of the problem size", "Partitioning with a functional performance model", "More general; this work uses one measured speed per process"],
    ["Lai et al. [R11], 2018", "Xeon Phi accelerated clusters", "Profiling-based data distribution model", "With even distribution, faster ranks wait for the slowest at synchronization points; 2× speedup over the native model", "Describes the imbalance observed for the Equal strategy at P = 8"],
    ["Bystrov et al. [R12], 2023", "Heterogeneous containers (MPI, OpenCL)", "Resource-aware weighted partitioning", "Up to 32.6% less time than unweighted partitioning", "Similar order of gain to the 28.3% LBG reduction at P = 8 (different application)"],
    ["Żytko et al. [R13], 2025", "Intel 12th and 13th generation processors", "Comparison of P-cores and E-cores", "P-cores 1.3 to 3.2 times faster than E-cores", "Consistent with a speed difference compensated by the Adaptive strategy"],
    ["This work", "Hybrid CPU (6 P-cores, 8 E-cores)", "Speed-weighted distribution (Adaptive) against equal distribution", "Adaptive faster than Equal for P ≥ 8: LBG time 1.39× to 1.21× lower (28.3% to 17.2%); total time 17.9% to 8.8% lower", "Equal and Adaptive differ by at most 1.3% for P ≤ 6"],
], [2.6, 2.6, 3.8, 4.0, 4.0])

P("The comparison shows three points. First, previous accelerations of LBG [R1, R2] reduce the number of operations of a sequential program by modifying the training procedure, whereas the present work distributes the unchanged computation and reproduces the sequential reconstruction exactly (Section 4.8); the two approaches are complementary. Second, the speedups reported for GPU implementations of fractal compression [R6–R8] refer to different algorithms and hardware, and cannot be compared directly with the speedup of 9.19× obtained here for LBG training on a CPU. Third, the methods that reach a high PSNR [R3–R5] operate at much lower compression ratios or are evaluated against other reference methods; for example, the coder of [R5] has a compression ratio of 1.61:1, compared with 25.92 for the present framework, so their PSNR values do not indicate a higher quality at the same compression.")
P("For reference, JPEG and JPEG 2000 applied to the four grayscale images at the same compression ratio gave mean PSNR values of 32.69 dB and 34.93 dB, compared with 29.49 dB for the proposed framework. The objective of this work is not to compete with these codecs in rate–distortion performance but to accelerate the LBG codebook training without changing the verified reconstruction results.")
P("The principle of the Adaptive strategy, partitioning the data in proportion to the measured speed of each processing unit, has been used on heterogeneous platforms [R9, R10], and the cause of the imbalance of the Equal strategy, faster processes waiting for the slowest at synchronization points [R11], agrees with the increase of the Equal-strategy time at P = 8 observed in Section 4.6. Studies of hybrid processors report that performance cores are 1.3 to 3.2 times faster than efficiency cores [R13], and that the benefit of thread pinning depends on the application [R14, R15]. In this work every process was pinned to a core to separate the effect of the distribution strategy from that of operating-system scheduling; this choice is a limitation, since a different scheduling policy may behave differently.")
P("The reviewed studies accelerate LBG by modifying the training procedure on a single processor, or accelerate other compression algorithms on GPUs. To our knowledge, none of them parallelizes the LBG codebook training with MPI while preserving the sequential result and compensating for the speed difference between performance and efficiency cores. This work addresses this gap: the parallel implementation reproduces the sequential reconstruction exactly, reaches a speedup of 9.19× for the LBG stage on 14 processes, and a runtime speed-weighted distribution reduces the LBG time by 17.2% to 28.3% compared with equal distribution on the hybrid processor. The remaining stages of the program, which account for about 58% (grayscale) and 40% (color) of the total time at P = 14, limit the end-to-end speedup and are a direction for future work.")

H("References of Section 4.9 (complete the bibliographic details from the original sources)", 3)
for r in [
    "[R1] Bilal M., Ullah Z., Mujahid O., Fouzder T., “Fast Linde–Buzo–Gray (FLBG) algorithm for image compression through rescaling using bilinear interpolation,” Journal of Imaging, 10(5):124, 2024. https://doi.org/10.3390/jimaging10050124",
    "[R2] Severo V. et al., “On the initialization of swarm intelligence algorithms for vector quantization codebook design,” Sensors, 2024.",
    "[R3] Ranjan R., Kumar P., “An improved image compression algorithm using 2D DWT and PCA with canonical Huffman encoding,” Entropy, 25(10):1382, 2023. https://doi.org/10.3390/e25101382",
    "[R4] Vijaywargiya Y., Pandey R.K., “Hybrid image compression algorithm based on singular value decomposition and discrete wavelet transform,” Procedia Computer Science, 260:1043–1051, 2025. https://doi.org/10.1016/j.procs.2025.03.289",
    "[R5] Thomas S., Krishna A., Govind S., Sahu A.K., “A novel image compression method using wavelet coefficients and Huffman coding,” Journal of Engineering Research, 13(1):361–370, 2025. https://doi.org/10.1016/j.jer.2023.08.015",
    "[R6] Pang J. et al., “A parallel compression framework for fractal images using DCT block classification,” IEEE IUCC/CIT/DSCI/SmartCNS, 2022.",
    "[R7] Alzeidi N. et al., “CUDA implementation of fractal image compression,” Journal of Real-Time Image Processing, 2019.",
    "[R8] Hernandez-Lopez F.J. et al., “Parallel fractal image compression using quadtree partition with task and dynamic parallelism,” Journal of Real-Time Image Processing, 2022.",
    "[R9] Zhong Z. et al., “Data partitioning on heterogeneous multicore platforms,” IEEE International Conference on Cluster Computing, 2011.",
    "[R10] Lastovetsky A.L. et al., “Data partitioning with a functional performance model of heterogeneous processors,” International Journal of High Performance Computing Applications, 2007.",
    "[R11] Lai C. et al., “Performance optimization on Intel Xeon Phi through load balancing,” 2018.",
    "[R12] Bystrov O. et al., “Hybrid parallelization of discrete element software for heterogeneous resources,” Proc. Seventh Int. Conf. on Parallel, Distributed, GPU and Cloud Computing for Engineering, 2023.",
    "[R13] Żytko D. et al., “Analysis of performance and energy efficiency of processors with hybrid architecture,” Journal of Computer Sciences Institute, 2025.",
    "[R14] Velugoti N. et al., “Effects of hybrid CPU and cache architectures on parallel HPC and cloud applications,” 2026.",
    "[R15] Galante G. et al., “To pin or not to pin: that is the question,” SSCAD 2025.",
    "[R16] Top A.E. et al., “Parallel k-means clustering with naive sharding using MPI for unsupervised image segmentation,” Mühendislik Bilimleri ve Tasarım Dergisi, 2020.",
    "[R17] Tanović A. et al., “Implementation of parallel K-means algorithm for image classification using OpenMP and MPI libraries,” Zooming Innovation in Consumer Technologies Conference (ZINC), 2024.",
    "[R18] Papakyriakou D. et al., “Parallel k-means benchmarking on a CPU-bound Beowulf cluster of Raspberry Pi nodes: an MPI-based scaling analysis,” International Journal of Computer Applications, 2025.",
    "[R19] Bhimani J. et al., “Accelerating K-means clustering with parallel implementations and GPU computing,” IEEE High Performance Extreme Computing Conference (HPEC), 2015.",
    "[R20] Kwedlo W., Czochanski P.J., “A hybrid MPI/OpenMP parallelization of K-means algorithms accelerated using the triangle inequality,” IEEE Access, 2019."]:
    p = doc.add_paragraph(r); p.paragraph_format.left_indent = Cm(0.8); p.paragraph_format.first_line_indent = Cm(-0.8)
    for run in p.runs: run.font.size = Pt(10.5)
doc.save(OUT); print("saved", os.path.abspath(OUT))
