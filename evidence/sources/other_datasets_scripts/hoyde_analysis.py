import json, numpy as np
from collections import Counter, defaultdict
from shapely.geometry import shape, Point
from shapely.prepared import prep
from shapely.strtree import STRtree

D = '/home/user/test/data/raw/magnus/public/data/'
h = json.load(open(D + 'hoyde891.json'))
a = np.array(h['punkter'], dtype=float)
lat, lon, z, road, se = a.T

inn = prep(shape(json.load(open(D + 'innlandet.json'))['geometry']))
kom = json.load(open(D + 'kommunevurdering.json'))
kgeoms = [shape(f['geometry']) for f in kom['features']]
kprops = [f['properties'] for f in kom['features']]
tree = STRtree(kgeoms)

def kommune(la, lo):
    p = Point(lo, la)
    for i in tree.query(p):
        if kgeoms[i].contains(p):
            return kprops[i]['navn'], kprops[i]['v']
    return (None, None)

ininn = np.array([inn.contains(Point(x, y)) for y, x in zip(lat, lon)])
km = [kommune(y, x) for y, x in zip(lat, lon)]
kn = np.array([k[0] or '?' for k in km]); kv = np.array([k[1] or '?' for k in km])
np.savez('/tmp/claude-0/-home-user-test/cdc3054c-9af4-5a32-8665-8227f802a011/scratchpad/hoyde_meta.npz', ininn=ininn, kn=kn, kv=kv)

b810 = (z >= 810) & (z <= 891)
b800 = (z >= 800) & (z <= 900)
print('total', len(a), 'inInnlandet', ininn.sum())
print('810-891', b810.sum(), 'in Innlandet', (b810 & ininn).sum(), 'with SE road', (b810 & ininn & (se == 1)).sum())
print('800-900', b800.sum(), 'in Innlandet', (b800 & ininn).sum(), 'with SE road', (b800 & ininn & (se == 1)).sum())
for dist in [100, 250, 500, 900]:
    print(f'810-891 in Innlandet road<= {dist} m:', (b810 & ininn & (road <= dist)).sum(), ' +SE:', (b810 & ininn & (road <= dist) & (se == 1)).sum())
# Exact heights near the 3 candidate interpretations
for c in [810, 875, 891]:
    m = np.abs(z - c) <= 5
    print(f'|z-{c}|<=5:', m.sum(), 'in Innlandet', (m & ininn).sum())
print('\nTop kommuner for 810-891 (all):')
c = Counter(kn[b810])
for name, n in c.most_common(40):
    v = kv[b810][kn[b810] == name][0]
    print(f'  {name:25s} {v:16s} n={n}  inn={int((b810 & ininn & (kn==name)).sum())} SE={int((b810 & (se==1) & (kn==name)).sum())}')
print('\nkommune verdict among 810-891:', Counter(kv[b810]))
print('kommune verdict among 810-891 in Innlandet:', Counter(kv[b810 & ininn]))

# Clusters: connected components on the grid (8-neighbour), 810-891 band
import scipy.ndimage as ndi
ilat = np.round((lat - lat.min()) / 0.005).astype(int)
ilon = np.round((lon - lon.min()) / 0.01).astype(int)
grid = np.zeros((ilat.max() + 1, ilon.max() + 1), dtype=bool)
grid[ilat[b810], ilon[b810]] = True
lab, n = ndi.label(grid, structure=np.ones((3, 3)))
print('\n810-891 connected components:', n)
lbl = lab[ilat, ilon]
sizes = Counter(lbl[b810])
print('component size distribution: >=50:', sum(1 for s in sizes.values() if s >= 50), '>=10:', sum(1 for s in sizes.values() if s >= 10), 'singletons:', sum(1 for s in sizes.values() if s == 1))
print('Largest 25 components:')
for L, s in sizes.most_common(25):
    m = b810 & (lbl == L)
    names = Counter(kn[m]).most_common(3)
    print(f'  n={s:4d} lat {lat[m].min():.3f}-{lat[m].max():.3f} lon {lon[m].min():.2f}-{lon[m].max():.2f} centroid ({lat[m].mean():.3f},{lon[m].mean():.3f}) z {int(z[m].min())}-{int(z[m].max())} medRoad {int(np.median(road[m]))} SE% {100*se[m].mean():.0f} inn% {100*ininn[m].mean():.0f} kommuner {names}')

# Coarse 0.25 x 0.5 deg blocks
print('\nCoarse blocks 0.25 lat x 0.5 lon, 810-891 counts (top 30):')
bl = Counter(zip(np.floor(lat[b810] / 0.25) * 0.25, np.floor(lon[b810] / 0.5) * 0.5))
for (y, x), n in bl.most_common(30):
    print(f'  {y:.2f}-{y+0.25:.2f}N {x:.1f}-{x+0.5:.1f}E : {n}')
