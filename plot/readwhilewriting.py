#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
	print('Usage: ' + sys.argv[0] + ' dir')
	exit()
dir = sys.argv[1]

import os
import math
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec

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

vec_write_MB_s = [10, 20, 30, 40, 50, 60]

versions = ['rocksdb-tuned', 'tiering2', 'tiering4', 'tiering8', 'universal', 'benefit-cost']

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
gs = gridspec.GridSpec(1, 2, figure=fig)
plt.subplot(gs[0, 0])
ax_num_srs = plt.gca()
plt.subplot(gs[0, 1])
ax_latency = plt.gca()

for version in versions:
    num_srs = []
    read_avg_latency_us = []
    for write_MB_s in vec_write_MB_s:
        workload = 'readwhilewriting-key-16-value-503-unique-size-10GB-memtable-8MiB-'
        if version in ['tiering2', 'tiering4', 'tiering8', 'benefit-cost']:
            workload += 'max-running-bg-jobs-1-'
        workload += 'compaction-200MB-s-write-' + str(write_MB_s) + 'MB-s-scan-len-meituan-get-0.87-seek-0.13-write-100GB'
        data_dir = os.path.join(dir, workload, version)
        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        # Use the last 30%
        report = report.iloc[-math.ceil(len(report) * 0.3):]
        num_srs.append(report['num-sorted-runs'].mean())
        
        read_count_time = pd.read_csv(os.path.join(data_dir, 'read-count-time.csv'))
        read_count_time = read_count_time.iloc[-math.ceil(len(read_count_time) * 0.3):]
        read_avg_latency_us.append(read_count_time['micros'].sum() / read_count_time['count'].sum())
    ax_num_srs.plot(vec_write_MB_s, num_srs)
    ax_latency.plot(vec_write_MB_s, read_avg_latency_us)
ax_num_srs.set_xlabel('Write speed (MB/s)', fontsize=9)
ax_num_srs.set_xticks(vec_write_MB_s)
ax_num_srs.tick_params(axis='x', which='major', labelsize=9)
ax_num_srs.set_ylabel('# of sorted runs', fontsize=9)
ax_num_srs.tick_params(axis='y', which='major', labelsize=9)
ax_num_srs.set_yscale('log')

ax_latency.set_xlabel('Write speed (MB/s)', fontsize=9)
ax_latency.set_xticks(vec_write_MB_s)
ax_latency.tick_params(axis='x', which='major', labelsize=9)
ax_latency.set_ylabel('Read latency (us)', fontsize=9)
ax_latency.tick_params(axis='y', which='major', labelsize=9)
ax_latency.set_yscale('log')

fig.legend(versions, fontsize=9, ncol=3, loc='center', bbox_to_anchor=(0.5, 1.1))
pdf_path = os.path.join(dir, 'readwhilewriting.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
