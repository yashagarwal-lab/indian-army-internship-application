import numpy as np
import glob
import os

fs = 400000.0

def exact_features(filepath):
    raw = np.fromfile(filepath, dtype=np.float32)
    x = raw[0::2] + 1j*raw[1::2]
    
    # Accurate Power
    pwr = np.mean(np.abs(x)**2)
    pwr_db = 10 * np.log10(pwr)
    
    # Accurate fc
    # Square signal to get 2*fc peak
    x2 = x**2
    F = np.fft.fft(x2)
    freqs = np.fft.fftfreq(len(x2), 1/fs)
    
    # The true fc might be negative. Let's find the absolute maximum peak ignoring DC
    pos_idx = np.abs(freqs) > 1000
    peak_idx = np.argmax(np.abs(F[pos_idx]))
    fc2 = freqs[pos_idx][peak_idx]
    
    # But x^2 peak is at 2*fc. So fc = fc2 / 2
    fc = fc2 / 2.0
    
    # Exact symbol rate
    # BPSK squared doesn't necessarily have a symbol rate peak unless we use magnitude or something else.
    # Let's take the magnitude squared and look at its spectrum.
    # Since it's BPSK, transitions cause dips in magnitude if pulse shaped.
    mag = np.abs(x)
    F_mag = np.fft.fft(mag - np.mean(mag))
    f_mag = np.fft.fftfreq(len(mag), 1/fs)
    sym_idx = (f_mag > 4000) & (f_mag < 6000)
    peak_sym_idx = np.argmax(np.abs(F_mag[sym_idx]))
    sym_rate = np.abs(f_mag[sym_idx][peak_sym_idx])
    
    return fc, pwr_db, sym_rate

print("Reference Radios:")
refs = sorted(glob.glob("reference/*.sigmf-data"))
for ref in refs:
    fc, pwr, sym_rate = exact_features(ref)
    name = os.path.basename(ref).split('.')[0]
    print(f"{name:12s}: fc = {fc:8.1f} Hz, pwr = {pwr:6.2f} dB, sym_rate = {sym_rate:6.1f} Hz")

print("\nUnknown:")
unk_fc, unk_pwr, unk_sym = exact_features("unknown/unknown_transmission.sigmf-data")
print(f"Unknown     : fc = {unk_fc:8.1f} Hz, pwr = {unk_pwr:6.2f} dB, sym_rate = {unk_sym:6.1f} Hz")
