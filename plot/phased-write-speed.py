#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
    print('Usage: ' + sys.argv[0] + ' dir')
    exit()
dir = sys.argv[1]

phase_secs = 3600

vec_write_MB_s = [10, 30, 50, 30, 10]

import math
import os
import json
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
    'text.usetex': True,
    'text.latex.preamble': r'''
        \usepackage{amsmath}
        \usepackage{libertine}
        \usepackage[libertine]{newtxmath}
    ''',
})

write_MB_s_string = ''
for write_MB_s in vec_write_MB_s:
    write_MB_s_string += '-' + str(write_MB_s)
versions = [
    {
        'path': os.path.join(f'readwhilewriting-key-16-value-603-unique-size-10GB-phase-secs-{phase_secs}-write-MB-s{write_MB_s_string}-autotune_entropy_threshold-no-stall-memtable-8MiB-compaction-200MB-s-get-0.87-seek-0.13-nexts-48', 'no_preemption_conditions'),
        'name': 'By-theory',
        'color': common.colors[0]['dark'],
        'linestyle': 'dashed',
    },
    {
        'path': os.path.join(f'readwhilewriting-key-16-value-603-unique-size-10GB-phase-secs-{phase_secs}-write-MB-s{write_MB_s_string}-entropy-threshold-0-max-running-bg-jobs-1-no-stall-memtable-8MiB-compaction-200MB-s-get-0.87-seek-0.13-nexts-48', 'entropy-based'),
        'name': common.versions['entropy-based']['name'],
        'color': common.versions['entropy-based']['color'],
        'linestyle': 'solid',
    },
]
version_names = [version['name'] for version in versions]

def add_write_MB_s():
    for i, write_MB_s in enumerate(vec_write_MB_s):
        plt.text((i + 0.5) / len(vec_write_MB_s), 1, f'{write_MB_s}MB/s', transform=ax.transAxes, ha="center", va="bottom")


fig = plt.figure(dpi = 300, figsize = (common.acmsmall_inch, 1.7), constrained_layout=True)
fig.get_layout_engine().set(
    rect=(0, 0, 1, 0.9),
)
ax = plt.gca()
plt.xlabel('Time (hours)')
plt.xticks(ticks=[i * 3600 for i in range(0, 6)], labels=[i for i in range(0, 6)])
plt.ylabel(r'$R_\text{eff}$ of new compactions')
add_write_MB_s()

time_adjust_entropy_threshold = []
entropy_thresholds = []

ts_begin_ns = None
for line in open(os.path.join(dir, versions[0]['path'], 'log.json')):
    entry = json.loads(line)
    if entry['event'] == 'new-benchmark':
        if ts_begin_ns is None:
            if entry['name'] in ['readwhilewriting', 'customperiodic']:
                ts_begin_ns = entry['timestamp(ns)']
        continue
    if ts_begin_ns is None:
        continue
    if entry['event'] == 'adjust-entropy-threshold':
        time_adjust_entropy_threshold.append((entry['timestamp(ns)'] - ts_begin_ns) / 1e9)
        entropy_thresholds.append(entry['value'])
time_adjust_entropy_threshold.append(phase_secs * len(vec_write_MB_s))
for i, entropy_threshold in enumerate(entropy_thresholds):
    plt.hlines(entropy_threshold, xmin=time_adjust_entropy_threshold[i], xmax=time_adjust_entropy_threshold[i+1], colors='blue', linewidth=1)

time_new_compaction = []
reff_new_compaction = []

ts_begin_ns = None
for line in open(os.path.join(dir, versions[1]['path'], 'log.json')):
    entry = json.loads(line)
    if entry['event'] == 'new-benchmark':
        if ts_begin_ns is None:
            if entry['name'] in ['readwhilewriting', 'customperiodic']:
                ts_begin_ns = entry['timestamp(ns)']
        continue
    if ts_begin_ns is None:
        continue
    if entry['event'] == 'new-compaction':
        time_new_compaction.append((entry['timestamp(ns)'] - ts_begin_ns) / 1e9)
        reff_new_compaction.append(entry['R_eff'])
scatter = plt.scatter(time_new_compaction, reff_new_compaction, linewidth=0, s=2, color=versions[1]['color'], rasterized=True)
plt.xlim((0, len(vec_write_MB_s) * phase_secs))
ylim = math.ceil(max(reff_new_compaction))
plt.ylim((0, ylim))
plt.vlines([phase_secs * i for i in range(1, len(vec_write_MB_s))], ymin=0, ymax=ylim, linewidth=1, colors='gray', linestyles='dashed')

legend = fig.legend(
    handles=[
        mpl.lines.Line2D([0], [0], color='blue', linewidth=1),
        plt.scatter([], [], 3, color=versions[1]['color'])
    ],
    labels=[
        'Theoretical threshold',
        common.versions['entropy-based']['name'],
    ],
    ncol=len(versions),
    loc='upper center',
    bbox_to_anchor=(0.5, 1.03),
    frameon=False,
    borderaxespad=0,
)
scatter_label = legend.get_texts()[1]
scatter_label.set_position((scatter_label.get_position()[0] - 7, scatter_label.get_position()[1]))

pdf_path = os.path.join(dir, f'phased-write-speed-phase_secs-{phase_secs}-write_MB_s{write_MB_s_string}-reff.pdf')
common.check_visible_labels(fig)
fig.savefig(pdf_path, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)


fig = plt.figure(dpi = 300, figsize = (common.acmsmall_inch, 1.5), constrained_layout=True)
fig.get_layout_engine().set(
    rect=(0, 0, 1, 0.9),
)
ax = plt.gca()
plt.xlabel('Time (hours)')
plt.xticks(ticks=[i * 3600 for i in range(0, 6)], labels=[i for i in range(0, 6)])
plt.ylabel('\\# of sorted runs')
ax.tick_params(axis='y', which='minor', labelleft=False)
ax.grid(axis='y')
add_write_MB_s()
for version in versions:
    report = pd.read_csv(os.path.join(dir, version['path'], 'report.csv'))
    report = report[['secs_elapsed', 'num-sorted-runs']]
    report = report.groupby(report.index // 200).mean()
    plt.plot(report['secs_elapsed'], report['num-sorted-runs'], linewidth=1, color=version['color'], linestyle=version['linestyle'])
plt.xlim((0, len(vec_write_MB_s) * phase_secs))
plt.ylim(bottom=0)
plt.vlines([phase_secs * i for i in range(1, len(vec_write_MB_s))], ymin=0, ymax=100, linewidth=1, colors='gray', linestyles='dashed')
fig.legend(
    version_names,
    ncol=len(versions),
    loc='upper center',
    bbox_to_anchor=(0.5, 1.03),
    frameon=False,
    borderaxespad=0,
)

pdf_path = os.path.join(dir, f'phased-write-speed-phase_secs-{phase_secs}-write_MB_s{write_MB_s_string}-num-srs.pdf')
common.check_visible_labels(fig)
fig.savefig(pdf_path, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
