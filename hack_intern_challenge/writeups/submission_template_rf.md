# RF Track Write-up

## RF-H1: Two Radios, One Channel

### 1. What I tried first, and why it did not work
My first thought was to open the IQ recording in a spectrum analyzer and apply a frequency filter to isolate the weak signal. I quickly realized this wouldn't work because both the loud signal and the hidden weak signal were transmitting on the exact same frequency bandwidth. Any filter I applied to kill the loud signal would also completely destroy the weak signal I was trying to read.

### 2. The insight that actually cracked it
I realized I had to use Successive Interference Cancellation (SIC) to mathematically subtract the loud signal. I first demodulated the loud BPSK signal to get its exact bits and timing. I then generated a perfect, noiseless mathematical reconstruction of that loud waveform. Because I was working with raw I/Q data, I simply subtracted my reconstructed waveform from the original recording. The loud signal vanished, dropping the noise floor and perfectly exposing the hidden BPSK signal underneath.

### 3. How I satisfied myself the answer was right
Before the subtraction, the weak signal was completely invisible—just a block of static. After the subtraction, the constellation diagram for the weak signal resolved into two perfect, tight dots (+1 and -1), which is the exact mathematical signature of a clean BPSK signal. Running a standard demodulator on it yielded a perfectly readable ASCII flag.

### 4. Where I used an AI assistant and what I had to correct
I had never heard of Successive Interference Cancellation before. I asked an AI how to separate two signals on the same frequency, and it explained the concept of mathematically subtracting the loud waveform. I understood the idea, but aligning the phase of the reconstructed signal perfectly with the original recording in Python was tricky. The AI helped me write a fine-sync function to align the arrays before doing the subtraction.

---

## RF-H2: Chipped

### 1. What I tried first, and why it did not work
I knew running a standard BPSK demodulator directly on the recording would fail instantly. The signal was a Direct-Sequence Spread Spectrum (DSSS) transmission buried completely beneath the noise floor. Without knowing the secret spreading code, a standard demodulator would just spit out random static.

### 2. The insight that actually cracked it
I knew the symbol length was exactly 127 chips, which meant the secret spreading code repeated exactly every 127 chips. I realized I could blindly extract this code using linear algebra. I chopped the entire recording into blocks of 127 chips and stacked them into a giant matrix. By squaring the blocks (which wipes away the +1/-1 data modulation), the only thing left was the repeating structure of the chips. I ran Principal Component Analysis (PCA) on this matrix, and the strongest principal component that popped out was the exact secret spreading code!

### 3. How I satisfied myself the answer was right
When I cross-correlated the spreading code my PCA script found against the raw recording, massive correlation spikes shot out of the noise floor. In DSP, you do not get massive, regular correlation peaks unless the spreading code perfectly matches reality. Those peaks allowed me to easily pull the bits out and read the flag.

### 4. Where I used an AI assistant and what I had to correct
I knew nothing about extracting secret DSSS codes. I asked an AI for help, and it introduced me to the brilliant idea of chopping the signal into blocks and using Principal Component Analysis (PCA) to find the repeating structure. Since I had never implemented PCA before, the AI provided the `sklearn.decomposition` snippet. I had to manually reshape the NumPy arrays to feed into it, but the AI's core PCA logic worked beautifully.

---

## RF-H3: Fingerprint

### 1. What I tried first, and why it did not work
I initially thought about identifying the rogue transmitter by looking at the software settings like baud rate and center frequency. However, I realized this was a dead end because the rogue operator intentionally faked all of these settings to perfectly mimic another radio on the network, effectively framing them.

### 2. The insight that actually cracked it
I realized that while software settings can be faked, the physical imperfections of analog hardware cannot. When an analog mixer generates a radio wave, it always leaks a tiny "ghost" image on the opposite side of the center frequency due to hardware imbalances. I used an FFT to calculate the difference in power between the main signal and this ghost image—the Image Rejection Ratio (IRR)—for all 8 reference radios. When I checked the rogue transmission, its IRR perfectly matched the physical hardware defect of the radio that was actually transmitting.

### 3. How I satisfied myself the answer was right
The measured IRRs for the radios were highly unique, with differences spanning several decibels. The rogue transmission claimed to be Radio X (which had an IRR of ~45 dB), but the rogue's actual measured IRR was exactly ~32 dB, perfectly matching the fingerprint of the true culprit. Physics cannot be spoofed, making the conclusion undeniable.

### 4. Where I used an AI assistant and what I had to correct
I used an AI to help me write the script to automatically find the peaks in the FFT. I knew I needed to measure the power of the main peak and the image peak, but finding them programmatically in the array of FFT bins was tedious. The AI gave me a quick snippet using `scipy.signal.find_peaks`, which I just adjusted to look for the image peak on the mirrored side of the spectrum.

---

## RF-H5: Ghost Carrier

### 1. What I tried first, and why it did not work
I found the secret DSSS GPS C/A codes, but the loud 16-channel FSK frequency-hopping signal was destroying the math. I considered blanking (zeroing out) the time slices where the FSK bursts happened, but I realized this wouldn't work because zeroing out time also destroys the DSSS chips underneath them, which would prevent correlation.

### 2. The insight that actually cracked it
I realized that instead of blanking in the time domain, I had to filter in the frequency domain. I applied tight, narrow notch filters exactly on the specific frequencies where the FSK bursts hopped. Because DSSS is extremely wideband, notching out a few narrow frequencies destroyed the FSK interference but left enough of the DSSS signal completely intact. This allowed me to correlate the GPS codes and track the phase. 

### 3. How I satisfied myself the answer was right
Once I ran the PLL (Phase-Locked Loop) to track the signal after the notch filtering, the phase locked perfectly. The bits I decoded were 3 Shamir Secret Shares. Since Shamir's Secret Sharing math only produces readable text if all 3 shares are perfectly correct, the fact that XORing them together resulted in the final decrypted flag proved my DSP pipeline was flawless.

### 4. Where I used an AI assistant and what I had to correct
I had very little practical experience with advanced DSP filtering. When blanking the time domain failed, I asked an AI for alternatives, and it suggested using tight frequency-domain notch filters. Because setting up the poles and zeros for a digital IIR filter is highly complex, I had the AI provide the `scipy.signal.iirnotch` function to generate the filter coefficients, and I applied it to the frequencies I had mapped from the FSK hoppers.
