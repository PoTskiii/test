"""Overlay every magnus dataset onto the hoyde891 points (790-911 moh within 900 m of road)."""
import json, gzip, datetime as dt
import numpy as np
from collections import Counter
from shapely.geometry import shape, Point
from shapely.prepared import prep
from shapely.strtree import STRtree
from shapely.validation import make_valid

D = '/home/user/test/data/raw/magnus/public/data/'
S = '/tmp/claude-0/-home-user-test/cdc3054c-9af4-5a32-8665-8227f802a011/scratchpad/'  # working dir for .npz intermediates (hoyde_analysis.py -> overlay.py -> combos.py/figs.py)
ADSB = '/home/user/test/data/raw/mk_bevis/bevis/claude-2026-09-25/adsb/'
J = lambda f: json.load(open(D + f))

h = J('hoyde891.json'); a = np.array(h['punkter'], float)
lat, lon, z, road, se = a.T
meta = np.load(S + 'hoyde_meta.npz'); ininn = meta['ininn']; kn = meta['kn']; kv = meta['kv']
N = len(a)

# utelukket (0.05 x 0.1, keyed like modell.ts utelukkNokkel)
ut = {(f"{round(x[0]/0.05)*0.05:.2f}", f"{round(x[1]/0.1)*0.1:.1f}"): x[2] for x in J('utelukket.json')['celler']}
ukey = lambda la, lo: (f"{round(la/0.05)*0.05:.2f}", f"{round(lo/0.1)*0.1:.1f}")
ucls = np.array([ut.get(ukey(y, x), 'open') for y, x in zip(lat, lon)])

# fellesskap891 (same 0.005 x 0.01 grid as hoyde891)
fk = {(round(x[0], 3), round(x[1], 2)) for x in J('fellesskap891.json')['celler']}
infk = np.array([(round(y, 3), round(x, 2)) in fk for y, x in zip(lat, lon)])

# treslag (0.02 x 0.04); nearest cell centre
t = J('treslag.json'); tc = np.array(t['celler'])
tk = {(round(r[0], 2), round(r[1], 2)): r for r in tc}
t_lat0, t_lon0 = tc[:, 0].min(), tc[:, 1].min()
def tcell(la, lo):
    i = round((la - t_lat0) / 0.02); j = round((lo - t_lon0) / 0.04)
    return tk.get((round(t_lat0 + i * 0.02, 2), round(t_lon0 + j * 0.04, 2)))
tinfo = [tcell(y, x) for y, x in zip(lat, lon)]
tscore = np.array([r[2] if r is not None else np.nan for r in tinfo])
tcover = (lat >= 59.80) & (lat <= 62.20) & (lon >= 9.80) & (lon <= 12.88)

# storvilt / verneomrader
sv = [make_valid(shape(f['geometry'])) for f in J('storvilt.json')['features']]
svt = STRtree(sv)
insv = np.array([any(sv[i].contains(Point(x, y)) for i in svt.query(Point(x, y))) for y, x in zip(lat, lon)])
vf = J('verneomrader_jakt.json')['features']; vg = [make_valid(shape(f['geometry'])) for f in vf]; vt = STRtree(vg)
def vern(la, lo):
    p = Point(lo, la); c = [vf[i]['properties']['jakt'] for i in vt.query(p) if vg[i].contains(p)]
    for k in ['forbudt', 'delvis', 'ukjent', 'tillatt']:
        if k in c: return k
    return 'none'
vcls = np.array([vern(y, x) for y, x in zip(lat, lon)])

# wind (0.2 x 0.4) nearest
w = np.array(J('vind.json')['celler'])
def wind(la, lo):
    d = (w[:, 0] - la) ** 2 + ((w[:, 1] - lo) * 0.5) ** 2; return w[np.argmin(d), 2]
wv = np.array([wind(y, x) for y, x in zip(lat, lon)])

# drive time (0.1 x 0.2) nearest
dtg = np.array([[p[0], p[1], p[2] if p[2] is not None else np.nan] for p in J('drivetime.json')['punkter']])
def drive(la, lo):
    d = (dtg[:, 0] - la) ** 2 + ((dtg[:, 1] - lo) * 0.5) ** 2; return dtg[np.argmin(d), 2] / 3600
dh = np.array([drive(y, x) for y, x in zip(lat, lon)])

# Aircraft geometry with true (trace) times. Stream 21:29:38 minus delay 15..60 s -> real 21:28:38..21:29:23 CEST
tz = dt.timezone(dt.timedelta(hours=2))
t0 = dt.datetime(2026, 9, 21, 21, 28, 38, tzinfo=tz).timestamp(); t1 = dt.datetime(2026, 9, 21, 21, 29, 23, tzinfo=tz).timestamp()
tr = {}
for cs, f in [('NOZ9EG', 'trace_4791ac.json'), ('NOZ56U', 'trace_47a3b0.json')]:
    j = json.loads(gzip.decompress(open(ADSB + f, 'rb').read()))
    T = np.array([j['timestamp'] + p[0] for p in j['trace']])
    ag = np.array([p[10] if (len(p) > 10 and p[10] is not None) else (p[3] if isinstance(p[3], (int, float)) else np.nan) for p in j['trace']])
    LA = np.array([p[1] for p in j['trace']]); LO = np.array([p[2] for p in j['trace']])
    ts = np.arange(t0, t1 + 0.1, 5.0)
    tr[cs] = np.c_[np.interp(ts, T, LA), np.interp(ts, T, LO), np.interp(ts, T, ag) * 0.3048]
R = 6371000.0
def geom(la, lo, moh, P):
    x = np.radians(P[:, 1] - lo) * np.cos(np.radians((la + P[:, 0]) / 2)) * R
    y = np.radians(P[:, 0] - la) * R
    Dh = np.hypot(x, y); hh = P[:, 2] - moh - Dh ** 2 / (2 * R)
    return Dh.min() / 1000, np.degrees(np.arctan2(hh, Dh)).max()
g56 = np.array([geom(y, x, zz, tr['NOZ56U']) for y, x, zz in zip(lat, lon, z)])
g9 = np.array([geom(y, x, zz, tr['NOZ9EG']) for y, x, zz in zip(lat, lon, z)])
dmin = np.minimum(g56[:, 0], g9[:, 0]); emax = np.maximum(g56[:, 1], g9[:, 1])

np.savez(S + 'overlay.npz', lat=lat, lon=lon, z=z, road=road, se=se, ininn=ininn, kn=kn, kv=kv, ucls=ucls, infk=infk,
         tscore=tscore, tcover=tcover, insv=insv, vcls=vcls, wv=wv, dh=dh, d56=g56[:, 0], e56=g56[:, 1], d9=g9[:, 0], e9=g9[:, 1])
print('saved')
