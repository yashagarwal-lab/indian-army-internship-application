import numpy as np
from scipy.linalg import svd

raw = np.fromfile("buried.sigmf-data", dtype=np.float32)
x = raw[0::2] + 1j*raw[1::2]

L = 508
num_blocks = 1015

max_s1 = -1
best_tau = -1

for tau in range(L):
    M = np.zeros((num_blocks, L), dtype=np.complex128)
    for k in range(num_blocks):
        M[k, :] = x[tau + k*L : tau + (k+1)*L]
    
    # We only need the largest singular value. 
    # For speed, we can compute the largest eigenvalue of M^H M
    Cov = M.conj().T @ M
    eigvals = np.linalg.eigvalsh(Cov)
    s1 = eigvals[-1] # Largest eigenvalue
    if s1 > max_s1:
        max_s1 = s1
        best_tau = tau

print(f"Best tau: {best_tau}")

# Now extract symbols at best tau
M = np.zeros((num_blocks, L), dtype=np.complex128)
for k in range(num_blocks):
    M[k, :] = x[best_tau + k*L : best_tau + (k+1)*L]

U, S, Vh = np.linalg.svd(M, full_matrices=False)
u1 = U[:, 0]
v1 = Vh[0, :]

# Phase correction: the symbols should be real BPSK
# We can find the phase that maximizes the real variance
phase = np.angle(np.sum(u1**2)) / 2.0
u1_rot = u1 * np.exp(-1j * phase)
symbols = np.sign(u1_rot.real).astype(int)

# Now we have symbols +1 and -1. Convert to 1 and 0.
bits = (symbols > 0).astype(int)

# Search for sync word
sync = "0111111000011101"
sync_bits = np.array([int(b) for b in sync])

for polarity in [1, -1]:
    if polarity == -1:
        cur_bits = 1 - bits
    else:
        cur_bits = bits
    
    for i in range(len(cur_bits) - 16):
        if np.array_equal(cur_bits[i:i+16], sync_bits):
            msg = []
            for j in range(i+16, len(cur_bits)-8, 8):
                byte_bits = cur_bits[j:j+8]
                byte_val = int("".join(map(str, byte_bits)), 2)
                msg.append(chr(byte_val))
            msg_str = "".join(msg)
            if "RFCTF" in msg_str:
                print(f"FOUND FLAG! Polarity {polarity}")
                print(msg_str)
                break
    else:
        continue
    break
