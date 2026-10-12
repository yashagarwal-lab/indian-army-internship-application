"""
Better trace alignment using cross-correlation on a reference template
built from the MEAN of first-pass aligned traces (iterative refinement).
Then re-run CPA on better-aligned traces.
"""
import numpy as np

SBOX = np.array([
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16
], dtype=np.uint8)

HW = np.array([bin(x).count("1") for x in range(256)], dtype=np.uint8)

# ── Load raw traces ────────────────────────────────────────────────────────────
z = np.load("traces.npz")
raw_traces = z["traces"].astype(np.float64)
plaintexts = z["plaintexts"]
N, L = raw_traces.shape
print(f"Raw traces: {N} x {L}")

# ── Step 1: coarse alignment on the repeatable burst ──────────────────────────
# Use the burst signature (consistent across all traces) to align.
# Template = first trace
MAX_SHIFT = 80   # allow up to 80 sample jitter
TEMPLATE_START = 0
TEMPLATE_LEN = 200   # use first 200 samples (contains the burst)

# Build initial template from the first trace
template = raw_traces[0, TEMPLATE_START:TEMPLATE_START + TEMPLATE_LEN]

offsets = []
for i in range(N):
    t = raw_traces[i]
    # Search in a window around where the burst should be
    window = t[TEMPLATE_START : TEMPLATE_START + TEMPLATE_LEN + MAX_SHIFT]
    corr = np.correlate(window - window.mean(), template - template.mean(), mode='valid')
    shift = int(np.argmax(corr))
    offsets.append(shift)

offsets = np.array(offsets)
print(f"Shifts: min={offsets.min()}, max={offsets.max()}, std={offsets.std():.2f}")

# Trim to a length that works for all shifts
min_off = offsets.min()
max_off = offsets.max()
aligned_len = L - max_off
print(f"Aligned length: {aligned_len}")

aligned = np.zeros((N, aligned_len), dtype=np.float32)
for i in range(N):
    start = offsets[i] - min_off
    aligned[i] = raw_traces[i, start:start + aligned_len]

# ── Step 2: iterative refinement using mean template ──────────────────────────
for iteration in range(3):
    mean_trace = aligned.mean(axis=0)
    template_r = mean_trace[50:250]   # use the encryption region, skip leading burst
    offsets2 = []
    for i in range(N):
        window = aligned[i][0:300]
        corr = np.correlate(window - window.mean(), template_r - template_r.mean(), mode='valid')
        shift = int(np.argmax(corr))
        offsets2.append(shift)
    offsets2 = np.array(offsets2)
    min_o2 = offsets2.min()
    max_o2 = offsets2.max()
    new_len = aligned.shape[1] - max_o2
    refined = np.zeros((N, new_len), dtype=np.float32)
    for i in range(N):
        s = offsets2[i] - min_o2
        refined[i] = aligned[i, s:s + new_len]
    aligned = refined
    print(f"Iter {iteration+1}: shifts {min_o2}..{max_o2}, new shape {aligned.shape}")

print(f"\nFinal aligned shape: {aligned.shape}")

# ── Step 3: CPA ───────────────────────────────────────────────────────────────
traces_f = aligned.astype(np.float32)
traces_mean = np.mean(traces_f, axis=0)
traces_centered = traces_f - traces_mean
traces_ss = np.sum(traces_centered**2, axis=0)

print("\nTop-5 candidates per byte (CPA on re-aligned traces):\n")
recovered = []
for b in range(16):
    scores = []
    for guess in range(256):
        hyp = SBOX[plaintexts[:, b] ^ guess]
        preds = HW[hyp].astype(np.float32)
        preds_centered = preds - preds.mean()
        preds_ss = np.sum(preds_centered**2)
        if preds_ss == 0:
            continue
        cov = np.dot(preds_centered, traces_centered)
        corr = cov / np.sqrt(preds_ss * traces_ss)
        peak = float(np.max(np.abs(corr)))
        scores.append((peak, guess))
    scores.sort(reverse=True)
    top = scores[:5]
    top_str = "  ".join(f"{g:02x}({c:.4f})" for c, g in top)
    best = top[0][1]
    recovered.append(best)
    print(f"Byte {b:2d}: {top_str}")

hex_key = "".join(f"{x:02x}" for x in recovered)
print(f"\nIntern_Pro_Max{{{hex_key}}}")
