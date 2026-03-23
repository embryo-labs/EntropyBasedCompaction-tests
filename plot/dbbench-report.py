#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
    print('Usage: ' + sys.argv[0] + ' data-dir')
    exit()
data_dir = sys.argv[1]

import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

import common

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'serif',
    'font.serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 9,
})

plot_dir = data_dir + '/plot'
if not os.path.exists(plot_dir):
    os.system('mkdir -p ' + plot_dir)

report = pd.read_table(os.path.join(data_dir, 'report.csv'), sep=',')
# It seems that the ops of the first several seconds is not limited.
report = report.iloc[20:]

def draw(ylabel, col_name, pdf_name=None):
    if pdf_name is None:
        pdf_name = col_name
    plt.figure(dpi = 300, figsize = (common.single_col_inch, 2), constrained_layout=True)
    ax = plt.gca()
    formatter = ScalarFormatter(useMathText=True)
    formatter.set_powerlimits((-3, 4))
    ax.yaxis.set_major_formatter(formatter)
    plt.plot(report['secs_elapsed'], report[col_name])
    ax.set_ylim(bottom=0)
    plt.xlabel('Time (Seconds)')
    plt.ylabel(ylabel)
    pdf_path = os.path.join(plot_dir, pdf_name + '.pdf')
    plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
    print('Plot saved to ' + pdf_path)
draw('Operation per second', 'interval_qps', 'ops')
draw('Number of wait for LLC', 'wait-for-last-level-compaction')
draw('Size', 'size')
draw('Size of buffer level', 'rocksdb.buffer-level-size')
if 'rate-limit' in report:
    draw('Rate limit', 'rate-limit')
if 'size-ratio' in report:
    draw('Size ratio', 'size-ratio')

def draw_num_sorted_runs(report, fname, yscale=None):
    fig = plt.figure(dpi = 300, figsize = (common.single_col_inch, 2), constrained_layout=True)
    ax = plt.gca()
    plt.plot(report['secs_elapsed'], report['num-sorted-runs'])
    plt.plot(report['secs_elapsed'], report['rocksdb.num-merging-main-level-sorted-runs'])
    if yscale is not None:
        plt.yscale(yscale)
    ax.set_ylim(bottom=1)
    plt.xlabel('Time (Seconds)')
    plt.ylabel('# of sorted runs')
    plt.legend(['Total', 'Merging'])
    pdf_path = os.path.join(plot_dir, fname)
    plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
    print('Plot saved to ' + pdf_path)
    if 'DISPLAY' in os.environ:
        plt.show(block=False)
draw_num_sorted_runs(report, 'num-sorted-runs.pdf')
draw_num_sorted_runs(report, 'num-sorted-runs-log.pdf', yscale='log')
if len(report) >= 200:
    mean_step = len(report) // 100
    draw_num_sorted_runs(report[['secs_elapsed', 'num-sorted-runs', 'rocksdb.num-merging-main-level-sorted-runs']].groupby(report.index // mean_step).mean(), 'num-sorted-runs-mean-every-1p.pdf')

fig = plt.figure(dpi = 300, figsize = (common.single_col_inch, 2), constrained_layout=True)
ax = plt.gca()
x = sorted(report['num-sorted-runs'])
plt.ylim(0, 4)
y = np.linspace(0, 1, num=len(x), endpoint=False)
y_log = -np.log10(1 - y)
plt.plot(x, y_log)
ticks = np.array([0, 0.5, 0.9, 0.99, 0.999, 0.9999])
ticks_log = -np.log10(1 - ticks)
plt.yticks(ticks_log, labels=ticks)
ax.grid(axis='y')
plt.xlabel('# of sorted runs')
plt.ylabel('CDF')
pdf_path = os.path.join(plot_dir, 'num-sorted-runs-cdf.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show(block=False)

fig = plt.figure(dpi = 300, figsize = (common.single_col_inch, 2), constrained_layout=True)
ax = plt.gca()
plt.plot(report['secs_elapsed'], report['num-flushes'] + report['num-compactions'])
if 'num-running-bg-jobs' in report:
    plt.plot(report['secs_elapsed'], report['num-running-bg-jobs'])
    plt.legend(['Total', 'Running'])
plt.xlabel('Time (Seconds)')
plt.ylabel('Num bg jobs')
ax.set_ylim(bottom=0)
pdf_path = os.path.join(plot_dir, 'num-bg-jobs.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show(block=False)

plt.figure(dpi = 300, figsize = (common.single_col_inch, 2), constrained_layout=True)
ax = plt.gca()
formatter = ScalarFormatter(useMathText=True)
formatter.set_powerlimits((-3, 4))
ax.yaxis.set_major_formatter(formatter)
data = report[report['Re'] != 0]
plt.plot(data['secs_elapsed'], data['Re'])
ax.set_ylim(bottom=0)
plt.xlabel('Time (Seconds)')
plt.ylabel('Re')
pdf_path = os.path.join(plot_dir, 'Re.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
