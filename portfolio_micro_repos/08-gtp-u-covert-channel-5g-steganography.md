# 5G GTP-U User-Plane Covert Channel & Network Steganography

> **tl;dr:** A malicious insider in a standalone 5G private network exfiltrates classified intelligence across the N3 interface without tripping Deep Packet Inspection (DPI). While the application payloads are completely clean, the adversary embeds a 4-bit covert channel into the low-order nibble of inner UDP header length fields. We de-encapsulate the GTP-U tunnel, track network flows, detect the self-synchronizing `0xDEAD` preamble, and reconstruct the secret exfiltration stream.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Data via LFS](https://img.shields.io/badge/data-Git%20LFS-orange)
![Topics](https://img.shields.io/badge/topics-5G%20%7C%20GTP--U%20%7C%20Network--Steganography%20%7C%20Packet--Analysis-purple)

---

## 1. The Engineering Problem

In a private 5G Standalone (SA) container terminal network, mission-critical operations—such as automated quay crane positioning, gate telemetry, and automated guided vehicles (AGVs)—communicate across cellular radio infrastructure. Traffic between the Next Generation NodeB (gNB) and the User Plane Function (UPF) is transported across the 3GPP **N3 interface** via GPRS Tunnelling Protocol User Plane (**GTP-U**) encapsulation over UDP port 2152.

An insider threat was suspected of moving unauthorized intelligence out of the perimeter. Network compliance and cybersecurity personnel conducted automated Deep Packet Inspection (DPI) on the captured telemetry (`data/n3_userplane.pcap`):
- All inner application payloads (JSON, sensor streams, media) were verified to be benign.
- Signatures and hashes matched standard commercial terminal operating software.

However, signals intelligence intercepted an operator note confirming that an exfiltration channel had been established:
1. It transmits exactly **4 bits (one nibble) per packet**.
2. It is **self-synchronizing**, preceded by the hexadecimal sequence `D E A D` (`1101 1110 1010 1101`).
3. Two successive nibbles form one 8-bit ASCII character (big-endian).
4. The message repeats continuously across the active flow.

The objective is to deconstruct the GTP-U encapsulation hierarchy, isolate the anomalous flow among dozens of legitimate subscriber streams, locate the carrier field, and extract the exfiltrated flag.

---

## 2. Why Naive Approaches Fail

1. **Payload-Centric DPI**: Conventional Next-Generation Firewalls (NGFW) and Snort/Suricata rules inspect packet payload buffers. Because the adversary left the payload completely unaltered, content inspection engines report zero alerts.
2. **Standard GTP-U Tunnel Decoding**: When security tools dissect GTP-U, they routinely validate outer UDP checksums and tunnel endpoint identifiers (TEIDs), forwarding inner packets directly to egress routing without verifying internal header field entropy.
3. **Entropy Scanning on Full Packets**: Computing Shannon entropy across entire packets fails to flag the anomaly because a 4-bit variation in a 500-byte packet alters total entropy by less than 0.05%, remaining well below statistical anomaly thresholds.

---

## 3. The Mathematical & Protocol Foundation

### 3.1 5G N3 Interface Tunnel Architecture

In 5G Core (5GC) networks, subscriber IP packets are not routed directly over physical backhaul links. Instead, the gNB encapsulates the complete inner User Equipment (UE) packet inside a GTP-U tunnel packet addressed to the UPF:

```
+-------------------------------------------------------------------------+
| Layer 2: Ethernet Frame Header (14 bytes)                              |
+-------------------------------------------------------------------------+
| Outer IPv4 Header (20 bytes): gNB IP -> UPF IP                          |
+-------------------------------------------------------------------------+
| Outer UDP Header (8 bytes): Dport = 2152 (GTP-U)                        |
+-------------------------------------------------------------------------+
| GTP-U Header (8 bytes):                                                 |
|   Flags (1B: v1, PT=1) | Msg Type (1B: 0xFF = T-PDU) | Length (2B)      |
|   TEID (4 bytes: Tunnel Endpoint Identifier, e.g. 0x3F2A1B)             |
+-------------------------------------------------------------------------+
| Inner IPv4 Header (20 bytes): UE Private IP -> Terminal Server IP       |
+-------------------------------------------------------------------------+
| Inner UDP Header (8 bytes): Ephemeral Sport -> Service Dport            |
|   Sport (2B) | Dport (2B) | Length (2B) | Checksum (2B)                 |
+-------------------------------------------------------------------------+
| Inner Application Payload (N bytes)                                     |
+-------------------------------------------------------------------------+
```

### 3.2 Network Steganography via Header Modulation

Network covert storage channels exploit variable or loosely enforced fields in standard network protocols. In an IPv4/UDP packet, the inner header comprises 28 bytes (20 IP + 8 UDP). 

Candidate modulation fields:
- IP Identification (16 bits)
- IP Type of Service / DSCP / ECN (8 bits)
- IP Time-to-Live (TTL) (8 bits)
- UDP Length field (16 bits, bytes 24..25 from start of inner IP)

Because small packet size variations (0 to 15 bytes) are easily absorbed by application buffers as ordinary padding, modulating the least significant nibble of the **UDP Length** header ($L_{\mathrm{UDP}}$) yields an ideal covert carrier:

$$\text{Carrier Byte} = \text{Header}[25]$$

$$\text{Nibble}_{\mathrm{low}}(k) = \text{Header}_k[25] \wedge \text{0x0F}$$

### 3.3 Channel Capacity & Self-Synchronizing Protocol

The channel capacity is:

$$\mathcal{C} = 4\,\text{bits/packet} = 0.5\,\text{bytes/packet}$$

For a message of length $M$ characters ($2M$ nibbles), transmission requires $2M$ packets. To overcome packet loss, out-of-order delivery, and arbitrary receiver capture start times, the transmitter implements a **self-synchronizing frame marker**:

$$\text{Sync Marker} = \text{0xDEAD} = [13, 14, 10, 13]_{16}$$

Upon detecting four consecutive nibbles matching `0xD, 0xE, 0xA, 0xD`, the demodulator establishes byte alignment. Subsequent nibbles are combined pairwise into ASCII octets:

$$B_j = (N_{2j} \ll 4) \vee N_{2j+1}$$

---

## 4. Algorithmic Breakdown

1. **PCAP De-encapsulation**:
   - Stream raw frames from `data/n3_userplane.pcap`.
   - Strip 14-byte Ethernet header, 20-byte outer IP, and 8-byte outer UDP.
   - Verify GTP-U UDP destination port ($2152$).
   - Skip 8-byte GTP-U header to expose inner IP packet.
2. **Flow Demultiplexing**:
   - Extract inner IP Source, Destination, and UDP Destination Port.
   - Group packets into discrete communication flows: `flow_key = (src_ip, dst_ip, dst_port)`.
3. **Multi-Field Nibble Extraction**:
   - For each flow, extract the 28-byte combined inner header (20 IP + 8 UDP).
   - For every byte position $i \in [0, 27]$, compile the sequence of high nibbles (`b >> 4`) and low nibbles (`b & 0x0F`).
4. **Preamble Acquisition**:
   - Search nibble strings for the hex pattern `dead`.
   - Locate the exact carrier: byte index 25 (lower byte of inner UDP Length), low-nibble position.
5. **ASCII Stream Demodulation**:
   - Slice nibbles immediately following the `dead` sequence.
   - Pair nibbles into 8-bit bytes and convert to ASCII characters.
   - Filter non-printable noise to recover the repeating message.

---

## 5. Dataset & Data Schema

| File | Description | Packets | Size | LFS |
|------|-------------|---------|------|-----|
| `data/n3_userplane.pcap` | GTP-U encapsulated N3 user-plane trace | 1,500 | 440 KB | Yes |

### PCAP Characteristics
- **Outer Transport**: IPv4 / UDP / Port 2152
- **GTP-U TEID**: `0x3F2A1B` (Message Type `0xFF`)
- **Inner Protocols**: IPv4 / UDP (Crane Telemetry, Port 8853, Container Automation)

---

## 6. Repository Structure

```
gtp-u-covert-channel-5g-steganography/
├── .gitattributes             # Git LFS tracking for *.pcap
├── .gitignore
├── LICENSE                    # MIT License
├── README.md                  # Protocol analysis & derivation
├── requirements.txt           # Scapy dependency
├── solve.py                   # High-speed native binary PCAP extractor
├── solve2.py                  # Scapy-based reference implementation
└── data/
    └── n3_userplane.pcap      # N3 interface packet capture (LFS)
```

---

## 7. Setup & Execution

### Prerequisites

Ensure Git LFS is installed to pull the packet capture:
```bash
git lfs install
```

### Installation & Run

```bash
git clone https://github.com/<your-username>/gtp-u-covert-channel-5g-steganography.git
cd gtp-u-covert-channel-5g-steganography
git lfs pull
pip install -r requirements.txt
python solve.py
```

---

## 8. Expected Output

```
[+] Ingested 1500 packets from data/n3_userplane.pcap
[+] Stripping GTP-U outer encapsulation (UDP:2152, TEID:0x3F2A1B)...
[+] Demultiplexed 12 distinct inner subscriber UDP flows
[+] Scanning header nibble matrices across all 28 inner header byte offsets...
[!] SYNC DETECTED: Flow (10.60.12.37 -> 203.0.113.47:8853)
    Carrier Offset: Byte Index 25 (Inner UDP Length field, low byte)
    Modulation: Low Nibble (4 bits per packet)
    Preamble Match: 0xDEAD found at packet offset #14
[+] Reassembling nibble stream into 8-bit ASCII...

============================================================
RECOVERED EXFILTRATION PAYLOAD:
||RFCTF{s1z3_1s_th3_m3ss4g3}||
============================================================
```

---

## 9. Further Reading

- 3GPP TS 29.281: *General Packet Radio System (GPRS) Tunnelling Protocol User Plane (GTPv1-U)*.
- Zander, S., Armitage, G., & Branch, P. (2007). *A Survey of Covert Channels and Countermeasures in Computer Network Protocols*. IEEE Communications Surveys & Tutorials.
- Wendzel, S., et al. (2015). *Categorization of Network Covert Channels*. arXiv:1506.01460.
