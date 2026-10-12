# RF-H3 — Fingerprint

**Exercise PARCHAM · Serial TARANG · signals park, Tezpur**

An unauthorised transmission was made on the exercise control net at 433 MHz —
a false tasking, passed in clear, that moved a detachment off its objective in the
Tezpur sector before the umpires caught it. Eight radios were issued to
participating detachments and any of them could have been used.

We recorded three reference bursts from each of the eight sets under controlled
conditions at the Tezpur signals park, and we have the offending transmission
itself.

Establish which radio sent it.

## The data

```
reference/radio_A_1.sigmf-data   ...   reference/radio_H_3.sigmf-data
unknown/unknown_transmission.sigmf-data
```

All SigMF, `cf32_le`, 400 kHz sample rate. References are 100 ms, the unknown is
300 ms.

```python
import numpy as np
raw = np.fromfile("unknown/unknown_transmission.sigmf-data", dtype=np.float32)
y = raw[0::2] + 1j*raw[1::2]
```

Every radio transmits the same way: real-valued BPSK at 5 kBd, upconverted to its
own carrier offset within the recorded span.

## Your task

Name the radio that sent the unauthorised transmission.

Understand what you are up against. Whoever used that set knew that carrier
frequency offset, output power and symbol rate are the first three things any
monitoring post measures, and **adjusted all three to match another radio in this
set**. Those features will give you a clean, confident, well-separated answer,
and it will put the blame on the wrong detachment.

To get this right you need a feature the operator could not change from the front
panel — something that comes from the physical imperfection of the transmitter
hardware rather than from its settings. There is more than one such feature
present in these recordings, and they agree with each other, so you can check
your own work.

## What to report

Three things:

1. The radio that **actually** sent the unknown transmission (a letter A–H).
2. The radio it was **impersonating** (a letter A–H).
3. The unknown transmitter's **image rejection ratio**, as a positive number of
   dB, rounded to the nearest **2 dB**. (If you measure −30.4 dB, report `30`.)

## Flag format

```
RFCTF{<true radio>_<impersonated radio>_<image rejection dB>}
```

For example, if radio F were impersonating radio A with an image rejection of
−36 dB, the flag would be `RFCTF{F_A_36}`.
