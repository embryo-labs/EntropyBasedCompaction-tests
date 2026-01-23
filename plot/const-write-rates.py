#!/usr/bin/env python3
import sys
import os
import math
import numpy as np
import pandas as pd
import json
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.ticker import LogLocator, NullFormatter, ScalarFormatter
import subprocess

# --- Input Check ---
if len(sys.argv) != 2:
    print('Usage: ' + sys.argv[0] + ' dir')
    exit()
dir = sys.argv[1]

# --- Configuration Parameters ---
value = '-value-1000'
compaction = '-compaction-200MB-s'
warmup_secs = 1500
run_secs = 500
read_workload = '-nexts-50-seek-1'
unique_size = '10GB'

# Parse size using humanfriendly if available, otherwise fallback
try:
    unique_size_bytes = subprocess.run(['humanfriendly', '--parse-size', unique_size], stdout=subprocess.PIPE, text=True).stdout
    unique_size_bytes = int(unique_size_bytes)
except:
    unique_size_bytes = 10 * 1024**3 

# --- Plotting Style Settings ---
SINGLE_COL_WIDTH = 8.5
DOUBLE_COL_WIDTH = 17.8 

def cm_to_inch(value):
    return value/2.54

mpl.rcParams.update({
    # --- Make hatch lines thinner here ---
    'hatch.linewidth': 0.5,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Linux Libertine O', 'DejaVu Sans', 'Arial'],
    'axes.unicode_minus': False,
    'font.size': 9,
    'axes.labelsize': 9,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'lines.linewidth': 1,
    'axes.linewidth': 1,
    'xtick.major.width': 0.5,
    'ytick.major.width': 0.5,
    'xtick.minor.width': 0.5,
    'ytick.minor.width': 0.5,
})

vec_write_MB_s = [10, 30, 50]

versions = [
    {'path': 'rocksdb-tuned', 'marker': 'o', 'markersize': 4, 'markerfacecolor': 'none'},
    {'path': 'tiering2', 'marker': 'v', 'markersize': 4, 'markerfacecolor': 'none'},
    {'path': 'tiering4', 'marker': '^', 'markersize': 4, 'markerfacecolor': 'none'},
    {'path': 'tiering8', 'marker': '>', 'markersize': 4, 'markerfacecolor': 'none'},
    {'path': 'universal', 'marker': 's', 'markersize': 2},
    {'path': 'benefit-cost', 'marker': 'D', 'markersize': 2},
]

# Try importing common configuration, use defaults if missing
try:
    import common
    for v in versions:
        if v['path'] in common.versions:
            v.update(common.versions[v['path']])
except ImportError:
    colors = ["C0", "C1", "C3", "C4", "C5", "C2"]
    # Use SINGLE characters for thinner appearance
    hatches = ['/', '\\', '|', '-', '+', 'x']
    for i, v in enumerate(versions):
        if 'color' not in v: v['color'] = colors[i % len(colors)]
        if 'hatch' not in v: v['hatch'] = hatches[i % len(hatches)]
        if 'name' not in v: v['name'] = v['path']

version_names = [v.get('name', v['path']) for v in versions]
bar_width = 1 / (len(versions) + 1)
cluster_width = bar_width * len(versions)

# --- Data Loading and Caching ---
data_cache = {}
for i, write_MB_s in enumerate(vec_write_MB_s):
    data_cache[i] = {}
    for v_idx, version in enumerate(versions):
        workload = 'readwhilewriting-key-16' + value + '-unique-size-10GB-warmup-secs-' + str(warmup_secs) + '-run-secs-' + str(run_secs) + '-memtable-8MiB'
        if version['path'] in ['tiering2', 'tiering4', 'tiering8', 'benefit-cost']:
            workload += '-max-running-bg-jobs-1'
        workload += compaction + '-write-' + str(write_MB_s) + 'MB-s' + read_workload
        
        data_dir = os.path.join(dir, workload, version['path'])
        try:
            report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
            with open(os.path.join(data_dir, 'read-latency-us.json')) as f:
                latency = json.load(f)
            data_cache[i][v_idx] = {'report': report, 'latency': latency}
        except Exception:
            data_cache[i][v_idx] = None

