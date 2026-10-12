# CEMA Track: Comprehensive Technical Writeup

This document provides a highly detailed, atomic-level breakdown of the three challenges in the CEMA (Cyber Electromagnetic Activities) track. It covers Side-Channel Analysis (SCA), Galois Field cryptanalysis, and raw memory forensics.

---

## CEMA-H1: Quiet Power

### Context & Goal
You are provided with a dataset of electromagnetic/power traces (`traces.npz`) recorded while a microcontroller encrypts known plaintexts using AES-128. Due to the physical properties of CMOS transistors, the power consumed by the chip correlates with the number of bits flipping inside the registers (Hamming Weight). The objective is to extract the secret 16-byte AES key using Correlation Power Analysis (CPA).

### The Vulnerability / Concept
AES encryption begins with an `AddRoundKey` step (XORing the plaintext with the key), immediately followed by the `SubBytes` step (passing the result through the non-linear S-Box). 
$$v = SBOX[plaintext \oplus key]$$
Since we know the `plaintext` and the `SBOX` is public, we only need to guess the 8-bit `key` byte (256 possibilities). For each guess, we compute the theoretical Hamming Weight (HW) of $v$. If our guess is correct, this theoretical HW vector (across all 2000 traces) will highly correlate with the actual measured power traces at the specific point in time when the S-Box lookup occurs. We use the **Pearson Correlation Coefficient** to measure this statistical alignment.

### Algorithmic Breakdown
1.  **Trace Preparation:** Load the numpy array of power traces and their corresponding plaintexts. Center the traces by subtracting their mean to optimize the Pearson correlation math.
2.  **Key Byte Loop:** Loop through each of the 16 bytes of the AES key.
3.  **Hypothesis Generation:** For a given byte, loop through all 256 possible key guesses. Calculate the hypothetical intermediate value: `hyp = SBOX[plaintexts[:, b] ^ guess]`.
4.  **Hamming Weight Mapping:** Convert `hyp` to its Hamming weight (number of `1` bits).
5.  **Pearson Correlation:** Compute the dot product between the centered HW predictions and the centered power traces. Divide by the standard deviations. 
6.  **Peak Detection:** The key guess that produces the highest absolute correlation peak over time is the mathematically proven correct byte.

### Code Walkthrough (Key Segments)

```python
# Pre-calculate centered traces for fast Pearson correlation
traces_centered = traces - np.mean(traces, axis=0)
traces_ss = np.sum(traces_centered**2, axis=0)

for b in range(16): # For each byte of the key
    max_corr = 0
    best_guess = 0
    for guess in range(256):
        # 1. Calculate the hypothetical S-Box output
        hyp = SBOX[plaintexts[:, b] ^ guess]
        # 2. Map to Hamming Weight
        preds = HW[hyp].astype(np.float32)
        
        preds_centered = preds - np.mean(preds)
        preds_ss = np.sum(preds_centered**2)
        
        # 3. Fast Cross-Covariance across time
        cov = np.dot(preds_centered, traces_centered)
        corr = cov / np.sqrt(preds_ss * traces_ss)
        
        # 4. Record the highest correlation
        peak_corr = np.max(np.abs(corr))
        if peak_corr > max_corr:
            max_corr = peak_corr
            best_guess = guess
```

### Execution & Results
Running the CPA script processes all 2000 traces in a few seconds. The Pearson correlation spikes dramatically for exactly one guess per byte, successfully extracting the full 16-byte `Intern_Pro_Max{...}` flag.

---

## CEMA-H2: Mission Seal II

### Context & Goal
A hostile drone validates uploaded missions by checking a 24-bit "seal" appended to the file. The seal is generated using a custom hashing function seeded by a secret 64-bit squadron key. You intercepted 5 mission files and their seals. Brute-forcing a 64-bit key ($2^{64}$ possibilities) is computationally impossible. You must reverse the key using cryptanalysis.

### The Vulnerability / Concept
By analyzing the provided Python `seal` algorithm, a critical cryptographic flaw is evident: **the algorithm is entirely linear over Galois Field GF(2).**
The operations used are:
1.  Left bitwise rotation (`rotl`)
2.  XOR (`^`)
3.  Multiplication modulo $x^{64} + x^4 + x^3 + x + 1$ (`gf_mul`)

Because there are no non-linear components (like an S-Box or modular addition), the entire hashing process can be modeled as a matrix multiplication. A 64-bit state transitioning through this algorithm is mathematically equivalent to multiplying a $64 \times 64$ binary matrix $M$ by the initial 64-bit key $K$. 

