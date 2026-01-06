#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
    print('Usage: ' + sys.argv[0] + ' dir')
    exit()
dir = sys.argv[1]
mean_step_secs = 300

num_shards = 5
period_secs = 14400
read_workload = 'nexts-50-seek-1'
unique_size = '10GB'

import humanfriendly
unique_size_bytes = humanfriendly.parse_size(unique_size)

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

for day_type in ['peak', 'normal']:
    fig = plt.figure(dpi = 300, figsize = (cm_to_inch(DOUBLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
    gs = gridspec.GridSpec(1, 3, figure=fig)

    def find_data_dir(version_path):
        workload = 'meituan-writer-' + day_type + '-day-period-secs-' + str(period_secs) + '-num_shards-' + str(num_shards) + '-key-16-value-603-unique-size-' + unique_size + '-memtable-8MiB'
        if version_path in ['tiering2', 'tiering4', 'tiering8', 'tiering2-auto', 'benefit-cost']:
            workload += '-max-running-bg-jobs-1'
        workload += '-compaction-200MB-s-' + read_workload
        return os.path.join(dir, workload, version_path)

    plt.subplot(gs[0, 0])
    ax_num_srs = plt.gca()
    plt.xlabel('Time (hours)', fontsize=9)
    plt.xticks(fontsize=9)
    plt.ylabel('# of sorted runs', fontsize=9)
    plt.ylim(0, 100)
    plt.yticks(fontsize=9)

    plt.subplot(gs[0, 1])
    ax_latency = plt.gca()
    plt.xlabel('Time (hours)', fontsize=9)
    plt.xticks(fontsize=9)
    plt.ylabel('Read latency (us)', fontsize=9)
    plt.ylim((0, 10000))
    plt.yticks(fontsize=9)

    plt.subplot(gs[0, 2])
    ax_space = plt.gca()
    plt.xlabel('Time (hours)', fontsize=9)
    plt.xticks(fontsize=9)
    plt.ylabel('Space amplification', fontsize=9)
    plt.ylim((1, 5))
    plt.yticks(fontsize=9)

    for version in versions:
        data_dir = find_data_dir(version['path'])
        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        report = report[['secs_elapsed', 'num-sorted-runs', 'size']]
        report = report.groupby(report.index // mean_step_secs).mean()
        ax_num_srs.plot(report['secs_elapsed'] / 3600, report['num-sorted-runs'], linewidth=linewidth, color=version['color'])
        ax_space.plot(report['secs_elapsed'] / 3600, report['size'] / unique_size_bytes, linewidth=linewidth, color=version['color'])

        read_count_time = pd.read_csv(os.path.join(data_dir, 'read-count-time.csv'))

        time = read_count_time['secs_elapsed']
        time = time.groupby(time.index // mean_step_secs).mean()

        micros = read_count_time['micros']
        count = read_count_time['count']
        read_latency = micros.groupby(micros.index // mean_step_secs).sum() / count.groupby(count.index // mean_step_secs).sum()

        ax_latency.plot(time / 3600, read_latency, linewidth=linewidth, color=version['color'])
    ax_num_srs.grid(axis='y')
    ax_latency.grid(axis='y')

    fig.legend(handles=handles, fontsize=9, ncol=4, loc='center', bbox_to_anchor=(0.5, 1.1), handlelength=1, handletextpad=0.5, columnspacing=1.5, frameon=False)
    pdf_path = os.path.join(dir, 'meituan-' + day_type + '-day-num_shards-' + str(num_shards) + '-unique_size-' + unique_size + '-period_secs-' + str(period_secs) + '-' + read_workload + '-mean_step_secs-' + str(mean_step_secs) + '.pdf')
    plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
    print('Plot saved to ' + pdf_path)
    if 'DISPLAY' in os.environ:
        plt.show()
