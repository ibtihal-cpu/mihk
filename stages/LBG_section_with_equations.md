---
title: "Vector quantization and LBG section, with the 8 equations (ready to paste)"
---

*(The text starts after "...not identical to the original image [12].")*

Let each $4 \times 4$ block of the image be a vector $\mathbf{x} \in \mathbb{R}^{16}$, and let $\mathcal{C} = \{\mathbf{c}_1, \dots, \mathbf{c}_K\}$ be the codebook, with $K = 64$ codewords. The distortion between a vector and a codeword is measured by the squared Euclidean distance

$$d(\mathbf{x}, \mathbf{c}_j) = \sum_{i=1}^{16} \left( x_i - c_{j,i} \right)^2 = \left\lVert \mathbf{x} - \mathbf{c}_j \right\rVert_2^2 \qquad (1)$$

The quantization operation can be expressed as

$$Q(\mathbf{x}) = \mathbf{c}_{j^*}, \qquad j^* = \arg\min_{1 \le j \le K} \, d(\mathbf{x}, \mathbf{c}_j) \qquad (2)$$

where $\mathbf{x}$ is an input vector and $\mathbf{c}_{j^*}$ is the codeword that minimizes the distortion between the input vector and the available codewords. For the $n$-th block $\mathbf{x}_n$, the index $I_n = j^*(\mathbf{x}_n)$ is stored instead of the block itself.

The codebook is designed with the Linde–Buzo–Gray (LBG) algorithm [LBG80], which is based on the nearest-neighbor and centroid conditions [GG92]. The training set consists of the $N = 16{,}384$ non-overlapping blocks of the image. The algorithm starts with a single codeword, the mean of the training vectors,

$$\mathbf{c}_1 = \frac{1}{N} \sum_{n=1}^{N} \mathbf{x}_n \qquad (3)$$

and doubles the size of the codebook at each stage by splitting every codeword into two slightly perturbed copies,

$$\mathbf{c}_j^{(1)} = (1 + \delta)\,\mathbf{c}_j, \qquad \mathbf{c}_j^{(2)} = (1 - \delta)\,\mathbf{c}_j \qquad (4)$$

with $\delta = 0.01$, so that the codebook grows from 1 to 64 codewords in six stages. In each stage, two steps are repeated. First, every training vector is assigned to the cell of its nearest codeword,

$$S_j = \left\{ \mathbf{x}_n : j^*(\mathbf{x}_n) = j \right\} \qquad (5)$$

Second, every codeword is replaced by the centroid of its cell,

$$\mathbf{c}_j = \frac{1}{\lvert S_j \rvert} \sum_{\mathbf{x}_n \in S_j} \mathbf{x}_n \qquad (6)$$

and a codeword whose cell is empty is left unchanged. After each iteration $m$, the average distortion

$$D_m = \frac{1}{N} \sum_{n=1}^{N} \min_{1 \le j \le K} \, d(\mathbf{x}_n, \mathbf{c}_j) \qquad (7)$$

is computed, and the stage stops when its relative decrease falls below the threshold $\varepsilon$, or after at most 100 iterations:

$$\frac{D_{m-1} - D_m}{D_m} \le \varepsilon, \qquad \varepsilon = 10^{-4} \qquad (8)$$

For color images, vector quantization can be applied independently to the red, green, and blue channels. Each channel is treated as a grayscale image and uses a separate codebook. The VQ indices are generated and decoded separately for each channel, after which the three reconstructed channels are combined to form the output color image.

---

**Notes (not part of the thesis text).**

1. Replace the placeholders with your reference numbers: [LBG80] = Linde, Buzo, Gray (1980), IEEE Trans. Commun., vol. COM-28, no. 1, pp. 84–95; [GG92] = Gersho and Gray, *Vector Quantization and Signal Compression*, Kluwer, 1992. If you also cite the recent studies, add them after the first sentence of the LBG paragraph: Severo et al., Sensors 24(8), 2606, 2024 (doi:10.3390/s24082606) and Bilal et al., J. Imaging 10(5), 124, 2024 (doi:10.3390/jimaging10050124); check their text before citing a section or an equation number.
2. Eqs. (1)–(8) correspond to the program: the distance and the nearest codeword (distance16 and the search loop), the initial mean, the multiplicative splitting with $\delta = 0.01$ (codebook$[k+i] = (1-\delta)\,$codebook$[i]$), the centroid with exact sums, the relative decrease of the distortion with $\varepsilon = 0.0001$, and the limit of 100 iterations per stage (Section 4.4 explains that the reported iteration count is the total over the six stages).
3. Eq. (4) is the multiplicative perturbation used in the program; the original paper describes the splitting with a perturbation, so the sentence says "slightly perturbed copies".
4. The equation numbers (1)–(8) are temporary.
