# 5G Mobile Track: Comprehensive Technical Writeup

This document outlines the detailed operations across the three challenges of the 5G Mobile track. By understanding the protocol-level mechanics of GTP-U, NAS (Non-Access Stratum) signaling, and 5G Mobility tracking, you will gain the depth needed to draft your final report.

---

## 5G-H1: The Quiet Exfil

### Context & Goal
A compromised insider within a private 5G network is exfiltrating data. The network's compliance team analyzed the GTP-U encapsulated UDP payloads (`n3_userplane.pcap`) and found them to be completely benign. The challenge states that the data is not in the payload, but is self-synchronizing with the marker `D E A D`, carrying 4 bits per packet. The goal is to extract the exfiltrated ASCII flag.

### The Vulnerability / Concept
Network steganography often involves hiding data in innocuous packet header fields (covert channels). Because IPv4 and UDP headers contain variable or loosely-enforced fields (e.g., IP ID, DSCP/TOS, specific lengths, or checksums), an attacker can inject custom bits into these fields without corrupting the packet's ability to be routed. Since 4 bits (one nibble) are exfiltrated per packet, we can scan the headers of each distinct UDP flow byte-by-byte, checking the high (top 4 bits) and low (bottom 4 bits) nibbles for the hex sequence `D E A D`.

### Algorithmic Breakdown
1.  **Flow Separation:** Read the PCAP and strip the GTP-U encapsulation. Group the inner IP/UDP packets by their network flows (Source IP, Dest IP, Dest Port).
2.  **Header Extraction:** For each flow, extract the first 28 bytes (20 bytes IPv4 header + 8 bytes UDP header).
3.  **Nibble Scanning:** Iterate over all 28 byte indices. For each index, extract the `high` and `low` nibble sequences across all packets in the flow.
4.  **Sync Detection:** Search the resulting nibble strings for the substring `dead`. 
5.  **Reassembly:** Once `dead` is found, take the remaining nibbles, pair them into 8-bit bytes (most significant nibble first), and cast them to ASCII characters to read the hidden message.

### Code Walkthrough (Key Segments)

```python
# Strip GTP-U and extract headers
if GTP_U_Header in p and IP in inner and UDP in inner[IP]:
    header = bytes(inner[IP])[:20] + bytes(inner[UDP])[:8]
    
# Scan for the 'dead' sequence in the 4-bit nibbles
seq1 = ''.join(f'{n >> 4:x}' for n in bytes_list)  # High nibbles
seq2 = ''.join(f'{n & 0xf:x}' for n in bytes_list) # Low nibbles

if 'dead' in seq2:
    idx = seq2.find('dead')
    data_nibbles = seq2[idx+4:] # Extract data post-sync

# Reassemble nibbles into bytes
for j in range(0, len(data_nibbles)-1, 2):
    b = int(data_nibbles[j:j+2], 16)
    msg += chr(b)
```

---

## 5G-H2: Replay

### Context & Goal
A replay attack was executed against a 5G Non-Access Stratum (NAS) connection (`nas_signalling.pcap`). The attacker intercepted an uplink NAS message and re-injected it. However, the network itself also legitimately retransmits dropped packets. The objective is to identify the singular, maliciously injected frame and the AMF UE NGAP ID of the affected subscriber.

### The Vulnerability / Concept
NAS handles mobility and session management between the User Equipment (UE) and the AMF. Each NAS message has a sequence number. When a packet is retransmitted legitimately, it usually occurs rapidly after a timeout. A *malicious replay*, however, is often injected much later, meaning the UE's state may have completely changed or advanced to a new sequence number. By parsing the custom `NASX` binary structure over UDP, sorting by the UE ID, and checking the sequence numbers and timing, we can spot the anomalous frame.

