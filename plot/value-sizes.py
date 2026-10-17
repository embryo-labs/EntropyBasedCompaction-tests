#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
    print('Usage: ' + sys.argv[0] + ' dir')
    exit()
dir = sys.argv[1]

compaction = '-compaction-200MB-s'
warmup_secs = 1200
run_secs = 1200
read_workload = '-get-0.87-seek-0.13-nexts-48'

unique_size = '10GB'

import json
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import gridspec

import common

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'serif',
    'font.serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 10,
})

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
for version in versions:
    version.update(common.versions[version['path']])
version_names = [v.get('name', v['path']) for v in versions]

def get_data_dir(version, value_size, write_MB_s):
    if version['max-running-bg-jobs'] is not None:
        max_running_bg_jobs = f"-max-running-bg-jobs-{version['max-running-bg-jobs']}"
    else:
        max_running_bg_jobs = ''
    workload = (
        f'readwhilewriting-key-16-value-{value_size}-unique-size-{unique_size}-warmup-secs-{warmup_secs}-run-secs-{run_secs}{max_running_bg_jobs}-write-{write_MB_s}MB-s-no-stall-memtable-8MiB{compaction}{read_workload}'
    )
    return os.path.join(dir, workload, version['path'])

fig = plt.figure(dpi=300, figsize=(common.acmsmall_inch, 1.4), constrained_layout=True)
fig.get_layout_engine().set(
    h_pad=0.01,
    w_pad=0.01,
    wspace=0.13,
    rect=(0, 0.13, 1, 0.79),
)
gs = gridspec.GridSpec(1, 4, figure=fig)

ax_srs = fig.add_subplot(gs[0, :2])
value_sizes = [603, 1000, 2000, 4000, 8000, 16000]
lines = [
    {
        'write_MB_s': 10,
        'color': common.colors[0]['dark'],
        'marker': 'o',
    },
    {
        'write_MB_s': 30,
        'color': common.colors[1]['dark'],
        'marker': 's',
    },
]
ax_srs.set_xlabel('Value size (KB)', labelpad=0)
ax_srs.set_xscale('log', base=2)
ax_srs.tick_params(axis='x', pad=0)
ax_srs.set_xticks([600, 1000, 2000, 4000, 8000, 16000], labels=['0.6', '1', '2', '4', '8', '16'])
ax_srs.set_ylabel('Avg # of runs')

ax_read_lat = []
ax = fig.add_subplot(gs[0, 2])
ax.set_xlabel(f"10MB/s")
ax.set_xticks([])
ax.set_ylabel('Latency (ms)', loc='top')
ax_read_lat.append(ax)

ax = fig.add_subplot(gs[0, 3])
ax.set_xlabel(f"30MB/s")
ax.set_xticks([])
ax_read_lat.append(ax)

handles = []
for v in versions:
    handles.append(mpl.patches.Patch(facecolor=v['facecolor'], hatch=v['hatch'], edgecolor='black', linewidth=0.5))
fig.legend(
    handles=handles,
    labels=version_names,
    ncol=len(versions),
    loc='upper center',
    bbox_to_anchor=(0.76, 1.03),
    frameon=False,
    borderaxespad=0,
    handlelength=1.3,
    handletextpad=0.5,
    columnspacing=0.6,
)

for line in lines:
    average_runs = []
    for value_size in value_sizes:
        report = pd.read_csv(os.path.join(get_data_dir(versions[2], value_size, line['write_MB_s']), 'report.csv'))
        average_runs.append(report['num-sorted-runs'].mean())
    ax_srs.plot(
        value_sizes,
        average_runs,
        color=line['color'],
        marker=line['marker'],
        linewidth=1,
        markersize=3,
        label=f'EBC, {line['write_MB_s']}MB/s',
    )
ax_srs.set_ylim(bottom=0, top=20)
ax_srs.legend(
    loc='center',
    bbox_to_anchor=(0.5, 0.5),
    frameon=False,
    handlelength=1.5,
    handletextpad=0.5,
    labelspacing=0.1,
)

bar_width = 1 / (len(versions) + 1)
cluster_width = bar_width * len(versions)
for i, write_MB_s in enumerate([10, 30]):
    for version_idx, version in enumerate(versions):
        x = -cluster_width / 2 + bar_width / 2 + version_idx * bar_width
        data_dir = get_data_dir(version, 16000, write_MB_s)
        read_latency_us = json.load(open(os.path.join(data_dir, 'read-latency-us.json')))
        ax_read_lat[i].bar(x, read_latency_us['Average'] / 1000, width=bar_width * 0.65, edgecolor='black', linewidth=0.5, facecolor=version['facecolor'], hatch=version['hatch'])

fig.text(0.23, 0.02, '(a) EBC sorted run count across value sizes', ha='center', va='bottom')
fig.text(0.78, 0, '(b) Read latency across compaction\npolicies with 16KB values', ha='center', va='bottom')

pdf_path = os.path.join(dir, f'value-sizes{compaction}-warmup-{warmup_secs}-run-{run_secs}{read_workload}.pdf')
common.check_visible_labels(fig)
fig.savefig(pdf_path, metadata={'CreationDate': None})
print(f'Plot saved to {pdf_path}')
