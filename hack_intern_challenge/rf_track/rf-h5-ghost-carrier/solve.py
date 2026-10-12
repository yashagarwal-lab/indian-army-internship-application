#!/usr/bin/env python3
"""
PARCHAM / Serial Dhwani - intercept GC-0914 : "Ghost Carrier" solver
=====================================================================

Input : ghost_carrier.sigmf-data  (ci16_le, 1 MS/s, 4 s)  + intercept_notes.txt facts
Output: RFCTF{...}

Pipeline
  Stage 1  FHSS packet network (16 ch, 2-FSK 25 kBd)
           channelise -> burst detect -> FM demod -> bit slice -> find frame start
           by brute force (sync word is not documented) -> de-whiten (per-channel
           seed) -> CRC-16/CCITT-FALSE -> reassemble 23 packets -> zlib -> manifest.
  Stage 2  "Ghost carrier": DSSS / DBPSK, GPS C/A codes, 125 kchip/s, buried in noise
           excise hop bursts (narrowband notch, NOT blanking) -> notch static
           interferers -> FFT code-phase/frequency acquisition over PRNs ->
           per-PRN tracking (code-phase drift + linear carrier chirp) ->
           despread one code period per bit -> differential decode ->
           F0C3 key frames (CRC-8/07) -> XOR shares = key.
  Final    flag = ct XOR SHAKE256(key)[:len(ct)], verified against the manifest SHA-256.

Usage
  python3 solve.py ghost_carrier.sigmf-data
  python3 solve.py ghost_carrier.sigmf-data --cache work      # resumable (recommended)
  python3 solve.py ghost_carrier.sigmf-data --prns 17 19 32   # skip the PRN search

Requires: numpy, scipy.  Runtime: ~6-8 min single core for the full PRN search
(~1.5 min if --prns is given).
"""
import argparse, hashlib, json, os, re, sys, time, zlib
import numpy as np
import scipy.fft as sf
from scipy import signal

FS = 1e6                       # sample rate (from .sigmf-meta)
N = 8184                       # samples per C/A code period at 8 samples/chip
NCH = 16                       # hop channels
CH_F0, CH_DF = -375e3, 49.95e3 # channel plan found in the spectrum (low -> high)
DEC = 5
log = lambda *a: print(*a, flush=True)

# ------------------------------------------------------------------ helpers
def load_iq(path):
    raw = np.fromfile(path, dtype="<i2")
    x = (raw[0::2] + 1j * raw[1::2]).astype(np.complex64)
    return x - x.mean()                       # remove DC offset

def whitening(channel, n):                    # from intercept_notes.txt
    state, out = 0x100 | channel, []
    for _ in range(n):
        byte = 0
        for b in range(8):
            byte |= (state & 1) << b
            fb = (state & 1) ^ ((state >> 5) & 1)
            state = (state >> 1) | (fb << 8)
        out.append(byte)
    return bytes(out)

def crc16_ccitt_false(data, init=0xFFFF):
    c = init
    for byte in data:
        c ^= byte << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
    return c

def crc8_07(data, init=0x00):
    c = init
    for b in data:
        c ^= b
        for _ in range(8):
            c = ((c << 1) ^ 0x07) & 0xFF if c & 0x80 else (c << 1) & 0xFF
    return c

def bits_to_bytes(bits):
    return bytes(int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits) - 7, 8))

