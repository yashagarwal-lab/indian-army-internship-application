"""
CPA attack on AES-128 power traces.

Strategy:
1. Align traces using cross-correlation on the burst region
2. For each key byte, compute HW(SBOX[pt ^ k]) for all 256 candidates
3. Correlate hypothetical power with measured traces
4. The candidate with highest Pearson correlation is the key byte
5. Validate by checking correlation margin (best vs second-best)
"""

import numpy as np
from scipy import signal

# AES S-box
SBOX = [
    0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76,
    0xCA, 0x82, 0xC9, 0x7D, 0xFA, 0x59, 0x47, 0xF0, 0xAD, 0xD4, 0xA2, 0xAF, 0x9C, 0xA4, 0x72, 0xC0,
    0xB7, 0xFD, 0x93, 0x26, 0x36, 0x3F, 0xF7, 0xCC, 0x34, 0xA5, 0xE5, 0xF1, 0x71, 0xD8, 0x31, 0x15,
    0x04, 0xC7, 0x23, 0xC3, 0x18, 0x96, 0x05, 0x9A, 0x07, 0x12, 0x80, 0xE2, 0xEB, 0x27, 0xB2, 0x75,
    0x09, 0x83, 0x2C, 0x1A, 0x1B, 0x6E, 0x5A, 0xA0, 0x52, 0x3B, 0xD6, 0xB3, 0x29, 0xE3, 0x2F, 0x84,
    0x53, 0xD1, 0x00, 0xED, 0x20, 0xFC, 0xB1, 0x5B, 0x6A, 0xCB, 0xBE, 0x39, 0x4A, 0x4C, 0x58, 0xCF,
    0xD0, 0xEF, 0xAA, 0xFB, 0x43, 0x4D, 0x33, 0x85, 0x45, 0xF9, 0x02, 0x7F, 0x50, 0x3C, 0x9F, 0xA8,
    0x51, 0xA3, 0x40, 0x8F, 0x92, 0x9D, 0x38, 0xF5, 0xBC, 0xB6, 0xDA, 0x21, 0x10, 0xFF, 0xF3, 0xD2,
    0xCD, 0x0C, 0x13, 0xEC, 0x5F, 0x97, 0x44, 0x17, 0xC4, 0xA7, 0x7E, 0x3D, 0x64, 0x5D, 0x19, 0x73,
    0x60, 0x81, 0x4F, 0xDC, 0x22, 0x2A, 0x90, 0x88, 0x46, 0xEE, 0xB8, 0x14, 0xDE, 0x5E, 0x0B, 0xDB,
    0xE0, 0x32, 0x3A, 0x0A, 0x49, 0x06, 0x24, 0x5C, 0xC2, 0xD3, 0xAC, 0x62, 0x91, 0x95, 0xE4, 0x79,
    0xE7, 0xC8, 0x37, 0x6D, 0x8D, 0xD5, 0x4E, 0xA9, 0x6C, 0x56, 0xF4, 0xEA, 0x65, 0x7A, 0xAE, 0x08,
    0xBA, 0x78, 0x25, 0x2E, 0x1C, 0xA6, 0xB4, 0xC6, 0xE8, 0xDD, 0x74, 0x1F, 0x4B, 0xBD, 0x8B, 0x8A,
    0x70, 0x3E, 0xB5, 0x66, 0x48, 0x03, 0xF6, 0x0E, 0x61, 0x35, 0x57, 0xB9, 0x86, 0xC1, 0x1D, 0x9E,
    0xE1, 0xF8, 0x98, 0x11, 0x69, 0xD9, 0x8E, 0x94, 0x9B, 0x1E, 0x87, 0xE9, 0xCE, 0x55, 0x28, 0xDF,
    0x8C, 0xA1, 0x89, 0x0D, 0xBF, 0xE6, 0x42, 0x68, 0x41, 0x99, 0x2D, 0x0F, 0xB0, 0x54, 0xBB, 0x16,
]

HW = [bin(x).count("1") for x in range(256)]


def align_traces(traces, ref_range=(0, 100)):
    """Align traces using cross-correlation on the burst region."""
    lo, hi = ref_range
    # Use median trace in burst region as reference
    # First pass: rough alignment using a single reference trace
    peak_positions = np.argmax(traces[:, lo:hi], axis=1)
    median_peak = int(np.median(peak_positions))
    ref_idx = np.where(peak_positions == median_peak)[0][0]
    ref = traces[ref_idx, lo:hi].astype(np.float64)
    
    n_traces, n_samples = traces.shape
    aligned = np.zeros((n_traces, n_samples), dtype=traces.dtype)
    shifts = np.zeros(n_traces, dtype=int)
    
    for i in range(n_traces):
        corr = np.correlate(traces[i, lo:hi].astype(np.float64), ref, mode='full')
        best_lag = np.argmax(corr) - (hi - lo - 1)
        shifts[i] = best_lag
        
        if best_lag > 0:
            if best_lag < n_samples:
                aligned[i, :-best_lag] = traces[i, best_lag:]
                aligned[i, -best_lag:] = traces[i, -1]
        elif best_lag < 0:
            if -best_lag < n_samples:
                aligned[i, -best_lag:] = traces[i, :best_lag]
                aligned[i, :-best_lag] = traces[i, 0]
        else:
            aligned[i] = traces[i]
    
    return aligned, shifts


