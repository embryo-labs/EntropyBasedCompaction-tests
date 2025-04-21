#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
    print('Usage: ' + sys.argv[0] + ' dir')
    exit()
dir = sys.argv[1]

import os
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

benchmarks = [
    {
        'path': 'seekrandom',
        'run-phase-op': 'seek',
    },
    {
        'path': 'readrandom',
        'run-phase-op': 'read',
    },
    {
        'path': 'mergerandom-readrandom',
        'run-phase-op': 'read',
    },
]

for benchmark in benchmarks:
    x = []
    avg_v = []
    p99_v = []
    p999_v = []
    p9999_v = []
    for num in range(1, 100):
        x.append(num)
        data_dir = os.path.join(dir, benchmark['path'] + '-sorted-runs-' + str(num) + '-threads-16', 'leveling')
        stdout = open(os.path.join(data_dir, 'stdout.txt'))
        for line in stdout:
            if line.strip() == 'Microseconds per ' + benchmark['run-phase-op'] + ':':
                break
        s = stdout.readline().split(' ')
        assert s[2] == 'Average:'
        avg_v.append(float(s[3]))
        stdout.readline()
        s = stdout.readline().split(' ')
        assert s[5] == 'P99:'
        p99_v.append(float(s[6]))
        assert s[7] == 'P99.9:'
        p999_v.append(float(s[8]))
        assert s[9] == 'P99.99:'
        p9999_v.append(float(s[10]))
    fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
    ax = plt.gca()
    plt.plot(x, avg_v, linewidth=0.5)
    plt.plot(x, p99_v, linewidth=0.5)
    plt.plot(x, p999_v, linewidth=0.5)
    plt.plot(x, p9999_v, linewidth=0.5)
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=8)
    plt.xlabel('# of sorted runs', fontsize=8)
    plt.ylabel('Latency (us)', fontsize=8)
    plt.legend(['Average', '99%', '99.9%', '99.99%'], fontsize=8)
    pdf_path = os.path.join(dir, 'num-sorted-runs-' + benchmark['path'] + '-latency.pdf')
    plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
    print('Plot saved to ' + pdf_path)
    if 'DISPLAY' in os.environ:
        plt.show(block=False)

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
ax = plt.gca()
for benchmark in benchmarks:
    x = []
    y = []
    for num in range(1, 100):
        x.append(num)
        data_dir = os.path.join(dir, benchmark['path'] + '-sorted-runs-' + str(num) + '-threads-16', 'leveling')
        report = os.path.join(data_dir, 'report.csv')
        report = pd.read_csv(report)
        y.append(report['interval_qps'].sum() / report.iloc[-1]['secs_elapsed'])
    plt.plot(x, y, linewidth=0.5)
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)
ax.set_ylim(bottom=0)
plt.xlabel('# of sorted runs', fontsize=8)
plt.ylabel('Operation per second', fontsize=8)
plt.legend(['Seek', 'Read', 'Merge-Read'], fontsize=8)
pdf_path = os.path.join(dir, 'num-sorted-runs-throughput.pdf')
plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
    plt.show()
