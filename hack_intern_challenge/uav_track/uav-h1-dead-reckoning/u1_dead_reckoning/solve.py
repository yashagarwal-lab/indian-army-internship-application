import pandas as pd
import numpy as np
import math

imu = pd.read_csv('imu.csv')
gnss = pd.read_csv('gnss.csv')

dt = np.zeros(len(imu))
dt[1:] = imu['t_s'].values[1:] - imu['t_s'].values[:-1]
dt[0] = dt[1]

imu['vel_n'] = np.cumsum(imu['acc_n_mps2'] * dt)
imu['vel_e'] = np.cumsum(imu['acc_e_mps2'] * dt)

gnss_vel_n = gnss['vel_n_mps'].values
gnss_vel_e = gnss['vel_e_mps'].values

imu_vel_n_interp = np.interp(gnss['t_s'], imu['t_s'], imu['vel_n'])
imu_vel_e_interp = np.interp(gnss['t_s'], imu['t_s'], imu['vel_e'])

diff_vel_n = gnss_vel_n - imu_vel_n_interp
diff_vel_e = gnss_vel_e - imu_vel_e_interp

mask = gnss['t_s'] < 400
z_n = np.polyfit(gnss['t_s'][mask], diff_vel_n[mask], 1)
p_n = np.poly1d(z_n)
trend_n = p_n(gnss['t_s'])

z_e = np.polyfit(gnss['t_s'][mask], diff_vel_e[mask], 1)
p_e = np.poly1d(z_e)
trend_e = p_e(gnss['t_s'])

diff_vel_n_detrended = diff_vel_n - trend_n
diff_vel_e_detrended = diff_vel_e - trend_e

mask_baseline = (gnss['t_s'] >= 1000) & (gnss['t_s'] < 1140)
n_base = diff_vel_n_detrended[mask_baseline].mean()
e_base = diff_vel_e_detrended[mask_baseline].mean()

mask_plateau1 = (gnss['t_s'] >= 1200) & (gnss['t_s'] < 1400)
mask_plateau2 = (gnss['t_s'] >= 1400) & (gnss['t_s'] < 1600)
mask_plateau3 = (gnss['t_s'] >= 1600) & (gnss['t_s'] < 1800)

for m, name in [(mask_plateau1, '1200-1400'), (mask_plateau2, '1400-1600'), (mask_plateau3, '1600-1800')]:
    n_plat = diff_vel_n_detrended[m].mean() - n_base
    e_plat = diff_vel_e_detrended[m].mean() - e_base
    bearing = math.degrees(math.atan2(e_plat, n_plat))
    print(f"Plateau {name}: n={n_plat:.4f}, e={e_plat:.4f}, bearing={bearing:.2f}")

mask_all_plateau = (gnss['t_s'] >= 1200) & (gnss['t_s'] < 1800)
n_plat_all = diff_vel_n_detrended[mask_all_plateau].mean() - n_base
e_plat_all = diff_vel_e_detrended[mask_all_plateau].mean() - e_base
bearing_all = math.degrees(math.atan2(e_plat_all, n_plat_all))
print(f"All Plateau: n={n_plat_all:.4f}, e={e_plat_all:.4f}, bearing={bearing_all:.2f}")
