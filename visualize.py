
from util import read_graph, visualize
actual = read_graph('section3_graphs/inferred2.graph')
a = read_graph('section3_graphs/inferred1.graph')
visualize('inferred2.svg', [actual], [], [], 1)
