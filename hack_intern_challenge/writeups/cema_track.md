# CEMA Track Writeup

### CEMA-H1: Quiet Power

**Goal:**
I was given a dataset of power traces recorded while a chip was encrypting data using AES-128. My goal was to figure out the secret 16-byte AES key by analyzing the power consumption.

**Thought process:**
Since the chip uses more power when more bits are flipping (Hamming Weight), I could guess the key by comparing the power traces to the expected AES math. I knew the plaintexts, so for every single byte of the 16-byte key, I just looped through all 256 possible guesses. 

For each guess, I simulated the AES S-Box output and calculated its Hamming Weight. Then, I used Pearson correlation to compare my simulated weights against the actual power traces. The correct key byte was just the one that caused a massive correlation spike. I did this 16 times to pull the full flag out.

**What I learned:**
This challenge was really cool because it showed me how hardware actually leaks secret information through its power consumption.

***

### CEMA-H2: Mission Seal II

**Goal:**
A hostile drone used a secret 64-bit key to hash and seal its mission files. I intercepted 5 sealed missions. My goal was to recover the 64-bit key without brute-forcing it, which would take 580 years.

**Thought process:**
I looked at the Python code for the seal algorithm and noticed it only used bitwise shifts, XORs, and Galois Field multiplication. There were no non-linear operations at all. This meant the entire hashing process was completely linear over modulo 2.

Because it was linear, I could represent the entire algorithm as a giant 64x64 binary matrix. Since I had 5 missions with 24 bits of the seal exposed for each, I had 120 linear equations. I just built an augmented matrix and used standard Gaussian Elimination over GF(2) to solve for the exact 64-bit key instantly.

**What I learned:**
This challenge was really cool because it showed me that custom crypto can be completely broken if it relies only on linear operations.

***

### CEMA-H3: Core Dump 2

**Goal:**
I got a raw RAM dump from a microcontroller that was running AES. A security scrub had zeroed out the master key, but the goal was to somehow recover it from the memory anyway.

**Thought process:**
Even though the master key was deleted, AES creates a large "Key Schedule" (an array of round keys) to do the encryption. The challenge hinted that parts of this key schedule might still be in memory. 

I knew a mathematical property of the AES key schedule: for a specific alignment, any word XORed with the word before it equals the word 4 spaces back. I wrote a script to scan the entire RAM dump for any 20-byte block that matched this XOR pattern. Once my scanner found an intact round key, I just wrote a script to run the AES key expansion algorithm backward to calculate what the original master key was, and then used it to decrypt the flag.

**What I learned:**
This challenge was really cool because it showed me that even if you delete a key, its derived state can still be sitting in memory.
