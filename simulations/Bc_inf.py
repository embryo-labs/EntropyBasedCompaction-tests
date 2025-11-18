#!/usr/bin/env python3
import math
from dataclasses import dataclass
from typing import Any, Callable

def simulate(N, policy, print_status):
    Ac = 0
    sum_num_srs = 0
    max_num_srs = 0
    for _ in range(0, N):
        policy.flush()
        if print_status:
            policy.print_status()
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
    return (Ac / N, sum_num_srs / N, max_num_srs)

class PolicyBySize:
    merge: Callable[[list], Any]
    s: list
    def __init__(self, merge=None):
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
    # Return the amount of data written
    def pick_and_do_compaction(self, pick):
        picked = pick()
        if picked is None:
            return None
        (i, j) = picked
        self.s[j] = self.merge(self.s[i:(j+1)])
        written = self.s[j]
        del self.s[i:j]
        return written

class Leveling(PolicyBySize):
    T: float
    def __init__(self, T, merge=None):
        super().__init__(merge)
        self.T = T
    def pick(self):
        next_level_capacity = 1
        for i in range(0, len(self.s) - 1):
            while next_level_capacity <= self.s[i]:
                next_level_capacity *= self.T
            # next_level_capacity > s[i]
            if self.s[i+1] < next_level_capacity:
                return (i, i+1)
    def pick_and_do_compaction(self):
        return super().pick_and_do_compaction(self.pick)

class BenefitCost(PolicyBySize):
    t_e: float

    def __init__(self, t_e, merge=None):
        super().__init__(merge)
        self.t_e = t_e

    def Re(self, sizes):
        v = 0
        for size in sizes:
            v += size * math.log2(size)
        s = sum(sizes)
        return math.log2(s) - v / s

    def pick(self):
        best_Re = None
        best_range = None
        for i in range(0, len(self.s) - 1):
            sizes = [self.s[i]]
            for j in range(i + 1, len(self.s)):
                sizes.append(self.s[j])
                Re = self.Re(sizes)
                if Re >= self.t_e:
                    if best_Re is None or Re > best_Re:
                        best_Re = Re
                        best_range = (i, j)
        return best_range

    def pick_and_do_compaction(self):
        return super().pick_and_do_compaction(self.pick)

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

def benefit_cost(N, entropy_threshold, S=None, print_status=False):
    if S is None:
        merge = None
    else:
        merge = Merger(S).merge
    return simulate(N, BenefitCost(entropy_threshold, merge), print_status)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-S', type=int)
    parser.add_argument('-N', type=int, required=True)
    parser.add_argument('--policy', choices=['leveling', 'tiering', 'benefit-cost'], required=True)
    parser.add_argument('--entropy_threshold', type=float)
    parser.add_argument('-T', type=int)
    args = parser.parse_args()
    print_status = True

    policy = args.policy
    if policy == 'leveling':
        res = leveling(args.N, args.T, args.S, print_status)
    elif policy == 'tiering':
        res = tiering(args.N, args.T, args.S, print_status)
    elif policy == 'benefit-cost':
        res = benefit_cost(args.N, args.entropy_threshold, args.S, print_status)
    else:
        assert False
    (wa, avg_num_srs, max_num_srs) = res
    print('%f\t%f\t%f' %(wa, avg_num_srs, max_num_srs))
