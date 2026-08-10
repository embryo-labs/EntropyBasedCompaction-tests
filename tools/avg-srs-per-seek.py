#!/usr/bin/env python3
import pandas as pd
seek_count = pd.read_csv('seek-count-time.csv')['count']
num_srs = pd.read_csv('report.csv')['num-sorted-runs']
print(sum(num_srs * seek_count) / sum(seek_count))
