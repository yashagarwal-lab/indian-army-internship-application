# RF Track Writeup

### RF-H1: Two Radios, One Channel

**Goal:**
I got an IQ recording with two BPSK radio signals transmitting on the exact same frequency. The loud one was a boring 12.5 kBd signal, but the flag was hidden in the weaker signal underneath it. My goal was to isolate and read the weak signal.

**Thought process:**
Since the loud signal was 15 dB stronger, it completely dominated the recording. To read the weak one, I had to do Successive Interference Cancellation. 

I demodulated the loud signal to get its exact bits and timing. Then, I mathematically reconstructed a perfect, noiseless version of that loud waveform and subtracted it from the raw recording. Once the loud signal was subtracted out, the noise floor dropped and the weak signal was perfectly visible. I just ran a standard BPSK demodulator on the clean recording to read the flag.

**What I learned:**
This challenge was really cool because it showed me that you can actually subtract radio signals from each other to see what's underneath.

***

### RF-H2: Chipped

**Goal:**
A secret Direct-Sequence Spread Spectrum (DSSS) link was transmitting below the noise floor. I knew the symbol length was 127 chips, but I didn't know the spreading code. My goal was to blindly figure out the code and decode the flag.

**Thought process:**
In DSSS, every data bit is just the entire 127-chip spreading sequence multiplied by +1 or -1. Since the sequence repeats exactly every 127 chips, I could chop the recording into blocks of exactly 127 chips and stack them on top of each other.

Because the data modulation was just +1 or -1, squaring the blocks wiped away the data and left only the repeating structure. I used Principal Component Analysis (PCA) on the stacked blocks to extract the strongest repeating pattern, which turned out to be the exact spreading code! Then I just correlated that code against the whole recording to pull the BPSK bits out of the noise.

**What I learned:**
This challenge was really cool because it showed me how to use matrix math to blindly extract structures hidden beneath the noise floor.

***

### RF-H3: Fingerprint

**Goal:**
Eight radios were recorded, and one of them sent an unauthorized rogue transmission. The rogue operator tried to frame another radio by perfectly matching its transmission settings. My goal was to figure out which radio was actually transmitting.

**Thought process:**
Even though the operator faked the software settings, they couldn't fake the physical hardware imperfections of the radio. An analog IQ mixer always creates a tiny "ghost" signal on the opposite side of the center frequency due to slight imbalances in the circuits. 

The difference in power between the main signal and this ghost signal is called the Image Rejection Ratio (IRR). I took the FFT of all 8 reference radios and calculated their unique IRR. Then, I calculated the IRR of the rogue transmission. Even though it was pretending to be Radio X, its IRR perfectly matched the hardware fingerprint of Radio Y.

**What I learned:**
This challenge was really cool because it showed me that hardware imperfections act like unforgeable physical fingerprints.

***

### RF-H5: Ghost Carrier

**Goal:**
A recording had a loud 16-channel FSK frequency-hopping network, but there was a secret DSSS "Ghost Carrier" transmitting at the exact same time. My goal was to decode both and get the final flag.

**Thought process:**
First, I demodulated the FSK hoppers and brute-forced the bit offset by testing the CRC checksum until it passed. That gave me a file telling me about the Ghost Carrier.

The Ghost Carrier used GPS C/A codes. I correlated all 32 possible GPS codes across the data using FFTs and found three massive peaks, proving the signal was there. However, the loud FSK hops were destroying the data. Instead of blanking out the hops in time (which deletes the DSSS chips too), I applied tight notch filters in the frequency domain just to kill the FSK interference. After tracking the frequency drift with a PLL, I recovered the bits, which were 3 Shamir Secret Shares. I XORed them together and decrypted the final flag.

**What I learned:**
This challenge was really cool because it showed me how to use narrow frequency notching to clean up wideband interference.
