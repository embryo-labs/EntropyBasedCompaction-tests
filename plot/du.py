#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
	print('Usage: ' + sys.argv[0] + ' dir')
	exit()
d = sys.argv[1]

import os
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

fontsize=9
fonten = {'family': 'Linux Libertine O', 'size': fontsize}

mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Linux Libertine O'],
    })  # 设置全局字体
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

du = pd.read_table(os.path.join(d, 'du.sh.txt'), sep='\s+')
time = (du['Timestamp(ns)'] - du['Timestamp(ns)'][0]) / 1e9

plot_dir = os.path.join(d, 'plot')
if not os.path.exists(plot_dir):
	os.system('mkdir -p ' + plot_dir)
pdf_path = os.path.join(plot_dir, 'du.pdf')
plt.plot(time, du['size'])
plt.xlabel('Time (Seconds)', fontdict=fonten)
plt.ylabel('Size (Bytes)', fontdict=fonten)
plt.title('Disk usage')
plt.savefig(pdf_path, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)
if 'DISPLAY' in os.environ:
	plt.show()
