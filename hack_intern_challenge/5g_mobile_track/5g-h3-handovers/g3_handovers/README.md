# 5G-H3 — Needle in the Handovers

**Exercise PARCHAM · Serial LOHA JAAL · private 5G network, Kandla port**

A mobility-event export from the terminal network's AMF covering about half an
hour across its twelve cells, with ten handsets active on the estate.

We are interested in exactly one subscriber — a handset the red cell booked onto
the network on an Indian test PLMN and then walked through the yard:

```
imsi-404861234591203
```

Exercise control wants to know where it went and what temporary identity it was
holding when the serial ended.

## The data

`mobility_events.pcap` — each packet is a UDP datagram (port 9801) whose payload
is a pipe-delimited ASCII record beginning with `NGEV`:

```
NGEV|ev=<type>|ran=<ran ue id>|<field>=<value>|...
```

Event types and their fields:

| `ev=` | meaning | fields |
|---|---|---|
| `register` | initial registration | `ran`, `suci`, `cell` |
| `identity` | identity response | `ran`, `supi` |
| `service` | service request on an existing registration | `ran`, `guti`, `cell` |
| `handover` | the subscriber moved cell | `ran`, `frm`, `to` |
| `realloc` | the network assigned a new 5G-GUTI | `ran`, `newguti` |
| `release` | the connection was torn down | `ran` |

## How identity works here, and why this is not a grep

The permanent identity (`supi`) appears **exactly once** in the entire capture.
Every event after that refers to the subscriber only by a temporary `guti`, and
the network **reallocates that GUTI on every connection** — which is the whole
purpose of a GUTI. To follow one subscriber you have to follow a chain: the GUTI
presented when a connection opens, and the new GUTI issued before that connection
is released, belong to the same person.

The obvious thing to link those two halves with is the `ran` id. Be careful. A
RAN UE ID identifies a *connection*, not a subscriber, and this network has a
small pool of them that it **recycles** — a busy terminal churns through
connections all shift. Each `ran` value in this file is used by several different
handsets at different times. Grouping events by `ran` across the whole capture
will join other people's movements onto your target's, and it will not look like
an error — it will just give you a bigger, wrong answer.

## Your task

Determine, for the subscriber above:

1. The **final 5G-GUTI** they held at the end of the capture. Report only the
   last part — the 8 hexadecimal characters after the second hyphen. (For a GUTI
   of `404-86-1a2b3c4d`, report `1a2b3c4d`.)
2. The **number of distinct cells** they were present in across the whole
   capture, counting the cell they started each connection in as well as every
   cell they were handed over to.

## Flag format

```
RFCTF{<final guti suffix>_<number of cells>}
```

For example `RFCTF{1a2b3c4d_5}`.
