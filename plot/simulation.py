#!/usr/bin/env python3
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-S', type=int, default=1000)
parser.add_argument('-N', type=int, default=10000)
parser.add_argument('--entropy_threshold_begin', type=float, default=0.5)
parser.add_argument('--entropy_threshold_step', type=float, default=0.01)
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
    pdf_path = prefix
    if S is not None:
        pdf_path += '-S-' + str(S)
    pdf_path += '-N-' + str(N) + '-entropy_threshold_begin-' + str(args.entropy_threshold_begin) + '.pdf'
    return pdf_path

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 9,
})

@dataclass
class BenefitCostResult:
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
def benefit_cost(C, k_n):
    result = BenefitCostResult()
    if S is not None:
        result.vec_space_amp = []
    for entropy_threshold in np.arange(args.entropy_threshold_begin, 3 + args.entropy_threshold_step, args.entropy_threshold_step):
        (wa, avg_num_srs, max_num_srs, max_size) = Bc_inf.benefit_cost(N, entropy_threshold, S, C, k_n)
        if args.verbose:
            print('%f\t%f\t%f\t%f' %(entropy_threshold, wa, avg_num_srs, max_num_srs))
        result.vec_entropy_threshold.append(entropy_threshold)
        if S is None:
            wa_theory = math.log2(N) / entropy_threshold
        else:
            wa_theory = common.bound_wa(S, entropy_threshold)
        result.vec_wa_theory.append(wa_theory)
        result.vec_wa.append(wa)
        result.vec_avg_num_srs.append(avg_num_srs)
        result.vec_max_num_srs.append(max_num_srs)

        result.vec_num_srs_theory.append(common.bound_ra(max_size, entropy_threshold))
        result.vec_space_amp_estimation.append(common.bound_sa(entropy_threshold))

        if S is not None:
            result.vec_space_amp.append(max_size / S)
    return result
result_benefit_cost = benefit_cost(None, None)

linewidth = 1
markersize = 3

num_marks = 5
markevery = len(result_benefit_cost.vec_wa) // num_marks

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
ax.plot(result_benefit_cost.vec_entropy_threshold, result_benefit_cost.vec_wa_theory, linewidth=linewidth, marker='s', markevery=markevery, markersize=markersize, label='Theoretical bound')
ax.plot(result_benefit_cost.vec_entropy_threshold, result_benefit_cost.vec_wa, linewidth=linewidth, marker='o', markevery=markevery, markersize=markersize, label='Simulated')
ax.set_ylim(bottom=0)
ax.set_axisbelow(True)
ax.grid(axis='y')
lines, labels = ax.get_legend_handles_labels()
ax.legend(lines, labels, handlelength=1, handletextpad=0.5, columnspacing=1.5)

subfig = plt.subplot(gs[0, 1])
ax = plt.gca()
ax.set_xlabel('Entropy threshold')
ax.set_ylabel('# of sorted runs')
ax.plot(result_benefit_cost.vec_entropy_threshold, result_benefit_cost.vec_num_srs_theory, linewidth=linewidth, marker='s', markevery=markevery, markersize=markersize, label='Theoretical bound')
ax.plot(result_benefit_cost.vec_entropy_threshold, result_benefit_cost.vec_max_num_srs, linewidth=linewidth, marker='o', markevery=markevery, markersize=markersize, label='Simulated max')
ax.plot(result_benefit_cost.vec_entropy_threshold, result_benefit_cost.vec_avg_num_srs, linewidth=linewidth, marker='D', markevery=markevery, markersize=markersize, label='Simulated avg')
ax.set_ylim(bottom=0)
ax.set_axisbelow(True)
ax.grid(axis='y')
lines, labels = ax.get_legend_handles_labels()
ax.legend(lines, labels, handlelength=1, handletextpad=0.5, columnspacing=1.5, frameon=False, borderaxespad=0, labelspacing=0.4)

