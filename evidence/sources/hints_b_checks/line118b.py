import math, pyproj
from shapely.geometry import LineString, Point
from pyproj import Geod
g=Geod(ellps='WGS84')
tr=pyproj.Transformer.from_crs(4326,25833,always_xy=True)
merc=pyproj.Transformer.from_crs(4326,3857,always_xy=True)
imerc=pyproj.Transformer.from_crs(3857,4326,always_xy=True)
lat0,lon0=60.3896,5.3297
places={'Odda':(60.069,6.546),'Tokke (Magnus pos)':(59.444,7.989),'Vinje sentrum':(59.568,7.993),'Seljord':(59.487,8.628),'Drangedal':(59.095,9.064),'Kragerø':(58.869,9.414),'Bennyøy':(59.2666,9.1327)}
def rhumb(b):
    x0,y0=merc.transform(lon0,lat0)
    th=math.radians(b)
    pts=[imerc.transform(x0+s*math.sin(th), y0+s*math.cos(th)) for s in range(0,900001,5000)]
    return pts
def geod(b):
    return [g.fwd(lon0,lat0,b,d)[:2] for d in range(0,450001,2000)]
for name,pts in [('rhumb118',rhumb(118)),('geod122',geod(122)),('rhumb122',rhumb(122))]:
    line=LineString([tr.transform(*p) for p in pts])
    print(name, {n: round(line.distance(Point(tr.transform(lo,la)))/1000,1) for n,(la,lo) in places.items()})
