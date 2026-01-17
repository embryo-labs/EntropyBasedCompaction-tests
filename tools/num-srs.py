#!/usr/bin/env python3
import math
import os
import numpy as np
import pandas as pd

report = pd.read_csv('report.csv')
print('Average: ' + str(report['num-sorted-runs'].mean()) + '\nP99: ' + str(np.percentile(report['num-sorted-runs'], 99)))
