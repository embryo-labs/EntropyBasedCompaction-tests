#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
    print('Usage: ' + sys.argv[0] + ' dir')
    exit(1)
dir = sys.argv[1]

write_MB_s = 50

import json
import os

from dataclasses import dataclass
from itertools import accumulate
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

import common

mpl.rcParams.update({
    'hatch.linewidth': 0.5,
    'font.family': 'serif',
    'font.serif': ['Linux Libertine O'],
    'axes.unicode_minus': False,
    'font.size': 9,
    'text.usetex': True,
    'text.latex.preamble': r'''
        \usepackage{amsmath}
        \usepackage{libertine}
        \usepackage[libertine]{newtxmath}
    ''',
})

versions = [
    {
        'path': 'universal-hard-trigger',
        'max-running-bg-jobs': None,
    },
    {
        'path': 'entropy-based',
        'max-running-bg-jobs': 1,
    },
]
for v in versions:
    v.update(common.versions[v['path']])
version_names = [v['name'] for v in versions]

fig = plt.figure(dpi=300, figsize=(common.single_col_inch, 1), constrained_layout=True)
fig.get_layout_engine().set(
    h_pad=0.01,
    w_pad=0.01,
)
ax = plt.gca()
ax.set_xlabel(r'Compaction efficiency $R_\text{eff}$')
ax.set_ylabel('CDF')
ax.set_ylim(0, 1)
ax.grid(axis="y")
for version in versions:
    if version['max-running-bg-jobs'] is None:
        max_running_bg_jobs = ''
    else:
        max_running_bg_jobs = '-max-running-bg-jobs-1'
    workload = f'readwhilewriting-key-16-value-603-unique-size-10GB-warmup-secs-1200-run-secs-1200{max_running_bg_jobs}-write-{write_MB_s}MB-s-no-stall-memtable-8MiB-compaction-200MB-s-get-0.87-seek-0.13-nexts-48'
    data_dir = os.path.join(dir, workload, version['path'])
    warmup = False
    ts_begin_ns = None
    @dataclass(slots=True)
    class Compaction:
        R_eff: float
        output_bytes: int
    compactions = []
    for line in open(os.path.join(data_dir, 'log.json')):
        entry = json.loads(line)
        if entry['event'] == 'new-benchmark':
            if entry['name'] != 'readwhilewriting':
                continue
            if warmup == False:
                warmup = True
                continue
            ts_begin_ns = entry['timestamp(ns)']
        if ts_begin_ns is None:
            continue
        if entry['event'] == "compaction-finished":
            compactions.append(Compaction(entry['R_eff'], entry['output_bytes']))
    compactions.sort(key=lambda c: c.R_eff)
    reff = [0]
    reff.extend(c.R_eff for c in compactions)
    output_bytes = np.fromiter(accumulate((c.output_bytes for c in compactions), initial=0), dtype=np.int64)
    cdf = output_bytes / output_bytes[-1]

    ax.step(
        reff,
        cdf,
        where="post",
        label=version['name'],
        color=version['color'],
        linewidth=1,
    )
ax.set_xlim(left=0)
ax.legend(frameon=False)

pdf_path = os.path.join(dir, f"universal-efficiency-{write_MB_s}MB-s.pdf")
fig.savefig(pdf_path, metadata={"CreationDate": None})
print("Plot saved to " + pdf_path)
