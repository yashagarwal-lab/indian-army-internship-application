# RF-H2 — Chipped

**Exercise PARCHAM · Serial TARANG · forward logistics node, Tezpur**

The signals cell believes a covert link was run against the forward logistics node
at Tezpur during the night serial — an umpire-authorised insertion, reported after
the fact, with no parameters released. The wideband recording below was taken while
it was active.

Nothing is visible in it.

## The data

`buried.sigmf-data` / `buried.sigmf-meta` — SigMF, `cf32_le`, 400 kHz sample
rate, 516,128 complex samples, centred in the 2.4 GHz ISM band.

```python
import numpy as np
raw = np.fromfile("buried.sigmf-data", dtype=np.float32)
x = raw[0::2] + 1j*raw[1::2]
```

## What we know

The link is **direct-sequence spread spectrum**:

- Chip rate **100 kchip/s** (so 4 samples per chip at this sample rate).
- **127 chips per data symbol** — one full spreading code per bit.
- The data underneath is **BPSK**, framed as a 16-bit sync word
  `0111111000011101` followed by 8-bit ASCII, repeating.
- In-band signal-to-noise ratio is about **−12 dB**. The signal is well below the
  noise floor, which is why your spectrum plot looks empty. That is expected and
  is not a sign that you have the wrong file.

## What we do not have

**The spreading code.** It was never handed over. It is a 127-chip binary sequence
and it is not an m-sequence, a Gold code, a Barker code, or anything else you can
look up or generate — it is specific to this radio, and it is the one input that
every despreading tutorial assumes you already have.

The code's phase relative to the start of the file is also unknown, as is the
sample-level chip alignment.

## Your task

Recover the message. The flag is in it.

You will have to establish the spreading code from the capture itself. Think about
what the received chip stream looks like if you cut it into lengths of exactly one
code period — and what changes about that structure if you cut it in the wrong
place.

## Flag format

```
RFCTF{...}
```
