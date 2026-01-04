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

compaction = '200MB-s'
vec_write_MB_s = [10, 20, 30, 40, 50, 60]

versions = [
    {
        'path': 'rocksdb-tuned',
        'marker': 'o',
        'markersize': 4,
        'markerfacecolor': 'none',
    },
    {
        'path': 'tiering2',
        'marker': 'v',
        'markersize': 4,
        'markerfacecolor': 'none',
    },
    {
        'path': 'tiering4',
        'marker': '^',
        'markersize': 4,
        'markerfacecolor': 'none',
    },
    {
        'path': 'tiering8',
        'marker': '>',
        'markersize': 4,
        'markerfacecolor': 'none',
    },
    {
        'path': 'universal',
        'marker': 's',
        'markersize': 2,
    },
    {
        'path': 'benefit-cost',
        'marker': 'D',
        'markersize': 2,
    },
]
import common
for v in versions:
    v['name'] = common.versions[v['path']]['name']
    v['color'] = common.versions[v['path']]['color']
    if 'markerfacecolor' not in v:
        v['markerfacecolor'] = v['color']
version_names = [v['name'] for v in versions]

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
gs = gridspec.GridSpec(1, 2, figure=fig)
plt.subplot(gs[0, 0])
ax_avg = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('Average # of sorted runs', fontsize=9)
plt.ylim((0, 100))
plt.yticks(fontsize=9)

plt.subplot(gs[0, 1])
ax_p99 = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('P99 # of sorted runs', fontsize=9)
plt.ylim((0, 100))
plt.yticks(fontsize=9)

for version in versions:
    avg = []
    p99 = []
    for write_MB_s in vec_write_MB_s:
        workload = 'overwrite-key-16-value-1000-unique-size-10GB-memtable-8MiB-'
        if version['path'] in ['tiering2', 'tiering4', 'tiering8', 'benefit-cost']:
            workload += 'max-running-bg-jobs-1-'
        workload += 'compaction-' + compaction + '-write-' + str(write_MB_s) + 'MB-s-write-100GB'
        data_dir = os.path.join(dir, workload, version['path'])
        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        # Use the last 30%
        report = report.iloc[-math.ceil(len(report) * 0.3):]
        avg.append(report['num-sorted-runs'].mean())
        p99.append(np.percentile(report['num-sorted-runs'], 99))
    ax_avg.plot(vec_write_MB_s, avg, linewidth=1, color=version['color'], marker=version['marker'], markersize=version['markersize'], markerfacecolor=version['markerfacecolor'], markeredgewidth=0.8)
    ax_p99.plot(vec_write_MB_s, p99, linewidth=1, color=version['color'], marker=version['marker'], markersize=version['markersize'], markerfacecolor=version['markerfacecolor'], markeredgewidth=0.8)

fig.legend(version_names, fontsize=9, ncol=3, loc='center', bbox_to_anchor=(0.5, 1.1))
pdf_path = os.path.join(dir, 'write-rates-num-srs-' + compaction + '.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)

versions = [
    {
        'path': 'preempt-only-by-entropy-ke-1',
        'name': 'Only-by-entropy',
        'marker': 'v',
        'markersize': 4,
        'color': plt.cm.tab10(1),
        'markerfacecolor': 'none',
    },
    {
        'path': 'preempt-only-by-num',
        'name': 'Only-by-num',
        'marker': '^',
        'markersize': 4,
        'color': plt.cm.tab10(3),
        'markerfacecolor': 'none',
    },
    {
        'path': 'no-sliding-window',
        'name': 'No-sliding-window',
        'marker': '>',
        'markersize': 4,
        'color': plt.cm.tab10(4),
        'markerfacecolor': 'none',
    },
    {
        'path': 'benefit-cost',
        'marker': 'D',
        'markersize': 2,
        'name': common.versions['benefit-cost']['name'],
        'color': common.versions['benefit-cost']['color'],
        'markerfacecolor': common.versions['benefit-cost']['color'],
    },
]
version_names = [v['name'] for v in versions]

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
gs = gridspec.GridSpec(1, 2, figure=fig)
plt.subplot(gs[0, 0])
ax_avg = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('Average # of sorted runs', fontsize=9)
plt.ylim((0, 100))
plt.yticks(fontsize=9)

plt.subplot(gs[0, 1])
ax_p99 = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('P99 # of sorted runs', fontsize=9)
plt.ylim((0, 100))
plt.yticks(fontsize=9)

for version in versions:
    avg = []
    p99 = []
    for write_MB_s in vec_write_MB_s:
        workload = 'overwrite-key-16-value-1000-unique-size-10GB-memtable-8MiB-max-running-bg-jobs-1-compaction-' + compaction + '-write-' + str(write_MB_s) + 'MB-s-write-100GB'
        data_dir = os.path.join(dir, workload, version['path'])
        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        # Use the last 30%
        report = report.iloc[-math.ceil(len(report) * 0.3):]
        avg.append(report['num-sorted-runs'].mean())
        p99.append(np.percentile(report['num-sorted-runs'], 99))
    ax_avg.plot(vec_write_MB_s, avg, linewidth=1, color=version['color'], marker=version['marker'], markersize=version['markersize'], markerfacecolor=version['markerfacecolor'], markeredgewidth=0.8)
    ax_p99.plot(vec_write_MB_s, p99, linewidth=1, color=version['color'], marker=version['marker'], markersize=version['markersize'], markerfacecolor=version['markerfacecolor'], markeredgewidth=0.8)

fig.legend(version_names, fontsize=9, ncol=2, loc='center', bbox_to_anchor=(0.5, 1.1))
pdf_path = os.path.join(dir, 'write-rates-num-srs-ablation-study-' + compaction + '.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
