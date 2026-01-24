# Paper specific settings
single_col_inch = 3.4
double_col_inch = 7

import math
from scipy.optimize import root_scalar

def bound_wa(S, entropy_threshold):
    return math.log2(S * math.e) / entropy_threshold

def bound_ra(S, entropy_threshold):
    def f(k, n):
        return math.log2(k+n-1) - k * math.log2(k) / (k+n-1)
    n = math.ceil(2**entropy_threshold)
    # Make sure that k0 > 1
    while f(1, n) < entropy_threshold + 1e-6:
        n += 1
    best = math.inf
    while n <= best:
        k_upper = 2
        while f(k_upper, n) >= entropy_threshold:
            k_upper *= 2
        sol = root_scalar(lambda k: f(k, n) - entropy_threshold, bracket=[1, k_upper])
        assert sol.converged
        k0 = sol.root
        assert k0 > 1
        bound = (math.floor(math.log(S) / math.log(k0)) + 1) * (n-1)
        best = min(best, bound)
        n += 1
    return best

def bound_sa(entropy_threshold):
    def f(i, x):
        if x > 1/i - 1e-6:
            return -math.log2(i)
        return (1 - i * x) * math.log2(1 - i * x) + i * x * math.log2(x)
    i = math.ceil(2**entropy_threshold - 1)
    sol = root_scalar(lambda x: f(i, x) + entropy_threshold, bracket=[1 / (i+1), 1 / i])
    assert sol.converged
    return 1 / sol.root

import matplotlib.pyplot as plt

versions = {
    'rocksdb-tuned': {
        'name': 'RocksDB-Tuned',
        'color': 'C0',
        'hatch': 'XX',
    },
    'tiering2': {
        'name': 'Tiering2',
        'color': 'C1',
        'hatch': '--//',
    },
    'tiering4': {
        'name': 'Tiering4',
        'color': 'C3',
        'hatch': '---',
    },
    'tiering8': {
        'name': 'Tiering8',
        'color': 'C4',
        'hatch': '--\\\\',
    },
    'universal': {
        'name': 'Universal',
        'color': 'C5',
        'hatch': '\\\\\\',
    },
    'benefit-cost': {
        'name': 'EUC',
        'color': plt.get_cmap('Set2')(0),
        'hatch': '///',
    },
}
