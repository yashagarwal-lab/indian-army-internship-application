import sys
import struct
from Crypto.Cipher import AES

# 1. Find and extract the mission record
with open("controller_ram.bin", "rb") as f:
    data = f.read()

idx = data.find(b"MSNCRYPT")
if idx == -1:
    print("Could not find MSNCRYPT")
    sys.exit(1)

print(f"Found MSNCRYPT at offset {hex(idx)}")
version = struct.unpack("<H", data[idx+8:idx+10])[0]
length = struct.unpack("<I", data[idx+10:idx+14])[0]
iv = data[idx+14:idx+30]
ciphertext = data[idx+30:idx+30+length]

print(f"Version: {version}")
print(f"Length: {length}")
print(f"IV: {iv.hex()}")

# 2. Search for AES key schedule
# AES S-box
SBOX = bytes([
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16
])
RCON = [0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36]

def sub_word(w):
    return bytes([SBOX[b] for b in w])

def rot_word(w):
    return w[1:] + w[:1]

def xor_bytes(a, b):
    return bytes([x ^ y for x, y in zip(a, b)])

def get_prev_round_key(rk, rcon_idx):
    # rk is a 16-byte round key (round > 0)
    # We want to find the previous round key prev_rk
    # rk is composed of 4 words: w4, w5, w6, w7
    # prev_rk is: w0, w1, w2, w3
    # w7 = w6 ^ w3 => w3 = w7 ^ w6
    # w6 = w5 ^ w2 => w2 = w6 ^ w5
    # w5 = w4 ^ w1 => w1 = w5 ^ w4
    # w4 = w0 ^ SubWord(RotWord(w3)) ^ Rcon
    # => w0 = w4 ^ SubWord(RotWord(w3)) ^ Rcon
    w4 = rk[0:4]
    w5 = rk[4:8]
    w6 = rk[8:12]
    w7 = rk[12:16]
    
    w3 = xor_bytes(w7, w6)
    w2 = xor_bytes(w6, w5)
    w1 = xor_bytes(w5, w4)
    
    tmp = sub_word(rot_word(w3))
    rcon_word = bytes([RCON[rcon_idx], 0, 0, 0])
    w0 = xor_bytes(w4, xor_bytes(tmp, rcon_word))
    
    return w0 + w1 + w2 + w3

def verify_key(key):
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    pt = cipher.decrypt(ciphertext)
    if b"Intern_Pro_Max" in pt:
        print(f"Found valid key! {key.hex()}")
        print(pt)
        return True
    return False

# Search for any valid step in the key schedule
# A round key is 16 bytes. If we consider a 32-byte window as (prev_rk, rk)
# we can check if rk is derived from prev_rk at round r
# Since we don't know the alignment, we check all offsets and all rounds.
# But "Memory gets reused... do not expect any region to be wholly intact"
# So checking a full 32 bytes might fail if only one rk is intact.
# If we have just 16 bytes of an intact rk, we can derive the original key!
# Actually, wait. Can we verify if 16 bytes is a valid round key without the previous one?
# No, 16 random bytes could theoretically be ANY round key (it's a bijection).
# But wait! If we take 16 bytes, assume it's round key R, derive the master key, and try decrypting.
# There are 1,048,576 bytes. So 1,048,576 - 15 possible 16-byte sequences.
# Assume each is round key R (for R=1..10).
# That's 10 * 1,048,576 = 10 million AES decryptions. That takes a few seconds in Python!
# Let's optimize: an AES key schedule has a strong property across 32 bytes, but if memory is corrupted,
# maybe we only have one intact round key.
# But wait, checking all 16-byte chunks is possible but maybe too much.
# Let's first check for 20-byte or 24-byte intact regions, or just use the relation:
# w_i = w_{i-4} ^ ...
# Actually, let's just do a linear scan for ANY valid `w_i == w_{i-4} ^ w_{i-1}` for non-multiple-of-4 words.
# Specifically, for a 16-byte round key (w4, w5, w6, w7):
# w5 = w4 ^ w1
# w6 = w5 ^ w2
# w7 = w6 ^ w3
# This is true for the current round key and the previous.
# So w_i ^ w_{i-1} ^ w_{i-4} == 0.
# If we have 20 consecutive bytes (5 words), we can check this.
# If we just do the decryption test for all 16-byte aligned chunks, maybe?
# The challenge says "The scrub zeroed the sixteen bytes that held it. Think about what else an AES implementation keeps in memory... The relationship between those values runs in only one direction... Memory gets reused. Something else was allocated over part of what you are looking for."
# This implies that the key schedule might be partially overwritten.
# We just need to find one round key and step back!

def derive_master_from_rk(rk, r):
    curr = rk
    for i in range(r, 0, -1):
        curr = get_prev_round_key(curr, i)
    return curr

# To quickly find candidates, we can scan for a valid 24-byte or 20-byte sequence.
# Let's check for any index i where:
# data[i:i+4] ^ data[i+4:i+8] == data[i+16:i+20] (which is w_{k} ^ w_{k+1} == w_{k+4})
# Wait, w_{k+4} = w_{k} ^ w_{k+3} is for the NEXT round key.
# Actually, in a contiguous key schedule array of 44 words:
# For k not a multiple of 4, w_k = w_{k-1} ^ w_{k-4} => w_{k-4} ^ w_{k-1} ^ w_k = 0.
# So data[i:i+4] ^ data[i+12:i+16] ^ data[i+16:i+20] == 0.
# This requires 20 bytes (w_0, w_1, w_2, w_3, w_4).
# And it works for any k % 4 != 0.
# Let's scan for this property!

candidates = []
for i in range(len(data) - 20):
    w_minus_4 = data[i:i+4]
    w_minus_1 = data[i+12:i+16]
    w_0       = data[i+16:i+20]
    
    if xor_bytes(w_minus_4, w_minus_1) == w_0:
        candidates.append(i)

print(f"Found {len(candidates)} candidates with w_0 = w_-4 ^ w_-1")

# From these candidates, we might have found a piece of the key schedule.
# If i is the offset of w_{k-4}, then w_0 is w_k.
# We don't know k. But k % 4 != 0.
# Let's just try to assume the 16 bytes starting at various offsets near 'i' are a round key r,
# derive the master key, and test.

def try_all_candidates():
    for cand in candidates:
        # A candidate is 20 bytes. It could be anywhere in the key schedule.
        # Let's just take 16-byte chunks around this candidate.
        # Check from cand - 32 to cand + 32
        for offset in range(cand - 64, cand + 64):
            if offset < 0 or offset + 16 > len(data): continue
            rk = data[offset:offset+16]
            for r in range(1, 11):
                try:
                    mk = derive_master_from_rk(rk, r)
                    if verify_key(mk):
                        return
                except:
                    pass

try_all_candidates()

