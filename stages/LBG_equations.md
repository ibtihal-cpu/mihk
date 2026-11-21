---
title: "LBG equations and sources (ready to paste)"
---

**Notation.** The image is divided into $N = 16{,}384$ blocks of $4 \times 4$ pixels (512 × 512 image). Each block is a vector $\mathbf{x}_n \in \mathbb{R}^{16}$, $n = 1, \dots, N$. The codebook is $\mathcal{C} = \{\mathbf{c}_1, \dots, \mathbf{c}_K\}$ with $K = 64$.

**Squared Euclidean distance** between a vector and a codeword:

$$d(\mathbf{x}, \mathbf{c}_j) = \sum_{i=1}^{16} \left( x_i - c_{j,i} \right)^2 = \left\lVert \mathbf{x} - \mathbf{c}_j \right\rVert_2^2 \qquad (1)$$

**Nearest-codeword rule** (the index stored for block $n$):

$$I_n = \arg\min_{1 \le j \le K} \, d(\mathbf{x}_n, \mathbf{c}_j) \qquad (2)$$

**Cell of codeword $j$:**

$$S_j = \left\{ \mathbf{x}_n : I_n = j \right\} \qquad (3)$$

**Centroid update** (a codeword with an empty cell is left unchanged):

$$\mathbf{c}_j = \frac{1}{\lvert S_j \rvert} \sum_{\mathbf{x}_n \in S_j} \mathbf{x}_n \qquad (4)$$

**Average distortion:**

$$D = \frac{1}{N} \sum_{n=1}^{N} \min_{1 \le j \le K} \, d(\mathbf{x}_n, \mathbf{c}_j) \qquad (5)$$

**Stopping rule** of one splitting stage (iteration $m$), with $\varepsilon = 10^{-4}$ and at most 100 iterations per stage:

$$\frac{D_{m-1} - D_m}{D_m} \le \varepsilon \qquad (6)$$

**Initial codeword** (global mean):

$$\mathbf{c}_1 = \frac{1}{N} \sum_{n=1}^{N} \mathbf{x}_n \qquad (7)$$

**Codeword splitting**, with $\delta = 0.01$; the codebook size doubles at each stage, $K = 1 \rightarrow 2 \rightarrow 4 \rightarrow \dots \rightarrow 64$ (six stages):

$$\mathbf{c}_j^{(1)} = (1 + \delta)\,\mathbf{c}_j, \qquad \mathbf{c}_j^{(2)} = (1 - \delta)\,\mathbf{c}_j \qquad (8)$$

**Sentence for the thesis.** The LBG algorithm was introduced by Linde et al. [1]; the nearest-neighbor and centroid conditions behind Eqs. (2) and (4) are treated in [2], and recent studies address LBG-based codebook design for image compression [3], [4].

**References** (IEEE style)

[1] Y. Linde, A. Buzo, and R. M. Gray, "An algorithm for vector quantizer design," *IEEE Trans. Commun.*, vol. COM-28, no. 1, pp. 84–95, Jan. 1980.

[2] A. Gersho and R. M. Gray, *Vector Quantization and Signal Compression*. Boston, MA, USA: Kluwer Academic Publishers, 1992.

[3] V. Severo, F. B. S. Ferreira, R. Spencer, A. Nascimento, and F. Madeiro, "On the initialization of swarm intelligence algorithms for vector quantization codebook design," *Sensors*, vol. 24, no. 8, Art. no. 2606, 2024, doi: 10.3390/s24082606.

[4] M. Bilal, Z. Ullah, O. Mujahid, and T. Fouzder, "Fast Linde–Buzo–Gray (FLBG) algorithm for image compression through rescaling using bilinear interpolation," *J. Imaging*, vol. 10, no. 5, Art. no. 124, 2024, doi: 10.3390/jimaging10050124.

**Check before submitting.** (a) Equation numbers (1)–(8) are temporary. (b) References [3] and [4] were identified from their publisher records (authors, journal, volume, DOI), but their full texts were not opened here: open Section 2 of [3] and the LBG section of [4] and confirm that they contain the distance and nearest-codeword formulation before citing a section or an equation number. (c) Eq. (8) is the multiplicative splitting used in the program (codebook$[k+i] = (1-\delta)\,$codebook$[i]$); the original paper [1] describes the splitting with a perturbation, so write "following the splitting initialization of LBG [1]".
