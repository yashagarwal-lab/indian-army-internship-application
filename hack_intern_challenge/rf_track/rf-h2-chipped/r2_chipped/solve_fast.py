import numpy as np
from scipy.sparse.linalg import svds
import time

t0 = time.time()
raw = np.fromfile("buried.sigmf-data", dtype=np.float32)
x = raw[0::2] + 1j*raw[1::2]

L = 508
num_blocks = len(x) // L - 1

# Pre-compute all blocks using stride tricks
shape = (len(x) - L + 1, L)
strides = (x.strides[0], x.strides[0])
X_all = np.lib.stride_tricks.as_strided(x, shape=shape, strides=strides)

max_s1 = -1
best_tau = -1

# Evaluate tau every 1 chip, wait, the offset might be sample-level. So we check all 508 offsets.
# But we can just use svds!
print("Starting search...")
for tau in range(L):
    # Form M for this tau
    # We take rows tau, tau+L, tau+2L...
    M = X_all[tau : tau + num_blocks*L : L]
    
    # Fast largest singular value
    # using svds
    # if M is too large, it might be slow. M is 1015 x 508
    U, S, Vt = svds(M, k=1)
    s1 = S[0]
    
    if s1 > max_s1:
        max_s1 = s1
        best_tau = tau

print(f"Best tau: {best_tau}")
print(f"Time taken: {time.time() - t0}s")

M = X_all[best_tau : best_tau + num_blocks*L : L]
U, S, Vh = np.linalg.svd(M, full_matrices=False)
u1 = U[:, 0]
v1 = Vh[0, :]

phase = np.angle(np.sum(u1**2)) / 2.0
u1_rot = u1 * np.exp(-1j * phase)
symbols = np.sign(u1_rot.real).astype(int)

bits = (symbols > 0).astype(int)

sync = "0111111000011101"
sync_bits = np.array([int(b) for b in sync])

for polarity in [1, -1]:
    cur_bits = 1 - bits if polarity == -1 else bits
    for i in range(len(cur_bits) - 16):
        if np.array_equal(cur_bits[i:i+16], sync_bits):
            msg = []
            for j in range(i+16, len(cur_bits)-8, 8):
                if j+8 > len(cur_bits): break
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

