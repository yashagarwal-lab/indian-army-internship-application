from scapy.all import rdpcap
from scapy.contrib.gtp import GTP_U_Header
from scapy.all import IP, UDP, Raw
from collections import Counter

pkts = rdpcap("n3_userplane.pcap")

flows = Counter()

for p in pkts:
    if GTP_U_Header in p:
        inner = p[GTP_U_Header].payload
        if IP in inner:
            ip = inner[IP]
            if UDP in ip:
                udp = ip[UDP]
                flow = (ip.src, ip.dst, udp.sport, udp.dport)
                flows[flow] += 1

for f, count in flows.most_common():
    print(f"{f}: {count}")
