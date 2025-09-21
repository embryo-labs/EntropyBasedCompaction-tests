#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
	print('Usage: ' + sys.argv[0] + ' dir')
	exit()
dir = sys.argv[1]
from_MB_s = 10
to_MB_s = 100

import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

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

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
ax = plt.gca()
plt.xlabel('Write (MB/s)', fontsize=8)
plt.ylabel('# of sorted runs')
plt.xticks(np.linspace(from_MB_s, to_MB_s, 10), fontsize=8)
plt.yticks(fontsize=8)

def add(version):
    data_dir = os.path.join(dir, version)
    data = pd.read_csv(os.path.join(data_dir, 'report.csv'))
    max_secs_elapsed = data.iloc[-1]['secs_elapsed']
    data['write-speed'] = data['secs_elapsed'] / max_secs_elapsed * (to_MB_s - from_MB_s) + from_MB_s
    mean_step = len(data['write-speed']) / 100
    data = data[['write-speed', 'num-sorted-runs']].groupby(data.index // mean_step).mean()
    plt.plot(data['write-speed'], data['num-sorted-runs'])

versions = []
for ratio in [5, 10]:
    version = 'leveling' + str(ratio)
    add(version)
    versions.append(version)
for ratio in [2, 10]:
    version = 'tiering' + str(ratio)
    add(version)
    versions.append(version)
for version in ['rocksdb-tuned', 'universal', 'benefit-cost']:
    add(version)
    versions.append(version)

plt.yscale('log')
plt.xlim((from_MB_s, to_MB_s))
ax.set_ylim(bottom=1, top=100)
plt.legend(versions, fontsize=8)

pdf_path = os.path.join(dir, 'increasing-write-speed-num-sorted-runs-avg-every-1p.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
