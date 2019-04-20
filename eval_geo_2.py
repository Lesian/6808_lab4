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
	return (actual_one, actual_two, inferred_one, inferred_two)


def shortest_path_distance(graph, src, dst):
	
	shortest_paths = {src: (None, 0) }
	current_vertex = src
	visited = set()
	
	while current_vertex != dst:
		visited.add(current_vertex)
		destination_edges = current_vertex.out_edges
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
			return None

		current_vertex = min(next_destination, key=lambda k: next_destination[k][1])
	return (shortest_paths[dst][1])

match_count = 0
total_count = 0
for _ in range(1000):
	actual_one, actual_two, inferred_one, inferred_two = get_pairs_from_graphs(actual, inferred)
	actual_shortest_distance = shortest_path_distance(actual, actual_one, actual_two)
	inferred_shortest_distance = shortest_path_distance(inferred, inferred_one, inferred_two)
	if (actual_shortest_distance == None and infrerred_shortest_distance == None):
		match_count += 1
	elif (actual_shortest_distance == None or inferred_shortest_distance == None):
		pass
	elif (abs(actual_shortest_distance - inferred_shortest_distance) < 5):
		match_count += 1
	else:
		pass
print(float(match_count) / 1000)
