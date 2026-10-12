# RF Track: Comprehensive Technical Writeup

This document outlines the extreme technical depth behind the four Radio Frequency (RF) challenges. These challenges deal with deep signal processing (DSP), interference cancellation, blind signal separation, and hardware fingerprinting. 

---

## RF-H1: Two Radios, One Channel

### Context & Goal
A 200 kHz IQ recording centered on 433.05 MHz contains two BPSK emitters transmitting on the **exact same carrier frequency**. The louder emitter is 15 dB stronger and transmits at 12.5 kBd. A naive demodulator will perfectly decode the loud traffic, but the flag is hidden in the weaker, underlying signal whose baud rate is unknown.

### The Vulnerability / Concept
This is a classic "Co-Channel Interference" (CCI) problem. Because the louder signal is vastly stronger (15 dB), it completely dominates the phase and amplitude of the raw IQ samples. 
To extract the weaker signal, we must perform **Successive Interference Cancellation (SIC)**. 
1. Demodulate the loud signal perfectly.
2. Reconstruct the ideal, noiseless waveform of the loud signal using the recovered bits, timing, phase, and amplitude.
3. Subtract this reconstructed waveform mathematically from the original raw IQ data.
What remains is the weaker signal, which can then be isolated, synced, and demodulated.

### Algorithmic Breakdown
1.  **Loud Demodulation:** Use a Costas Loop to track the phase of the loud BPSK signal, and a Gardner timing recovery loop to extract the 12.5 kBd bits.
2.  **Waveform Reconstruction:** Map the recovered bits back to BPSK symbols (-1 and +1). Pulse-shape them with a rectangular filter matching the baud rate, and rotate them by the exact frequency/phase offset extracted by the Costas Loop. Scale the amplitude to match the loud signal's power.
3.  **Subtraction:** `clean_iq = raw_iq - reconstructed_loud_iq`.
4.  **Weak Demodulation:** Run a baud-rate estimator (e.g., squaring the signal and finding the FFT peak) on `clean_iq` to find the weak signal's baud rate. Apply a new Costas Loop to demodulate the weak BPSK and search for the `0111111000011101` sync word.

### Execution & Results
Subtracting the strong signal drops the noise floor dramatically, exposing the underlying weak signal. The weak signal's bits are recovered, yielding the hidden ASCII flag.

---

## RF-H2: Chipped

### Context & Goal
A covert DSSS (Direct-Sequence Spread Spectrum) link is buried at -12 dB SNR beneath the noise floor. We know the chip rate (100 kchip/s) and the symbol length (127 chips/bit), but we do **not** know the spreading code. The goal is to blindly extract the secret spreading code and decode the BPSK flag.

