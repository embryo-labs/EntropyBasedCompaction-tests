#!/usr/bin/env python3
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-s', type=int)
parser.add_argument('-k', type=float, required=True)
parser.add_argument('-R', type=int, required=True)
parser.add_argument('-C', type=int, required=True)
parser.add_argument('--no-global-compaction', action='store_true')
parser.add_argument('--print-a', action='store_true')
parser.add_argument('--print-path', action='store_true')
parser.add_argument('--export-policy', nargs='?', default=False)
args = parser.parse_args()

s = args.s
k = args.k
R = args.R
C = args.C
no_global_compaction = args.no_global_compaction
print_a = args.print_a
print_path = args.print_path
export_policy = args.export_policy

import sys
if export_policy is False:
    export_policy = None
else:
    if export_policy is None:
        export_policy = sys.stdout
    else:
        export_policy = open(export_policy, mode='w')

def export_policy_begin(a):
    print('{', file=export_policy)
    if s is not None:
        print('''\
    "s": %d,''' %s, file=export_policy)
    print('''\
    "R": %d,
    "a": %d,
    "rounds": [
        {
            "n": 0,
            "steps": [''' %(R, a), file=export_policy)

def no_answer():
    print('No answer')
    if export_policy:
        a = 2 * R
        if s is not None:
            a += s
        export_policy_begin(a)
        # Don't do any compaction except global compaction
        print(f'''\
                {{"total": {R}, "compact": {R}}}
            ]
        }},
        {{
            "n": {R},
            "steps": [
                {{"total": {R}, "compact": {R}}}
            ]
        }}
    ]
}}''', file=export_policy)
    exit(1)

if k >= 1:
    no_answer()

assert R >= 1

import math
from dataclasses import dataclass

@dataclass
class Result:
    n: int
    m: int

@dataclass
class Mem:
    n: int
    m: int
    x: int
    def as_result(self):
        return Result(n=self.n, m=self.m)

mem_f = {}
def f(a, b, c):
    if a < b:
        return None
    if c < 0:
        return None
    if c == 0:
        return Result(n=b, m=0)
    if b == 0 and c == 1:
        return Result(n=1, m=0)
    if (a, b, c) in mem_f:
        mem = mem_f[(a, b, c)]
    else:
        mem = f_calc(a, b, c)
        mem_f[(a, b, c)] = mem
    if mem is None:
        return None
    else:
        return mem.as_result()
def f_calc(a, b, c):
    best = None
    for x in range(1, b + c):
        if x == 1:
            delta_b = 0
            m1 = 0
        else:
            delta_b = math.ceil(k * x)
            m1 = x
        # It is possible that 1 < x < b because sometimes we can only merge part of the pending sorted runs to avoid exceeding the sorted run number limit due to long merging.
        if x <= b:
            if b + math.floor(k * x) > a:
                continue
            new_b = b - x + delta_b
            new_c = c - delta_b
        else:
            first_phase = f(a, b, x - b)
            if first_phase is None:
                continue
            if first_phase.n + math.floor(k * x) > a:
                continue
            m1 += first_phase.m
            new_b = delta_b
            new_c = c - (x-b) - delta_b
        second_phase = f(a - 1, new_b, new_c)
        if second_phase is None:
            continue
        n = 1 + second_phase.n
        m = m1 + second_phase.m
        if best is not None:
            if best.n < n:
                continue
            if best.n == n:
                if best.m < m:
                    continue
        best = Mem(n=n, m=m, x=x)
    return best

@dataclass
class MemG:
    n: int
    x: int
    a_n: int
mem_g = {}
def g(a, n, ns=set()):
    if a < n:
        return None
    if (a, n) in mem_g:
        mem = mem_g[(a, n)]
    else:
        mem = g_calc(a, n, ns)
        mem_g[(a, n)] = mem
    if mem is None:
        return None
    else:
        return mem.n
def g_calc(a, n, ns):
    assert n > 1
    m = R * C
    if n + math.floor(R * k) > a:
        return None
    best = None
    b = math.ceil(R * k)
    for x in range(b + math.floor(k * m), R + 1):
        for a_n in range(1, a):
            first_phase = h(a - 1, a_n, b, x-b)
            if first_phase is None:
                continue
            if b + math.floor((first_phase.m + m) * k) > x:
                continue
            if x < R:
                new_b = math.ceil(k * x)
                second_phase = f(a-1, new_b, R-x-new_b)
                if second_phase is None:
                    continue
                new_n = 1 + second_phase.n
            else:
                new_n = first_phase.n
            if best is not None:
                if best.n <= new_n:
                    continue
                if best.n == n:
                    assert best.x <= x
                    if best.a_n <= a_n:
                        continue
            best = MemG(n=new_n, x=x, a_n=a_n)
    if best is None:
        return None
    if best.n != n and best.n not in ns:
        ns.add(best.n)
        result = g(a, best.n, ns)
        ns.remove(best.n)
        if result is None:
            return None
    return best

@dataclass
class MemH:
    n: int
    m: int
    x: int
    a_n1: int
    def as_result(self):
        return Result(n=self.n, m=self.m)
mem_h = {}
def h(a, a_n, b, c):
    assert a_n <= a
    if a_n < 1:
        return None
    if a_n < b:
        return None
    if c < 0:
        return None
    if c == 0:
        return Result(n=b, m=0)
    if b == 0 and c == 1:
        return Result(n=1, m=0)
    if (a, a_n, b, c) in mem_h:
        mem = mem_h[(a, a_n, b, c)]
    else:
        mem = h_calc(a, a_n, b, c)
        mem_h[(a, a_n, b, c)] = mem
    if mem is None:
        return None
    else:
        return mem.as_result()
