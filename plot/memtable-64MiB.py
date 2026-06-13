#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
	print('Usage: ' + sys.argv[0] + ' dir')
	exit()
dir = sys.argv[1]

value = '-value-603'
compaction = '-compaction-200MB-s'
warmup_secs = 3 * 3600
run_secs = 3 * 3600
read_workload = '-get-0.87-seek-0.13-nexts-48'

unique_size = '100GB'

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

import common

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'serif',
    'font.serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 9,
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
path_version = {}
for v in versions:
    if v['path'] in common.versions:
        v.update(common.versions[v['path']])
    path_version[v['path']] = v
version_names = [v.get('name', v['path']) for v in versions]

map_path_to_version_idx = {}
for version_idx, v in enumerate(versions):
    map_path_to_version_idx[v['path']] = version_idx

bar_width = 1 / (len(versions) + 1)
cluster_width = 1 / (len(versions) + 1) * len(versions)

fig = plt.figure(dpi=300, figsize=(3.1, 1.2), constrained_layout=True)
gs = gridspec.GridSpec(1, 2, figure=fig)
plt.subplot(gs[0, 0])
ax_10 = plt.gca()
plt.xlabel('(a) User write 10MB/s')
plt.xticks([])
plt.ylabel('Avg # of sorted runs')

plt.subplot(gs[0, 1])
ax_30 = plt.gca()
plt.xlabel('(b) User write 30MB/s')
plt.xticks([])

handles = []
version_names = []
for v_intro in versions:
    v = path_version[v_intro['path']]
    handles.append(mpl.patches.Patch(facecolor=v['facecolor'], hatch=v['hatch'], edgecolor='black', linewidth=0.5))
    version_names.append(v_intro['name'])
fig.legend(handles=handles, labels=version_names, ncol=len(versions), 
        loc='upper center', bbox_to_anchor=(0.56, 1.2), frameon=False, 
        handlelength=1.3, handletextpad=0.5, columnspacing=1.0)

for i, write_MB_s in enumerate(vec_write_MB_s):
    for version_idx, version in enumerate(versions):
        x = -cluster_width / 2 + bar_width / 2 + version_idx * bar_width
        if version['path'] in ['entropy-based']:
            compaction_trigger = '-compaction-trigger-2'
        else:
            compaction_trigger = ''
        if version['max-running-bg-jobs'] is None:
            max_running_bg_jobs = ''
        else:
            max_running_bg_jobs = '-max-running-bg-jobs-1'
        workload = f'readwhilewriting-key-16{value}-unique-size-{unique_size}-warmup-secs-{warmup_secs}-run-secs-{run_secs}{compaction_trigger}{max_running_bg_jobs}{compaction}-write-{write_MB_s}MB-s{read_workload}'
        data_dir = os.path.join(dir, workload, version['path'])
        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        read_latency_us = json.load(open(os.path.join(data_dir, 'read-latency-us.json')))
        scan_latency_us = json.load(open(os.path.join(data_dir, 'seek-latency-us.json')))
        get_latency_us = json.load(open(os.path.join(data_dir, 'get-latency-us.json')))

        num_srs_avg = report['num-sorted-runs'].mean()

        version_idx = map_path_to_version_idx[version['path']]
        match write_MB_s:
            case 10:
                ax = ax_10
            case 30:
                ax = ax_30
            case _:
                assert False
        x = -cluster_width / 2 + bar_width / 2 + version_idx * bar_width
        ax.bar(x, num_srs_avg, width=bar_width * 0.65, edgecolor='black', linewidth=0.5, facecolor=version['facecolor'], hatch=version['hatch'])

ax_30.set_ylim(bottom=1)
pdf_path = os.path.join(dir, f'memtable-64MiB{value}{compaction}-warmup-{warmup_secs}-run-{run_secs}{read_workload}.pdf')
fig.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print(f'Plot saved to {pdf_path}')
