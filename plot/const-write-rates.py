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
path_version = {}
for v in versions:
    if v['path'] in common.versions:
        v.update(common.versions[v['path']])
    path_version[v['path']] = v
version_names = [v.get('name', v['path']) for v in versions]

bar_width = 1 / (len(versions) + 1)
cluster_width = bar_width * len(versions)

def draw_panel(panel):
    for i, write_MB_s in enumerate(vec_write_MB_s):
        ax = panel['ax'][i]
        ax.set_xlabel(f"{write_MB_s}MB/s")
        ax.set_xticks([])
        if i == 0:
            ax.set_ylabel(panel['ylabel'], loc=panel.get('ylabel_loc', 'center'))
        if panel['log_scale'][i]:
            ax.set_yscale('log')
            ax.tick_params(axis='y', pad=1)
        if 'yticks' in panel and panel['yticks'][i] is not None:
            ax.set_yticks(panel['yticks'][i])
        ax.tick_params(axis='y', which='minor', labelleft=False)
        ax.set_axisbelow(True)
        ax.grid(axis='y')

def draw_panel_ylims(panel):
    for i in range(len(vec_write_MB_s)):
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
            'ylabel_loc': 'top',
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
]
fig_main = plt.figure(dpi=300, figsize=(common.double_col_inch, 2.8))
outer_grid = gridspec.GridSpec(2, 2, figure=fig_main, left=0.06, bottom=0.12, right=0.998, top=0.93, wspace=0.2, hspace=0.4)
for row in range(0, len(panels_main)):
    for col in range(0, len(panels_main[row])):
        panel = panels_main[row][col]
        inner_grid = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=outer_grid[row, col], wspace=0.4)
        for i in range(len(vec_write_MB_s)):
            ax = fig_main.add_subplot(inner_grid[i])
            panel['ax'].append(ax)
        draw_panel(panel)
        bbox = outer_grid[row, col].get_position(fig_main)
        fig_main.text(bbox.x0 + bbox.width/2, bbox.y0 - 0.07, panel['title'], ha='center', va='top')
handles = [mpl.patches.Patch(facecolor=v['facecolor'], hatch=v['hatch'], 
                            edgecolor='black', linewidth=0.5) for v in versions]
fig_main.legend(
    handles=handles,
    labels=version_names,
    ncol=len(versions),
    loc='upper center',
    bbox_to_anchor=(0.5, 1.02),
    frameon=False,
    borderpad=0,
    handlelength=1.5,
    handletextpad=0.5,
    columnspacing=1.0,
)

panel_sa_max = {
    "ylabel": "Max space amp",
    'ylims': [None, None, None],
    'yticks': [None, None, None],
    "log_scale": [False, False, False],
    'ax': [],
}
fig_sa_max = plt.figure(dpi=300, figsize=(common.single_col_inch, 1.2), constrained_layout=True)
fig_sa_max.get_layout_engine().set(
    h_pad=0.01,
    w_pad=0.01,
    rect=(0, 0, 1, 0.74),
)
gs = gridspec.GridSpec(1, 3, figure=fig_sa_max)
for i in range(len(vec_write_MB_s)):
    ax = plt.subplot(gs[0, i])
    panel_sa_max['ax'].append(ax)
draw_panel(panel_sa_max)
handles = [mpl.patches.Patch(facecolor=v['facecolor'], hatch=v['hatch'], 
                            edgecolor='black', linewidth=0.5) for v in versions]
fig_sa_max.legend(
    handles=handles,
    labels=version_names,
    ncol=3,
    loc='upper center',
    bbox_to_anchor=(0.53, 1.04),
    frameon=False,
    borderpad=0,
    handlelength=1.5,
    handletextpad=0.5,
    columnspacing=1.0,
    labelspacing=0.3,
)

panels_scan_get = [
    {
        "title": "(a) Scan latency (average)",
        'title_xy': (0.5, 0.5),
        "ylabel": "Avg scan latency (ms)",
        'ylims': [None, (1, None), (1, None)],
        "log_scale": [False, True, True],
        'ax': [],
    },
    {
        'title': '(b) Get latency (average)',
        'title_xy': (0.5, 0.05),
        'ylabel': 'Avg get latency (ms)',
        'ylims': [None, None, None],
        'yticks': [[0, 0.1], [0, 0.1], None],
        'log_scale': [False, False, False],
        'ax': [],
    },
]
fig_scan_get = plt.figure(dpi=300, figsize=(common.single_col_inch, 2.8), constrained_layout=True)
gs = gridspec.GridSpec(2, 3, figure=fig_scan_get)
fig_scan_get.get_layout_engine().set(
    w_pad=0.01,
    hspace=0.13,
    rect=(0, 0.05, 1, 0.85),
)
for row, panel in enumerate(panels_scan_get):
    for col in range(len(vec_write_MB_s)):
        ax = plt.subplot(gs[row, col])
        panel['ax'].append(ax)
    draw_panel(panel)
    x, y = panel['title_xy']
    fig_scan_get.text(x, y, panel['title'], ha='center', va='top')
handles = [mpl.patches.Patch(facecolor=v['facecolor'], hatch=v['hatch'], 
                            edgecolor='black', linewidth=0.5) for v in versions]
fig_scan_get.legend(
    handles=handles,
    labels=version_names,
    ncol=3,
    loc='upper center',
    bbox_to_anchor=(0.55, 1.0),
    borderaxespad=0.01,
    frameon=False,
    borderpad=0,
    handlelength=1.5,
    handletextpad=0.5,
    columnspacing=1.0,
    labelspacing=0.4,
)


