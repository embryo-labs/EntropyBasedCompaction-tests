#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
	print('Usage: ' + sys.argv[0] + ' dir')
	exit()
dir = sys.argv[1]

value = '-value-603'
warmup_secs = 1500
run_secs = 1000
compaction = '-compaction-200MB-s'
read_workload = '-nexts-48-seek-1'

import os
import numpy as np
import pandas as pd
import json
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

import common

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 9,
})

vec_write_MB_s = [10, 50]
versions = [
    {
        'k_n': 1.4,
        'color': plt.get_cmap('tab20c')(1),
        'hatch': '---',
    },
    {
        'k_n': 1.7,
        'color': common.versions['benefit-cost']['color'],
        'hatch': common.versions['benefit-cost']['hatch'],
    },
    {
        'k_n': 2,
        'color': plt.get_cmap('tab20c')(6),
        'hatch': '\\\\\\',
    },
    {
        'k_n': 4,
        'color': '#ff6060',
        'hatch': '--//',
    },
    {
        'k_n': 8,
        'color': plt.get_cmap('tab20c')(13),
        'hatch': 'XX',
    },
    {
        'k_n': 16,
        'color': plt.get_cmap('tab20')(11),
        'hatch': '--\\\\',
    },
    {
        'k_n': 32,
        'color': 'C6',
        'hatch': '--XX',
    },
    {
        'k_n': 64,
        'color': plt.get_cmap('tab20c')(17),
        'hatch': 'XXXX',
    }
]

bar_width = 1 / (len(versions) + 1)
cluster_width = bar_width * len(versions)

fig = plt.figure(dpi=300, figsize=(common.single_col_inch, 1.3), constrained_layout=True)
gs = GridSpec(1, len(vec_write_MB_s), figure=fig)
for i, write_MB_s in enumerate(vec_write_MB_s):
    plt.subplot(gs[0, i])
    ax = plt.gca()
    plt.xlabel(f'{write_MB_s}MB/s')
    plt.xticks([])
    if i == 0:
        plt.ylabel('P99 # of sorted runs')

    for version_idx, version in enumerate(versions):
        x = -cluster_width / 2 + bar_width / 2 + version_idx * bar_width
        k_n = version['k_n']
        if k_n == 1.7:
            workload = 'readwhilewriting-key-16' + value + '-unique-size-10GB-warmup-secs-' + str(warmup_secs) + '-run-secs-' + str(run_secs) + '-memtable-8MiB-max-running-bg-jobs-1' + compaction + '-write-' + str(write_MB_s) + 'MB-s' + read_workload
        else:
            workload = 'readwhilewriting-key-16' + value + '-unique-size-10GB-warmup-secs-' + str(warmup_secs) + '-run-secs-' + str(run_secs) + '-k_n-' + str(k_n) + '-memtable-8MiB-max-running-bg-jobs-1' + compaction + '-write-' + str(write_MB_s) + 'MB-s' + read_workload
        data_dir = os.path.join(dir, workload, 'benefit-cost')

        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        ax.bar(x, np.percentile(report['num-sorted-runs'], 99), width=bar_width, facecolor=version['color'], edgecolor='black', linewidth=0.5, hatch=version['hatch'])

names = []
for version in versions:
    k_n = version['k_n']
    if k_n == 1.7:
        names.append(common.versions['benefit-cost']['name'] + ' (' + str(k_n) + ')')
    else:
        names.append(str(k_n))
fig.legend(names, fontsize=9, ncol=4, loc='center', bbox_to_anchor=(0.5, 1.1), frameon=False, handlelength=1.5, handletextpad=0.5)
pdf_path = os.path.join(dir, f'sensitivity-k_n{value}{compaction}-warmup-{warmup_secs}-run-{run_secs}{read_workload}.pdf')
fig.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