# --- Panel Configuration ---
panels = [
    {
        "title": "(a) Number of sorted runs (average)",
        "ylabel": "Avg # of sorted runs",
        "getter": lambda d: d['report']['num-sorted-runs'].mean(),
        "ylims": [None, (1, 200), (1, 2000)],
        "log_scale": [False, True, True]
    },
    {
        "title": "(b) Number of sorted runs (99th percentile)",
        "ylabel": "P99 # of sorted runs",
        "getter": lambda d: np.percentile(d['report']['num-sorted-runs'], 99),
        "ylims": [None, (1, 200), (1, 2000)],
        "log_scale": [False, True, True]
    },
    {
        "title": "(c) Read latency (average)",
        "ylabel": "Avg read latency (ms)",
        "getter": lambda d: float(d['latency']['Average'] / 1000),
        "ylims": [None, (1, 20), (1, 300)],
        "log_scale": [False, True, True]
    },
    {
        "title": "(d) Read latency (99th percentile)",
        "ylabel": "P99 read latency (ms)",
        "getter": lambda d: float(d['latency']['99%'] / 1000),
        "ylims": [None, (1, 40), (1, 300)],
        "log_scale": [False, True, True]
    },
    {
        "title": "(e) Space amplification (average)",
        "ylabel": "Average space amp",
        "getter": lambda d: d['report']['size'].mean() / unique_size_bytes,
        "ylims": [(0, 3), (0, 7.5), (0, 12)],
        "log_scale": [False, False, False]
    },
    {
        "title": "(f) Space amplification (max)",
        "ylabel": "Max space amp",
        "getter": lambda d: d['report']['size'].max() / unique_size_bytes,
        "ylims": [(0, 3), (0, 7.5), (0, 12)],
        "log_scale": [False, False, False]
    }
]

# --- Plotting ---
fig_height_cm = 12
fig = plt.figure(dpi=300, figsize=(cm_to_inch(DOUBLE_COL_WIDTH), cm_to_inch(fig_height_cm)))

outer_grid = gridspec.GridSpec(3, 2, figure=fig, hspace=0.37, wspace=0.15, 
                               left=0.08, right=0.99, top=0.92, bottom=0.06) 
# Note: Increased 'left' margin slightly (from 0.06 to 0.08) to make space for aligned labels

for p_idx, panel in enumerate(panels):
    row, col = divmod(p_idx, 2)
    
    # Inner Grid
    inner_grid = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=outer_grid[row, col], wspace=0.35)
    
    for i in range(len(vec_write_MB_s)):
        ax = plt.Subplot(fig, inner_grid[i])
        fig.add_subplot(ax)
        
        # 1. Y-axis settings
        ax.tick_params(axis='y', which='both', left=True, right=False, labelleft=True, direction='out', width=0.5)

        if i == 0:
            lbl = ax.set_ylabel(panel['ylabel'], fontsize=9)
            # --- Key Fix: Force Label Alignment ---
            # Set the label coordinates relative to the axes:
            # x = -0.35 (push left), y = 0.5 (center vertically)
            # You might need to tweak -0.35 depending on your tick lengths
            # ax.yaxis.set_label_coords(-0.25, 0.5) 
        
        # X-axis settings
        ax.set_xlabel(f"{vec_write_MB_s[i]}MB/s", fontsize=8, labelpad=2)
        ax.set_xticks([]) 
        
        # 2. Apply Custom Limits and Log Scale
        # Set Scale
        if panel['log_scale'][i]:
            ax.set_yscale('log')
            # Force ticks for log scale
            ax.yaxis.set_minor_locator(LogLocator(base=10.0, subs='auto', numticks=10))
            ax.yaxis.set_minor_formatter(NullFormatter()) 
            ax.tick_params(axis='y', which='minor', left=True, length=2)
        
        # Set Limits (if defined)
        if panel['ylims'][i] is not None:
            ax.set_ylim(panel['ylims'][i])
        
        ax.set_axisbelow(True)
        ax.grid(axis='y', linestyle='-', alpha=0.5, linewidth=0.5)
        
        # 3. Draw Bars
        for v_idx, version in enumerate(versions):
            dataset = data_cache[i][v_idx]
            if dataset is None: continue
            
            val = panel['getter'](dataset)
            x = -cluster_width / 2 + bar_width / 2 + v_idx * bar_width
            
            ax.bar(x, val, width=bar_width, 
                   edgecolor='black', linewidth=0.5, 
                   color=version['color'], hatch=version['hatch'], zorder=3)

    # Add Bottom Title
    bbox = outer_grid[row, col].get_position(fig)
    fig.text(bbox.x0 + bbox.width/2, bbox.y0 - 0.037, panel['title'], 
             ha='center', va='top', fontsize=10)

# --- Legend ---
handles = [mpl.patches.Patch(facecolor=v.get('color', 'gray'), hatch=v.get('hatch', ''), 
                             edgecolor='black', linewidth=0.5) for v in versions]
fig.legend(handles=handles, labels=version_names, fontsize=9, ncol=len(versions), 
           loc='upper center', bbox_to_anchor=(0.5, 0.99), frameon=False, 
           handlelength=1.5, handletextpad=0.5, columnspacing=1.0)

# --- Save to File ---
output_path = os.path.join(dir, f'all-in-one{value}{compaction}.pdf')
plt.savefig(output_path, format='pdf', bbox_inches='tight', pad_inches=0.02, dpi=300)
print(f'Saved to {output_path}')