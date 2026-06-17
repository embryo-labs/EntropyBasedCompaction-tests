#!/usr/bin/env python3
import pandas as pd
report = pd.read_csv('report.csv')
print(report['size'].max() / 1e9, 'GB')
