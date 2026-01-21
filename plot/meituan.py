#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
    print('Usage: ' + sys.argv[0] + ' dir')
    exit()
dir = sys.argv[1]
mean_step_secs = 300

num_shards = 5
period_secs = 14400
read_workload = 'nexts-50-seek-1'
unique_size = '10GB'

# The humanfriendly module requires Python <= 3.12
import subprocess
unique_size_bytes = subprocess.run(['humanfriendly', '--parse-size', unique_size], stdout=subprocess.PIPE, text=True).stdout
unique_size_bytes = int(unique_size_bytes)

import os
import json
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

versions = [
    {
        'path': 'rocksdb-tuned',
        'marker': 'o',
        'markersize': 3,
    },
    {
        'path': 'tiering2',
        'marker': 'v',
        'markersize': 3,
    },
    {
        'path': 'tiering4',
        'marker': '^',
        'markersize': 3,
    },
    {
        'path': 'tiering8',
        'marker': '>',
        'markersize': 3,
    },
    {
        'path': 'universal',
        'marker': 's',
        'markersize': 3,
    },
    {
        'path': 'benefit-cost',
        'marker': 'D',
        'markersize': 3,
    },
]
import common
for v in versions:
    v.update(common.versions[v['path']])
version_names = [v['name'] for v in versions]

linewidth = 1
markevery = len(versions)
offset = 1

bar_width = 1 / (len(versions) + 1)
cluster_width = bar_width * len(versions)

def find_data_dir(day_type, version_path):
    workload = 'meituan-writer-' + day_type + '-day-period-secs-' + str(period_secs) + '-num_shards-' + str(num_shards) + '-key-16-value-603-unique-size-' + unique_size + '-memtable-8MiB'
    if version_path in ['tiering2', 'tiering4', 'tiering8', 'benefit-cost']:
        workload += '-max-running-bg-jobs-1'
    workload += '-compaction-200MB-s-' + read_workload
    return os.path.join(dir, workload, version_path)

