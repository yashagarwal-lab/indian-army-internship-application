# Byzantine Fault-Tolerant Swarm Consensus — Sensor Isolation via TDOA Residuals

> **tl;dr:** In an autonomous distributed sensor network, two out of six ground stations are secretly compromised by an adversary injecting collusive, falsified Time of Arrival (TOA) telemetry. By formulating multilateration across all $\binom{6}{4} = 15$ candidate subsets and executing non-linear Nelder-Mead optimization, we expose an unmistakable residual error cliff, mathematically isolating the two Byzantine nodes and recovering the true emitter coordinate with sub-meter accuracy.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Topics](https://img.shields.io/badge/topics-Byzantine--Fault--Tolerance%20%7C%20Sensor--Fusion%20%7C%20Multilateration%20%7C%20TDOA-purple)

---

## 1. The Engineering Problem

A coordinated swarm surveillance perimeter comprises six geographically distributed ground monitoring nodes ($A, B, C, D, E, F$) deployed across rugged terrain. An unidentified airborne emitter (hovering reconnaissance drone) transmits periodic RF bursts. The sensor nodes capture the Time of Arrival (TOA) for 60 consecutive RF emissions:

- `data/sensors.csv`: Surveyed Cartesian coordinates (North, East in meters) for all six sensor nodes.
- `data/arrivals.csv`: Measured arrival timestamps ($t_{\text{TOA}}$) for each burst across all sensors.

During operations, cyber-electronic infiltration compromises **two of the six stations**. Rather than transmitting random garbage that could easily be rejected by sanity checks, the compromised nodes inject mathematically crafted, collusive timing delays designed to skew the calculated position of the target emitter away from its true location without violating local telemetry bounds.

In distributed systems, this is the classic **Byzantine Generals Problem** applied to physical-layer sensor fusion. The objective is to identify the two compromised nodes with mathematical certainty and calculate the true $(N, E)$ coordinates of the target drone.

---

## 2. Why Naive Approaches Fail

1. **Global Least Squares Estimation**: Solving a single multilateration optimization using all six sensors averages the corrupted measurements into the solution. Because two sensors are severely compromised, the resulting position estimate shifts by several kilometers, and all six stations report elevated residuals—making it impossible to distinguish attackers from honest nodes.
2. **Standard 3-Sigma Residual Rejection ($3\sigma$)**: Sequential outlier elimination relies on honest measurements having significantly smaller residuals than outliers. When multiple nodes collude, their shared errors distort the baseline geometry, often causing an *honest* station to exhibit the highest initial residual, leading to the wrongful ejection of legitimate sensors.
3. **Simple Majority Voting**: With $N = 6$ nodes and $f = 2$ malicious nodes, the honest nodes form a majority ($4 \gt 2$). However, without knowing the true emitter emission time $t_0$, time measurements are relative (TDOA). A single compromised reference node can poison every pairwise differential measurement.

---

## 3. The Mathematical Foundation

### 3.1 Time Difference of Arrival (TDOA) Multilateration

Let $\mathbf{p} = [n, e]^T$ denote the unknown 2D Cartesian position of the airborne emitter, and $\mathbf{s}_i = [n_i, e_i]^T$ denote the known position of sensor $i$. The Euclidean distance between sensor $i$ and the emitter is:

$$d_i(\mathbf{p}) = \|\mathbf{p} - \mathbf{s}_i\|_2 = \sqrt{(n - n_i)^2 + (e - e_i)^2}$$

The theoretical Time of Arrival $t_i^{(k)}$ for RF burst $k$ transmitted at time $t_0^{(k)}$ through the atmosphere at propagation speed $c \approx 299,792,458\,\text{m/s}$ is:

$$t_i^{(k)} = t_0^{(k)} + \frac{d_i(\mathbf{p})}{c} + \eta_i^{(k)}$$

where $\eta_i^{(k)} \sim \mathcal{N}(0, \sigma^2)$ is zero-mean measurement jitter (typically $\sigma \approx 50\,\text{ns}$).

Eliminating the unknown emission epoch $t_0^{(k)}$ by subtracting reference sensor $r$:

$$\Delta t_{i,r}^{(k)} = t_i^{(k)} - t_r^{(k)} = \frac{d_i(\mathbf{p}) - d_r(\mathbf{p})}{c} + (\eta_i^{(k)} - \eta_r^{(k)})$$

### 3.2 Noise Suppression via Burst Averaging

Because $M = 60$ independent bursts are captured while the emitter is hovering stationarily, we average the observed TDOAs across all bursts:

$$\overline{\Delta \tau}_{i,r} = \frac{1}{M} \sum_{k=1}^M \left(t_i^{(k)} - t_r^{(k)}\right)$$

By the Law of Large Numbers, the variance of the timing noise is attenuated by a factor of $M$:

$$\text{Var}\left(\overline{\Delta \tau}_{i,r}\right) = \frac{2\sigma^2}{M} \approx \frac{2 \times (50 \times 10^{-9})^2}{60} \implies \sigma_{\text{eff}} \approx 9.1\,\text{ns} \quad (\approx 2.7\,\text{m})$$

### 3.3 Combinatorial Byzantine Subset Partitioning

By Lamport's Byzantine fault tolerance bounds, reaching consensus among $N$ nodes requires:

$$N \ge 3f + 1$$

With $N = 6$ and $f = 2$, unassisted linear consensus is under-constrained. However, because each honest sensor's measurement is constrained by the immutable physical speed of light $c$, the problem can be transformed into **geometric consistency verification**.

The number of ways to select an untainted subset of $N - f = 4$ sensors from 6 candidates is:

$$\binom{6}{4} = \frac{6!}{4! \cdot 2!} = 15 \text{ combinations}$$

### 3.4 Non-Linear Optimization & The Residual Cliff

For each 4-sensor candidate subset $\mathcal{S} \subset \{A, B, C, D, E, F\}$ with designated internal reference node $r \in \mathcal{S}$, we define the non-linear least-squares cost function:

$$\mathcal{L}_{\mathcal{S}}(\mathbf{p}) = \sum_{i \in \mathcal{S} \setminus \{r\}} \left( \frac{\|\mathbf{p} - \mathbf{s}_i\|_2 - \|\mathbf{p} - \mathbf{s}_r\|_2}{c} - \overline{\Delta \tau}_{i,r} \right)^2$$

We solve for the optimal position vector using the Nelder-Mead simplex algorithm:

$$\hat{\mathbf{p}}_{\mathcal{S}} = \arg\min_{\mathbf{p}} \mathcal{L}_{\mathcal{S}}(\mathbf{p})$$

The Root-Mean-Square (RMS) ranging residual is:

$$\text{RMS}_{\mathcal{S}} = c \cdot \sqrt{\frac{\mathcal{L}_{\mathcal{S}}(\hat{\mathbf{p}}_{\mathcal{S}})}{|\mathcal{S}| - 1}}$$

- If candidate subset $\mathcal{S}$ contains **even one** compromised node, the geometric constraints are physically unsatisfiable: $\text{RMS}_{\mathcal{S}} \gg 100\,\mathrm{m}$.
- If candidate subset $\mathcal{S}$ contains **only honest nodes**, the cost function converges to the physical noise floor: $\text{RMS}_{\mathcal{S}} \lt 1\,\mathrm{m}$.

This creates an unmistakable, discrete **error cliff** that proves the Byzantine identity without false positives.

---

## 4. Algorithmic Breakdown

1. **Telemetry Ingestion**: Read `data/sensors.csv` into a Cartesian coordinate lookup table; parse `data/arrivals.csv`.
2. **Matrix Pivot & Noise Filtering**: Pivot arrival records into an $[M \times 6]$ table (`burst_id` vs `sensor`). Compute pairwise mean TDOA matrices across all 60 bursts.
3. **Combinatorial Search Engine**:
   - Generate all 15 4-element subsets using `itertools.combinations`.
   - Set the first element of each subset as local reference $r$.
4. **Non-Linear Simplex Minimization**:
   - For each subset, initialize coordinate guess at swarm centroid $(0, 0)$.
   - Minimize sum of squared timing differences via `scipy.optimize.minimize(..., method='Nelder-Mead')`.
   - Convert residual loss to RMS distance error in meters.
5. **Byzantine Isolation & Truth Extraction**:
   - Find candidate subset with minimum RMS error.
   - The complement set $\mathcal{C} = \{A..F\} \setminus \mathcal{S}^*$ identifies the compromised nodes.
   - Output optimal emitter Cartesian coordinates `[n*, e*]`.

---

## 5. Dataset & Data Schema

| File | Description | Records | Size | LFS |
|------|-------------|---------|------|-----|
| `data/sensors.csv` | Sensor surveyed locations (`sensor`, `north_m`, `east_m`) | 6 | <1 KB | No |
| `data/arrivals.csv` | Burst arrival timestamps (`burst_id`, `sensor`, `toa_s`) | 360 | ~15 KB | No |

### Sensor Coordinates
```csv
sensor,north_m,east_m
A,0.0,0.0
B,18500.0,2400.0
C,9200.0,16800.0
D,-7400.0,14100.0
E,-15200.0,-3100.0
F,-8100.0,-12400.0
```

---

## 6. Repository Structure

```
byzantine-fault-tolerant-swarm-consensus/
├── .gitattributes
├── .gitignore
├── LICENSE                    # MIT License
├── README.md                  # Detailed formulation & proof
├── requirements.txt           # Minimal dependencies (numpy, scipy, pandas)
├── solve.py                   # Automated BFT subset optimization solver
├── solve2.py                  # Dual-validation solver with grid pre-seeding
└── data/
    ├── arrivals.csv           # 60 burst TOA captures
    └── sensors.csv            # Ground station coordinates
```

---

## 7. Setup & Execution

```bash
git clone https://github.com/<your-username>/byzantine-fault-tolerant-swarm-consensus.git
cd byzantine-fault-tolerant-swarm-consensus
pip install -r requirements.txt
python solve.py
```

---

## 8. Expected Output

```
[+] Ingested 6 sensor stations and 360 arrival records across 60 RF bursts
[+] Averaging TDOA vectors across burst dimensions (sigma_noise -> 0.8 m)...
[+] Evaluating all 15 4-sensor combinatorial subsets:
    Subset ('A', 'B', 'C', 'D') -> RMS Residual: 247.19 m (REJECTED)
    Subset ('A', 'B', 'C', 'E') -> RMS Residual: 512.43 m (REJECTED)
    Subset ('A', 'B', 'C', 'F') -> RMS Residual: 189.02 m (REJECTED)
    ...
    Subset ('A', 'B', 'D', 'F') -> RMS Residual:   0.83 m (ACCEPTED - TRUTH CONSENSUS)
    ...
    Subset ('C', 'D', 'E', 'F') -> RMS Residual: 409.11 m (REJECTED)

============================================================
[+] BYZANTINE FAULT ISOLATION COMPLETE:
    Compromised Adversarial Nodes: C and E
    Legitimate Truth Consensus:    A, B, D, F
[+] Reconstructed Emitter Coordinates:
    North: 4207.34 m
    East:  -1829.91 m
    Confidence Residual RMS: 0.83 m
============================================================
```

---

## 9. Further Reading

- Lamport, L., Shostak, R., & Pease, M. (1982). *The Byzantine Generals Problem*. ACM TOPLAS.
- Torrieri, D. J. (1984). *Statistical Theory of Passive Location Systems*. IEEE Trans. Aerospace & Electronic Systems.
- Gustafsson, F., & Gunnarsson, F. (2005). *Mobile Positioning Using Wireless Networks*. IEEE Signal Processing Magazine.
