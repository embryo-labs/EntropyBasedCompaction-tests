#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
    print('usage: ' + sys.argv[0] + ' file')
    exit(1)
file = sys.argv[1]

import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'serif',
    'font.serif': ['Linux Libertine O'],
})
plt.rcParams['axes.unicode_minus'] = False

SINGLE_COL_WIDTH = 8.5
def cm_to_inch(value):
    return value/2.54

import os
import json
import humanfriendly
data = json.load(open(file))

def draw(type):
    fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
    x = []
    y = []
    for a in data:
        expected_MiB_s = a['expected(MiB/s)']
        x.append(expected_MiB_s)
        results = a['results']
        read_latency_us_sum = 0
        for result in results:
            assert result['real'].endswith('/s')
            real_MiB_s = humanfriendly.parse_size(result['real'].removesuffix('/s')) / 1024 / 1024
            if real_MiB_s < expected_MiB_s * 0.99 or real_MiB_s > expected_MiB_s * 1.01:
                print('Warning: expected throughput: ' + str(expected_MiB_s) + ' MiB/s, got ' + str(real_MiB_s) + ' MiB/s')
            read_latency_us_sum += result['read-latency-' + type + '(us)']
        y.append(read_latency_us_sum / len(results))

    ax = plt.gca()
    plt.plot(x, y, linewidth=0.5)
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    ax.set_ylim(bottom=0)
    plt.xlabel('Compaction (MiB/s)', fontsize=8)
    plt.ylabel(type + ' latency (us)', fontsize=8)

    pdf_path = os.path.splitext(file)[0] + '-' + type + '.pdf'
    plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
    print('Plot saved to ' + pdf_path)

draw('avg')
draw('99%')
draw('99.9%')
draw('99.99%')
