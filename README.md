# Exercise PARCHAM & Autonomous Intelligence Architecture

**Indian Army Technical Internship Application Portfolio**  
Candidate: **Yash Agarwal** ([@yashagarwal-lab](https://github.com/yashagarwal-lab))

[![CTF Status: 100% Solved](https://img.shields.io/badge/Exercise%20PARCHAM-13%2F13%20Challenges%20Solved-success.svg)](https://github.com/yashagarwal-lab)
[![Publication Engine](https://img.shields.io/badge/Magazine%20Engine-50--Page%20A4%20Print%20%2B%20Web-blue.svg)](https://github.com/yashagarwal-lab/automated-defense-magazine-generator)
[![Zero DOM Overflow](https://img.shields.io/badge/DOM%20Overflow-0mm%20Clipping-brightgreen.svg)](https://github.com/yashagarwal-lab/automated-defense-magazine-generator)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎖️ Executive Summary

This repository represents the master engineering portfolio submitted for the **Indian Army Technical Internship**. It consolidates verified, production-grade solutions for **Exercise PARCHAM** (a high-intensity multi-domain signals intelligence, cyber-electronic warfare, and unmanned autonomy CTF) alongside a standalone, autonomous open-source defense intelligence curation and publishing system.

### Key Contributions:
1. **100% CTF Challenge Resolution (13/13 Solved):** Across 4 operational domains—Serial TARANG (RF/Signal Processing), Serial GAGAN (UAV Systems & Autonomy), Serial LOHA JAAL (5G Core & Protocol Forensics), and Serial NIGHT KITE (CEMA & Cryptanalysis).
2. **13 Standalone Engineering Micro-Repositories:** Decomposed and open-sourced under `@yashagarwal-lab`, each featuring mathematical proofs, signal processing theory, unit tests, and self-contained datasets.
3. **Autonomous Defense Publication Engine (`mag-gen`):** A 50-page print-ready A4 magazine and interactive digital reader compiler with zero DOM clipping and mathematical page budgeting, published at [`yashagarwal-lab/automated-defense-magazine-generator`](https://github.com/yashagarwal-lab/automated-defense-magazine-generator).
4. **4 Formal Technical Writeups:** Comprehensive research papers analyzing the underlying physics, vulnerabilities, and counter-tactics across RF, UAV, 5G, and CEMA domains.

---

## 🌐 Ecosystem Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│               INDIAN ARMY INTERNSHIP APPLICATION ECOSYSTEM                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────┐          ┌──────────────────────────────────┐  │
│  │   Master Portfolio Repo │ ───────> │  Autonomous Magazine Generator   │  │
│  │   (This Repository)     │          │  (mag-gen) - 50p A4 / Web Reader │  │
│  └───────────┬─────────────┘          └──────────────────────────────────┘  │
│              │                                                              │
│              ▼                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │               13 Standalone Engineering Micro-Repositories            │  │
│  ├───────────────────┬───────────────────┬───────────────────┬───────────┤  │
│  │    RF / Tarang    │    UAV / Gagan    │   5G / Loha Jaal  │CEMA/Night │  │
│  │  • SIC Cancellation│  • GNSS Dead-Reck │  • GTP-U Steg     │• CPA Power│  │
│  │  • Blind DSSS PCA │  • LFSR Hop State │  • NAS Replay     │• GF(2) Alg│  │
│  │  • RF Fingerprint │  • Byzantine Swarm│  • GUTI Tracking  │• AES Key  │  │
│  │  • FHSS Dewhiten  │                   │                   │  Schedule │  │
│  └───────────────────┴───────────────────┴───────────────────┴───────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📡 Exercise PARCHAM — Challenge Matrix & Micro-Repositories

Each challenge has been solved, verified, and published as a self-contained GitHub micro-repository:

### Track 1: Serial TARANG — RF & Signal Processing

| Challenge | Title & Physics | Solved Flag / Output | Standalone Repository |
|---|---|---|---|
| **RF-H1** | Successive Interference Cancellation (SIC), Costas loop carrier sync, Gardner TED, BPSK pilot isolation | `RFCTF{two_radios_c0_chann3l_succ3ss}` | [successive-interference-cancellation](https://github.com/yashagarwal-lab/successive-interference-cancellation) |
| **RF-H2** | Blind DSSS Despreading, SVD/PCA eigenvector decomposition, principal chip sequence recovery | `RFCTF{wh0_n33ds_th3_c0d3_b00k}` | [blind-dsss-pca-despreader](https://github.com/yashagarwal-lab/blind-dsss-pca-despreader) |
| **RF-H3** | RF Hardware Fingerprinting, IQ mixer imbalance, Image Rejection Ratio (IRR), spectral asymmetry emitter ID | `RFCTF{r4d10_dna_1mbalance_match}` | [rf-hardware-fingerprinting-iq-imbalance](https://github.com/yashagarwal-lab/rf-hardware-fingerprinting-iq-imbalance) |
| **RF-H5** | 16-channel FHSS Demodulation, 2-FSK matched filtering, GPS C/A PRN de-whitening, notch filtering, Shamir secret recovery | `RFCTF{gh0st_c4rr13r_fhss_unm4sk3d}` | [fhss-lfsr-dewhitening-gps-ca](https://github.com/yashagarwal-lab/fhss-lfsr-dewhitening-gps-ca) |

### Track 2: Serial GAGAN — Unmanned Systems & Autonomy

| Challenge | Title & Mathematics | Solved Flag / Output | Standalone Repository |
|---|---|---|---|
| **UAV-H1** | GNSS Spoofing Onset Detection, Newtonian IMU dead-reckoning integration, detrended innovation statistics | `RFCTF{spoof_detected_t_142_8s}` | [gnss-spoofing-imu-dead-reckoning](https://github.com/yashagarwal-lab/gnss-spoofing-imu-dead-reckoning) |
| **UAV-H2** | Fibonacci LFSR Frequency-Hop State Recovery, non-linear filter inversion, Berlekamp-Massey / C state solver | `RFCTF{lfsr_st4t3_0x8f2d4a1b}` | [lfsr-frequency-hop-sequence-recovery](https://github.com/yashagarwal-lab/lfsr-frequency-hop-sequence-recovery) |
| **UAV-H3** | Byzantine Fault-Tolerant Swarm Consensus, TDOA hyperbolic multilateration, Trimmed-Mean / Krum outlier rejection | `KST{4210_-1830_CE}` | [byzantine-fault-tolerant-swarm-consensus](https://github.com/yashagarwal-lab/byzantine-fault-tolerant-swarm-consensus) |

### Track 3: Serial LOHA JAAL — 5G Core & Protocol Forensics

| Challenge | Title & Protocols | Solved Flag / Output | Standalone Repository |
|---|---|---|---|
| **5G-H1** | 5G N3 Interface GTP-U Covert Channel, UDP reserved header steganography, IP userplane exfiltration extraction | `RFCTF{gtp_u_c0v3rt_ch4nn3l_f0und}` | [gtp-u-covert-channel-5g-steganography](https://github.com/yashagarwal-lab/gtp-u-covert-channel-5g-steganography) |
| **5G-H2** | 5G NAS Signaling Replay Detection, 3GPP TS 33.501 sequence counter monotonicity violation audit | Frame 218 (`UE 4217`, DL, Type `0x54`, Seq `0`) | [5g-nas-replay-attack-detection](https://github.com/yashagarwal-lab/5g-nas-replay-attack-detection) |
| **5G-H3** | 5G-GUTI Temporary Identifier Tracking, chained finite-state machine (FSM), N2/Xn handover mobility tracing | `RFCTF{6b5a87ba_6}` | [5g-guti-mobility-tracking](https://github.com/yashagarwal-lab/5g-guti-mobility-tracking) |

### Track 4: Serial NIGHT KITE — Cyber-Electronic Warfare & Cryptanalysis

| Challenge | Title & Cryptanalysis | Solved Flag / Output | Standalone Repository |
|---|---|---|---|
| **CEMA-H1** | AES-128 Correlation Power Analysis (CPA), CMOS dynamic power consumption model, Pearson correlation on Hamming weight | `Intern_Pro_Max{1be077d94bd50ab8f50e04fef7a5df14}` | [aes-correlation-power-analysis](https://github.com/yashagarwal-lab/aes-correlation-power-analysis) |
| **CEMA-H2** | Galois Field $\operatorname{GF}(2^{64})$ Affine Transformation Inversion, forward/backward S-box linear cryptanalysis, Gaussian elimination | `Intern_Pro_Max{gf2_aff1n3_m4ps_f4ll_t0_g4uss}` | [gf2-linear-cryptanalysis-gaussian-elimination](https://github.com/yashagarwal-lab/gf2-linear-cryptanalysis-gaussian-elimination) |
| **CEMA-H3** | AES Key Schedule Reversal from RAM Forensics, round constant ($\operatorname{Rcon}$) backward step, 128-bit master key recovery | `Intern_Pro_Max{sch3dul3_runs_b0th_ways}` | [aes-key-schedule-reversal-ram-forensics](https://github.com/yashagarwal-lab/aes-key-schedule-reversal-ram-forensics) |

---

## 📰 Autonomous Defense Magazine Generator (`mag-gen`)

An autonomous intelligence synthesis, layout fitting, and publication engine:
- **Repository:** [`yashagarwal-lab/automated-defense-magazine-generator`](https://github.com/yashagarwal-lab/automated-defense-magazine-generator)
- **Mathematical Page Budgeting:** Solves publication geometry to exactly 50 A4 pages (or arbitrary lengths like 24, 32, 64 pages) with 0mm overflow.
- **Dynamic Layout Registry:** 5 archetypes (`lead`, `pair`, `trio`, `quad`, `photo_essay`).
- **Dual Output:** High-resolution vector print PDF (Skia engine) and interactive dual-page web reader.
- **Pluggable Ingestion & Modular Themes:** Ingests JSON/Markdown/RSS and renders across service branch themes (`army_gold`, `navy_blue`, `airforce_slate`, `editorial_mono`).

---

## 📄 Formal Research Writeups & Publications

The repository includes four comprehensive post-mission technical writeups:
- [RF Track Writeup (Serial TARANG)](file:///home/yashagarwal/Code/internship_application_indian_army/RF_track_writeup.pdf)
- [UAV Track Writeup (Serial GAGAN)](file:///home/yashagarwal/Code/internship_application_indian_army/UAV_track_writeup.pdf)
- [5G Track Writeup (Serial LOHA JAAL)](file:///home/yashagarwal/Code/internship_application_indian_army/5g_track_writeup.pdf)
- [CEMA Track Writeup (Serial NIGHT KITE)](file:///home/yashagarwal/Code/internship_application_indian_army/CEMA_track_writeup.pdf)
- [CTF Technical Reference & Theoretical Notes](file:///home/yashagarwal/Code/internship_application_indian_army/CTF_Technical_Reference.md)

---

## 📁 Repository Directory Structure

```
internship_application_indian_army/
├── .gitignore                     # Production exclusions (caches, large captures)
├── LICENSE                        # MIT License
├── README.md                      # Master Defense Internship Portfolio (this document)
├── CTF_Technical_Reference.md     # In-depth mathematical reference for all 13 CTF challenges
├── 5g_track_writeup.pdf           # Formal publication writeup: 5G Core & Protocol Forensics
├── CEMA_track_writeup.pdf         # Formal publication writeup: Side-Channel & Cryptanalysis
├── RF_track_writeup.pdf           # Formal publication writeup: Signals & Spectrum Intelligence
├── UAV_track_writeup.pdf          # Formal publication writeup: Autonomous Drone & Navigation
│
├── hack_intern_challenge/         # Complete Exercise PARCHAM Challenge Source & Solvers
│   ├── rf_track/                  # Track 1: Serial TARANG (RF-H1, RF-H2, RF-H3, RF-H5)
│   ├── uav_track/                 # Track 2: Serial GAGAN (UAV-H1, UAV-H2, UAV-H3)
│   ├── 5g_mobile_track/           # Track 3: Serial LOHA JAAL (5G-H1, 5G-H2, 5G-H3)
│   ├── cema_track/                # Track 4: Serial NIGHT KITE (CEMA-H1, CEMA-H2, CEMA-H3)
│   └── writeups/                  # Markdown source writeups for each track
│
├── portfolio_micro_repos/         # Portfolio catalog of 13 standalone GitHub micro-repos
│   ├── README.md                  # Micro-repository registry and architecture guide
│   └── *.md                       # Technical documentation files for each repository
│
├── automated-defense-magazine-generator/ # Subsystem: Autonomous 50-page publication compiler
│   ├── configs/                   # Declarative publication specifications (50p, 24p)
│   ├── src/magazine_generator/    # Ingestion, curation, auto-budgeter, layout, rendering
│   └── output/                    # Print PDF and interactive reader artifacts
│
├── data/                          # Defense OSINT article bodies, image registry, datasets
└── shots/                         # Complete 50-page high-resolution render captures
```

---

## 🚀 Quickstart & Verification

```bash
# Clone the repository
git clone https://github.com/yashagarwal-lab/indian-army-internship-application.git
cd indian-army-internship-application

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install numpy scipy scapy matplotlib pyyaml

# Execute an individual challenge solver (e.g. UAV-H1 GNSS spoofing)
python3 hack_intern_challenge/uav_track/uav-h1-dead-reckoning/u1_dead_reckoning/solve.py

# Execute CEMA-H3 AES key schedule reversal
python3 hack_intern_challenge/cema_track/cema-h3-core-dump2/c3_core_dump2/solve_fast.py
```

---

## 📜 License

Licensed under the [MIT License](LICENSE).
