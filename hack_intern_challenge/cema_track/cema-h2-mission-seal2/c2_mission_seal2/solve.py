import sys

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

def mat_mul(A, B):
    r1, c1 = len(A), len(A[0])
    r2, c2 = len(B), len(B[0])
    assert c1 == r2
    Bt = list(zip(*B))
    res = []
    for i in range(r1):
        row = []
        for j in range(c2):
            val = sum(A[i][k] * Bt[j][k] for k in range(c1)) % 2
            row.append(val)
        res.append(row)
    return res

def mat_pow(A, n):
    res = [[1 if i == j else 0 for j in range(len(A))] for i in range(len(A))]
    base = A
    while n:
        if n & 1:
            res = mat_mul(res, base)
        base = mat_mul(base, base)
        n >>= 1
    return res

def solve_linear_system_gf2(A, b):
    M = [row + [b[i]] for i, row in enumerate(A)]
    rows = len(M)
    cols = len(M[0]) - 1
    
    r = 0
    for c in range(cols):
        if r >= rows:
            break
        pivot = r
        while pivot < rows and M[pivot][c] == 0:
            pivot += 1
        if pivot == rows:
            continue
        M[r], M[pivot] = M[pivot], M[r]
        for i in range(rows):
            if i != r and M[i][c] == 1:
                M[i] = [M[i][j] ^ M[r][j] for j in range(cols + 1)]
        r += 1
        
    solution = [0] * cols
    for i in range(r):
        for j in range(cols):
            if M[i][j] == 1:
                solution[j] = M[i][cols]
                break
    
    for i in range(r, rows):
        if M[i][cols] == 1:
            return None # Inconsistent
            
    return solution

M_rows = []
for i in range(64):
    val = T_func(1 << i)
    row = [(val >> j) & 1 for j in range(64)]
    M_rows.append(row)

missions = []
with open("sealed_missions.txt", "r") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"): continue
        msg_hex, seal_hex = line.split(":")
        msg = bytes.fromhex(msg_hex)
        seal = int(seal_hex, 16)
        missions.append((msg, seal))

equations = []
rhs = []

for msg, seal in missions:
    n = len(msg)
    V_val = seal_state(0, msg)
    
    Mn = mat_pow(M_rows, n)
    
    for j in range(40, 64):
        col = [Mn[i][j] for i in range(64)]
        equations.append(col)
        
        v_j = (V_val >> j) & 1
        s_j = (seal >> (j - 40)) & 1
        rhs.append(s_j ^ v_j)

print(f"Number of equations: {len(equations)}")
K = solve_linear_system_gf2(equations, rhs)

if K is None:
    print("Inconsistent system!")
else:
    key_val = sum(K[i] << i for i in range(64))
    print(f"Recovered key: {key_val:016x}")
    print(f"Flag: Intern_Pro_Max{{{key_val:016x}}}")
