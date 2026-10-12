# UAV Track: Comprehensive Technical Writeup

This document provides an atomic-level breakdown of the three challenges in the UAV track. By deconstructing the underlying physics, mathematics, and code logic, you will have the profound depth required to write your final report in your own words.

---

## UAV-H1: Dead Reckoning

### Context & Goal
A UAV mapping the Pokhran ranges was subjected to a GNSS spoofing attack. The spoofer injected a constant velocity error, faded it in smoothly, and did not cause any sudden jumps. You are given `gnss.csv` (spoofed satellite navigation fixes at 5 Hz) and `imu.csv` (un-spoofed inertial accelerations at 50 Hz). The objective is to determine the exact **onset** time (when the error started, to the nearest 5 seconds) and the compass **bearing** of the injected velocity error (to the nearest 10 degrees).

### The Vulnerability / Concept
The GNSS receiver reports position and velocity, which can be spoofed by overriding the satellite signals. However, the IMU (Inertial Measurement Unit) measures physical acceleration from inside the aircraft and cannot be spoofed remotely. 

According to classical mechanics, velocity is the integral of acceleration:
$$v(t) = \int a(t) dt$$

If we numerically integrate the IMU's raw horizontal accelerations (`acc_n`, `acc_e`), we get the drone's true velocity. By subtracting this true velocity from the GNSS-reported velocity, the difference should be constant (representing the uncalibrated IMU bias). When the spoofing begins, this difference will diverge (ramp up) and eventually settle on a new plateau representing the injected velocity error.

### Algorithmic Breakdown
1.  **Numerical Integration:** Multiply the IMU acceleration by the time delta ($dt = 0.02$s for 50 Hz) and take the cumulative sum to get velocity.
2.  **Interpolation:** Because IMU is 50 Hz and GNSS is 5 Hz, we use linear interpolation (`np.interp`) to align the IMU timestamps to the GNSS timestamps.
3.  **Detrending the Bias:** We fit a 1st-degree polynomial (`np.polyfit`) to the velocity difference during the first 400 seconds (before the spoofing) to find the linear drift caused by the constant IMU bias. We subtract this trend line from the entire dataset.
4.  **Finding the Plateau:** After detrending, the pre-attack difference is exactly 0. We average the stable plateau region (e.g., from 1200 to 1800 seconds) to find the steady-state spoofed velocity components (`n_plat`, `e_plat`).
5.  **Bearing Calculation:** We use the arctangent function (`math.atan2(East, North)`) to convert the North and East Cartesian vectors into a compass bearing.

### Code Walkthrough (Key Segments)

```python
# 1. Integrate IMU Acceleration to Velocity
dt = np.diff(imu['t_s'])
dt = np.insert(dt, 0, dt[0]) # Pad first element
imu['vel_n'] = np.cumsum(imu['acc_n_mps2'] * dt)
imu['vel_e'] = np.cumsum(imu['acc_e_mps2'] * dt)

# 2. Interpolate IMU to GNSS timestamps
imu_vel_n_interp = np.interp(gnss['t_s'], imu['t_s'], imu['vel_n'])

# 3. Detrending the baseline (first 400s is clean)
diff_vel_n = gnss['vel_n_mps'].values - imu_vel_n_interp
mask = gnss['t_s'] < 400
z_n = np.polyfit(gnss['t_s'][mask], diff_vel_n[mask], 1)
trend_n = np.poly1d(z_n)(gnss['t_s'])
diff_vel_n_detrended = diff_vel_n - trend_n

# 4. Calculate Bearing of the injected spoofing
n_plat_all = diff_vel_n_detrended[mask_all_plateau].mean() - n_base
e_plat_all = diff_vel_e_detrended[mask_all_plateau].mean() - e_base
bearing_all = math.degrees(math.atan2(e_plat_all, n_plat_all))
```

### Execution & Results
By plotting `diff_vel_n_detrended`, we visually identify the onset time when the flat 0-line begins to ramp up (e.g., at $T=400$s). The `atan2` math accurately extracts the bearing of the plateau, yielding the final flag.

---

## UAV-H2: Hopscotch 2

### Context & Goal
A frequency-hopping radio uses a 20-bit Fibonacci Linear Feedback Shift Register (LFSR) combined with a non-linear output filter to pick its channels. You are given a CSV of partial, noisy detections (some real, some from a nearby detachment) and a watchlist of channels the receiver was actually tuned to. You must recover the initial 20-bit state ($s_0$) and predict the next 12 hops (1000 through 1011).

