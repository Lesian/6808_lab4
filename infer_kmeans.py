from util import Trace, Observation, Point, PointWithID, Index, Graph, vector_angle, read_traces
import math
import random

SEED_DISTANCE = 20
DISTANCE_THRESHOLD = 70
BEARING_THRESHOLD = 45
MOVEMENT_THRESHOLD = 10

class Cluster(Point):
	def __init__(self, center):
		'''
		Initialize a cluster.

		center is an instance of Point (see util.py).
		'''
		super(Cluster, self).__init__(center.x, center.y, center.bearing)
		self.center = center
		self.members = []

	def add_member(self, point):
		'''
		Add a new member to this cluster.

		point is an instance of Point (see util.py).
		'''
		self.members.append(point)

	def get_mean(self):
		'''
		Returns a Point that is the mean of this cluster's members.

		The x and y positions are simple averages over the members' positions. The bearing
		is computed by averaging the x and y components of the unit vectors represented by
		the bearing.
		'''
		if not self.members:
			return self.center

		x = 0
		y = 0
		bearing_x = 0
		bearing_y = 0
		for member in self.members:
			x += member.x
			y += member.y
			bearing_x += math.cos(math.radians(member.bearing))
			bearing_y += math.sin(math.radians(member.bearing))
		x /= len(self.members)
		y /= len(self.members)
		bearing_x /= len(self.members)
		bearing_y /= len(self.members)
		return Point(x, y, math.degrees(vector_angle(bearing_x, bearing_y)))

	def __repr__(self):
		return 'Cluster at {} ({} members)'.format(self.center, len(self.members))

def get_markers(traces, seed_distance):
	'''
	Create seed points from the provided traces.

	We create seed points every seed_distance meters along the traces, computing the
	bearing as the angle from the positive x axis. Then, as we generate seed points, we
	compare each new point to existing clusters to check whether there is a cluster that
	satisfies the distance and bearing thresholds to the new point. If so, we assign the
	point to the cluster. If not, we create a new cluster with the seed point as its
	center.

	For example, suppose we have a trace with three observations: (0, 0), (0, 50), and
	(50, 50), and that seed_distance=30. We create seed points at (0, 0, 90), (0, 30, 90),
	(10, 50, 0), and (40, 50, 0).
	'''

	def get_trace_markers(trace):
		'''
		Create and return list of seed points for this trace.
		'''
		last_distance = seed_distance
		seed_points = []
		for i in xrange(len(trace.observations) - 1):
			next_obs = trace.observations[i + 1]
			point = trace.observations[i].to_point(next_obs)
			while point.distance_to(next_obs) > seed_distance - last_distance:
				length = point.distance_to(next_obs)
				factor = (seed_distance - last_distance) / length
				point.x, point.y = (point.x + (next_obs.x - point.x) * factor), (point.y + (next_obs.y - point.y) * factor)
				seed_points.append(Point(point.x, point.y, point.bearing))
				last_distance = 0
			last_distance += point.distance_to(trace.observations[i + 1])
		return seed_points

	# return a list of markers corresponding to each trace
	# we assign global IDs to each marker to use later
	markers_by_trace = []
	next_id = 0
	for trace in traces:
		trace_markers = []
		for marker in get_trace_markers(trace):
			trace_markers.append(PointWithID(next_id, marker.x, marker.y, marker.bearing))
			next_id += 1
		markers_by_trace.append(trace_markers)
	return markers_by_trace

def initialize_clusters(markers, distance_threshold, bearing_threshold):
	'''
	Create an initial set of clusters.

	Return a list of Cluster objects.

	markers is a list of PointWithID instances.

	We arbitrarily select a marker that has not yet been assigned to a cluster, and create
	a new cluster at the marker. Then, any markers that are within distance_threshold and
	bearing_threshold of the selected marker are added to the cluster.
	
	For example, suppose that we have created a cluster at (26, 0, 83), and the remaining
	seed points are at (0, 0, 90), (30, 0, 90), (50, 10, 0), and (50, 40, 0). Then,
	(30, 0, 90) is assigned to the existing cluster since the distance to the cluster is 4
	while the bearing difference is 7, which are both within the thresholds. The other seed
	points become new clusters.
	
	You might find Index (from util.py) useful to query points that are near a specified
	location.
	'''
        clusters = []
        while markers:
            random_marker = markers[random.randint(0, len(markers) - 1)]
            markers.remove(random_marker)
            
            nearest_markers = Index(markers).nearby(random_marker, distance_threshold)

            nearest_markers = [marker for marker in  nearest_markers if marker.angle_to(random_marker) <= bearing_threshold]

            cluster = Cluster(random_marker)
            cluster.add_member(random_marker)
            for marker in nearest_markers:
                cluster.add_member(marker)

            clusters.append(cluster)

            markers = list(set(markers) - set(nearest_markers))
        return clusters
	

