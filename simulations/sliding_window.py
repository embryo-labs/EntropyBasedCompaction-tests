#!/usr/bin/env python3
import ast
sizes = input()
sizes = ast.literal_eval(sizes)

k_n = 1.7
entropy_threshold = 0.78

import math

size = sizes[0]
num = 1
sum_nlog2n = size * math.log2(size)
i = 0
class BestInfo:
    r_e: float
    r_n: float
    first: int
    last: int
    def __init__(self, r_e, r_n, first, last):
        self.r_e = r_e
        self.r_n = r_n
        self.first = first
        self.last = last
best = None
for j in range(1, len(sizes)):
    size += sizes[j]
    num += 1
    sum_nlog2n += sizes[j] * math.log2(sizes[j])
    while num > 2 and sizes[i] <= (size - sizes[i]) / (num - 1) / k_n:
        size -= sizes[i]
        num -= 1
        sum_nlog2n -= sizes[i] * math.log2(sizes[i])
        i += 1
    r_e = math.log2(size) - sum_nlog2n / size
    if r_e < entropy_threshold - 1e-6:
        continue
    if best is None:
        better = True
    else:
        if best.r_e < r_e - 1e-6:
            better = True
        elif best.r_e > r_e + 1e-6:
            better = False
        else:
            better = best.r_n < (num - 1) / size
    if better:
        best = BestInfo(r_e, (num - 1) / size, i, j)
print(best.first, best.last)
print(sizes[best.first:best.last + 1])
