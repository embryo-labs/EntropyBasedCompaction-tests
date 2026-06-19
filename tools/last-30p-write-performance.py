#!/usr/bin/env python3
import pandas as pd
write_count_time = pd.read_csv('write-count-time.csv')
write_count_time = write_count_time.iloc[-len(write_count_time)*3//10:]
print('ops:', write_count_time['count'].mean())
print('latency:', (write_count_time['micros'].sum() / write_count_time['count'].sum()), 'us')
