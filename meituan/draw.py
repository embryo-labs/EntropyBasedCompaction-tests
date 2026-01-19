#!/usr/bin/env python3
import sys
assert len(sys.argv) > 0
import os

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec
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

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(4)), constrained_layout=True)
gs = gridspec.GridSpec(1, 2, figure=fig)

peak_day_index = 35
normal_day_index = 51

plt.subplot(gs[0, 0])
ax = plt.gca()
formatter = ScalarFormatter(useMathText=True)
formatter.set_powerlimits((-3, 4))
ax.yaxis.set_major_formatter(formatter)
ax.yaxis.get_offset_text().set_fontsize(9)
plt.xlabel('Days', fontsize=9, labelpad=1)
plt.text(0.5, -0.45, '(a) Over 3 months', fontsize=9, transform=ax.transAxes, ha="center", va="center")
plt.ylabel('# of writes per day', fontsize=9)
num_writes_per_day = pd.read_csv(os.path.join(os.path.dirname(sys.argv[0]), 'num-writes-per-day'), header=None).iloc[:,0]
plt.plot(num_writes_per_day, linewidth=1)
plt.xticks([0, 30, 60, 90], fontsize=9)
plt.ylim((0, 1.5e10))
plt.yticks(fontsize=9)
ax.grid(axis='y')
plt.scatter(peak_day_index, num_writes_per_day[peak_day_index], marker='o', s=10, color='C0')
plt.text(peak_day_index + 5, num_writes_per_day[peak_day_index], 'Peak day', fontsize=9)
plt.scatter(normal_day_index, num_writes_per_day[normal_day_index], marker='s', s=8, color='C0')
plt.annotate('Normal day', fontsize=9, xy=(normal_day_index, num_writes_per_day[normal_day_index]), xytext=(0.3, 0.1), textcoords='axes fraction', arrowprops=dict(arrowstyle="->", shrinkA=0))

num_marks = 5
markersize = 3

plt.subplot(gs[0, 1])
ax = plt.gca()
formatter = ScalarFormatter(useMathText=True)
formatter.set_powerlimits((-3, 4))
ax.yaxis.set_major_formatter(formatter)
ax.yaxis.get_offset_text().set_fontsize(9)
plt.xlabel('Hours', fontsize=9, labelpad=1)
plt.text(0.5, -0.45, '(b) In a day', fontsize=9, transform=ax.transAxes, ha="center", va="center")
plt.ylabel('# of writes per second', fontsize=9)

write_speed_peak_day = pd.read_csv(os.path.join(os.path.dirname(sys.argv[0]), 'write-speed-peak-day'), header=None).iloc[:,0]
n = len(write_speed_peak_day)
assert n % 24 == 0
assert round(write_speed_peak_day.sum() * (24 * 60 * 60 / n)) == num_writes_per_day[peak_day_index]
markevery = n // num_marks
plt.plot(write_speed_peak_day, linewidth=1, marker='o', markevery=markevery, markersize=markersize)

write_speed_normal_day = pd.read_csv(os.path.join(os.path.dirname(sys.argv[0]), 'write-speed-normal-day'), header=None).iloc[:,0]
assert len(write_speed_normal_day) == n
assert round(write_speed_normal_day.sum() * (24 * 60 * 60 / n)) == num_writes_per_day[normal_day_index]
plt.plot(write_speed_normal_day, linewidth=1, marker='s', markevery=markevery, markersize=markersize)
hours = np.arange(0, 25, 4)
plt.xticks(hours * n / 24, hours, fontsize=9)
plt.ylim((0, 4e5))
plt.yticks([0, 1e5, 2e5, 3e5, 4e5], fontsize=9)
ax.grid(axis='y')
plt.legend(['Peak day', 'Normal day'], fontsize=8, frameon=False, loc='upper right', bbox_to_anchor=(1.07, 1.08), labelspacing=0)

pdf_path = 'meituan-num-writes.pdf'
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