# ------------------------------------------------------------------ stage 1
def stage1(x):
    centers = CH_F0 + np.arange(NCH) * CH_DF
    lp = signal.firwin(161, 16e3, fs=FS)
    n_all = np.arange(len(x))
    bursts = []
    log("[stage1] channelising + burst detection")
    for k, fc in enumerate(centers):
        y = signal.lfilter(lp, 1, x * np.exp(-2j * np.pi * fc * n_all / FS))[::DEC]
        am = signal.lfilter(np.ones(8) / 8, 1, np.abs(y))
        thr = max(np.median(am) * 3, 1000)
        on = (am > thr).astype(int)
        rise = np.where(np.diff(on) == 1)[0]
        fall = np.where(np.diff(on) == -1)[0]
        for r in rise:
            f = fall[fall > r]
            if len(f) and f[0] - r >= 200:              # >= 1 ms
                bursts.append((k, int(r), int(f[0])))
    log(f"[stage1] {len(bursts)} burst segments")

    def demod_bits(k, s, e):
        fc = centers[k]
        lo, hi = max(s * DEC - 2000, 0), min(e * DEC + 2000, len(x))
        n = np.arange(lo, hi)
        y = signal.lfilter(lp, 1, x[lo:hi] * np.exp(-2j * np.pi * fc * n / FS))[::DEC]
        on = np.where(signal.lfilter(np.ones(8) / 8, 1, np.abs(y)) > 1000)[0]
        st, en = on[0], on[-1]
        d = np.angle(y[1:] * np.conj(y[:-1])) * (FS / DEC) / (2 * np.pi)   # Hz
        d = signal.lfilter(np.ones(3) / 3, 1, d)
        seg = d[st + 8:en - 8]
        dd = seg - (np.percentile(seg, 15) + np.percentile(seg, 85)) / 2    # remove CFO
        sps, best = 8.0, None                                               # 25 kBd @ 200 kS/s
        for p in np.arange(0, sps, 0.25):                                   # symbol timing
            idx = np.round(p + np.arange(int((len(dd) - p) / sps)) * sps).astype(int)
            idx = idx[idx < len(dd)]
            m = np.abs(dd[idx]).mean()
            if best is None or m > best[0]:
                best = (m, idx)
        return (dd[best[1]] > 0).astype(int)

    def try_frame(bits, k, off):
        data = bits_to_bytes(bits[off:])
        wh = whitening(k, len(data))
        dw = bytes(a ^ b for a, b in zip(data, wh))
        if len(dw) < 5:
            return None
        seq, total, ln = dw[0], dw[1], dw[2]
        if ln > 100 or 3 + ln + 2 > len(dw):
            return None
        if crc16_ccitt_false(dw[:3 + ln]) == (dw[3 + ln] << 8 | dw[4 + ln]):
            return seq, total, dw[3:3 + ln]
        return None

    packets, offs = {}, {}
    for k, s, e in sorted(bursts, key=lambda t: t[1]):
        if (e - s) / 200.0 < 9.4:          # fragments cannot hold a full frame
            continue
        bits = demod_bits(k, s, e)
        for off in range(56, 80):          # sync word unknown -> brute-force frame start
            r = try_frame(bits, k, off)
            if r:
                packets.setdefault(r[0], r[2]); offs[off] = offs.get(off, 0) + 1
                break
    log(f"[stage1] CRC-valid packets: {sorted(packets)}   frame-start offsets {offs}")
    # reassemble the longest contiguous prefix and inflate (partial OK)
    blob = b""
    i = 0
    while i in packets:
        blob += packets[i]; i += 1
    manifest = zlib.decompressobj().decompress(blob).decode("latin1")
    return bursts, manifest

# ------------------------------------------------------------------ stage 2
def excise_hops(x, bursts):
    """Remove the narrowband FSK hop bursts but keep the wideband DSSS underneath."""
    centers = CH_F0 + np.arange(NCH) * CH_DF
    ev = {}
    for k, rs, fe in bursts:
        ev.setdefault(k, []).append((rs * DEC, fe * DEC))
    segs = []
    for k, l in ev.items():
        l.sort(); cur = list(l[0])
        for s, e in l[1:]:
            if s - cur[1] < 15000: cur[1] = max(cur[1], e)
            else: segs.append((k, *cur)); cur = [s, e]
        segs.append((k, *cur))
    xc = x.astype(np.complex128).copy()
    for k, s, e in segs:
        lo, hi = max(s - 1500, 0), min(e + 1500, len(x)); L = hi - lo
        F = sf.fft(x[lo:hi] * signal.windows.tukey(L, 0.15))
        m = np.abs(sf.fftfreq(L, 1 / FS) - centers[k]) < 18e3
        xc[lo:hi] -= sf.ifft(np.where(m, F, 0))
    return xc.astype(np.complex64)

