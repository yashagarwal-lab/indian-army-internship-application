import numpy as np
import glob
import os

fs = 400000.0

def get_sym_rate(filepath):
    raw = np.fromfile(filepath, dtype=np.float32)
    x = raw[0::2] + 1j*raw[1::2]
    
    x2 = x**2
    F = np.fft.fft(x2)
    freqs = np.fft.fftfreq(len(x2), 1/fs)
    
    pos_idx = np.abs(freqs) > 1000
    peak_idx = np.argmax(np.abs(F[pos_idx]))
    fc2 = freqs[pos_idx][peak_idx]
    
    # look around fc2 + 5000
    search_idx = (np.abs(freqs - (fc2 + 5000)) < 200) | (np.abs(freqs - (fc2 - 5000)) < 200)
    
    # Actually, we can just look at np.abs(np.diff(np.abs(x)))
    mag = np.abs(x)
    F_mag = np.fft.fft(np.abs(np.diff(mag)))
    f_mag = np.fft.fftfreq(len(F_mag), 1/fs)
    sym_idx = (f_mag > 4900) & (f_mag < 5100)
    if not np.any(sym_idx): return 0
    peak_sym_idx = np.argmax(np.abs(F_mag[sym_idx]))
    sym_rate = np.abs(f_mag[sym_idx][peak_sym_idx])
    return sym_rate

print("Reference Radios:")
refs = sorted(glob.glob("reference/*.sigmf-data"))
for ref in refs:
    sym_rate = get_sym_rate(ref)
    name = os.path.basename(ref).split('.')[0]
    print(f"{name:12s}: sym_rate = {sym_rate:8.2f} Hz")

print("\nUnknown:")
unk_sym = get_sym_rate("unknown/unknown_transmission.sigmf-data")
print(f"Unknown     : sym_rate = {unk_sym:8.2f} Hz")
