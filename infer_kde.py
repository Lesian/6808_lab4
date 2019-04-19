import cv
from math import atan2,sqrt,ceil,pi
import sys,getopt,os
from infer_kde_lib import TripLoader
from pylibs import spatialfunclib
from itertools import tee, izip

if len(sys.argv) < 2:
    print "Usage: infer_kde.py trip_dir [-c <cell_size>] [-t <mask_threshold>] [-b <gaussian_blur_size>] [-s <voronoi_sampling_interval>] [-d <shave_until_fraction>] [-n <max_trips>] [-h]\n"
    sys.exit()

all_trips = TripLoader.get_all_trips(sys.argv[1])

##
## important parameters
##

cell_size = 2 # meters
mask_threshold = int(len(all_trips) * 0.05) # turns grayscale into binary
gaussian_blur = 17
voronoi_sampling_interval = 10 # sample one point every so many pixels along the outline
MIN_DIR_COUNT = 10
shave_until = 0.9999
trip_max = len(all_trips)

opts,args = getopt.getopt(sys.argv[2:],"c:t:b:s:hn:d:")
for o,a in opts:
    if o == "-c":
        cell_size=int(a)
    elif o == "-t":
        mask_threshold=int(a)
    elif o == "-b":
        gaussian_blur = int(a)
    elif o == "-s":
        voronoi_sampling_interval = int(a)
    elif o == "-d":
        shave_until = float(a)
    elif o == "-n":
        trip_max = int(a)
    elif o == "-h":
        print "Usage: infer_kde.py trip_dir [-c <cell_size>] [-t <mask_threshold>] [-b <gaussian_blur_size>] [-s <voronoi_sampling_interval>] [-d <shave_until_fraction>] [-n <max_trips>] [-h]\n"
        sys.exit()

# 0 = North, 2 = East, 4 = South, 6 = West
def getsector(fromx,fromy,tox,toy):
    angle = atan2(toy-fromy,tox-fromx)
    # subtract pi/8 to align better with cardinal directions
    return int(-angle/(pi/4)+2) % 8

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)

##
## initialize some globals and read in the trips
##

all_locations = reduce(lambda x,y: x+y,[t.locations for t in all_trips[:trip_max]])
all_x = [l.x for l in all_locations]
all_y = [l.y for l in all_locations]

# find bounding box for data
min_x = min(all_x)-300
max_x = max(all_x)+300
min_y = min(all_y)-300
max_y = max(all_y)+300

diff_x = max_x - min_x
diff_y = max_y - min_y

print min_x, min_y, max_x,max_y

width = int(diff_x / cell_size)
height = int(diff_y / cell_size)
xscale = width / diff_x # pixels per x
yscale = height / diff_y # pixels per y

# aggregate intensity map for all traces
themap = cv.CreateMat(height,width,cv.CV_16UC1)
cv.SetZero(themap)

# aggregate intensity map for all traces, split by sector heading
sector_maps = {}

##
## Build an aggregate intensity map from all the edges
##

filename = "cache/n%d_c%d.xml"%(trip_max,cell_size)
if os.access(filename,os.F_OK) and False:
    print "Found cached intensity map %s, loading."%(filename)
    themap = cv.Load(filename)
    for sector in range(8):
        sector_maps[sector]=cv.Load("cache/n%d_c%d_s%d.xml"%(trip_max,cell_size,sector))
else:
    print "Making new intensity map %s."%(filename)
    sector_temp = {}
    sector_temp2 = {}
    for sector in range(8):
        sector_maps[sector]=cv.CreateMat(height,width,cv.CV_16UC1)
        cv.SetZero(sector_maps[sector])
        sector_temp[sector]=cv.CreateMat(height,width,cv.CV_8UC1)
        cv.SetZero(sector_temp[sector])
        sector_temp2[sector]=cv.CreateMat(height,width,cv.CV_16UC1)
        cv.SetZero(sector_temp2[sector])

    for trip in all_trips[:trip_max]:
        temp = cv.CreateMat(height,width,cv.CV_8UC1)
        cv.SetZero(temp)
        temp16 = cv.CreateMat(height,width,cv.CV_16UC1)
        cv.SetZero(temp16)

        for (orig,dest) in pairwise(trip.locations):
            oy=height-int(yscale*(orig.y - min_y))
            ox=int(xscale*(orig.x - min_x))
            dy=height-int(yscale*(dest.y - min_y))
            dx=int(xscale*(dest.x - min_x))
            cv.Line(temp,(ox,oy),(dx,dy),(32),1,cv.CV_AA)

            sector = getsector(ox,oy,dx,dy)
            cv.Line(sector_temp[sector],(ox,oy),(dx,dy),(32),1,cv.CV_AA)

        # accumulate trips into themap
        cv.ConvertScale(temp,temp16,1,0);
        cv.Add(themap,temp16,themap);

        # accumulate sector-separated trips into sector_maps
        for sector in range(8):
            cv.ConvertScale(sector_temp[sector],sector_temp2[sector],1,0);
            cv.Add(sector_maps[sector],sector_temp2[sector],sector_maps[sector])
            sector_temp[sector]=cv.CreateMat(height,width,cv.CV_8UC1)
            cv.SetZero(sector_temp[sector])
        
    print("filename here:" + filename)
    new_filename = "/Users/lesian/6808_lab4/" + filename
    # cv.Save(filename,themap)
    # cv.Save(new_filename,themap)
    for sector in range(8):
        #cv.Save("cache/n%d_c%d_s%d.xml"%(trip_max,cell_size,sector),sector_maps[sector])
        pass

    lines = cv.CreateMat(height,width,cv.CV_8U)
    cv.SetZero(lines)
    for trip in all_trips:
        for (orig,dest) in pairwise(trip.locations):
            oy=height-int(yscale*(orig.y - min_y))
            ox=int(xscale*(orig.x - min_x))
            dy=height-int(yscale*(dest.y - min_y))
            dx=int(xscale*(dest.x - min_x))
            cv.Line(lines,(ox,oy),(dx,dy),(255),1,cv.CV_AA)
    cv.SaveImage("lines.png",lines)