def draw(day_type, num_srs_yticks, latency_ylim, latency_yticks, sa_yticks):
    fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(12)), constrained_layout=True)
    gs = gridspec.GridSpec(3, 1, figure=fig)

    plt.subplot(gs[0, 0])
    ax_num_srs = plt.gca()
    plt.xlabel('Time (hours)', fontsize=9)
    plt.xticks(fontsize=9)
    plt.ylabel('# of sorted runs', fontsize=9)
    plt.yscale('log')
    plt.ylim((min(num_srs_yticks), max(num_srs_yticks)))
    plt.yticks(num_srs_yticks, labels=num_srs_yticks, fontsize=9)
    ax_num_srs.tick_params(axis='y', which='minor', labelleft=False)

    plt.subplot(gs[1, 0])
    ax_latency = plt.gca()
    plt.xlabel('Time (hours)', fontsize=9)
    plt.xticks(fontsize=9)
    plt.ylabel('Read latency (ms)', fontsize=9)
    plt.yscale('log')
    plt.ylim(latency_ylim)
    plt.yticks(latency_yticks, labels=latency_yticks, fontsize=9)
    ax_latency.tick_params(axis='y', which='minor', labelleft=False)

    plt.subplot(gs[2, 0])
    ax_sa = plt.gca()
    plt.xlabel('Time (hours)', fontsize=9)
    plt.xticks(fontsize=9)
    plt.ylabel('Space amplification', fontsize=9)
    plt.yscale('log')
    plt.ylim((min(sa_yticks), max(sa_yticks)))
    plt.yticks(sa_yticks, labels=sa_yticks, fontsize=9)
    ax_sa.tick_params(axis='y', which='minor', labelleft=False)

    for i in range(len(versions)):
        version = versions[i]
        data_dir = find_data_dir(day_type, version['path'])
        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        report = report[['secs_elapsed', 'num-sorted-runs', 'size']]
        report = report.groupby(report.index // mean_step_secs).mean()
        ax_num_srs.plot(report['secs_elapsed'] / 3600, report['num-sorted-runs'], linewidth=linewidth, color=version['color'], marker=version['marker'], markersize=version['markersize'], markeredgewidth=0.8, markevery=(i * offset, markevery))
        ax_sa.plot(report['secs_elapsed'] / 3600, report['size'] / unique_size_bytes, linewidth=linewidth, color=version['color'], marker=version['marker'], markersize=version['markersize'], markeredgewidth=0.8, markevery=(i * offset, markevery))

        read_count_time = pd.read_csv(os.path.join(data_dir, 'read-count-time.csv'))

        time = read_count_time['secs_elapsed']
        time = time.groupby(time.index // mean_step_secs).mean()

        micros = read_count_time['micros']
        count = read_count_time['count']
        read_latency = micros.groupby(micros.index // mean_step_secs).sum() / count.groupby(count.index // mean_step_secs).sum()

        ax_latency.plot(time / 3600, read_latency / 1000, linewidth=linewidth, color=version['color'], marker=version['marker'], markersize=version['markersize'], markeredgewidth=0.8, markevery=(i * offset, markevery))
    ax_num_srs.grid(axis='y')
    ax_latency.grid(axis='y')
    ax_sa.grid(axis='y')

    fig.legend(version_names, fontsize=9, ncol=3, loc='center', bbox_to_anchor=(0.5, 1.05), handlelength=1, handletextpad=0.5, columnspacing=1.5, frameon=False)
    pdf_path = os.path.join(dir, 'meituan-' + day_type + '-day-num_shards-' + str(num_shards) + '-unique_size-' + unique_size + '-period_secs-' + str(period_secs) + '-' + read_workload + '-mean_step_secs-' + str(mean_step_secs) + '.pdf')
    plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
    print('Plot saved to ' + pdf_path)

draw('peak', [3, 10, 100], (0.4, 10), [0.4, 1, 10], [1, 10])
draw('normal', [3, 10, 30], (0.4, 4), [0.4, 1, 4], [1, 5])

day_type = 'normal'
fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(4)), constrained_layout=True)
gs = gridspec.GridSpec(1, 2, figure=fig)

plt.subplot(gs[0, 0])
ax_p99 = plt.gca()
plt.xlabel('(a) 99%', fontsize=9)
plt.xticks([])
plt.ylabel('Read latency (ms)', fontsize=9)
plt.yticks(fontsize=9)
ax_p99.set_axisbelow(True)
ax_p99.grid(axis='y')

plt.subplot(gs[0, 1])
ax_p999 = plt.gca()
plt.xlabel('(b) 99.9%', fontsize=9)
plt.xticks([])
plt.ylabel('Read latency (ms)', fontsize=9)
plt.yticks(fontsize=9)
ax_p999.set_axisbelow(True)
ax_p999.grid(axis='y')

vec_x = []
for version_idx in range(len(versions)):
    x = -cluster_width / 2 + bar_width / 2 + version_idx * bar_width
    vec_x.append(x)
    version = versions[version_idx]
    data_dir = find_data_dir(day_type, version['path'])
    read_latency_us = json.load(open(os.path.join(data_dir, 'read-latency-us.json')))
    ax_p99.bar(x, read_latency_us['99%'] / 1000, width=bar_width, edgecolor='black', linewidth=0.5, color=version['color'], hatch=version['hatch'])
    ax_p999.bar(x, read_latency_us['99.9%'] / 1000, width=bar_width, edgecolor='black', linewidth=0.5, color=version['color'], hatch=version['hatch'])
fig.legend(version_names, fontsize=9, ncol=3, loc='center', bbox_to_anchor=(0.5, 1.1), handlelength=1, handletextpad=0.5, columnspacing=1.5, frameon=False)
pdf_path = os.path.join(dir, 'meituan-latency-' + day_type + '-day-num_shards-' + str(num_shards) + '-unique_size-' + unique_size + '-period_secs-' + str(period_secs) + '-' + read_workload + '.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
