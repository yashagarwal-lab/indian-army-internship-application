import numpy as np
import time

raw = np.fromfile("buried.sigmf-data", dtype=np.float32)
x = raw[0::2] + 1j*raw[1::2]

L = 508

t0 = time.time()
best_tau = 194
print(f"Using tau = {best_tau}")

num_blocks = len(x) // L - 1
M = np.zeros((num_blocks, L), dtype=np.complex128)
for k in range(num_blocks):
    M[k, :] = x[best_tau + k*L : best_tau + (k+1)*L]

print(f"Formed M in {time.time() - t0}s")

# Power iteration
np.random.seed(0)
u1 = np.random.randn(num_blocks) + 1j*np.random.randn(num_blocks)
u1 /= np.linalg.norm(u1)

t1 = time.time()
for _ in range(50):
    v1 = np.dot(M.conj().T, u1)
    v1 /= np.linalg.norm(v1)
    u1 = np.dot(M, v1)
    u1 /= np.linalg.norm(u1)

print(f"Power iteration took {time.time() - t1}s")

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