def static_notch_mask(xc):
    """Auto-detect persistent narrowband interferers (the +-455 kHz lines, DC spur)."""
    nb = len(xc) // N
    P = np.zeros(N)
    for b in range(0, nb, 4):
        P += np.abs(sf.fft(xc[b * N:(b + 1) * N])) ** 2
    ref = signal.medfilt(P, 2001)
    hit = P > 8 * ref
    hit = np.convolve(hit.astype(float), np.ones(401), "same") > 0       # +-~25 kHz
    fr = sf.fftfreq(N, 1 / FS)
    hit |= np.abs(fr) < 3e3
    return hit

def code_vec(prn):
    taps = {1:(2,6),2:(3,7),3:(4,8),4:(5,9),5:(1,9),6:(2,10),7:(1,8),8:(2,9),9:(3,10),10:(2,3),
            11:(3,4),12:(5,6),13:(6,7),14:(7,8),15:(8,9),16:(9,10),17:(1,4),18:(2,5),19:(3,6),
            20:(4,7),21:(5,8),22:(6,9),23:(1,3),24:(4,6),25:(5,7),26:(6,8),27:(7,9),28:(8,10),
            29:(1,6),30:(2,7),31:(3,8),32:(4,9),33:(1,4),34:(2,5),35:(3,6),36:(4,7),37:(5,8)}[prn]
    g1, g2, out = [1] * 10, [1] * 10, []
    for _ in range(1023):
        out.append(g1[9] ^ g2[taps[0] - 1] ^ g2[taps[1] - 1])
        f1 = g1[2] ^ g1[9]; f2 = g2[1] ^ g2[2] ^ g2[5] ^ g2[7] ^ g2[8] ^ g2[9]
        g1 = [f1] + g1[:9]; g2 = [f2] + g2[:9]
    return np.array(out, np.float32) * 2 - 1           # +-1 chips, length 1023

def acquire(xc, notch, prn, b0=150, nblk=4):
    """Parallel code-phase search at every 122 Hz carrier bin (+-489 kHz), non-coherent."""
    C = np.conj(sf.fft(np.repeat(code_vec(prn), 8).astype(np.complex64)))
    SH, k = np.arange(-4000, 4000), np.arange(N)
    acc = np.zeros((len(SH), N), np.float32)
    for b in range(b0, b0 + nblk):
        S = sf.fft(xc[b * N:(b + 1) * N]); S[notch] = 0
        for i0 in range(0, len(SH), 400):
            sh = SH[i0:i0 + 400]
            y = sf.ifft(S[(k[None, :] + sh[:, None]) % N] * C[None, :], axis=1)
            acc[i0:i0 + 400] += y.real ** 2 + y.imag ** 2
    i, j = np.unravel_index(acc.argmax(), acc.shape)
    return float(acc.max() / acc.mean()), float(SH[i] * FS / N), int(j)

