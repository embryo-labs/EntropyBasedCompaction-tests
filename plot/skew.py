#!/usr/bin/env python3
import sys
if len(sys.argv) != 2:
    print('Usage: ' + sys.argv[0] + ' dir')
    exit()
dir = sys.argv[1]

vec_zipfian_theta = [0, 0.5, 0.8, 0.9, 0.99]

import io
import os
import json
import runstats
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import gridspec

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
        'path': 'no_preemption_conditions',
        'name': 'By-theory',
        'facecolor': common.colors[0]['light'],
        'hatch': 'XX',
    },
    {
        'path': 'entropy-based',
        'name': common.versions['entropy-based']['name'],
        'facecolor': common.versions['entropy-based']['facecolor'],
        'hatch': common.versions['entropy-based']['hatch'],
    }
]
version_names = [version['name'] for version in versions]

bar_width = 1 / (len(versions) + 1)
cluster_width = bar_width * len(versions)

fig = plt.figure(dpi=300, figsize=(common.single_col_inch, 1), constrained_layout=True)
fig.get_layout_engine().set(
    h_pad=0.01,
    w_pad=0.01,
    wspace=0.1,
    rect=(0, 0.12, 1, 0.75),
)
gs = gridspec.GridSpec(1, 2, figure=fig)

x_labelpad = 1

ax_reff = plt.subplot(gs[0, 0])
fig.text(0.25, 0, r'(a) Avg $R_\text{eff}$ of new compactions', ha='center', va='bottom')
plt.ylabel(r'Average $R_\text{eff}$', loc='top')
ax_reff.tick_params(axis='x', pad=0)
plt.xlabel(r'Zipfian $\theta$', labelpad=x_labelpad)
plt.xticks(list(range(0, len(vec_zipfian_theta))), vec_zipfian_theta)

ax_num_srs = plt.subplot(gs[0, 1])
fig.text(0.76, 0, r'(b) Avg number of sorted runs', ha='center', va='bottom')
plt.ylabel('Avg \\# of runs', loc='top')
ax_num_srs.tick_params(axis='x', pad=0)
plt.xlabel(r'Zipfian $\theta$', labelpad=x_labelpad)
plt.xticks(list(range(0, len(vec_zipfian_theta))), vec_zipfian_theta)

version_num_srs_avg = {}
for cluster_idx, zipfian_theta in enumerate(vec_zipfian_theta):
    for version_idx, version in enumerate(versions):
        x = cluster_idx - cluster_width / 2 + bar_width / 2 + version_idx * bar_width
        if zipfian_theta == 0:
            skew = ''
        else:
            skew = f'-write_zipfian_theta-{zipfian_theta}'
        if version['path'] == 'entropy-based':
            entropy_threshold = ''
            max_running_bg_jobs = '-max-running-bg-jobs-1'
        else:
            entropy_threshold = '-autotune_entropy_threshold'
            max_running_bg_jobs = ''
        workload = f'readwhilewriting-key-16-value-603-unique-size-10GB-warmup-secs-1200-run-secs-1200{max_running_bg_jobs}{entropy_threshold}{skew}-write-50MB-s-no-stall-memtable-8MiB-compaction-200MB-s-get-0.87-seek-0.13-nexts-48'
        data_dir = os.path.join(dir, workload, version['path'])
        log_json = open(os.path.join(data_dir, 'log.json'))
        for i in range(0, 2):
            while True:
                entry = json.loads(log_json.readline())
                if entry['event'] == 'new-benchmark':
                    if entry['name'] == 'readwhilewriting':
                        break
        stats = runstats.Statistics()
        while True:
            entry = json.loads(log_json.readline())
            if entry['event'] == 'new-benchmark':
                break
            if entry['event'] == 'new-compaction':
                stats.push(entry['R_eff'])
        reff_avg = stats.mean()
        reff_stddev = stats.stddev()

        report = pd.read_csv(os.path.join(data_dir, 'report.csv'))
        num_srs_avg = report['num-sorted-runs'].mean()

        ax_reff.bar(x, reff_avg, width=bar_width, edgecolor='black', linewidth=0.5, facecolor=version['facecolor'], hatch=version['hatch'])
        ax_num_srs.bar(x, num_srs_avg, width=bar_width, edgecolor='black', linewidth=0.5, facecolor=version['facecolor'], hatch=version['hatch'])

        if zipfian_theta == 0.99:
            version_num_srs_avg[version['name']] = num_srs_avg
ax_reff.set_ylim(bottom=0)
ax_num_srs.set_ylim(bottom=0)
handles = [mpl.patches.Patch(facecolor=v['facecolor'], hatch=v['hatch'], 
                            edgecolor='black', linewidth=0.5) for v in versions]
fig.legend(
    handles=handles,
    labels=version_names,
    ncol=len(versions),
    loc='upper center',
    bbox_to_anchor=(0.5, 1.1),
    frameon=False,
)
pdf_path = os.path.join(dir, f'skew-zipfian.pdf')
fig.savefig(pdf_path, metadata={'CreationDate': None})
print('Plot saved to ' + pdf_path)

tex = io.StringIO()
num_srs_by_theory = version_num_srs_avg['By-theory']
num_srs_our = version_num_srs_avg[common.versions['entropy-based']['name']]
num_srs_reduction = (num_srs_by_theory - num_srs_our) / num_srs_by_theory
print('\\defmacro{ZipfianNumSrsReduction}{%.0f\\%%}' %(num_srs_reduction * 100), file=tex)
tex = tex.getvalue()
print(tex)
open('skew-zipfian.tex', mode='w').write(tex)
