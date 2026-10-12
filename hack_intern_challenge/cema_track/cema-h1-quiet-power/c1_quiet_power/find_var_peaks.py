import numpy as np

z = np.load("aligned.npz")
traces = z["traces"].astype(np.float32)

v = np.var(traces, axis=0)

# Find peaks in variance after the initial burst (say after sample 150)
v_after_burst = v[150:]
peaks = []
for i in range(1, len(v_after_burst)-1):
    if v_after_burst[i] > v_after_burst[i-1] and v_after_burst[i] > v_after_burst[i+1]:
        if v_after_burst[i] > np.mean(v_after_burst) + 2*np.std(v_after_burst):
            peaks.append((v_after_burst[i], i + 150))

peaks.sort(reverse=True)
for val, idx in peaks[:20]:
    print(f"Time {idx:3d}: variance {val:.2f}")