def kmeans(markers, initial_clusters, distance_threshold, movement_threshold):
	'''
	Run K-means algorithm on the clusters.

	markers is a list of PointWithID instances, while initial_clusters is what you returned
	in initialize_clusters above.

	On each iteration, we first recompute the set of clusters: for every cluster from the
	previous iteration, we initialize one cluster at the mean of the members of the old
	cluster. Then, we re-assign marker points to the new clusters.
	
	To re-assign points, distance_threshold is an upper bound for the distance that a
	marker can be from a cluster. You can use this to search for nearby clusters using the
	Index. However, you should use similarity_metric to determine the most similar cluster.

	We continue until the sum of the distance that clusters move on the recomputation step
	is less than movement_threshold. For example, if we have two clusters (0, 0) and (1, 1)
	with three points (0, 0), (1, 1), and (1.1, 1), then the first point is assigned to
	the first cluster while the other two are assigned to the second cluster. On the next
	recomputation step, the first cluster moves 0 units, and the second cluster moves 0.1
	units; if movement_threshold > 0.1, then we would terminate.
	'''
	def similarity_metric(cluster, marker):
		'''
		Returns a similarity metric between the specified cluster and marker.
		
		A lower value indicates greater similarity.
		'''
		distance = marker.distance_to(cluster)
		angle_difference = marker.angle_to(cluster)
		return distance + angle_difference

	def recompute_clusters(prev_clusters):
		'''
		Return a list of new clusters, and the sum of the distances that clusters moved.
		'''
                new_clusters = []
                total_distance_moved = 0
		for cluster in prev_clusters:
                    new_cluster = Cluster(cluster.get_mean())
                    new_clusters.append(new_cluster)
                    total_distance_moved += new_cluster.center.distance_to(cluster.center)

                return new_clusters, total_distance_moved



	def assign_members(cluster_index, markers):
		'''
		Assign each marker point to the closest cluster.
		'''
		# your code here
                for marker in markers:
                    nearby_clusters = cluster_index.nearby(marker, distance_threshold)

                    if nearby_clusters:
                        best_cluster = nearby_clusters[0]
                        best_similarity = similarity_metric(best_cluster, marker)
                        for cluster in nearby_clusters:
                            similarity = similarity_metric(cluster, marker)
                            if similarity < best_similarity:
                                best_cluster = cluster
                                best_similarity = similarity
                        best_cluster.add_member(marker)

                    else:
                        print("Marker not within distance distance_threshold to any point")


	clusters = initial_clusters
	distance = float('inf')
	while distance >= movement_threshold:
		clusters, distance = recompute_clusters(clusters)
		index = Index(clusters)
		assign_members(index, markers)
		print 'moved clusters distance={}'.format(distance)
	return clusters

def generate_edges(graph, markers_by_trace, clusters):
	'''
	Connects clusters that appear consecutively in a trace.
	
	graph is a road network graph where each cluster is a vertex but no edges have been
	added yet. markers_by_trace is a list, where the i-th element is the list of markers
	for trace i. clusters is the final clusters returned by kmeans above, but each cluster
	will have an additional vertex field.
	
	You can use graph.add_edge(src_cluster.vertex, dst_cluster.vertex) to create an
	edge.
	
	You don't need to return anything, just update the graph.
	'''
	def get_marker_cluster_map(clusters):
		'''
		Returns a map from marker ID to the cluster that the marker has been assigned to.
		'''
		m = {}
		for cluster in clusters:
			for member in cluster.members:
				m[member.id] = cluster
		return m

        marker_cluster_map = get_marker_cluster_map(clusters)


        for trace_markers in markers_by_trace:
            for i in range(1, len(trace_markers)):
                cluster_one = marker_cluster_map[trace_markers[i-1]]
                cluster_two = marker_cluster_map[trace_markers[i]]
                if cluster_one != cluster_two:
                    graph.add(cluster_one.vertex, cluster_two.vertex)

'''
You can use the code below to run manually.
This will also produce visualizations of the inferred graph, the clusters after k-means, and the traces.

import util
import infer_kmeans
traces = util.read_traces('out/')
markers_by_trace = infer_kmeans.get_markers(traces[0:100], 20)
flat_markers = [marker for trace_markers in markers_by_trace for marker in trace_markers]
initial_clusters = infer_kmeans.initialize_clusters(flat_markers, 70, 45)
clusters = infer_kmeans.kmeans(flat_markers, initial_clusters, 140, 10)
graph = util.Graph()
for cluster in clusters:
	cluster.vertex = graph.add_vertex(cluster.x, cluster.y)
infer_kmeans.generate_edges(graph, markers_by_trace, clusters)
util.visualize('out.svg', [graph], [], [], 3)
util.visualize('clusters.svg', [], [], clusters, 3)
util.visualize('traces.svg', [], traces[0:100], [], 3)
graph.write('kmeans-inferred.graph')
'''

if __name__ == "__main__":
	import sys
	
	if len(sys.argv) < 2:
		print 'usage: infer_kmeans.py path_to_trips/'
		sys.exit(0)

	# load traces
	traces = read_traces(sys.argv[1])
	
	# get initial markers
	markers_by_trace = get_markers(traces, SEED_DISTANCE)
	flat_markers = [marker for trace_markers in markers_by_trace for marker in trace_markers]
	
	# initialize clusters and run k-means
	initial_clusters = initialize_clusters(flat_markers, DISTANCE_THRESHOLD, BEARING_THRESHOLD)
	clusters = kmeans(flat_markers, initial_clusters, 2 * DISTANCE_THRESHOLD, MOVEMENT_THRESHOLD)
	
	# extract road network
	graph = Graph()
	for cluster in clusters:
		cluster.vertex = graph.add_vertex(cluster.x, cluster.y)
	generate_edges(graph, markers_by_trace, clusters)
	
	# output graph
	graph.write('kmeans-inferred.graph')
