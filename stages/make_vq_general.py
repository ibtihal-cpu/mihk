#!/usr/bin/env python3
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
d = Document(); st = d.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(12)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
for s in d.sections: s.left_margin = s.right_margin = Cm(2.5)
def P(t, it=False):
    p = d.add_paragraph(); r = p.add_run(t); r.italic = it; p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; p.paragraph_format.space_after = Pt(8)
def E(t, n):
    p = d.add_paragraph(); r = p.add_run(f'{t}\t\t({n})'); r.font.name = 'Cambria Math'; r.font.size = Pt(13)
    p.paragraph_format.left_indent = Cm(1.0); p.paragraph_format.space_after = Pt(8)
h = d.add_heading('General explanation of vector quantization (ready to paste)', 1)
P('Starts after: "... not identical to the original image [12]."', it=True)
P('In vector quantization (VQ), the image is divided into non-overlapping blocks, and each block is treated as a vector. '
  'In this work, the blocks have 4 × 4 pixels, so every vector has 16 components. A codebook of K codewords, each of the same '
  'dimension, is designed from training vectors. The encoder replaces every block by the index of its nearest codeword, and the '
  'decoder reconstructs the block by looking up the codeword of that index in the codebook. The distortion between a vector x and '
  'a codeword c_j is measured by the squared Euclidean distance')
E('d(x, c_j) = Σ (x_i − c_j,i)²,   i = 1, …, 16', 1)
P('The quantization operation can be expressed as')
E('Q(x) = c_j*,   j* = arg min d(x, c_j),   j = 1, …, K', 2)
P('where x is an input vector and c_j* is the codeword that minimizes the distortion between the input vector and the available '
  'codewords. Since only the index of the codeword is stored for each block, a codebook of K = 64 codewords requires log2(64) = 6 bits '
  'per block, i.e., 6/16 = 0.375 bits per pixel, in addition to the codebook itself. The codebook is designed with the '
  'Linde–Buzo–Gray (LBG) algorithm [LBG80], which is described in Chapter 3.')
P('For color images, vector quantization can be applied independently to the red, green, and blue channels. Each channel is treated as a '
  'grayscale image and uses a separate codebook. The VQ indices are generated and decoded separately for each channel, after which the '
  'three reconstructed channels are combined to form the output color image.')
P('Notes: replace [LBG80] with your reference number (Linde, Buzo, Gray, IEEE Trans. Commun., vol. COM-28, no. 1, pp. 84–95, 1980). '
  'Equation numbers are temporary. In Word, type the two equations with Insert > Equation (or keep them as plain text). '
  'The 0.375 bits per pixel counts only the indices; the compression ratio reported in Chapter 4 also includes the codebook, the header, '
  'and the entropy coding.', it=True)
d.save('stages/VQ_general_section.docx'); print('saved')
