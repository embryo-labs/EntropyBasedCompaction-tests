#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
    print('Usage: ' + sys.argv[0] + ' dir')
    exit()
dir = sys.argv[1]
mean_step_secs = 100

num_shards = 5

import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec

# Paper specific settings
SINGLE_COL_WIDTH = 8.5
DOUBLE_COL_WIDTH = 17.8
def cm_to_inch(value):
    return value/2.54

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Linux Libertine O'],
})
plt.rcParams['axes.unicode_minus'] = False

versions = [
    {
        'path': 'rocksdb-tuned',
        'name': 'Leveling5',
        'color': plt.cm.tab10(0),
    },
    {
        'path': 'tiering2',
        'name': 'Tiering2',
        'color': plt.cm.tab10(1),
    },
    {
        'path': 'tiering4',
        'name': 'Tiering4',
        'color': plt.cm.tab10(2),
    },
    {
        'path': 'tiering8',
        'name': 'Tiering8',
        'color': plt.cm.tab10(3),
    },
    {
        'path': 'universal',
        'name': 'Universal',
        'color': plt.cm.tab10(4),
    },
    {
        'path': 'benefit-cost',
        'name': 'Entropy-Based',
        'color': plt.cm.tab10(5),
    },
]
linewidth = 1
handles = []
for version in versions:
    handles.append(mpl.lines.Line2D([], [], linewidth=linewidth, color=version['color'], linestyle=None, label=version['name']))

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(DOUBLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
gs = gridspec.GridSpec(1, 3, figure=fig)

def find_data_dir(version_path):
    workload = 'meituan-writer-peak-day-period-secs-14400-num_shards-' + str(num_shards) + '-repeat-1-key-16-value-603-unique-size-10GB-memtable-8MiB'
    if version_path in ['tiering2', 'tiering4', 'tiering8', 'benefit-cost']:
        workload += '-max-running-bg-jobs-1'
    workload += '-compaction-200MB-s-scan-len-meituan-get-0.87-seek-0.13'
    return os.path.join(dir, workload, version_path)

plt.subplot(gs[0, 0])
ax = plt.gca()
plt.xlabel('Time (hours)', fontsize=9)
plt.ylabel('Write speed(MB/s)', fontsize=9)
write_count = pd.read_csv(os.path.join(find_data_dir('benefit-cost'), 'write-count-time.csv'))
write_count = write_count[['secs_elapsed', 'count']]
write_count = write_count.groupby(write_count.index // mean_step_secs).mean()
plt.plot(write_count['secs_elapsed'] / 3600, write_count['count'] * (16 + 503) / 1e6, linewidth=linewidth, color='black')
plt.xticks(fontsize=9)
plt.yticks(fontsize=9)
ax.grid(axis='y')

plt.subplot(gs[0, 1])
ax_num_srs = plt.gca()
plt.xlabel('Time (hours)', fontsize=9)
plt.xticks(fontsize=9)
plt.ylabel('# of sorted runs', fontsize=9)
plt.ylim(0, 50)
plt.yticks(fontsize=9)

plt.subplot(gs[0, 2])
ax_latency = plt.gca()
plt.xlabel('Time (hours)', fontsize=9)
plt.xticks(fontsize=9)
plt.ylabel('Read latency (us)', fontsize=9)
plt.ylim((0, 2000))
plt.yticks(fontsize=9)

for version in versions:
    data_dir = find_data_dir(version['path'])
    report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
    report = report[['secs_elapsed', 'num-sorted-runs']]
    report = report.groupby(report.index // mean_step_secs).mean()
    ax_num_srs.plot(report['secs_elapsed'] / 3600, report['num-sorted-runs'], linewidth=linewidth, color=version['color'])

    read_count_time = pd.read_csv(os.path.join(data_dir, 'read-count-time.csv'))

    time = read_count_time['secs_elapsed']
    time = time.groupby(time.index // mean_step_secs).mean()

    micros = read_count_time['micros']
    count = read_count_time['count']
    read_latency = micros.groupby(micros.index // mean_step_secs).sum() / count.groupby(count.index // mean_step_secs).sum()

    ax_latency.plot(time / 3600, read_latency, linewidth=linewidth, color=version['color'])
ax_num_srs.grid(axis='y')
ax_latency.grid(axis='y')

fig.legend(handles=handles, fontsize=9, ncol=len(handles), loc='center', bbox_to_anchor=(0.5, 1.03), handlelength=1, handletextpad=0.5, columnspacing=1.5, frameon=False)
pdf_path = os.path.join(dir, 'meituan-num_shards-' + str(num_shards) + '.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show()
