MASK = 0xFFFFF

def step(s):
    fb = ((s >> 19) ^ (s >> 16)) & 1
    return ((s << 1) | fb) & MASK

def channel_of(s):
    t1 = s & 0x7F
    t2 = (s >> 7) & 0x7F
    t3 = (s >> 14) & 0x3F
    return ((t1 ^ t2) + (t2 * t3)) % 80

s0 = 648113
s = s0
for k in range(1012):
    if k >= 1000:
        print(channel_of(s), end="-" if k < 1011 else "\n")
    s = step(s)
