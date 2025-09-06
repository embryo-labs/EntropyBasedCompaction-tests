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

plot_dir = data_dir + '/plot'
if not os.path.exists(plot_dir):
    os.system('mkdir -p ' + plot_dir)

report = pd.read_table(os.path.join(data_dir, 'report.csv'), sep=',')
# It seems that the ops of the first several seconds is not limited.
report = report.iloc[20:]

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
ax = plt.gca()
formatter = ScalarFormatter(useMathText=True)
formatter.set_powerlimits((-3, 4))
ax.yaxis.set_major_formatter(formatter)
ax.yaxis.get_offset_text().set_fontsize(8)
plt.plot(report['secs_elapsed'], report['interval_qps'], linewidth=0.5)
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)
ax.set_ylim(bottom=0)
plt.xlabel('Time (Seconds)', fontsize=8)
plt.ylabel('Operation per second', fontsize=8)
pdf_path = plot_dir + '/ops.pdf'
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show(block=False)

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
ax = plt.gca()
plt.plot(report['secs_elapsed'], report['wait-for-last-level-compaction'])
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)
ax.set_ylim(bottom=0)
plt.xlabel('Time (Seconds)', fontsize=8)
plt.ylabel('Number of wait for LLC', fontsize=8)
pdf_path = os.path.join(plot_dir, 'wait-for-last-level-compaction.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show(block=False)

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
ax = plt.gca()
plt.plot(report['secs_elapsed'], report['num-sorted-runs'] - report['rocksdb.num-top-level-sorted-runs'])
plt.plot(report['secs_elapsed'], report['rocksdb.num-merging-main-level-sorted-runs'])
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)
ax.set_ylim(bottom=0)
plt.xlabel('Time (Seconds)', fontsize=8)
plt.ylabel('# of sorted runs', fontsize=8)
plt.legend(['Total', 'Merging'], fontsize=8)
pdf_path = os.path.join(plot_dir, 'num-sorted-runs-main-level.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show(block=False)

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
ax = plt.gca()
x = sorted(report['num-sorted-runs'])
plt.ylim(0, 4)
y = np.linspace(0, 1, num=len(x), endpoint=False)
y_log = -np.log10(1 - y)
plt.plot(x, y_log)
ticks = np.array([0, 0.5, 0.9, 0.99, 0.999, 0.9999])
ticks_log = -np.log10(1 - ticks)
plt.yticks(ticks_log, labels=ticks, fontsize=8)
ax.grid(axis='y')
plt.xlabel('# of sorted runs', fontsize=8)
plt.ylabel('CDF', fontsize=8)
pdf_path = os.path.join(plot_dir, 'num-sorted-runs-cdf.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show(block=False)

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
ax = plt.gca()
plt.plot(report['secs_elapsed'], report['num-flushes'] + report['num-compactions'])
if 'num-running-bg-jobs' in report:
    plt.plot(report['secs_elapsed'], report['num-running-bg-jobs'])
    plt.legend(['Total', 'Running'], fontsize=8)
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)
plt.xlabel('Time (Seconds)', fontsize=8)
plt.ylabel('Num bg jobs', fontsize=8)
ax.set_ylim(bottom=0)
pdf_path = os.path.join(plot_dir, 'num-bg-jobs.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show(block=False)

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
ax = plt.gca()
plt.plot(report['secs_elapsed'], report['rocksdb.buffer-level-size'])
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)
ax.set_ylim(bottom=0)
plt.xlabel('Time (Seconds)', fontsize=8)
plt.ylabel('Size of buffer level', fontsize=8)
pdf_path = os.path.join(plot_dir, 'buffer-level-size.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show()

if 'rate-limit' in report:
    fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
    ax = plt.gca()
    formatter = ScalarFormatter(useMathText=True)
    formatter.set_powerlimits((-3, 4))
    ax.yaxis.set_major_formatter(formatter)
    ax.yaxis.get_offset_text().set_fontsize(8)
    plt.plot(report['secs_elapsed'], report['rate-limit'])
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    ax.set_ylim(bottom=0)
    plt.xlabel('Time (Seconds)', fontsize=8)
    plt.ylabel('Rate limit', fontsize=8)
    pdf_path = os.path.join(plot_dir, 'rate-limit.pdf')
    plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
    print('Plot saved to ' + pdf_path)

if 'size-ratio' in report:
    fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
    ax = plt.gca()
    plt.plot(report['secs_elapsed'], report['size-ratio'])
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    ax.set_ylim(bottom=0)
    plt.xlabel('Time (Seconds)', fontsize=8)
    plt.ylabel('Size ratio', fontsize=8)
    pdf_path = os.path.join(plot_dir, 'size-ratio.pdf')
    plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
    print('Plot saved to ' + pdf_path)
