#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
	print('Usage: ' + sys.argv[0] + ' dir')
	exit()
dir = sys.argv[1]

value = '-value-1000'
compaction = '-compaction-200MB-s'
warmup_secs = 1500
run_secs = 500
read_workload = '-nexts-50-seek-1'

unique_size = '10GB'

# The humanfriendly module requires Python <= 3.12
import subprocess
unique_size_bytes = subprocess.run(['humanfriendly', '--parse-size', unique_size], stdout=subprocess.PIPE, text=True).stdout
unique_size_bytes = int(unique_size_bytes)

import os
import math
import numpy as np
import pandas as pd
import json
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

vec_write_MB_s = [10, 30, 50]

versions = [
    {
        'path': 'rocksdb-tuned',
        'marker': 'o',
        'markersize': 4,
        'markerfacecolor': 'none',
    },
    {
        'path': 'tiering2',
        'marker': 'v',
        'markersize': 4,
        'markerfacecolor': 'none',
    },
    {
        'path': 'tiering4',
        'marker': '^',
        'markersize': 4,
        'markerfacecolor': 'none',
    },
    {
        'path': 'tiering8',
        'marker': '>',
        'markersize': 4,
        'markerfacecolor': 'none',
    },
    {
        'path': 'universal',
        'marker': 's',
        'markersize': 2,
    },
    {
        'path': 'benefit-cost',
        'marker': 'D',
        'markersize': 2,
    },
]
import common
for v in versions:
    v.update(common.versions[v['path']])
version_names = [v['name'] for v in versions]

bar_width = 1 / (len(versions) + 1)
cluster_width = bar_width * len(versions)

fig = plt.figure(dpi=300, figsize=(cm_to_inch(DOUBLE_COL_WIDTH), cm_to_inch(1)), constrained_layout=True)
handles = []
for version in versions:
    handles.append(mpl.patches.Patch(facecolor=version['color'], hatch=version['hatch'], edgecolor='black', linewidth=0.5))
fig.legend(handles=handles, labels=version_names, fontsize=9, ncol=len(versions), loc='center', bbox_to_anchor=(0.5, 1.05), handlelength=1, handletextpad=0.5, frameon=False)
pdf_path = os.path.join(dir, 'const-write-rates-legend.pdf')
fig.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)

subfig_height = 3.5
fig_srs_avg = plt.figure(dpi=300, figsize=(cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(subfig_height)), constrained_layout=True)
gs = gridspec.GridSpec(1, 3, figure=fig_srs_avg)
vec_ax_srs_avg = []
for i in range(0, len(vec_write_MB_s)):
    plt.subplot(gs[0, i])
    plt.xlabel(str(vec_write_MB_s[i]) + 'MB/s', fontsize=9)
    plt.xticks([])
    if i == 0:
        plt.ylabel('Avg # of sorted runs', fontsize=9)
    if i == 1:
        plt.yscale('log')
        plt.ylim((1, 200))
    elif i == 2:
        plt.yscale('log')
        plt.ylim((1, 2000))
    ax = plt.gca()
    ax.set_axisbelow(True)
    ax.grid(axis='y')
    vec_ax_srs_avg.append(plt.gca())

fig_srs_p99 = plt.figure(dpi=300, figsize=(cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(subfig_height)), constrained_layout=True)
gs = gridspec.GridSpec(1, 3, figure=fig_srs_p99)
vec_ax_srs_p99 = []
for i in range(0, len(vec_write_MB_s)):
    plt.subplot(gs[0, i])
    plt.xlabel(str(vec_write_MB_s[i]) + 'MB/s', fontsize=9)
    plt.xticks([])
    if i == 0:
        plt.ylabel('P99 # of sorted runs', fontsize=9)
    if i == 1:
        plt.yscale('log')
        plt.ylim((1, 200))
    elif i == 2:
        plt.yscale('log')
        plt.ylim((1, 2000))
    ax = plt.gca()
    ax.set_axisbelow(True)
    ax.grid(axis='y')
    vec_ax_srs_p99.append(ax)

fig_lat_avg = plt.figure(dpi=300, figsize=(cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(subfig_height)), constrained_layout=True)
gs = gridspec.GridSpec(1, 3, figure=fig_lat_avg)
vec_ax_lat_avg = []
for i in range(0, len(vec_write_MB_s)):
    plt.subplot(gs[0, i])
    plt.xlabel(str(vec_write_MB_s[i]) + 'MB/s', fontsize=9)
    plt.xticks([])
    if i == 0:
        plt.ylabel('Avg read latency (ms)', fontsize=9)
    if i == 1:
        plt.yscale('log')
        plt.ylim((1, 20))
    elif i == 2:
        plt.yscale('log')
        plt.ylim((1, 200))
    ax = plt.gca()
    ax.set_axisbelow(True)
    ax.grid(axis='y')
    vec_ax_lat_avg.append(ax)

