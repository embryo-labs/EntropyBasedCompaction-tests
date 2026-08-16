#!/usr/bin/env python3
import sys
if len(sys.argv) != 1:
    print('No argument expected')
    exit(1)
import os
data_dir = os.path.join(os.path.dirname(sys.argv[0]), '..', 'meituan')

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.ticker import ScalarFormatter

import common

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'serif',
    'font.serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 9,
})

fig = plt.figure(dpi = 300, figsize = (common.single_col_inch, 1.5), constrained_layout=True)
fig.get_layout_engine().set(
    h_pad=0.01,
    w_pad=0.01,
    rect=(0, 0, 1, 1),
)
gs = gridspec.GridSpec(1, 2, figure=fig)

peak_day_index = 35
normal_day_index = 51

plt.subplot(gs[0, 0])
ax = plt.gca()
formatter = ScalarFormatter(useMathText=True)
formatter.set_powerlimits((-3, 4))
ax.yaxis.set_major_formatter(formatter)
plt.xlabel('Days\n(a) Over 3 months', labelpad=1)
plt.ylabel('# of writes per day', loc='top')
num_writes_per_day = pd.read_csv(os.path.join(data_dir, 'num-writes-per-day'), header=None).iloc[:,0]
plt.plot(num_writes_per_day, linewidth=1)
plt.xticks([0, 30, 60, 90])
plt.ylim((0, 1.5e10))
ax.grid(axis='y')
plt.scatter(peak_day_index, num_writes_per_day[peak_day_index], marker='o', s=10, color='C0')
plt.text(peak_day_index + 5, num_writes_per_day[peak_day_index], 'Peak day')
plt.scatter(normal_day_index, num_writes_per_day[normal_day_index], marker='s', s=8, color='C0')
plt.annotate('Normal day', xy=(normal_day_index, num_writes_per_day[normal_day_index]), xytext=(0.3, 0.1), textcoords='axes fraction', arrowprops=dict(arrowstyle="->", shrinkA=0))

num_marks = 5
markersize = 3

ax = plt.subplot(gs[0, 1])
formatter = ScalarFormatter(useMathText=True)
formatter.set_powerlimits((-3, 4))
ax.yaxis.set_major_formatter(formatter)
plt.xlabel('Hours\n(b) In a day', labelpad=1)
plt.ylabel('# of writes per second', loc='top')

write_speed_peak_day = pd.read_csv(os.path.join(data_dir, 'write-speed-peak-day'), header=None).iloc[:,0]
n = len(write_speed_peak_day)
assert n % 24 == 0
assert round(write_speed_peak_day.sum() * (24 * 60 * 60 / n)) == num_writes_per_day[peak_day_index]
markevery = n // num_marks
plt.plot(write_speed_peak_day, linewidth=1, marker='o', markevery=markevery, markersize=markersize)

write_speed_normal_day = pd.read_csv(os.path.join(data_dir, 'write-speed-normal-day'), header=None).iloc[:,0]
assert len(write_speed_normal_day) == n
assert round(write_speed_normal_day.sum() * (24 * 60 * 60 / n)) == num_writes_per_day[normal_day_index]
plt.plot(write_speed_normal_day, linewidth=1, marker='s', markevery=markevery, markersize=markersize)
hours = np.arange(0, 25, 4)
plt.xticks(hours * n / 24, hours)
plt.ylim((0, 4e5))
plt.yticks([0, 1e5, 2e5, 3e5, 4e5])
ax.grid(axis='y')
plt.legend(
    ['Peak day', 'Normal day'],
    fontsize=8,
    frameon=False,
    loc='upper right',
    bbox_to_anchor=(1.04, 1.06),
    labelspacing=0,
    borderpad=0,
)

pdf_path = 'meituan-num-writes.pdf'
plt.savefig(pdf_path, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