def h_calc(a, a_n, b, c):
    best = None
    for x in range(1, b + c):
        for a_n1 in range(1, a + 1):
            if x == 1:
                delta_b = 0
                m1 = 0
            else:
                delta_b = math.ceil(k * x)
                m1 = x
            # It is possible that 1 < x < b because sometimes we can only merge part of the pending sorted runs to avoid exceeding the sorted run number limit due to long merging.
            if x <= b:
                if b + math.floor(k * x) > a:
                    continue
                new_b = b - x + delta_b
                new_c = c - delta_b
            else:
                first_phase = h(a, a_n1, b, x - b)
                if first_phase is None:
                    continue
                if first_phase.n + math.floor(k * x) > a:
                    continue
                m1 += first_phase.m
                new_b = delta_b
                new_c = c - (x-b) - delta_b
            second_phase = h(a-1, a_n-1, new_b, new_c)
            if second_phase is None:
                continue
            n = 1 + second_phase.n
            m = m1 + second_phase.m
            if best is not None:
                if best.m < m:
                    continue
                if best.m == m:
                    if best.n < n:
                        continue
                    if best.n == n:
                        if best.x > x:
                            continue
            best = MemH(m=m, n=n, x=x, a_n1=a_n1)
    return best

a = 1
if no_global_compaction:
    max_a = R
else:
    max_a = 2 * R
while a <= max_a:
    result = f(a, 0, R)
    if result is None:
        a += 1
        continue
    if no_global_compaction:
        break
    n = result.n
    result = g(a, n)
    if result is not None:
        break
    a += 1
else:
    no_answer()

if s is None:
    a_ans = a
else:
    a_ans = s + a
if print_a:
    print(a_ans)

def print_status(lst):
    if s is None:
        print(lst)
    else:
        print([s * x for x in lst])

# e: the number of sorted runs before the first phase
def print_first_phase_merge(lst, e, x):
    assert sum(lst[e:]) == x
    if x > 1:
        if export_policy is not None:
            print('''\
                {"total": %d, "compact": %d},''' %(len(lst), len(lst) - e), file=export_policy)
        del lst[e:]
        lst.append(x)
        if print_path:
            print_status(lst)

def print_f_path(lst, a, b, c):
    if c == 0:
        for i in range(0, b):
            lst.append(1)
            if print_path:
                print_status(lst)
        return
    if b == 0 and c == 1:
        lst.append(1)
        if print_path:
            print_status(lst)
        return
    x = mem_f[(a, b, c)].x
    if x == 1:
        delta_b = 0
    else:
        delta_b = math.ceil(k * x)
    e = len(lst)
    if x <= b:
        for i in range(0, x):
            lst.append(1)
            if print_path:
                print_status(lst)
        new_b = b - x + delta_b
        new_c = c - delta_b
    else:
        print_f_path(lst, a, b, x - b)
        new_b = delta_b
        new_c = c - (x-b) - delta_b
    print_first_phase_merge(lst, e, x)
    print_f_path(lst, a - 1, new_b, new_c)

def print_g_path(a, n):
    lst = []
    assert a >= n
    assert n > 1
    if export_policy is not None:
        print('''\
        {
            "n": %d,
            "steps": [''' %n, file=export_policy)
    b = math.ceil(R * k)
    mem = mem_g[(a, n)]
    x = mem.x
    a_n = mem.a_n
    print_h_path(lst, a - 1, a_n, b, x-b)
    if x < R:
        print_first_phase_merge(lst, 0, x)
        b = math.ceil(k * x)
        print_f_path(lst, a-1, b, R-x-b)
    if export_policy is not None:
        print('''\
                {"total": %d, "compact": %d}
            ]
        }''' %(len(lst), len(lst)), end='', file=export_policy)
    if len(lst) == n:
        if export_policy is not None:
            print(file=export_policy)
        return
    if export_policy is not None:
        print(',', file=export_policy)
    print_g_path(a, len(lst))

def print_h_path(lst, a, a_n, b, c):
    assert a_n >= 1
    assert b <= a_n
    if c == 0:
        for i in range(0, b):
            lst.append(1)
            if print_path:
                print_status(lst)
        return
    if b == 0 and c == 1:
        lst.append(1)
        if print_path:
            print_status(lst)
        return
    mem = mem_h[(a, a_n, b, c)]
    x = mem.x
    a_n1 = mem.a_n1
    if x == 1:
        delta_b = 0
    else:
        delta_b = math.ceil(k * x)
    e = len(lst)
    if x <= b:
        for i in range(0, x):
            lst.append(1)
            if print_path:
                print_status(lst)
        new_b = b - x + delta_b
        new_c = c - delta_b
    else:
        print_h_path(lst, a, a_n1, b, x - b)
        new_b = delta_b
        new_c = c - (x-b) - delta_b
    print_first_phase_merge(lst, e, x)
    print_h_path(lst, a-1, a_n-1, new_b, new_c)

if print_path or export_policy is not None:
    if export_policy is not None:
        export_policy_begin(a_ans)
    print_f_path([], a, 0, R)
    result = mem_f[(a, 0, R)]
    n = result.n
    if export_policy is not None:
        print('''\
                {"total": %d, "compact": %d}
            ]
        }''' %(n, n), end='', file=export_policy)
    if no_global_compaction:
        if export_policy is not None:
            print(file=export_policy)
    else:
        if export_policy is not None:
            print(',', file=export_policy)
        print_g_path(a, n)
    if export_policy is not None:
        print('''\
    ]
}''', file=export_policy)
