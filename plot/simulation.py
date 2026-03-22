#!/usr/bin/env python3
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-S', type=int, default=1200)
parser.add_argument('-N', type=int, default=100000)
parser.add_argument('--verbose', action='store_true')
args = parser.parse_args()
if args.S == 0:
    S = None
else:
    S = args.S
N = args.N

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'simulations'))
import Bc_inf

import math
from dataclasses import dataclass
from typing import Optional
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.lines import Line2D

import common

def get_pdf_path(prefix):
    if S is not None:
        S_str = '-S-' + str(S)
    else:
        S_str = ''
    return f'{prefix}{S_str}-N-{N}.pdf'

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 9,
})

entropy_thresholds = [0.5, 0.6, 0.8, 1, 1.2, 1.5, 2, 3, 4, 5]
@dataclass
class ResultEntropyBased:
    vec_entropy_threshold: list
    vec_wa_theory: list
    vec_wa: list
    vec_avg_num_srs: list
    vec_max_num_srs: list
    vec_num_srs_theory: list
    vec_space_amp_estimation: list
    vec_space_amp: Optional[list]
    def __init__(self):
        self.vec_entropy_threshold = []
        self.vec_wa_theory = []
        self.vec_wa = []
        self.vec_avg_num_srs = []
        self.vec_max_num_srs = []
        self.vec_num_srs_theory = []
        self.vec_space_amp_estimation = []
result_entropy_based = ResultEntropyBased()
if S is not None:
    result_entropy_based.vec_space_amp = []
if args.verbose:
    print('Threshold\twrite-amp\tavg-num-srs\tmax-num-srs')
for entropy_threshold in entropy_thresholds:
    (wa, avg_num_srs, max_num_srs, max_size) = Bc_inf.benefit_cost(N, entropy_threshold, S, None, None)
    if args.verbose:
        print('%f\t%f\t%f\t%f' %(entropy_threshold, wa, avg_num_srs, max_num_srs))
    result_entropy_based.vec_entropy_threshold.append(entropy_threshold)

    if S is None:
        wa_theory = math.log2(N) / entropy_threshold
    else:
        wa_theory = common.bound_wa(S, entropy_threshold)
    result_entropy_based.vec_wa_theory.append(wa_theory)
    result_entropy_based.vec_wa.append(wa)
    result_entropy_based.vec_avg_num_srs.append(avg_num_srs)
    result_entropy_based.vec_max_num_srs.append(max_num_srs)

    result_entropy_based.vec_num_srs_theory.append(common.bound_ra(max_size, entropy_threshold))
    result_entropy_based.vec_space_amp_estimation.append(common.bound_sa(entropy_threshold))

    if S is not None:
        result_entropy_based.vec_space_amp.append(max_size / S)

linewidth = 1
markersize = 3

if S is None:
    fig = plt.figure(dpi = 300, figsize = (common.double_col_inch / 3 * 2, 1.6), constrained_layout=True)
    gs = gridspec.GridSpec(1, 2, figure=fig)
else:
    fig = plt.figure(dpi = 300, figsize = (common.double_col_inch, 1.6), constrained_layout=True)
    gs = gridspec.GridSpec(1, 3, figure=fig)

subfig = plt.subplot(gs[0, 0])
ax = plt.gca()
ax.set_xlabel('Entropy threshold')
ax.set_ylabel('Write amplification')
ax.plot(result_entropy_based.vec_entropy_threshold, result_entropy_based.vec_wa_theory, linewidth=linewidth, marker='s', markersize=markersize, label='Theoretical bound')
ax.plot(result_entropy_based.vec_entropy_threshold, result_entropy_based.vec_wa, linewidth=linewidth, marker='o', markersize=markersize, label='Simulated')
ax.set_xticks([0, 1, 2, 3, 4, 5])
ax.set_ylim(bottom=0)
ax.set_axisbelow(True)
ax.grid()
lines, labels = ax.get_legend_handles_labels()
ax.legend(lines, labels, handlelength=1, handletextpad=0.5, columnspacing=1.5)