### Algorithmic Breakdown
1.  **Matrix Construction:** We construct the transformation matrix $M$ by passing the standard basis vectors (a 64-bit integer with only one bit set to 1) through one cycle of the seal's internal permutation function.
2.  **Exponentiation:** For a mission of length $n$ bytes, the state undergoes the transformation $n$ times. Thus, the transformation for that specific mission is $M^n$ (calculated rapidly using matrix exponentiation by squaring over GF(2)).
3.  **Equation Building:** The final seal is the top 24 bits of the 64-bit state. For each mission, we extract the corresponding 24 rows from $M^n$. Since we have 5 missions, we gather $5 \times 24 = 120$ linear equations.
4.  **Gaussian Elimination:** We have 120 equations and only 64 unknown bits (the key). We set up an augmented matrix and use Gaussian Elimination over GF(2) to solve for the exact 64-bit key.

### Code Walkthrough (Key Segments)

```python
# 1. Build the base 64x64 Transformation Matrix M
M_rows = []
for i in range(64):
    val = T_func(1 << i) # Pass basis vector through the linear function
    row = [(val >> j) & 1 for j in range(64)]
    M_rows.append(row)

# 2. Build equations for each intercepted mission
equations = []
rhs = []
for msg, seal in missions:
    n = len(msg)
    # Calculate M^n over GF(2)
    Mn = mat_pow(M_rows, n) 
    
    # Extract equations for the 24 exposed bits
    for j in range(40, 64): 
        col = [Mn[i][j] for i in range(64)]
        equations.append(col)
        # ... right hand side calculation

# 3. Solve the system
K = solve_linear_system_gf2(equations, rhs)
```

### Execution & Results
Instead of waiting 580 years for a brute force, the script constructs the matrices, performs Gaussian elimination, and solves the system in less than a second, outputting the secret 64-bit key.

---

## CEMA-H3: Core Dump 2

### Context & Goal
You are provided with a raw binary RAM dump (`controller_ram.bin`) from a microcontroller. The microcontroller was in the middle of executing AES encryption when the memory was dumped, but a security "scrub" zeroed out the master key array. However, AES utilizes an expanded "Key Schedule" (44 words/176 bytes for AES-128) derived from the master key. You must find remnants of the key schedule in RAM and reverse the AES key expansion algorithm to recover the master key.

### The Vulnerability / Concept
While the 16-byte master key was zeroed out, AES key expansion works by deriving Round $N$ from Round $N-1$. Because this algorithm is fully deterministic and reversible, if we can find **any** intact 16-byte round key in memory, we can run the key schedule in reverse to recover the master key.
Furthermore, the key schedule words follow a strict mathematical property: for any word index $k$ that is not a multiple of 4, $w_k = w_{k-1} \oplus w_{k-4}$. This means $w_{k-4} \oplus w_{k-1} \oplus w_k = 0$. We can scan the entire RAM dump for any 20-byte sequence that satisfies this equation.

### Algorithmic Breakdown
1.  **Extract Ciphertext:** Scan the RAM dump for the magic header `MSNCRYPT` to locate the ciphertext and Initialization Vector (IV).
2.  **Memory Scanning:** Slide a 20-byte window across the entire RAM dump. Check if the XOR relationship ($w_{-4} \oplus w_{-1} == w_0$) holds true. This identifies candidates for partially intact key schedules.
3.  **Reverse Key Schedule:** Implement the inverse AES key schedule (`get_prev_round_key`). Given a 16-byte round key, reverse the SubWord, RotWord, and Rcon XOR operations to calculate the previous round's key.
4.  **Verification:** For every candidate, assume it belongs to round $R$ (where $R \in [1, 10]$). Step backward to Round 0 to get a candidate master key. Use the IV and Ciphertext extracted in Step 1 to test decryption. If the plaintext contains `Intern_Pro_Max`, the key is correct.

### Code Walkthrough (Key Segments)

