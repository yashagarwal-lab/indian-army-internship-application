# CEMA-H3 — Core Dump II

**Exercise PARCHAM · Serial NIGHT KITE · Rann of Kutch**

A flight controller was recovered from a crash site in the Rann of Kutch, where a
hostile-role aircraft went in hard after losing its link. Before the board was
sent for disposal we pulled a 1 MB image of its RAM.

We know the firmware encrypts mission records with AES-128 and that one encrypted
record was resident in memory at the time of capture. Exercise control wants to
know what that aircraft had been tasked to do.

The bad news is that this firmware scrubs its key material on shutdown, and the
shutdown path ran. We have already searched the image for the key and it is not
there.

## The data

`controller_ram.bin` — 1,048,576 bytes, a raw memory image. No symbols, no page
table, no structure guaranteed. It contains what you would expect in a live
embedded system's RAM: heap, zeroed pages, log text, string tables, driver
structures, and anything else that happened to be resident.

Encrypted mission records in this firmware are laid out as:

| offset | size | field |
|---|---|---|
| 0 | 8 | ASCII magic `MSNCRYPT` |
| 8 | 2 | version |
| 10 | 4 | ciphertext length, little-endian |
| 14 | 16 | AES-CBC initialisation vector |
| 30 | *len* | ciphertext (AES-128-CBC, PKCS#7 padded) |

---

## Your task

Read the encrypted mission record. The flag is inside the plaintext.

Some things worth knowing before you start:

- The key itself is gone. The scrub zeroed the sixteen bytes that held it. If you
  are grepping for key bytes you are looking for something that no longer exists.
  Think about what *else* an AES implementation keeps in memory while it works,
  and whether the relationship between those values runs in only one direction.
- Whatever you find is not labelled, not aligned to any convenient boundary, and
  sits next to nothing that identifies it. The image has plenty of high-entropy
  regions that are not what you want.
- Memory gets reused. Something else was allocated over part of what you are
  looking for, so do not expect any region of this dump to be wholly intact or
  wholly self-consistent. An approach that requires everything to check out will
  find nothing at all.
- If you recover a candidate key, the only way to know it is right is to use it.
  A wrong one will decrypt just as happily into noise.

## Flag format

The flag appears in the decrypted plaintext in the form:

```
Intern_Pro_Max{...}
```

Submit it exactly as it appears.
