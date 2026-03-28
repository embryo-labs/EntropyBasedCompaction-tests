#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
    print('Usage: ' + sys.argv[0] + ' dir')
    exit()
dir = sys.argv[1]
mean_step_secs = 300

num_shards = 5
period_secs = 10800
read_workload = '-get-0.87-seek-0.13-nexts-48'
unique_size = '10GB'

# The humanfriendly module requires Python <= 3.12
import subprocess
unique_size_bytes = subprocess.run(['humanfriendly', '--parse-size', unique_size], stdout=subprocess.PIPE, text=True).stdout
unique_size_bytes = int(unique_size_bytes)

import os
import json
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'serif',
    'font.serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 9,
})

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
        'path': 'universal-hard-trigger',
        'marker': 's',
        'markersize': 3,
    },
    {
        'path': 'entropy-based',
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
    workload = 'meituan-writer-' + day_type + '-day-period-secs-' + str(period_secs) + '-num_shards-' + str(num_shards) + '-key-16-value-603-unique-size-' + unique_size
    if version_path == 'entropy-based':
        workload += '-compaction-trigger-2'
    workload += '-memtable-8MiB'
    if version_path in ['tiering2', 'tiering4', 'tiering8', 'entropy-based']:
        workload += '-max-running-bg-jobs-1'
    workload += '-compaction-200MB-s' + read_workload
    return os.path.join(dir, workload, version_path)

sa_yticks = [1, 10]

fig = plt.figure(dpi=300, figsize=(common.single_col_inch, 4.5), constrained_layout=True)
gs = gridspec.GridSpec(3, 1, figure=fig)

plt.subplot(gs[0, 0])
ax_num_srs = plt.gca()
plt.xlabel('Time (hours)')
plt.ylabel('# of sorted runs')
plt.yscale('log')
plt.ylim((3, 100))
ax_num_srs.tick_params(axis='y', which='minor', labelleft=False)
ax_num_srs.grid(axis='y')

plt.subplot(gs[1, 0])
ax_read = plt.gca()
plt.xlabel('Time (hours)')
plt.ylabel('Read latency (ms)')
plt.yscale('log')
plt.ylim((0.1, 2))
ax_read.tick_params(axis='y', which='minor', labelleft=False)
ax_read.grid(axis='y')

plt.subplot(gs[2, 0])
ax_sa = plt.gca()
plt.xlabel('Time (hours)')
plt.ylabel('Space amplification')
plt.yscale('log')
plt.ylim((min(sa_yticks), max(sa_yticks)))
plt.yticks(sa_yticks)
ax_sa.tick_params(axis='y', which='minor', labelleft=False)
ax_sa.grid(axis='y')

for version_idx, version in enumerate(versions):
    data_dir = find_data_dir('peak', version['path'])
    report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
    report = report[['secs_elapsed', 'num-sorted-runs', 'size']]
    report = report.groupby(report.index // mean_step_secs).mean()
    ax_num_srs.plot(report['secs_elapsed'] / 3600, report['num-sorted-runs'], linewidth=linewidth, color=version['color'], marker=version['marker'], markersize=version['markersize'], markeredgewidth=0.8, markevery=(version_idx * offset, markevery))
    ax_sa.plot(report['secs_elapsed'] / 3600, report['size'] / unique_size_bytes, linewidth=linewidth, color=version['color'], marker=version['marker'], markersize=version['markersize'], markeredgewidth=0.8, markevery=(version_idx * offset, markevery))

    read_count_time = pd.read_csv(os.path.join(data_dir, 'read-count-time.csv'))

    time = read_count_time['secs_elapsed']
    time = time.groupby(time.index // mean_step_secs).mean()
    micros = read_count_time['micros']
    count = read_count_time['count']
    read_latency = micros.groupby(micros.index // mean_step_secs).sum() / count.groupby(count.index // mean_step_secs).sum()
    ax_read.plot(time / 3600, read_latency / 1000, linewidth=linewidth, color=version['color'], marker=version['marker'], markersize=version['markersize'], markeredgewidth=0.8, markevery=(version_idx * offset, markevery))

fig.legend(version_names, ncol=3, loc='center', bbox_to_anchor=(0.5, 1.05), handlelength=1, handletextpad=0.5, columnspacing=1.5, frameon=False)
pdf_path = os.path.join(dir, f'meituan-peak-day-num_shards-{num_shards}-unique_size-{unique_size}-period_secs-{period_secs}{read_workload}-mean_step_secs-{mean_step_secs}.pdf')
fig.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)


def draw_panels(panels, xlabelpad=None, xlabel_loc=None):
    for col, panel in enumerate(panels):
        plt.subplot(gs[0, col])
        ax = plt.gca()
        plt.xlabel(panel['title'], labelpad=xlabelpad, loc=xlabel_loc)
        plt.ylabel(panel['ylabel'])
        if 'yticks' in panel:
            plt.yticks(panel['yticks'])
        plt.xticks([])
        ax.set_axisbelow(True)
        ax.grid(axis='y')
        panel['ax'] = ax

panels_read = [
    {
        'title': '(a) Read latency',
        'ylabel': 'Avg read latency (ms)',
        'ax': None,
    },
    {
        'title': '(b) Scan latency',
        'ylabel': 'Avg scan latency (ms)',
        'ax': None,
    },
    {
        'title': '(c) Get latency',
        'ylabel': 'Avg get latency (ms)',
        'yticks': [0, 0.1],
        'ax': None,
    }
]
fig_read = plt.figure(dpi=300, figsize=(common.single_col_inch, 1.3), constrained_layout=True)
gs = gridspec.GridSpec(1, 3, figure=fig_read)
draw_panels(panels_read, xlabelpad=5, xlabel_loc='right')

panels_p99 = [
    {
        'title': '(a) Peak day',
        'ylabel': 'P99 read latency (ms)',
        'ax': None,
    },
    {
        'title': '(b) Normal day',
        'ylabel': 'P99 read latency (ms)',
        'ax': None,
    }
]
fig_p99 = plt.figure(dpi = 300, figsize = (common.single_col_inch, 1.3), constrained_layout=True)
gs = gridspec.GridSpec(1, 2, figure=fig_p99)
draw_panels(panels_p99)

for day_type in ['peak', 'normal']:
    match day_type:
        case 'peak':
            panel_p99 = panels_p99[0]
        case 'normal':
            panel_p99 = panels_p99[1]
    for version_idx, version in enumerate(versions):
        x = -cluster_width / 2 + bar_width / 2 + version_idx * bar_width
        data_dir = find_data_dir(day_type, version['path'])
        read_latency_us = json.load(open(os.path.join(data_dir, 'read-latency-us.json')))
        def add_bar(ax, v):
            ax.bar(x, v, width=bar_width, facecolor=version['facecolor'], edgecolor='black', linewidth=0.5, hatch=version['hatch'])
        if day_type == 'peak':
            scan_latency_us = json.load(open(os.path.join(data_dir, 'seek-latency-us.json')))
            get_latency_us = json.load(open(os.path.join(data_dir, 'get-latency-us.json')))
            add_bar(panels_read[0]['ax'], read_latency_us['Average'] / 1000)
            add_bar(panels_read[1]['ax'], scan_latency_us['Average'] / 1000)
            add_bar(panels_read[2]['ax'], get_latency_us['Average'] / 1000)
        add_bar(panel_p99['ax'], read_latency_us['99%'] / 1000)

fig_read.legend(version_names, ncol=3, loc='center', bbox_to_anchor=(0.5, 1.15), handlelength=1, handletextpad=0.5, columnspacing=1.5, frameon=False)
pdf_path = os.path.join(dir, f'meituan-peak-day-read-latency-num_shards-{num_shards}-unique_size-{unique_size}-period_secs-{period_secs}{read_workload}-mean_step_secs-{mean_step_secs}.pdf')
fig_read.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)

fig_p99.legend(version_names, ncol=3, loc='center', bbox_to_anchor=(0.5, 1.15), handlelength=1, handletextpad=0.5, columnspacing=1.5, frameon=False)
pdf_path = os.path.join(dir, 'meituan-p99-read-num_shards-' + str(num_shards) + '-unique_size-' + unique_size + '-period_secs-' + str(period_secs) + read_workload + '.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
