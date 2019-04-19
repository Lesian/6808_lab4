
from util import read_graph, visualize
actual = read_graph('boston.graph')
a = read_graph('kde-inferred.graph')
b = read_graph('kmeans-inferred.graph')
visualize('graph.svg', [actual, a, b], [], [], 3)
