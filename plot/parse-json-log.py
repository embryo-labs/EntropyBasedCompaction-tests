#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
    print('Usage: ' + sys.argv[0] + ' data-dir')
    exit()
data_dir = sys.argv[1]

import math
import os
import json
import matplotlib as mpl
import matplotlib.pyplot as plt

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

time_new_compaction = []
reff_new_compaction = []
time_resume_compaction = []
reff_resume_compaction = []
time = []
reff = []

ts_begin_ns = None
for line in open(os.path.join(data_dir, 'log.json')):
    entry = json.loads(line)
    if entry['event'] == 'new-benchmark':
        if ts_begin_ns is None:
            if entry['name'] in ['customperiodic', 'readrandomwriterandom', 'readwhilewriting']:
                ts_begin_ns = entry['timestamp(ns)']
        continue
    if ts_begin_ns is None:
        continue
    if entry['event'] == 'new-compaction':
        time_new_compaction.append((entry['timestamp(ns)'] - ts_begin_ns) / 1e9)
        reff_new_compaction.append(entry['R_eff'])
    if entry['event'] == 'resume-compaction':
        time_resume_compaction.append((entry['timestamp(ns)'] - ts_begin_ns) / 1e9)
        reff_resume_compaction.append(entry['R_eff'])
    if entry['event'] in ['new-compaction', 'resume-compaction']:
        time.append((entry['timestamp(ns)'] - ts_begin_ns) / 1e9)
        reff.append(entry['R_eff'])

ylim = (0, math.ceil(max(reff)))

plt.figure(dpi = 300, figsize = (common.single_col_inch, 2), constrained_layout=True)
plt.xlabel('Time (Seconds)')
plt.ylabel('R_eff')
plt.ylim(ylim)
plt.scatter(time_new_compaction, reff_new_compaction, 0.1)
pdf_path = os.path.join(plot_dir, 'Re-new-compaction.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)


plt.figure(dpi = 300, figsize = (common.single_col_inch, 2), constrained_layout=True)
plt.xlabel('Time (Seconds)')
plt.ylabel('R_eff')
plt.ylim(ylim)
plt.scatter(time_resume_compaction, reff_resume_compaction, 0.1)
pdf_path = os.path.join(plot_dir, 'Re-resume-compaction.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)

plt.figure(dpi = 300, figsize = (common.single_col_inch, 2), constrained_layout=True)
plt.xlabel('Time (Seconds)')
plt.ylabel('R_eff')
plt.ylim(ylim)
plt.scatter(time, reff, 0.1)
pdf_path = os.path.join(plot_dir, 'Re-from-log.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
