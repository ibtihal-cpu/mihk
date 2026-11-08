from docx import Document
from docx.shared import Pt, Cm
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

rows = [
 # study, venue, topic/method, parallel model & platform, workload distribution, data, key result, relation to thesis, use
 ["Annaji and Rao (2009)\narXiv:0910.4711", "Int. J. Image Processing (arXiv v1, Oct. 2009)",
  "Parallel LBG codebook generation, master/slave, shared memory",
  "OpenMP; results are simulations with 4 processors, codebook 8–128",
  "Equal chunks of the training data to all processors (stated)",
  "2000 training vectors, dimension 2–10 (not images)",
  "Execution-time plots; Amdahl estimate 2.76× for 4 cores if 85% is parallel; no measured speedup table",
  "Closest to parallel LBG; equal partitioning; shared memory, homogeneous, not MPI",
  "Intro [7]; Related Work (Parallel LBG)"],
 ["Hu et al. (2023)\nBDMIP '23", "ACM, Xiamen, Nov. 2023, doi 10.1145/3645279.3645280",
  "Parallel fractal compression of transmission-line video images",
  "MPI and MPI+OpenMP; two Celeron 1.8 GHz PCs on a LAN, MPICH, Windows XP (the text also mentions three nodes)",
  "Each frame divided horizontally into n blocks; process 0 reads, divides, compresses one block and sends the rest",
  "Video frames 1800 × 960",
  "Parallel efficiency (Fig. 4) and time (Fig. 5) in figures; no speedup numbers in the text; states MPI suits homogeneous clusters",
  "MPI in image compression; homogeneous platform; no heterogeneity",
  "Intro [6]; Related Work (parallel image compression)"],
 ["Bilal et al. (2024)", "J. Imaging 10(5):124, doi 10.3390/jimaging10050124",
  "Fast LBG (FLBG): bilinear rescaling + match function",
  "Sequential; Intel Core i5-3210M, MATLAB R2019a",
  "Not applicable",
  "512 × 512 gray: Cameraman, Baboon, Peppers, Barb, Goldhill; codebook 8–1024",
  "Computational complexity −50.2% vs LBG, above 97% vs swarm-based LBG; memory −20%; PSNR comparable to LBG",
  "Algorithmic acceleration of LBG (not parallel); shares Cameraman and Peppers",
  "Intro [4]; Related Work (LBG improvements)"],
 ["Fernández-Fraga et al. (2024)", "SAC '24, Avila, Apr. 2024, doi 10.1145/3605098.3635986",
  "Dynamic load balancing with MPI RMA (one-sided) for ParRADMeth (genomics)",
  "MPI/OpenMP; cluster of 8 nodes × 32 cores (Xeon Silver 4216)",
  "Dynamic: blocks assigned at run time; compared with static distribution",
  "Genomic methylation datasets",
  "Up to 243× vs sequential and 1.74× vs the previous parallel version",
  "Dynamic balancing of irregular tasks on a homogeneous cluster; differs from rate-based static split on hybrid cores",
  "Intro [9]; Related Work (load balancing)"],
 ["Velugoti et al. (2026)\narXiv:2608.23165", "arXiv, 24 Aug. 2026",
  "Effects of hybrid P/E cores and cache on parallel HPC workloads",
  "OpenMP threads; Intel Alder Lake (8 P + 8 E cores); miniVite and NAS SP, BT, LU, FT",
  "Not a distribution method; studies thread scaling and affinity",
  "Benchmarks, not images",
  "Scaling changes across the P/E boundary; imbalanced workloads scale better across hybrid cores with affinity disabled; E-cores about 60% of P-core speed (as stated)",
  "Motivation: P/E cores behave differently; OpenMP, not MPI",
  "Intro [8]; Related Work (hybrid CPUs)"],
 ["Li and U (2026)", "Electronics 15(5):922, doi 10.3390/electronics15050922",
  "Fast fractal compression, non-uniform partition, vectorization",
  "MATLAB; Intel Core i5-9500 (CPU), Tesla T4 (GPU), parfor",
  "Not applicable (GPU/parfor not faster on 512 × 512 images)",
  "512 × 512: Zelda, Peppers, Plane, Cameraman, CT; larger Kodim and RSI images",
  "Peppers CR 21.10, PSNR 31.43; Cameraman CR 20.29, PSNR 32.53; encoding about 2 s",
  "Same images (Peppers, Cameraman); algorithmic, not parallel, acceleration",
  "Chapter 4 Table 4.21; Related Work (accelerated compression)"],
 ["Zangana (2025)", "EAI Endorsed Trans. AI Robotics, doi 10.4108/airo.7832",
  "Bitplane, wavelet and predictive coding, GPU/FPGA",
  "CUDA/OpenCL; GPUs, model not stated",
  "Dynamic work stealing (stated)",
  "Images not specified",
  "9.09× on 16 GPUs vs 1 GPU (1000 ms to 110 ms); quality values not verifiable",
  "Parallel image compression; no stated images or hardware model",
  "Chapter 4 Table 4.22"],
 ["Pang et al. (2022)", "IEEE IUCC 2022, doi 10.1109/IUCC-CIT-DSCI-SmartCNS57392.2022.00047",
  "Fractal compression with DCT block classification",
  "CUDA; Intel i7-9700 + RTX 2070, Python",
  "Not applicable",
  "256 × 256 gray: Lena, Baboon, Peppers, Boat, germ, cell",
  "Speedup 89.75× to 107.88× vs a slow Python baseline (about 120 s)",
  "Algorithm shown in this work's reference implementation (classification); baseline not comparable",
  "Not used in tables (image size and baseline differ)"],
 ["Hernandez-Lopez and Muñiz-Pérez (2022)", "J. Real-Time Image Process. 19:391–402, doi 10.1007/s11554-021-01193-w (full text read)",
  "Parallel fractal compression, quadtree, classification",
  "OpenMP tasks on CPU; CUDA dynamic parallelism on GPU. Laptop: i7-4720HQ (8 threads), GTX 980M. Server: i9-9920X (24 threads), TITAN RTX; 20 runs, mean",
  "Dynamic: tasks created by the quadtree recursion",
  "Peppers, Boat, Cameraman, Baboon at 256 x 256 (laptop); Boat, Baboon at 512 x 512 and Male, Airport at 1024 x 1024 (server); D3 domain library",
  "Laptop 256 x 256: 2.25x (2 threads) to 6.06x (8 threads); GPU slower than serial. Server, tol = 5: 24 threads 13.5x-14.9x, GPU 17.3x-24.5x; tol = 20: 7.1x-9.5x (24 threads), 5.0x-10.4x (GPU)",
  "Shows that speedup depends on image size and tolerance; same family of images (names), different sizes and algorithm",
  "Chapter 4 Table 4.22 (corrected values); Related Work"],
 ["Chitra et al. (1997)", "IFAC Proc. Vol. 30(25):307-312 (cited in Hernandez-Lopez)",
  "Parallel fractal coding, quadtree, master-slave", "Multi-core system (as reported)", "Four partitions of the image assigned to slave processors",
  "512 x 512 (as reported)", "1.80x (as reported)", "Early parallel quadtree fractal coding", "Related Work (second-hand; verify the original)"],
 ["Cao and Gu (2010)", "ICEEE 2010 (cited in Hernandez-Lopez)",
  "OpenMP parallel Jacquin fractal encoding", "OpenMP; four physical cores at 2.33 GHz (as reported)", "Loop over horizontal partitions",
  "512 x 512 (as reported)", "Almost 6x (as reported)", "OpenMP fractal encoding", "Related Work (second-hand; verify the original)"],
 ["Khan and Akhtar (2013)", "ITTC 2013 (cited in Hernandez-Lopez)",
  "Fractal compression on CUDA", "CUDA GPU", "Range and domain blocks mapped to thread blocks",
  "512 x 512 (as reported)", "10.75x (as reported)", "GPU fractal compression", "Related Work (second-hand; verify the original)"],
 ["Chauhan et al. (2014)", "SocProS 2012, Springer (cited in Hernandez-Lopez)",
  "Fractal compression on a pipelined GPU cluster", "Cluster of 24 GPUs, master and slaves", "Dynamic allocation in a circulating pipeline",
  "Not stated in the citing paper", "Almost 14x (as reported)", "GPU cluster", "Related Work (second-hand; verify the original)"],
 ["Al Sideiri et al. (2020)", "J. Real-Time Image Process. 17(5):1375-1387 (cited in Hernandez-Lopez)",
  "CUDA fractal compression with Fisher classification", "CUDA GPU", "Quadtree linearized, kernels launched per level",
  "1024 x 1024 (as reported)", "4.9x (as reported)", "GPU fractal compression with classification", "Related Work (second-hand; verify the original)"],
 ["SairaBanu et al. (2015)", "Indian J. Sci. Technol. 8(13)",
  "Parallel SVD image compression, OpenMP",
  "OpenMP; dual-core Intel processor",
  "Not applicable",
  "320 × 240, 550 × 500, 610 × 423 images",
  "Speedup about 1.15",
  "Weak and old", "Not used"],
 ["Huang et al. (C-Coll)", "arXiv:2304.03890 (IPDPS 2024)",
  "Lossy compression of MPI messages", "MPI collectives on HPC clusters", "Not applicable",
  "Scientific data", "1.8–2.7× on MPI collectives", "Not image compression", "Not used"],
 ["Yao et al. (MPI-PRV)", "Predictive monitoring of MPI programs",
  "Verification of MPI programs", "Not applicable", "Not applicable", "MPI applications",
  "Bug detection efficiency", "Not related to compression or load balancing", "Not used"],
]
head = ["Study", "Venue", "Topic / method", "Parallel model and platform", "Workload distribution", "Data used", "Main result (as stated)", "Relation to this thesis", "Where used"]

