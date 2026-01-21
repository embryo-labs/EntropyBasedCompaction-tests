#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
	print('Usage: ' + sys.argv[0] + ' dir')
	exit()
dir = sys.argv[1]

read_workload = 'nexts-50-seek-1'
compaction = '200MB-s'
warmup_secs = 1500
run_secs = 500

io_sa = ''

def workload_path(max_running_bg_jobs = None, has_io_sa = False):
    workload = 'readwhilewriting-key-16-value-1000-unique-size-10GB-warmup-secs-' + str(warmup_secs) + '-run-secs-' + str(run_secs) + '-memtable-8MiB'
    if max_running_bg_jobs is not None:
        workload += '-max-running-bg-jobs-1'
    if has_io_sa:
        workload += io_sa
    workload += '-compaction-' + compaction + '-write-' + str(write_MB_s) + 'MB-s-' + read_workload
    return workload

import os
import math
import numpy as np
import pandas as pd
import json
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

fig = plt.figure(dpi=300, figsize=(cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(12)), constrained_layout=True)
gs = gridspec.GridSpec(3, 2, figure=fig)

plt.subplot(gs[0, 0])
ax_srs_avg = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('Average # of sorted runs', fontsize=9)
plt.yscale('log')
plt.ylim((4, 1000))
yticks = [4, 10, 100, 1000]
plt.yticks(yticks, labels=yticks, fontsize=9)

plt.subplot(gs[0, 1])
ax_srs_p99 = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('P99 # of sorted runs', fontsize=9)
plt.yscale('log')
plt.ylim((4, 1000))
yticks = [4, 10, 100, 1000]
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

plt.subplot(gs[2, 0])
ax_size_avg = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('Average size (GB)', fontsize=9)
plt.yscale('log')
plt.ylim((10, 100))
yticks = [10, 100]
plt.yticks(yticks, labels=yticks, fontsize=9)
ax_size_avg.tick_params(axis='y', which='minor', labelleft=False)

plt.subplot(gs[2, 1])
ax_size_max = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('Max size (GB)', fontsize=9)
plt.yscale('log')
plt.ylim((10, 100))
yticks = [10, 100]
plt.yticks(yticks, labels=yticks, fontsize=9)
ax_size_max.tick_params(axis='y', which='minor', labelleft=False)

for version in versions:
    srs_avg = []
    srs_p99 = []
    lat_avg = []
    lat_p99 = []
    size_avg = []
    size_max = []
    for write_MB_s in vec_write_MB_s:
        if version['path'] in ['tiering2', 'tiering4', 'tiering8', 'benefit-cost']:
            max_running_bg_jobs = 1
        else:
            max_running_bg_jobs = None
        workload = workload_path(max_running_bg_jobs, version['path'] == 'benefit-cost')
        data_dir = os.path.join(dir, workload, version['path'])

        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        srs_avg.append(report['num-sorted-runs'].mean())
        srs_p99.append(np.percentile(report['num-sorted-runs'], 99))

        read_latency_us = json.load(open(os.path.join(data_dir, 'read-latency-us.json')))
        lat_avg.append(float(read_latency_us['Average'] / 1000))
        lat_p99.append(float(read_latency_us['99%']) / 1000)

        size_avg.append(report['size'].mean() / 1e9)
        size_max.append(report['size'].max() / 1e9)
    ax_srs_avg.plot(vec_write_MB_s, srs_avg, linewidth=1, color=version['color'], marker=version['marker'], markersize=version['markersize'], markerfacecolor=version['markerfacecolor'], markeredgewidth=0.8)
    ax_srs_p99.plot(vec_write_MB_s, srs_p99, linewidth=1, color=version['color'], marker=version['marker'], markersize=version['markersize'], markerfacecolor=version['markerfacecolor'], markeredgewidth=0.8)

    ax_lat_avg.plot(vec_write_MB_s, lat_avg, linewidth=1, color=version['color'], marker=version['marker'], markersize=version['markersize'], markerfacecolor=version['markerfacecolor'], markeredgewidth=0.8)
    ax_lat_p99.plot(vec_write_MB_s, lat_p99, linewidth=1, color=version['color'], marker=version['marker'], markersize=version['markersize'], markerfacecolor=version['markerfacecolor'], markeredgewidth=0.8)

    ax_size_avg.plot(vec_write_MB_s, size_avg, linewidth=1, color=version['color'], marker=version['marker'], markersize=version['markersize'], markerfacecolor=version['markerfacecolor'], markeredgewidth=0.8)
    ax_size_max.plot(vec_write_MB_s, size_max, linewidth=1, color=version['color'], marker=version['marker'], markersize=version['markersize'], markerfacecolor=version['markerfacecolor'], markeredgewidth=0.8)

