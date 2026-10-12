import numpy as np
import matplotlib.pyplot as plt

z = np.load("traces.npz")
traces = z["traces"]

plt.figure(figsize=(12, 6))
for i in range(5):
    plt.plot(traces[i] + i*2000, label=f"Trace {i}")
plt.legend()
plt.savefig("traces_plot.png")
