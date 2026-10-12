import pandas as pd
import numpy as np
from scipy.optimize import minimize
import itertools

# Load sensors
sensors = pd.read_csv('sensors.csv')
sensor_pos = {row['sensor']: (row['north_m'], row['east_m']) for _, row in sensors.iterrows()}
sensor_names = sorted(list(sensor_pos.keys()))

# Load arrivals
arrivals = pd.read_csv('arrivals.csv')

# Speed of light
c = 299792458.0

# Group by burst_id
bursts = arrivals.groupby('burst_id')

# Calculate mean TDOA for each sensor relative to sensor A (or just mean pairwise TDOAs)
# Wait, let's just use a reference sensor, say sensor A.
# But what if sensor A is compromised? It doesn't matter for TDOA.
# Actually, let's just calculate the TDOA between all pairs, or just optimize over (n, e) and T_i.
# Since T_i is unknown, for a stationary drone, T_i = t_{i,j} - D_j/c.
# So t_{i,j} - t_{i,k} = (D_j - D_k)/c.
# This must hold for all i.
# Let's average the TDOA across all bursts to reduce noise.
tdoa = {}
for s in sensor_names:
    if s == 'A': continue
    # For each burst, get TOA for s and TOA for A
    diffs = []
    for name, group in bursts:
        t_A = group[group['sensor'] == 'A']['toa_s'].values
        t_s = group[group['sensor'] == s]['toa_s'].values
        if len(t_A) > 0 and len(t_s) > 0:
            diffs.append(t_s[0] - t_A[0])
    if diffs:
        tdoa[s] = np.mean(diffs)

def get_distance(pos1, pos2):
    return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

# We will try all combinations of 4 sensors
best_error = float('inf')
best_pos = None
best_subset = None

for subset in itertools.combinations(sensor_names, 4):
    subset = list(subset)
    
    # We want to find (n, e) that minimizes the squared error in TDOA
    # We don't have to use A as reference if A is not in subset.
    # Let's use subset[0] as reference.
    
    ref = subset[0]
    
    # Mean TDOAs relative to ref
    tdoa_ref = {}
    for s in subset[1:]:
        diffs = []
        for name, group in bursts:
            t_ref = group[group['sensor'] == ref]['toa_s'].values
            t_s = group[group['sensor'] == s]['toa_s'].values
            if len(t_ref) > 0 and len(t_s) > 0:
                diffs.append(t_s[0] - t_ref[0])
        tdoa_ref[s] = np.mean(diffs)
        
    def error_func(x):
        n, e = x
        err = 0
        d_ref = get_distance((n, e), sensor_pos[ref])
        for s in subset[1:]:
            d_s = get_distance((n, e), sensor_pos[s])
            expected_tdoa = (d_s - d_ref) / c
            err += (expected_tdoa - tdoa_ref[s])**2
        return err

    # Initial guess: centroid of the 4 sensors
    n0 = np.mean([sensor_pos[s][0] for s in subset])
    e0 = np.mean([sensor_pos[s][1] for s in subset])
    
    # We can also do multiple initial guesses to avoid local minima
    res = minimize(error_func, [n0, e0], method='Nelder-Mead')
    
    # RMS error in meters
    rms_error = np.sqrt(res.fun / 3) * c
    
    if rms_error < best_error:
        best_error = rms_error
        best_pos = res.x
        best_subset = subset

print(f"Best subset: {best_subset}")
print(f"Error (m): {best_error}")
print(f"Position (n, e): {best_pos[0]}, {best_pos[1]}")

compromised = [s for s in sensor_names if s not in best_subset]
print(f"Compromised sensors: {compromised}")

n_rounded = int(round(best_pos[0] / 10.0) * 10)
e_rounded = int(round(best_pos[1] / 10.0) * 10)
letters = "".join(sorted(compromised))

print(f"Flag: KST{{{n_rounded}_{e_rounded}_{letters}}}")
