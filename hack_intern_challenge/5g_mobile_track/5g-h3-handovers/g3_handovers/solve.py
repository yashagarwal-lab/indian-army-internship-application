import struct

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
            
            # Find NGEV
            idx = pkt_data.find(b'NGEV|')
            if idx != -1:
                yield pkt_data[idx:].decode('ascii', errors='ignore')
            frame_num += 1

events = list(parse_pcap('mobility_events.pcap'))

parsed_events = []
for ev_str in events:
    parts = ev_str.strip().split('|')
    ev_dict = {}
    for part in parts:
        if '=' in part:
            k, v = part.split('=', 1)
            ev_dict[k] = v
    parsed_events.append(ev_dict)

TARGET_SUPI = "imsi-404861234591203"

current_ran = None
current_guti = None
visited_cells = set()
active_ran_cells = {}

for ev in parsed_events:
    ran = ev.get('ran')
    
    if ev.get('ev') == 'register' or ev.get('ev') == 'service':
        if ran:
            active_ran_cells[ran] = ev.get('cell')
            
    if ev.get('ev') == 'identity' and ev.get('supi') == TARGET_SUPI:
        current_ran = ran
        print(f"Target found on initial ran: {current_ran}")
        if current_ran in active_ran_cells:
            cell = active_ran_cells[current_ran]
            visited_cells.add(cell)
            print(f"Registered on cell (from previous event): {cell}")
        
    elif current_ran is not None and ran == current_ran:
        if ev.get('ev') == 'realloc':
            current_guti = ev.get('newguti')
            print(f"New GUTI allocated: {current_guti}")
        elif ev.get('ev') == 'handover':
            to_cell = ev.get('to')
            visited_cells.add(to_cell)
            print(f"Handover to cell: {to_cell}")
        elif ev.get('ev') == 'release':
            print(f"Connection on ran {current_ran} released. Waiting for GUTI: {current_guti}")
            current_ran = None
            
    elif current_ran is None and current_guti is not None:
        if ev.get('ev') == 'service' and ev.get('guti') == current_guti:
            current_ran = ran
            cell = ev.get('cell')
            visited_cells.add(cell)
            print(f"Target reconnected with GUTI on ran: {current_ran}, cell: {cell}")
        elif ev.get('ev') == 'register' and ev.get('guti') == current_guti:
            # Wait, what if it's a register with guti? The instructions say register has suci. 
            pass

print("\n--- Results ---")
print(f"Final GUTI: {current_guti}")
if current_guti:
    suffix = current_guti.split('-')[-1]
    print(f"Final GUTI suffix: {suffix}")
print(f"Visited cells: {visited_cells}")
print(f"Number of visited cells: {len(visited_cells)}")
if current_guti:
    print(f"Flag: RFCTF{{{suffix}_{len(visited_cells)}}}")

