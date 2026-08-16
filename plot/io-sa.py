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
from matplotlib.gridspec import GridSpec

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'serif',
    'font.serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 9,
})

import common

our_path = 'entropy-based'
versions = [
    {
        'path': 'rocksdb-tuned',
    },
    {
        'path': 'universal-hard-trigger',
    },
    {
        'path': our_path,
    },
    {
        'path': our_path,
        'reserve-MB-s': 10,
        'facecolor': common.colors[1]['light'],
        'hatch': '---',
    },
    {
        'path': our_path,
        'reserve-MB-s': 30,
        'facecolor': common.colors[3]['light'],
        'hatch': '--\\\\'
    },
    {
        'path': our_path,
        'reserve-MB-s': 50,
        'facecolor': common.colors[4]['light'],
        'hatch': '--//',
    },
    {
        'path': our_path,
        'reserve-MB-s': 70,
        'facecolor': common.colors[6]['light'],
        'hatch': '--XX'
    },
    {
        'path': our_path,
        'reserve-MB-s': 90,
        'facecolor': common.colors[7]['light'],
        'hatch': 'XXXX',
    },
]
version_names = []
for version in versions:
    if 'reserve-MB-s' in version:
        version_names.append(str(version['reserve-MB-s']) + 'MB/s')
    else:
        version_names.append(common.versions[version['path']]['name'])
        version.update(common.versions[version['path']])

bar_width = 1 / (len(versions) + 1)
cluster_width = bar_width * len(versions)

vec_write_MB_s = [30, 50]

panels = [
    {
        'title': '(a) P99 # of sorted runs',
        'title-xy': (0.25, 0),
        'ylabel': 'P99 # of runs',
        'ax': [],
    },
    {
        'title': '(b) Max space amplification',
        'title-xy': (0.75, 0),
        'ylabel': 'Max space amp',
        'ax':[],
    }
]

fig = plt.figure(dpi=300, figsize=(common.single_col_inch, 1.3), constrained_layout=True)
fig.get_layout_engine().set(
    h_pad=0.01,
    w_pad=0.01,
    wspace=0.07,
    rect=(0, 0.1, 1, 0.7),
)
gs = GridSpec(1, 4, figure=fig)

for panel_idx, panel in enumerate(panels):
    (x, y) = panel['title-xy']
    fig.text(x, y, panel['title'], ha='center', va='bottom')
    for i, write_MB_s in enumerate(vec_write_MB_s):
        ax = plt.subplot(gs[0, panel_idx * len(vec_write_MB_s) + i])
        plt.xlabel(f'{write_MB_s}MB/s')
        plt.xticks([])
        ax.tick_params(axis='y', pad=1)
        if i == 0:
            plt.ylabel(panel['ylabel'], loc='top', labelpad=1)
        panel['ax'].append(ax)
handles = [mpl.patches.Patch(facecolor=v['facecolor'], hatch=v['hatch'], 
                            edgecolor='black', linewidth=0.5) for v in versions]
fig.legend(
    handles=handles,
    labels=version_names,
    ncol=4, 
    loc='upper center',
    bbox_to_anchor=(0.5, 1.03),
    frameon=False,
    borderaxespad=0,
    handlelength=1.2,
    handletextpad=0.5,
    columnspacing=1.0,
    labelspacing=0.2,
)

for col, write_MB_s in enumerate(vec_write_MB_s):
    for version_idx, version in enumerate(versions):
        x = -cluster_width / 2 + bar_width / 2 + version_idx * bar_width
        if 'reserve-MB-s' in version:
            io_sa = '-io_sa-' + str(version['reserve-MB-s']) + 'MB-s'
        else:
            io_sa = ''
        if version['path'] == our_path:
            compaction_trigger = '-compaction-trigger-2'
            max_running_bg_jobs = '-max-running-bg-jobs-1'
        else:
            compaction_trigger = ''
            max_running_bg_jobs = ''
        workload = f'readwhilewriting-key-16{value}-unique-size-10GB-warmup-secs-{warmup_secs}-run-secs-{run_secs}{compaction_trigger}-memtable-8MiB{max_running_bg_jobs}{io_sa}{compaction}-write-{write_MB_s}MB-s{read_workload}'
        data_dir = os.path.join(dir, workload, version['path'])

        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        panels[0]['ax'][col].bar(x, np.percentile(report['num-sorted-runs'], 99), width=bar_width, facecolor=version['facecolor'], edgecolor='black', linewidth=0.5, hatch=version['hatch'])
        panels[1]['ax'][col].bar(x, report['size'].max() / unique_size_bytes, width=bar_width, facecolor=version['facecolor'], edgecolor='black', linewidth=0.5, hatch=version['hatch'])

renderer = fig.canvas.get_renderer()
tight_bbox = fig.get_tightbbox(renderer)
print(f'width: {tight_bbox.width}, height: {tight_bbox.height}')

pdf_path = os.path.join(dir, f'io-sa-p99-srs-max-sa{value}{compaction}-warmup-{warmup_secs}-run-{run_secs}{read_workload}.pdf')
fig.savefig(pdf_path, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
