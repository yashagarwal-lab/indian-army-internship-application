# 5G-H1 — The Quiet Exfil

**Exercise PARCHAM · Serial LOHA JAAL · private 5G network, Kandla port**

The captive 5G network serving the container terminal at Kandla carries crane
telemetry, gate automation and handheld traffic. During the exercise an insider
serial was run on it: one subscriber was tasked to move data off the estate
without tripping the terminal's monitoring.

This capture is from the N3 interface — GTP-U user plane between a gNB and the
UPF. The terminal's own compliance team has already reviewed the payloads and
found nothing actionable.

## The data

`n3_userplane.pcap` — 1500 packets, all GTP-U encapsulated (TEID `0x3F2A1B`),
carrying ordinary inner IPv4/UDP traffic for several subscribers.

```python
from scapy.all import rdpcap
from scapy.contrib.gtp import GTP_U_Header
from scapy.all import IP, UDP, Raw
pkts = rdpcap("n3_userplane.pcap")
inner = pkts[0][GTP_U_Header].payload     # the inner IP packet
```

`tshark -r n3_userplane.pcap` works fine too; GTP-U is dissected natively.

## What we know

- The exfiltration channel carries **four bits per packet**.
- The bit stream is **self-synchronising**: the data is preceded by the sync
  nibbles `D E A D`, which establishes where bytes begin. Two nibbles make one
  byte, most significant first, and the result is ASCII.
- The channel repeats its message, so you do not need every packet to read it.

## What we do not know

Which packets carry it, and what carries the four bits.

## Your task

Recover the exfiltrated message.

Compliance was right about the payloads: they really are clean. Every byte being
carried in this capture is innocuous, and the one thing in there that looks like a
secret is not one. If your approach is to search the contents of packets, you will
spend a long time confirming that.

What this capture does have is a dozen distinct inner flows, and one of them does
not behave like port traffic.

## Flag format

```
RFCTF{...}
```