print "Intensity map acquired."



##
## Processing of intensity map below this line
##

def sector_count(line):
    (orig,dest)=line
    sector = getsector(orig[0],orig[1],dest[0],dest[1])
    li = cv.InitLineIterator(sector_maps[sector],orig,dest,8)
    li2 = cv.InitLineIterator(sector_maps[(sector+1)%8],orig,dest,8)
    li3 = cv.InitLineIterator(sector_maps[(sector+7)%8],orig,dest,8)
    return sum(li)+sum(li2)+sum(li3)

def draw_subdiv_facet( img, contour, edge ):
    lines = []
    t = cv.Subdiv2DGetEdge( edge, cv.CV_NEXT_AROUND_LEFT );
    last_t = None
    while t!=edge:
        assert t>4
        if t == last_t:
            break
        last_t = t
        pt = cv.Subdiv2DEdgeOrg( t );
        pt2 = cv.Subdiv2DEdgeDst( t );
        if pt==None or pt2==None: break

        line=((cv.Round(pt.pt[0]), cv.Round(pt.pt[1])) ,
              (cv.Round(pt2.pt[0]), cv.Round(pt2.pt[1])))

       # cv.Line( img, line[0], line[1], (0,255,0),1,cv.CV_AA);

        # if it's inside the top contour, check that it's not in a hole.
        # if it's in a hole, see if there's an inside shape, and so on
        def test_edge(seq,adding,level):
            if seq == None:
                return adding

            dst1=cv.PointPolygonTest(seq,pt.pt,1)
            dst2=cv.PointPolygonTest(seq,pt2.pt,1)

            if adding and dst1>0 and dst2>0:
                return False
            elif adding and (dst1>0 or dst2>0):
                return False
            elif not adding and (dst1>0 and dst2>0):
                return test_edge(seq.v_next(),adding!=True,level+1)
            else:
                return test_edge(seq.h_next(),adding,level+1)

        if pt!=pt2 and test_edge(contour,False,0):
            forward_count = sector_count(line)
            reverse_line = (line[1],line[0])
            reverse_count = sector_count(reverse_line)

            # if the count is within a factor of 4, we consider the road bi-directional
            if min(forward_count,reverse_count)>0 and max(forward_count,reverse_count) / min(forward_count,reverse_count) < 4:
                lines.append(line)
                lines.append(reverse_line)
            # if we don't have a count in either direction, the edge is probably a bit crooked.
            # include it as a bi-directional edge - it'll wash out on a long street
            elif forward_count <= MIN_DIR_COUNT and reverse_count <= MIN_DIR_COUNT:
                lines.append(line)
                lines.append(reverse_line)
            elif forward_count>reverse_count:
                lines.append(line)
            else:
                    lines.append(reverse_line)

            t = cv.Subdiv2DGetEdge( t, cv.CV_NEXT_AROUND_LEFT );

    return lines;

def shave_lines(lines):
    nmap = {}
    for line in lines:
        orig=line[0]
        dest=line[1]
        if not orig in nmap: nmap[orig]=set();
        if not dest in nmap: nmap[dest]=set();

        if orig!=dest:
            nmap[orig].add(dest);
            nmap[dest].add(orig);

    newlines = []
    for line in lines:
        if len(nmap[line[0]])>1 and len(nmap[line[1]])>1:
            newlines.append(line)
    return newlines

def paint_voronoi( subdiv, contour, img ):
    total = len(list(subdiv.edges));
    print 'processing {} edges'.format(total)
