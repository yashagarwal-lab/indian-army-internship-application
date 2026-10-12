import struct
import sys

def parse_pcap(filename):
    with open(filename, 'rb') as f:
        global_header = f.read(24)
        if not global_header:
            return
            
        frame_num = 1
        while True:
            pkt_header = f.read(16)
            if len(pkt_header) < 16:
                break
            
            ts_sec, ts_usec, incl_len, orig_len = struct.unpack('<IIII', pkt_header)
            pkt_data = f.read(incl_len)
            
            # search for NASX magic
            idx = pkt_data.find(b'NASX')
            if idx != -1:
                nas_data = pkt_data[idx:]
                if len(nas_data) >= 16:
                    yield frame_num, nas_data
            
            frame_num += 1

class NASMsg:
    def __init__(self, frame_num, data):
        self.frame_num = frame_num
        self.magic = data[0:4]
        self.version = data[4]
        self.direction = data[5] # 0=UL, 1=DL
        self.ue_id = struct.unpack(">H", data[6:8])[0]
        self.msg_type = data[8]
        self.seq_num = data[9]
        self.mac = data[10:14]
        self.body_len = struct.unpack(">H", data[14:16])[0]
        self.body = data[16:16+self.body_len]
        
    def __str__(self):
        dir_str = "UL" if self.direction == 0 else "DL"
        return f"Frame {self.frame_num:3d} | UE {self.ue_id:4d} | {dir_str} | Type 0x{self.msg_type:02X} | Seq {self.seq_num:3d}"

messages = []
for frame_num, data in parse_pcap("nas_signalling.pcap"):
    messages.append(NASMsg(frame_num, data))

for m in messages:
    if m.ue_id == 4217:
        print(m)
