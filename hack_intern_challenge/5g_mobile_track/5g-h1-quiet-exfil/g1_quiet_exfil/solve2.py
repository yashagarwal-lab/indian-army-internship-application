from scapy.all import rdpcap
from scapy.contrib.gtp import GTP_U_Header
from scapy.all import IP, UDP

pkts = rdpcap("n3_userplane.pcap")

# Group packets by flow
flows = {}

for p in pkts:
    if GTP_U_Header in p:
        inner = p[GTP_U_Header].payload
        if IP in inner:
            ip = inner[IP]
            if UDP in ip:
                udp = ip[UDP]
                flow_key = (ip.src, ip.dst, udp.sport, udp.dport)
                # Wait, some flows might have varying source ports, maybe group by src/dst IP?
                # Let's just group by src/dst IP and maybe dport.
                key = (ip.src, ip.dst, udp.dport)
                if key not in flows:
                    flows[key] = []
                flows[key].append((ip, udp))

print(f"Found {len(flows)} flows based on src, dst, dport.")

# Look for D E A D in 4-bit fields in consecutive packets
def find_dead(packets):
    # Let's extract sequences for various fields
    # IP TOS (8 bits -> 2 nibbles)
    # IP ID (16 bits -> 4 nibbles)
    # IP Flags (3 bits) + Frag Offset (13 bits) -> 4 nibbles
    # IP TTL (8 bits -> 2 nibbles)
    # UDP sport (16 bits)
    # UDP dport (16 bits)
    # UDP len (16 bits)
    # UDP chksum (16 bits)
    
    # Let's just look at 4-bit sliding windows of all header fields, or specific ones.
    # What are the likely 4-bit fields?
    # - IP TOS / DSCP (6 bits) + ECN (2 bits) -> maybe one nibble is used?
    # - IP ID is often used.
    # - UDP source port might be varying but usually is random.
    # - TTL is usually constant.
    # Let's collect a sequence of nibbles for each position
    
    # To be general, let's extract all header bytes
    for i in range(28): # 20 bytes IP + 8 bytes UDP
        nibbles_high = []
        nibbles_low = []
        for ip, udp in packets:
            header = bytes(ip)[:20] + bytes(udp)[:8]
            if i < len(header):
                b = header[i]
                nibbles_high.append(b >> 4)
                nibbles_low.append(b & 0xf)
        
        # Check if D, E, A, D is in nibbles_high or nibbles_low
        seq1 = ''.join(f'{n:x}' for n in nibbles_high)
        seq2 = ''.join(f'{n:x}' for n in nibbles_low)
        
        if 'dead' in seq1:
            print(f"Found 'dead' in high nibble of byte {i} in flow")
            return (i, 'high', seq1)
        if 'dead' in seq2:
            print(f"Found 'dead' in low nibble of byte {i} in flow")
            return (i, 'low', seq2)
            
    return None

for key, packets in flows.items():
    if len(packets) < 10:
        continue
    res = find_dead(packets)
    if res:
        print(f"Flow {key} has DEAD sequence!")
        i, pos, seq = res
        print(f"Byte index: {i}, Position: {pos}")
        
        # Decode the message
        # Sync nibbles D E A D establish where bytes begin.
        # Two nibbles make one byte, most significant first.
        # The channel repeats its message.
        
        idx = seq.find('dead')
        # Start reading after 'dead'
        data_nibbles = seq[idx+4:]
        
        msg = ""
        for j in range(0, len(data_nibbles)-1, 2):
            b = int(data_nibbles[j:j+2], 16)
            if 32 <= b <= 126:
                msg += chr(b)
            else:
                msg += '.'
        print(f"Decoded: {msg}")

