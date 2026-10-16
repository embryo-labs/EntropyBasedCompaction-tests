# Paper specific settings
single_col_inch = 3.3
double_col_inch = 6.9

acmsmall_inch = 5.44

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


# Not reviewed. Just for reference.
def check_visible_labels(figure):
    """Warn about visible text and legends outside the canvas; return warning messages.

    Checks PDF rendering, ignoring hidden elements and tick labels outside the
    axis view limits. Bounds do not account for savefig cropping or occlusion
    by other elements.
    """
    import warnings
    from io import BytesIO
    from matplotlib.legend import Legend
    from matplotlib.text import Text
    from math import isfinite
    from matplotlib.collections import Collection
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from matplotlib.transforms import Bbox

    issues = []

    def check_rendered_labels(event):
        renderer = event.renderer
        canvas = figure.bbox
        excluded = set()
        for ax in figure.axes:
            if not ax.get_visible():
                excluded.update(ax.findobj())
                continue
            for axis in (ax.xaxis, ax.yaxis):
                if not axis.get_visible():
                    excluded.update(axis.findobj())
                    continue
                lower, upper = sorted(axis.get_view_interval())
                view_tolerance = (upper - lower) * 1e-10
                for tick in axis.get_major_ticks() + axis.get_minor_ticks():
                    if (not tick.get_visible()
                            or not lower - view_tolerance <= tick.get_loc() <= upper + view_tolerance):
                        excluded.update((tick.label1, tick.label2))
        for legend in figure.findobj(match=Legend):
            if not legend.get_visible():
                excluded.update(legend.findobj())

        for artist in figure.findobj(match=lambda item: isinstance(item, (Text, Legend))):
            if artist in excluded or not artist.get_visible() or artist.get_alpha() == 0:
                continue
            if isinstance(artist, Text) and not artist.get_text().strip():
                continue
            if isinstance(artist, Legend) and not artist.get_frame_on():
                # A frameless legend's layout bounds include invisible border padding.
                content = artist.findobj(
                    match=lambda item: isinstance(item, (Text, Line2D, Patch, Collection))
                )
                content_bounds = [
                    item.get_window_extent(renderer)
                    for item in content
                    if item is not artist.get_frame()
                    and item.get_visible() and item.get_alpha() != 0
                    and (not isinstance(item, Text) or item.get_text().strip())
                ]
                content_bounds = [bounds for bounds in content_bounds
                                  if all(isfinite(value) for value in bounds.extents)]
                if not content_bounds:
                    continue
                bounds = Bbox.union(content_bounds)
            else:
                bounds = artist.get_window_extent(renderer)
            overflow_pt = {
                'left': canvas.x0 - bounds.x0,
                'right': bounds.x1 - canvas.x1,
                'bottom': canvas.y0 - bounds.y0,
                'top': bounds.y1 - canvas.y1,
            }
            overflow_mm = {
                side: round(float(pixels) / figure.dpi * 25.4, 3)
                for side, pixels in overflow_pt.items() if pixels > 0
            }
            if overflow_mm:
                label = repr(artist.get_text()) if isinstance(artist, Text) else 'Legend'
                message = f'{label} exceeds canvas (mm): {overflow_mm}'
                issues.append(message)
                warnings.warn(message, stacklevel=1)

    canvas = figure.canvas
    # During PDF drawing, the event provides the PDF renderer and the figure
    # uses PDF coordinates. Screen rendering can give different text bounds.
    callback_id = canvas.mpl_connect('draw_event', check_rendered_labels)
    try:
        with BytesIO() as output:
            figure.savefig(output, format='pdf')
    finally:
        canvas.mpl_disconnect(callback_id)
    return issues
