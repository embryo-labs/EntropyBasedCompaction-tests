#!/usr/bin/env python3
import math
import os
import pandas as pd

report = pd.read_csv('report.csv')
report = report.iloc[-math.ceil(len(report) * 0.3):]
print(report['num-sorted-runs'].mean())
