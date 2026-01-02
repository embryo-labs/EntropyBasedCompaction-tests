import matplotlib.pyplot as plt

versions = {
    'rocksdb-tuned': {
        'name': 'Leveling5',
        'color': plt.cm.tab10(0),
    },
    'tiering2': {
        'name': 'Tiering2',
        'color': plt.cm.tab10(1),
    },
    'tiering4': {
        'name': 'Tiering4',
        'color': plt.cm.tab10(2),
    },
    'tiering8': {
        'name': 'Tiering8',
        'color': plt.cm.tab10(3),
    },
    'universal': {
        'name': 'Universal',
        'color': plt.cm.tab10(4),
    },
    'benefit-cost': {
        'name': 'Entropy-Based',
        'color': plt.cm.tab10(5),
    },
}
