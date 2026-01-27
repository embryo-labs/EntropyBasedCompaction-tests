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
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Linux Libertine O'],
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
    workload += '-compaction-200MB-s' + read_workload
    return os.path.join(dir, workload, version_path)

def draw(config):
    day_type = config['day-type']
    fig = plt.figure(dpi=300, figsize=(common.single_col_inch, 4.5), constrained_layout=True)
    gs = gridspec.GridSpec(3, 1, figure=fig)

    plt.subplot(gs[0, 0])
    ax_num_srs = plt.gca()
    plt.xlabel('Time (hours)')
    plt.ylabel('# of sorted runs')
    plt.yscale('log')
    plt.ylim((min(config['num-srs-yticks']), max(config['num-srs-yticks'])))
    plt.yticks(config['num-srs-yticks'])
    ax_num_srs.tick_params(axis='y', which='minor', labelleft=False)
    ax_num_srs.grid(axis='y')

    plt.subplot(gs[1, 0])
    ax_read = plt.gca()
    plt.xlabel('Time (hours)')
    plt.ylabel('Read latency (ms)')
    plt.yscale('log')
    plt.ylim(config['read-ylim'])
    ax_read.tick_params(axis='y', which='minor', labelleft=False)
    ax_read.grid(axis='y')

    plt.subplot(gs[2, 0])
    ax_sa = plt.gca()
    plt.xlabel('Time (hours)')
    plt.ylabel('Space amplification')
    plt.yscale('log')
    plt.ylim((min(config['sa-yticks']), max(config['sa-yticks'])))
    plt.yticks(config['sa-yticks'])
    ax_sa.tick_params(axis='y', which='minor', labelleft=False)
    ax_sa.grid(axis='y')

    fig_read = plt.figure(dpi=300, figsize=(common.single_col_inch, 3), constrained_layout=True)
    gs = gridspec.GridSpec(2, 1, figure=fig_read)

    plt.subplot(gs[0, 0])
    ax_scan = plt.gca()
    plt.xlabel('Time (hours)')
    plt.ylabel('Scan latency (ms)')
    plt.yscale('log')
    ax_scan.tick_params(axis='y', which='minor', labelleft=False)
    ax_scan.grid(axis='y')

    plt.subplot(gs[1, 0])
    ax_get = plt.gca()
    plt.xlabel('Time (hours)')
    plt.ylabel('Get latency (ms)')
    plt.ylim((0, 0.3))
    ax_get.tick_params(axis='y', which='minor', labelleft=False)
    ax_get.grid(axis='y')

    for i in range(len(versions)):
        version = versions[i]
        data_dir = find_data_dir(day_type, version['path'])
        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        report = report[['secs_elapsed', 'num-sorted-runs', 'size']]
        report = report.groupby(report.index // mean_step_secs).mean()
        ax_num_srs.plot(report['secs_elapsed'] / 3600, report['num-sorted-runs'], linewidth=linewidth, color=version['color'], marker=version['marker'], markersize=version['markersize'], markeredgewidth=0.8, markevery=(i * offset, markevery))
        ax_sa.plot(report['secs_elapsed'] / 3600, report['size'] / unique_size_bytes, linewidth=linewidth, color=version['color'], marker=version['marker'], markersize=version['markersize'], markeredgewidth=0.8, markevery=(i * offset, markevery))

        def draw_latency(ax, op):
            count_time = pd.read_csv(os.path.join(data_dir, op + '-count-time.csv'))

            time = count_time['secs_elapsed']
            time = time.groupby(time.index // mean_step_secs).mean()

            micros = count_time['micros']
            count = count_time['count']
            read_latency = micros.groupby(micros.index // mean_step_secs).sum() / count.groupby(count.index // mean_step_secs).sum()

            ax.plot(time / 3600, read_latency / 1000, linewidth=linewidth, color=version['color'], marker=version['marker'], markersize=version['markersize'], markeredgewidth=0.8, markevery=(i * offset, markevery))
        draw_latency(ax_read, 'read')
        draw_latency(ax_scan, 'seek')
        draw_latency(ax_get, 'get')

    fig.legend(version_names, ncol=3, loc='center', bbox_to_anchor=(0.5, 1.05), handlelength=1, handletextpad=0.5, columnspacing=1.5, frameon=False)
    pdf_path = os.path.join(dir, f'meituan-{day_type}-day-num_shards-{num_shards}-unique_size-{unique_size}-period_secs-{period_secs}{read_workload}-mean_step_secs-{mean_step_secs}.pdf')
    fig.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
    print('Plot saved to ' + pdf_path)

    fig_read.legend(version_names, ncol=3, loc='center', bbox_to_anchor=(0.5, 1.05), handlelength=1, handletextpad=0.5, columnspacing=1.5, frameon=False)
    pdf_path = os.path.join(dir, f'meituan-{day_type}-day-read-latency-num_shards-{num_shards}-unique_size-{unique_size}-period_secs-{period_secs}{read_workload}-mean_step_secs-{mean_step_secs}.pdf')
    fig_read.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
    print('Plot saved to ' + pdf_path)

draw({
    'day-type': 'peak',
    'num-srs-yticks': [3, 10, 100],
    'read-ylim': (0.1, 2),
    'sa-yticks': [1, 10],
})
draw({
    'day-type': 'normal',
    'num-srs-yticks': [3, 10, 30],
    'read-ylim': (0.1, 1),
    'sa-yticks': [1, 5],
})


panels = [
    {
        'day-type': 'peak',
        'title': '(a) Peak day',
        'ylabel': 'P99 read latency (ms)',
        'ax': None,
    },
    {
        'day-type': 'normal',
        'title': '(b) Normal day',
        'ylabel': 'P99 read latency (ms)',
        'ax': None,
    }
]
fig = plt.figure(dpi = 300, figsize = (common.single_col_inch, 1.3), constrained_layout=True)
gs = gridspec.GridSpec(1, 2, figure=fig)

for col, panel in enumerate(panels):
    plt.subplot(gs[0, col])
    ax = plt.gca()
    plt.xlabel(panel['title'])
    plt.xticks([])
    plt.ylabel(panel['ylabel'])
    ax.set_axisbelow(True)
    ax.grid(axis='y')
    panel['ax'] = ax

for panel in panels:
    day_type = panel['day-type']
    for version_idx in range(len(versions)):
        x = -cluster_width / 2 + bar_width / 2 + version_idx * bar_width
        version = versions[version_idx]
        data_dir = find_data_dir(day_type, version['path'])
        read_latency_us = json.load(open(os.path.join(data_dir, 'read-latency-us.json')))
        panel['ax'].bar(x, read_latency_us['99%'] / 1000, width=bar_width, facecolor=version['facecolor'], edgecolor='black', linewidth=0.5, hatch=version['hatch'])
fig.legend(version_names, ncol=3, loc='center', bbox_to_anchor=(0.5, 1.15), handlelength=1, handletextpad=0.5, columnspacing=1.5, frameon=False)
pdf_path = os.path.join(dir, 'meituan-p99-read-num_shards-' + str(num_shards) + '-unique_size-' + unique_size + '-period_secs-' + str(period_secs) + read_workload + '.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
