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

def get_nearest_vertex(vertex, graph):
	return min(graph.vertices, key = lambda v: v.distance_to(vertex))

def get_pairs_from_graphs(actual, inferred):
	actual_one = random.choice(actual.vertices)
	actual_two = random.choice(actual.vertices)

	inferred_one = get_nearest_vertex(actual_vertex_one, inferred)
	inferred_two = get_nearest_vertex(actual_vertex_two, inferred)

	return (actual_one, actual_two, inferred_one, inferred_two)


def shortest_path_distance(graph, src, dst):
	
	shortest_paths = {src: (None, 0) }
	current_vertex = src
	visited = set()
	
	while current_vertex != dst:
		visited.add(current_vertex)
		destination_edges = [edge in graph.edges if edge.src == current_vertex]
		weight_to_current_vertex = shortest_paths[current_vertex][1]

		for edge in destinations_edges:
			weight = edge.length + weight_to_current_vertex
			if edge.dst not in shortest_paths:
				shortest_paths[edge.dst] = (current_vertex, weight)
			else:
				current_shortest_weight = shortest_paths[edge.dst][1]
				if current_shortest_weight > weight:
					shortest_paths[edge.dst] = (current_vertex, weight)

		next_destination = {node: shortest_paths[node] for node in shortest_paths if node not in visited}
		if not next_destinations:
			return 'route not possible'

		current_node = min(next_destinations, key=lambda k: next_destinations[k][1])

	return shortest_paths[current_vertex][1]
		

	#find nearest vertices in other graph
def get_markers(graph):
	# we repeatedly select a random unvisited vertex, do a BFS from the vertex, and put down
	# markers while searching
	remaining_vertices = {}
	for vertex in graph.vertices:
		remaining_vertices[vertex.id] = vertex
	search_queue = []
	markers = []
	
	def add_marker_at(point):
		markers.append(util.PointWithID(len(markers), point.x, point.y, 0))

	def search_vertex(vertex, remaining_distance):
		if vertex.id not in remaining_vertices:
			return
		del remaining_vertices[vertex.id]
		for edge in vertex.out_edges:
			if edge.dst.id in remaining_vertices:
				search_edge_pos(edge, 0, remaining_distance)

	def search_edge_pos(edge, distance_along_edge, remaining_distance):
		if edge.length() > distance_along_edge + remaining_distance:
			search_queue.append((edge, distance_along_edge + remaining_distance))
			add_marker_at(edge.point_along_edge(distance_along_edge + remaining_distance))
		else:
			search_vertex(edge.dst, distance_along_edge + remaining_distance - edge.length())

	while len(remaining_vertices) > 0:
		search_queue = []
		vertex = random.choice(remaining_vertices.values())
		if len(vertex.out_edges) == 0 and len(vertex.in_edges) == 0:
			del remaining_vertices[vertex.id]
			continue
		add_marker_at(vertex)
		search_vertex(vertex, MARKER_FREQUENCY)
		while len(search_queue) > 0:
			edge, distance_along_edge = search_queue[0]
			search_queue = search_queue[1:]
			search_edge_pos(edge, distance_along_edge, MARKER_FREQUENCY)
	
	return markers


for _ in range(10):
	actual_one, actual_two, inferred_one, inferred_two = get_pairs_from_graphs(actual, inferred)
	actual_shortest_path = shortest_path_distance(actual, actual_one, actual_two)
	inferred_shortest_path = shortest_path_distance(inferred, inferred_one, inferred_two)
	

actual_markers = get_markers(actual)
inferred_markers = get_markers(inferred)
actual_index = util.Index(actual_markers)
actual_matched_set = set()
inferred_matched_set = set()
for marker in inferred_markers:
	candidates = actual_index.nearby(marker, MATCH_DISTANCE)
	candidates = [candidate for candidate in candidates if marker.distance_to(candidate) < MATCH_DISTANCE]
	if candidates:
		for candidate in candidates:
			actual_matched_set.add(candidate.id)
		inferred_matched_set.add(marker.id)
precision = float(len(inferred_matched_set)) / float(len(inferred_markers))
recall = float(len(actual_matched_set)) / float(len(actual_markers))
if precision + recall > 0:
	score = 2 * precision * recall / (precision + recall)
else:
	score = 0
print 'precision={}, recall={}, score={}'.format(precision, recall, score)
