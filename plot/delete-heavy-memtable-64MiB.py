#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
	print('Usage: ' + sys.argv[0] + ' dir')
	exit()
dir = sys.argv[1]

value = '-value-603'
compaction = '-compaction-200MB-s'
read_workload = '-get-0.87-seek-0.13-nexts-48'

import json
import os
import pandas as pd
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

vec_write_MB_s = [10, 30]

versions = [
    {
        'path': 'rocksdb-tuned',
        'max-running-bg-jobs': None,
    },
    {
        'path': 'tiering4',
        'max-running-bg-jobs': 1,
    },
    {
        'path': 'entropy-based',
        'max-running-bg-jobs': 1,
    },
]
for v in versions:
    if v['path'] in common.versions:
        v.update(common.versions[v['path']])
version_names = [v.get('name', v['path']) for v in versions]

bar_width = 1 / (len(versions) + 1)
cluster_width = 1 / (len(versions) + 1) * len(versions)

panels = [
    {
        'title': '(a) Delete-heavy',
        'workload': 'readwhilewriting-key-16{value}-unique-size-10GB-warmup-secs-1200-run-secs-1200{max_running_bg_jobs}-write-{write_MB_s}MB-s-no-stall-memtable-8MiB{compaction}{read_workload}-delete-heavy',
        'ax': [],
    },
    {
        'title': '(b) 64MiB MemTable',
        'workload': 'readwhilewriting-key-16{value}-unique-size-100GB-warmup-secs-10800-run-secs-10800{max_running_bg_jobs}-write-{write_MB_s}MB-s-no-stall{compaction}{read_workload}',
        'ax': [],
    },
]
fig = plt.figure(dpi=300, figsize=(common.acmsmall_inch, 1.1), constrained_layout=True)
fig.get_layout_engine().set(
    h_pad=0.01,
    w_pad=0.01,
    wspace=0.15,
    rect=(0, 0.13, 1, 0.72),
)
gs = gridspec.GridSpec(1, 5, figure=fig, width_ratios=[1, 1, 0.2, 1, 1])
for panel_idx, panel in enumerate(panels):
    for i, write_MB_s in enumerate(vec_write_MB_s):
        ax = plt.subplot(gs[0, panel_idx * (len(vec_write_MB_s) + 1) + i])
        panel['ax'].append(ax)
        ax.set_xlabel(f'{write_MB_s}MB/s')
        ax.set_xticks([])
        if i == 0:
            ax.set_ylabel('Latency (ms)', loc='top')

handles = []
version_names = []
for version in versions:
    handles.append(mpl.patches.Patch(facecolor=version['facecolor'], hatch=version['hatch'], edgecolor='black', linewidth=0.5))
    version_names.append(version['name'])
fig.legend(
    handles=handles,
    labels=version_names,
    ncol=len(versions), 
    loc='upper center',
    bbox_to_anchor=(0.5, 1.04),
    frameon=False,
    borderaxespad=0,
    handlelength=1.3,
    handletextpad=0.5,
    columnspacing=2.5,
)

fig.text(0.27, 0, panels[0]['title'], ha='center', va='bottom')
fig.text(0.8, 0, panels[1]['title'], ha='center', va='bottom')

for panel_idx, panel in enumerate(panels):
    for i, write_MB_s in enumerate(vec_write_MB_s):
        for version_idx, version in enumerate(versions):
            x = -cluster_width / 2 + bar_width / 2 + version_idx * bar_width
            if version['max-running-bg-jobs'] is None:
                max_running_bg_jobs = ''
            else:
                max_running_bg_jobs = '-max-running-bg-jobs-1'
            workload = panel['workload'].format(
                value=value,
                compaction=compaction,
                read_workload=read_workload,
                max_running_bg_jobs=max_running_bg_jobs,
                write_MB_s = write_MB_s,
            )
            data_dir = os.path.join(dir, workload, version['path'])
            read_latency_us = json.load(open(os.path.join(data_dir, 'read-latency-us.json')))
            panel['ax'][i].bar(x, read_latency_us['Average'] / 1000, width=bar_width * 0.65, edgecolor='black', linewidth=0.5, facecolor=version['facecolor'], hatch=version['hatch'])

pdf_path = os.path.join(dir, f'delete-heavy-memtable-64MiB{value}{compaction}{read_workload}.pdf')
common.check_visible_labels(fig)
fig.savefig(pdf_path, metadata={'CreationDate': None})
print(f'Plot saved to {pdf_path}')
