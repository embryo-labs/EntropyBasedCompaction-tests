#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
	print('Usage: ' + sys.argv[0] + ' dir')
	exit()
dir = sys.argv[1]

value = '-value-603'
compaction = '-compaction-200MB-s'
warmup_secs = 1200
run_secs = 1200
read_workload = '-get-0.87-seek-0.13-nexts-48'

unique_size = '10GB'

# The humanfriendly module requires Python <= 3.12
import subprocess
unique_size_bytes = subprocess.run(['humanfriendly', '--parse-size', unique_size], stdout=subprocess.PIPE, text=True).stdout
unique_size_bytes = int(unique_size_bytes)

import os
import numpy as np
import pandas as pd
import json
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec

import common

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'serif',
    'font.serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 9,
})

vec_write_MB_s = [10, 30, 50]

versions = [
    {
        'path': 'rocksdb-tuned',
        'max-running-bg-jobs': None,
    },
    {
        'path': 'tiering2',
        'max-running-bg-jobs': 1,
    },
    {
        'path': 'tiering4',
        'max-running-bg-jobs': 1,
    },
    {
        'path': 'tiering8',
        'max-running-bg-jobs': 1,
    },
    {
        'path': 'universal-hard-trigger',
        'max-running-bg-jobs': None,
    },
    {
        'path': 'entropy-based',
        'max-running-bg-jobs': 1,
    },
]

for v in versions:
    if v['path'] in common.versions:
        v.update(common.versions[v['path']])
version_names = [v.get('name', v['path']) for v in versions]

bar_width = 1 / (len(versions) + 1)
cluster_width = bar_width * len(versions)

def draw_panels(fig, outer_grid, panels):
    for row in range(0, len(panels)):
        for col in range(0, len(panels[row])):
            panel = panels[row][col]
            inner_grid = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=outer_grid[row, col], wspace=0.4)
            for i, write_MB_s in enumerate(vec_write_MB_s):
                ax = plt.Subplot(fig, inner_grid[i])
                fig.add_subplot(ax)
                panel['ax'].append(ax)

                ax.set_xlabel(f"{write_MB_s}MB/s")
                ax.set_xticks([])

                if i == 0:
                    ax.set_ylabel(panel['ylabel'])
                if panel['log_scale'][i]:
                    ax.set_yscale('log')
                    ax.tick_params(axis='y', pad=1)
                if 'yticks' in panel and panel['yticks'][i] is not None:
                    ax.set_yticks(panel['yticks'][i])
                ax.tick_params(axis='y', which='minor', labelleft=False)
                ax.set_axisbelow(True)
                ax.grid(axis='y')
def draw_ylims(panels):
    for row in range(0, len(panels)):
        for col in range(0, len(panels[row])):
            panel = panels[row][col]
            for i, write_MB_s in enumerate(vec_write_MB_s):
                ax = panel['ax'][i]
                if panel['ylims'][i] is not None:
                    ax.set_ylim(panel['ylims'][i])

panels_main = [
    [
        {
            "title": "(a) Number of sorted runs (average)",
            "ylabel": "Avg # of sorted runs",
            'ylims': [None, (1, None), (1, None)],
            "log_scale": [False, True, True],
            'ax': [],
        },
        {
            "title": "(b) Number of sorted runs (99th percentile)",
            "ylabel": "P99 # of sorted runs",
            'ylims': [None, (1, None), (1, None)],
            "log_scale": [False, True, True],
            'ax': [],
        },
    ],
    [
        {
            "title": "(c) Read latency (average)",
            "ylabel": "Avg read latency (ms)",
            'ylims': [None, (0.1, None), (0.1, None)],
            "log_scale": [False, True, True],
            'ax': [],
        },
        {
            "title": "(d) Read latency (99th percentile)",
            "ylabel": "P99 read latency (ms)",
            'ylims': [None, (1, None), (1, None)],
            "log_scale": [False, True, True],
            'ax': [],
        },
    ],
    [
        {
            "title": "(e) Space amplification (average)",
            "ylabel": "Average space amp",
            'ylims': [None, None, None],
            "log_scale": [False, False, False],
            'ax': [],
        },
        {
            "title": "(f) Space amplification (max)",
            "ylabel": "Max space amp",
            'ylims': [None, None, None],
            'yticks': [None, [0, 2, 4, 6, 8, 10], None],
            "log_scale": [False, False, False],
            'ax': [],
        },
    ],
]
fig_main = plt.figure(dpi=300, figsize=(common.double_col_inch, 4.5))
outer_grid = gridspec.GridSpec(3, 2, figure=fig_main, hspace=0.4, wspace=0.2, left=0, right=0.93, bottom=0, top=0.92)
draw_panels(fig_main, outer_grid, panels_main)
for row in range(0, len(panels_main)):
    for col in range(0, len(panels_main[row])):
        panel = panels_main[row][col]
        bbox = outer_grid[row, col].get_position(fig_main)
        fig_main.text(bbox.x0 + bbox.width/2, bbox.y0 - 0.045, panel['title'], ha='center', va='top')
