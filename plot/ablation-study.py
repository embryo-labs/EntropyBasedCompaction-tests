#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
	print('Usage: ' + sys.argv[0] + ' dir')
	exit()
dir = sys.argv[1]

value = '-value-603'
compaction = '-compaction-200MB-s'
warmup_secs = 1500
run_secs = 500
read_workload = '-get-0.87-seek-0.13-nexts-48'

import os
import numpy as np
import pandas as pd
import json
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec

import common

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 9,
})

vec_write_MB_s = [10, 20, 30, 40, 50, 60]

versions = [
    {
        'path': 'preempt-only-by-entropy-ke-1',
        'name': 'Only-by-entropy',
        'max-running-bg-jobs': 1,
        'marker': 's',
        'markersize': 3,
        'color': common.colors[0]['dark'],
    },
    {
        'path': 'preempt-only-by-num',
        'name': 'Only-by-num',
        'max-running-bg-jobs': 1,
        'marker': 'v',
        'markersize': 3,
        'color': common.colors[1]['dark'],
    },
    {
        'path': 'no-sliding-window',
        'name': 'No-sliding-window',
        'max-running-bg-jobs': 1,
        'marker': '>',
        'markersize': 3,
        'color': common.colors[3]['dark'],
    },
    {
        'path': 'benefit-cost',
        'name': 'No-running-jobs-limit',
        'max-running-bg-jobs': None,
        'marker': 'o',
        'markersize': 3,
        'color': common.colors[5]['dark'],
    },
    {
        'path': 'benefit-cost',
        'max-running-bg-jobs': 1,
        'marker': 'D',
        'markersize': 3,
        'name': common.versions['benefit-cost']['name'],
        'color': common.versions['benefit-cost']['color'],
    },
]
version_names = [v['name'] for v in versions]

fig = plt.figure(dpi=300, figsize=(common.single_col_inch, 1.7), constrained_layout=True)
gs = gridspec.GridSpec(1, 2, figure=fig)
plt.subplot(gs[0, 0])
ax_srs_avg = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('Average # of sorted runs', fontsize=9)
plt.ylim((0, 100))
plt.yticks(fontsize=9)
ax_srs_avg.grid(axis='y')

plt.subplot(gs[0, 1])
ax_srs_p99 = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('P99 # of sorted runs', fontsize=9)
plt.ylim((0, 100))
plt.yticks(fontsize=9)
ax_srs_p99.grid(axis='y')

for version in versions:
    srs_avg = []
    srs_p99 = []
    for write_MB_s in vec_write_MB_s:
        workload = 'readwhilewriting-key-16' + value + '-unique-size-10GB-warmup-secs-' + str(warmup_secs) + '-run-secs-' + str(run_secs) + '-memtable-8MiB'
        if version['max-running-bg-jobs'] is not None:
            workload += '-max-running-bg-jobs-1'
        workload += compaction + '-write-' + str(write_MB_s) + 'MB-s' + read_workload
        data_dir = os.path.join(dir, workload, version['path'])
        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        srs_avg.append(report['num-sorted-runs'].mean())
        srs_p99.append(np.percentile(report['num-sorted-runs'], 99))

        read_latency_us = json.load(open(os.path.join(data_dir, 'read-latency-us.json')))
    ax_srs_avg.plot(vec_write_MB_s, srs_avg, linewidth=1, color=version['color'], marker=version['marker'], markersize=version['markersize'], markeredgewidth=0.8)
    ax_srs_p99.plot(vec_write_MB_s, srs_p99, linewidth=1, color=version['color'], marker=version['marker'], markersize=version['markersize'], markeredgewidth=0.8)

fig.legend(version_names, fontsize=9, ncol=2, loc='center', bbox_to_anchor=(0.5, 1.15), frameon=False)
pdf_path = os.path.join(dir, f'ablation-study{value}{compaction}-warmup-{warmup_secs}-run-{run_secs}{read_workload}.pdf')
fig.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
