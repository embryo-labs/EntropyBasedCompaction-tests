#!/usr/bin/env python3
import pandas as pd
report = pd.read_csv('report.csv')
print(report['rocksdb.stall.micros'].sum() / 1e6)
