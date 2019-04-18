import math
import pyqtree
import svgwrite
import os
import os.path

def vector_angle(x, y):
	return math.atan2(y, x) - math.atan2(0, 1)

class Point(object):
	def __init__(self, x, y, bearing):
		self.x = float(x)
		self.y = float(y)
		self.bearing = float(bearing)

	def distance_to(self, other):
		'''
		Returns the distance to another Point or Observation.
		'''
		return math.sqrt((other.x - self.x) * (other.x - self.x) + (other.y - self.y) * (other.y - self.y))

	def angle_to(self, other):
		'''
		Returns the angle difference to another Point.
		'''
		d = other.bearing - self.bearing
		return abs((d + 180) % 360 - 180)

	def __repr__(self):
		return '({}, {}, {})'.format(self.x, self.y, self.bearing)

class PointWithID(Point):
	def __init__(self, id, x, y, bearing):
		super(PointWithID, self).__init__(x, y, bearing)
		self.id = id

class Observation(object):
	def __init__(self, x, y):
		self.x = x
		self.y = y

	def to_point(self, next_obs):
		'''
		Converts this Observation into a Point.

		A Point has a bearing whereas an Observation does not. The bearing is estimated
		from next_obs, which should be the observation immediately following this one in
		the parent trace.
		'''
		bearing = vector_angle(next_obs.x - self.x, next_obs.y - self.y)
		return Point(self.x, self.y, math.degrees(bearing))

class Rectangle(object):
	def __init__(self, min_point, max_point):
		self.min_point = min_point
		self.max_point = max_point

	def lengths(self):
		return self.max_point.x - self.min_point.x, self.max_point.y - self.min_point.y
	
	def extend_to_contain(self, point):
		self.min_point.x = min(self.min_point.x, point.x)
		self.min_point.y = min(self.min_point.y, point.y)
		self.max_point.x = max(self.max_point.x, point.x)
		self.max_point.y = max(self.max_point.y, point.y)
	
	def extend_to_contain_rect(self, rect):
		self.extend_to_contain(rect.min_point)
		self.extend_to_contain(rect.max_point)

def get_empty_rectangle():
	return Rectangle(Point(float('inf'), float('inf'), 0), Point(float('-inf'), float('-inf'), 0))

class Trace(object):
	def __init__(self, observations):
		self.observations = observations
	
	def bounds(self):
		r = get_empty_rectangle()
		for obs in self.observations:
			r.extend_to_contain(obs)
		return r

def read_traces(dir):
	files = [os.path.join(dir, fbase) for fbase in os.listdir(dir)]
	files = [fname for fname in files if os.path.isfile(fname)]
	traces = []
	for fname in files:
		with open(fname, 'r') as f:
			observations = []
			for line in f:
				parts = line.strip().split(' ')
				observations.append(Observation(float(parts[0]), float(parts[1])))
			traces.append(Trace(observations))
	return traces

class Index(object):
	def __init__(self, points):
		'''
		Create an index over the specified points.
		
		Each element must have x and y attributes.
		'''
		# compute bounding box
		r = get_empty_rectangle()
		for point in points:
			r.extend_to_contain(point)
		self.index = pyqtree.Index(bbox=(r.min_point.x - 1, r.min_point.y - 1, r.max_point.x + 1, r.max_point.y + 1))
		
		# insert points into index, with bounding box being unit square around the point
		for point in points:
			self.index.insert(point, (point.x - 0.5, point.y - 0.5, point.x + 0.5, point.y + 0.5))
	
	def nearby(self, point, distance):
		'''
		Returns points in the index that are within distance to the specified point.
		'''
		# convert to Point object in case something else is provided (for distance_to function)
		point = Point(point.x, point.y, 0)
		
		# filter points
		candidates = self.index.intersect((point.x - distance, point.y - distance, point.x + distance, point.y + distance))
		return [candidate for candidate in candidates if point.distance_to(candidate) < distance]

class Vertex(object):
	def __init__(self, id, x, y):
		self.id = id
		self.x = x
		self.y = y
		self.in_edges = []
		self.out_edges = []

class Edge(object):
	def __init__(self, id, src, dst):
		self.id = id
		self.src = src
		self.dst = dst
	
	def length(self):
		dx = self.dst.x - self.src.x
		dy = self.dst.y - self.src.y
		return math.sqrt(dx * dx + dy * dy)
	
	def point_along_edge(self, distance):
		'''
		Returns the point along this edge that is distance away from the source vertex.
		'''
		factor = distance / self.length()
		return Point(self.src.x + factor * (self.dst.x - self.src.x), self.src.y + factor * (self.dst.y - self.src.y), 0)

class Graph(object):
	def __init__(self):
		self.vertices = []
		self.edges = []
	
	def add_vertex(self, x, y):
		vertex = Vertex(len(self.vertices), x, y)
		self.vertices.append(vertex)
		return vertex
	
	def add_edge(self, src, dst):
		edge = Edge(len(self.edges), src, dst)
		self.edges.append(edge)
		src.out_edges.append(edge)
		dst.in_edges.append(edge)
		return edge
	
	def write(self, fname):
		with open(fname, 'w') as f:
			for vertex in self.vertices:
				f.write("{} {}\n".format(vertex.x, vertex.y))
			f.write("\n")
			for edge in self.edges:
				f.write("{} {}\n".format(edge.src.id, edge.dst.id))
	
	def bounds(self):
		r = get_empty_rectangle()
		for vertex in self.vertices:
			r.extend_to_contain(vertex)
		return r

def read_graph(fname):
	graph = Graph()
	with open(fname) as f:
		section = 'vertices'
		for line in f:
			line = line.strip()
			if section == 'vertices':
				if line:
					parts = line.split(' ')
					graph.add_vertex(float(parts[0]), float(parts[1]))
				else:
					section = 'edges'
			elif line:
				parts = line.split(' ')
				src_id = int(parts[0])
				dst_id = int(parts[1])
				graph.add_edge(graph.vertices[src_id], graph.vertices[dst_id])
	return graph
	
def visualize(fname, graphs, traces, points, width):
	# automatically determine scale based on the bounding box
	r = get_empty_rectangle()
	for graph in graphs:
		r.extend_to_contain_rect(graph.bounds())
	for trace in traces:
		r.extend_to_contain_rect(trace.bounds())
	for point in points:
		r.extend_to_contain(point)
	l = max(r.lengths()[0], r.lengths()[1])
	scale = 1000 / l
	lengths = r.lengths()[0] * scale, r.lengths()[1] * scale
	origin = r.min_point
	drawing = svgwrite.Drawing(fname, (int(lengths[0]) + 1, int(lengths[1]) + 1))

	def convert_coords(point):
		return Point(int((point.x - origin.x) * scale), int(lengths[1] - (point.y - origin.y) * scale), 0)

	for graph in graphs:
		for edge in graph.edges:
			start = convert_coords(edge.src)
			end = convert_coords(edge.dst)
			drawing.add(drawing.line((start.x, start.y), (end.x, end.y), stroke=svgwrite.rgb(10, 10, 16, '%'), stroke_width=width))
	for trace in traces:
		for i in xrange(len(trace.observations) - 1):
			start = convert_coords(trace.observations[i])
			end = convert_coords(trace.observations[i + 1])
			drawing.add(drawing.line((start.x, start.y), (end.x, end.y), stroke=svgwrite.rgb(10, 10, 16, '%'), stroke_width=width))
	for point in points:
		c = convert_coords(point)
		drawing.add(drawing.circle(center=(c.x, c.y), r=width, fill='blue'))

	drawing.save()