handles = [mpl.patches.Patch(facecolor=v['facecolor'], hatch=v['hatch'], 
                            edgecolor='black', linewidth=0.5) for v in versions]
fig_main.legend(handles=handles, labels=version_names, ncol=len(versions), 
        loc='upper center', bbox_to_anchor=(0.44, 0.99), frameon=False, 
        handlelength=1.5, handletextpad=0.5, columnspacing=1.0)

panels_scan_get = [
    [
        {
            "title": "(a) Scan latency (average)",
            "ylabel": "Avg scan latency (ms)",
            'ylims': [None, (1, None), (1, None)],
            "log_scale": [False, True, True],
            'ax': [],
        },
    ],
    [
        {
            'title': '(b) Get latency (average)',
            'ylabel': 'Avg get latency (ms)',
            'ylims': [None, None, None],
            'yticks': [[0, 0.1], [0, 0.1], None],
            'log_scale': [False, False, False],
            'ax': [],
        },
    ],
]
fig_scan_get = plt.figure(dpi=300, figsize=(common.single_col_inch, 2.8))
outer_grid = gridspec.GridSpec(2, 1, figure=fig_scan_get, hspace=0.4, wspace=0.2, 
                            left=0, right=0.93, bottom=0, top=0.92)
draw_panels(fig_scan_get, outer_grid, panels_scan_get)
for row in range(0, len(panels_scan_get)):
    for col in range(0, len(panels_scan_get[row])):
        panel = panels_scan_get[row][col]
        bbox = outer_grid[row, col].get_position(fig_scan_get)
        fig_scan_get.text(bbox.x0 + bbox.width/2, bbox.y0 - 0.07, panel['title'], ha='center', va='top')
handles = [mpl.patches.Patch(facecolor=v['facecolor'], hatch=v['hatch'], 
                            edgecolor='black', linewidth=0.5) for v in versions]
fig_scan_get.legend(handles=handles, labels=version_names, ncol=3, 
        loc='upper center', bbox_to_anchor=(0.44, 1.1), frameon=False, 
        handlelength=1.5, handletextpad=0.5, columnspacing=1.0)


for i, write_MB_s in enumerate(vec_write_MB_s):
    for version_idx, version in enumerate(versions):
        x = -cluster_width / 2 + bar_width / 2 + version_idx * bar_width
        if version['name'] == 'By-theory':
            entropy_threshold = '-autotune_entropy_threshold'
        else:
            entropy_threshold = ''
        if version['path'] in ['no_preemption_conditions', 'entropy-based']:
            compaction_trigger = '-compaction-trigger-2'
        else:
            compaction_trigger = ''
        if version['max-running-bg-jobs'] is None:
            max_running_bg_jobs = ''
        else:
            max_running_bg_jobs = '-max-running-bg-jobs-1'
        workload = f'readwhilewriting-key-16{value}-unique-size-10GB-warmup-secs-{warmup_secs}-run-secs-{run_secs}{entropy_threshold}{compaction_trigger}-memtable-8MiB{max_running_bg_jobs}{compaction}-write-{write_MB_s}MB-s{read_workload}'
        data_dir = os.path.join(dir, workload, version['path'])
        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        read_latency_us = json.load(open(os.path.join(data_dir, 'read-latency-us.json')))
        scan_latency_us = json.load(open(os.path.join(data_dir, 'seek-latency-us.json')))
        get_latency_us = json.load(open(os.path.join(data_dir, 'get-latency-us.json')))

        def add_bar(panel, val):
            panel['ax'][i].bar(x, val, width=bar_width, edgecolor='black', linewidth=0.5, facecolor=version['facecolor'], hatch=version['hatch'])
        add_bar(panels_main[0][0], report['num-sorted-runs'].mean())
        add_bar(panels_main[0][1], np.percentile(report['num-sorted-runs'], 99))
        add_bar(panels_main[1][0], read_latency_us['Average'] / 1000)
        add_bar(panels_main[1][1], read_latency_us['99%'] / 1000)
        add_bar(panels_main[2][0], report['size'].mean() / unique_size_bytes)
        add_bar(panels_main[2][1], report['size'].max() / unique_size_bytes)

        add_bar(panels_scan_get[0][0], scan_latency_us['Average'] / 1000)
        add_bar(panels_scan_get[1][0], get_latency_us['Average'] / 1000)

renderer = fig_main.canvas.get_renderer()
tight_bbox = fig_main.get_tightbbox(renderer)
print(f'width: {tight_bbox.width}, height: {tight_bbox.height}')

draw_ylims(panels_main)
pdf_path = os.path.join(dir, f'const-write-rates{value}{compaction}-warmup-{warmup_secs}-run-{run_secs}{read_workload}.pdf')
fig_main.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print(f'Plot saved to {pdf_path}')


draw_ylims(panels_scan_get)
pdf_path = os.path.join(dir, f'const-write-rates-read-latency{value}{compaction}-warmup-{warmup_secs}-run-{run_secs}{read_workload}.pdf')
fig_scan_get.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print(f'Plot saved to {pdf_path}')
