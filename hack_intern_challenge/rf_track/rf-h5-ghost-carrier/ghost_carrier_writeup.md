# Ghost Carrier - RF CTF Writeup

## Challenge Overview
**Challenge:** Exercise PARCHAM · Serial Dhwani · intercept GC-0914
**Band:** 915 MHz ISM
**Objective:** Recover the flag hidden inside an RF recording containing two radio links.

The recording holds two distinct radio links, and recovering the final flag requires fully decoding both. Think of it as a radio recording with two conversations: one loud conversation that anyone can hear, and a second, hidden conversation buried underneath the noise floor.

---

## Stage 1: The Loud Conversation (Frequency Hopping Network)

### 1. Spotting the Signal
The first link is a frequency-hopping network. Picture a crowded room where people are shouting in short bursts, jumping to a different "channel" (a slightly different pitch) every time. By plotting the spectral energy against frequency, we can clearly see **16 evenly spaced channels** (50 kHz spacing) across the 1 MHz bandwidth. 

### 2. Turning Sound into Bits
The radios encode `0`s and `1`s by switching between two nearby pitches (±20 kHz deviation). This modulation scheme is **2-FSK** at a data rate of 8000 baud. To extract the bits, we tuned to each of the 16 channels, measured whether the pitch was above or below the center frequency, and read off the resulting bitstream.

Each burst begins with a preamble (`101010...`), which acts like a steady drumbeat, allowing us to synchronize our timing and learn the rhythm before the actual message begins.

### 3. Finding the Message Start and Whitening
The challenge notes did not explicitly define the "start of frame" marker, so we had to dynamically search for it. We tested every possible starting position in the bitstream.

For each candidate position, we reversed the data scrambling (whitening). The radios scramble the bits to prevent long runs of identical ones or zeros. The whitening recipe was provided, and the PRNG is seeded based on the specific channel the burst arrived on. 

After unwhitening, we ran the **CRC-16/CCITT-FALSE** checksum. Since the checksum acts as an exact validation, only the correct starting position resulted in a passing CRC.

### 4. Stage 1 Result
By extracting all the numbered packets that passed the CRC check and gluing them together in order, we recovered a compressed text file. This file contained:
1. The encrypted flag.
2. A note describing the existence of a hidden second conversation.
3. The revelation that the decryption key was split into three pieces and transmitted inside that hidden signal.

---

## Stage 2: The Hidden Conversation (Ghost Carrier)

### 1. The DSSS Signal
The second conversation is the true "Ghost Carrier." This signal uses **Direct Sequence Spread Spectrum (DSSS)**. Imagine someone whispering a message but smearing it across a huge range of pitches at once, so quietly that at every individual pitch it is weaker than the background hiss. It is literally below the noise floor, which is why standard spectrograms looked empty.

### 2. De-spreading with GPS C/A Codes
Each transmitter spreads its signal using a secret pattern of 1,023 chips (a GPS C/A code). If you know the exact pattern, you can multiply the recording by it and integrate. The hidden message adds up coherently and pops out, while the random noise cancels out.

However, three parameters were unknown:
- Which of the 32 possible PRN patterns was used.
- The exact time alignment of the sequence.
- The exact carrier frequency (since the cheap SDR has an LO offset).

Using FFT-based fast correlation, we tested all possible combinations. **Three patterns lit up far above the noise: PRN 17, 19, and 32.** While incorrect guesses had a peak-to-mean ratio of around 7, the correct patterns peaked around 40!

### 3. Cleaning the Spectrum
Before extracting the bits, two major sources of interference had to be addressed:
1. Two loud, steady tones near the edges of the band were notched out.
2. The Stage 1 hopping bursts caused severe interference. Instead of blanking out the entire time slice (which would erase the hidden signal and corrupt bits), we applied narrow notch filters to remove only the specific hopping pitch, leaving the wideband hidden signal intact.

### 4. Tracking and Demodulation
Because the cheap radio's clock and pitch were unsteady, the signal's pitch drifted steadily (chirped) and its timing drifted. We implemented a tracking loop to follow the signal's drift.

Each repetition of the 1,023-chip pattern carries exactly one data bit. The modulation is **DBPSK** (Differential BPSK), meaning a `1` or `0` is encoded as a phase flip relative to the previous repetition. By measuring these phase differences, we recovered a clean bitstream.

### 5. Recovering the Secret Shares
Each recovered bitstream contained a message starting with the frame sync marker `F0C3`, followed by an index, the key piece (share), and a CRC8 checksum.
- `idx=0` total=3 share=`d543865df58cc0b3154bbe2145093a4c8392aa9e0a7219c5`
- `idx=1` total=3 share=`b452b63916c644e019c61a0fa4e832c9a08a4fbc8234b304`
- `idx=2` total=3 share=`5e2a2ddf4dab2a9cc694374f999582d73f468baf2d52203f`

All three checksums passed perfectly.

---

## The Finish

The instructional note from Stage 1 revealed that the master decryption key was the three pieces XORed together (a form of secret sharing where any missing piece leaves you with random junk). 

By XORing the three shares together, we recovered the 192-bit master key:
`key = 3f3b1dbbaee1aecfca19936178748a521c5e6e8da5148afe`

Using this key to unlock the encrypted flag payload from Stage 1, and verifying it against the provided SHA-256 fingerprint, we successfully recovered the flag:

**`FLAG: RFCTF{ph4nt0m_sp3ctrum_b3n34th_th3_fl00r_0f_n01s3}`**
