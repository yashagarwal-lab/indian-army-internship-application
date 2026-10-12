import numpy as np

z = np.load("traces.npz")
traces = z["traces"]
plaintexts = z["plaintexts"]

ref = traces[0]
peak_0 = np.argmax(np.abs(np.diff(ref)))

template = ref[peak_0 - 10 : peak_0 + 20]

peaks = []
for i in range(len(traces)):
    window = traces[i][:150]
    corr = np.correlate(window, template, mode='valid')
    best_start = np.argmax(corr)
    peak_i = best_start + 10
    peaks.append(peak_i)

min_peak = np.min(peaks)
max_peak = np.max(peaks)
print(f"Min peak: {min_peak}, Max peak: {max_peak}")

# We want the peak to be at index `min_peak` for all traces.
# So for trace i, we start extracting at `peaks[i] - min_peak`.
offset = min_peak
length = 800 - max_peak + min_peak
aligned_traces = []

for i in range(len(traces)):
    start = peaks[i] - min_peak
    end = start + length
    aligned_traces.append(traces[i][start:end])

aligned_traces = np.array(aligned_traces)
print("Aligned traces shape:", aligned_traces.shape)

np.savez("aligned.npz", traces=aligned_traces, plaintexts=plaintexts)
