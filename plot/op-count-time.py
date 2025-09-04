#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
	print('Usage: ' + sys.argv[0] + ' data-dir')
	exit()
data_dir = sys.argv[1]

import os
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

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

plot_dir = data_dir + '/plot'
if not os.path.exists(plot_dir):
	os.system('mkdir -p ' + plot_dir)

operations = [
	{
		'path': 'write',
		'name': 'Writes',
	},
	{
		'path': 'seek',
		'name': 'Seeks',
	},
	{
		'path': 'get',
		'name': 'Gets',
	}
]
read_operations = ['get', 'seek']

def draw(stat, op_path, op_name):
	# Drop the first 1% because it is usually abnormal
	stat = stat.iloc[len(stat) // 100:]

	if (len(stat) >= 1000):
		mean_step = len(stat) // 1000
	else:
		mean_step = 1
	throughput = stat[['secs_elapsed', 'count']].groupby(stat.index // mean_step).mean()

	fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
	ax = plt.gca()
	formatter = ScalarFormatter(useMathText=True)
	formatter.set_powerlimits((-3, 4))
	ax.yaxis.set_major_formatter(formatter)
	ax.yaxis.get_offset_text().set_fontsize(8)
	plt.plot(throughput['secs_elapsed'], throughput['count'], linewidth=0.5)
	plt.xticks(fontsize=8)
	plt.yticks(fontsize=8)
	ax.set_ylim(bottom=0)
	plt.xlabel('Time (Seconds)', fontsize=8)
	plt.ylabel(op_path + ' per second', fontsize=8)
	pdf_path = os.path.join(plot_dir, op_path + '-per-second.pdf')
	plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
	print('Plot saved to ' + pdf_path)

	fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
	ax = plt.gca()
	plt.plot(stat['secs_elapsed'], stat['micros'] / stat['count'], linewidth=0.5)
	plt.xticks(fontsize=8)
	plt.yticks(fontsize=8)
	ax.set_ylim(bottom=0)
	plt.xlabel('Time (Seconds)', fontsize=8)
	plt.ylabel('Average latency (us)', fontsize=8)
	pdf_path = os.path.join(plot_dir, op_path + '-avg-latency.pdf')
	plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
	print('Plot saved to ' + pdf_path)

num_read_types = 0
stat_read = pd.DataFrame({'secs_elapsed': [], 'read-count': [], 'read-micros': []})
for op in operations:
	stat = os.path.join(data_dir, op['path'] + '-count-time.csv')
	if not os.path.exists(stat):
		continue
	stat = pd.read_csv(stat)
	if op['path'] in read_operations:
		num_read_types += 1
		stat_read = pd.merge_ordered(stat_read, stat, on='secs_elapsed', how='outer').fillna(0)
		stat_read['read-count'] += stat_read.pop('count')
		stat_read['read-micros'] += stat_read.pop('micros')

	draw(stat, op['path'], op['name'])

stat_read = stat_read.rename(columns={'read-count': 'count', 'read-micros': 'micros'})

if num_read_types > 1:
	draw(stat_read, 'read', 'Read')
