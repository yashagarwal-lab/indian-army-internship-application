import numpy as np

z = np.load("traces.npz")
plaintexts = z["plaintexts"]

for b in range(16):
    print(f"Byte {b}: min={np.min(plaintexts[:, b])}, max={np.max(plaintexts[:, b])}, unique={len(np.unique(plaintexts[:, b]))}")

# Check correlation between plaintexts
import itertools
for i, j in itertools.combinations(range(16), 2):
    if np.array_equal(plaintexts[:, i], plaintexts[:, j]):
        print(f"Byte {i} and Byte {j} are identical!")
    else:
        # Check if they are linearly correlated
        c = np.corrcoef(plaintexts[:, i], plaintexts[:, j])[0, 1]
        if abs(c) > 0.5:
            print(f"Byte {i} and Byte {j} are highly correlated (c={c:.2f})!")

