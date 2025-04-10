#!/usr/bin/env python3
import sys
if len(sys.argv) != 4:
    print('Usage: ' + sys.argv[0] + ' dir prefix pdf-path')
    exit(1)
dir = sys.argv[1]
prefix = sys.argv[2]
pdf_path = sys.argv[3]

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
    'font.family': 'sans-serif',
    'font.sans-serif': ['Linux Libertine O'],
})
plt.rcParams['axes.unicode_minus'] = False

x = []
avg = []
P99 = []
P999 = []
import os
for seek in range(1000, 20000 + 1, 1000):
    data_dir = os.path.join(dir, prefix + str(seek), 'leveling')
    data_dir = os.path.join(dir, prefix + str(seek), 'leveling')
    stdout = open(os.path.join(data_dir, 'stdout.txt'))
    while stdout.readline() != 'Microseconds per seek:\n':
        pass
    while stdout.readline() != 'Microseconds per seek:\n':
        pass
    x.append(seek)

    a = stdout.readline().split(' ')
    assert a[2] == 'Average:'
    avg.append(float(a[3]))

    stdout.readline()

    a = stdout.readline().split(' ')
    assert a[5] == 'P99:'
    P99.append(float(a[6]))
    assert a[7] == 'P99.9:'
    P999.append(float(a[8]))

fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
plt.plot(x, avg, linewidth=0.5)
plt.plot(x, P99, linewidth=0.5)
plt.plot(x, P999, linewidth=0.5)
plt.legend(['Avg', '99%', '99.9%'], fontsize=9)
plt.xlabel('Seek per second', fontsize=9)
plt.ylabel('Latency (us)', fontsize=9)
plt.yscale('log')
plt.savefig(pdf_path)
if 'DISPLAY' in os.environ:
	plt.show()
