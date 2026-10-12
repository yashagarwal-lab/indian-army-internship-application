# CEMA-H2 — Mission Seal II

**Exercise PARCHAM · Serial NIGHT KITE · Barmer sector**

Every mission file uploaded to the hostile-role drone squadron carries a 24-bit
**authentication seal**. The aircraft refuses any mission whose seal does not
check out, which is why the last three attempts to feed it a false tasking were
rejected on the pad. The seal is computed from the mission bytes together with a
64-bit **squadron key** that is provisioned once and never transmitted.

The monitoring detachment has intercepted five sealed missions off the uplink. We
want the squadron key, so that exercise control can author a tasking the aircraft
will accept.

## The seal algorithm

This is published and complete. Nothing is withheld — the key is the only secret.

```python
MASK64 = (1 << 64) - 1
MULC   = 0x9E3779B97F4A7C15
REDUCE = (1 << 4) | (1 << 3) | (1 << 1) | 1     # x^64 + x^4 + x^3 + x + 1

def rotl(x, n):
    return ((x << n) | (x >> (64 - n))) & MASK64

def gf_mul(a, b):
    """Multiply in GF(2^64) modulo x^64 + x^4 + x^3 + x + 1."""
    r = 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1
        a <<= 1
        if a & (1 << 64):
            a = (a & MASK64) ^ REDUCE
    return r & MASK64

def expand(m):
    """One message byte spread across 64 bits."""
    return (m * 0x0101010101010101) & MASK64

def seal(key, msg):
    s = key & MASK64
    for m in msg:                 # msg is a bytes object
        s = rotl(s, 11)
        s ^= expand(m)
        s = gf_mul(s, MULC)
    return s >> 40                # the top 24 bits are the seal
```

## The data

`sealed_missions.txt`, one mission per line:

```
<mission bytes as hex>:<seal as 6 hex digits>
```

The five missions are of five different lengths. All five were sealed with the
same squadron key.

---

## Your task

Recover the 64-bit squadron key.

Be warned that the obvious approach does not fit in the time available: there are
2⁶⁴ possible keys, and at a billion seal evaluations per second a full sweep takes
about 580 years. The serial runs for 48 hours. If you find yourself writing a loop
over the key space, stop and look harder at what the seal function actually does
to its state.

Note also that the seal is truncated — you only ever see 24 of the 64 bits the
algorithm computes. One mission on its own does not pin the key down.

## Flag format

The key as 16 lowercase hexadecimal characters:

```
Intern_Pro_Max{<16 hex chars>}
```

Verify before you submit: your key should reproduce all five published seals
exactly.