### The Vulnerability / Concept
The state space of a 20-bit LFSR is extremely small: exactly $2^{20} = 1,048,576$ possible initial states. Because the state space is so small, cryptographic techniques aren't necessary. A pure brute-force approach is perfectly viable. 

By taking the observed `t_s` timestamps, dividing by the hop grid duration ($20$ ms), we can determine the exact hop index $k$ for every detection. We then iterate through all $2^{20}$ possible states, simulating the LFSR forward for each detection index, and checking if the simulated output matches the observed channel. 

### Algorithmic Breakdown
1.  **Hop Index Calculation:** $k = \text{round}(t / 0.02)$.
2.  **LFSR Simulation:** Implement the Fibonacci LFSR step function (shifting left by 1 and XORing taps 19 and 16 to feed the LSB).
3.  **Non-Linear Filter:** Implement the `channel_of(s)` logic, which extracts 7-bit and 6-bit chunks from the state and mixes them with XOR and multiplication modulo 80.
4.  **Brute Force Evaluation:** Since the data is noisy (contains false positives from another radio), we cannot demand a 100% match. Instead, for each of the $1,048,576$ seeds, we count how many of its predicted channels match the `detections.csv`. The seed with the highest score is $s_0$.

### Code Walkthrough (Key Segments)

```python
# The LFSR Step Function
MASK = 0xFFFFF
def step(s):
    fb = ((s >> 19) ^ (s >> 16)) & 1
    return ((s << 1) | fb) & MASK

# The Non-Linear Channel Filter
def channel_of(s):
    t1 = s & 0x7F
    t2 = (s >> 7) & 0x7F
    t3 = (s >> 14) & 0x3F
    return ((t1 ^ t2) + (t2 * t3)) % 80

# To predict the flag, run the recovered seed forward 1000 steps
s0 = 648113 # Recovered from brute force
s = s0
for k in range(1012):
    if k >= 1000:
        print(channel_of(s))
    s = step(s)
```

### Execution & Results
Running the brute-force script in C (for speed) or optimized Python quickly reveals the true seed ($s_0 = 648113$). Stepping this state forward 1000 times perfectly predicts the requested 12-channel sequence.

---

## UAV-H3: Consensus

### Context & Goal
Six ground sensors (A through F) report the Time of Arrival (TOA) of 60 RF bursts from a hovering drone. The problem states that exactly **two** sensors are compromised (spoofed/lying) but internally consistent. The goal is to determine the true Cartesian position of the drone and identify the two lying sensors.

### The Vulnerability / Concept
This is a classic TDOA (Time Difference of Arrival) geolocation problem (Multilateration).
In a vacuum, if we know the drone's position $(N, E)$, the theoretical TDOA between any sensor $S$ and a reference sensor $R$ is strictly defined by the speed of light $c$:
$$\text{TDOA}_{S,R} = \frac{Distance_S - Distance_R}{c}$$

Because exactly two sensors are lying, the remaining **four** sensors must form a perfectly consistent truth group. The number of ways to pick 4 sensors out of 6 is $C(6,4) = 15$. We can simply test all 15 combinations. For each combination, we run a non-linear optimizer to find the $(N,E)$ coordinate that minimizes the TDOA error. 14 of the combinations will result in massive errors because they include a lying sensor. Exactly 1 combination will converge to near-zero error.

### Algorithmic Breakdown
1.  **TDOA Calculation:** Group the bursts by `burst_id` and average the TOA differences over all 60 bursts to filter out the 50ns timing noise.
2.  **Combinatorics:** Use `itertools.combinations(sensors, 4)` to iterate through the 15 subsets.
3.  **Cost Function:** For a guessed position $(n, e)$, calculate the theoretical TDOA for the subset and subtract the measured TDOA. Square this error.
4.  **Nelder-Mead Optimization:** Use `scipy.optimize.minimize` to find the $(N, E)$ that minimizes the cost function for that subset.
5.  **Truth Extraction:** The subset yielding an RMS error near ~15m (the theoretical noise floor) is the truth subset. The 2 excluded sensors are the compromised ones.

### Code Walkthrough (Key Segments)

