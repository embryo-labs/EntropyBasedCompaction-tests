#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
	print('Usage: ' + sys.argv[0] + ' dir')
	exit()
dir = sys.argv[1]
from_MB_s = 10
to_MB_s = 100

import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# Paper specific settings
SINGLE_COL_WIDTH = 8.5
DOUBLE_COL_WIDTH = 17.8
def cm_to_inch(value):
    return value/2.54

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Linux Libertine O'],
})
plt.rcParams['axes.unicode_minus'] = False

def draw(plot_version, name, ylabel, ylim = None):
    fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
    ax = plt.gca()
    plt.xlabel('Write (MB/s)', fontsize=8)
    plt.ylabel(ylabel, fontsize=8)
    plt.xticks(np.linspace(from_MB_s, to_MB_s, 10), fontsize=8)
    plt.yticks(fontsize=8)
    versions = []
    for ratio in [5, 10]:
        version = 'leveling' + str(ratio)
        plot_version(version)
        versions.append(version)
    for ratio in [2, 10]:
        version = 'tiering' + str(ratio)
        plot_version(version)
        versions.append(version)
    for version in ['rocksdb-tuned', 'universal', 'benefit-cost']:
        if os.path.exists(os.path.join(dir, version)):
            plot_version(version)
            versions.append(version)
    plt.yscale('log')
    plt.xlim((from_MB_s, to_MB_s))
    if ylim is not None:
        plt.ylim(ylim)
    plt.legend(versions, fontsize=8)
    pdf_path = os.path.join(dir, 'increasing-write-speed-' + name + '-avg-every-1p.pdf')
    plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
    print('Plot saved to ' + pdf_path)

def plot_num_sorted_runs(version):
    data_dir = os.path.join(dir, version)
    data = pd.read_csv(os.path.join(data_dir, 'report.csv'))
    max_secs_elapsed = data.iloc[-1]['secs_elapsed']
    data['write-speed'] = data['secs_elapsed'] / max_secs_elapsed * (to_MB_s - from_MB_s) + from_MB_s
    mean_step = len(data['write-speed']) / 100
    data = data[['write-speed', 'num-sorted-runs']].groupby(data.index // mean_step).mean()
    plt.plot(data['write-speed'], data['num-sorted-runs'])

draw(plot_num_sorted_runs, 'num-sorted-runs', '# of sorted runs', (1, 1000))

for op in ['prefix-scan', 'seek']:
    def plot_version(version):
        data_dir = os.path.join(dir, version)
        data = pd.read_csv(os.path.join(data_dir, op + '-count-time.csv'))
        latency_us = data['micros'] / data['count']
        if (len(latency_us) >= 200):
            mean_step = len(latency_us) / 100
            latency_us = latency_us.groupby(latency_us.index // mean_step).mean()
        write_speed = np.linspace(0, 1, num=len(latency_us), endpoint=False) * (to_MB_s - from_MB_s) + from_MB_s
        plt.plot(write_speed, latency_us)

    if os.path.exists(os.path.join(dir, 'benefit-cost', op + '-count-time.csv')):
        draw(plot_version, op, 'Latency (us)')
