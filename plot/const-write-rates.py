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

unique_size = '10GB'

# The humanfriendly module requires Python <= 3.12
import subprocess
unique_size_bytes = subprocess.run(['humanfriendly', '--parse-size', unique_size], stdout=subprocess.PIPE, text=True).stdout
unique_size_bytes = int(unique_size_bytes)

import os
import numpy as np
import pandas as pd
import json
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.ticker import LogLocator, NullFormatter

if len(sys.argv) != 2:
    print('Usage: ' + sys.argv[0] + ' dir')
    exit()
dir = sys.argv[1]

SINGLE_COL_WIDTH = 8.5
DOUBLE_COL_WIDTH = 17.8 
def cm_to_inch(value):
    return value/2.54

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 9,
})

vec_write_MB_s = [10, 30, 50]

versions = [
    {
        'path': 'rocksdb-tuned',
    },
    {
        'path': 'tiering2',
    },
    {
        'path': 'tiering4',
    },
    {
        'path': 'tiering8',
    },
    {
        'path': 'universal',
    },
    {
        'path': 'benefit-cost',
    },
]

import common
for v in versions:
    if v['path'] in common.versions:
        v.update(common.versions[v['path']])
version_names = [v.get('name', v['path']) for v in versions]

bar_width = 1 / (len(versions) + 1)
cluster_width = bar_width * len(versions)

data_cache = {}
for i, write_MB_s in enumerate(vec_write_MB_s):
    data_cache[i] = {}
    for version_idx, version in enumerate(versions):
        workload = 'readwhilewriting-key-16' + value + '-unique-size-10GB-warmup-secs-' + str(warmup_secs) + '-run-secs-' + str(run_secs) + '-memtable-8MiB'
        if version['path'] in ['tiering2', 'tiering4', 'tiering8', 'benefit-cost']:
            workload += '-max-running-bg-jobs-1'
        workload += compaction + '-write-' + str(write_MB_s) + 'MB-s' + read_workload
        data_dir = os.path.join(dir, workload, version['path'])
        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        data_cache[i][version_idx] = {
            'report': report,
            'scan': json.load(open(os.path.join(data_dir, 'seek-latency-us.json'))),
            'get': json.load(open(os.path.join(data_dir, 'get-latency-us.json'))),
            'read': json.load(open(os.path.join(data_dir, 'read-latency-us.json'))),
        }

panels = [
    {
        "title": "(a) Number of sorted runs (average)",
        "ylabel": "Avg # of sorted runs",
        "getter": lambda d: d['report']['num-sorted-runs'].mean(),
        "ylims": [None, (1, 300), (1, 3000)],
        "log_scale": [False, True, True]
    },
    {
        "title": "(b) Number of sorted runs (99th percentile)",
        "ylabel": "P99 # of sorted runs",
        "getter": lambda d: np.percentile(d['report']['num-sorted-runs'], 99),
        "ylims": [None, (1, 300), (1, 3000)],
        "log_scale": [False, True, True]
    },
    {
        "title": "(c) Scan latency (average)",
        "ylabel": "Avg scan latency (ms)",
        "getter": lambda d: float(d['scan']['Average'] / 1000),
        "ylims": [None, (1, 30), (1, 1000)],
        "log_scale": [False, True, True],
    },
    {
        "title": "(d) Scan latency (99th percentile)",
        "ylabel": "P99 scan latency (ms)",
        "getter": lambda d: float(d['scan']['99%'] / 1000),
        'ylims': [None, (1, 100), (1, 1000)],
        'log_scale': [False, True, True],
    },
    {
        'title': '(e) Get latency (average)',
        'ylabel': 'Avg get latency (ms)',
        'getter': lambda d: float(d['get']['Average'] / 1000),
        'ylims': [None, None, (0.1, 1)],
        'yticks': [[0, 0.1], None, None],
        'log_scale': [False, False, True],
    },
    {
        'title': '(f) Get latency (99th percentile)',
        'ylabel': 'P99 get latency (ms)',
        'getter': lambda d: float(d['get']['99%'] / 1000),
        'ylims': [None, (0, 1), (0.1, 10)],
        'yticks': [None, [0, 0.5, 1], None],
        'log_scale': [False, False, True],
    },
    {
        "title": "(g) Read latency (average)",
        "ylabel": "Avg read latency (ms)",
        "getter": lambda d: float(d['read']['Average'] / 1000),
        "ylims": [None, (0.1, 4), (0.1, 40)],
        "log_scale": [False, True, True]
    },
    {
        "title": "(h) Read latency (99th percentile)",
        "ylabel": "P99 read latency (ms)",
        "getter": lambda d: float(d['read']['99%'] / 1000),
        "ylims": [None, (1, 40), (1, 1000)],
        "log_scale": [False, True, True]
    },
    {
        "title": "(i) Space amplification (average)",
        "ylabel": "Average space amp",
        "getter": lambda d: d['report']['size'].mean() / unique_size_bytes,
        "ylims": [(0, 3), (0, 7.5), (0, 12)],
        "log_scale": [False, False, False]
    },
    {
        "title": "(j) Space amplification (max)",
        "ylabel": "Max space amp",
        "getter": lambda d: d['report']['size'].max() / unique_size_bytes,
        "ylims": [(0, 3), (0, 7.5), (0, 12)],
        "log_scale": [False, False, False]
    }
]

