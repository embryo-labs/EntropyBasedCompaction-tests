#!/usr/bin/env python3
import pandas as pd
report = pd.read_csv('report.csv')
max_srs = report['num-sorted-runs'].max()
print(max_srs)
print(list(report['secs_elapsed'][report['num-sorted-runs'] == max_srs]))
