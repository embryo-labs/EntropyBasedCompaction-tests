#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
	print('Usage: ' + sys.argv[0] + ' dir')
	exit()
dir = sys.argv[1]

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

vec_write_MB_s = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
versions = []
for i in [5, 7, 10]:
    versions.append('leveling' + str(i))
for i in [2]:
    versions.append('tiering' + str(i))
versions.append('universal')
versions.append('benefit-cost')

percentiles_throughput = [10, 1, 0.1, 0.01]
percentile_names_throughput = ['10%', '1%', '0.1%', '0.01%']
assert len(percentile_names_throughput) == len(percentiles_throughput)
percentile_paths_throughput = ['p10', 'p1', 'p01', 'p001']
assert len(percentile_paths_throughput) == len(percentiles_throughput)

percentiles_sr = [90, 99, 99.9, 99.99]
percentile_names_sr = ['90%', '99%', '99.9%', '99.99%']
assert len(percentile_names_sr) == len(percentiles_sr)
percentile_paths_sr = ['p90', 'p99', 'p999', 'p9999']
assert len(percentile_paths_sr) == len(percentiles_sr)

throughput_avg = {}
throughput_percentiles = {}
for name in percentile_names_throughput:
    throughput_percentiles[name] = {}
num_sorted_runs_avg = {}
num_sorted_runs_percentiles = {}
for name in percentile_names_sr:
    num_sorted_runs_percentiles[name] = {}

for version in versions:
    throughput_avg[version] = []
    for name in percentile_names_throughput:
        throughput_percentiles[name][version] = []
    num_sorted_runs_avg[version] = []
    for name in percentile_names_sr:
        num_sorted_runs_percentiles[name][version] = []
    for write_MB_s in vec_write_MB_s:
        data_dir = os.path.join(dir, 'readwhilewriting-key-24-value-1000-unique-size-10GB-memtable-8MB-compaction-256MB-s-write-' + str(write_MB_s) + 'MB-s-threads-64-write-100GB-get-0.97-seek-0.03', version)
        stat_read = pd.DataFrame({'secs_elapsed': [], 'read-count': []})
        for op in ['get', 'seek']:
            stat = pd.read_csv(os.path.join(data_dir, op + '-count-time.csv'))
            stat = stat.iloc[len(stat) // 2:]
            stat_read = pd.merge_ordered(stat_read, stat[['secs_elapsed', 'count']], on='secs_elapsed', how='outer').fillna(0)
            stat_read['read-count'] += stat_read.pop('count')
        stat_read = stat_read.rename(columns={'read-count': 'count'})
        throughput_avg[version].append(stat_read['count'].mean())
        p = np.percentile(stat_read['count'], percentiles_throughput)
        assert len(p) == len(percentiles_throughput)
        for i in range(len(p)):
            throughput_percentiles[percentile_names_throughput[i]][version].append(p[i])

        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        report = report.iloc[len(report) // 2:]
        num_sorted_runs_avg[version].append(report['num-sorted-runs'].mean())
        p = np.percentile(report['num-sorted-runs'], percentiles_sr)
        assert len(p) == len(percentiles_sr)
        for i in range(len(p)):
            num_sorted_runs_percentiles[percentile_names_sr[i]][version].append(p[i])

def draw1(data, ylabel):
    fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
    ax = plt.gca()
    plt.xlabel('Write (MB/s)', fontsize=8)
    plt.ylabel(ylabel, fontsize=8)
    plt.xticks(vec_write_MB_s, fontsize=8)
    plt.yticks(fontsize=8)
    for version in versions:
        plt.plot(vec_write_MB_s, data[version])

def draw2(filename):
    plt.legend(versions, fontsize=8)
    pdf_path = os.path.join(dir, filename)
    plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
    print('Plot saved to ' + pdf_path)

def draw_throughput(data, ylabel, filename):
    draw1(data, ylabel)
    draw2(filename)

def draw_num_sorted_runs(data, ylabel, filename):
    draw1(data, ylabel)
    plt.yscale('log')
    plt.ylim(1, 100)
    draw2(filename)

draw_throughput(throughput_avg, 'Throughput (average)', 'readwhilewriting-throughput-average.pdf')
for i in range(len(percentiles_throughput)):
    draw_throughput(throughput_percentiles[percentile_names_throughput[i]], 'Throughput (' + percentile_names_throughput[i] + ')', 'readwhilewriting-throughput-' + percentile_paths_throughput[i] + '.pdf')

draw_num_sorted_runs(num_sorted_runs_avg, '# of sorted runs (average)', 'readwhilewriting-num-sorted-runs-average.pdf')
for i in range(len(percentiles_sr)):
    draw_num_sorted_runs(num_sorted_runs_percentiles[percentile_names_sr[i]], '# of sorted runs (' + percentile_names_sr[i] + ')', 'readwhilewriting-num-sorted-runs-' + percentile_paths_sr[i] + '.pdf')
