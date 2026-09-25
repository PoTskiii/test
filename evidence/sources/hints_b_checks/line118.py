from pyproj import Geod
from shapely.geometry import LineString, Point
import pyproj
g=Geod(ellps='WGS84')
lat0,lon0=60.3896,5.3297
pts=[]
for d in range(0,400001,2000):
    lon,lat,_=g.fwd(lon0,lat0,118,d); pts.append((lon,lat))
# project to UTM33
tr=pyproj.Transformer.from_crs(4326,25833,always_xy=True)
line=LineString([tr.transform(*p) for p in pts])
places={'Odda':(60.069,6.546),'Tokke (2023, Magnus pos)':(59.444,7.989),'Vinje sentrum':(59.568,7.993),'Seljord':(59.487,8.628),'Drangedal':(59.095,9.064),'Kragerø':(58.869,9.414),'Bennyøy (Magnus pos)':(59.2666,9.1327),'Rjukan':(59.878,8.594)}
for n,(la,lo) in places.items():
    p=Point(tr.transform(lo,la)); print(f'{n}: {line.distance(p)/1000:.1f} km from 118deg geodesic from Bergen')
# where does line hit coast lat ~58.87?
for d in range(300000,400001,10000):
    lon,lat,_=g.fwd(lon0,lat0,118,d); print(d/1000, round(lat,3), round(lon,3))
