"""
Inspect the trace structure to understand what the burst looks like
and where the encryption activity is.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

z = np.load("traces.npz")
raw = z["traces"].astype(np.float64)
pts = z["plaintexts"]
N, L = raw.shape

# Plot first 10 traces and mean
fig, axes = plt.subplots(3, 1, figsize=(14, 10))

# Raw first few traces
ax = axes[0]
for i in range(5):
    ax.plot(raw[i], alpha=0.5, lw=0.5, label=f"trace {i}")
ax.plot(raw.mean(axis=0), 'k-', lw=1.5, label='mean')
ax.set_title("First 5 raw traces + mean")
ax.set_xlabel("Sample")
ax.legend(fontsize=7)

# Variance across traces
ax = axes[1]
ax.plot(raw.var(axis=0), 'b-', lw=0.8)
ax.set_title("Variance across 2000 traces (high = data-dependent, low = repeatable)")
ax.set_xlabel("Sample")
ax.set_ylabel("Variance")

# Mean of absolute values
ax = axes[2]
ax.plot(np.abs(raw).mean(axis=0), 'r-', lw=0.8, label='mean |trace|')
ax.plot(raw.std(axis=0), 'b-', lw=0.8, label='std')
ax.set_title("Mean |amplitude| and std")
ax.set_xlabel("Sample")
ax.legend()

plt.tight_layout()
plt.savefig("trace_structure.png", dpi=100)
print("Saved trace_structure.png")

# Also: look at the first 150 samples of 5 raw traces
print("\nFirst 150 samples of first 5 traces:")
for i in range(5):
    print(f"Trace {i}: max_abs_pos={np.argmax(np.abs(raw[i]))} max={np.max(np.abs(raw[i])):.0f}")
    # Find the burst: look for large derivative
    d = np.abs(np.diff(raw[i]))
    top5 = np.argsort(d)[-5:][::-1]
    print(f"         Top5 derivative positions: {sorted(top5)}")

# Find the "repeatable burst" by looking at where the mean is high AND variance is low
mean_abs = np.abs(raw.mean(axis=0))
var_trace = raw.var(axis=0)
# Normalize
ratio = mean_abs / (var_trace + 1e-6)
print(f"\nBurst-detection ratio (high mean/var):")
top10 = np.argsort(ratio)[-10:][::-1]
print(f"Top10 positions: {sorted(top10)}")

# Quick look at where the mean trace has peaks
mean_trace = raw.mean(axis=0)
print(f"\nMean trace range: {mean_trace.min():.1f} to {mean_trace.max():.1f}")
print(f"Mean trace argmin: {mean_trace.argmin()}, argmax: {mean_trace.argmax()}")