fig_lat_p99 = plt.figure(dpi=300, figsize=(cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(subfig_height)), constrained_layout=True)
gs = gridspec.GridSpec(1, 3, figure=fig_lat_p99)
vec_ax_lat_p99 = []
for i in range(0, len(vec_write_MB_s)):
    plt.subplot(gs[0, i])
    plt.xlabel(str(vec_write_MB_s[i]) + 'MB/s', fontsize=9)
    plt.xticks([])
    if i == 0:
        plt.ylabel('P99 read latency (ms)', fontsize=9)
    if i == 1:
        plt.yscale('log')
        plt.ylim((1, 40))
    elif i == 2:
        plt.yscale('log')
        plt.ylim((1, 300))
    ax = plt.gca()
    ax.set_axisbelow(True)
    ax.grid(axis='y')
    vec_ax_lat_p99.append(ax)

fig_sa_avg = plt.figure(dpi=300, figsize=(cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(subfig_height)), constrained_layout=True)
gs = gridspec.GridSpec(1, 3, figure=fig_sa_avg)
vec_ax_sa_avg = []
for i in range(0, len(vec_write_MB_s)):
    plt.subplot(gs[0, i])
    plt.xlabel(str(vec_write_MB_s[i]) + 'MB/s', fontsize=9)
    plt.xticks([])
    if i == 0:
        plt.ylabel('Average space amp', fontsize=9)
    ax = plt.gca()
    ax.set_axisbelow(True)
    ax.grid(axis='y')
    vec_ax_sa_avg.append(ax)

fig_sa_max = plt.figure(dpi=300, figsize=(cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(subfig_height)), constrained_layout=True)
gs = gridspec.GridSpec(1, 3, figure=fig_sa_max)
vec_ax_sa_max = []
for i in range(0, len(vec_write_MB_s)):
    plt.subplot(gs[0, i])
    plt.xlabel(str(vec_write_MB_s[i]) + 'MB/s', fontsize=9)
    plt.xticks([])
    if i == 0:
        plt.ylabel('Max space amp', fontsize=9)
    ax = plt.gca()
    ax.set_axisbelow(True)
    ax.grid(axis='y')
    vec_ax_sa_max.append(ax)

for i in range(len(vec_write_MB_s)):
    write_MB_s = vec_write_MB_s[i]
    for version_idx in range(len(versions)):
        version = versions[version_idx]
        x = -cluster_width / 2 + bar_width / 2 + version_idx * bar_width

        workload = 'readwhilewriting-key-16' + value + '-unique-size-10GB-warmup-secs-' + str(warmup_secs) + '-run-secs-' + str(run_secs) + '-memtable-8MiB'
        if version['path'] in ['tiering2', 'tiering4', 'tiering8', 'benefit-cost']:
            workload += '-max-running-bg-jobs-1'
        workload += compaction + '-write-' + str(write_MB_s) + 'MB-s' + read_workload

        data_dir = os.path.join(dir, workload, version['path'])

        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        vec_ax_srs_avg[i].bar(x, report['num-sorted-runs'].mean(), width=bar_width, edgecolor='black', linewidth=0.5, color=version['color'], hatch=version['hatch'])
        vec_ax_srs_p99[i].bar(x, np.percentile(report['num-sorted-runs'], 99), width=bar_width, edgecolor='black', linewidth=0.5, color=version['color'], hatch=version['hatch'])

        read_latency_us = json.load(open(os.path.join(data_dir, 'read-latency-us.json')))
        vec_ax_lat_avg[i].bar(x, float(read_latency_us['Average'] / 1000), width=bar_width, edgecolor='black', linewidth=0.5, color=version['color'], hatch=version['hatch'])
        vec_ax_lat_p99[i].bar(x, float(read_latency_us['99%']) / 1000, width=bar_width, edgecolor='black', linewidth=0.5, color=version['color'], hatch=version['hatch'])

        vec_ax_sa_avg[i].bar(x, report['size'].mean() / unique_size_bytes, width=bar_width, edgecolor='black', linewidth=0.5, color=version['color'], hatch=version['hatch'])
        vec_ax_sa_max[i].bar(x, report['size'].max() / unique_size_bytes, width=bar_width, edgecolor='black', linewidth=0.5, color=version['color'], hatch=version['hatch'])

def savefig(fig, name):
    pdf_path = os.path.join(dir, 'const-write-rates-' + name + value + compaction + '-warmup-' + str(warmup_secs) + '-run-' + str(run_secs) + read_workload + '.pdf')
    fig.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
    print('Plot saved to ' + pdf_path)

savefig(fig_srs_avg, 'num-srs-avg')
savefig(fig_srs_p99, 'num-srs-p99')
savefig(fig_lat_avg, 'latency-avg')
savefig(fig_lat_p99, 'latency-p99')
savefig(fig_sa_avg, 'sa-avg')
savefig(fig_sa_max, 'sa-max')
