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
        'color': plt.cm.tab10(3),
    },
    'tiering8': {
        'name': 'Tiering8',
        'color': plt.cm.tab10(4),
    },
    'universal': {
        'name': 'Universal',
        'color': plt.cm.tab10(5),
    },
    'benefit-cost': {
        'name': 'Entropy-based',
        'color': plt.cm.tab10(2),
    },
}
