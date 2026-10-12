# UAV-H3 — Consensus

**Exercise PARCHAM · Serial GAGAN · Jaisalmer sector**

Six ground sensors, deployed by the exercise signals intelligence cell across the
Jaisalmer sector, form a passive network that geolocates UAV uplink beacons by
time difference of arrival. A target drone held a hover somewhere inside the
network and transmitted 60 beacon bursts in the 865–867 MHz band. Every sensor
time-stamped every burst.

The network's own software reported a position, and the detachment acted on it.
Post-serial debrief says the aircraft was never there.

We have reason to believe **two of the six sensors have been interfered with** —
part of the serial, authorised by exercise control, and nobody is saying which
two.

The compromised sensors are not broken and are not jamming. They are reporting
arrival times that are internally consistent and perfectly plausible — just not
true. Their clocks are fine. Their data is complete. Nothing about either one
looks wrong when you examine it on its own.

## The data

### `sensors.csv`
| column | meaning |
|---|---|
| `sensor` | sensor identifier, `A` to `F` |
| `north_m`, `east_m` | sensor position in a local north/east plane, metres |

These positions are surveyed and correct for all six sensors.

### `arrivals.csv`
| column | meaning |
|---|---|
| `burst_id` | which beacon burst, 0 to 59 |
| `sensor` | which sensor reported it |
| `toa_s` | time of arrival at that sensor, seconds, on a common network clock |

The drone's transmit times are unknown. Sensor timing noise is around 50 ns
(1 σ), which is about 15 m of range.

Assume the drone was stationary for the whole recording.

---

## Your task

Report **where the drone actually was**, and **which two sensors are lying**.

- **Position** — north and east in metres in the same local frame as
  `sensors.csv`, each **rounded to the nearest 10 m**. Include a minus sign if
  the coordinate is negative.
- **Compromised sensors** — the two sensor letters, in alphabetical order, with
  nothing between them.

## Flag format

```
KST{<north>_<east>_<letters>}
```

For example, a drone at 3,480 m north and 920 m *south* (i.e. −920) with sensors
B and D compromised would be `KST{3480_-920_BD}`.
