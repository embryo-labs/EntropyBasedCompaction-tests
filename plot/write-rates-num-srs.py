#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
	print('Usage: ' + sys.argv[0] + ' dir')
	exit()
dir = sys.argv[1]

import os
import math
import numpy as np
import pandas as pd
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

vec_write_MB_s = [10, 20, 30, 40, 50, 60]

versions = ['rocksdb-tuned', 'tiering2', 'tiering4', 'tiering8', 'universal', 'benefit-cost']

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
gs = gridspec.GridSpec(1, 2, figure=fig)
plt.subplot(gs[0, 0])
ax_avg = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('Average # of sorted runs', fontsize=9)
plt.ylim((0, 100))
plt.yticks(fontsize=9)

plt.subplot(gs[0, 1])
ax_p99 = plt.gca()
plt.xlabel('Write rates (MB/s)', fontsize=9)
plt.xticks(vec_write_MB_s, fontsize=9)
plt.ylabel('P99 # of sorted runs', fontsize=9)
plt.ylim((0, 100))
plt.yticks(fontsize=9)

for version in versions:
    avg = []
    p99 = []
    for write_MB_s in vec_write_MB_s:
        workload = 'overwrite-key-16-value-1000-unique-size-10GB-memtable-8MiB-'
        if version in ['tiering2', 'tiering4', 'tiering8', 'benefit-cost']:
            workload += 'max-running-bg-jobs-1-'
        workload += 'compaction-200MB-s-write-' + str(write_MB_s) + 'MB-s-write-100GB'
        data_dir = os.path.join(dir, workload, version)
        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        # Use the last 30%
        report = report.iloc[-math.ceil(len(report) * 0.3):]
        avg.append(report['num-sorted-runs'].mean())
        p99.append(np.percentile(report['num-sorted-runs'], 99))
    ax_avg.plot(vec_write_MB_s, avg)
    ax_p99.plot(vec_write_MB_s, p99)

fig.legend(versions, fontsize=9, ncol=3, loc='center', bbox_to_anchor=(0.5, 1.1))
pdf_path = os.path.join(dir, 'write-rates-num-srs.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
