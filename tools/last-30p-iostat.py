#!/usr/bin/env python3
import pandas as pd
iostat = pd.read_table('iostat.txt', sep=r'\s+')
iostat = iostat.iloc[-len(iostat)*3//10:]
print('r/s:', iostat['r/s'].mean())
print('Read throughput:', iostat['rkB/s'].mean() / 1000, 'MB/s')
print('Write throughput:', iostat['wkB/s'].mean() / 1000, 'MB/s')
print('Read await:', iostat['r_await'].mean(), 'ms')
print('Write await:', iostat['w_await'].mean(), 'ms')
print('Average queue depth:', iostat['aqu-sz'].mean())
