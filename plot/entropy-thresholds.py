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

import math
import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

import common

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'serif',
    'font.serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 9,
})

vec_write_MB_s = [10, 20, 30, 40, 50, 60]

fig_num_srs = plt.figure(dpi=300, figsize=(common.single_col_inch, 1.4), constrained_layout=True)
fig_num_srs.get_layout_engine().set(
    h_pad=0.01,
    w_pad=0.01,
    wspace=0.1,
    rect=(0, 0, 1, 0.82),
)
gs = GridSpec(1, 2, figure=fig_num_srs)
ax_srs_avg = plt.subplot(gs[0, 0])
plt.xlabel('User write speed (MB/s)', loc='right', labelpad=0)
plt.xticks(vec_write_MB_s)
plt.ylabel('Avg # of sorted runs', loc='top')
plt.yscale('log')
plt.ylim((4, 100))
yticks = [4, 10, 100]
plt.yticks(yticks, labels=yticks)
ax_srs_avg.set_axisbelow(True)
ax_srs_avg.grid(axis='y')

ax_srs_p99 = plt.subplot(gs[0, 1])
plt.xlabel('User write speed (MB/s)', loc='right', labelpad=0)
plt.xticks(vec_write_MB_s)
plt.ylabel('P99 # of sorted runs', loc='top')
plt.yscale('log')
plt.ylim((4, 120))
yticks = [4, 10, 100]
plt.yticks(yticks, labels=yticks)
ax_srs_p99.set_axisbelow(True)
ax_srs_p99.grid(axis='y')

versions = [
    {
        't_e': 0,
        'marker': 'o',
        'markersize': 7,
        'markerfacecolor': 'none',
    },
    {
        't_e': 0.5,
        'marker': 's',
        'markersize': 4,
        'markerfacecolor': 'none',
    },
    {
        't_e': 0.78,
        'marker': '^',
        'markersize': 3,
        'markerfacecolor': None,
    },
    {
        't_e': 1,
        'marker': '>',
        'markersize': 3,
        'markerfacecolor': None,
    },
    {
        't_e': 2,
        'marker': '<',
        'markersize': 3,
        'markerfacecolor': None,
    },
    {
        't_e': 3,
        'marker': 'v',
        'markersize': 3,
        'markerfacecolor': None,
    },
]

lines = [
    {
        'name': 'Theoretical',
        'color': common.colors[0]['dark'],
        'linestyle': '-',
        'marker': 's',
        'markersize': 3,
    },
    {
        'name': 'Max allowed',
        'color': common.colors[1]['dark'],
        'linestyle': '--',
        'marker': None,
        'markersize': None,
    },
    {
        'name': 'Real',
        'color': common.versions['entropy-based']['color'],
        'linestyle': '-',
        'marker': 'o',
        'markersize': 3,
    },
]
fig_wa = plt.figure(dpi=300, figsize=(common.single_col_inch, 1.2), constrained_layout=True)
fig_wa.get_layout_engine().set(
    h_pad=0.01,
    w_pad=0.01,
    wspace=0.1,
    rect=(0, 0, 1, 0.87),
)
gs = GridSpec(1, 2, figure=fig_wa)
ax_10 = plt.subplot(gs[0, 0])
plt.ylabel('Write amplification', y=0.36)
plt.xlabel('Entropy threshold\n(a) User write 10MB/s', labelpad=0)
plt.xticks([0, 1, 2, 3])
ax_10.tick_params(axis='x', pad=0)

plt.subplot(gs[0, 1])
ax_50 = plt.gca()
plt.xlabel('Entropy threshold\n(b) User write 50MB/s', labelpad=0)
plt.xticks([0, 1, 2, 3])
ax_50.tick_params(axis='x', pad=0)

vec_entropy_threshold = [version['t_e'] for version in versions]
vec_wa_theory = []
for entropy_threshold in vec_entropy_threshold:
    if entropy_threshold == 0:
        vec_wa_theory.append(math.inf)
    else:
        vec_wa_theory.append(math.log2(math.e * 1200) / entropy_threshold)
ax_10.plot(vec_entropy_threshold, vec_wa_theory, linewidth=1, color=lines[0]['color'], marker=lines[0]['marker'], markersize=lines[0]['markersize'])
ax_50.plot(vec_entropy_threshold, vec_wa_theory, linewidth=1, color=lines[0]['color'], marker=lines[0]['marker'], markersize=lines[0]['markersize'])

