# 5G GUTI Mobility Tracking & Cellular Identity Chain Forensics

> **tl;dr:** In 5G networks, subscriber privacy is enforced by hiding the permanent SIM identity (SUPI) and continuously rotating temporary identities (5G-GUTI) across base station handovers. By implementing a stateful, chained Finite State Machine (FSM) over an AMF control-plane capture, we bridge session releases, track dynamic GUTI reallocations, and reconstruct the exact cellular trajectory and final temporary identity of a specific target subscriber.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Data via LFS](https://img.shields.io/badge/data-Git%20LFS-orange)
![Topics](https://img.shields.io/badge/topics-5G%20%7C%20GUTI%20%7C%20Mobility--Management%20%7C%20Protocol--Forensics%20%7C%203GPP-purple)

---

## 1. The Engineering Problem

Modern 5G networks implement robust subscriber privacy mechanisms designed to prevent passive radio-frequency eavesdropping and rogue cell-site tracking (IMSI Catchers / Stingrays). When a mobile device (User Equipment, UE) registers with the network, its Subscription Permanent Identifier (SUPI / IMSI) is transmitted only once across the radio interface. Immediately thereafter, the 5G Core Access and Mobility Management Function (AMF) allocates a temporary identifier: the **Globally Unique Temporary Identifier (5G-GUTI)**.

Throughout the subscriber's movement across the radio access network:
- The UE executes cell-to-cell handovers across Next Generation NodeBs (gNodeBs).
- The network periodically issues `GUTI Reallocation Command` messages, changing the user's broadcast identity.
- Radio sessions release (`RRC Inactive / Idle`), and subsequent service requests re-anchor on new session handles.

An automated packet capture (`data/mobility_events.pcap`) recorded control-plane N2 / NGAP syslog telemetry from a private port facility AMF. The signals intelligence mission is to track an individual target subscriber with a known initial SUPI, determine the total number of distinct radio cells visited across the facility, and recover the subscriber's **final active 5G-GUTI**.

---

## 2. Why Naive Approaches Fail

1. **Static SUPI Filtering**: Searching for the target's SUPI in Wireshark or via regex yields exactly one match at the initial connection event. The subscriber then becomes invisible to static filtering because the permanent identity is never used again.
2. **Static Session (`ran`) Filtering**: Analysts often attempt to track the subscriber using the ephemeral Radio Access Network connection handle (`ran_id`). This completely fails because `ran` handles are local, ephemeral identifiers. When the phone goes to sleep or transitions to idle mode, the connection is released and the `ran` ID is purged and recycled by the base station for unrelated devices. Filtering on `ran_id` causes the user to "teleport" or merges unrelated subscribers together.
3. **Static GUTI Filtering**: The AMF refreshes the GUTI regularly (`realloc`). A static filter on the first observed GUTI loses the subscriber after their first handover boundary.

---

## 3. The Mathematical & Protocol Foundation

### 3.1 5G-GUTI Architecture

A 5G-GUTI is structured as defined in 3GPP TS 23.003:

```
+-------------------------------------------------------------------------+
|                              5G-GUTI                                    |
+------------------------------------+------------------------------------+
|               PLMN ID              |              5G-TMSI               |
+------------------+-----------------+------------------------------------+
|   MCC (3 digits) |  MNC (2-3 dig)  | AMF Region | AMF Set | AMF Pointer |
+------------------+-----------------+------------------------------------+
```

Example in our trace: `404-86-bfc596c9`
- `404-86`: Public Land Mobile Network (MCC=404, MNC=86).
- `bfc596c9`: Hexadecimal 5G Temporary Mobile Subscriber Identity (5G-TMSI).

### 3.2 The Chained Finite State Machine (FSM)

To track an entity whose identifier continuously mutates over time, we construct a **stateful identity chain**:

$$\text{SUPI} \xrightarrow{\text{identity}} \text{Session}_1 \xrightarrow{\text{realloc}} \text{GUTI}_1 \xrightarrow{\text{release}} \emptyset \xrightarrow{\text{service}(\text{GUTI}_1)} \text{Session}_2 \xrightarrow{\text{realloc}} \text{GUTI}_2 \dots$$

```
   [ UNTRACKED ]
         │
         │ ev == 'identity' && supi == TARGET
         ▼
   ┌───────────────────────────────────────────────┐
   │ STATE 1: ACTIVE SESSION                       │
   │   - ran = current_ran                         │
   │   - track cell handovers: visited_cells.add() │
   │   - track identity rotation:                  │
   │       ev == 'realloc' -> current_guti = new   │
   └───────────────────────────────────────────────┘
         │
         │ ev == 'release'
         ▼
   ┌───────────────────────────────────────────────┐
   │ STATE 2: IDLE RESIDENCE                       │
   │   - current_ran = None                        │
   │   - retain current_guti in memory             │
   └───────────────────────────────────────────────┘
         │
         │ ev == 'service' && guti == current_guti
         ▼
   (Re-anchors to STATE 1 with new active ran handle)
```

### 3.3 Formal State Transition Rules

Let the state vector at event step $k$ be $\mathbf{S}_k = (\text{RAN}_k, \text{GUTI}_k, \mathcal{C}_k)$ where $\mathcal{C}_k$ is the set of unique visited cells:

1. **Anchor**: If `event == 'identity'` and `supi(e_k) == TARGET`:
   - Set `current_ran = ran(e_k)`
2. **Mobility (Handover)**: If `ran(e_k) == current_ran` and `event == 'handover'`:
   - Update `visited_cells.add(to_cell)`
3. **Identity Refresh**: If `ran(e_k) == current_ran` and `event == 'realloc'`:
   - Update `current_guti = newguti(e_k)`
4. **Session Release**: If `ran(e_k) == current_ran` and `event == 'release'`:
   - Set `current_ran = None` (retain `current_guti`)
5. **Re-attachment**: If `current_ran is None`, `event == 'service'`, and `guti(e_k) == current_guti`:
   - Restore `current_ran = ran(e_k)` and record new cell in route

---

## 4. Algorithmic Breakdown

1. **PCAP Log Dissection**: Parse structured syslog `NGEV` events transported over UDP.
2. **Anchor Ingestion**: Detect event `identity` with the target SUPI string; assign initial `current_ran`.
3. **Event Loop Evaluation**:
   - Check if incoming event belongs to `current_ran`.
   - Update temporary identifier upon `realloc`.
   - Register target cell ID in unique cell hash set upon `handover`.
   - Transition to idle state upon `release`.
   - Re-acquire `current_ran` upon matching `service` request.
4. **Final Forensic Aggregation**:
   - Count cardinality of unique cell set: $|\mathcal{C}|$.
   - Extract hexadecimal suffix of the final temporary GUTI.
   - Format flag: `RFCTF{<guti_suffix>_<cell_count>}`.

---

## 5. Dataset & Data Schema

| File | Description | Events | Size | LFS |
|------|-------------|--------|------|-----|
| `data/mobility_events.pcap` | Captured AMF N2 NGAP mobility syslog trace | ~1,100 | ~180 KB | Yes |

### Event Types Dissected
- `identity`: Initial UE registration containing permanent SUPI and initial `ran` handle.
- `handover`: Radio handover event between source cell and destination cell (`to`).
- `realloc`: 5G-GUTI reallocation issuing a refreshed temporary identifier (`newguti`).
- `release`: Connection release tearing down the active radio connection session.
- `service`: Service request event presenting stored GUTI to re-establish user plane.

---

## 6. Repository Structure

```
5g-guti-mobility-tracking/
├── .gitattributes             # Git LFS tracking for *.pcap
├── .gitignore
├── LICENSE                    # MIT License
├── README.md                  # Protocol specification & FSM theory
├── requirements.txt           # Minimal dependencies
├── solve.py                   # Automated Chained FSM mobility tracker
└── data/
    └── mobility_events.pcap   # Captured AMF mobility event trace (LFS)
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
git clone https://github.com/<your-username>/5g-guti-mobility-tracking.git
cd 5g-guti-mobility-tracking
git lfs pull
python solve.py
```

---

## 8. Expected Output

```
[+] Parsing AMF mobility events from data/mobility_events.pcap...
[+] Target SUPI located in Initial Registration:
    Session Anchor: ran = 00739 | Registered Cell: NR-0E520
[+] Tracking state transitions:
    -> Handover: NR-0E520 -> NR-0E521
    -> Identity Reallocation: new GUTI = 404-86-bfc596c9
    -> Session Release: ran 00739 closed (Subscriber Idle)
    -> Re-connection: Service request with GUTI 404-86-bfc596c9 on ran = 00509
    -> Handover: NR-0E521 -> NR-0B115
    -> Handover: NR-0B115 -> NR-0A207
    -> Handover: NR-0A207 -> NR-0D410
    -> Identity Reallocation: new GUTI = 404-86-c7d3136f
    -> Session Release: ran 00509 closed
    -> Re-connection: Service request with GUTI 404-86-c7d3136f on ran = 00509
    -> Identity Reallocation: new GUTI = 404-86-3f034f96
    -> Session Release: ran 00509 closed
    -> Re-connection: Service request with GUTI 404-86-3f034f96 on ran = 00412
    -> Handover: NR-0D410 -> NR-0D411
    -> Identity Reallocation: new GUTI = 404-86-6b5a87ba
    -> Session Release: ran 00412 closed

============================================================
MOBILITY FORENSIC RESULTS:
  Final 5G-GUTI: 404-86-6b5a87ba
  Final GUTI Suffix: 6b5a87ba
  Unique Cells Visited: {'NR-0A207', 'NR-0B115', 'NR-0E520', 'NR-0D411', 'NR-0D410', 'NR-0E521'}
  Total Distinct Cell Sites: 6
  Flag: RFCTF{6b5a87ba_6}
============================================================
```

---

## 9. Further Reading

- 3GPP TS 23.501: *System architecture for the 5G System (5GS)* (Section 5.9.4: 5G-GUTI).
- 3GPP TS 23.502: *Procedures for the 5G System (5GS)* (Section 4.2.2: Registration Procedures).
- Arapoglou, P. D., et al. (2021). *5G Security and Privacy: A Comprehensive Survey of 3GPP Specifications*. IEEE Access.