subfig = plt.subplot(gs[0, 1])
ax = plt.gca()
ax.set_xlabel('Entropy threshold')
ax.set_ylabel('# of sorted runs')
ax.plot(result_entropy_based.vec_entropy_threshold, result_entropy_based.vec_num_srs_theory, color=common.colors[0]['dark'], linewidth=linewidth)
ax.plot(result_entropy_based.vec_entropy_threshold, result_entropy_based.vec_max_num_srs, color=common.colors[1]['dark'], linewidth=linewidth)
ax.plot(result_entropy_based.vec_entropy_threshold, result_entropy_based.vec_avg_num_srs, color=common.colors[2]['dark'], linewidth=linewidth)
for entropy_threshold in [0.5, 1, 2, 3, 4, 5]:
    i = entropy_thresholds.index(entropy_threshold)
    ax.scatter(entropy_threshold, result_entropy_based.vec_num_srs_theory[i], marker='s', color=common.colors[0]['dark'], s=15, linewidth=0, zorder=2)
    ax.scatter(entropy_threshold, result_entropy_based.vec_max_num_srs[i], marker='o', color=common.colors[1]['dark'], s=15, linewidth=0, zorder=2)
    ax.scatter(entropy_threshold, result_entropy_based.vec_avg_num_srs[i], marker='D', color=common.colors[2]['dark'], s=15, linewidth=0, zorder=2)
ax.set_xticks([0, 1, 2, 3, 4, 5])
ax.set_ylim(bottom=0)
ax.set_axisbelow(True)
ax.grid()
ax.legend([
        mpl.lines.Line2D([0], [0], color=common.colors[0]['dark'], linewidth=linewidth, marker='s', markersize=markersize),
        mpl.lines.Line2D([0], [0], color=common.colors[1]['dark'], linewidth=linewidth, marker='o', markersize=markersize),
        mpl.lines.Line2D([0], [0], color=common.colors[2]['dark'], linewidth=linewidth, marker='D', markersize=markersize),
    ], ['Theoretical bound', 'Simulated max', 'Simulated avg'], handlelength=1, handletextpad=0.5, columnspacing=1.5, labelspacing=0.4)

if S is not None:
    subfig = plt.subplot(gs[0, 2])
    ax = plt.gca()
    ax.set_xlabel('Entropy threshold')
    ax.set_ylabel('Space amplification')
    ax.plot(result_entropy_based.vec_entropy_threshold, result_entropy_based.vec_space_amp_estimation, linewidth=linewidth)
    ax.plot(result_entropy_based.vec_entropy_threshold, result_entropy_based.vec_space_amp, linewidth=linewidth)
    for entropy_threshold in [0.5, 1, 2, 3, 4, 5]:
        i = entropy_thresholds.index(entropy_threshold)
        ax.scatter(entropy_threshold, result_entropy_based.vec_space_amp_estimation[i], marker='s', color=common.colors[0]['dark'], s=15, linewidth=0, zorder=2)
        ax.scatter(entropy_threshold, result_entropy_based.vec_space_amp[i], marker='o', color=common.colors[1]['dark'], s=15, linewidth=0, zorder=2)
    ymax = math.ceil(max(result_entropy_based.vec_space_amp_estimation))
    ax.set_xticks([0, 1, 2, 3, 4, 5])
    ax.set_ylim((0, ymax))
    ax.grid()
    ax.legend([
            mpl.lines.Line2D([0], [0], color=common.colors[0]['dark'], linewidth=linewidth, marker='s', markersize=markersize),
            mpl.lines.Line2D([0], [0], color=common.colors[1]['dark'], linewidth=linewidth, marker='o', markersize=markersize),
        ], ['Theoretical bound', 'Simulated'], handlelength=1, handletextpad=0.5, columnspacing=1.5)

pdf_path = get_pdf_path('simulation')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show()


@dataclass
class Result:
    vec_wa_theory: list
    vec_wa: list
    vec_num_srs_theory: list
    vec_avg_num_srs: list
    vec_max_num_srs: list
    vec_space_amp: Optional[list]
    def __init__(self):
        self.vec_wa_theory = []
        self.vec_wa = []
        self.vec_num_srs_theory = []
        self.vec_avg_num_srs = []
        self.vec_max_num_srs = []
        if S is not None:
            self.vec_space_amp = []
result_leveling = Result()
for T in range(3, 11):
    (wa, avg_num_srs, max_num_srs, max_size) = Bc_inf.leveling(N, T, S)
    if S is None:
        L = math.log(N, T)
    else:
        L = math.log(S, T)
    result_leveling.vec_wa_theory.append(T * L / 2)
    result_leveling.vec_wa.append(wa)
    result_leveling.vec_num_srs_theory.append(L)
    result_leveling.vec_avg_num_srs.append(avg_num_srs)
    result_leveling.vec_max_num_srs.append(max_num_srs)
    if S is not None:
        result_leveling.vec_space_amp.append(max_size / S)

