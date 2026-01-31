#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
    print('Usage: ' + sys.argv[0] + ' data-dir')
    exit()
data_dir = sys.argv[1]

import os
import json
import matplotlib as mpl
import matplotlib.pyplot as plt

import common

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 9,
})

plot_dir = data_dir + '/plot'
if not os.path.exists(plot_dir):
    os.system('mkdir -p ' + plot_dir)

time = []
reff = []
ts_begin_ns = None
for line in open(os.path.join(data_dir, 'log.json')):
    entry = json.loads(line)
    if entry['event'] == 'new-benchmark':
        if ts_begin_ns is None:
            if entry['name'] == 'readwhilewriting':
                ts_begin_ns = entry['timestamp(ns)']
        continue
    if ts_begin_ns is None:
        continue
    if entry['event'] in ['new-compaction', 'resume-compaction']:
        time.append((entry['timestamp(ns)'] - ts_begin_ns) / 1e9)
        reff.append(entry['R_eff'])

plt.figure(dpi = 300, figsize = (common.single_col_inch, 2), constrained_layout=True)
ax = plt.gca()
plt.plot(time, reff)
ax.set_ylim(bottom=0)
plt.xlabel('Time (Seconds)')
plt.ylabel('R_eff')
pdf_path = os.path.join(plot_dir, 'Re-from-log.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
