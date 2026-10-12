import numpy as np

z = np.load("traces.npz")
traces = z["traces"]

print("Traces shape:", traces.shape)
print("Data type:", traces.dtype)

# Find a good template for the burst
ref = traces[0]

import matplotlib.pyplot as plt

plt.plot(ref)
plt.savefig("ref.png")

# Let's write a small script to find alignments
shifts = []
template = ref[0:150]
for i in range(len(traces)):
    c = np.correlate(traces[i], template, mode='valid')
    shifts.append(np.argmax(c))

print("Unique shifts:", np.unique(shifts))
