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
    'font.family': 'serif',
    'font.serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 9,
})

vec_write_MB_s = [10, 30, 50]

versions = [
    {
        'path': 'preempt_only_by_entropy-be-0',
        'name': 'Only-by-entropy',
        'max-running-bg-jobs': 1,
        'color': common.colors[0]['light'],
        'hatch': '--//',
    },
    {
        'path': 'preempt_only_by_num',
        'name': 'Only-by-num',
        'max-running-bg-jobs': 1,
        'color': common.colors[1]['light'],
        'hatch': '---',
    },
    {
        'path': 'no_exclude_small',
        'name': 'No-exclude-small',
        'max-running-bg-jobs': 1,
        'color': common.colors[3]['light'],
        'hatch': '--\\\\',
    },
    {
        'path': 'entropy-based',
        'name': 'Soft-preemption',
        'max-running-bg-jobs': None,
        'color': common.colors[4]['light'],
        'hatch': '\\\\\\',
    },
    {
        'path': 'entropy-based',
        'name': common.versions['entropy-based']['name'],
        'max-running-bg-jobs': 1,
        'color': common.versions['entropy-based']['facecolor'],
        'hatch': '///',
    },
]
version_names = [v['name'] for v in versions]

bar_width = 1 / (len(versions) + 1)
cluster_width = bar_width * len(versions)

row_configs = [
    {
        'ylabel': 'Avg # of sorted runs',
        'ylims': [(1, None), (10, None), (10, None)],
        'log-scale': [True, True, True],
        'ax': [],
    },
]

fig = plt.figure(dpi=300, figsize=(common.single_col_inch, 2.1), constrained_layout=True)
gs = gridspec.GridSpec(2, 3, figure=fig)
for row, row_config in enumerate(row_configs):
    for col, write_MB_s in enumerate(vec_write_MB_s):
        plt.subplot(gs[row, col])
        ax = plt.gca()
        plt.xlabel(f'{write_MB_s}MB/s')
        plt.xticks([])
        if col == 0:
            plt.ylabel(row_config['ylabel'])
        if row_config['log-scale'][col]:
            plt.yscale('log')
        ax.set_axisbelow(True)
        ax.grid(axis='y')
        row_config['ax'].append(ax)

for col, write_MB_s in enumerate(vec_write_MB_s):
    for version_idx, version in enumerate(versions):
        x = -cluster_width / 2 + bar_width / 2 + version_idx * bar_width
        if version['max-running-bg-jobs'] is not None:
            max_running_bg_jobs = '-max-running-bg-jobs-1'
        else:
            max_running_bg_jobs = ''
        if version['path'] == 'benefit-cost':
            compaction_trigger = ''
        else:
            compaction_trigger = '-compaction-trigger-2'
        workload = f'readwhilewriting-key-16{value}-unique-size-10GB-warmup-secs-{warmup_secs}-run-secs-{run_secs}{compaction_trigger}-memtable-8MiB{max_running_bg_jobs}{compaction}-write-{write_MB_s}MB-s{read_workload}'
        data_dir = os.path.join(dir, workload, version['path'])
        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        row_configs[0]['ax'][col].bar(x, report['num-sorted-runs'].mean(), width=bar_width, edgecolor='black', linewidth=0.5, facecolor=version['color'], hatch=version['hatch'])

for row, row_config in enumerate(row_configs):
    for col in range(0, len(vec_write_MB_s)):
        if row_config['ylims'][col] is not None:
            row_config['ax'][col].set_ylim(row_config['ylims'][col])

fig.legend(version_names, fontsize=9, ncol=3, loc='center', bbox_to_anchor=(0.5, 1.08), frameon=False, handlelength=1.5, handletextpad=0.5, columnspacing=1.0)
pdf_path = os.path.join(dir, f'ablation-study{value}{compaction}-warmup-{warmup_secs}-run-{run_secs}{read_workload}.pdf')
fig.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
