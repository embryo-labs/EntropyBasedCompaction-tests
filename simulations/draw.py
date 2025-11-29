#!/usr/bin/env python3
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-S', type=int)
parser.add_argument('-N', type=int, required=True)
parser.add_argument('--entropy_threshold_begin', type=float, required=True)
parser.add_argument('--verbose', action='store_true')
args = parser.parse_args()
S = args.S
N = args.N

entropy_threshold_step = 0.05

import os
import math
from dataclasses import dataclass
from typing import Optional
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec

import Bc_inf

def get_pdf_path(prefix):
    pdf_path = prefix
    if S is not None:
        pdf_path += '-S-' + str(S)
    pdf_path += '-N-' + str(N) + '-entropy_threshold_begin-' + str(args.entropy_threshold_begin) + '.pdf'
    return pdf_path

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

@dataclass
class Result:
    vec_wa: list
    vec_avg_num_srs: list
    vec_max_num_srs: list
    vec_space_amp: Optional[list]
    def __init__(self):
        self.vec_wa = []
        self.vec_avg_num_srs = []
        self.vec_max_num_srs = []
        if S is not None:
            self.vec_space_amp = []
result_leveling = Result()
for T in range(3, 11):
    (wa, avg_num_srs, max_num_srs, max_size) = Bc_inf.leveling(N, T, S)
    if args.verbose:
        print('%d\t%f\t%f\t%f' %(T, wa, avg_num_srs, max_num_srs))
    result_leveling.vec_wa.append(wa)
    result_leveling.vec_avg_num_srs.append(avg_num_srs)
    result_leveling.vec_max_num_srs.append(max_num_srs)
    if S is not None:
        result_leveling.vec_space_amp.append(max_size / S)

result_tiering = Result()
for T in range(2, 11):
    (wa, avg_num_srs, max_num_srs, max_size) = Bc_inf.tiering(N, T, S)
    result_tiering.vec_wa.append(wa)
    result_tiering.vec_avg_num_srs.append(avg_num_srs)
    result_tiering.vec_max_num_srs.append(max_num_srs)
    if S is not None:
        result_tiering.vec_space_amp.append(max_size / S)

@dataclass
class BenefitCostResult:
    vec_entropy_threshold: list
    vec_wa_theory: list
    vec_wa: list
    vec_avg_num_srs: list
    vec_max_num_srs: list
    vec_space_amp: Optional[list]
    def __init__(self):
        self.vec_entropy_threshold = []
        self.vec_wa_theory = []
        self.vec_wa = []
        self.vec_avg_num_srs = []
        self.vec_max_num_srs = []
def benefit_cost(C, k_n):
    result = BenefitCostResult()
    if S is not None:
        result.vec_space_amp = []
    for entropy_threshold in np.arange(args.entropy_threshold_begin, 3, entropy_threshold_step):
        (wa, avg_num_srs, max_num_srs, max_size) = Bc_inf.benefit_cost(N, entropy_threshold, S, C, k_n)
        if args.verbose:
            print('%f\t%f\t%f\t%f' %(entropy_threshold, wa, avg_num_srs, max_num_srs))
        result.vec_entropy_threshold.append(entropy_threshold)
        if S is None:
            wa_theory = math.log2(N) / entropy_threshold
        else:
            wa_theory = math.log2(S / math.e) / entropy_threshold + math.e + 1
            # wa_theory = math.log2(S) / entropy_threshold
        result.vec_wa_theory.append(wa_theory)
        result.vec_wa.append(wa)
        result.vec_avg_num_srs.append(avg_num_srs)
        result.vec_max_num_srs.append(max_num_srs)
        if S is not None:
            result.vec_space_amp.append(max_size / S)
    return result
result_entropy_only = benefit_cost(None, None)
result_with_large_compaction = benefit_cost(math.e, None)
result_with_mid_compaction = benefit_cost(math.e, math.inf)
result_sliding_window = benefit_cost(math.e, 1.7)

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
ax = plt.gca()
plt.xlabel('Write amplification', fontsize=8)
plt.ylabel('Num sorted runs', fontsize=8)
plt.plot(result_leveling.vec_wa, result_leveling.vec_avg_num_srs)
plt.plot(result_leveling.vec_wa, result_leveling.vec_max_num_srs)
plt.plot(result_tiering.vec_wa, result_tiering.vec_avg_num_srs)
plt.plot(result_tiering.vec_wa, result_tiering.vec_max_num_srs)
plt.plot(result_with_mid_compaction.vec_wa, result_with_mid_compaction.vec_avg_num_srs)
plt.plot(result_with_mid_compaction.vec_wa, result_with_mid_compaction.vec_max_num_srs)
plt.ylim(bottom=0)
plt.legend(['leveling avg', 'leveling max', 'tiering avg', 'tiering max', 'with-mid-comp avg', 'with-mid-comp max'], fontsize=8)
pdf_path = get_pdf_path('simulation-wa-ra')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show(block=False)

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
ax = plt.gca()
plt.xlabel('Write amplification', fontsize=8)
plt.ylabel('Space amplification', fontsize=8)
plt.plot(result_leveling.vec_wa, result_leveling.vec_space_amp, label='leveling')
plt.plot(result_tiering.vec_wa, result_tiering.vec_space_amp, label='tiering')
plt.plot(result_entropy_only.vec_wa, result_entropy_only.vec_space_amp, label='entropy-only')
plt.plot(result_with_large_compaction.vec_wa, result_with_large_compaction.vec_space_amp, label='with-large-comp')
plt.plot(result_with_mid_compaction.vec_wa, result_with_mid_compaction.vec_space_amp, label='with-mid-comp')
plt.plot(result_sliding_window.vec_wa, result_sliding_window.vec_space_amp, label='sliding-window')
plt.ylim(bottom=1)
plt.xticks(fontsize=8)
plt.yticks(list(range(1, math.ceil(max(result_tiering.vec_space_amp)) + 1, 1)), fontsize=8)
ax.grid(axis='y')
points_x = []
points_y = []
points_text = []
for T in [3, 5, 10]:
    points_x.append(result_leveling.vec_wa[T - 3])
    points_y.append(result_leveling.vec_space_amp[T - 3])
    points_text.append('L-' + str(T))
