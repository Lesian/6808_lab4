from util import Trace, Observation, Point, PointWithID, Index, Graph, vector_angle
from infer_kmeans import Cluster, get_markers, initialize_clusters, kmeans

def float_equals(a, b, epsilon=0.00001):
	return abs(a - b) < epsilon

def point_equals(a, b):
	return float_equals(a.x, b.x) and float_equals(a.y, b.y) and float_equals(a.bearing, b.bearing)

def test_get_markers():
	# this test simply runs through the example case in the docstring
	trace = Trace([Observation(0, 0), Observation(0, 50), Observation(50, 50)])
	markers = get_markers([trace], 30)[0]
	if len(markers) != 4:
		print 'test_get_markers: expected 4 markers'
	expected_markers = [Point(0, 0, 90), Point(0, 30, 90), Point(10, 50, 0), Point(40, 50, 0)]
	for a in markers:
		for i in xrange(len(expected_markers)):
			b = expected_markers[i]
			if point_equals(a, b):
				del expected_markers[i]
				break
	if expected_markers:
		print 'test_get_markers: expected get_markers to return markers at {}'.format(expected_markers[0])

def test_initialize_clusters():
	points = [
		PointWithID(0, 0, 0, 30), # cluster 1
		PointWithID(1, 2, 2, 35),
		PointWithID(2, 2, 0, 90), # cluster 2
		PointWithID(3, 1, 1, 85),
		PointWithID(4, 2, 2, 80),
		PointWithID(5, 10, 0, 30), # cluster 3
		PointWithID(6, 12, 2, 40),
		PointWithID(7, 20, 20, 20), # cluster 4
	]
	clusters = initialize_clusters(points, 5, 15)
	expected_clusters = [[0, 1], [2, 3, 4], [5, 6], [7]]
	id_to_cluster = {}
	for cluster in clusters:
		for member in cluster.members:
			id_to_cluster[member.id] = cluster
	for group in expected_clusters:
		cluster = id_to_cluster[group[0]]
		for member in group:
			if id_to_cluster[member] != cluster:
				a = points[group[0]]
				b = points[member]
				print 'test_initialize_clusters: expected points {} and {} to be in the same cluster'.format(a, b)
				break
        print 'you are good'

def test_kmeans():
	positions = [
		[0, 5], # cluster 1
		[0, 4],
		[0, 3],
		[1.5, 2], # cluster 2
		[1.5, 1],
		[2, 0],
		[3, 0],
		[3.5, 1],
		[3.5, 2],
		[5, 3], # cluster 3
		[5, 4],
		[5, 5],
	]
	initial_means = [
		[2, 6],
		[2, 3],
		[4.5, 3],
	]
	points = [PointWithID(i, positions[i][0], positions[i][1], 0) for i in xrange(len(positions))]
	initial_clusters = [Cluster(Point(mean[0], mean[1], 0)) for mean in initial_means]
	initial_clusters[0].add_member(points[0])
	initial_clusters[1].add_member(points[1])
	initial_clusters[1].add_member(points[2])
	initial_clusters[1].add_member(points[3])
	initial_clusters[1].add_member(points[4])
	initial_clusters[1].add_member(points[5])
	initial_clusters[1].add_member(points[6])
	initial_clusters[2].add_member(points[7])
	initial_clusters[2].add_member(points[8])
	initial_clusters[2].add_member(points[9])
	initial_clusters[2].add_member(points[10])
	initial_clusters[2].add_member(points[11])
	clusters = kmeans(points, initial_clusters, 20, 0.01)
	
	expected_clusters = [[0, 1, 2], [3, 4, 5, 6, 7, 8], [9, 10, 11]]
	id_to_cluster = {}
	for cluster in clusters:
		for member in cluster.members:
			id_to_cluster[member.id] = cluster
	for group in expected_clusters:
		cluster = id_to_cluster[group[0]]
		for member in group:
			if id_to_cluster[member] != cluster:
				a = points[group[0]]
				b = points[member]
				print 'test_kmeans: expected points {} and {} to be in the same cluster'.format(a, b)
				print clusters
				break

test_get_markers()
test_initialize_clusters()
test_kmeans()
