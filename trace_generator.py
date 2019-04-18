import xml.etree.ElementTree
import numpy as np
import sys, getopt, os
import math
import random



def LoadOSM(osm_file_name):
	roadForMotorDict = {'motorway','trunk','primary','secondary','tertiary','unclassified','residential','service'}
	roadForMotorBlackList = {'None', 'pedestrian','footway','bridleway','steps','path','sidewalk','cycleway','proposed','construction','bus_stop','crossing','elevator','emergency_access_point','escape','give_way'}

	#import map from XML  
	mapxml = xml.etree.ElementTree.parse(osm_file_name).getroot()

	nodes = mapxml.findall('node')
	ways = mapxml.findall('way')

	nodedict = {}
	nodelinkdict = {}

	for anode in nodes:
		lat = float(anode.get('lat'))
		lon = float(anode.get('lon'))
		nodedict.update({anode.get('id'):(lat,lon)})
		nodelinkdict.update({anode.get('id'):[]})

	for away in ways:
		nds = away.findall('nd')
		highway = 'None'

		for atag in away.findall('tag'):
			if atag.get('k') == 'highway':
				highway = atag.get('v')

		if highway not in roadForMotorBlackList: 
		#if highway in roadForMotorDict:
			lastnodeid = None
			for anode in away.findall('nd'):
				refid = anode.get('ref')
				if lastnodeid == None:
					lastnodeid = refid
					continue
				else:
					nodelinkdict[refid].append(lastnodeid)
					nodelinkdict[lastnodeid].append(refid)

				lastnodeid = refid
				#mlat.append(float(nodedict[refid].get('lat')))
				#mlon.append(float(nodedict[refid].get('lon')))


	# Remove dead ends
	#return nodedict, nodelinkdict

	print("Removing dead ends...")
		

	update_node = {}
	update_link = {}
	for key in nodelinkdict.keys():
		update_node[key] = 1

	c = 0
	while True:
		c = c + 1
		del_num = 0

		update_link = {}

		for key in update_node.keys():
		#for key in nodelinkdict.keys():
			if len(nodelinkdict[key]) <= 1:
				if len(nodelinkdict[key]) == 1:
					update_link[nodelinkdict[key][0]] = 1
				#del nodedict[key]
				del nodelinkdict[key]
				del_num = del_num + 1
	

		update_node = {}

		#for key, value in nodelinkdict.iteritems():
		for key in update_link.keys():
			if key in nodelinkdict.keys():
				value = nodelinkdict[key]
				for n in value:
					if n not in nodelinkdict.keys():
						while n in nodelinkdict[key]:
							nodelinkdict[key].remove(n)

						update_node[key] = 1
						#del_num = del_num + 1

		print("Iteration "+str(c) + "  Delete "+str(del_num) + " nodes")

		if del_num == 0 :
			break

		#break

	for key in nodelinkdict.keys():
		value = nodelinkdict[key]
		if len(value) <= 1:
			print("Wrong key",key)

		
	return nodedict, nodelinkdict


def GenerateTrace(nodes, nodelinks):
	cur_node = random.choice(nodelinks.keys())
	old_node = None

	length = 0

	trace = []
	trace.append(nodes[cur_node])

	while True:
		possible_next_node = nodelinks[cur_node]
		#print(cur_node,old_node, possible_next_node)

		if old_node != None and old_node in possible_next_node:
			possible_next_node.remove(old_node)

		if len(possible_next_node) == 0:
			#print("Early Return")
			break

		next_node = random.choice(possible_next_node)

		trace.append(nodes[next_node])

		old_node = cur_node
		cur_node = next_node

		length = length + 1

		if length > 300 :
			break


	return trace

def latlon2meters(lat,lon):
	resolution_lat = 1.0 / (111111.0) 
	resolution_lon = 1.0 / (111111.0 * math.cos(lat / 360.0 * (math.pi * 2)))

	lat_meter = (lat - 40) / resolution_lat
	lon_meter = (lon + 70) / resolution_lon

	return lat_meter, lon_meter

def getInterceptionPoint(Target, PointA, PointB, distance, c):
	A = (PointB[0] - PointA[0]) * (PointB[0] - PointA[0]) + c * (PointB[1] - PointA[1]) * (PointB[1] - PointA[1])
	B = (2 * (PointB[0] - PointA[0]) * (PointA[0] - Target[0]) + c * 2 * (PointB[1] - PointA[1]) * (PointA[1] - Target[1]))
	C = (PointA[0] - Target[0]) * (PointA[0] - Target[0]) + c * (PointA[1] - Target[1]) * (PointA[1] - Target[1]) - distance * distance

	R = B*B - 4*A*C

	if R > 0:
		alpha1 =  ( -B + math.sqrt(R) ) / ( 2 * A)
		alpha2 =  ( -B - math.sqrt(R) ) / ( 2 * A)
	else :
		alpha1 = -1
		alpha2 = -1


	#print(alpha1, alpha2, A,B,C,R)
	#print(Target,PointA,PointB)

	return (alpha1, alpha2)


