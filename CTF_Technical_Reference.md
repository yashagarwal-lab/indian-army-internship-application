# Technical & Mathematical Reference for CTF Write-ups

This document details the mathematical models, algorithms, and technical procedures used to solve the CTF challenges. Use this as a study guide to understand the underlying mechanics before writing your final H4 reports in your own words.

---

## 1. CEMA Track (Cyber Electromagnetic Activities)

### H1 — Quiet Power (Side-Channel Analysis)
**The Problem:** We had 2,000 power traces of an AES-128 encryption, but the trigger was unreliable, leading to temporal jitter (misalignment).
**The Mathematics:**
1.  **Cross-Correlation for Alignment:**
    To fix jitter, we used the discrete cross-correlation function to find the time delay $d$ that maximizes the similarity between a trace $T$ and a reference template $R$ (taken from the highly variant burst region):
    $$ (T \star R)[d] = \sum_{t} T[t] \cdot R[t+d] $$
    We shifted each trace by its optimal $d$ to align all 2,000 captures perfectly.
2.  **Correlation Power Analysis (CPA):**
    The power consumption of a microcontroller correlates with the Hamming Weight (number of set bits) of the data being processed. For AES, the point of highest leakage is the S-box output in the first round:
    $$ L_{i,k} = HW(Sbox[P_i \oplus K]) $$
    Where $P_i$ is a known plaintext byte, and $K \in [0, 255]$ is a guessed key byte.
    For each of the 16 key bytes, we compute the Pearson Correlation Coefficient ($\rho$) between our hypothetical leakage $L_k$ and the measured power traces $T$ at every time sample $t$:
    $$ \rho(L_k, T_t) = \frac{\text{cov}(L_k, T_t)}{\sigma_{L_k} \sigma_{T_t}} $$
    The key byte candidate $K$ that produces the maximum correlation $\rho$ is the correct key.

### H2 — Mission Seal II (Authentication / Cryptanalysis)
**The Problem:** Recover a 64-bit key from an iterative hash-like function. A brute force search of $2^{64}$ keys would take 580 years.
**The Mathematics:**
The `seal` function consists of bit rotations, XORs, and Galois Field (GF) multiplication modulo $x^{64}+x^4+x^3+x+1$.
Crucially, over the field $GF(2)$, all these operations are **linear**. 
1.  **Affine Transformation Representation:**
    Because polynomial multiplication distributes over addition (XOR in GF(2)), the entire loop updating the 64-bit state $s$ can be represented as an affine transformation:
    $$ s_{next} = (s \cdot M) \oplus C $$
    Where $s$ is a 1x64 row vector, $M$ is a 64x64 binary transformation matrix, and $C$ is a constant vector derived from the message byte.
2.  **System of Linear Equations:**
    For a message of length $n$, the final state $s_n$ is purely a function of the initial key $K$:
    $$ s_n = (K \cdot M^n) \oplus V_{msg} $$
    Where $V_{msg}$ is the state reached if the key was $0$.
    Since the final seal gives us the top 24 bits of $s_n$, we get 24 linear equations for the 64 bits of $K$. With 5 seals, we have 120 equations.
3.  **Gaussian Elimination:**
    We construct an augmented matrix of these 120 equations and solve for the 64 unknowns using standard Gaussian Elimination over $GF(2)$, returning the key instantly.

### H3 — Core Dump II (Memory Forensics)
**The Problem:** Recover a scrubbed 16-byte AES-128 master key from a 1MB RAM dump.
**The Mathematics:**
AES-128 expands a 16-byte key into 44 32-bit words ($w_0 \dots w_{43}$) to act as 11 round keys. The key schedule is a bijection (fully reversible).
1.  **The Key Expansion Non-Linear Relation:**
    For words where the index is a multiple of 4 (e.g., $w_4$), the expansion uses a non-linear relation involving the S-box, a bit rotation, and a round constant ($Rcon$):
    $$ w_4 = w_0 \oplus SubWord(RotWord(w_3)) \oplus Rcon[r] $$
2.  **Probability & Search:**
    Rather than doing millions of slow AES decryptions to test every 16-byte chunk in RAM, we scan the dump for any 20-byte sequence (5 words) that satisfies the equation above. Since the relation is highly specific, the probability of a random 20-byte sequence satisfying it is $\approx 10/2^{32}$ (effectively zero).
3.  **Reversing the Schedule:**
    Once we found a matching 20-byte sequence at round $r=2$, we algebraically reversed the XORs and S-box operations to step backwards from $w_4 \dots w_7$ down to $w_0 \dots w_3$, yielding the scrubbed master key.

---

## 2. RF Track (Radio Frequency Analysis)

### H1 — Two Radios, One Channel (Interference)
**The Mathematics:**
Two signals were colliding on the same frequency. The stronger signal was QPSK; the weaker hidden signal was BPSK. We applied **Successive Interference Cancellation (SIC)**.
1. We locked onto the stronger QPSK signal's phase and frequency using a Costas Loop and demodulated it.
2. We mathematically reconstructed the ideal QPSK waveform based on those demodulated symbols.
3. We subtracted the reconstructed QPSK waveform from the raw IQ data: $IQ_{clean} = IQ_{raw} - IQ_{reconstructed}$.
4. The remainder was the pristine BPSK signal, which we then demodulated.

### H2 — Chipped (Direct-Sequence Spread Spectrum)
**The Mathematics:**
The signal was buried beneath the noise floor using DSSS. 
1. **Autocorrelation:** To blindly find the unknown spreading code (chip sequence), we calculated the autocorrelation of the signal. Spreading codes are designed to have a massive autocorrelation peak when aligned, and near-zero otherwise. By measuring the distance between peaks, we found the sequence length.
2. **Despreading:** By multiplying the raw incoming IQ data by the synchronized spreading code, the bandwidth collapsed, raising the hidden signal out of the noise floor so it could be read.

### H3 — Fingerprint (RF-DNA)
**The Mathematics:**
We needed to identify an unknown radio transmitter based solely on physical hardware imperfections. We extracted statistical features from the transient (turn-on) phase of the radio bursts.
Features included:
*   **IQ Imbalance:** Measuring the amplitude/phase mismatch between the In-phase and Quadrature channels caused by imperfect local oscillators.
*   **Spectral Asymmetry:** Analyzing the uneven distribution of power across the positive and negative frequency bins.

---

## Plan for Remaining Tasks

To complete the CTF and get you ready for the final H4 submissions, here is my plan of action for us:

1. **UAV Track Completion:** We still need to solve **UAV-H3 (Consensus)**. I will analyze the swarm navigation telemetry data to figure out the consensus algorithm vulnerability.
2. **5G Track Completion:** We still need to solve **5G-H2 (Replay or Retransmit)** and **5G-H3 (Needle in the Handovers)**. I will parse the PCAP files and use Scapy/Wireshark logic to crack the encryption/state-machine flaws.
3. Once those are solved, I will append their mathematical procedures to this document.
4. You will then have all the underlying theory needed to draft the 4 required PDFs!
