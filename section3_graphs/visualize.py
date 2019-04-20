
from util import read_graph, visualize
actual = read_graph('actual1.graph')
a = read_graph('inferred1.graph')
b = read_graph('actual2.graph')
c = read_graph('inferred2.graph')
visualize('graph.svg', [actual, a, b, c], [], [], 4)
