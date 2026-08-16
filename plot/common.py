# Paper specific settings
single_col_inch = 3.3
double_col_inch = 6.9

import math
from scipy.optimize import root_scalar

def bound_wa(S, entropy_threshold):
    return math.log2(S * math.e) / entropy_threshold

def bound_ra_v1(S, entropy_threshold):
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

def bound_ra(max_size, entropy_threshold):
    def f(x): return x*math.log2(x)
    def g(x): return (-f(x)-f(1-x))/(1-x)
    def sol_a(t_e):
        # solve the equation g(x)=a
        a = 0
        for i in range(1, 30):
            add = 2 ** -i
            if g(a + add) < t_e: 
                a += add
        return a
    a = sol_a(entropy_threshold)
    return math.ceil(math.log2(2**entropy_threshold / max_size) / math.log2(a)) + math.floor(2**entropy_threshold + 1)

def bound_sa_v1(entropy_threshold):
    def f(i, x):
        if x > 1/i - 1e-6:
            return -math.log2(i)
        return (1 - i * x) * math.log2(1 - i * x) + i * x * math.log2(x)
    i = math.ceil(2**entropy_threshold - 1)
    sol = root_scalar(lambda x: f(i, x) + entropy_threshold, bracket=[1 / (i+1), 1 / i])
    assert sol.converged
    return 1 / sol.root

def bound_sa(entropy_threshold):
    return 2**entropy_threshold

import matplotlib.pyplot as plt

colors = [
    {
        'dark': 'C0',
        'light': plt.get_cmap('tab20c')(1),
    },
    {
        'dark': 'C1',
        'light': plt.get_cmap('tab20c')(6),
    },
    {
        'dark': 'C2',
        'light': plt.get_cmap('Set2')(0),
    },
    {
        'dark': 'C3',
        'light': '#ff7070',
    },
    {
        'dark': 'C4',
        'light': plt.get_cmap('tab20c')(13),
    },
    {
        'dark': 'C5',
        'light': plt.get_cmap('tab20')(11),
    },
    {
        'dark': 'C6',
        'light': 'C6',
    },
    {
        'dark': 'C7',
        'light': plt.get_cmap('tab20c')(17),
    },
    {
        'dark': 'C8',
        'light': 'C8',
    },
    {
        'dark': 'C9',
        'light': 'C9',
    },
]

versions = {
    'rocksdb-tuned': {
        'name': 'RocksDB-Tuned',
        'color': colors[0]['dark'],
        'facecolor': colors[0]['light'],
        'hatch': 'XX',
    },
    'tiering2': {
        'name': 'Tiering2',
        'color': colors[1]['dark'],
        'facecolor': colors[1]['light'],
        'hatch': '--//',
    },
    'tiering4': {
        'name': 'Tiering4',
        'color': colors[3]['dark'],
        'facecolor': colors[3]['light'],
        'hatch': '---',
    },
    'tiering8': {
        'name': 'Tiering8',
        'color': colors[4]['dark'],
        'facecolor': colors[4]['light'],
        'hatch': '--\\\\',
    },
    'universal-hard-trigger': {
        'name': 'Universal',
        'color': colors[5]['dark'],
        'facecolor': colors[5]['light'],
        'hatch': '\\\\\\',
    },
    'lazy-leveling-2-3': {
        'name': 'Lazy Leveling',
        'color': colors[6]['dark'],
        'facecolor': colors[6]['light'],
        'hatch': '--XX',
    },
    'bush': {
        'name': 'LSM-bush',
        'color': colors[7]['dark'],
        'facecolor': colors[7]['light'],
        'hatch': 'XXXX',
    },
    'vertiorizon-5-4': {
        'name': 'Vertiorizon',
        'color': colors[8]['dark'],
        'facecolor': colors[8]['light'],
        'hatch': '//////'
    },
    'silk5': {
        'name': 'SILK',
        'facecolor': 'white',
        'hatch': '------',
    },
    'endure-4-8-1': {
        'name': 'Endure',
        'color': colors[9]['dark'],
        'facecolor': colors[9]['light'],
        'hatch': '\\\\\\\\\\\\',
    },
    'entropy-based': {
        'name': 'EBC',
        'color': colors[2]['dark'],
        'facecolor': colors[2]['light'],
        'hatch': '///',
    },
}
