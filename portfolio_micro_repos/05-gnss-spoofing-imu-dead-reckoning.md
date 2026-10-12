# GNSS Velocity Spoofing Detection & Bearing Recovery via IMU Dead-Reckoning

> **tl;dr:** An airborne platform undergoes a stealthy GNSS velocity spoofing attack that ramps up smoothly to evade threshold alarms. By numerically integrating 50 Hz un-spoofable IMU accelerometer measurements, interpolating to 5 Hz GNSS timestamps, and detrending the linear sensor bias, we isolate the injected spoofing vector, extract the exact attack onset time, and calculate the adversary's injected velocity bearing.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Data via LFS](https://img.shields.io/badge/data-Git%20LFS-orange)
![Topics](https://img.shields.io/badge/topics-GNSS%20%7C%20IMU%20%7C%20Sensor--Fusion%20%7C%20Dead--Reckoning-purple)

---

## 1. The Engineering Problem

A surveillance UAV executing autonomous perimeter reconnaissance over remote terrain relies on dual navigation inputs: satellite GNSS fixes for global positioning and an internal Inertial Measurement Unit (IMU) for body-frame accelerations and angular rates. During routine flight, a hostile ground station initiates a **coordinated velocity spoofing attack**.

Rather than introducing an abrupt position hop or velocity step that would immediately trigger standard Kalman filter innovation/residual threshold tripwires, the adversary injects a smoothly ramping velocity offset vector into the satellite signal. The flight controller's onboard autopilot gradually slews off course under the false belief that it is counteracting wind shear, covertly diverting the drone toward adversarial airspace.

The incident response team extracts two telemetry streams:
- `gnss.csv`: Spoofed satellite navigation velocity and position fixes sampled at 5 Hz.
- `imu.csv`: Physical, un-spoofable strapdown inertial accelerations sampled at 50 Hz.

The mission objective is to reconstruct ground truth, mathematically prove the divergence, pinpoint the **attack onset timestamp** to the nearest 5 seconds, and recover the **compass bearing** of the injected velocity offset vector.

---

## 2. Why Naive Approaches Fail

1. **Direct GNSS Thresholding**: Standard flight-safety algorithms check acceleration jerk and velocity variance ($\Delta v / \Delta t$). Because the adversary applies a continuous, low-derivative ramp function, the pseudo-acceleration injected by the spoofer falls well within natural aerodynamic turbulence envelopes ($\lt 0.1\,\mathrm{m/s}^2$). No single-sensor outlier detector triggers.
2. **Raw Difference of IMU and GNSS**: If one integrates raw IMU accelerations without calibration and directly subtracts GNSS velocity, the resulting difference diverges exponentially or linearly over time due to **uncalibrated accelerometer bias** ($b_a$). The drift from cheap MEMS sensors overwhelms the spoofing signature, hiding the attack onset under an ever-growing linear error slope.
3. **Sampling Rate Mismatch**: GNSS arrives at 5 Hz ($T_s = 200\,\text{ms}$), while the IMU samples at 50 Hz ($T_s = 20\,\text{ms}$). A point-to-point subtraction without multi-rate temporal interpolation introduces severe aliasing and jitter.

---

## 3. The Mathematical Foundation

### 3.1 Inertial Dead-Reckoning (Newtonian Integration)

The physical acceleration measured by strapdown accelerometers along North and East navigation axes is:

$$a_{\text{meas}}(t) = a_{\text{true}}(t) + b_a + \eta_a(t)$$

where $b_a$ is the sensor bias and $\eta_a(t)$ is zero-mean Gaussian measurement noise.

Velocity is the Riemann integral of acceleration:

$$v_{\text{IMU}}(t) = v(0) + \int_{0}^{t} a_{\text{meas}}(\tau)\,d\tau \approx v(0) + \sum_{k=1}^{N} a_k \cdot \Delta t_k$$

In discrete time with $\Delta t = 0.02\,\text{s}$:

$$v_{\text{IMU}}[n] = \sum_{k=1}^{n} a_{\text{meas}}[k] \cdot \Delta t$$

Because $b_a$ is quasi-static, the integrated velocity contains an accumulated linear drift component:

$$v_{\text{IMU}}(t) = v_{\text{true}}(t) + b_a \cdot t + \int \eta_a(\tau)\,d\tau$$

### 3.2 Spoofed GNSS Model

The satellite receiver reports true velocity plus the adversary's injected error vector $v_{\text{spoof}}(t)$:

$$v_{\text{GNSS}}(t) = v_{\text{true}}(t) + v_{\text{spoof}}(t)$$

where:
- For $t \lt t_{\mathrm{onset}}$: $v_{\mathrm{spoof}}(t) = 0$
- For $t_{\mathrm{onset}} \le t \lt t_{\mathrm{settle}}$: $v_{\mathrm{spoof}}(t)$ ramps linearly or smoothly
- For $t \ge t_{\mathrm{settle}}$: $v_{\mathrm{spoof}}(t) = v_{\mathrm{plateau}}$ (constant injected drift vector)

### 3.3 Residual Divergence & Bias Detrending

Taking the raw difference between GNSS and interpolated IMU velocity yields:

$$\Delta v(t) = v_{\text{GNSS}}(t) - v_{\text{IMU}}(t) = v_{\text{spoof}}(t) - b_a \cdot t - v(0)$$

During the known pre-attack operational window ($t \in [0, 400]\,\text{s}$), $v_{\text{spoof}}(t) \equiv 0$. Therefore:

$$\Delta v_{\text{pre}}(t) = - b_a \cdot t - v(0)$$

We fit a first-order polynomial via least-squares linear regression:

$$\min_{m, c} \sum_{t_i \lt 400} \left(\Delta v(t_i) - (m \cdot t_i + c)\right)^2$$

Subtracting this baseline trend across the entire duration yields the **detrended velocity error**:

$$\Delta v_{\text{detrended}}(t) = \Delta v(t) - (m \cdot t + c) \approx v_{\text{spoof}}(t)$$

This cancels the accelerometer sensor bias completely:
- For $t \lt t_{\mathrm{onset}}$: $\Delta v_{\mathrm{detrended}}(t) \approx 0$
- For $t \gt t_{\mathrm{settle}}$: $\Delta v_{\mathrm{detrended}}(t)$ sits on a steady-state plateau $[v_{\mathrm{plat}, N}, v_{\mathrm{plat}, E}]$.

### 3.4 Injected Bearing Extraction

Given the steady-state Cartesian components of the detrended velocity plateau:

$$\Delta v_N = \mathbb{E}\left[\Delta v_{\text{detrended}, N}(t)\right]_{t \in [1200, 1800]}$$

$$\Delta v_E = \mathbb{E}\left[\Delta v_{\text{detrended}, E}(t)\right]_{t \in [1200, 1800]}$$

The compass bearing $\theta$ (measured clockwise from True North) is computed via two-argument arctangent:

$$\theta = \text{atan2}(\Delta v_E, \Delta v_N) \times \frac{180^\circ}{\pi} \pmod{360^\circ}$$

---

## 4. Algorithmic Breakdown

1. **Load Telemetry**:
   - Ingest `gnss.csv` (`t_s`, `vel_n_mps`, `vel_e_mps`).
   - Ingest `imu.csv` (`t_s`, `acc_n_mps2`, `acc_e_mps2`).
2. **Compute Time Step**: Extract $\Delta t$ per IMU sample and pad the initial step.
3. **Cumulative Numerical Integration**: Compute `vel_n` and `vel_e` as `np.cumsum(acc * dt)`.
4. **Multi-Rate Interpolation**: Project 50 Hz IMU integrated velocities onto 5 Hz GNSS timestamps using 1D piecewise linear interpolation (`np.interp`).
5. **Compute Raw Differential Velocity**: $\Delta v_N = v_{\text{GNSS}, N} - v_{\text{IMU}, N}$.
6. **First-Order Bias Detrending**:
   - Filter timestamps $t \lt 400\,\mathrm{s}$.
   - Fit linear coefficients $(m_N, c_N)$ and $(m_E, c_E)$ using `np.polyfit(..., 1)`.
   - Subtract evaluated polynomial trend from all timestamps.
7. **Onset & Plateau Isolation**:
   - Observe divergence onset at $t \approx 400\,\text{s}$.
   - Compute mean plateau offset in the steady-state window $t \in [1200, 1800]\,\text{s}$.
8. **Bearing Calculation**: Compute `math.atan2(e_plat, n_plat)` and round to compass degrees.

---

## 5. Dataset & Data Schema

| File | Description | Frequency | Samples | Size | LFS |
|------|-------------|-----------|---------|------|-----|
| `data/gnss.csv` | Spoofed satellite velocity/position fixes | 5 Hz | ~10,000 | 379 KB | Yes |
| `data/imu.csv` | Un-spoofed 3-axis accelerometer readings | 50 Hz | ~100,000 | 2.3 MB | Yes |
| `data/vel_diff.png` | Plot of raw velocity divergence showing sensor drift | — | — | ~60 KB | Yes |
| `data/vel_diff_detrended.png` | Plot of detrended velocity error showing spoof onset | — | — | ~60 KB | Yes |

### CSV Schemas

- **`gnss.csv`**:
  ```csv
  t_s,lat_deg,lon_deg,alt_m,vel_n_mps,vel_e_mps,vel_d_mps
  0.0,27.0234,71.9123,240.1,12.34,-4.12,0.01
  ...
  ```
- **`imu.csv`**:
  ```csv
  t_s,acc_n_mps2,acc_e_mps2,acc_d_mps2
  0.0,0.123,-0.045,9.806
  ...
  ```

---

## 6. Repository Structure

```
gnss-spoofing-imu-dead-reckoning/
├── .gitattributes             # Git LFS tracking for CSV and PNG
├── .gitignore
├── LICENSE                    # MIT License
├── README.md                  # Technical specification & derivation
├── requirements.txt           # Minimal pinned dependencies
├── solve.py                   # Automated sensor fusion & detector
└── data/
    ├── gnss.csv               # 5 Hz GNSS telemetry (LFS)
    ├── imu.csv                # 50 Hz IMU telemetry (LFS)
    ├── vel_diff.png           # Raw divergence plot (LFS)
    └── vel_diff_detrended.png # Detrended divergence plot (LFS)
```

---

## 7. Setup & Execution

### Prerequisites

Ensure Git LFS is installed and initialised:
```bash
git lfs install
```

### Installation

```bash
git clone https://github.com/<your-username>/gnss-spoofing-imu-dead-reckoning.git
cd gnss-spoofing-imu-dead-reckoning
git lfs pull
pip install -r requirements.txt
```

### Running the Detector

```bash
python solve.py
```

---

## 8. Expected Output

```
[+] Ingested 10000 GNSS samples (5 Hz) and 100000 IMU samples (50 Hz)
[+] Numerical integration and multi-rate temporal interpolation complete
[+] Calibrating accelerometer bias drift over clean window (t < 400 s)...
    North bias drift: -0.0124 m/s^2 | East bias drift: 0.0089 m/s^2
[+] Detrended residual velocity calculated
[+] Detected Attack Onset: t = 400 s
[+] Steady-State Spoofed Velocity Plateau (t in [1200, 1800] s):
    Delta v_North = -8.12 m/s
    Delta v_East  = 14.07 m/s
[+] Calculated Injected Bearing: 120° (Compass heading ESE)
```

---

## 9. Further Reading

- Farrell, J. A. (2008). *Aided Navigation: GPS with High Rate Sensors*. McGraw-Hill.
- Humphreys, T. E., et al. (2008). *Assessing the Spoofing Threat: Development of a Portable Civilian GPS Spoofer*. ION GNSS.
- Groves, P. D. (2013). *Principles of GNSS, Inertial, and Multisensor Integrated Navigation Systems*. Artech House.
