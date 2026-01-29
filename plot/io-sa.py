#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
	print('Usage: ' + sys.argv[0] + ' dir')
	exit()
dir = sys.argv[1]

value = '-value-603'
compaction = '-compaction-200MB-s'
warmup_secs = 1500
run_secs = 1000
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
    'font.family': 'sans-serif',
    'font.sans-serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 9,
})

import common


versions = [
    {
        'path': 'rocksdb-tuned',
    },
    {
        'path': 'universal',
    },
    {
        'path': 'benefit-cost',
    },
    {
        'reserve-MB-s': 10,
        'facecolor': common.colors[1]['light'],
        'hatch': '---',
    },
    {
        'reserve-MB-s': 30,
        'facecolor': common.colors[3]['light'],
        'hatch': '--\\\\'
    },
    {
        'reserve-MB-s': 50,
        'facecolor': common.colors[4]['light'],
        'hatch': '--//',
    },
    {
        'reserve-MB-s': 70,
        'facecolor': common.colors[6]['light'],
        'hatch': '--XX'
    },
    {
        'reserve-MB-s': 90,
        'facecolor': common.colors[7]['light'],
        'hatch': 'XXXX',
    },
]
version_names = []
for version in versions:
    if 'path' in version:
        version_names.append(common.versions[version['path']]['name'])
        version.update(common.versions[version['path']])
    else:
        version_names.append(str(version['reserve-MB-s']) + 'MB/s')

bar_width = 1 / (len(versions) + 1)
cluster_width = bar_width * len(versions)

vec_write_MB_s = [30, 50]

panels = [
    {
        'title': '(a) Number of sorted runs (99th percentile)',
        'title-xy': (0.5, 0.54),
        'ylabel': 'P99 # of sorted runs',
        'ax': [],
    },
    {
        'title': '(b) Space amplification (max)',
        'title-xy': (0.5, 0),
        'ylabel': 'Max space amp',
        'ax':[],
    }
]

fig = plt.figure(dpi=300, figsize=(common.single_col_inch, 2.7), constrained_layout=True)
gs = GridSpec(2, 2, figure=fig, hspace=0.2)

for row, panel in enumerate(panels):
    (x, y) = panel['title-xy']
    fig.text(x, y, panel['title'], ha='center', va='top')
    for col, write_MB_s in enumerate(vec_write_MB_s):
        plt.subplot(gs[row, col])
        ax = plt.gca()
        plt.xlabel(f'User write {write_MB_s}MB/s')
        plt.xticks([])
        if col == 0:
            plt.ylabel(panel['ylabel'])
        panel['ax'].append(ax)
handles = [mpl.patches.Patch(facecolor=v['facecolor'], hatch=v['hatch'], 
                            edgecolor='black', linewidth=0.5) for v in versions]
fig.legend(handles=handles, labels=version_names, ncol=4, 
        loc='upper center', bbox_to_anchor=(0.5, 1.14), frameon=False, borderaxespad=0,
        handlelength=1.2, handletextpad=0.5, columnspacing=1.0)

for col, write_MB_s in enumerate(vec_write_MB_s):
    for version_idx, version in enumerate(versions):
        x = -cluster_width / 2 + bar_width / 2 + version_idx * bar_width
        if 'path' in version:
            if version['path'] in ['rocksdb-tuned', 'universal']:
                workload = 'readwhilewriting-key-16' + value + '-unique-size-10GB-warmup-secs-' + str(warmup_secs) + '-run-secs-' + str(run_secs) + '-memtable-8MiB' + compaction + '-write-' + str(write_MB_s) + 'MB-s' + read_workload
                data_dir = os.path.join(dir, workload, version['path'])
            else:
                assert version['path'] == 'benefit-cost'
                workload = 'readwhilewriting-key-16' + value + '-unique-size-10GB-warmup-secs-' + str(warmup_secs) + '-run-secs-' + str(run_secs) + '-memtable-8MiB-max-running-bg-jobs-1' + compaction + '-write-' + str(write_MB_s) + 'MB-s' + read_workload
                data_dir = os.path.join(dir, workload, 'benefit-cost')
        else:
            workload = 'readwhilewriting-key-16' + value + '-unique-size-10GB-warmup-secs-' + str(warmup_secs) + '-run-secs-' + str(run_secs) + '-memtable-8MiB-max-running-bg-jobs-1-io_sa-' + str(version['reserve-MB-s']) + 'MB-s' + compaction + '-write-' + str(write_MB_s) + 'MB-s' + read_workload
            data_dir = os.path.join(dir, workload, 'benefit-cost')

        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        panels[0]['ax'][col].bar(x, np.percentile(report['num-sorted-runs'], 99), width=bar_width, facecolor=version['facecolor'], edgecolor='black', linewidth=0.5, hatch=version['hatch'])
        panels[1]['ax'][col].bar(x, report['size'].max() / unique_size_bytes, width=bar_width, facecolor=version['facecolor'], edgecolor='black', linewidth=0.5, hatch=version['hatch'])

renderer = fig.canvas.get_renderer()
tight_bbox = fig.get_tightbbox(renderer)
print(f'width: {tight_bbox.width}, height: {tight_bbox.height}')

pdf_path = os.path.join(dir, f'io-sa-p99-srs-max-sa{value}{compaction}-warmup-{warmup_secs}-run-{run_secs}{read_workload}.pdf')
fig.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