versions_intro = [
    {
        'path': 'rocksdb-tuned',
        'name': 'Leveling (T=5)',
    },
    {
        'path': 'tiering4',
        'name': 'Tiering (T=4)',
    },
    {
        'path': 'entropy-based',
        'name': common.versions['entropy-based']['name'],
    },
]
map_path_to_version_intro_idx = {}
for version_intro_idx, v in enumerate(versions_intro):
    map_path_to_version_intro_idx[v['path']] = version_intro_idx

bar_width_intro = 1 / (len(versions_intro) + 1)
cluster_width_intro = 1 / (len(versions_intro) + 1) * len(versions_intro)

fig_intro = plt.figure(dpi=300, figsize=(3.1, 1.2), constrained_layout=True)
gs = gridspec.GridSpec(1, 2, figure=fig_intro)
plt.subplot(gs[0, 0])
ax_10 = plt.gca()
plt.xlabel('(a) User write 10MB/s')
plt.xticks([])
plt.ylabel('Avg # of sorted runs')

plt.subplot(gs[0, 1])
ax_30 = plt.gca()
plt.xlabel('(b) User write 30MB/s')
plt.xticks([])

handles = []
version_names = []
for v_intro in versions_intro:
    v = path_version[v_intro['path']]
    handles.append(mpl.patches.Patch(facecolor=v['facecolor'], hatch=v['hatch'], edgecolor='black', linewidth=0.5))
    version_names.append(v_intro['name'])
fig_intro.legend(handles=handles, labels=version_names, ncol=len(versions_intro), 
        loc='upper center', bbox_to_anchor=(0.56, 1.2), frameon=False, 
        handlelength=1.3, handletextpad=0.5, columnspacing=1.0)


for i, write_MB_s in enumerate(vec_write_MB_s):
    for version_idx, version in enumerate(versions):
        x = -cluster_width / 2 + bar_width / 2 + version_idx * bar_width
        if version['max-running-bg-jobs'] is None:
            max_running_bg_jobs = ''
        else:
            max_running_bg_jobs = '-max-running-bg-jobs-1'
        workload = f'readwhilewriting-key-16{value}-unique-size-{unique_size}-warmup-secs-{warmup_secs}-run-secs-{run_secs}{max_running_bg_jobs}-write-{write_MB_s}MB-s-no-stall-memtable-8MiB{compaction}{read_workload}'
        data_dir = os.path.join(dir, workload, version['path'])
        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        read_latency_us = json.load(open(os.path.join(data_dir, 'read-latency-us.json')))
        scan_latency_us = json.load(open(os.path.join(data_dir, 'seek-latency-us.json')))
        get_latency_us = json.load(open(os.path.join(data_dir, 'get-latency-us.json')))

        num_srs_avg = report['num-sorted-runs'].mean()

        def add_bar(panel, val):
            panel['ax'][i].bar(x, val, width=bar_width, edgecolor='black', linewidth=0.5, facecolor=version['facecolor'], hatch=version['hatch'])
        add_bar(panels_main[0][0], num_srs_avg)
        add_bar(panels_main[0][1], np.percentile(report['num-sorted-runs'], 99))
        add_bar(panels_main[1][0], read_latency_us['Average'] / 1000)
        add_bar(panels_main[1][1], read_latency_us['99%'] / 1000)

        add_bar(panel_sa_max, report['size'].max() / unique_size_bytes)

        add_bar(panels_scan_get[0], scan_latency_us['Average'] / 1000)
        add_bar(panels_scan_get[1], get_latency_us['Average'] / 1000)

        if version['path'] in map_path_to_version_intro_idx:
            version_intro_idx = map_path_to_version_intro_idx[version['path']]
            match write_MB_s:
                case 10:
                    ax = ax_10
                case 30:
                    ax = ax_30
                case _:
                    ax = None
            if ax is not None:
                x = -cluster_width_intro / 2 + bar_width_intro / 2 + version_intro_idx * bar_width_intro
                ax.bar(x, num_srs_avg, width=bar_width_intro * 0.65, edgecolor='black', linewidth=0.5, facecolor=version['facecolor'], hatch=version['hatch'])

renderer = fig_main.canvas.get_renderer()
tight_bbox = fig_main.get_tightbbox(renderer)
print(f'width: {tight_bbox.width}, height: {tight_bbox.height}')
for row in range(0, len(panels_main)):
    for col in range(0, len(panels_main[row])):
        draw_panel_ylims(panels_main[row][col])
pdf_path = os.path.join(dir, f'const-write-rates{value}{compaction}-warmup-{warmup_secs}-run-{run_secs}{read_workload}.pdf')
fig_main.savefig(pdf_path, metadata={'CreationDate': None})
print(f'Plot saved to {pdf_path}')

draw_panel_ylims(panel_sa_max)
pdf_path = os.path.join(dir, f'const-write-rates-sa-max{value}{compaction}-warmup-{warmup_secs}-run-{run_secs}{read_workload}.pdf')
fig_sa_max.savefig(pdf_path, metadata={'CreationDate': None})
print(f'Plot saved to {pdf_path}')

for panel in panels_scan_get:
    draw_panel_ylims(panel)
pdf_path = os.path.join(dir, f'const-write-rates-read-latency{value}{compaction}-warmup-{warmup_secs}-run-{run_secs}{read_workload}.pdf')
fig_scan_get.savefig(pdf_path, metadata={'CreationDate': None})
print(f'Plot saved to {pdf_path}')


pdf_path = os.path.join(dir, f'const-write-rates-intro{value}{compaction}-warmup-{warmup_secs}-run-{run_secs}{read_workload}.pdf')
fig_intro.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print(f'Plot saved to {pdf_path}')
