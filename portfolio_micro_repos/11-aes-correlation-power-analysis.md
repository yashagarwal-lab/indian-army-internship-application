# AES-128 Correlation Power Analysis (CPA) — Breaking AES with Power Traces

> **tl;dr:** AES is not broken by mathematics — it is broken by physics. When a microcontroller runs AES, its power consumption leaks information about the internal state. With 2000 captured power traces and a Hamming Weight leakage model, this repo recovers the full 16-byte AES-128 key byte-by-byte using the Pearson correlation coefficient.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Data via LFS](https://img.shields.io/badge/data-Git%20LFS-orange)
![Topics](https://img.shields.io/badge/topics-Side--Channel%20%7C%20CPA%20%7C%20AES%20%7C%20Power%20Analysis-purple)

---

## 1. The Engineering Problem

A captured embedded flight controller authenticates command packets with AES-128. The firmware is closed-source; the key cannot be read from registers. However, a current probe on the power rail was used to record 2000 encryptions, each with a different known plaintext. The goal: recover the 16-byte key from the power measurements alone.

---

## 2. Why AES is Vulnerable to Power Analysis

CMOS digital logic consumes power proportional to the number of bit transitions (0→1 and 1→0) during each clock cycle. The **Hamming Weight** (number of set bits) of the data being computed is a proxy for these transitions:

```
Power(t) ∝ HW(data being processed at time t)
```

The critical moment in AES-128 is the **first-round S-Box** operation. After key addition, byte `i` of the state becomes:

```
S_out[i] = AES_SBOX[ plaintext[i] XOR key[i] ]
```

If we guess `key[i]`, we can compute a hypothetical `S_out[i]` for all 2000 traces, and therefore a hypothetical power value. The correct guess will **correlate** with the actual measured power.

---

## 3. The Mathematical Foundation

### 3.1 Hamming Weight Leakage Model

For a guessed key byte `k ∈ [0, 255]` and plaintext byte `p`:

```
H[i, k] = HW(SBOX[p[i] XOR k])     for i ∈ {0, …, 1999}
```

`H` is the hypothetical leakage matrix: shape (2000, 256).

### 3.2 Pearson Correlation

The Pearson correlation coefficient between the hypothetical leakage column `H_k` (one guess) and the measured power at time sample `t` across all 2000 traces:

```
ρ(H_k, T_t) = cov(H_k, T_t) / (σ_{H_k} · σ_{T_t})

           = E[(H_k - μ_{H_k})(T_t - μ_{T_t})] / (σ_{H_k} · σ_{T_t})
```

For the **correct** key byte `k*`, `ρ(H_{k*}, T_t)` will spike to a large value at the time sample `t` when the S-Box computation occurs. All wrong guesses produce near-zero correlation at all times.

### 3.3 Key Byte Recovery

```
k*_byte = argmax_{k ∈ [0,255]}  max_{t}  |ρ(H_k, T_t)|
```

Repeat independently for all 16 key bytes.

### 3.4 Trace Alignment (Jitter Correction)

The instrument trigger was unreliable — each trace starts at a slightly different point in the encryption. Unaligned traces produce near-zero correlation everywhere.

Fix: cross-correlate each trace against a reference template taken from the high-variance region:

```
d* = argmax_d  (T ⋆ R)[d] = argmax_d  Σ_t T[t] · R[t + d]
```

Shift each trace by `d*` to align all 2000 captures to a common temporal reference.

---

## 4. Algorithmic Breakdown

1. **Load traces**: `traces.npz` → `traces` (2000×800 int16), `plaintexts` (2000×16 uint8)
2. **Align**: Cross-correlation of each trace against a reference → shift to align
3. **For each of 16 key bytes**:
   - Compute `H[i, k] = HW(SBOX[pt[i] XOR k])` for all 2000 traces and all 256 guesses
   - Compute `ρ(H_k, T_t)` for all 256 guesses and all 800 time samples
   - Select `k* = argmax_k max_t |ρ(H_k, T_t)|`
4. **Verify**: Encrypt any known plaintext with recovered key and check S-Box output consistency

---

## 5. Dataset Schema

| File | Shape | Dtype | Description |
|------|-------|-------|-------------|
| `data/traces.npz['traces']` | (2000, 800) | int16 | Raw power traces (arbitrary ADC units) |
| `data/traces.npz['plaintexts']` | (2000, 16) | uint8 | Known plaintext bytes for each trace |
| `data/aligned.npz` | Same | int16 | Pre-aligned traces (jitter corrected) |

```python
import numpy as np
z = np.load("data/traces.npz")
traces, plaintexts = z["traces"].astype(float), z["plaintexts"]
```

---

## 6. Repository Structure

```
aes-correlation-power-analysis/
├── data/
│   ├── traces.npz     ← Git LFS (raw traces, ~5 MB)
│   └── aligned.npz    ← Git LFS (pre-aligned, ~5 MB)
├── align.py           # Cross-correlation trace aligner
└── solve.py           # Full CPA engine + key byte recovery
```

---

## 7. Setup and Execution

```bash
git clone https://github.com/<username>/aes-correlation-power-analysis.git
cd aes-correlation-power-analysis
git lfs pull

python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python align.py          # produces aligned.npz
python solve.py          # prints recovered 16-byte key
```

---

## 8. Further Reading

- Brier, Clavier, Olivier — "Correlation Power Analysis with a Leakage Model", *CHES 2004*
- Mangard, Oswald, Popp — *Power Analysis Attacks: Revealing the Secrets of Smart Cards*, Springer 2007
- NIST FIPS 197 — *Advanced Encryption Standard*, 2001 (AES key schedule spec)
- Riscure — [riscure.com/security-tools/inspector](https://www.riscure.com) (industry CPA tooling)
