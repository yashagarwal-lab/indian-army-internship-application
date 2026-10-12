import numpy as np

z = np.load("traces.npz")
traces = z["traces"]
plaintexts = z["plaintexts"]

# Let's find the burst using the peak derivative
# The burst is a strong, repeatable activity.
burst_peaks = []
for t in traces:
    # Use sum of absolute differences over a window or just argmax of derivative
    diff = np.abs(np.diff(t))
    peak = np.argmax(diff)
    burst_peaks.append(peak)

# Let's print the first 10 peaks and some stats
print("First 10 peaks:", burst_peaks[:10])
print("Min peak:", np.min(burst_peaks))
print("Max peak:", np.max(burst_peaks))
print("Unique peaks count:", len(np.unique(burst_peaks)))