```python
# 1. Scan memory for the AES Key Schedule signature
candidates = []
for i in range(len(data) - 20):
    w_minus_4 = data[i:i+4]
    w_minus_1 = data[i+12:i+16]
    w_0       = data[i+16:i+20]
    
    # AES property: w[i] = w[i-1] ^ w[i-4]
    if xor_bytes(w_minus_4, w_minus_1) == w_0:
        candidates.append(i)

# 2. Reversing a Round Key
def get_prev_round_key(rk, rcon_idx):
    w4, w5, w6, w7 = rk[0:4], rk[4:8], rk[8:12], rk[12:16]
    w3 = xor_bytes(w7, w6)
    w2 = xor_bytes(w6, w5)
    w1 = xor_bytes(w5, w4)
    # Reverse the non-linear transformation
    tmp = sub_word(rot_word(w3))
    rcon_word = bytes([RCON[rcon_idx], 0, 0, 0])
    w0 = xor_bytes(w4, xor_bytes(tmp, rcon_word))
    return w0 + w1 + w2 + w3

# 3. Test decryption
def verify_key(key):
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    pt = cipher.decrypt(ciphertext)
    return b"Intern_Pro_Max" in pt
```

### Execution & Results
The scanner rapidly isolates the few memory locations containing corrupted key schedules. By running the schedule backward from an intact chunk, the master key is recovered, decrypting the payload and revealing the flag.

---
---

## Deep Dive: CEMA & Hardware Cryptanalysis Glossary

To truly master the Cyber Electromagnetic Activities (CEMA) track, you need to understand the physics of computation and the mathematical structure of cryptography. Here is a deep dive into the underlying principles.

### 1. Side-Channel Analysis (SCA) & Power Analysis (H1)
When a computer runs, it is physically just billions of microscopic transistors turning on and off. Moving electrons from a `0` state to a `1` state requires physical energy. 
- **The Concept:** If a chip does an operation with a lot of `1`s, it draws more power than if it does an operation with mostly `0`s. By hooking up an oscilloscope to the power supply of a chip, you can literally "see" the data being processed.
- **Correlation Power Analysis (CPA):** Instead of guessing the whole 16-byte key at once, we guess just 1 byte (256 guesses). For each guess, we mathematically calculate what the power *should* look like. We then overlay our theoretical graph onto the real oscilloscope graph using a statistical formula called Pearson Correlation. The guess that perfectly aligns with the physical reality of the chip is the correct key.

### 2. Hamming Weight (H1)
The Hamming Weight is simply the number of `1`s in a binary string. 
For example, the binary string `10110010` has a Hamming Weight of 4. In power analysis, we assume that the power a chip consumes is directly proportional to the Hamming Weight of the data sitting in its registers at that exact microsecond.

### 3. AES (Advanced Encryption Standard) S-Box (H1, H3)
AES is the global standard for encryption. It is incredibly strong, but it relies on an **S-Box** (Substitution Box). The S-Box takes an 8-bit input and spits out a completely scrambled 8-bit output. 
- In H1, because the S-Box scrambles data so violently, a wrong key guess will have a completely different Hamming Weight than the right key guess, making CPA highly effective.
- In H3, we had to reverse the S-Box operation to walk backward through the Key Schedule.

### 4. Galois Fields (GF(2)) and Linear Cryptanalysis (H2)
Standard arithmetic uses normal numbers (1, 2, 3...) and operations (+, -, *, /). Cryptography uses "Finite Fields" (Galois Fields), which are math systems where numbers wrap around like a clock.
- **GF(2):** This is a field with only two numbers: `0` and `1`. In GF(2), addition is the exact same thing as the bitwise XOR operation (`^`), and multiplication is just a logical AND.
- **Linearity:** If a cryptographic function only uses XORs and bit shifts (which are just multiplications in GF(2)), the entire function is **linear**. 
- **The Vulnerability (H2):** If a function is linear, it doesn't matter how complicated it looks; it can always be represented as a giant matrix multiplication. This turns a completely impossible brute-force cracking attempt (trying $2^{64}$ passwords) into a basic algebra problem (solving $Ax = B$ using Gaussian Elimination), which a computer can solve in 0.01 seconds.

### 5. Memory Forensics & Key Schedules (H3)
When you encrypt a file, AES doesn't just use your password. It takes your password (the Master Key) and expands it into 11 different "Round Keys" (the Key Schedule).
- **The Scrub:** Security protocols often try to delete passwords from memory ("scrubbing") after they are used. In H3, the scrub deleted the Master Key, but left parts of the expanded Key Schedule in RAM.
- **The Reversal:** Because the AES key expansion algorithm is just a predictable mathematical formula, it is completely reversible. If you can find Round Key #7 sitting in RAM, you can just do the math in reverse to calculate Round Key #6, then #5, all the way back to the Master Key.