if S is not None:
    subfig = plt.subplot(gs[0, 2])
    ax = plt.gca()
    ax.set_xlabel('Entropy threshold')
    ax.set_ylabel('Space amplification')
    ax.plot(result_benefit_cost.vec_entropy_threshold, result_benefit_cost.vec_space_amp_estimation, linewidth=linewidth, marker='s', markevery=markevery, markersize=markersize, label='Theoretical bound')
    ax.plot(result_benefit_cost.vec_entropy_threshold, result_benefit_cost.vec_space_amp, linewidth=linewidth, marker='o', markevery=markevery, markersize=markersize, label='Simulated')
    ymax = math.ceil(max(result_benefit_cost.vec_space_amp_estimation))
    ax.set_ylim((1, ymax))
    plt.yticks(list(range(1, ymax + 1)))
    ax.grid()
    lines, labels = ax.get_legend_handles_labels()
    ax.legend(lines, labels, handlelength=1, handletextpad=0.5, columnspacing=1.5)

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
    def __init__(self):
        self.vec_wa_theory = []
        self.vec_wa = []
        self.vec_num_srs_theory = []
        self.vec_avg_num_srs = []
        self.vec_max_num_srs = []
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

result_tiering = Result()
for T in range(2, 11):
    (wa, avg_num_srs, max_num_srs, max_size) = Bc_inf.tiering(N, T, S)
    L = math.log(N, T)
    result_tiering.vec_wa_theory.append(L)
    result_tiering.vec_wa.append(wa)
    result_tiering.vec_num_srs_theory.append((T-1) * L)
    result_tiering.vec_avg_num_srs.append(avg_num_srs)
    result_tiering.vec_max_num_srs.append(max_num_srs)

result_universal = Result()
for compaction_trigger in range(2, 20):
    (wa, avg_num_srs, max_num_srs, max_size) = Bc_inf.universal(N, compaction_trigger, S)
    result_universal.vec_wa.append(wa)
    result_universal.vec_avg_num_srs.append(avg_num_srs)
    result_universal.vec_max_num_srs.append(max_num_srs)

versions = [
    {
        'result': result_leveling,
        'color': common.colors[0]['dark'],
        'marker': 's',
        'markevery': None,
    },
    {
        'result': result_tiering,
        'color': common.colors[1]['dark'],
        'marker': 'o',
        'markevery': None,
    },
    {
        'result': result_universal,
        'color': common.colors[3]['dark'],
        'marker': '^',
        'markevery': None,
    },
    {
        'result': result_benefit_cost,
        'color': common.versions['benefit-cost']['color'],
        'marker': 'D',
        'markevery': markevery,
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
    result = version['result']
    ax.plot(result.vec_wa, result.vec_avg_num_srs, color=version['color'], linewidth=linewidth, marker=version['marker'], markersize=markersize, markevery=version['markevery'])
ax.set_ylim(bottom=0)

subfig = plt.subplot(gs[0, 1])
ax = plt.gca()
plt.xlabel('Write amplification')
plt.ylabel('Max # of sorted runs')
ax.set_axisbelow(True)
ax.grid(axis='y')
for version in versions:
    result = version['result']
    ax.plot(result.vec_wa, result.vec_max_num_srs, color=version['color'], linewidth=linewidth, marker=version['marker'], markersize=markersize, markevery=version['markevery'])
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
    result = version['result']
    ax.plot(result.vec_wa_theory, result.vec_num_srs_theory, color=version['color'], linewidth=linewidth, marker=version['marker'], markersize=markersize, markevery=version['markevery'])
ax.set_ylim(bottom=0)

handles = []
for version in versions:
    handles.append(Line2D([0], [0], color=version['color'], linewidth=linewidth, marker=version['marker'], markersize=markersize))
fig.legend(handles, ['Leveling', 'Tiering', 'Universal', 'Entropy-based'], ncol=len(versions), loc='upper center', bbox_to_anchor=(0.5, 1.14), frameon=False, borderaxespad=0,)
pdf_path = get_pdf_path('simulation-srs')
fig.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show()
