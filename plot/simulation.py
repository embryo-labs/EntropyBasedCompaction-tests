#!/usr/bin/env python3
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-S', type=int, default=1200)
parser.add_argument('-N', type=int, default=100000)
parser.add_argument('--verbose', action='store_true')
args = parser.parse_args()
S = args.S
N = args.N

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'simulations'))
import Bc_inf

import math
from dataclasses import dataclass
from typing import Optional
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.lines import Line2D

import common

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

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'serif',
    'font.serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 10,
})

linewidth = 1
markersize = 3

ytick_pad = 1
ylabel_pad = 1
borderpad = 0.2
borderaxespad = 0.1

fig = plt.figure(dpi = 300, figsize = (common.acmsmall_inch, 1.3), constrained_layout=True)
fig.get_layout_engine().set(
    h_pad=0.01,
    w_pad=0.01,
    wspace=0.07,
)
gs = gridspec.GridSpec(1, 3, figure=fig)

subfig = plt.subplot(gs[0, 0])
ax = plt.gca()
ax.set_xlabel('Entropy threshold', labelpad=1)
ax.tick_params(axis='y', pad=ytick_pad)
ax.set_ylabel('Write amplification', loc='top', labelpad=ylabel_pad)
ax.plot(result_entropy_based.vec_entropy_threshold, result_entropy_based.vec_wa_theory, linewidth=linewidth, marker='s', markersize=markersize, label='Bound')
ax.plot(result_entropy_based.vec_entropy_threshold, result_entropy_based.vec_wa, linewidth=linewidth, marker='o', markersize=markersize, label='Simulated')
ax.set_xticks([0, 1, 2, 3, 4, 5])
ax.set_ylim(bottom=0)
ax.set_axisbelow(True)
ax.grid()
lines, labels = ax.get_legend_handles_labels()
ax.legend(lines, labels, handlelength=1, handletextpad=0.5, columnspacing=1.5, labelspacing=0.2, borderpad=borderpad, borderaxespad=borderaxespad)

subfig = plt.subplot(gs[0, 1])
ax = plt.gca()
ax.set_xlabel('Entropy threshold', labelpad=1)
ax.tick_params(axis='y', pad=ytick_pad)
ax.set_ylabel('# of sorted runs', labelpad=ylabel_pad)
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
    ], ['Bound', 'Max', 'Avg'], handlelength=1, handletextpad=0.5, columnspacing=1.5, labelspacing=0.2, borderpad=borderpad, borderaxespad=borderaxespad)

subfig = plt.subplot(gs[0, 2])
ax = plt.gca()
ax.set_xlabel('Entropy threshold', labelpad=1)
ax.tick_params(axis='y', pad=ytick_pad)
ax.set_ylabel('Space amplification', loc='top', labelpad=ylabel_pad)
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
    ], ['Bound', 'Simulated'], loc='upper left', handlelength=1, handletextpad=0.5, columnspacing=1.5, labelspacing=0.2, borderpad=borderpad, borderaxespad=borderaxespad)

pdf_path = f'simulation-S-{S}-N-{N}.pdf'
common.check_visible_labels(fig)
plt.savefig(pdf_path, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show()