def max_wa(write_MB_s):
    return [(compaction_MB_s - write_MB_s) / write_MB_s for entropy_threshold in vec_entropy_threshold]
ax_10.hlines(max_wa(10), min(vec_entropy_threshold), max(vec_entropy_threshold), linewidth=1, color=lines[1]['color'], linestyles=lines[1]['linestyle'])
ax_50.hlines(max_wa(50), min(vec_entropy_threshold), max(vec_entropy_threshold), linewidth=1, color=lines[1]['color'], linestyles=lines[1]['linestyle'])

vec_wa_10 = []
vec_wa_50 = []

linewidth=0.7

for version in versions:
    srs_avg = []
    srs_p99 = []
    for write_MB_s in vec_write_MB_s:
        entropy_threshold = version['t_e']
        if entropy_threshold != 0.78:
            entropy_threshold_str = f'-entropy-threshold-{entropy_threshold}'
        else:
            entropy_threshold_str = ''
        workload = f'readwhilewriting-key-16{value}-unique-size-10GB-warmup-secs-{warmup_secs}-run-secs-{run_secs}{entropy_threshold_str}-max-running-bg-jobs-1-write-{write_MB_s}MB-s-no-stall-memtable-8MiB{compaction}{read_workload}'
        data_dir = os.path.join(dir, workload, 'entropy-based')

        report = pd.read_csv(os.path.join(data_dir, 'report.csv')).iloc[1:]
        srs_avg.append(report['num-sorted-runs'].mean())
        srs_p99.append(np.percentile(report['num-sorted-runs'], 99))

        if write_MB_s in [10, 50]:
            compact_write_bytes = report['rocksdb.compact.write.bytes']
            secs = len(compact_write_bytes)
            wa = compact_write_bytes.sum() / (write_MB_s * 1e6 * secs)
            if write_MB_s == 10:
                assert entropy_threshold == vec_entropy_threshold[len(vec_wa_10)]
                vec_wa_10.append(wa)
            else:
                assert write_MB_s == 50
                assert entropy_threshold == vec_entropy_threshold[len(vec_wa_50)]
                vec_wa_50.append(wa)
    ax_srs_avg.plot(vec_write_MB_s, srs_avg, linewidth=linewidth, marker=version['marker'], markersize=version['markersize'], markerfacecolor=version['markerfacecolor'], markeredgewidth=linewidth)
    ax_srs_p99.plot(vec_write_MB_s, srs_p99, linewidth=linewidth, marker=version['marker'], markersize=version['markersize'], markerfacecolor=version['markerfacecolor'], markeredgewidth=linewidth)

ax_10.plot(vec_entropy_threshold, vec_wa_10, linewidth=1, color=lines[2]['color'], marker=lines[2]['marker'], markersize=lines[2]['markersize'])
ax_50.plot(vec_entropy_threshold, vec_wa_50, linewidth=1, color=lines[2]['color'], marker=lines[2]['marker'], markersize=lines[2]['markersize'])

ax_10.set_ylim((0, 23))
ax_50.set_ylim((0, 23))

names = []
for version in versions:
    t_e = version['t_e']
    if t_e == 0.78:
        names.append(f'{t_e} ({common.versions['entropy-based']['name']})')
    else:
        names.append(str(t_e))
fig_num_srs.legend(
    names,
    ncol=3,
    loc='upper center',
    bbox_to_anchor=(0.5, 1.07),
    frameon=False,
    labelspacing=0.2,
)
pdf_path = os.path.join(dir, f'entropy-thresholds{value}{compaction}-warmup-{warmup_secs}-run-{run_secs}{read_workload}.pdf')
fig_num_srs.savefig(pdf_path, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)

handles = []
names = []
for line in lines:
    handles.append(mpl.lines.Line2D([0], [0], linewidth=1, color=line['color'], linestyle=line['linestyle'], marker=line['marker'], markersize=line['markersize']))
    names.append(line['name'])
fig_wa.legend(
    handles=handles,
    labels=names,
    ncol=len(lines),
    loc='upper center',
    bbox_to_anchor=(0.5, 1.09),
    handlelength=1.5,
    frameon=False,
)
pdf_path = os.path.join(dir, f'entropy-thresholds{value}{compaction}-warmup-{warmup_secs}-run-{run_secs}-wa.pdf')
fig_wa.savefig(pdf_path, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
