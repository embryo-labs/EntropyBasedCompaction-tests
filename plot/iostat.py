#!/usr/bin/env python3
import sys
if len(sys.argv) != 3:
	print('Usage: ' + sys.argv[0] + ' dir mean-step')
	exit()
d = sys.argv[1]
mean_step = int(sys.argv[2])

import os
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# Paper specific settings
SINGLE_COL_WIDTH = 8.5
DOUBLE_COL_WIDTH = 17.8
def cm_to_inch(value):
    return value/2.54

mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Linux Libertine O'],
})
plt.rcParams['axes.unicode_minus'] = False

def read_table(file):
    iostat_raw = pd.read_table(file, sep='\s+')
    iostat_raw['Time(Seconds)'] = (iostat_raw['Timestamp(ns)'] - iostat_raw['Timestamp(ns)'][0]) / 1e9
    iostat = iostat_raw[['r/s', 'w/s', 'rkB/s', 'wkB/s']].groupby(iostat_raw.index // mean_step).mean()
    iostat['Time(Seconds)'] = iostat_raw['Time(Seconds)'].groupby(iostat_raw.index // mean_step).first()
    return iostat
iostat = read_table(d + '/iostat.txt')

plot_dir = d + '/plot'
if not os.path.exists(plot_dir):
	os.system('mkdir -p ' + plot_dir)

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
ax = plt.gca()
plt.plot(iostat['Time(Seconds)'], iostat['r/s'], linewidth=0.5)
plt.plot(iostat['Time(Seconds)'], iostat['w/s'], linewidth=0.5)
plt.legend(['r/s', 'w/s'], fontsize=8)
plt.xlabel('Time (Seconds)', fontsize=8)
pdf_path = plot_dir + '/tps.pdf'
plt.savefig(pdf_path)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
	plt.show()

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
ax = plt.gca()
plt.plot(iostat['Time(Seconds)'], iostat['rkB/s'] * 1024 / 1e6, linewidth=0.5)
plt.plot(iostat['Time(Seconds)'], iostat['wkB/s'] * 1024 / 1e6, linewidth=0.5)
plt.legend(['read', 'write'], fontsize=8)
plt.xlabel('Time (Seconds)', fontsize=8)
plt.ylabel('Throughput (MB/s)', fontsize=8)
pdf_path = plot_dir + '/throughput.pdf'
plt.savefig(pdf_path)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
	plt.show()