for entropy_threshold in [args.entropy_threshold_begin, 0.65, 1, 2, 3]:
    i = round((entropy_threshold - args.entropy_threshold_begin) / entropy_threshold_step)
    points_x.append(result_sliding_window.vec_wa[i])
    points_y.append(result_sliding_window.vec_space_amp[i])
    points_text.append('E-' + str(entropy_threshold))
plt.scatter(points_x, points_y)
for i in range(0, len(points_text)):
    plt.text(points_x[i], points_y[i] + 0.4, points_text[i], fontsize=7, ha='center', va='center')
lines, labels = ax.get_legend_handles_labels()
ax.legend(lines, labels, fontsize=8)
pdf_path = get_pdf_path('simulation-wa-sa')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show()

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(10)), constrained_layout=True)
gs = gridspec.GridSpec(2, 2, figure=fig)
subfig = plt.subplot(gs[0, 0])
ax = plt.gca()
ax.set_xlabel('Entropy threshold', fontsize=8)
ax.set_ylabel('Write amplification', fontsize=8)
ax.plot(result_entropy_only.vec_entropy_threshold, result_entropy_only.vec_wa, label='entropy-only')
ax.plot(result_with_large_compaction.vec_entropy_threshold, result_with_large_compaction.vec_wa, label='with-large-comp')
ax.plot(result_with_mid_compaction.vec_entropy_threshold, result_with_mid_compaction.vec_wa, label='with-mid-comp')
ax.plot(result_sliding_window.vec_entropy_threshold, result_sliding_window.vec_wa, label='sliding-window')
ax.plot(result_entropy_only.vec_entropy_threshold, result_entropy_only.vec_wa_theory, label='theory bound')
ax.set_ylim(bottom=0)
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)
lines, labels = ax.get_legend_handles_labels()
ax.legend(lines, labels, fontsize=8)

subfig = plt.subplot(gs[0, 1])
ax = plt.gca()
ax.set_xlabel('Entropy threshold', fontsize=8)
ax.set_ylabel('Space amplification', fontsize=8)
ax.plot(result_entropy_only.vec_entropy_threshold, result_entropy_only.vec_space_amp, label='entropy-only')
ax.plot(result_with_large_compaction.vec_entropy_threshold, result_with_large_compaction.vec_space_amp, label='with-large-comp')
ax.plot(result_with_mid_compaction.vec_entropy_threshold, result_with_mid_compaction.vec_space_amp, label='with-mid-comp')
ax.plot(result_sliding_window.vec_entropy_threshold, result_sliding_window.vec_space_amp, label='sliding-window')
ax.set_ylim(bottom=1)
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)

subfig = plt.subplot(gs[1, 0])
ax = plt.gca()
ax.set_xlabel('Entropy threshold', fontsize=8)
ax.set_ylabel('Average num of sorted runs', fontsize=8)
ax.plot(result_entropy_only.vec_entropy_threshold, result_entropy_only.vec_avg_num_srs, label='entropy-only')
ax.plot(result_with_large_compaction.vec_entropy_threshold, result_with_large_compaction.vec_avg_num_srs, label='with-large-comp')
ax.plot(result_with_mid_compaction.vec_entropy_threshold, result_with_mid_compaction.vec_avg_num_srs, label='with-mid-comp')
ax.plot(result_sliding_window.vec_entropy_threshold, result_sliding_window.vec_avg_num_srs, label='sliding-window')
ax.set_ylim(bottom=0)
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)

subfig = plt.subplot(gs[1, 1])
ax = plt.gca()
ax.set_xlabel('Entropy threshold', fontsize=8)
ax.set_ylabel('Max num of sorted runs', fontsize=8)
ax.plot(result_entropy_only.vec_entropy_threshold, result_entropy_only.vec_max_num_srs, label='entropy-only')
ax.plot(result_with_large_compaction.vec_entropy_threshold, result_with_large_compaction.vec_max_num_srs, label='with-large-comp')
ax.plot(result_with_mid_compaction.vec_entropy_threshold, result_with_mid_compaction.vec_max_num_srs, label='with-mid-comp')
ax.plot(result_sliding_window.vec_entropy_threshold, result_sliding_window.vec_max_num_srs, label='sliding-window')
ax.set_ylim(bottom=0)
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)

pdf_path = get_pdf_path('simulation-benefit-cost')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show()