### Algorithmic Breakdown
1.  **Binary Parsing:** The PCAP contains custom UDP payloads starting with the magic bytes `NASX`. We unpack the binary headers (`struct.unpack`) to extract the Direction, UE ID, Message Type, and Sequence Number.
2.  **Filtering by UE:** By printing out the message stream for the target UE (or filtering for duplicate sequence numbers), we generate a chronological trace of the connection state.
3.  **State Analysis:** We visually compare the duplicate sequence frames. The legitimate retransmission happens almost immediately. The malicious injection happens much later, at a point where the legitimate communication has already advanced well past that sequence number. 

### Code Walkthrough (Key Segments)
```python
# Custom NAS parser
self.magic = data[0:4] # b'NASX'
self.direction = data[5] # 0=UL, 1=DL
self.ue_id = struct.unpack(">H", data[6:8])[0]
self.seq_num = data[9]
```

---

## 5G-H3: Needle in the Handovers

### Context & Goal
You are given a syslog of mobility events (`NGEV`) from an AMF in Kandla port. Your goal is to track a single subscriber with a known IMSI (SUPI) as they walk through the yard, calculate how many distinct cells they visited, and determine their final 5G-GUTI.

### The Vulnerability / Concept
In 5G, the permanent IMSI/SUPI is only sent once (for privacy). Afterwards, the network identifies the subscriber using a temporary 5G-GUTI, which is continuously reallocated for security. The logs use a `ran` (Radio Access Network) ID to track a *connection session*.
To track a single subscriber across time, you must perform stateful tracking:
`SUPI -> triggers initial RAN connection -> network issues GUTI_1 -> connection drops (RAN cleared) -> UE reconnects -> presents GUTI_1 -> establishes new RAN connection -> network issues GUTI_2`.

### Algorithmic Breakdown
1.  **Initialization:** Search for the `identity` event matching the target SUPI. Record the active `ran` ID.
2.  **Session Tracking:** While a `ran` is active, record any `handover` events (add target cells to a set) and any `realloc` events (store the new `guti`).
3.  **Connection Release:** When a `release` event matches the current `ran`, set the active `ran` to `None`. The subscriber is now idle, but they still hold the last recorded `guti`.
4.  **Reconnection:** When a `service` request appears carrying the subscriber's current `guti`, they have reconnected. Record the new `ran` ID and the `cell` they connected to.
5.  **Aggregation:** Continue this state machine until the end of the log to output the total unique cells and the final active GUTI.

### Code Walkthrough (Key Segments)
```python
# The Stateful Tracking Loop
if ev.get('ev') == 'identity' and ev.get('supi') == TARGET_SUPI:
    current_ran = ran # Anchor the first session

elif current_ran is not None and ran == current_ran:
    if ev.get('ev') == 'realloc':
        current_guti = ev.get('newguti') # Update temporary ID
    elif ev.get('ev') == 'handover':
        visited_cells.add(ev.get('to'))  # Track mobility
    elif ev.get('ev') == 'release':
        current_ran = None               # Drop session

elif current_ran is None and current_guti is not None:
    if ev.get('ev') == 'service' and ev.get('guti') == current_guti:
        current_ran = ran                # Re-anchor the new session
```

---
---

## Deep Dive: Computer Networking & 5G Principles Glossary

To truly master this track, you must deeply understand the underlying architecture of how computers and phones talk to each other. Here is an atomic-level breakdown of every networking term and Python mechanism used in the solutions above.

### 1. Packets and the OSI Model
Think of the internet like a physical postal system. When you send a picture to a friend, your phone doesn't send the whole picture as one giant chunk. It chops the picture into thousands of tiny envelopes called **Packets**. 
These packets travel across copper wires, fiber optics, and radio waves. To make sure routers know what to do with them, every packet is wrapped in **Headers** (the outside of the envelope). This wrapping happens in layers (The OSI/TCP-IP model):
- **Layer 2 (Ethernet/MAC):** The physical envelope moving between two local machines.
- **Layer 3 (IP - Internet Protocol):** The global addresses (Source IP and Destination IP). This gets the packet across the world.
- **Layer 4 (UDP/TCP):** The ports. Once the packet reaches the correct computer, Port numbers (like Port 80 for HTTP, or Port 9801 for the logs in H3) tell the computer which specific application should open the envelope.

