import numpy as np

z = np.load("aligned.npz")
traces = z["traces"].astype(np.float32)

# Check variance of aligned traces
v = np.var(traces, axis=0)

import matplotlib.pyplot as plt
plt.plot(v)
plt.title("Variance of Aligned Traces")
plt.savefig("aligned_variance.png")

# Also print the max variance in the first 150 samples (which should cover the burst)
print("Mean variance in first 150 samples:", np.mean(v[:150]))
print("Max variance in first 150 samples:", np.max(v[:150]))
