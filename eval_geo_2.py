import util
import sys
import random

MARKER_FREQUENCY = 30
MATCH_DISTANCE = 60

if len(sys.argv) < 3:
	print 'usage: eval_geo.py actual.graph inferred.graph'
	sys.exit(0)

actual = util.read_graph(sys.argv[1])
inferred = util.read_graph(sys.argv[2])

def distance_btn_vertices(v1, v2):
	return ((v1.x - v2.x) ** 2 + (v1.y - v2.y) ** 2) ** 1/2

def get_nearest_vertex(vertex, graph):
	return min(graph.vertices, key = lambda v: distance_btn_vertices(v, vertex))

def get_pairs_from_graphs(actual, inferred):
	actual_one = random.choice(actual.vertices)
	actual_two = random.choice(actual.vertices)

	inferred_one = get_nearest_vertex(actual_one, inferred)
	inferred_two = get_nearest_vertex(actual_two, inferred)
        
        print(actual_one.x, actual_one.y)
	print(actual_two.x, actual_two.y)
	print(inferred_one.x, inferred_one.y)
	print(inferred_two.x, inferred_two.y)
	return (actual_one, actual_two, inferred_one, inferred_two)


def shortest_path_distance(graph, src, dst):
	
	shortest_paths = {src: (None, 0) }
	current_vertex = src
	visited = set()
	
	while current_vertex != dst:
		visited.add(current_vertex)
		destination_edges = [edge for edge in graph.edges if edge.src == current_vertex]
		weight_to_current_vertex = shortest_paths[current_vertex][1]

		for edge in destination_edges:
			weight = edge.length() + weight_to_current_vertex
			if edge.dst not in shortest_paths:
				shortest_paths[edge.dst] = (current_vertex, weight)
			else:
				current_shortest_weight = shortest_paths[edge.dst][1]
				if current_shortest_weight > weight:
					shortest_paths[edge.dst] = (current_vertex, weight)

		next_destination = {node: shortest_paths[node] for node in shortest_paths if node not in visited}
		if not next_destination:
			return 'route not possible'

		current_vertex = min(next_destination, key=lambda k: next_destination[k][1])

	return shortest_paths[current_vertex][1]

for _ in range(100):
	actual_one, actual_two, inferred_one, inferred_two = get_pairs_from_graphs(actual, inferred)
	actual_shortest_distance = shortest_path_distance(actual, actual_one, actual_two)
	inferred_shortest_distance = shortest_path_distance(inferred, inferred_one, inferred_two)
	print("inferred_distance: ", inferred_shortest_distance)
	print("actual_distance: ", actual_shortest_distance)
	print('\n')

