#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
    print('usage: ' + sys.argv[0] + ' data-dir')
    exit(1)
data_dir = sys.argv[1]

import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Linux Libertine O'],
})
plt.rcParams['axes.unicode_minus'] = False

SINGLE_COL_WIDTH = 8.5
def cm_to_inch(value):
    return value/2.54
fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)

import os
import json
data = json.load(open(os.path.join(data_dir, 'read-preempt-write.json')))
x = []
y = []
for a in data:
    expected_write_MB_s = a['expected-write(MB/s)']
    x.append(expected_write_MB_s)
    results = a['results']
    read_latency_sum = 0
    for result in results:
        write_MB_s = result['write(MB/s)']
        if write_MB_s < expected_write_MB_s * 0.99 or write_MB_s > expected_write_MB_s * 1.01:
            print('Warning: expected write throughput: ' + str(expected_write_MB_s) + ' MB/s, got ' + str(write_MB_s) + ' MB/s')
        read_latency_sum += result['avg-read-latency(ns)']
    y.append(read_latency_sum / len(results) / 1000)

ax = plt.gca()
plt.plot(x, y, linewidth=0.5)
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)
ax.set_ylim(bottom=0)
plt.xlabel('Write (MB/s)', fontsize=8)
plt.ylabel('Read latency (us)', fontsize=8)

pdf_path = os.path.join(data_dir, 'read-preempt-write.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
	plt.show()
