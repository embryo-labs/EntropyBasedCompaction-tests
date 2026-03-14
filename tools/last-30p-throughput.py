#!/usr/bin/env python3
import pandas as pd
iostat = pd.read_table('iostat.txt', sep=r'\s+')
print('Write throughput:', iostat.iloc[-len(iostat)*3//10:]['wkB/s'].mean() / 1000, 'MB/s')
