# AES Key Schedule Reversal & Embedded Controller RAM Forensics

> **tl;dr:** When an embedded microcontroller holding classified flight directives is captured, defensive firmware triggers a memory scrub that zeroes out the AES-128 master key. However, the hardware crypto engine leaves expanded round key words scattered in transient RAM. By scanning a 1 MB raw memory dump for the algebraic invariants of the AES key expansion schedule, we isolate surviving round-key words, invert the non-linear key schedule backwards to Round 0, recover the master key, and decrypt the mission container.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Data via LFS](https://img.shields.io/badge/data-Git%20LFS-orange)
![Topics](https://img.shields.io/badge/topics-Memory--Forensics%20%7C%20AES%20%7C%20Cryptanalysis%20%7C%20Key--Schedule%20%7C%20Embedded--Security-purple)

---

## 1. The Engineering Problem

During tactical operations, an autonomous reconnaissance pod crashed in contested territory. Physical recovery specialists pulled a raw memory image from the onboard ARM Cortex microcontroller's SRAM (`data/controller_ram.bin`, exactly 1 MB flat binary).

Upon detecting loss of power integrity or enclosure tamper signals, the device's defensive bootloader executed a memory sanitization routine intended to thwart forensic recovery:
- The active 16-byte master key array in the primary security configuration register was overwritten with zeros (`0x00`).
- The decrypted mission package buffer was wiped.

However, modern embedded cryptographic stacks (such as mbedTLS, WolfSSL, or custom DMA hardware blocks) expand the master key into an intermediate **176-byte Key Schedule** (44 32-bit words) during cipher initialization. Because compiler optimizations and stack/heap allocation dynamics frequently duplicate or orphan these buffers in un-zeroed RAM regions, fragments of the key schedule persist.

The mission is to scan the 1 MB memory dump without symbols, locate the surviving round keys using pure mathematical invariant matching, reverse the non-linear AES key schedule backward to recover the original master key, and decrypt the `MSNCRYPT` mission record.

---

## 2. Why Naive Approaches Fail

1. **Standard Memory Forensics Frameworks**: Tools like Volatility, Rekall, or LiME are designed for rich operating systems (Linux, Windows, macOS). They require ELF/PE binaries, task structures, page tables, and symbol tables. A bare-metal microcontroller flat binary has no OS abstractions, rendering standard forensic toolkits inoperable.
2. **Entropy Scanning**: Cryptographic keys exhibit high Shannon entropy. However, 1 MB of embedded firmware RAM contains compiled machine code, lookup tables, compressed assets, and telemetry buffers that also exhibit near-maximal entropy ($H \gt 7.5\,\mathrm{bits/byte}$). Entropy scanning produces thousands of false positives.
3. **Pure Brute-Force Scanning for Master Key**: Because the master key was explicitly scrubbed, searching for the original key buffer will always yield zero results. One must search for the *remnants of the expansion process*.

---

## 3. The Mathematical & Cryptanalytic Foundation

### 3.1 Structure of AES-128 Key Expansion

AES-128 expands a 16-byte master key $K = [w_0, w_1, w_2, w_3]$ into 44 words ($w_0, w_1, \dots, w_{43}$), where each word $w_i \in \{0, 1\}^{32}$ is a 4-byte column vector.

The key expansion algorithm obeys two distinct transition rules:

#### Rule 1: Intra-Round Linear Recurrence (for $i \not\equiv 0 \pmod 4$)
For words that do not lie on round boundaries:

$$w_i = w_{i-1} \oplus w_{i-4}$$

Rearranging into an invariant test condition:

$$w_{i-4} \oplus w_{i-1} \oplus w_i = \mathbf{0}_{32}$$

#### Rule 2: Round Boundary Non-Linear Step (for $i \equiv 0 \pmod 4$)
For the first word of each 4-word round key:

$$w_i = w_{i-4} \oplus \text{SubWord}(\text{RotWord}(w_{i-1})) \oplus \text{Rcon}[i/4]$$

where:
- $\text{RotWord}([b_0, b_1, b_2, b_3]) = [b_1, b_2, b_3, b_0]$ (1-byte circular left shift).
- $\text{SubWord}(\cdot)$ applies the Rijndael non-linear S-Box to each of the 4 bytes.
- $\text{Rcon}[j]$ is the round constant: $\text{Rcon}[j] = [\text{RC}[j], 0x00, 0x00, 0x00]$ in $\text{GF}(2^8)$.

```
Round 0 (Master Key):  [ w0   w1   w2   w3  ]
                         │    │    │    │
                         ▼    ▼    ▼    ▼
Round 1:               [ w4   w5   w6   w7  ]
                         │
                         ├─ w4 = w0 ⊕ SubWord(RotWord(w3)) ⊕ Rcon[1]
                         ├─ w5 = w1 ⊕ w4
                         ├─ w6 = w2 ⊕ w5
                         └─ w7 = w3 ⊕ w6
```

### 3.2 False-Positive Probability of the Invariant Filter

We slide a 20-byte window across the 1 MB RAM image. A candidate 20-byte slice consists of five consecutive 32-bit words $[v_0, v_1, v_2, v_3, v_4]$.

We test whether the linear XOR condition holds across words:

$$v_0 \oplus v_3 == v_4$$

Assuming uninitialized or random memory represents uniform independent random variables:

$$\mathbb{P}(v_0 \oplus v_3 == v_4) = \frac{1}{2^{32}} \approx 2.33 \times 10^{-10}$$

Across a 1 MB search space ($N = 1,048,576 - 20 \approx 10^6$ test offsets), the expected number of false positives $\mathbb{E}[\text{FP}]$ is:

$$\mathbb{E}[\text{FP}] \approx 10^6 \times 2.33 \times 10^{-10} \approx 0.000233$$

**The mathematical false positive rate is effectively zero.** Finding a 20-byte slice satisfying this relation is an infallible signature of an AES key schedule.

### 3.3 Algebraic Inversion of the Key Schedule

Once a 16-byte round key for round $R$ is recovered:

$$\mathbf{RK}_R = [w_{4R}, w_{4R+1}, w_{4R+2}, w_{4R+3}]$$

The expansion equations can be solved in reverse to reconstruct the previous round key:

$$\mathbf{RK}_{R-1} = [w_{4R-4}, w_{4R-3}, w_{4R-2}, w_{4R-1}]$$

1. **Reconstruct preceding words via linear backward XOR**:
   $$w_{4R-1} = w_{4R+3} \oplus w_{4R+2}$$
   $$w_{4R-2} = w_{4R+2} \oplus w_{4R+1}$$
   $$w_{4R-3} = w_{4R+1} \oplus w_{4R}$$
2. **Invert the non-linear boundary word**:
   $$w_{4R-4} = w_{4R} \oplus \text{SubWord}(\text{RotWord}(w_{4R-1})) \oplus \text{Rcon}[R]$$

Because every step is a bijection, we cascade this backward transformation from round $R$ down to $R=0$. The resulting $\mathbf{RK}_0 = [w_0, w_1, w_2, w_3]$ is the **exact master encryption key**.

---

## 4. Algorithmic Breakdown

1. **RAM Stream Ingestion**: Open `data/controller_ram.bin` (1,048,576 bytes).
2. **Encrypted Container Discovery**:
   - Search memory for magic token `b"MSNCRYPT"`.
   - Parse 16-byte IV and subsequent encrypted payload blocks.
3. **Key Expansion Invariant Scanner**:
   - Slide a 20-byte window across all byte offsets $i \in [0, 1048576 - 20]$.
   - Extract words $w_{-4} = \text{data}[i:i+4]$, $w_{-1} = \text{data}[i+12:i+16]$, and $w_0 = \text{data}[i+16:i+20]$.
   - Test if $w_{-4} \oplus w_{-1} == w_0$.
   - Locate candidate match at offset `0x3a1d7`.
4. **Round Key Inversion**:
   - Extract 16-byte round key at `0x3a1d7`.
   - Test round indices $R \in [1, 10]$.
   - Cascade backward using `get_prev_round_key` until Round 0 is reached.
5. **Decryption & Payload Verification**:
   - Decrypt `MSNCRYPT` container with candidate master key using AES-128-CBC.
   - Inspect plaintext for ASCII header `FLEET DIRECTIVE`.

---

## 5. Dataset & Data Schema

| File | Description | Format | Size | LFS |
|------|-------------|--------|------|-----|
| `data/controller_ram.bin` | Raw SRAM dump from ARM Cortex controller | Raw binary | 1,048,576 B (1 MB) | Yes |

### In-Memory Artifacts
- **Magic Container**: `MSNCRYPT` followed by 16-byte CBC IV and 64-byte ciphertext.
- **Key Schedule Remnant**: Located at memory offset `0x3a1d7` (Round 2 key schedule).

---

## 6. Repository Structure

```
aes-key-schedule-reversal-ram-forensics/
├── .gitattributes             # Git LFS tracking for *.bin
├── .gitignore
├── LICENSE                    # MIT License
├── README.md                  # Detailed cryptanalysis & reversal derivation
├── requirements.txt           # Cryptography dependency
├── solve.py                   # Automated RAM scanner, inverter, & decryptor
└── data/
    └── controller_ram.bin     # 1 MB embedded RAM image (LFS)
```

---

## 7. Setup & Execution

### Prerequisites

Ensure Git LFS is installed:
```bash
git lfs install
```

### Installation & Run

```bash
git clone https://github.com/yashagarwal-lab/aes-key-schedule-reversal-ram-forensics.git
cd aes-key-schedule-reversal-ram-forensics
git lfs pull
pip install -r requirements.txt
python solve.py
```

---

## 8. Expected Output

```
[+] Ingested 1,048,576 bytes from data/controller_ram.bin
[+] Located encrypted mission container at offset 0x12F40:
    Magic: MSNCRYPT | IV: 4a2b1c8e... (16 bytes) | Ciphertext: 64 bytes
[+] Scanning RAM for AES key expansion word relationships (P_FP = 2.3e-10)...
[!] CANDIDATE LOCATED:
    Offset: 0x3a1d7
    Round Key Words Match: Round 2 Schedule
[+] Reversing AES Key Schedule:
    Round 2 -> Round 1 -> Round 0 (Master Key)
[+] Reconstructed Master Key: 3d59c0b41e7a862fd0481b9e5c73a6f1
[+] Decrypting AES-CBC ciphertext...

============================================================
DECRYPTED MISSION DIRECTIVE:
FLEET DIRECTIVE 7 // AUTHENTICATION OVERRIDE
issuing_node=GCS-04  validity=48h
seal_key_provisioned=true
flag=Intern_Pro_Max{sch3dul3_runs_b0th_ways}
// end of record
============================================================
```

---

## 9. Further Reading

- Daemen, J., & Rijmen, V. (2002). *The Design of Rijndael: AES - The Advanced Encryption Standard*. Springer.
- Halderman, J. A., et al. (2009). *Lest We Remember: Cold-Boot Attacks on Encryption Keys*. Communications of the ACM.
- NIST FIPS PUB 197: *Advanced Encryption Standard (AES)*.
