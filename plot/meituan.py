#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
    print('Usage: ' + sys.argv[0] + ' dir')
    exit()
dir = sys.argv[1]
mean_step_secs = 300

num_shards = 5
period_secs = 10800
read_workload = '-get-0.87-seek-0.13-nexts-48'
unique_size = '10GB'

# The humanfriendly module requires Python <= 3.12
import subprocess
unique_size_bytes = subprocess.run(['humanfriendly', '--parse-size', unique_size], stdout=subprocess.PIPE, text=True).stdout
unique_size_bytes = int(unique_size_bytes)

import io
import os
import json
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'serif',
    'font.serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 10,
})

versions = [
    {
        'path': 'rocksdb-tuned',
        'max-running-bg-jobs': None,
        'marker': 'o',
        'markersize': 3,
    },
    {
        'path': 'tiering2',
        'max-running-bg-jobs': 1,
        'marker': 'v',
        'markersize': 3,
    },
    {
        'path': 'tiering4',
        'max-running-bg-jobs': 1,
        'marker': '^',
        'markersize': 3,
    },
    {
        'path': 'tiering8',
        'max-running-bg-jobs': 1,
        'marker': '>',
        'markersize': 3,
    },
    {
        'path': 'universal-hard-trigger',
        'max-running-bg-jobs': None,
        'marker': 's',
        'markersize': 3,
    },
    {
        'path': 'lazy-leveling-2-3',
        'max-running-bg-jobs': 1,
    },
    {
        'path': 'bush',
        'max-running-bg-jobs': 1,
    },
    {
        'path': 'vertiorizon-5-4',
        'max-running-bg-jobs': 1,
    },
    {
        'path': 'silk5',
        'max-running-bg-jobs': None,
    },
    {
        'path': 'endure-4-8-1',
        'max-running-bg-jobs': None,
        'memtable': '26MiB',
    },
    {
        'path': 'entropy-based',
        'max-running-bg-jobs': 1,
        'marker': 'D',
        'markersize': 3,
    },
]
import common
for v in versions:
    v.update(common.versions[v['path']])
version_names = [v['name'] for v in versions]

versions_typical = []
for version in versions:
    if 'marker' in version:
        versions_typical.append(version)
version_names_typical = [v['name'] for v in versions_typical]

class BarPlotter:
    versions: list
    bar_width: float
    cluster_width: float
    def __init__(self, versions):
        self.versions = versions
        self.bar_width = 1 / (len(self.versions) + 1)
        self.cluster_width = self.bar_width * len(self.versions)
    def add_bar(self, ax, version_idx, value):
        x = -self.cluster_width / 2 + self.bar_width / 2 + version_idx * self.bar_width
        version = self.versions[version_idx]
        ax.bar(x, value, width=self.bar_width, facecolor=version['facecolor'], edgecolor='black', linewidth=0.5, hatch=version['hatch'])

bar_plotter = BarPlotter(versions)

linewidth = 1
markevery = len(versions_typical)
offset = 1

def find_data_dir(day_type, version):
    if version['max-running-bg-jobs'] is None:
        max_running_bg_jobs = ''
    else:
        max_running_bg_jobs = '-max-running-bg-jobs-1'
    if 'memtable' in version:
        memtable = version['memtable']
    else:
        memtable = '8MiB'
    workload = f'meituan-writer-{day_type}-day-period-secs-{period_secs}-num_shards-{num_shards}-key-16-value-603-unique-size-{unique_size}{max_running_bg_jobs}-no-stall-memtable-{memtable}-compaction-200MB-s{read_workload}'
    return os.path.join(dir, workload, version['path'])

xlabelpad = 1
sa_yticks = [1, 10]

fig = plt.figure(dpi=300, figsize=(common.acmsmall_inch, 5), constrained_layout=True)
fig.get_layout_engine().set(
    h_pad=0.01,
    w_pad=0.01,
    hspace=0.07,
    rect=(0, 0, 1, 0.96),
)
gs = gridspec.GridSpec(3, 1, figure=fig)

plt.subplot(gs[0, 0])
ax_num_srs = plt.gca()
plt.xlabel('Time (hours)\n(a) Number of sorted runs (log scale)', labelpad=xlabelpad)
plt.ylabel('# of sorted runs')
plt.yscale('log')
plt.ylim((3, 100))
ax_num_srs.tick_params(axis='y', which='minor', labelleft=False)
ax_num_srs.grid(axis='y')

plt.subplot(gs[1, 0])
ax_read = plt.gca()
plt.xlabel('Time (hours)\n(b) Read latency (log scale)', labelpad=xlabelpad)
plt.ylabel('Read latency (ms)')
plt.yscale('log')
plt.ylim((0.1, 2))
ax_read.tick_params(axis='y', which='minor', labelleft=False)
ax_read.grid(axis='y')

