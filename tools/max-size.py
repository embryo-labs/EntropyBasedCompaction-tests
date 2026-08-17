#!/usr/bin/env python3
import sys
data_dir = '.'
if len(sys.argv) == 2:
    data_dir = sys.argv[1]
import os
import pandas as pd
report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
print(report['size'].max() / 1e9, 'GB')