def pearson_corr_vectorized(hypotheses, traces):
    """
    Compute Pearson correlation between hypotheses (n_traces,) and traces (n_traces, n_samples).
    Returns correlation for each sample point.
    """
    n = len(hypotheses)
    h = hypotheses.astype(np.float64)
    t = traces.astype(np.float64)
    
    h_mean = h.mean()
    t_mean = t.mean(axis=0)
    
    h_centered = h - h_mean
    t_centered = t - t_mean
    
    numerator = (h_centered[:, None] * t_centered).sum(axis=0)
    
    h_std = np.sqrt((h_centered ** 2).sum())
    t_std = np.sqrt((t_centered ** 2).sum(axis=0))
    
    denom = h_std * t_std
    denom[denom == 0] = 1  # avoid div by zero
    
    return numerator / denom


def cpa_attack(traces, plaintexts, sample_range=None):
    """
    Run CPA attack for all 16 key bytes.
    Returns the best key byte and correlation for each position.
    """
    n_traces, n_samples = traces.shape
    
    if sample_range is not None:
        traces = traces[:, sample_range[0]:sample_range[1]]
        n_samples = traces.shape[1]
    
    key = np.zeros(16, dtype=np.uint8)
    correlations = np.zeros(16)  # best correlation for each byte
    margins = np.zeros(16)  # margin between best and second best
    best_sample_positions = np.zeros(16, dtype=int)
    
    for byte_idx in range(16):
        best_corr = 0
        second_corr = 0
        best_key = 0
        best_sample = 0
        
        for k_guess in range(256):
            # Compute hypothetical Hamming weight
            hw = np.array([HW[SBOX[int(plaintexts[i, byte_idx]) ^ k_guess]] 
                          for i in range(n_traces)], dtype=np.float64)
            
            # Correlate with each time sample
            corr = pearson_corr_vectorized(hw, traces)
            max_corr = np.max(np.abs(corr))
            max_sample = np.argmax(np.abs(corr))
            
            if max_corr > best_corr:
                second_corr = best_corr
                best_corr = max_corr
                best_key = k_guess
                best_sample = max_sample
            elif max_corr > second_corr:
                second_corr = max_corr
        
        key[byte_idx] = best_key
        correlations[byte_idx] = best_corr
        margins[byte_idx] = best_corr - second_corr
        best_sample_positions[byte_idx] = best_sample
        
        print(f"Byte {byte_idx:2d}: key=0x{best_key:02x}  corr={best_corr:.4f}  "
              f"margin={best_corr - second_corr:.4f}  sample={best_sample}")
    
    return key, correlations, margins, best_sample_positions


def main():
    print("Loading data...")
    z = np.load("traces.npz")
    traces, plaintexts = z["traces"], z["plaintexts"]
    print(f"Traces: {traces.shape}, Plaintexts: {plaintexts.shape}")
    
    # Step 1: Align traces
    print("\nAligning traces...")
    aligned, shifts = align_traces(traces, ref_range=(0, 100))
    print(f"Shifts: min={shifts.min()}, max={shifts.max()}, std={shifts.std():.1f}")
    
    # Step 2: Run CPA on aligned traces, skip the burst region
    print("\n=== CPA on aligned traces (samples 100-800) ===")
    key, corrs, margins, positions = cpa_attack(aligned, plaintexts, sample_range=(100, 800))
    
    key_hex = ''.join(f'{b:02x}' for b in key)
    print(f"\nRecovered key: {key_hex}")
    print(f"Flag: Intern_Pro_Max{{{key_hex}}}")
    
    # Show confidence analysis
    print(f"\nConfidence analysis:")
    print(f"  Min margin: {margins.min():.4f} (byte {margins.argmin()})")
    print(f"  Mean margin: {margins.mean():.4f}")
    
    # Check for low-confidence bytes
    low_conf = np.where(margins < 0.005)[0]
    if len(low_conf) > 0:
        print(f"  WARNING: Low-confidence bytes: {low_conf}")
        print("  These bytes may be incorrect.")
    
    # Also run on raw traces for comparison
    print("\n=== CPA on RAW traces (samples 100-800) ===")
    key2, corrs2, margins2, positions2 = cpa_attack(traces, plaintexts, sample_range=(100, 800))
    key_hex2 = ''.join(f'{b:02x}' for b in key2)
    print(f"\nRecovered key (raw): {key_hex2}")
    
    # Compare
    match = (key == key2)
    print(f"\nBytes matching between aligned and raw: {match.sum()}/16")
    for i in range(16):
        status = "MATCH" if match[i] else "DIFFER"
        print(f"  Byte {i:2d}: aligned=0x{key[i]:02x}(m={margins[i]:.4f}) "
              f"raw=0x{key2[i]:02x}(m={margins2[i]:.4f}) {status}")


if __name__ == "__main__":
    main()