plt.subplot(gs[2, 0])
ax_sa = plt.gca()
plt.xlabel('Time (hours)\n(c) Space amplification (log scale)', labelpad=xlabelpad)
plt.ylabel('Space amplification')
plt.yscale('log')
plt.ylim((min(sa_yticks), max(sa_yticks)))
plt.yticks(sa_yticks)
ax_sa.tick_params(axis='y', which='minor', labelleft=False)
ax_sa.grid(axis='y')

peak_max_sizes = {}
for version_idx, version in enumerate(versions_typical):
    data_dir = find_data_dir('peak', version)
    report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
    if version['path'] in ['rocksdb-tuned', 'entropy-based']:
        peak_max_sizes[version['path']] = report['size'].max()
    report = report[['secs_elapsed', 'num-sorted-runs', 'size']]
    report = report.groupby(report.index // mean_step_secs).mean()
    ax_num_srs.plot(report['secs_elapsed'] / 3600, report['num-sorted-runs'], linewidth=linewidth, color=version['color'], marker=version['marker'], markersize=version['markersize'], markeredgewidth=0.8, markevery=(version_idx * offset, markevery))
    ax_sa.plot(report['secs_elapsed'] / 3600, report['size'] / unique_size_bytes, linewidth=linewidth, color=version['color'], marker=version['marker'], markersize=version['markersize'], markeredgewidth=0.8, markevery=(version_idx * offset, markevery))

    read_count_time = pd.read_csv(os.path.join(data_dir, 'read-count-time.csv'))

    time = read_count_time['secs_elapsed']
    time = time.groupby(time.index // mean_step_secs).mean()
    micros = read_count_time['micros']
    count = read_count_time['count']
    read_latency = micros.groupby(micros.index // mean_step_secs).sum() / count.groupby(count.index // mean_step_secs).sum()
    ax_read.plot(time / 3600, read_latency / 1000, linewidth=linewidth, color=version['color'], marker=version['marker'], markersize=version['markersize'], markeredgewidth=0.8, markevery=(version_idx * offset, markevery))

fig.legend(
    version_names_typical,
    ncol=6,
    loc='upper center',
    bbox_to_anchor=(0.5, 1.01),
    borderaxespad=0,
    frameon=False,
    handlelength=1,
    handletextpad=0.5,
    columnspacing=1.3,
)
pdf_path = os.path.join(dir, f'meituan-peak-day-num_shards-{num_shards}-unique_size-{unique_size}-period_secs-{period_secs}{read_workload}-mean_step_secs-{mean_step_secs}.pdf')
common.check_visible_labels(fig)
fig.savefig(pdf_path, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)


motivating_versions = [
    version for version in versions_typical
    if version['path'] in ['rocksdb-tuned', 'tiering4', 'entropy-based']
]
panels_motivation = [
    {
        'title': '(a) Normal day',
        'day-type': 'normal',
    },
    {
        'title': '(b) Peak day',
        'day-type': 'peak',
    },
]
fig_motivation = plt.figure(
    dpi=300,
    figsize=(common.acmsmall_inch, 1.5),
    constrained_layout=True,
)
fig_motivation.get_layout_engine().set(
    h_pad=0.01,
    w_pad=0.01,
    rect=(0, 0, 1, 0.85),
)
gs = gridspec.GridSpec(1, 2, figure=fig_motivation)
for col, panel in enumerate(panels_motivation):
    ax = plt.subplot(gs[0, col])
    ax.set_xlabel(f'Time (hours)\n{panel['title']}', labelpad=xlabelpad)
    ax.set_xticks([0, 1, 2, 3])
    if col == 0:
        ax.set_ylabel('# of sorted runs')
    ax.set_yscale('log')
    ax.tick_params(axis='y', which='minor', labelleft=False)
    ax.grid(axis='y')
    for version_idx, version in enumerate(motivating_versions):
        data_dir = find_data_dir(panel['day-type'], version)
        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        report = report[['secs_elapsed', 'num-sorted-runs']]
        report = report.groupby(report.index // mean_step_secs).mean()
        ax.plot(
            report['secs_elapsed'] / 3600,
            report['num-sorted-runs'],
            linewidth=linewidth,
            color=version['color'],
            marker=version['marker'],
            markersize=version['markersize'],
            markeredgewidth=0.8,
            markevery=(version_idx * 2, len(motivating_versions) * 2),
        )
fig_motivation.legend(
    [version['name'] for version in motivating_versions],
    ncol=3,
    loc='upper center',
    bbox_to_anchor=(0.5, 1.01),
    borderaxespad=0,
    frameon=False,
    handlelength=1,
    handletextpad=0.5,
    columnspacing=1,
)
pdf_path = os.path.join(dir, f'meituan-motivation-num_shards-{num_shards}-unique_size-{unique_size}-period_secs-{period_secs}{read_workload}-mean_step_secs-{mean_step_secs}.pdf')
common.check_visible_labels(fig_motivation)
fig_motivation.savefig(pdf_path, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)


def draw_panels(panels, xlabelpad=None):
    for col, panel in enumerate(panels):
        ax = plt.subplot(gs[0, col])
        plt.xlabel(panel['title'], labelpad=xlabelpad)
        ax.tick_params(axis='y', pad=2)
        ax.set_ylabel(panel['ylabel'], loc=panel.get('ylabel_loc', 'center'))
        if 'yticks' in panel:
            plt.yticks(panel['yticks'])
        plt.xticks([])
        ax.set_axisbelow(True)
        ax.grid(axis='y')
        panel['ax'] = ax

panels_read = [
    {
        'title': '(a) Read latency',
        'ylabel': 'Avg latency (ms)',
        'ylabel_loc': 'top',
        'ax': None,
    },
    {
        'title': '(b) Scan latency',
        'ylabel': 'Avg latency (ms)',
        'ylabel_loc': 'top',
        'ax': None,
    },
    {
        'title': '(c) Get latency',
        'ylabel': 'Avg latency (ms)',
        'ylabel_loc': 'top',
        'yticks': [0, 0.1],
        'ax': None,
    }
]
fig_read = plt.figure(dpi=300, figsize=(common.acmsmall_inch, 1.4), constrained_layout=True)
fig_read.get_layout_engine().set(
    h_pad=0.01,
    w_pad=0.01,
    wspace=0.07,
    rect=(0, 0, 1, 0.75),
)
gs = gridspec.GridSpec(1, 3, figure=fig_read)
draw_panels(panels_read, xlabelpad=5)

panels_p99 = [
    {
        'title': '(a) Normal day',
        'ylabel': 'P99 latency (ms)',
        'ylabel_loc': 'top',
        'ax': None,
    },
    {
        'title': '(b) Peak day',
        'ylabel': 'P99 latency (ms)',
        'ylabel_loc': 'top',
        'ax': None,
    },
]
fig_p99 = plt.figure(dpi = 300, figsize = (common.acmsmall_inch, 1.4), constrained_layout=True)
fig_p99.get_layout_engine().set(
    h_pad=0.01,
    w_pad=0.01,
    wspace=0.07,
    rect=(0, 0, 1, 0.75),
)
gs = gridspec.GridSpec(1, 2, figure=fig_p99)
draw_panels(panels_p99)

for day_type in ['normal', 'peak']:
    match day_type:
        case 'normal':
            panel_p99 = panels_p99[0]
        case 'peak':
            panel_p99 = panels_p99[1]
        case _:
            assert False
    for version_idx, version in enumerate(versions):
        data_dir = find_data_dir(day_type, version)
        read_latency_us = json.load(open(os.path.join(data_dir, 'read-latency-us.json')))
        if day_type == 'peak':
            scan_latency_us = json.load(open(os.path.join(data_dir, 'seek-latency-us.json')))
            get_latency_us = json.load(open(os.path.join(data_dir, 'get-latency-us.json')))
            bar_plotter.add_bar(panels_read[0]['ax'], version_idx, read_latency_us['Average'] / 1000)
            bar_plotter.add_bar(panels_read[1]['ax'], version_idx, scan_latency_us['Average'] / 1000)
            bar_plotter.add_bar(panels_read[2]['ax'], version_idx, get_latency_us['Average'] / 1000)
        bar_plotter.add_bar(panel_p99['ax'], version_idx, read_latency_us['99%'] / 1000)

fig_read.legend(
    version_names,
    ncol=6,
    loc='upper center',
    bbox_to_anchor=(0.5, 1.03),
    borderaxespad=0,
    frameon=False,
    handlelength=1,
    handletextpad=0.35,
    columnspacing=1.0,
    labelspacing=0.2,
)
pdf_path = os.path.join(dir, f'meituan-peak-day-read-latency-num_shards-{num_shards}-unique_size-{unique_size}-period_secs-{period_secs}{read_workload}-mean_step_secs-{mean_step_secs}.pdf')
common.check_visible_labels(fig_read)
fig_read.savefig(pdf_path, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)

fig_p99.legend(
    version_names,
    ncol=6,
    loc='upper center',
    bbox_to_anchor=(0.5, 1.03),
    borderaxespad=0,
    frameon=False,
    handlelength=1,
    handletextpad=0.35,
    columnspacing=1.0,
    labelspacing=0.2,
)
pdf_path = os.path.join(dir, 'meituan-p99-read-num_shards-' + str(num_shards) + '-unique_size-' + unique_size + '-period_secs-' + str(period_secs) + read_workload + '.pdf')
common.check_visible_labels(fig_p99)
fig_p99.savefig(pdf_path, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)

tex = io.StringIO()
print('\\defmacro{MeituanPeakRocksDBTunedMaxSize}{' + f'{peak_max_sizes["rocksdb-tuned"] / 1e9:.1f}' + '\\,GB}', file=tex)
print('\\defmacro{MeituanPeakEBCMaxSize}{' + f'{peak_max_sizes["entropy-based"] / 1e9:.1f}' + '\\,GB}', file=tex)
tex = tex.getvalue()
print(tex)
tex_path = 'meituan.tex'
open(tex_path, mode='w').write(tex)
print(f'TeX saved to {tex_path}')
