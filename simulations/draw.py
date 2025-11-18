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

import os
import math
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

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

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
ax = plt.gca()
plt.xlabel('Write amplification', fontsize=8)
plt.ylabel('Num sorted runs', fontsize=8)

vec_wa = []
vec_avg_num_srs = []
vec_max_num_srs = []
for T in range(3, 11):
    (wa, avg_num_srs, max_num_srs) = Bc_inf.leveling(N, T, S)
    if args.verbose:
        print('%d\t%f\t%f\t%f' %(T, wa, avg_num_srs, max_num_srs))
    vec_wa.append(wa)
    vec_avg_num_srs.append(avg_num_srs)
    vec_max_num_srs.append(max_num_srs)
plt.plot(vec_wa, vec_avg_num_srs)
plt.plot(vec_wa, vec_max_num_srs)

vec_wa = []
vec_avg_num_srs = []
vec_max_num_srs = []
for T in range(2, 11):
    (wa, avg_num_srs, max_num_srs) = Bc_inf.tiering(N, T, S)
    vec_wa.append(wa)
    vec_avg_num_srs.append(avg_num_srs)
    vec_max_num_srs.append(max_num_srs)
plt.plot(vec_wa, vec_avg_num_srs)
plt.plot(vec_wa, vec_max_num_srs)

vec_entropy_threshold = []
vec_wa_theory = []
vec_num_srs_theory = []
vec_wa = []
vec_avg_num_srs = []
vec_max_num_srs = []
for entropy_threshold in np.arange(args.entropy_threshold_begin, 3, 0.05):
    (wa, avg_num_srs, max_num_srs) = Bc_inf.benefit_cost(N, entropy_threshold, S)
    if args.verbose:
        print('%f\t%f\t%f\t%f' %(entropy_threshold, wa, avg_num_srs, max_num_srs))
    vec_entropy_threshold.append(entropy_threshold)
    if S is None:
        wa_theory = math.log2(N) / entropy_threshold
    else:
        wa_theory = math.log2(S / math.e) / entropy_threshold + math.e + 1
    vec_wa_theory.append(wa_theory)
    # vec_num_srs_theory.append()
    vec_wa.append(wa)
    vec_avg_num_srs.append(avg_num_srs)
    vec_max_num_srs.append(max_num_srs)
plt.plot(vec_wa, vec_avg_num_srs)
plt.plot(vec_wa, vec_max_num_srs)

plt.ylim(bottom=0)
plt.legend(['leveling avg', 'leveling max', 'tiering avg', 'tiering max', 'benefit-cost avg', 'benefit-cost max'], fontsize=8)
pdf_path = get_pdf_path('simulation-wa-ra')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show(block=False)

color_list = plt.rcParams['axes.prop_cycle'].by_key()['color']
color_index = 0

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
plt.xlabel('Entropy threshold', fontsize=8)
ax1 = plt.gca()
ax1.set_ylabel('Write amplification', fontsize=8)
ax1.plot(vec_entropy_threshold, vec_wa_theory, label='WA theory', color=color_list[color_index])
color_index += 1
ax1.plot(vec_entropy_threshold, vec_wa, label='WA simulation', color=color_list[color_index])
color_index += 1
ax1.set_ylim(bottom=0)
ax2 = ax1.twinx()
ax2.set_ylabel('Num sorted runs', fontsize=8)
ax2.plot(vec_entropy_threshold, vec_avg_num_srs, label='# runs avg', color=color_list[color_index])
color_index += 1
ax2.plot(vec_entropy_threshold, vec_max_num_srs, label='# runs max', color=color_list[color_index])
color_index += 1
ax2.set_ylim(bottom=0)
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=8)
pdf_path = get_pdf_path('simulation-benefit-cost')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show()