```python
# The Error / Cost Function for the Optimizer
def error_func(x):
    n, e = x
    err = 0
    d_ref = get_distance((n, e), sensor_pos[ref])
    for s in subset[1:]:
        d_s = get_distance((n, e), sensor_pos[s])
        expected_tdoa = (d_s - d_ref) / c
        # Add squared error between theoretical TDOA and measured TDOA
        err += (expected_tdoa - tdoa_ref[s])**2
    return err

# Test all combinations of 4
for subset in itertools.combinations(sensor_names, 4):
    res = minimize(error_func, [n0, e0], method='Nelder-Mead')
    rms_error = np.sqrt(res.fun / 3) * c
    if rms_error < best_error:
        best_error = rms_error
        best_pos = res.x
        best_subset = subset
```

### Execution & Results
The optimizer tests all 15 permutations. It finds a massive error cliff for one specific subset of 4 sensors, immediately identifying the true coordinates of the drone and mathematically proving which two sensors were compromised.

---
---

## Deep Dive: UAV Tracking & Sensor Fusion Glossary

To truly master the UAV track, you need to understand navigation math, radio tracking, and error minimization algorithms. Here is an atomic-level breakdown of the concepts used.

### 1. GNSS vs IMU (H1)
- **GNSS (Global Navigation Satellite System):** Commonly known as GPS. It relies on extremely weak radio signals broadcast from satellites in space. Because the signals are so weak, it is trivial for an attacker on the ground to broadcast fake GPS signals and overpower the real ones ("Spoofing").
- **IMU (Inertial Measurement Unit):** A physical sensor sitting inside the drone containing tiny gyroscopes and accelerometers. It measures physical gravity and momentum. Because it is completely sealed off and doesn't rely on outside radio waves, it **cannot be spoofed remotely**. 
- **The Concept:** By comparing the easily-spoofed GPS data against the un-spoofable IMU data, you can instantly detect if a drone is being hijacked.

### 2. Integration and Detrending (H1)
- **Integration:** The IMU measures Acceleration ($m/s^2$). To compare it to the GPS Velocity ($m/s$), you must multiply the acceleration by the time that passed (dt). Accumulating these slices over time is called Integration ($v = \int a dt$).
- **Detrending Bias:** Cheap IMU sensors aren't perfect. They have a slight electrical "bias" (e.g., they might constantly report 0.01 $m/s^2$ of movement even when sitting perfectly still). If you integrate this bias over a 30-minute flight, your math will claim the drone drifted miles away! To fix this, you find the slope of the error during a known "safe" period, and subtract that slope from the whole dataset (Detrending).

### 3. LFSR (Linear Feedback Shift Register) (H2)
Instead of hard-coding a list of frequencies for a radio to hop between, engineers use LFSRs to generate a chaotic, random-looking sequence of channels on the fly.
An LFSR is just a binary counter (like a 20-bit register). Every "tick", it shifts all the bits to the left. The empty spot on the right is filled by taking a few bits from the middle (the "taps") and XORing them together. 
- **The Vulnerability:** An LFSR looks random, but it is entirely deterministic. If you know the starting state (the "Seed"), you can predict every single channel it will ever hop to. Because a 20-bit LFSR only has 1,048,576 possible seeds, a normal computer can test every single possibility in less than a second (Brute Force).

### 4. TDOA (Time Difference of Arrival) & Multilateration (H3)
Imagine two people standing far apart, listening for a lightning strike. The person closer to the lightning hears it first. By comparing the *Time Difference* between when Person A heard it and when Person B heard it, you can draw a curve (a hyperbola) on a map showing where the lightning could have hit.
- **Multilateration:** If you have 3 or 4 people (sensors) doing this, you can draw multiple intersecting hyperbolas. The exact point where they all intersect is the location of the drone.
- **The Math:** The time it takes a radio wave to travel is precisely $Distance / Speed Of Light$. By reversing this math, you convert the timestamps in the logs into physical distances.

### 5. Combinatorics and Error Minimization (H3)
- **Combinatorics:** You have 6 sensors, but you know 2 are compromised (giving fake data). Instead of trying to guess which two are fake, you just mathematically test every possible group of 4. Picking 4 out of 6 yields exactly 15 combinations ($C(6,4) = 15$).
- **Nelder-Mead Optimizer:** For each group of 4, the computer makes a wild guess about where the drone is (e.g., $X=0, Y=0$). It calculates what the TDOA *should* be for that guess, and compares it to the real TDOA from the logs. The difference is the "Error". The Nelder-Mead algorithm intelligently slides the $(X,Y)$ guess around the map until the Error hits rock bottom. 
- **The Insight:** If the group of 4 contains a fake sensor, the Error can never hit zero (the hyperbolas will never intersect). When the script finally tests the one group of 4 that has zero fake sensors, the Error magically drops to zero, proving you found both the true location and the true sensors!
