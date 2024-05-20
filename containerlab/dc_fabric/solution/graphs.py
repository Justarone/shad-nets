import json
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter

plt.gca().yaxis.set_major_formatter(FormatStrFormatter('%10d'))

def draw(source_to_label, title):
    plt.xlabel('клиенты')
    plt.ylabel('цена')
    plt.title(title)
    for source, label in source_to_label.items():
        graphs = None
        with open(source, 'r') as f:
            graphs = json.load(f)
        for prefix, graph in graphs.items():
            plt.plot(graph['x'], graph['y'], label=prefix + label)

    plt.legend(loc='upper left')
    plt.grid()
    plt.show()


sources10 = {'safe10.json': ', s=true', 'unsafe10.json': ', s=false'}
sources25 = {'safe25.json': ', s=true', 'unsafe25.json': ', s=false'}
draw(sources10, '10G клиентские порты')
draw(sources25, '25G клиентские порты')

