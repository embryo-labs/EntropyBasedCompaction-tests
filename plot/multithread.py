#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
    print('Usage: ' + sys.argv[0] + ' dir')
    exit()
dir = sys.argv[1]

value = '-value-603'
compaction = '-compaction-200MB-s'
warmup_secs = 1200
run_secs = 1200
rw_workload = '-nexts-48-put-0.34'

unique_size = '10GB'

import os
import pandas as pd
import json
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec

import common

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'serif',
    'font.serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 10,
})

vec_num_threads = [8, 64]

versions = [
    {
        'path': 'rocksdb-tuned',
        'name': 'RocksDB-Tuned',
        'max-running-bg-jobs': None,
        'facecolor': common.colors[0]['light'],
        'hatch': 'XX',
    },
    {
        'path': 'tiering4',
        'name': 'Tiering4',
        'max-running-bg-jobs': 1,
        'facecolor': common.colors[3]['light'],
        'hatch': '---',
    },
    {
        'path': 'entropy-based',
        'name': 'EBC (soft preemption)',
        'max-running-bg-jobs': None,
        'facecolor': common.colors[4]['light'],
        'hatch': '--\\\\',
    },
    {
        'path': 'entropy-based',
        'name': 'EBC (strict preemption)',
        'max-running-bg-jobs': 1,
        'facecolor': common.colors[2]['light'],
        'hatch': '///',
    },
]
version_names = [v.get('name', v['path']) for v in versions]

bar_width = 1 / (len(versions) + 1)
cluster_width = bar_width * len(versions)

panels = [
    {
        'title': '(a) Avg number of runs',
        'ylabel': 'Avg # of runs',
        'yscale': 'linear',
        'ax': None,
    },
    {
        'title': '(b) Avg read latency',
        'ylabel': 'Latency (ms)',
        'yscale': 'linear',
        'ax': None,
    },
    {
        'title': '(c) P99 read latency',
        'ylabel': 'Latency (ms)',
        'yscale': 'linear',
        'ax': None,
    },
    {
        'title': '(d) Avg Put latency',
        'ylabel': 'Latency (us)',
        'yscale': 'log',
        'ylim': (1, None),
        'ax': None,
    },
    {
        'title': '(e) User write throughput',
        'ylabel': 'Tput. (MB/s)',
        'yscale': 'linear',
        'ax': None,
    },
]

fig = plt.figure(dpi=300, figsize=(common.acmsmall_inch, 2.3))
gs = gridspec.GridSpec(
    2, 6, figure=fig,
    left=0.08,
    bottom=0.145,
    right=0.998,
    top=0.9,
    wspace=1.05,
    hspace=0.6,
)
panel_positions = [(0, 0), (0, 2), (0, 4), (1, 1), (1, 3)]
for panel, (row, col) in zip(panels, panel_positions):
    ax = fig.add_subplot(gs[row, col:col + 2])
    ax.set_xticks(list(range(0, len(vec_num_threads))), [str(num_threads) for num_threads in vec_num_threads])
    ax.set_xlabel(panel['title'], labelpad=1)
    ax.set_ylabel(panel['ylabel'])
    ax.tick_params(axis='x', length=0, pad=2)
    ax.set_yscale(panel['yscale'])
    ax.tick_params(axis='y', which='minor', labelleft=False)
    ax.set_axisbelow(True)
    ax.grid(axis='y')
    if row == 1:
        if col == 1:
            horizontal_offset = -0.02
        else:
            horizontal_offset = 0.02
        ax.set_position(ax.get_position().translated(horizontal_offset, 0))
    panel['ax'] = ax
handles = [mpl.patches.Patch(facecolor=v['facecolor'], hatch=v['hatch'], 
                            edgecolor='black', linewidth=0.5) for v in versions]
fig.legend(
    handles=handles,
    labels=version_names,
    ncol=len(versions),
    loc='upper center',
    bbox_to_anchor=(0.5, 1.0),
    frameon=False,
    handlelength=1.2,
    handletextpad=0.5,
    columnspacing=1.0,
    borderpad=0,
    borderaxespad=0,
)

for i, num_threads in enumerate(vec_num_threads):
    for version_idx, version in enumerate(versions):
        x = i - cluster_width / 2 + bar_width / 2 + version_idx * bar_width
        if version['max-running-bg-jobs'] is None:
            max_running_bg_jobs = ''
        else:
            max_running_bg_jobs = '-max-running-bg-jobs-1'
        workload = f'readrandomwriterandom-key-16{value}-unique-size-{unique_size}-warmup-secs-{warmup_secs}-run-secs-{run_secs}{max_running_bg_jobs}-slowdown-32-stop-50-memtable-8MiB{compaction}{rw_workload}-threads-{num_threads}'
        data_dir = os.path.join(dir, workload, version['path'])
        report = pd.read_csv(os.path.join(data_dir, 'report.csv')).iloc[1:]
        num_srs_avg = report['num-sorted-runs'].mean()
        read_latency_us = json.load(open(os.path.join(data_dir, 'read-latency-us.json')))
        put_latency_us = json.load(open(os.path.join(data_dir, 'write-latency-us.json')))
        user_write_throughput_MB = report['rocksdb.bytes.written'].mean() / 1e6

        def add_bar(panel, val):
            panel['ax'].bar(x, val, width=bar_width, edgecolor='black', linewidth=0.5, facecolor=version['facecolor'], hatch=version['hatch'])
        add_bar(panels[0], num_srs_avg)
        add_bar(panels[1], read_latency_us['Average'] / 1000)
        add_bar(panels[2], read_latency_us['99%'] / 1000)
        add_bar(panels[3], put_latency_us['Average'])
        add_bar(panels[4], user_write_throughput_MB)
for panel in panels:
    if 'ylim' in panel:
        panel['ax'].set_ylim(panel['ylim'])

pdf_path = os.path.join(dir, f'multithread{value}{compaction}-warmup-{warmup_secs}-run-{run_secs}{rw_workload}.pdf')
common.check_visible_labels(fig)
fig.savefig(pdf_path, metadata={'CreationDate': None})
print(f'Plot saved to {pdf_path}')
