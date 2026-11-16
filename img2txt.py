#!/usr/bin/env python3
"""Convert a standard test image (png/bmp/tif/jpg) to the text format lbgn.c reads.

usage:  python3 img2txt.py <image> <--gray|--color> [out.txt]

  --gray   : 262144 lines, one 0..255 value per line
  --color  : 262144 lines, "R G B" per line
Only 512x512 images are accepted as-is. Anything else is refused (resizing silently would
change the test image); pass --resize to resize explicitly and state it in the thesis.
"""
import sys
from PIL import Image

args = [a for a in sys.argv[1:] if a != "--resize"]
resize = "--resize" in sys.argv
if len(args) < 2 or args[1] not in ("--gray", "--color"):
    sys.exit(__doc__)
src, mode = args[0], args[1]
out = args[2] if len(args) > 2 else src.rsplit(".", 1)[0] + ("_gray.txt" if mode == "--gray" else "_color.txt")

im = Image.open(src)
if im.size != (512, 512):
    if not resize:
        sys.exit(f"{src} is {im.size[0]}x{im.size[1]}, not 512x512. Use --resize to resize explicitly.")
    im = im.resize((512, 512), Image.LANCZOS)

if mode == "--gray":
    px = im.convert("L").tobytes()
    lines = (str(v) for v in px)
else:
    raw = im.convert("RGB").tobytes()
    px = range(len(raw) // 3)
    lines = (f"{raw[3*i]} {raw[3*i+1]} {raw[3*i+2]}" for i in px)

with open(out, "w") as f:
    f.write("\n".join(lines) + "\n")
print(f"wrote {out}: {len(px)} pixels ({mode[2:]})")