result_tiering = Result()
for T in [2, 3, 4, 6, 10, 20]:
    (wa, avg_num_srs, max_num_srs, max_size) = Bc_inf.tiering(N, T, S)
    L = math.log(N, T)
    result_tiering.vec_wa_theory.append(L)
    result_tiering.vec_wa.append(wa)
    result_tiering.vec_num_srs_theory.append((T-1) * L)
    result_tiering.vec_avg_num_srs.append(avg_num_srs)
    result_tiering.vec_max_num_srs.append(max_num_srs)
    if S is not None:
        result_tiering.vec_space_amp.append(max_size / S)

result_universal = Result()
for compaction_trigger in [90, 80, 70, 60, 50, 40, 30, 20, 10, 4, 3]:
    (wa, avg_num_srs, max_num_srs, max_size) = Bc_inf.universal(N, compaction_trigger, 1, S)
    result_universal.vec_wa.append(wa)
    result_universal.vec_avg_num_srs.append(avg_num_srs)
    result_universal.vec_max_num_srs.append(max_num_srs)
    if S is not None:
        result_universal.vec_space_amp.append(max_size / S)
for size_ratio_trigger in np.arange(1, 10, 1):
    (wa, avg_num_srs, max_num_srs, max_size) = Bc_inf.universal(N, 2, size_ratio_trigger, S)
    result_universal.vec_wa.append(wa)
    result_universal.vec_avg_num_srs.append(avg_num_srs)
    result_universal.vec_max_num_srs.append(max_num_srs)
    if S is not None:
        result_universal.vec_space_amp.append(max_size / S)

versions = [
    {
        'result': result_leveling,
        'color': common.colors[0]['dark'],
        'marker': 's',
    },
    {
        'result': result_tiering,
        'color': common.colors[1]['dark'],
        'marker': 'o',
    },
    {
        'result': result_universal,
        'color': common.colors[3]['dark'],
        'marker': '^',
    },
    {
        'result': result_entropy_based,
        'color': common.versions['entropy-based']['color'],
        'marker': 'D',
    },
]
fig = plt.figure(dpi = 300, figsize = (common.double_col_inch, 1.6), constrained_layout=True)
gs = gridspec.GridSpec(1, 3, figure=fig)

subfig = plt.subplot(gs[0, 0])
ax = plt.gca()
plt.xlabel('Write amplification')
plt.ylabel('Avg # of sorted runs')
ax.set_axisbelow(True)
ax.grid(axis='y')
for version in versions:
    result_entropy_based = version['result']
    ax.plot(result_entropy_based.vec_wa, result_entropy_based.vec_avg_num_srs, color=version['color'], linewidth=linewidth, marker=version['marker'], markersize=markersize)
ax.set_ylim(bottom=0)

subfig = plt.subplot(gs[0, 1])
ax = plt.gca()
plt.xlabel('Write amplification')
plt.ylabel('Max # of sorted runs')
ax.set_axisbelow(True)
ax.grid(axis='y')
for version in versions:
    result_entropy_based = version['result']
    ax.plot(result_entropy_based.vec_wa, result_entropy_based.vec_max_num_srs, color=version['color'], linewidth=linewidth, marker=version['marker'], markersize=markersize)
ax.set_ylim(bottom=0)

subfig = plt.subplot(gs[0, 2])
ax = plt.gca()
plt.xlabel('Bound on write amplification')
plt.ylabel('Bound on # of sorted runs')
ax.set_axisbelow(True)
ax.grid(axis='y')
for version_idx, version in enumerate(versions):
    if version_idx == 2:
        continue
    result_entropy_based = version['result']
    ax.plot(result_entropy_based.vec_wa_theory, result_entropy_based.vec_num_srs_theory, color=version['color'], linewidth=linewidth, marker=version['marker'], markersize=markersize)
ax.set_ylim(bottom=0)

handles = []
for version in versions:
    handles.append(Line2D([0], [0], color=version['color'], linewidth=linewidth, marker=version['marker'], markersize=markersize))
fig.legend(handles, ['Leveling', 'Tiering', 'Universal', 'Entropy-based'], ncol=len(versions), loc='upper center', bbox_to_anchor=(0.5, 1.14), frameon=False, borderaxespad=0)
pdf_path = get_pdf_path('simulation-srs')
fig.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show()
