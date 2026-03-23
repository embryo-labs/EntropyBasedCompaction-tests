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
    'font.family': 'serif',
    'font.serif': ['Linux Libertine O'],
})
plt.rcParams['axes.unicode_minus'] = False

plot_dir = data_dir + '/plot'
if not os.path.exists(plot_dir):
	os.system('mkdir -p ' + plot_dir)

def draw(op_path):
	stat = os.path.join(data_dir, op + '-count-time.csv')
	if not os.path.exists(stat):
		return
	stat = pd.read_csv(stat)
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
	ax.grid(axis='y')
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
	ax.grid(axis='y')
	plt.xlabel('Time (Seconds)', fontsize=8)
	plt.ylabel('Average latency (us)', fontsize=8)
	pdf_path = os.path.join(plot_dir, op_path + '-avg-latency.pdf')
	plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
	print('Plot saved to ' + pdf_path)

	fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
	ax = plt.gca()
	plt.plot(stat['secs_elapsed'], stat['micros'] / stat['count'], linewidth=0.5)
	plt.xticks(fontsize=8)
	plt.yticks(fontsize=8)
	plt.yscale('log')
	ax.grid(axis='y')
	plt.xlabel('Time (Seconds)', fontsize=8)
	plt.ylabel('Average latency (us)', fontsize=8)
	pdf_path = os.path.join(plot_dir, op_path + '-avg-latency-log.pdf')
	plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
	print('Plot saved to ' + pdf_path)

for op in ['write', 'seek', 'get', 'prefix-scan', 'read']:
	draw(op)
