# RF-H1 — Two Radios, One Channel

**Exercise PARCHAM · Serial TARANG · Monitoring Post CHETAK, Siliguri corridor**

Monitoring Post CHETAK recorded two seconds of a 200 kHz span centred on 433.05 MHz
while working a routine serial. The post's own log notes the net it was tasked to
copy. The exercise signals cell, reviewing the tape afterwards, is satisfied that
**two** emitters were active during the recording, and that the one worth having is
the quieter of the two.

## The data

`cochannel.sigmf-data` / `cochannel.sigmf-meta` — SigMF, `cf32_le`,
200 kHz sample rate, 400,000 complex samples.

```python
import numpy as np
raw = np.fromfile("cochannel.sigmf-data", dtype=np.float32)
x = raw[0::2] + 1j*raw[1::2]
```

## What we know

- Both emitters are **BPSK with rectangular pulses**.
- Both are on the **same carrier frequency**. Not adjacent, not offset — the
  same. There is no frequency at which you will find one without the other.
- The net the post routinely copies runs at **12.5 kBd** and is the stronger of
  the two by roughly 15 dB.
- The other emitter's symbol rate is not known to us. It is not 12.5 kBd.
- Both streams are framed: a 16-bit sync word `0111111000011101` followed by
  8-bit ASCII, repeating. BPSK has no absolute phase reference, so the sync word
  is also what tells you whether your bit stream is the right way up.

## Your task

Recover the message carried by the **weaker** emitter. The flag is in it.

A word of warning: a plain demodulator will lock to the strong emitter and give
you a complete, clean, correct decode of the routine net traffic. That decode is
not a failure state — it will look like success. It is not the answer.

## Flag format

```
RFCTF{...}
```

Submit it exactly as it appears in the recovered message.
