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
import humanfriendly
data = json.load(open(os.path.join(data_dir, 'avg-read-latency-during-read.json')))
x = []
y = []
for a in data:
    expected_MiB_s = a['expected(MiB/s)']
    x.append(expected_MiB_s)
    results = a['results']
    read_latency_us_sum = 0
    for result in results:
        assert result['read'].endswith('/s')
        read_MiB_s = humanfriendly.parse_size(result['read'].removesuffix('/s')) / 1024 / 1024
        if read_MiB_s < expected_MiB_s * 0.99 or read_MiB_s > expected_MiB_s * 1.01:
            print('Warning: expected throughput: ' + str(expected_MiB_s) + ' MiB/s, got ' + str(read_MiB_s) + ' MiB/s')
        read_latency_us_sum += result['read-latency(us)']
    y.append(read_latency_us_sum / len(results))

ax = plt.gca()
plt.plot(x, y, linewidth=0.5)
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)
ax.set_ylim(bottom=0)
plt.xlabel('Sequential read (MiB/s)', fontsize=8)
plt.ylabel('Read latency (us)', fontsize=8)

pdf_path = os.path.join(data_dir, 'avg-read-latency-during-read.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
	plt.show()