def track(xc, prn, f0, b0):
    """Follow code phase (drifts: uncalibrated chip clock) and carrier (linear chirp)."""
    rep = np.repeat(code_vec(prn), 8).astype(np.complex64)
    C = np.conj(sf.fft(rep)); NB = len(xc) // N
    pts = {}
    def step(b, fpred):
        n0 = b * N
        mix = xc[n0:n0 + N] * np.exp(-2j * np.pi * fpred * np.arange(N) / FS).astype(np.complex64)
        y = np.abs(sf.ifft(sf.fft(mix) * C)) ** 2
        k = int(y.argmax()); snr = y[k] / y.mean()
        a = n0 + k                                           # period-aligned segment
        if a + N > len(xc): return None
        n = np.arange(a, a + N)
        z = xc[a:a + N] * rep * np.exp(-2j * np.pi * fpred * (n - a) / FS)
        q = z[:N // 8 * 8].reshape(8, -1).sum(1)             # 8 sub-sums: no bit edge inside
        df = np.angle(np.sum(q[1:] * np.conj(q[:-1]))) / (2 * np.pi * (N / 8) / FS)
        return k, snr, fpred + df, (a + N / 2) / FS
    def run(blocks, seed):
        hist = list(seed)
        for b in blocks:
            h = np.array(hist[-30:])
            if len(h) >= 3 and np.ptp(h[:, 0]) > 0:
                p = np.polyfit(h[:, 0], h[:, 1], 1)
                fpred = np.polyval(p, (b + 0.5) * N / FS)
            else:
                fpred = hist[-1][1]
            r = step(b, fpred)
            if r and r[1] > 12:
                pts[b] = r; hist.append((r[3], r[2]))
    k0 = step(b0, f0)
    hist0 = [(k0[3], k0[2])]
    run(range(b0 + 1, NB - 1), hist0)
    run(range(b0 - 1, -1, -1), hist0)
    bs = np.array(sorted(pts)); ks = np.array([pts[b][0] for b in bs], float)
    ts = np.array([pts[b][3] for b in bs]); fs_ = np.array([pts[b][2] for b in bs])
    # robust straight-line fits
    ref = np.median(ks); kk = ((ks - ref + N / 2) % N) - N / 2 + ref
    m = np.abs(kk - ref) < N / 4
    A = np.polyfit(bs[m], kk[m], 1)
    for _ in range(3):
        m = np.abs(kk - np.polyval(A, bs)) < 3; A = np.polyfit(bs[m], kk[m], 1)
    p = np.polyfit(ts, fs_, 1)
    for _ in range(3):
        m = np.abs(fs_ - np.polyval(p, ts)) < 25; p = np.polyfit(ts[m], fs_[m], 1)
    log(f"    track: {len(bs)}/{NB} blocks, code drift {A[0]:+.3f} smp/blk, chirp {p[0]:+.1f} Hz/s, f(0)={p[1]:.1f} Hz")
    return A, p[1], p[0]

def demod_dbpsk(xc, prn, A, fa, r):
    code = code_vec(prn); P = N + A[0]
    rows = []; j = 0
    while True:
        t = A[1] + j * P; j += 1
        if t < 0: continue
        n0 = int(np.ceil(t)); n1 = n0 + int(P)
        if n1 >= len(xc): break
        n = np.arange(n0, n1)
        ci = np.floor((n - t) * 1023 / P).astype(int) % 1023     # fractional chip alignment
        rows.append((xc[n0:n1] * code[ci], n / FS))
    prod = np.array([a for a, _ in rows]); tm = np.array([b for _, b in rows])
    def corr(fa_, r_):
        return (prod * np.exp(-2j * np.pi * (fa_ * tm + 0.5 * r_ * tm * tm))).sum(1)
    def coh(c):
        z = c[1:] * np.conj(c[:-1]); return abs(np.sum(z ** 2)) / np.sum(np.abs(z) ** 2)
    best = (coh(corr(fa, r)), fa, r)
    for it in range(3):                                  # refine on DBPSK coherence
        for dfa in np.arange(-20, 21, 4) * 0.5 ** it:
            for dr in np.arange(-2, 2.1, 0.5) * 0.5 ** it:
                m = coh(corr(best[1] + dfa, best[2] + dr))
                if m > best[0]: best = (m, best[1] + dfa, best[2] + dr)
    c = corr(best[1], best[2]); z = c[1:] * np.conj(c[:-1])
    log(f"    DBPSK coherence {best[0]:.3f}  ({len(c)} bits)")
    return (z.real < 0).astype(int)

def find_key_frames(bits):
    out = []
    for bb in (bits, 1 - bits):
        s = "".join(map(str, bb)); i = s.find("1111000011000011")
        while i != -1:
            d = bits_to_bytes(bb[i:])
            if len(d) >= 6 and d[4] <= 64 and 6 + d[4] <= len(d):
                idx, total, ln = d[2], d[3], d[4]
                if crc8_07(d[2:5 + ln]) == d[5 + ln]:
                    out.append((idx, total, d[5:5 + ln]))
            i = s.find("1111000011000011", i + 1)
    return out

# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data"); ap.add_argument("--cache", default=None)
    ap.add_argument("--prns", type=int, nargs="*", default=None, help="skip search, try only these")
    ap.add_argument("--thr", type=float, default=18.0, help="acquisition peak/mean threshold")
    a = ap.parse_args()
    cdir = a.cache
    if cdir: os.makedirs(cdir, exist_ok=True)
    cp = lambda f: os.path.join(cdir, f) if cdir else None
    t0 = time.time()
    x = load_iq(a.data); log(f"loaded {len(x)} samples ({len(x)/FS:.1f} s)")

    # ---- stage 1 (cached)
    if cdir and os.path.exists(cp("stage1.json")):
        j = json.load(open(cp("stage1.json"))); bursts, manifest = [tuple(b) for b in j["bursts"]], j["manifest"]
        log("[stage1] loaded from cache")
    else:
        bursts, manifest = stage1(x)
        if cdir: json.dump({"bursts": bursts, "manifest": manifest}, open(cp("stage1.json"), "w"))
    print("\n----- recovered manifest (stage 1) -----\n" + manifest + "\n-----------------------------------------\n")
    ct = bytes.fromhex(re.search(r"ct:\s*([0-9a-fA-F]+)", manifest).group(1))
    m = re.search(r"sha256\(flag\):\s*([0-9a-fA-F]+)", manifest); want = m.group(1).lower() if m else ""

    # ---- stage 2
    if cdir and os.path.exists(cp("xc.npy")):
        xc = np.load(cp("xc.npy"))
    else:
        log("[stage2] excising hop bursts"); xc = excise_hops(x, bursts)
        if cdir: np.save(cp("xc.npy"), xc)
    notch = static_notch_mask(xc); log(f"[stage2] static interference bins notched: {notch.sum()}")

    shares, total = {}, None
    cand = a.prns if a.prns else list(range(1, 38))
    for prn in cand:
        if total and len(shares) >= total: break
        f = cp(f"acq_{prn}.json")
        if a.prns:                                   # user-supplied PRN: always evaluate
            ratio, f0, ph = acquire(xc, notch, prn)
        elif f and os.path.exists(f):
            ratio, f0, ph = json.load(open(f))
        else:
            ratio, f0, ph = acquire(xc, notch, prn)
            if f: json.dump([ratio, f0, ph], open(f, "w"))
        log(f"[acq] PRN {prn:2d}  peak/mean {ratio:6.1f}  f={f0:10.1f} Hz")
        if ratio < a.thr: continue
        log(f"  >> PRN {prn} present - tracking")
        A, fa, r = track(xc, prn, f0, 150)
        bits = demod_dbpsk(xc, prn, A, fa, r)
        for idx, tot, sh in find_key_frames(bits):
            log(f"    key frame: idx={idx} total={tot} share={sh.hex()}")
            shares[idx] = sh; total = tot
    if not total or len(shares) < total:
        sys.exit(f"incomplete shares {sorted(shares)} / {total}")

    key = bytearray(len(shares[0]))
    for sh in shares.values():
        key = bytearray(p ^ q for p, q in zip(key, sh))
    key = bytes(key); log(f"\nkey = {key.hex()}")
    flag = bytes(c ^ k for c, k in zip(ct, hashlib.shake_256(key).digest(len(ct))))
    h = hashlib.sha256(flag).hexdigest()
    ok = h.startswith(want) if want else None
    log(f"sha256(flag) = {h}\nmatches manifest: {ok}")
    print("\nFLAG:", flag.decode()); log(f"(total time {time.time()-t0:.0f} s)")

if __name__ == "__main__":
    main()
