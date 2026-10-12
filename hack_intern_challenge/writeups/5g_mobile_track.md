# 5G Mobile Track Writeup

### 5G-H1: The Quiet Exfil

**Goal:**
Somebody inside a private 5G network was sneaking data out. The payloads were completely clean, so my job was to figure out how they were sneaking the data out and recover the hidden flag.

**Thought process:**
Since the data wasn't in the message payload, it had to be hidden somewhere in the packet headers. This is a steganography technique. The challenge hint mentioned they were sneaking out 4 bits of data per packet (a nibble) and using a sync word: `D E A D`. 

I wrote a Python script using Scapy to read the PCAP file. Instead of looking at the payloads, I looked at the IP and UDP headers. I grabbed every byte from the headers, chopped them in half to look at the 4-bit nibbles, and searched for the `dead` hex sequence. Once my script found `dead` hiding in the lower nibbles of a specific network flow, it grabbed the rest of the nibbles after it, paired them up into 8-bit bytes, converted them to ASCII, and printed the flag.

**What I learned:**
This challenge was really cool because it showed me that you can't just trust payload inspection.

***

### 5G-H2: Replay

**Goal:**
An attacker intercepted a 5G uplink NAS message and replayed it. However, the network also does legitimate retransmissions. My goal was to find the single malicious packet and report its frame number and the affected AMF UE NGAP ID.

**Thought process:**
Legitimate network retransmissions usually happen really fast after a packet gets dropped. A malicious replay usually happens much later, long after the phone's connection state or sequence number has moved on. 

I wrote a script to unpack the binary custom `NASX` headers over UDP to extract the UE ID, Message Type, and Sequence Number. I printed out all the messages for the specific UE to see its timeline. By looking at the duplicate sequence numbers, it was easy to spot the fake one because the time gap was way bigger than a normal network retry, and the connection had already advanced past that state.

**What I learned:**
This showed me how important sequence numbers and timing analysis are for spotting replay attacks in cellular networks.

***

### 5G-H3: Needle in the Handovers

**Goal:**
Track a single subscriber across a port's 5G network using a log of mobility events, figure out how many unique cells they visited, and find their final 5G-GUTI.

**Thought process:**
5G networks only send the permanent ID (SUPI) once for privacy. After that, they constantly issue new temporary IDs (GUTIs) to track the user. The log file used a `ran` ID to track a connection session, but `ran` IDs get recycled, so I couldn't just grep for it.

I had to build a state machine in Python. First, I found the initial `identity` event for the target SUPI and tracked that `ran` ID. Every time a `handover` happened, I logged the cell. When a `realloc` event happened, I saved the new GUTI. When the `release` event triggered, I cleared the `ran` ID and waited for the user to reconnect. When a new `service` request popped up with that saved GUTI, I grabbed the new `ran` ID and kept tracking. I just let the loop run to the end of the file to get the final cell count and GUTI.

**What I learned:**
This was a great lesson on how 5G handles privacy through temporary identities and how stateful tracking works.
