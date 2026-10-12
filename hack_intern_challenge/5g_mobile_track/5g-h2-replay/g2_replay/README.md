# 5G-H2 — Replay or Retransmit

**Exercise PARCHAM · Serial LOHA JAAL · private 5G network, Kandla port**

A NAS signalling tap from the terminal network's AMF. Eight subscribers — gate
handhelds and crane controllers — register, authenticate and request service over
about three minutes.

One of the uplink messages in this capture was **not sent by the subscriber it
claims to come from**. The exercise red cell captured it earlier in the serial and
injected it later. Find it.

## The data

`nas_signalling.pcap` — each packet is a UDP datagram (port 9999) carrying one
exported NAS message in this format:

| offset | size | field |
|---|---|---|
| 0 | 4 | ASCII magic `NASX` |
| 4 | 1 | version (1) |
| 5 | 1 | direction: `0` = uplink (subscriber → network), `1` = downlink |
| 6 | 2 | AMF UE NGAP ID, big-endian — identifies the subscriber |
| 8 | 1 | NAS message type |
| 9 | 1 | NAS sequence number |
| 10 | 4 | integrity MAC (truncated to 4 bytes) |
| 14 | 2 | body length, big-endian |
| 16 | *len* | message body |

Message types present: `0x41` Registration Request, `0x42` Registration Accept,
`0x4D` Authentication Request, `0x4E` Authentication Response,
`0x5D` Security Mode Command, `0x5E` Security Mode Complete,
`0x4C` Service Request, `0x54` Configuration Update.

Uplink NAS sequence numbers increment per subscriber, per uplink message.

## Things that will not help you

- **The source address.** The injection was made through the same gNB as all the
  legitimate traffic. Every uplink packet in this file has an identical 5-tuple.
- **The integrity MAC.** The replayed message carries the original subscriber's
  own genuine MAC, because it *is* the original message. It verifies correctly.
- **Finding duplicates.** There is more than one duplicated uplink message in
  this capture, and most of them are innocent: a handheld that does not get a
  response to an uplink NAS message legitimately retransmits it, byte for byte,
  and coverage inside a container stack is poor.
- **The size of the time gap.** One of the legitimate retransmissions is delayed
  longer than the injected message was.

## Your task

Identify the single injected message. To tell it apart from a legitimate
retransmission you will need to reason about what the subscriber's NAS state was
at the moment each duplicate arrived — whether the message was still current, or
whether that subscriber had already moved on.

Report the **frame number** of the injected packet (as numbered by tshark, i.e.
1-based position in the file) and the **AMF UE NGAP ID** of the affected
subscriber, in decimal.

## Flag format

```
RFCTF{<frame number>_<AMF UE NGAP ID>}
```

For example `RFCTF{412_4203}`.
