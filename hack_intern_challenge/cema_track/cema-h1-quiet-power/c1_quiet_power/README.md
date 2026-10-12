# CEMA-H1 — Quiet Power

**Exercise PARCHAM · Serial NIGHT KITE · EME field workshop, Barmer**

The hostile-role drone brought down in the Barmer sector has been stripped at the
field workshop. Its flight controller authenticates every command packet it
receives with AES-128, and the exercise cell wants the key so that the captured
airframe can be flown back against its own operators on the next serial.

We cannot read the key out of the chip. What we could do is put a current probe on
its power rail and record what the chip does while it encrypts.

We captured **2000 encryptions**, each with a different known input block. We want
the key.

## The data

`traces.npz` is a NumPy archive with two arrays:

| array | shape | meaning |
|---|---|---|
| `traces` | (2000, 800) `int16` | power measurement, 800 samples per encryption |
| `plaintexts` | (2000, 16) `uint8` | the 16 input bytes fed to that encryption |

```python
import numpy as np
z = np.load("traces.npz")
traces, plaintexts = z["traces"], z["plaintexts"]
```

## What the chip is doing

Standard AES-128. The measurable leakage is in the **first round**: the power drawn
while the chip handles a byte varies with the *Hamming weight* (number of set bits)
of the S-box output for that byte, i.e. of

```
SBOX[plaintext_byte ^ key_byte]
```

Each of the 16 bytes is processed at a different moment within the trace.

## Honest warnings about this capture

The workshop rig was triggered by the target's own activity rather than by a clean
external signal, and **the trigger was not reliable** — the recording window
started at a slightly different moment on every single encryption. The data is
exactly as it came off the instrument; we have not conditioned it in any way.

There is a strong, repeatable burst of activity near the beginning of every trace
which is the same on every capture. It is not part of the encryption.

Expect to need to look carefully at how confident your recovered bytes actually
are. An answer that comes out of the maths is not necessarily a correct one, and
this attack is perfectly capable of returning sixteen wrong bytes without
complaining.

---

## Your task

Recover the full 16-byte AES-128 key.

## Flag format

The key as 32 lowercase hexadecimal characters, no separators:

```
Intern_Pro_Max{<32 hex chars>}
```

For example a key of bytes `00 11 22 ... ff` would be written
`Intern_Pro_Max{00112233445566778899aabbccddeeff}`.
