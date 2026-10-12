import pandas as pd
import numpy as np
from scipy.optimize import minimize
import itertools

sensors = pd.read_csv('sensors.csv')
sensor_pos = {row['sensor']: (row['north_m'], row['east_m']) for _, row in sensors.iterrows()}
sensor_names = sorted(list(sensor_pos.keys()))

arrivals = pd.read_csv('arrivals.csv')
c = 299792458.0

bursts = arrivals.groupby('burst_id')

def get_distance(pos1, pos2):
    return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

results = []

for subset in itertools.combinations(sensor_names, 4):
    subset = list(subset)
    ref = subset[0]
    
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

    best_for_subset = float('inf')
    best_pos_for_subset = None
    
    # Grid search for initial guesses
    for n0 in np.linspace(-20000, 20000, 5):
        for e0 in np.linspace(-20000, 20000, 5):
            res = minimize(error_func, [n0, e0], method='Nelder-Mead')
            if res.fun < best_for_subset:
                best_for_subset = res.fun
                best_pos_for_subset = res.x
                
    rms_error = np.sqrt(best_for_subset / 3) * c
    results.append((rms_error, subset, best_pos_for_subset))
    
results.sort(key=lambda x: x[0])

for res in results:
    err, sub, pos = res
    print(f"Subset {sub}: Error = {err:.2f} m, Pos = ({pos[0]:.0f}, {pos[1]:.0f})")
