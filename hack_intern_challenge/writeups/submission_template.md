# 5G / Mobile Analysis Track Write-up

## 5G-H1: The Quiet Exfil

### 1. What I tried first, and why it did not work
The challenge hinted that the payloads were completely clean, so looking inside the message itself was a dead end. Because the setup wasn't overly complicated, I didn't waste time on multiple failed trials. The hints pointed directly to network steganography, which made me realize I had to look exclusively at the structural packet headers rather than the payloads.

### 2. The insight that actually cracked it
I knew the attacker was hiding exactly 4 bits of data per packet. I wrote a Python script using Scapy to strip the GTP-U encapsulation and group the packets into network flows. Then, I scanned the uppermost and lowermost nibbles (half-bytes) of the IP and UDP headers to check if the hex sync word "dead" was present. Once I found that sequence in the lower nibbles of a specific flow, I knew the hidden message started right after it. The final step was to extract the following nibbles, pair them into full 8-bit bytes, and convert them to ASCII to get the flag.

### 3. How I satisfied myself the answer was right
Because the procedure was relatively straightforward, my main verification was the final output itself. When I glued the extracted nibbles back together, instead of printing random garbage, it produced a perfectly readable ASCII string containing the RFCTF flag. That immediately proved I had successfully extracted the hidden covert channel data and wasn't just reading noise.

### 4. Where I used an AI assistant and what I had to correct
I did not have previous knowledge of how to use the Scapy library to parse network packets, so I used an AI assistant to get the idea for the coding aspect of it. I gave the AI my exact thinking process (grouping the flows and scanning the nibbles), and it generated the correct Scapy functions to pull the headers. I didn't have to correct much of the code since my core logic was already laid out.

---

## 5G-H2: Replay

### 1. What I tried first, and why it did not work
I initially thought about just scanning the packet capture for duplicate sequence numbers, but I realized this wouldn't work. The 5G network routinely drops packets and legitimately retransmits them byte-for-byte, meaning just finding a duplicate wasn't enough to prove it was an attack.

### 2. The insight that actually cracked it
I realized I needed to distinguish between a fast, legitimate network retry and a delayed, malicious replay. I wrote a Python script using the `struct` module to unpack the custom binary `NASX` headers over UDP. By extracting the UE ID, Message Type, and Sequence Number, I generated a chronological timeline for the specific subscriber. When I looked at the timeline, the malicious packet stood out because it was injected much later, long after the phone's connection state had already advanced past that sequence number.

### 3. How I satisfied myself the answer was right
To be absolutely sure, I compared the time gaps between the duplicates. The legitimate network retransmissions happened almost immediately after a timeout. The duplicate I flagged had a massive, unnatural time delay. Seeing that the connection had clearly moved on made me 100% confident this was the injected packet and not a normal network retry.

### 4. Where I used an AI assistant and what I had to correct
I used an AI assistant to help me figure out how to parse the custom binary packet headers. I had never used Python's `struct.unpack` before, so I explained which fields (like UE ID and Sequence Number) I needed to extract from the raw bytes, and the AI helped me write the correct unpacking format string. I didn't have to correct much, I just had to adapt the code to fit into my timeline script.

---

## 5G-H3: Needle in the Handovers

### 1. What I tried first, and why it did not work
Initially, looking at the log file was completely overwhelming because I didn't understand the 5G terminology. I saw the target's permanent ID (SUPI) appear only once. I tried to just filter the log for the `ran` ID attached to that first event, assuming it was a unique session token. This failed completely. The network recycles `ran` IDs constantly, so my script ended up merging the movements of a bunch of random users into my target's path, giving me a massive, impossible cell count.

### 2. The insight that actually cracked it
After using an AI to explain what all these terms actually meant, the core insight clicked: 5G uses temporary identities (GUTIs) for privacy, and I couldn't track a single ID statically. I had to build a "state machine" to track the identities as they chained together. I wrote a script that watched for a `realloc` event to catch the new temporary GUTI. When a `release` event dropped the connection, my script saved that GUTI. When a `service` event popped up later with that exact same GUTI, I knew it was my target reconnecting, allowing me to grab their new `ran` ID and resume tracking their handovers.

### 3. How I satisfied myself the answer was right
Before doing this, my blind filtering produced crazy results like the user teleporting across the port instantly. Once I built the state-tracking loop, the noise completely vanished. The resulting path showed a clean, logical sequence of physical cell handovers without any impossible jumps. Seeing the data switch from chaotic teleportation to a smooth physical path proved the state tracking was working correctly and I had isolated the true target.

### 4. Where I used an AI assistant and what I had to correct
I honestly had very little idea about the 5G concepts used in this challenge (like SUPI, GUTI, and RAN IDs). I asked an AI assistant to help break down exactly what the question was asking and to teach me how 5G temporary identities work. Once the AI helped me understand the underlying theory, I realized I needed to build a state machine. The AI then helped me structure the Python `if/elif` loops to track those state variables, though I had to correct some minor logic where the AI got confused between the `service` and `register` events.
