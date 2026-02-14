#!/usr/bin/env python3
import math
import enum
from dataclasses import dataclass
from typing import Any, Callable, Optional

def simulate(N, policy, print_status):
    Ac = 0
    sum_num_srs = 0
    max_num_srs = 0
    max_size = 0
    for _ in range(0, N):
        policy.flush()
        if print_status:
            policy.print_status()
        max_size = max(max_size, policy.size())
        while True:
            written = policy.pick_and_do_compaction()
            if written is None:
                break
            Ac += written
            if print_status:
                policy.print_status()
        num_srs = policy.num_sorted_runs()
        sum_num_srs += num_srs
        max_num_srs = max(max_num_srs, num_srs)
    return (Ac / N, sum_num_srs / N, max_num_srs, max_size)

class Leveling:
    T: float
    merge: Callable[[list], Any]
    s: list
    def __init__(self, T, merge=None):
        self.T = T
        if merge is None:
            self.merge = lambda s: sum(s)
        else:
            self.merge = merge
        self.s = []
    def num_sorted_runs(self):
        return len(self.s)
    def size(self):
        return sum(self.s)
    def print_status(self):
        print(self.s)
    def flush(self):
        self.s.insert(0, 1)
    def pick(self):
        level_capacity = self.s[-1] / self.T
        i = len(self.s) - 2
        next_level_not_empty = True
        while i >= 0:
            if self.s[i] <= level_capacity / self.T:
                level_capacity /= self.T
                next_level_not_empty = False
                continue
            # self.s[i] > level_capacity / self.T
            if self.s[i] <= level_capacity:
                level_capacity /= self.T
                i -= 1
                next_level_not_empty = True
                continue
            # self.s[i] > level_capacity
            assert next_level_not_empty
            return (i,i+1)
    # Return the amount of data written
    def pick_and_do_compaction(self):
        picked = self.pick()
        if picked is None:
            return None
        (i, j) = picked
        self.s[j] = self.merge(self.s[i:(j+1)])
        written = self.s[j]
        del self.s[i:j]
        return written

class BenefitCost:
    @dataclass
    class Info:
        size: Any
        compact_to_last: bool
    t_e: float
    merge: Callable[[list], Any]
    C: Optional[float]
    k_n: float
    s: list

    def __init__(self, t_e, merge=None, C=None, k_n=None):
        self.t_e = t_e
        if merge is None:
            self.merge = lambda s: sum(s)
        else:
            self.merge = merge
        self.C = C
        self.k_n = k_n
        self.s = []
    def num_sorted_runs(self):
        return len(self.s)
    def size(self):
        size = 0
        for s in self.s:
            size += s.size
        return size
    def flush(self):
        self.s.insert(0, self.Info(1, False))

    def Re(self, sizes):
        v = 0
        for size in sizes:
            v += size * math.log2(size)
        s = sum(sizes)
        return math.log2(s) - v / s

    class CompactionReason(enum.Enum):
        Entropy = 1
        MidCompaction = 2
        LargeCompaction = 3
    @dataclass
    class Compaction:
        first: int
        last: int
        reason: 'BenefitCost.CompactionReason'
    def pick(self):
        if len(self.s) < 2:
            return None
        if self.s[-2].compact_to_last:
            return self.Compaction(len(self.s) - 2, len(self.s) - 1, self.CompactionReason.LargeCompaction)
        if self.C is not None:
            size_threshold = self.s[-1].size / self.C
            if self.k_n is None:
                for i in range(0, len(self.s) - 1):
                    if self.s[i].size > size_threshold:
                        return self.Compaction(i, len(self.s) - 1, self.CompactionReason.LargeCompaction)
            else:
                j = len(self.s) - 2
                if j > 0:
                    size = self.s[j].size + self.s[j-1].size
                    i = j - 2
                    while i >= 0 and self.s[i].size > size / (j - i) / self.k_n:
                        size += self.s[i].size
                        i -= 1
                    i += 1
                    if size > size_threshold:
                        return self.Compaction(i, j, self.CompactionReason.MidCompaction)
        best_Re = None
        best_range = None
        for i in range(0, len(self.s) - 1):
            sizes = [self.s[i].size]
            for j in range(i + 1, len(self.s)):
                sizes.append(self.s[j].size)
                Re = self.Re(sizes)
                if Re >= self.t_e:
                    if best_Re is None or Re > best_Re:
                        best_Re = Re
                        best_range = (i, j)
        if best_range is not None:
            (i, j) = best_range
            return self.Compaction(i, j, self.CompactionReason.Entropy)

    # Return the amount of data written
    def pick_and_do_compaction(self):
        picked = self.pick()
        if picked is None:
            return None
        s = []
        for k in range(picked.first, picked.last + 1):
            s.append(self.s[k].size)
        self.s[picked.last].size = self.merge(s)
        written = self.s[picked.last].size
        if picked.reason == self.CompactionReason.MidCompaction:
            self.s[picked.last].compact_to_last = True
        del self.s[picked.first:picked.last]
        return written

    def as_string(self):
        s = '['
        i = 0
        while i < len(self.s):
            s += str(self.s[i].size)
            if self.s[i].compact_to_last:
                s += ' to last'
            if i == len(self.s) - 1:
                s += ']'
            else:
                s += ', '
            i += 1
        return s
    def print_status(self):
        print(self.as_string())

