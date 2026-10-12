# UAV-H2 — Hopscotch II

**Exercise PARCHAM · Serial GAGAN · Barmer sector**

A small quadrotor has been loitering over a forward post in the Barmer sector for
three nights running, playing the hostile UAS for the exercise. Its control uplink
hops across 80 channels in the 865–867 MHz band at 50 hops per second, and the EW
detachment wants to put a reactive jammer **ahead** of the hop rather than chasing
it. For that they need the next channels before the aircraft gets to them.

The hop sequence is generated as follows, and this is the complete and exact
specification — the exercise directing staff have released it in full, because the
point of the serial is the key recovery, not the algorithm:

### Hop generator

A 20-bit Fibonacci LFSR with the primitive polynomial **x²⁰ + x¹⁷ + 1**:

```python
MASK = 0xFFFFF                      # 20-bit state

def step(s):
    fb = ((s >> 19) ^ (s >> 16)) & 1
    return ((s << 1) | fb) & MASK
```

The state is **not** used as the channel directly. It passes through this
nonlinear output filter:

```python
def channel_of(s):
    t1 = s & 0x7F
    t2 = (s >> 7) & 0x7F
    t3 = (s >> 14) & 0x3F
    return ((t1 ^ t2) + (t2 * t3)) % 80
```

Hop *k* (counting from zero) uses channel `channel_of(s_k)`, where `s_0` is the
secret 20-bit initial state and `s_{k+1} = step(s_k)`.

**The only thing you do not know is `s_0`.**

### Timing

The hop grid is exactly 20 ms, and hop 0 begins at `t = 0.000`. So the hop index
of an event at time *t* is `round(t / 0.02)`.

---

## The data

### `detections.csv`
| column | meaning |
|---|---|
| `t_s` | time of the detection, seconds, with a little timestamp jitter |
| `channel` | the channel the receiver saw energy on |

### `watchlist.txt`
The 32 channels (of 80) that the detachment's receiver was actually tuned to
monitor, comma separated. A hop onto any channel outside this list produced no
entry at all.

Two things about this log you should take seriously:

1. **It is incomplete.** Most hops are simply absent, because the receiver was
   only covering part of the band, and even a hop into a watched channel was
   sometimes missed.
2. **It is not clean.** A detachment two valleys over was running its own serial
   on the same band that night. Some entries in this file did not come from the
   link you care about.

---

## Your task

Recover the secret initial state, then report the channels used by the **next 12
hops after the end of the log window** — that is, hops **1000 through 1011**
inclusive.

## Flag format

Twelve channel numbers in hop order, joined by single hyphens, no spaces:

```
KST{c1000-c1001-c1002-c1003-c1004-c1005-c1006-c1007-c1008-c1009-c1010-c1011}
```

For example, if the next twelve hops were channels 7, 19, 3, 44, 61, 0, 12, 38,
75, 22, 9 and 50, the flag would be `KST{7-19-3-44-61-0-12-38-75-22-9-50}`.