#    elem_size = subdiv.edges.elem_size;

    lines = []

    counter = 0
    for edge in subdiv.edges:
        org = (round(cv.Subdiv2DEdgeOrg(edge).pt[0]),round(cv.Subdiv2DEdgeOrg(edge).pt[1]))
        dst = (round(cv.Subdiv2DEdgeDst(edge).pt[0]),round(cv.Subdiv2DEdgeDst(edge).pt[1]))

        lines+=draw_subdiv_facet( img, contour,cv.Subdiv2DRotateEdge( edge, 1 ))
        lines+=draw_subdiv_facet( img, contour,cv.Subdiv2DRotateEdge( edge, 3 ))
        counter += 1
        if counter % 100 == 0:
            print '... do {} so far'.format(counter)

    print "Shaving lines"
    while len(lines) > 0:
        oldsize = len(lines)
        lines=shave_lines(lines)
        if len(lines)/float(oldsize) > shave_until: break
    print "Done shaving lines"

    vertex_ids={}
    vertices_by_id=[]
    vertex_id=0
    seen_lines={}
    edges = []
    f = open("kde-inferred.graph",'w')
    for line in lines:
        if line in seen_lines: continue
        else:
            seen_lines[line]=1

        cv.Line( img, line[0], line[1], (255,0,0),1,cv.CV_AA);
        if not line[0] in vertex_ids:
            vertex_ids[line[0]]=vertex_id
            vertices_by_id.append(line[0])
            vertex_id+=1
        if not line[1] in vertex_ids:
            vertex_ids[line[1]]=vertex_id
            vertices_by_id.append(line[1])
            vertex_id+=1
        edges.append((vertex_ids[line[0]], vertex_ids[line[1]]))
    for vertex in vertices_by_id:
        f.write("{} {}\n".format(vertex[0]/xscale+min_x, (height-vertex[1])/yscale+min_y))
    f.write("\n")
    for edge in edges:
        f.write("{} {}\n".format(edge[0], edge[1]))
    f.close()

# synthetic data - draw two antialiased lines and add these onto the main map

for sector in range(8):
    mask = cv.CreateMat(height,width,cv.CV_8U)
    cv.SetZero(mask)
    cv.Smooth(sector_maps[sector], sector_maps[sector], cv.CV_GAUSSIAN, gaussian_blur,gaussian_blur)
    cv.ConvertScale(sector_maps[sector],mask,1,0);
    cv.SaveImage("sector"+`sector`+".png",mask)
# # create the mask and compute the contour

mask = cv.CreateMat(height,width,cv.CV_8U)
cv.SetZero(mask)

# histogram creation
#temp = cv.CreateMat(height,width,cv.CV_32FC1) #cv.CV_8UC1)
#cv.SetZero(temp)
#cv.ConvertScale(themap,temp,40,0)
#temp2 = cv.CreateMat(height,width,cv.CV_32FC1)
#cv.SetZero(temp2)
#cv.Pow(temp,temp2,0.5)
#cv.SaveImage("histogram.png",temp2)

cv.Smooth(themap, themap, cv.CV_GAUSSIAN, gaussian_blur,gaussian_blur)
cv.SaveImage("map.png",themap)
(minval,maxval,minloc,maxloc)=cv.MinMaxLoc(themap)
print "Min: "+`minval`+" max: "+`maxval`
cv.ConvertScale(themap,mask,255.0/maxval,0);
cv.SaveImage("mask.png",mask)
cv.CmpS(themap,mask_threshold,mask,cv.CV_CMP_GT)
cv.SaveImage("thresholded.png",mask)

#contour = cv.FindContours(mask,cv.CreateMemStorage(),cv.CV_RETR_CCOMP,cv.CV_CHAIN_APPROX_SIMPLE)
chain = cv.FindContours(mask,cv.CreateMemStorage(),cv.CV_RETR_CCOMP,cv.CV_CHAIN_CODE)
contour = cv.ApproxChains(chain,cv.CreateMemStorage(),cv.CV_CHAIN_APPROX_NONE,0,100,1)

img = cv.CreateMat(height,width,cv.CV_8UC3)
cv.SetZero(img)
cv.DrawContours(img,contour,(255,255,255),(0,255,0),6,1)
cv.SaveImage("contours.png",img)

img = cv.CreateMat(height,width,cv.CV_8UC3)
cv.SetZero(img)

# # create the voronoi graph

delaunay = cv.CreateSubdivDelaunay2D((0,0,width,height),cv.CreateMemStorage())

def make_delaunay(seq):
    if seq == None: return
    i=0
    for point in seq:
        i+=1
        if i % voronoi_sampling_interval == 0:
#            cv.Circle(img,point,3,(0,255,0),1,cv.CV_AA)
            cv.SubdivDelaunay2DInsert(delaunay,point)
    make_delaunay(seq.h_next())
    make_delaunay(seq.v_next())

make_delaunay(contour)

# # draw and save the file
print "Calculating Voronoi"
cv.CalcSubdivVoronoi2D( delaunay );
print "Done calculating Voronoi"
print 'drawing contours'
cv.DrawContours(img,contour,(255,255,255),(0,0,255),6,1)
print 'painting voronoi'
paint_voronoi(delaunay,contour,img)
print 'saving image'
cv.SaveImage("voronoi.png",img)