class Tiering:
    @dataclass
    class Info:
        size: Any
        count: int

    T: int
    merge: Callable[[list], Any]
    s: list
    def __init__(self, T, merge=None):
        self.T = T
        if merge is None:
            self.merge = lambda s: sum(s)
        else:
            self.merge = merge
        self.s = []
    def _pick(self):
        count = 1
        num = 0
        i = 0
        while i < len(self.s):
            if count == self.s[i].count:
                num += 1
                i += 1
                continue
            if num >= self.T:
                assert num == self.T
                return (i - num, i - 1)
            num = 0
            if count < self.s[i].count:
                count *= self.T
            else:
                i += 1
        assert i == len(self.s)
        if num >= self.T:
            assert num == self.T
            return (i - num, i - 1)
    def num_sorted_runs(self):
        return len(self.s)
    def size(self):
        size = 0
        for s in self.s:
            size += s.size
        return size
    def flush(self):
        self.s.insert(0, self.Info(1, 1))
    # Return the amount of data written
    def pick_and_do_compaction(self):
        picked = self._pick()
        if picked is None:
            return None
        (i, j) = picked
        s = []
        count = 0
        for k in range(i, j + 1):
            s.append(self.s[k].size)
            count += self.s[k].count
        self.s[j] = self.Info(self.merge(s), count)
        written = self.s[j].size
        del self.s[i:j]
        return written
    def print_status(self):
        print('[', end='')
        i = 0
        while i < len(self.s):
            print(f'({self.s[i].size},{self.s[i].count})', end='')
            if i == len(self.s) - 1:
                print(']')
            else:
                print(', ', end='')
            i += 1

class Universal:
    compaction_trigger: int
    merge: Callable[[list], Any]
    s: list
    def __init__(self, compaction_trigger, merge=None):
        self.compaction_trigger = compaction_trigger
        if merge is None:
            self.merge = lambda s: sum(s)
        else:
            self.merge = merge
        self.s = []
    def num_sorted_runs(self):
        return len(self.s)
    def size(self):
        return sum(self.s)
    def flush(self):
        self.s.insert(0, 1)
    def pick_and_do_compaction(self):
        assert self.compaction_trigger >= 2
        if len(self.s) < self.compaction_trigger:
            return None
        i = 0
        while i < len(self.s) - 1:
            sum = self.s[i]
            j = i + 1
            while j < len(self.s) and self.s[j] <= sum:
                sum += self.s[j]
                j += 1
            j -= 1
            if j > i:
                break
            i += 1
        if i == len(self.s) - 1:
            return None
        assert i < j
        written = self.merge(self.s[i:j+1])
        del self.s[i:j]
        self.s[i] = written
        return written
    def print_status(self):
        print(self.s)

class Merger:
    S: int
    def __init__(self, S):
        self.S = S
    def merge(self, s):
        not_in_any = 1
        for x in s:
            not_in_any *= 1 - x / self.S
        return self.S * (1 - not_in_any)

def leveling(N, T, S=None, print_status=False):
    if S is None:
        merge = None
    else:
        merge = Merger(S).merge
    return simulate(N, Leveling(T, merge), print_status)

def tiering(N, T, S=None, print_status=False):
    if S is None:
        merge = None
    else:
        merge = Merger(S).merge
    return simulate(N, Tiering(T, merge), print_status)

def universal(N, compaction_trigger, S=None, print_status=False):
    if S is None:
        merge = None
    else:
        merge = Merger(S).merge
    return simulate(N, Universal(compaction_trigger, merge), print_status)

def benefit_cost(N, entropy_threshold, S=None, C=None, k_n=None, print_status=False):
    if S is None:
        merge = None
    else:
        merge = Merger(S).merge
    return simulate(N, BenefitCost(entropy_threshold, merge, C, k_n), print_status)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-S', type=int)
    parser.add_argument('-N', type=int, required=True)
    parser.add_argument('--policy', choices=['leveling', 'tiering', 'universal', 'benefit-cost'], required=True)
    parser.add_argument('--entropy_threshold', type=float)
    parser.add_argument('-C', type=float)
    parser.add_argument('--k_n', type=float)
    parser.add_argument('-T', type=int)
    parser.add_argument('--universal_compaction_trigger', type=int)
    args = parser.parse_args()
    print_status = True

    policy = args.policy
    if policy == 'leveling':
        res = leveling(args.N, args.T, args.S, print_status)
    elif policy == 'tiering':
        res = tiering(args.N, args.T, args.S, print_status)
    elif policy == 'universal':
        res = universal(args.N, args.universal_compaction_trigger, args.S, print_status)
    elif policy == 'benefit-cost':
        res = benefit_cost(args.N, args.entropy_threshold, args.S, args.C, args.k_n, print_status)
    else:
        assert False
    (wa, avg_num_srs, max_num_srs, max_size) = res
    print('%f\t%f\t%f\t%d' %(wa, avg_num_srs, max_num_srs, max_size))