fig.legend(version_names, fontsize=9, ncol=3, loc='center', bbox_to_anchor=(0.5, 1.05), handlelength=1, handletextpad=0.5, frameon=False)
pdf_path = os.path.join(dir, 'const-write-rates-' + compaction + '-warmup-' + str(warmup_secs) + '-run-' + str(run_secs) + io_sa + '-' + read_workload + '.pdf')
fig.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
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

fig = plt.figure(dpi=300, figsize=(cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(10)), constrained_layout=True)
gs = gridspec.GridSpec(2, 2, figure=fig)
plt.subplot(gs[0, 0])
ax_srs_avg = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('Average # of sorted runs', fontsize=9)
plt.ylim((0, 100))
plt.yticks(fontsize=9)

plt.subplot(gs[0, 1])
ax_srs_p99 = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('P99 # of sorted runs', fontsize=9)
plt.ylim((0, 100))
plt.yticks(fontsize=9)

plt.subplot(gs[1, 0])
ax_lat_avg = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('Average read latency (ms)', fontsize=9)
plt.ylim((0, 50))
plt.yticks(fontsize=9)

plt.subplot(gs[1, 1])
ax_lat_p99 = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('P99 read latency (ms)', fontsize=9)
plt.ylim((0, 200))
plt.yticks(fontsize=9)

for version in versions:
    srs_avg = []
    srs_p99 = []
    lat_avg = []
    lat_p99 = []
    for write_MB_s in vec_write_MB_s:
        workload = workload_path(1)
        data_dir = os.path.join(dir, workload, version['path'])
        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        srs_avg.append(report['num-sorted-runs'].mean())
        srs_p99.append(np.percentile(report['num-sorted-runs'], 99))

        read_latency_us = json.load(open(os.path.join(data_dir, 'read-latency-us.json')))
        lat_avg.append(float(read_latency_us['Average'] / 1000))
        lat_p99.append(float(read_latency_us['99%']) / 1000)
    ax_srs_avg.plot(vec_write_MB_s, srs_avg, linewidth=1, color=version['color'], marker=version['marker'], markersize=version['markersize'], markerfacecolor=version['markerfacecolor'], markeredgewidth=0.8)
    ax_srs_p99.plot(vec_write_MB_s, srs_p99, linewidth=1, color=version['color'], marker=version['marker'], markersize=version['markersize'], markerfacecolor=version['markerfacecolor'], markeredgewidth=0.8)

    ax_lat_avg.plot(vec_write_MB_s, lat_avg, linewidth=1, color=version['color'], marker=version['marker'], markersize=version['markersize'], markerfacecolor=version['markerfacecolor'], markeredgewidth=0.8)
    ax_lat_p99.plot(vec_write_MB_s, lat_p99, linewidth=1, color=version['color'], marker=version['marker'], markersize=version['markersize'], markerfacecolor=version['markerfacecolor'], markeredgewidth=0.8)

fig.legend(version_names, fontsize=9, ncol=2, loc='center', bbox_to_anchor=(0.5, 1.1))
pdf_path = os.path.join(dir, 'const-write-rates-ablation-study-' + compaction + io_sa + '-' + read_workload + '.pdf')
fig.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
