times = [
    (180, 0, 0x49), (23, 0, 0x6d), (488, 0, 0xfe), (433, 0, 0xdf), (504, 0, 0xc7),
    (347, 1, 0x72), (319, 1, 0x71), (640, 1, 0x23), (368, 1, 0x7b), (86, 1, 0xf4),
    (328, 2, 0x73), (206, 2, 0x1d), (165, 2, 0xa0), (204, 2, 0x8b), (261, 2, 0x45),
    (627, 3, 0xee), (59, 3, 0x13), (474, 3, 0xc8), (514, 3, 0x35), (400, 3, 0x87),
    (284, 4, 0x46), (575, 4, 0x07), (709, 4, 0xb4), (689, 4, 0x06), (320, 4, 0x5d),
    (554, 5, 0x70), (312, 5, 0x75), (603, 5, 0x5e), (516, 5, 0xc1), (677, 5, 0xcf),
    (553, 6, 0x38), (158, 6, 0xbe), (495, 6, 0x3e), (576, 6, 0x01), (633, 6, 0x41),
    (234, 7, 0xdd), (101, 7, 0xe9), (19, 7, 0xd6), (40, 7, 0x52), (211, 7, 0x82),
    (356, 8, 0x2b), (444, 8, 0xc4), (688, 8, 0x21), (627, 8, 0x44), (443, 8, 0xc1),
    (253, 9, 0x2e), (668, 9, 0x6f), (437, 9, 0x05), (17, 9, 0xc1), (250, 9, 0x91),
    (498, 10, 0x81), (216, 10, 0x5c), (452, 10, 0xd8), (243, 10, 0x8b), (714, 10, 0xa9),
    (395, 11, 0x4f), (644, 11, 0x1b), (243, 11, 0x09), (320, 11, 0x67), (520, 11, 0x50),
    (564, 12, 0x57), (451, 12, 0xfa), (294, 12, 0xcd), (330, 12, 0x07), (211, 12, 0x2b),
    (235, 13, 0x50), (498, 13, 0x61), (540, 13, 0x2c), (452, 13, 0xc7), (107, 13, 0x1a),
    (34, 14, 0xa9), (225, 14, 0x3b), (347, 14, 0xbd), (297, 14, 0xf9), (420, 14, 0xd0),
    (594, 15, 0x5c), (372, 15, 0x2f), (0, 15, 0x2d), (238, 15, 0x3b), (377, 15, 0x0f)
]

times.sort()

# Let's see if we can find 16 points with almost constant difference
best_seq = []
best_var = 1e9

for i in range(len(times)):
    for j in range(i+1, len(times)):
        t1 = times[i][0]
        t2 = times[j][0]
        diff = t2 - t1
        if diff < 10 or diff > 100:
            continue
            
        seq = [times[i], times[j]]
        expected_next = t2 + diff
        
        while len(seq) < 16:
            # find the closest time
            closest = None
            min_err = 1e9
            for k in range(j+1, len(times)):
                err = abs(times[k][0] - expected_next)
                if err < min_err:
                    min_err = err
                    closest = times[k]
            
            if min_err > 15:
                break
                
            seq.append(closest)
            expected_next = closest[0] + diff
            j = times.index(closest)
            
        if len(seq) == 16:
            # check if they have unique bytes
            bytes_in_seq = set([x[1] for x in seq])
            if len(bytes_in_seq) == 16:
                diffs = [seq[x+1][0] - seq[x][0] for x in range(15)]
                var = np.var(diffs)
                if var < best_var:
                    best_var = var
                    best_seq = seq

if best_seq:
    print("Found sequence:")
    for t, b, guess in best_seq:
        print(f"t={t:3d}: Byte {b:2d} -> {guess:02x}")
    
    key = [0]*16
    for t, b, guess in best_seq:
        key[b] = guess
        
    hex_key = "".join(f"{x:02x}" for x in key)
    print(f"\nIntern_Pro_Max{{{hex_key}}}")
else:
    print("No sequence found!")