def InterpolationWithFixedDistanceInterval(trace, interval):
	new_trace = []
	
	cur_p = 0
	tar_p = 0
	cur_alpha = 0

	lat = trace[cur_p][0]
	lon = trace[cur_p][1]

	heading = (np.rad2deg(np.arctan2(trace[cur_p+1][0]-lat, (trace[cur_p+1][1] - lon))*math.cos(lat / 360.0 * (math.pi * 2))) - 90) % 360




	new_trace.append([lat,lon, heading, cur_p,cur_alpha])

	while True:
		if tar_p == len(trace) - 1:
			break

		lat0, lon0 = latlon2meters(lat, lon)
		lat1, lon1 = latlon2meters(trace[tar_p][0], trace[tar_p][1])
		lat2, lon2 = latlon2meters(trace[tar_p + 1][0], trace[tar_p + 1][1])

		heading = (np.rad2deg(np.arctan2(lat2-lat1, (lon2-lon1)*math.cos(lat1 / 360.0 * (math.pi * 2)))) - 90) % 360


		
		a1, a2 = getInterceptionPoint((0,0), (lat1 - lat0, lon1 - lon0), (lat2 - lat0, lon2 - lon0), interval, 1 )

		if (a1 < 0 or a1 > 1) and (a2 < 0 or a2 > 1) :
			tar_p = tar_p + 1
		else :
			if a1 >= 0.0 and a1 <= 1.0 :
				if (tar_p == cur_p and a1 > cur_alpha) or (tar_p > cur_p) :
					cur_p = tar_p
					cur_alpha = a1
					lat = (1-a1) * trace[tar_p][0] + a1 * trace[tar_p+1][0]
					lon = (1-a1) * trace[tar_p][1] + a1 * trace[tar_p+1][1]
					new_trace.append([lat,lon,heading,cur_p,cur_alpha])
					continue
				else:
					if a2 >= 0.0 and a2 <= 1.0:
						if (tar_p == cur_p and a2 > cur_alpha) or (tar_p > cur_p) :
							cur_p = tar_p
							cur_alpha = a2
							lat = (1-a2) * trace[tar_p][0] + a2 * trace[tar_p+1][0]
							lon = (1-a2) * trace[tar_p][1] + a2 * trace[tar_p+1][1]
							new_trace.append([lat,lon,heading,cur_p,cur_alpha])
							continue

			tar_p = tar_p + 1

	return new_trace


def AddNoise(trace, gps_noise, heading_noise):
	for sample in trace:
		noise = np.random.normal(0,gps_noise,2)

		resolution_lat = 1.0 / (111111.0) 
		resolution_lon = 1.0 / (111111.0 * math.cos(sample[0] / 360.0 * (math.pi * 2)))

		sample[0] = sample[0] + noise[0] * resolution_lat
		sample[1] = sample[1] + noise[1] * resolution_lon

		noise = np.random.normal(0,heading_noise,1)

		sample[2] = (sample[2] + noise[0]) % 360

	return trace


def Dump2File(trace,filename):
	def to_meters(coords):
		origin = [-71.1229000, 42.3465000]
		return (111111 * math.cos(origin[1] * math.pi / 180) * (coords[0] - origin[0]), 111111 * (coords[1] - origin[1]))

	with open(filename, "w") as fout:
		for sample in trace:
			meters = to_meters([sample[1], sample[0]])
			fout.write(str(meters[0])+" "+str(meters[1])+"\n")



def VisualizeTraceAndMap(nodes, nodelinks, traces):
	import matplotlib.pyplot as plt
	fig = plt.figure()
	ax = fig.add_subplot(111)
	print(len(nodelinks.keys()))
	for key, value in nodelinks.iteritems():
		lat0 = nodes[key][0]
		lon0 = nodes[key][1]

		for n in value:
			lat1 = nodes[n][0]
			lon1 = nodes[n][1]
			ax.plot((lon0,lon1),(lat0, lat1),'b',linewidth=0.5)


	for trace in traces:
		lon = []
		lat = []
		for i in xrange(len(trace)):
			lon.append(trace[i][1])
			lat.append(trace[i][0])

		ax.plot(lon,lat,linewidth=0.5)

	plt.show()

	#raw_input() 





if __name__ == "__main__":
	osm_file_name = None
	output_folder = "output/"
	output_num = 100
	gps_noise = 5
	heading_noise = 15
	trace_interval = 20
	visualization = False

	opts,args = getopt.getopt(sys.argv[1:],"m:o:n:g:i:a:v")
	for o,a in opts:
		#print(o,a)
		if o == "-m":
			osm_file_name = str(a)
		elif o == "-i":
			trace_interval = float(a)
		elif o == "-o":
			output_folder = str(a)
		elif o == "-n":
			output_num = int(a)
		elif o == "-g":
			gps_noise = float(a)
		elif o == "-a":
			heading_noise = float(a)
		elif o == "-v":
			visualization = True
	

	print("Input OSM file name: " + osm_file_name)
	print("Output folder name: " + output_folder)
	print("Number of output traces: " + str(output_num))
	print("Sample interval: "+str(trace_interval)+" meters")
	print("GPS noise variance: "+ str(gps_noise)+" meters")
	print("Heading noise variance: "+ str(heading_noise)+" degrees")
	print("Visualization: "+ str(visualization))

	nodes, nodelinks = LoadOSM(osm_file_name)

	for key in nodelinks.keys():
			if len(nodelinks[key]) <= 1:
				print("Wrong key",key)
				exit()
			value = nodelinks[key]

			for k in value:
				if k not in nodelinks.keys():
					nodelinks[key].remove(k)


	traces = []

	if not os.path.exists(output_folder):
			os.makedirs(output_folder)

	print("Generating Trips ...")

	for i in xrange(output_num) :
		if (i+1) % 100 ==  0:
			print(str(i)+"/"+str(output_num))

		trace = []

		while len(trace) < 10:
			trace = GenerateTrace(nodes, nodelinks)

		trace = InterpolationWithFixedDistanceInterval(trace, trace_interval)

		trace = AddNoise(trace, gps_noise, heading_noise)

		Dump2File(trace, output_folder+"/trip_"+str(i)+".txt")

		traces.append(trace)


	#print(trace)
	if visualization == True:
		VisualizeTraceAndMap(nodes, nodelinks, traces)




