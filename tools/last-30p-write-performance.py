#!/usr/bin/env python3
import pandas as pd
write_count_time = pd.read_csv('write-count-time.csv')
write_count_time = write_count_time.iloc[-len(write_count_time)*3//10:]
print('ops:', write_count_time['count'].mean())
print('latency:', (write_count_time['micros'].sum() / write_count_time['count'].sum()), 'us')

report = pd.read_csv('report.csv')
report = report.iloc[-len(report)*3//10:]
secs_elapsed = report['secs_elapsed']
secs_elapsed = secs_elapsed.iloc[-1] - secs_elapsed.iloc[0] + 1
print('User write throughput:', report['rocksdb.bytes.written'].sum() / secs_elapsed / 1e6, 'MB/s')
print('Stall percentage:', report['rocksdb.stall.micros'].sum() / 1e6 / secs_elapsed * 100, '%')