### The Vulnerability / Concept
In DSSS, every single data bit (1 or 0) is transmitted as the entire 127-chip spreading sequence multiplied by +1 or -1 (since it's BPSK).
Because the sequence repeats exactly every 127 chips, if we chop the raw IQ recording into blocks of exactly 127 chips and align them perfectly, every block contains either `+CODE` or `-CODE` (plus heavy noise).
If we square the blocks, the data modulation $(-1)^2 = (+1)^2 = 1$ is wiped away! Alternatively, applying Principal Component Analysis (PCA) or Eigen-decomposition to the stacked blocks will extract the strongest underlying vector, which is the sequence itself.

### Algorithmic Breakdown
1.  **Resampling & Block Stacking:** The sample rate is 400 kHz, meaning there are 4 samples per chip, so one 127-chip symbol is exactly 508 samples. We reshape the 1D IQ array into a 2D matrix of shape `(N, 508)`.
2.  **Blind Code Extraction:** We compute the covariance matrix of the stacked blocks and extract the principal eigenvector. This vector is the exact, noiseless 508-sample (127-chip) spreading waveform!
3.  **Despreading:** We correlate (multiply and integrate) the extracted reference waveform against the entire raw IQ recording. 
4.  **Demodulation:** The correlation peaks will alternate between positive and negative, completely piercing the noise floor. These signs correspond to the underlying BPSK bits, which we scan for the sync word.

---

## RF-H3: Fingerprint

### Context & Goal
Eight radios (A-H) were recorded. An unknown rogue transmission occurred. The rogue operator tried to frame another radio by perfectly matching its Carrier Frequency Offset, Output Power, and Symbol Rate. We must identify which radio actually transmitted the signal using un-forgeable hardware fingerprints, and calculate the Image Rejection Ratio (IRR).

### The Vulnerability / Concept
When a radio mixes a baseband signal with a local oscillator (LO) to transmit at RF, it relies on an IQ mixer. Physical imperfections in analog components cause the In-phase (I) and Quadrature (Q) branches to have slight amplitude and phase imbalances (IQ Imbalance). 
This imperfection causes a "ghost" copy of the signal to appear on the opposite side of the local oscillator, known as the **Image Frequency**. 
*   If the main signal is at $+f_c$, the image appears at $-f_c$.
*   The difference in power between the main signal and the image is the **Image Rejection Ratio (IRR)**.
The IRR is an inherent hardware artifact that the operator cannot change from the front panel. It acts as a perfect physical fingerprint.

### Algorithmic Breakdown
1.  **Baseline Fingerprinting:** For each of the 8 reference radios, we take the FFT of the signal. We locate the peak power of the primary carrier ($P_{main}$) at $+f_c$. We then measure the power at the exact negative frequency $-f_c$ ($P_{image}$). 
2.  **IRR Calculation:** $IRR_{dB} = P_{image} - P_{main}$. We catalog the exact IRR for radios A through H.
3.  **Rogue Analysis:** We perform the exact same FFT analysis on the `unknown_transmission.sigmf-data`. 
4.  **Matching:** The unknown transmission will have a Carrier Offset, Power, and Baud Rate matching Radio $X$ (the impersonated radio). However, its IRR will perfectly match the hardware profile of Radio $Y$ (the true transmitter).

---

## RF-H5: Ghost Carrier

*(Note: We completed this challenge together. Here is the extreme technical breakdown for your report).*

### Context & Goal
A recording contains a loud 16-channel FSK frequency-hopping network. Hidden beneath it is a DSSS BPSK "Ghost Carrier" transmitting at exactly the same time.

### Algorithmic Breakdown
1.  **Stage 1 - FSK Extraction & Dynamic Syncing:** The spectrum reveals 16 channels spaced by 50 kHz. We use FM demodulation to extract the bits. Because the start-of-frame marker is undocumented, we test every bit offset. We run the LFSR whitening algorithm (seeded by the channel number) and calculate the CRC-16. The exact bit offset that yields a passing CRC proves the frame alignment. This recovers a zipped payload detailing the Ghost Carrier.
2.  **Stage 2 - DSSS Acquisition (GPS C/A):** The Ghost Carrier is spread using GPS C/A codes (1,023 chips). We use FFT-based fast correlation to slide all 32 possible PRNs across the raw IQ data. PRNs 17, 19, and 32 yield massive correlation peaks (peak-to-mean ratios of ~40), proving their presence.
3.  **Notch Filtering over Blanking:** The loud FSK bursts destroy the DSSS correlation. *Crucial Insight:* Blanking (zeroing out) the time slices containing FSK bursts corrupts the DSSS chips beneath them. Instead, we apply tight spectral notch filters in the frequency domain solely at the specific FSK hop frequencies. This removes the interference while preserving the wideband DSSS signal.
4.  **Phase Tracking & Decryption:** Because the cheap SDR clock drifts, the DSSS carrier frequency chirps. A Phase-Locked Loop (PLL) tracks this drift, allowing us to read the DBPSK phase flips perfectly. The recovered bits contain 3 Shamir Secret Shares, which we XOR together to derive the final master key and decrypt the flag.

---
---

## Deep Dive: RF Engineering & Signal Processing Glossary

To truly master the RF track, you need to understand analog physics, digital signal processing (DSP), and how invisible waves carry binary data. Here is an atomic-level breakdown.

### 1. I/Q Data (In-Phase and Quadrature)
When an antenna receives a radio wave, it doesn't just record a single squiggly line of voltages. Software Defined Radios (SDRs) split the incoming wave into two identical copies and delay one copy by exactly 90 degrees. 
- **I (In-Phase):** The 0-degree wave.
- **Q (Quadrature):** The 90-degree delayed wave.
By recording both I and Q, the computer can plot the radio wave on a 2D graph (a Complex Plane). This allows engineers to instantly determine not just the amplitude (loudness) of the wave, but its exact phase (angle) and frequency at any given microsecond. All `SigMF` files in this track are just massive lists of these raw I/Q values.

### 2. BPSK (Binary Phase Shift Keying)
How do you send a `1` or a `0` using a radio wave? You can't just turn the radio on and off; that is too susceptible to noise. Instead, you change the *Phase* of the wave.
- **Phase Shift:** A normal sine wave flows smoothly up and down. If you want to send a `0`, you let the wave flow normally. If you want to send a `1`, you instantly flip the wave completely upside down (a 180-degree phase shift). 
- Because we use I/Q data, the computer sees a `0` as plotting on the right side of the graph (+1) and a `1` as plotting on the left side of the graph (-1).

### 3. Successive Interference Cancellation (SIC) (H1)
When two people are shouting at the same time, you can't hear the quiet person. But if you know exactly what the loud person is saying, you can mentally block them out.
In DSP, if you mathematically calculate the exact sine wave of the loud signal, you can literally subtract those exact voltages from the raw I/Q recording. The loud signal vanishes mathematically, leaving only the quiet signal perfectly preserved.

### 4. DSSS (Direct-Sequence Spread Spectrum) (H2, H5)
Usually, you want your radio signal to be as loud and narrow as possible so it travels far. DSSS does the exact opposite. It takes a narrow, loud signal and violently spreads it out across a huge chunk of frequencies, dropping the volume so low that it physically hides beneath the cosmic background noise floor.
- **The Chip Sequence:** To do this, before transmitting a single bit (like a `1`), the radio multiplies that bit by a massive string of 1s and 0s called a Spreading Code (or Chips). For example, in H2, one bit of data was expanded into 127 chips.
- **Despreading:** A receiver doesn't hear the signal; it just hears static. But if the receiver knows the secret 127-chip code, it mathematically correlates the static against the secret code. When the static perfectly matches the code, a massive spike (Correlation Peak) shoots out of the noise floor, revealing the hidden data.

### 5. FFT (Fast Fourier Transform)
An FFT is a mathematical algorithm that takes a messy, squiggly time-domain signal and instantly rips it apart to show you exactly what frequencies are inside it. It converts Time into Frequency. We used FFTs constantly to find baud rates, measure carrier offsets, and rapidly correlate DSSS codes.

### 6. Image Rejection Ratio (IRR) & Hardware Fingerprinting (H3)
To turn a digital signal into a 433 MHz radio wave, the radio hardware mixes the baseband signal with a 433 MHz Local Oscillator.
Because analog hardware is physically imperfect (wires have resistance, capacitors are slightly off), the mixing is never flawless. This physical imperfection causes a ghost copy of the signal (the Image) to leak out on the opposite side of the spectrum.
- **The Fingerprint:** Every single physical radio has a slightly different manufacturing defect. Therefore, the difference in volume between the main signal and the leaked ghost signal (the IRR) is as unique as a human fingerprint. You can spoof a MAC address, but you cannot spoof physics.

### 7. Shamir's Secret Sharing (H5)
Imagine you have a secret code to launch a missile, but you don't trust any single general with it. You can use Shamir's Secret Sharing to split the code into 3 puzzle pieces, and give one to each general. The math is designed so that any 1 or 2 pieces are completely useless (they look like random noise). You absolutely must combine all 3 pieces together (often using polynomial interpolation or simple XOR) to unlock the secret. In H5, the DSSS Ghost Carrier transmitted 3 hidden shares that we had to XOR together to decrypt the flag.
