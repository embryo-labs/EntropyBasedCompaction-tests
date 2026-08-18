#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
	print('Usage: ' + sys.argv[0] + ' dir')
	exit()
dir = sys.argv[1]

value = '-value-603'
compaction_MB_s = 200
warmup_secs = 1200
run_secs = 1200
read_workload = '-get-0.87-seek-0.13-nexts-48'

compaction = f'-compaction-{compaction_MB_s}MB-s'
version_path = 'no_preemption_conditions'

import os
import bisect
import json
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

import common

# Paper specific settings
SINGLE_COL_WIDTH = 8.5
DOUBLE_COL_WIDTH = 17.8
def cm_to_inch(value):
    return value/2.54

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'serif',
    'font.serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 9,
})

lines_config = [
    {
        'write_MB_s': 10,
        'entropy_thresholds': [0, 1, 2, 3, 4, 5, 6],
        'color': common.colors[0]['dark'],
        'marker': 'o',
        'markersize': 10,
    },
    {
        'write_MB_s': 20,
        'entropy_thresholds': [0, 0.5, 0.9, 1, 2, 3, 4, 5, 6],
        'color': common.colors[1]['dark'],
        'marker': 'D',
        'markersize': 10,
    },
    {
        'write_MB_s': 30,
        'entropy_thresholds': [0, 1, 1.5, 1.6, 2, 2.5, 3, 4, 5, 6],
        'color': common.colors[3]['dark'],
        'marker': '^',
        'markersize': 15,
    },
    {
        'write_MB_s': 40,
        'entropy_thresholds': [0, 1, 1.5, 2, 2.3, 2.5, 2.8, 3, 3.5, 4, 5, 6],
        'color': common.colors[4]['dark'],
        'marker': 'v',
        'markersize': 15,
    },
    {
        'write_MB_s': 50,
        'entropy_thresholds': [2.5, 3, 3.1, 3.2, 3.5, 4, 5, 6],
        'color': common.colors[5]['dark'],
        'marker': '<',
        'markersize': 15,
    },
    {
        'write_MB_s': 60,
        'entropy_thresholds': [3.7, 3.8, 3.9, 4, 4.5, 5, 5.5, 6],
        'color': common.colors[6]['dark'],
        'marker': '>',
        'markersize': 15,
    },
]

fig = plt.figure(dpi=300, figsize=(common.single_col_inch, 1.5), constrained_layout=True)
fig.get_layout_engine().set(
    h_pad=0.01,
    w_pad=0.01,
    rect=(0, 0, 1, 0.81),
)
gs = GridSpec(1, 2, figure=fig, hspace=0.2)
plt.subplot(gs[0, 0])
ax_srs_avg = plt.gca()
plt.ylabel('Avg # of sorted runs', loc='top')
plt.xlabel('Entropy threshold', labelpad=1)
plt.xticks([0, 1, 2, 3, 4, 5, 6])
ax_srs_avg.set_axisbelow(True)
ax_srs_avg.grid()

plt.subplot(gs[0, 1])
ax_srs_p99 = plt.gca()
plt.ylabel('P99 # of sorted runs', loc='top')
plt.xlabel('Entropy threshold', labelpad=1)
plt.xticks([0, 1, 2, 3, 4, 5, 6])
ax_srs_p99.set_axisbelow(True)
ax_srs_p99.grid()

txt_file = open(os.path.join(dir, f'{version_path}{value}{compaction}-warmup-{warmup_secs}-run-{run_secs}{read_workload}.txt'), 'w')
version_names = []
for line_config in lines_config:
    write_MB_s = line_config['write_MB_s']
    entropy_thresholds = line_config['entropy_thresholds']
    version_names.append(f'{write_MB_s}MB/s')

    entropy_threshold_by_theory = None
    for line in open(os.path.join(dir, f'readwhilewriting-key-16{value}-unique-size-10GB-warmup-secs-{warmup_secs}-run-secs-{run_secs}-autotune_entropy_threshold-write-{write_MB_s}MB-s-no-stall-memtable-8MiB{compaction}{read_workload}', version_path, 'log.json')):
        entry = json.loads(line)
        if entry['event'] == 'adjust-entropy-threshold':
            entropy_threshold_by_theory = entry['value']
            break
    assert entropy_threshold_by_theory is not None
    bisect.insort(entropy_thresholds, entropy_threshold_by_theory)

    vec_srs_avg = []
    vec_srs_p99 = []
    for entropy_threshold in entropy_thresholds:
        if entropy_threshold == entropy_threshold_by_theory:
            entropy_threshold = '-autotune_entropy_threshold'
        else:
            entropy_threshold = f'-entropy-threshold-{entropy_threshold}'
        workload = f'readwhilewriting-key-16{value}-unique-size-10GB-warmup-secs-{warmup_secs}-run-secs-{run_secs}{entropy_threshold}-write-{write_MB_s}MB-s-no-stall-memtable-8MiB{compaction}{read_workload}'
        data_dir = os.path.join(dir, workload, version_path)

        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        vec_srs_avg.append(report['num-sorted-runs'].mean())
        vec_srs_p99.append(np.percentile(report['num-sorted-runs'], 99))
    print(f'{write_MB_s}MB/s', file=txt_file)
    print(pd.DataFrame({
        'entropy-threshold': entropy_thresholds,
        'srs-avg': vec_srs_avg,
        'srs-p99': vec_srs_p99,
    }).to_string(index=False), file=txt_file)
    header = f'{write_MB_s}MB/s\nentropy-threshold\tsrs-avg\t\t\tsrs-p99'
    ax_srs_avg.plot(entropy_thresholds, vec_srs_avg, linewidth=1, color=line_config['color'])
    ax_srs_p99.plot(entropy_thresholds, vec_srs_p99, linewidth=1, color=line_config['color'])
    for x in [0, 1, 2, 3, 4, 5, 6]:
        if x not in entropy_thresholds:
            continue
        i = entropy_thresholds.index(x)
        ax_srs_avg.scatter(x, vec_srs_avg[i], color=line_config['color'], marker=line_config['marker'], s=line_config['markersize'],linewidth=0, zorder=2)
        ax_srs_p99.scatter(x, vec_srs_p99[i], color=line_config['color'], marker=line_config['marker'], s=line_config['markersize'], linewidth=0, zorder=2)
    by_theory_index = entropy_thresholds.index(entropy_threshold_by_theory)
    color = common.colors[2]['dark']
    ax_srs_avg.scatter(entropy_threshold_by_theory, vec_srs_avg[by_theory_index], color=color, marker='s', s=15, linewidth=0, zorder=2)
    ax_srs_p99.scatter(entropy_threshold_by_theory, vec_srs_p99[by_theory_index], color=color, marker='s', s=15, linewidth=0, zorder=2)
ax_srs_avg.set_ylim(bottom=0, top=100)
ax_srs_p99.set_ylim(bottom=0, top=150)

handles = []
for line_config in lines_config:
    handles.append(mpl.lines.Line2D([0], [0], linewidth=1, color=line_config['color'], marker=line_config['marker'], markersize=3))
fig.legend(
    handles,
    version_names,
    ncol=3,
    loc='upper center',
    bbox_to_anchor=(0.5, 1.07),
    frameon=False,
    labelspacing=0.2,
)
pdf_path = os.path.join(dir, f'{version_path}{value}{compaction}-warmup-{warmup_secs}-run-{run_secs}{read_workload}.pdf')
fig.savefig(pdf_path, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
