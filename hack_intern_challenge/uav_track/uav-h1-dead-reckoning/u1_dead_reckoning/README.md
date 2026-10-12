# UAV-H1 — Dead Reckoning

**Exercise PARCHAM · Serial GAGAN · Pokhran Field Firing Ranges, Rajasthan**

No. 7 UAV Flight put a survey aircraft up for an 1800-second sortie over the
Pokhran ranges, mapping the eastern impact area. On recovery the detachment
commander reported that the aircraft "came home down a line it was never tasked
along", though the flight log looks clean on a first pass and the onboard
satellite navigation never raised an alarm.

Exercise control has confirmed that an umpire-authorised GNSS spoofing serial was
run against this sortie. Nobody will tell you when, and nobody will tell you from
where. That is your job.

The spoofer did not teleport the aircraft and did not produce a jump: it injected
a small constant velocity error, faded it in smoothly, and kept the reported
position and velocity consistent with each other throughout. Nothing inside the
GNSS data contradicts itself.

You have two files.

### `imu.csv` — inertial measurements, 50 Hz
| column | meaning |
|---|---|
| `t_s` | time since start of log, seconds |
| `acc_n_mps2` | acceleration, north component, m/s² |
| `acc_e_mps2` | acceleration, east component, m/s² |

These are navigation-frame horizontal accelerations as logged by the autopilot
(already rotated out of the body frame; gravity already removed). They come from
the aircraft's own inertial unit, which is **independent of the satellite
navigation**. The accelerometer has a small constant bias that nobody calibrated.

### `gnss.csv` — satellite navigation fixes, 5 Hz
| column | meaning |
|---|---|
| `t_s` | time since start of log, seconds |
| `pos_n_m`, `pos_e_m` | reported position in a local north/east plane, metres |
| `vel_n_mps`, `vel_e_mps` | reported velocity, m/s |

The log is as recorded, warts and all: there is a genuine loss of lock during the
sortie — the ranges are not kind to a small antenna — and a handful of
single-epoch bad fixes. **Not every anomaly in this file is the attack.**

---

## Your task

Determine **when the spoofing began** and **which way the spoofer pushed the
aircraft**.

- **Onset** — the time the injected error began to be applied, in seconds since
  the start of the log, **rounded to the nearest 5 seconds**. Note that the error
  is faded in gradually, so "the moment it became noticeable" is *later* than the
  moment it began. We want the moment it began.
- **Bearing** — the compass bearing of the injected velocity, in degrees, where
  0 = north and 90 = east, **rounded to the nearest 10 degrees**, written as three
  digits.

## Flag format

```
KST{<onset>_<bearing>}
```

Onset as a plain integer, bearing as three digits. For example, an attack
beginning at 400 seconds and pushing the aircraft due west would be
`KST{400_270}`.
