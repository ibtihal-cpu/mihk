#!/usr/bin/env python3
"""Convert an image file (png/tif/bmp/jpg) to the plain-text format read by the LBG programs.

  color : "R G B" per pixel, row by row (786432 integers for 512x512)      python3 img2txt.py in.png out.txt
  gray  : one integer per pixel, row by row (262144 integers)               python3 img2txt.py in.png out.txt --gray

The image must already be 512x512 (standard test images are distributed at that size); the script stops otherwise,
because resizing would change the standard image. Use --resize only if you accept that and will say so in the thesis.
Check afterwards:  wc -w out.txt   ->  786432 (color) or 262144 (gray).
"""
import sys
import numpy as np
from PIL import Image

args = [a for a in sys.argv[1:] if not a.startswith("--")]
gray = "--gray" in sys.argv
resize = "--resize" in sys.argv
if len(args) != 2:
    sys.exit(__doc__)
img = Image.open(args[0])
img = img.convert("L" if gray else "RGB")
if img.size != (512, 512):
    if not resize:
        sys.exit(f"ABORT: image is {img.size[0]}x{img.size[1]}, not 512x512 (use --resize only if you accept resizing)")
    img = img.resize((512, 512), Image.LANCZOS)
a = np.asarray(img, dtype=np.int64)
if gray:
    np.savetxt(args[1], a.reshape(-1), fmt="%d")
else:
    np.savetxt(args[1], a.reshape(-1, 3), fmt="%d")
print(f"wrote {args[1]}: {a.size} integers ({'gray' if gray else 'color'})")
