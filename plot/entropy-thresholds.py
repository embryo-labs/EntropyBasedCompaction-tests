#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
	print('Usage: ' + sys.argv[0] + ' dir')
	exit()
dir = sys.argv[1]

read_workload = 'nexts-50-seek-1'
compaction = '200MB-s'
warmup_secs = 1000
run_secs = 500

import os
import numpy as np
import pandas as pd
import json
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

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

fig = plt.figure(dpi=300, figsize=(cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(10)), constrained_layout=True)
gs = GridSpec(2, 2, figure=fig)
plt.subplot(gs[0, 0])
ax_srs_avg = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('Average # of sorted runs', fontsize=9)
plt.yscale('log')
plt.ylim((4, 100))
yticks = [4, 10, 100]
plt.yticks(yticks, labels=yticks, fontsize=9)

plt.subplot(gs[0, 1])
ax_srs_p99 = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('P99 # of sorted runs', fontsize=9)
plt.yscale('log')
plt.ylim((4, 100))
yticks = [4, 10, 100]
plt.yticks(yticks, labels=yticks, fontsize=9)

plt.subplot(gs[1, 0])
ax_lat_avg = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('Average read latency (ms)', fontsize=9)
plt.yscale('log')
plt.ylim((0.7, 50))
yticks = [1, 10, 50]
plt.yticks(yticks, labels=yticks, fontsize=9)

plt.subplot(gs[1, 1])
ax_lat_p99 = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('P99 read latency (ms)', fontsize=9)
plt.yscale('log')
plt.ylim((1, 100))
yticks = [1, 10, 100]
plt.yticks(yticks, labels=yticks, fontsize=9)

entropy_thresholds = [0, 0.5, 0.78, 1, 2, 3]
for t_e in entropy_thresholds:
    srs_avg = []
    srs_p99 = []
    lat_avg = []
    lat_p99 = []
    for write_MB_s in vec_write_MB_s:
        if t_e != 0.78:
            workload = 'readwhilewriting-key-16-value-1000-unique-size-10GB-warmup-secs-' + str(warmup_secs) + '-run-secs-' + str(run_secs) + '-entropy-threshold-' + str(t_e) + '-memtable-8MiB-max-running-bg-jobs-1-compaction-' + compaction + '-write-' + str(write_MB_s) + 'MB-s-' + read_workload
        else:
            workload = 'readwhilewriting-key-16-value-1000-unique-size-10GB-warmup-secs-' + str(warmup_secs) + '-run-secs-' + str(run_secs) + '-memtable-8MiB-max-running-bg-jobs-1-compaction-' + compaction + '-write-' + str(write_MB_s) + 'MB-s-' + read_workload
        data_dir = os.path.join(dir, workload, 'benefit-cost')

        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        srs_avg.append(report['num-sorted-runs'].mean())
        srs_p99.append(np.percentile(report['num-sorted-runs'], 99))

        read_latency_us = json.load(open(os.path.join(data_dir, 'read-latency-us.json')))
        lat_avg.append(float(read_latency_us['Average'] / 1000))
        lat_p99.append(float(read_latency_us['99%']) / 1000)
    ax_srs_avg.plot(vec_write_MB_s, srs_avg, linewidth=1)
    ax_srs_p99.plot(vec_write_MB_s, srs_p99, linewidth=1)

    ax_lat_avg.plot(vec_write_MB_s, lat_avg, linewidth=1)
    ax_lat_p99.plot(vec_write_MB_s, lat_p99, linewidth=1)

fig.legend(entropy_thresholds, fontsize=9, ncol=3, loc='center', bbox_to_anchor=(0.5, 1.05))
pdf_path = os.path.join(dir, 'entropy-thresholds-comparison-' + compaction + '-' + read_workload + '.pdf')
fig.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
