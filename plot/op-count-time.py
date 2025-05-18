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
		'path': 'read',
		'name': 'Reads',
	}
]
for op in operations:
	stat = os.path.join(data_dir, op['path'] + '-count-time.csv')
	if not os.path.exists(stat):
		continue
	stat = pd.read_csv(stat)

	fig = plt.figure(dpi = 300, figsize = (cm_to_inch(SINGLE_COL_WIDTH), cm_to_inch(5)), constrained_layout=True)
	ax = plt.gca()
	formatter = ScalarFormatter(useMathText=True)
	formatter.set_powerlimits((-3, 4))
	ax.yaxis.set_major_formatter(formatter)
	ax.yaxis.get_offset_text().set_fontsize(8)
	plt.plot(stat['secs_elapsed'], stat['count'], linewidth=0.5)
	plt.xticks(fontsize=8)
	plt.yticks(fontsize=8)
	ax.set_ylim(bottom=0)
	plt.xlabel('Time (Seconds)', fontsize=8)
	plt.ylabel(op['name'] + ' per second', fontsize=8)
	pdf_path = os.path.join(plot_dir, op['path'] + '-per-second.pdf')
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
	pdf_path = os.path.join(plot_dir, op['path'] + '-avg-latency.pdf')
	plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0.01)
	print('Plot saved to ' + pdf_path)
