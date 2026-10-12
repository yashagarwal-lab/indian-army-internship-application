import numpy as np
import time

x = np.random.randn(516128).astype(np.complex128)
L = 508
num_blocks = 1015

t0 = time.time()
for tau in range(10): # just 10 iterations
    M = np.zeros((num_blocks, L), dtype=np.complex128)
    for k in range(num_blocks):
        M[k, :] = x[tau + k*L : tau + (k+1)*L]
    Cov = M.conj().T @ M
    eigvals = np.linalg.eigvalsh(Cov)
    s1 = eigvals[-1]

print(f"Time for 10 iters: {time.time() - t0}s")
