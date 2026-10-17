# Section 4.9 - Table 4.x (studies on image compression and its acceleration)

Legend: no mark = value read by me in the published abstract; (v) = value reported by a secondary source, to be verified in the paper itself before submission.

| Study | Method | Platform | Computational performance | Quality / compression | Limitation |
|---|---|---|---|---|---|
| Bilal et al. [R1], 2024 | Fast LBG with bilinear-interpolation rescaling | Sequential | 50.2% lower computational complexity than LBG; 20% lower memory | No significant loss of quality relative to LBG | Not parallel; codebook-training procedure modified |
| Severo et al. [R2], 2024 | Initialization strategies for swarm-based codebook design | Sequential | Up to 67.05% less codebook-design time | Up to +4.43 dB PSNR (image Clock) | Not parallel; swarm-based design |
| Ranjan and Kumar [R3], 2023 | PCA + 2D Haar DWT + canonical Huffman | Sequential | Not reported | Up to 60% size reduction; PSNR gains of 5 dB (Lena 512x512) and 8 dB (Boat 256x256) over the reference methods | Not parallel; gains are relative to reference methods |
| Vijaywargiya and Pandey [R4], 2025 | SVD + DWT | Sequential | Not reported | PSNR increases with the SVD rank at the expense of compression; up to 89.02 dB at one rank (v) | Not parallel; result depends on the rank |
| Thomas et al. [R5], 2025 | DWT coefficient reduction + Huffman | Sequential | Not reported | CR 1.61:1, PSNR 54.66 dB, SSIM 0.999 on average; Lena 512x512: PSNR 54.28 dB (v) | Low compression ratio; not parallel |
| Pang et al. [R6], 2022 | Fractal + DCT block classification | GPU (CUDA) | About 107x speedup over the basic fractal scheme | PSNR decrease of about 0.4 dB | Different algorithm (fractal) |
| Alzeidi et al. [R7], 2019 | Parallel fractal compression (Fisher classification) | GPU (CUDA) | 6.4x speedup on some images (eight images, 512x512 to 2048x2048) | Not reported in the abstract | Different algorithm (fractal) |
| Hernandez-Lopez et al. [R8], 2022 | Parallel fractal compression, quadtree partition | Multicore CPU and GPU | About 15x (CPU) and 25x (GPU) over serial | Not reported in the abstract | Different algorithm (fractal) |
| **This work** | **LBG + delta + Huffman, MPI, adaptive workload distribution** | **MPI, 14-core hybrid CPU** | **LBG speedup 9.19x at P = 14 (efficiency 65.7%); total-time speedup 5.00x (grayscale), 6.84x (color)** | **Grayscale: CR 25.92, PSNR 29.49 dB, SSIM 0.8266; color: CR 24.47, PSNR 28.80 dB, SSIM 0.7654 (means)** | **One CPU platform; eight images** |