fig = plt.figure(dpi=300, figsize=(cm_to_inch(DOUBLE_COL_WIDTH), cm_to_inch(20)))

outer_grid = gridspec.GridSpec(5, 2, figure=fig, hspace=0.37, wspace=0.2, 
                               left=0.08, right=0.99, top=0.92, bottom=0.06) 

for p_idx, panel in enumerate(panels):
    row, col = divmod(p_idx, 2)
    inner_grid = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=outer_grid[row, col], wspace=0.4)
    for i in range(len(vec_write_MB_s)):
        ax = plt.Subplot(fig, inner_grid[i])
        fig.add_subplot(ax)

        ax.set_xlabel(f"{vec_write_MB_s[i]}MB/s")
        ax.set_xticks([])

        if i == 0:
            ax.set_ylabel(panel['ylabel'])
        if panel['log_scale'][i]:
            ax.set_yscale('log')
            ax.tick_params(axis='y', pad=1)
        if panel['ylims'][i] is not None:
            ax.set_ylim(panel['ylims'][i])
        if 'yticks' in panel and panel['yticks'][i] is not None:
            ax.set_yticks(panel['yticks'][i])
        ax.tick_params(axis='y', which='minor', labelleft=False)
        ax.set_axisbelow(True)
        ax.grid(axis='y')

        for version_idx, version in enumerate(versions):
            x = -cluster_width / 2 + bar_width / 2 + version_idx * bar_width
            dataset = data_cache[i][version_idx]
            val = panel['getter'](dataset)
            ax.bar(x, val, width=bar_width, edgecolor='black', linewidth=0.5, 
                   color=version['color'], hatch=version['hatch'])
    bbox = outer_grid[row, col].get_position(fig)
    fig.text(bbox.x0 + bbox.width/2, bbox.y0 - 0.025, panel['title'], ha='center', va='top')

handles = [mpl.patches.Patch(facecolor=v['color'], hatch=v['hatch'], 
                             edgecolor='black', linewidth=0.5) for v in versions]
fig.legend(handles=handles, labels=version_names, ncol=len(versions), 
           loc='upper center', bbox_to_anchor=(0.5, 0.99), frameon=False, 
           handlelength=1.5, handletextpad=0.5, columnspacing=1.0)

pdf_path = os.path.join(dir, f'const-write-rates{value}{compaction}-warmup-{warmup_secs}-run-{run_secs}{read_workload}.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print(f'Plot saved to {pdf_path}')
