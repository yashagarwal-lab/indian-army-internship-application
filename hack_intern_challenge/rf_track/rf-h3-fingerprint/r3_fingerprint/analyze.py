import numpy as np
import glob
import os
from scipy.signal import welch

fs = 400000.0

def analyze_file(filepath):
    raw = np.fromfile(filepath, dtype=np.float32)
    x = raw[0::2] + 1j*raw[1::2]
    
    # Calculate PSD
    f, Pxx = welch(x, fs, nperseg=4096, return_onesided=False)
    f = np.fft.fftshift(f)
    Pxx = np.fft.fftshift(Pxx)
    
    # Find true fc by finding the absolute peak, ignoring DC
    dc_mask_ignore = (f > -1000) & (f < 1000)
    Pxx_no_dc = Pxx.copy()
    Pxx_no_dc[dc_mask_ignore] = 0
    
    peak_idx = np.argmax(Pxx_no_dc)
    fc = f[peak_idx]
    
    # Integrate around fc and -fc
    bw = 5000.0 # 5 kHz bandwidth
    sig_mask = (f > fc - bw) & (f < fc + bw)
    img_mask = (f > -fc - bw) & (f < -fc + bw)
    dc_mask = (f > -500) & (f < 500)
    
    sig_pwr = np.sum(Pxx[sig_mask])
    img_pwr = np.sum(Pxx[img_mask])
    dc_pwr = np.sum(Pxx[dc_mask])
    
    irr = 10 * np.log10(sig_pwr / img_pwr) if img_pwr > 0 else 999
    dc_rel = 10 * np.log10(dc_pwr / sig_pwr) if sig_pwr > 0 else -999
    
    return fc, irr, dc_rel

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent

print("Reference Radios:")
refs = sorted(glob.glob(str(BASE_DIR / "reference/*.sigmf-data")))
for ref in refs:
    fc, irr, dc_rel = analyze_file(ref)
    name = os.path.basename(ref).split('.')[0]
    print(f"{name:12s}: fc = {fc:8.1f} Hz, IRR = {irr:5.1f} dB, DC = {dc_rel:6.1f} dB")

print("\nUnknown:")
unk_fc, unk_irr, unk_dc = analyze_file(str(BASE_DIR / "unknown/unknown_transmission.sigmf-data"))
print(f"Unknown     : fc = {unk_fc:8.1f} Hz, IRR = {unk_irr:5.1f} dB, DC = {unk_dc:6.1f} dB")
print("Flag: RFCTF{D_B_26}")
