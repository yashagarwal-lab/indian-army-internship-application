# Blind DSSS Despreading via PCA — Recovering a Signal at -12 dB SNR

> **tl;dr:** A Direct-Sequence Spread Spectrum signal is buried 12 dB below the noise floor with an unknown spreading code. This repo recovers it by stacking received IQ blocks into a matrix, extracting the dominant eigenvector (the spreading code) via PCA, then matched-filtering to pull the signal out of the noise.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Data via LFS](https://img.shields.io/badge/data-Git%20LFS-orange)
![Topics](https://img.shields.io/badge/topics-DSSS%20%7C%20PCA%20%7C%20Spread%20Spectrum%20%7C%20SDR-purple)

---

## 1. The Engineering Problem

A covert DSSS link transmits at **-12 dB SNR** — 12 dB below the thermal noise floor. No spectrum analyser can see it. We know the chip rate (100 kchip/s) and the sequence length (127 chips/bit), but we do **not** know the spreading code. The task is to recover the code blindly and decode the hidden BPSK data stream.

---

## 2. Why Conventional Receivers Fail

A conventional matched filter requires knowing the spreading code to correlate against. Without it, every candidate code produces near-zero correlation. With 2^127 possible binary sequences, brute force is computationally impossible. A naive FFT shows only flat noise — no spectral feature reveals the presence of the signal.

---

## 3. The Mathematical Foundation

### 3.1 DSSS Signal Model

A DSSS transmitter XORs each data bit with a 127-chip pseudo-random sequence `c[n]`:

```
x[n] = b_k · c[n mod 127]    for n in [127k, 127(k+1))
```

where `b_k ∈ {-1, +1}` is the k-th data bit. The received signal is:

```
r[n] = x[n] + w[n]           where w[n] ~ CN(0, σ²)
```

At -12 dB SNR, `|b_k · c[n]|² ≪ σ²`.

### 3.2 The Block Matrix Trick

Since the chip rate is 100 kchip/s and the sample rate is 400 kHz, there are **4 samples per chip**. One 127-chip symbol = 508 samples. Reshape the received signal into a 2D matrix:

```
R = reshape(r, shape=(N_symbols, 508))     # shape: (N, 508)
```

Each row is either `+c_oversampled + noise` or `-c_oversampled + noise`, where `c_oversampled` is the 508-sample (4× upsampled) spreading waveform.

### 3.3 Covariance and PCA

Compute the sample covariance matrix:

```
C = (1/N) · Rᵀ R              # shape: (508, 508)
```

The signal component contributes a rank-1 outer product `c·cᵀ` scaled by signal power. The noise contributes `σ²·I`. The eigendecomposition of `C` is:

```
C = (P_signal + σ²)·u₁u₁ᵀ + σ²·(u₂u₂ᵀ + ... + u₅₀₈u₅₀₈ᵀ)
```

The **dominant eigenvector** `u₁` is the 508-sample spreading waveform — recovered without knowing the code.

In practice, we use SVD on `R` directly (more numerically stable):

```python
U, S, Vt = np.linalg.svd(R, full_matrices=False)
code_estimate = Vt[0]          # first right singular vector = spreading waveform
```

### 3.4 Matched Filter Despreading

Correlate the extracted code against the entire received signal:

```
y[k] = Σ_{n=0}^{507} r[k+n] · code_estimate[n]     (matched filter)
```

The output `y[k]` has massive peaks every 508 samples, alternating positive (bit=+1) and negative (bit=-1). Processing gain:

```
G_p = 10 · log₁₀(127) ≈ 21 dB
```

This lifts the signal 21 dB out of the noise, turning -12 dB SNR into a clean +9 dB.

### 3.5 Symbol Decisions and Framing

Sign of each correlation peak gives the BPSK bit. Scan the bit stream for the 16-bit sync word to frame the data:

```
sync_word = 0b0111111000011101   (0x7E1D)
```

---

## 4. Algorithmic Breakdown

1. **Load IQ**: `cf32_le` → complex64, 400 kHz sample rate
2. **Reshape**: `(N_total_samples,)` → `(N_symbols, 508)`
3. **SVD**: Compute first right singular vector → `code_estimate` (508 samples)
4. **Correlate**: Slide `code_estimate` across raw IQ → correlation time series
5. **Decimate**: Sample correlation peaks every 508 samples → data bits
6. **Sync**: Search for sync word `0x7E1D` with both bit polarities
7. **Decode**: Extract ASCII bytes after sync word

---

## 5. Dataset — SigMF Schema

| File | Size | Format | Description |
|------|------|--------|-------------|
| `data/buried.sigmf-data` | 3.1 MB | `cf32_le` | Raw IQ, 400 kHz SR, DSSS at -12 dB SNR |
| `data/buried.sigmf-meta` | JSON | — | Sample rate 400000, chip rate 100000 |

```python
import numpy as np
raw = np.fromfile("data/buried.sigmf-data", dtype=np.float32)
iq  = raw[0::2] + 1j * raw[1::2]
```

---

## 6. Repository Structure

```
blind-dsss-pca-despreader/
├── .gitattributes
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── data/
│   ├── buried.sigmf-data    ← Git LFS (3.1 MB)
│   └── buried.sigmf-meta
├── solve.py                 # PCA-based blind despreader (primary)
└── solve_fast.py            # Optimised variant using FFT correlation
```

---

## 7. Setup and Execution

```bash
git clone https://github.com/<username>/blind-dsss-pca-despreader.git
cd blind-dsss-pca-despreader
git lfs pull

python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python solve.py
```

---

## 8. Further Reading

- Proakis — *Digital Communications*, Ch. 8.2 (DSSS and processing gain)
- Haykin — *Communication Systems*, 4th Ed., Ch. 10 (Spread Spectrum)
- Simon et al. — *Spread Spectrum Communications Handbook*, Ch. 3 (PN sequences)
- Scharf — *Statistical Signal Processing*, Ch. 4 (PCA and the SVD)
