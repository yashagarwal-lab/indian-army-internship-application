from sage.all import *

MASK64 = (1 << 64) - 1
MULC   = 0x9E3779B97F4A7C15
REDUCE = (1 << 4) | (1 << 3) | (1 << 1) | 1

def rotl(x, n):
    return ((x << n) | (x >> (64 - n))) & MASK64

def gf_mul(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1
        a <<= 1
        if a & (1 << 64):
            a = (a & MASK64) ^ REDUCE
    return r & MASK64

def expand(m):
    return (m * 0x0101010101010101) & MASK64

def seal_state(key, msg):
    s = key & MASK64
    for m in msg:
        s = rotl(s, 11)
        s ^= expand(m)
        s = gf_mul(s, MULC)
    return s

def T_func(x):
    return gf_mul(rotl(x, 11), MULC)

M_rows = []
for i in range(64):
    val = T_func(1 << i)
    row = [(val >> j) & 1 for j in range(64)]
    M_rows.append(row)

M = Matrix(GF(2), M_rows)

missions = []
with open("sealed_missions.txt", "r") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"): continue
        msg_hex, seal_hex = line.split(":")
        msg = bytes.fromhex(msg_hex)
        seal = int(seal_hex, 16)
        missions.append((msg, seal))

# We want to solve for key vector K (64 bits).
# For each mission, K * M^n + V = s
# where n = len(msg), V = seal_state(0, msg) as vector.
# We know the top 24 bits of s, so for j = 40..63:
# (K * M^n)[j] + V[j] = s[j]
# (K * M^n)[j] = s[j] + V[j]

equations = []
rhs = []

for msg, seal in missions:
    n = len(msg)
    V_val = seal_state(0, msg)
    
    Mn = M^n
    
    for j in range(40, 64):
        # We need the j-th bit of K * Mn
        # This is the inner product of K and the j-th column of Mn.
        # So it's the j-th column of Mn.
        col = Mn.column(j)
        equations.append(col)
        
        v_j = (V_val >> j) & 1
        s_j = (seal >> (j - 40)) & 1
        rhs.append(s_j ^^ v_j)  # XOR

A = Matrix(GF(2), equations)
b = vector(GF(2), rhs)

print(f"Matrix A dimensions: {A.dimensions()}")
try:
    K = A.solve_right(b)
    key_val = sum(int(K[i]) << i for i in range(64))
    print(f"Recovered key: {key_val:016x}")
    print(f"Flag: Intern_Pro_Max{{{key_val:016x}}}")
except Exception as e:
    print("Could not solve uniquely or error:")
    print(e)