### 2. UDP vs. TCP
- **TCP (Transmission Control Protocol):** Like making a phone call. It guarantees delivery. If a packet gets dropped, TCP mathematically realizes it and asks the sender to re-transmit it. It is reliable but slow.
- **UDP (User Datagram Protocol):** Like a firehose or a radio broadcast. It just blasts packets out as fast as possible. If a packet drops, UDP does not care. It is heavily used in 5G, video streaming, and gaming because speed is more important than perfect reliability.

### 3. GTP-U (GPRS Tunnelling Protocol - User Plane)
In 5G, when your phone sends a normal UDP packet to YouTube, the cell tower (gNB) doesn't just route it directly to the open internet. It wraps your *entire* packet inside **another** packet to send it through the cellular provider's private core network. This "packet inside a packet" wrapping is called **GTP-U Encapsulation**. In H1, we had to "strip" the GTP-U header off just to see the original, inner packet you were sending.

### 4. Sequence Numbers and Replay Attacks (H2)
When a network sends hundreds of packets, they might arrive out of order, or get lost entirely. To fix this, protocols assign a **Sequence Number** to every packet (Packet #1, Packet #2, Packet #3).
- **Legitimate Retransmission:** In 5G, if a packet drops (e.g., due to bad signal), the network waits a few milliseconds, times out, and resends the *exact same packet* with the *exact same sequence number*.
- **Replay Attack:** A hacker intercepts a secure packet (like an authentication request) and holds onto it. Hours later, the hacker injects that identical packet back into the network to trick the system into authenticating them.
- **The Defense:** A secure state machine tracks sequence numbers. If the network is currently expecting Packet #500, and a hacker suddenly injects Packet #2 (which was intercepted hours ago), the state machine knows it's a Replay Attack and rejects it.

### 5. Non-Access Stratum (NAS)
The cellular network is divided into two parts:
1. **AS (Access Stratum):** The actual radio waves connecting your phone to the cell tower.
2. **NAS (Non-Access Stratum):** The invisible conversation between your phone and the "Core Network" (the AMF). NAS handles things like authentication, mobility, and security. NAS messages don't care about radio waves; they care about proving *who* you are. In H2, we parsed custom binary `NASX` headers to read these conversations.

### 6. SUPI, GUTI, and Cellular Privacy (H3)
If your phone constantly broadcast its permanent ID (like a MAC address or phone number), anyone with a $20 antenna could track your location as you walked around the city. 5G prevents this using temporary identities.
- **SUPI (Subscription Permanent Identifier):** Your permanent SIM card identity. Your phone only broadcasts this exactly **once** when it first joins the network.
- **GUTI (Globally Unique Temporary Identifier):** After verifying your SUPI, the network issues you a random GUTI. You use this GUTI to identify yourself. Every time your connection drops or you move to a new cell tower, the network issues you a *brand new GUTI*.
- **The Challenge (H3):** Because the GUTI constantly changes (`realloc`), you cannot track a user by a single ID. You must build a **State Machine** in Python that remembers the link between the old GUTI and the new GUTI.

### 7. Code Deep Dive: `struct.unpack` and Binary Parsing
In H2, we used `struct.unpack('<IIII', pkt_header)`. Why?
When data is sent over a network, it is sent as raw binary (1s and 0s). Python reads this as a `bytes` object (e.g., `b'\x00\x04\x1a'`). 
If a 32-bit integer (4 bytes) is sent, Python doesn't automatically know it's an integer. It just sees 4 bytes. The `struct` library is the translator.
- The format string `'<IIII'` tells Python: *"Take these 16 bytes, and unpack them into four 32-bit Unsigned Integers (`I`), reading them in Little-Endian byte order (`<`)."* 
This is the fundamental way all low-level networking code (like Wireshark or Scapy) parses binary packet headers into readable variables.
