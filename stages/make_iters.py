#!/usr/bin/env python3
"""Generate stages/codes_iters.c from codes_min.c: the only change is verbose = 1 in the two lbg() calls, so that
the program prints one line per splitting stage ("k=  2 iter= 12 ... (converged)").  Same computation and output."""
s = open("codes_min.c").read()
old = "/*verbose=*/0"
assert s.count(old) == 2, s.count(old)
open("stages/codes_iters.c", "w").write(s.replace(old, "/*verbose=*/1"))
print("wrote stages/codes_iters.c")
