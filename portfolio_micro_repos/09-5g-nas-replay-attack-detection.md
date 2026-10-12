# 5G NAS Replay Attack Detection & Protocol Forensics

> **tl;dr:** In cellular 5G Non-Access Stratum (NAS) signalling, differentiating an adversarial message replay from benign protocol retransmissions is a core challenge. Because 3GPP standards mandate automated message retries upon packet loss, naive duplicate filters fail. By parsing custom `NASX` protocol frames, reconstructing the chronological sequence state machine per AMF UE NGAP ID, and detecting non-causal sequence counter rollbacks, we pinpoint the singular injected replay frame and identify the compromised subscriber.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Data via LFS](https://img.shields.io/badge/data-Git%20LFS-orange)
![Topics](https://img.shields.io/badge/topics-5G%20%7C%20NAS%20%7C%20Protocol--Forensics%20%7C%20Replay--Attack-purple)

---

## 1. The Engineering Problem

The 5G Non-Access Stratum (NAS) protocol governs critical control-plane signaling between the User Equipment (UE) and the Access and Mobility Management Function (AMF) in the 5G Core. NAS manages initial registration, security mode control, authentication, and PDU session establishment.

An adversarial software-defined radio (SDR) operating within radio range executed an active **man-in-the-middle replay attack** against an active 5G session. The adversary captured legitimate uplink signaling traffic, held an authentication or session-request frame, and re-injected it into the network at a later time.

A packet capture of the control-plane traffic (`data/nas_signalling.pcap`) was obtained. Security analysts reviewing the pcap face a major hurdle: cellular wireless channels frequently experience RF fading, packet drops, and timer expirations (e.g., 3GPP timers T3510, T3512), causing legitimate base stations and handsets to regularly retransmit dropped frames.

The forensic challenge is to systematically distinguish between **legitimate protocol retransmissions** and the **adversarial replay injection**, identifying the exact anomalous PCAP frame number and the affected subscriber's AMF UE NGAP ID.

---

## 2. Why Naive Approaches Fail

1. **Simple Packet Deduplication**: If an analyst runs a hash-based deduplication script (e.g., MD5/SHA256 of payload bytes) or flags duplicate sequence numbers, dozens of frames trigger alerts. Cellular networks routinely retransmit identical frames byte-for-byte upon missing an acknowledgement. Naive filtering yields an intolerable false-positive rate.
2. **Payload Decryption Assumption**: While production 5G NAS traffic utilizes 128-bit integrity protection (NIA1/NIA2/NIA3) and ciphering (NEA1/NEA2/NEA3), pre-security setup messages or telemetry test harnesses transport protocol fields in structured binary. Even without access to private K_AMF keys, behavioral sequence tracking exposes the attack.
3. **Ignoring Subscriber Context**: Analyzing sequence numbers globally across all packets produces nonsense because hundreds of distinct subscribers simultaneously maintain independent sequence counter state spaces starting from 0.

---

## 3. The Mathematical & Protocol Foundation

### 3.1 5G NAS Protocol Architecture & Binary Frame Format

NAS protocol signaling in this environment is transported over UDP encapsulating custom binary `NASX` protocol headers:

```
+-------------------------------------------------------------------------+
| Magic Identifier (4 bytes): ASCII "NASX" (0x4E 0x41 0x53 0x58)          |
+-------------------------------------------------------------------------+
| Reserved / Version (1 byte): 0x01                                       |
+-------------------------------------------------------------------------+
| Direction Flag (1 byte): 0x00 = Uplink (UE -> AMF), 0x01 = Downlink     |
+-------------------------------------------------------------------------+
| AMF UE NGAP ID (2 bytes, unsigned big-endian uint16): Subscriber Handle |
+-------------------------------------------------------------------------+
| Message Type (1 byte): e.g. 0x41, 0x4E, 0x4C, 0x54                       |
+-------------------------------------------------------------------------+
| Sequence Counter (1 byte, unsigned uint8): SN in [0, 255]               |
+-------------------------------------------------------------------------+
| Variable Information Elements / Payload Data (N bytes)                  |
+-------------------------------------------------------------------------+
```

### 3.2 Monotonic Sequence State Machine

For an honest subscriber session identified by `UE_ID`, the uplink sequence counter must satisfy strict forward monotonicity under ideal channel conditions:

$$\text{SN}_{k+1} = (\text{SN}_k + 1) \pmod{256}$$

### 3.3 The Formal Distinction: Retransmission vs. Replay

Let $f_a$ and $f_b$ be two captured frames with identical subscriber identity and sequence number:

$$\text{UE}(f_a) = \text{UE}(f_b) = u, \quad \text{SN}(f_a) = \text{SN}(f_b) = s, \quad t(f_a) \lt t(f_b)$$

#### Case A: Legitimate Retransmission
A transmission is dropped at the PHY/MAC layer. The sender's retransmission timer $T_{\mathrm{retrans}}$ expires before receiving a downlink ACK:

$$\Delta t = t(f_b) - t(f_a) \le T_{\mathrm{retrans}} \quad (\sim 10..50\,\text{ms})$$

Crucially, **no intervening messages with higher sequence numbers have been transmitted**:

$$\max_{f_i \in (f_a, f_b)} \text{SN}(f_i) = s$$

The session state machine has paused awaiting acknowledgement; no forward progress has occurred.

#### Case B: Adversarial Replay Attack
The adversary captures frame $f_a$ with sequence number $s$. Communication continues legitimately: the UE transmits $s+1, s+2, \dots, s+k$. At a later epoch $t(f_{\mathrm{replay}})$, the adversary injects the captured frame:

$$\Delta t = t(f_{\mathrm{replay}}) - t(f_a) \gg T_{\mathrm{retrans}}$$

$$\max_{f_i \in (f_a, f_{\mathrm{replay}})} \text{SN}(f_i) \ge s + 2$$

The appearance of sequence number $s$ after the state machine has already advanced to $s+2$ violates causality:

$$\text{SN}(f_{\mathrm{replay}}) \lt \text{SN}_{\mathrm{active}}$$

A physical UE firmware would never legitimately decrement its internal NAS sequence counter back to an earlier retired state. This mathematically flags $f_{\mathrm{replay}}$ as an unauthorized external injection.

---

## 4. Algorithmic Breakdown

1. **Native PCAP Parsing**:
   - Stream raw packets from `data/nas_signalling.pcap`.
   - Inspect UDP payloads for the `NASX` magic string (`b'NASX'`).
2. **Binary Header Unpacking**:
   - Extract `direction` (byte 5).
   - Extract `ue_id` via big-endian uint16 (`struct.unpack('>H', data[6:8])[0]`).
   - Extract `msg_type` (byte 8) and `seq_num` (byte 9).
3. **Per-Subscriber Session Demultiplexing**:
   - Bucket frames by `ue_id`.
   - Compile a chronological trace vector of uplink frames: $\mathcal{T}_u = [(f_i, t_i, \text{SN}_i)]$.
4. **State Machine Anomaly Inspection**:
   - For each subscriber, track the maximum observed uplink sequence number `SN_max`.
   - If a frame arrives with `SN_k < SN_max`, verify whether it is a delayed replay.
   - For UE `4217`, the sequence progression is:
     - Frame 48: Seq 4
     - Frame 78: Seq 5
     - Frame 92: Seq 6
     - **Frame 96: Seq 4** $\leftarrow$ Replay! $\text{SN}=4$ injected while active state is already $\text{SN}=6$!
     - Frame 109: Seq 7
     - Frame 119: Seq 8

---

## 5. Dataset & Data Schema

| File | Description | Packets | Size | LFS |
|------|-------------|---------|------|-----|
| `data/nas_signalling.pcap` | Captured 5G NAS control-plane signaling trace | 240 frames | ~35 KB | Yes |

### Header Fields Unpacked via Python
```python
magic, direction, ue_id, msg_type, seq_num = struct.unpack('>4sBxHBB', payload[:9])
```

---

## 6. Repository Structure

```
5g-nas-replay-attack-detection/
├── .gitattributes             # Git LFS tracking for *.pcap
├── .gitignore
├── LICENSE                    # MIT License
├── README.md                  # Protocol analysis & formal proof
├── requirements.txt           # Minimal dependencies
├── solve.py                   # Automated PCAP parser & state anomaly detector
└── data/
    └── nas_signalling.pcap    # 5G NAS signaling capture (LFS)
```

---

## 7. Setup & Execution

### Prerequisites

Ensure Git LFS is installed:
```bash
git lfs install
```

### Installation & Run

```bash
git clone https://github.com/<your-username>/5g-nas-replay-attack-detection.git
cd 5g-nas-replay-attack-detection
git lfs pull
python solve.py
```

---

## 8. Expected Output

```
[+] Ingested 240 packets from data/nas_signalling.pcap
[+] Parsing NASX protocol headers over UDP transport...
[+] Identified 14 active subscriber sessions (AMF UE NGAP IDs)
[+] Auditing Uplink Sequence Number state machines for non-causal transitions...

============================================================
CHRONOLOGICAL TIMELINE FOR SUBSCRIBER UE 4217:
  Frame  20 | UL | Type 0x41 | Seq  1  (Initial Registration)
  Frame  22 | UL | Type 0x4E | Seq  2  (Security Mode Complete)
  Frame  24 | UL | Type 0x5E | Seq  3  (PDU Session Est. Request)
  Frame  48 | UL | Type 0x4C | Seq  4  (Uplink NAS Transport)
  Frame  78 | UL | Type 0x4C | Seq  5  (Uplink NAS Transport)
  Frame  92 | UL | Type 0x4C | Seq  6  (Uplink NAS Transport)
  >>> Frame  96 | UL | Type 0x4C | Seq  4 <<< [ANOMALY: NON-CAUSAL ROLLBACK!]
  Frame 109 | UL | Type 0x4C | Seq  7  (Uplink NAS Transport)
  Frame 119 | UL | Type 0x4C | Seq  8  (Uplink NAS Transport)

============================================================
REPLAY ATTACK FORENSIC VERIFICATION:
  Malicious Injected Frame: 96
  Target AMF UE NGAP ID:    4217
  Evidence: Seq 4 re-injected after session successfully advanced to Seq 6.
  Flag: RFCTF{96_4217}
============================================================
```

---

## 9. Further Reading

- 3GPP TS 24.501: *Non-Access-Stratum (NAS) protocol for 5G System (5GS); Stage 3*.
- 3GPP TS 33.501: *Security architecture and procedures for 5G system*.
- Jover, R. P. (2019). *Security and Privacy Vulnerabilities in 5G: A First Look*. IEEE Communications Magazine.
