# CEMA Track Write-up

## CEMA-H1: Quiet Power

### 1. What I tried first, and why it did not work
Initially, I thought about brute-forcing the 16-byte AES key directly, but $2^{128}$ combinations is impossible to compute. I knew the chip leaked power based on what it was doing, but looking at raw power traces manually was a dead end because the noise completely hid any obvious bit patterns.

### 2. The insight that actually cracked it
I realized I didn't need to guess the whole key at once. I could use Correlation Power Analysis (CPA) to guess just one byte at a time. I wrote a script to simulate the AES S-Box output for all 256 possible guesses of a single byte and calculated the Hamming Weight (number of 1s) for each guess. By running a Pearson correlation between my simulated weights and the actual power traces, the mathematically correct guess spiked dramatically above the noise. I just looped this 16 times for all the bytes.

### 3. How I satisfied myself the answer was right
When I ran the script, 15 out of the 256 guesses for a byte would have near-zero correlation, but exactly one guess would produce a massive, undeniable mathematical spike. When I took all 16 of these high-correlation bytes and used them as the AES key, it perfectly decrypted the provided payload into the readable "Intern_Pro_Max" flag, proving the key was correct.

### 4. Where I used an AI assistant and what I had to correct
I had never even heard of Correlation Power Analysis (CPA) before this challenge. I asked an AI to explain how hardware power analysis works, and it taught me about using Pearson correlation to compare Hamming weights. Once I understood the theory, I asked the AI to help me write the vectorized NumPy math for the cross-covariance, which sped up my script massively. I just had to adapt the variable names to match my loaded datasets.

---

## CEMA-H2: Mission Seal II

### 1. What I tried first, and why it did not work
The first thing that crossed my mind was writing a loop to brute-force the 64-bit squadron key, simulating the seal function for each guess. However, the math showed that even at a billion checks per second, it would take almost 600 years to run, so brute-forcing was completely useless.

### 2. The insight that actually cracked it
I looked really closely at the provided Python `seal` algorithm and realized it only used bit shifts, XORs, and Galois Field multiplication. Because it had absolutely no non-linear operations (like an S-Box), the entire hashing process was completely linear over GF(2). This meant I could model the algorithm as a giant 64x64 binary matrix. Since I had 5 missions with 24 bits of the seal exposed each, I generated 120 linear equations and just used standard Gaussian Elimination over GF(2) to solve for the exact 64-bit key.

### 3. How I satisfied myself the answer was right
Because the matrix math is exact, there was no guessing involved. To be absolutely sure it wasn't a mathematical fluke, I plugged the key my script generated back into the original `seal` algorithm and ran it against all 5 intercepted missions. My key perfectly reproduced all 5 seals exactly as they appeared in the log.

### 4. Where I used an AI assistant and what I had to correct
I had very little knowledge about finite field mathematics. I asked an AI how to reverse the `seal` function, and it explained that because the function only uses XOR and bit-shifts, it is completely linear over Galois Field 2 and can be solved with matrix math. Since I had never written a Gaussian Elimination solver for GF(2), I had the AI write the `solve_linear_system_gf2` function for me. I didn't have to correct the math; I just fed my generated equations into it.

---

## CEMA-H3: Core Dump 2

### 1. What I tried first, and why it did not work
My first thought was to search the raw RAM dump for the 16-byte Master Key, assuming it might be sitting in plain text near the AES buffers. However, I realized this would be a complete waste of time because the prompt explicitly stated a security scrub had already zeroed out the Master Key array.

### 2. The insight that actually cracked it
The challenge hinted that the memory gets reused and other things are kept in memory. I realized that AES expands the Master Key into a large Key Schedule. Even if the Master Key was zeroed, parts of this expanded schedule might still be in RAM. I wrote a scanner to look for a specific mathematical property of the AES key schedule: `w[k] = w[k-1] ^ w[k-4]`. My scanner found a 20-byte block that perfectly matched this XOR rule. Once I had an intact round key, I just wrote a script to run the AES key expansion backward to recover the original Master Key.

### 3. How I satisfied myself the answer was right
To verify the Master Key, I searched the memory dump for the "MSNCRYPT" header to find the ciphertext and IV. I took the Master Key my script reversed, plugged it into a standard AES-CBC decryptor with the IV, and it perfectly decrypted the payload into the "Intern_Pro_Max" flag. 

### 4. Where I used an AI assistant and what I had to correct
I didn't know the deep mathematical internals of AES, so I asked an AI how the Key Schedule actually works. It explained the `w[k] = w[k-1] ^ w[k-4]` relationship to me. Since reversing the key schedule requires carefully undoing Rcon XORs and SubWord steps that I was completely unfamiliar with, I had the AI generate the inverse logic for the `get_prev_round_key` function. I wrote the memory scanning logic myself, and the AI's reversal function worked perfectly once I fed the block into it.
