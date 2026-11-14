import sys
import numpy as np

def load(path):
    a = np.loadtxt(path, dtype=np.int64)
    n = int(round(a.size ** 0.5)); return a[: n * n].reshape(n, n).astype(np.uint8)

def blocks(img, b=4):
    h, w = img.shape
    return img.reshape(h // b, b, w // b, b).transpose(0, 2, 1, 3).reshape(-1, b * b)

def lbg(X, K=64, delta=0.01, eps=1e-4, max_iter=100):
    X = X.astype(np.float64); n = len(X)
    cb = X.mean(0, keepdims=True); k = 1
    x2 = (X * X).sum(1)
    while k < K:
        cb = np.vstack([cb * (1 + delta), cb * (1 - delta)]); k *= 2
        prev = 1e30
        for it in range(max_iter):
            d = x2[:, None] - 2 * X @ cb.T + (cb * cb).sum(1)[None, :]
            lab = d.argmin(1); dist = d[np.arange(n), lab].sum() / n
            for c in range(k):
                m = lab == c
                if m.any(): cb[c] = X[m].mean(0)
            if abs(prev - dist) / (dist + 1e-9) <= eps: break
            prev = dist
    d = x2[:, None] - 2 * X @ cb.T + (cb * cb).sum(1)[None, :]
    return d.argmin(1)

def entropy(v):
    _, c = np.unique(v, return_counts=True); p = c / c.sum()
    return float(-(p * np.log2(p)).sum())

if len(sys.argv) > 1:
    img = load(sys.argv[1])
else:
    from sklearn.datasets import load_sample_image
    from PIL import Image
    img = np.asarray(Image.fromarray(load_sample_image("china.jpg")).convert("L"))[:424, :424]

x = lbg(blocks(img)).astype(np.float64)       # VQ index of each block, raster order
a, b = x[:-1], x[1:]
d = b - a                                      # Delta: index difference with the previous block
rho = float(np.corrcoef(a, b)[0, 1])
var_x = 0.5 * (a.var() + b.var())              # Proposition 1 assumes equal variances (A1)
print(f"blocks N = {len(x)}")
print(f"rho (consecutive indices)     = {rho:.3f}")
print(f"Var(x)                        = {var_x:.2f}")
print(f"Var(delta) measured           = {d.var():.2f}")
print(f"2*Var(x)*(1-rho)  (Eq. 10)    = {2 * var_x * (1 - rho):.2f}")
print(f"variance ratio Var(x)/Var(d)  = {var_x / d.var():.2f}   (reduction only if rho > 0.5)")
print(f"entropy of indices            = {entropy(x):.3f} bits")
print(f"entropy of delta              = {entropy(d):.3f} bits")