doc = Document()
sec = doc.sections[0]; sec.orientation = WD_ORIENT.LANDSCAPE
sec.page_width, sec.page_height = sec.page_height, sec.page_width
sec.left_margin = sec.right_margin = Cm(1.2); sec.top_margin = sec.bottom_margin = Cm(1.2)
st = doc.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(8)
p = doc.add_paragraph(); r = p.add_run('Summary of the studies read in full (or in abstract) for Chapters 1 and 4'); r.bold = True; r.font.size = Pt(12)
t = doc.add_table(rows=1, cols=len(head)); t.style = 'Table Grid'
def shade(cell):
    tcPr = cell._tc.get_or_add_tcPr(); shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), 'D9D9D9'); tcPr.append(shd)
for j, h in enumerate(head):
    c = t.rows[0].cells[j]; c.text = ''; rr = c.paragraphs[0].add_run(h); rr.bold = True; rr.font.size = Pt(8); shade(c)
for row in rows:
    cells = t.add_row().cells
    for j, v in enumerate(row):
        cells[j].text = ''; cells[j].paragraphs[0].add_run(v).font.size = Pt(7.5)
doc.add_paragraph()
doc.add_paragraph('Notes: values are those stated in the papers. Wakatani (2005), Bystrov et al. (2023), Severo et al. (2024), Zhu (2012), Thomas et al. (2025), Ranjan and Kumar (2023) and Ungureanu et al. (2024) have not been read in full in this work.')
doc.save('Literature_Summary.docx')

with open('Literature_Summary.md', 'w') as f:
    f.write('# Summary of the studies read\n\n| ' + ' | '.join(head) + ' |\n|' + '---|' * len(head) + '\n')
    for row in rows:
        f.write('| ' + ' | '.join(v.replace('\n', ' ').replace('|', '/') for v in row) + ' |\n')
print('ok')
