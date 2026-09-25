import sys, json, math
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magnus_model import *
import numpy as np
dt, fly, inn, ute = load()
pts = [dict(lat=a, lon=b, sek=c, meter=d, snap=e) for a,b,c,d,e in dt]
innR = [[(lat, lon) for lon, lat in poly[0]] for poly in inn['coordinates']]
uteS = set(nokkel(a, b) for a, b, _ in ute)
uteD = {nokkel(a,b):k for a,b,k in ute}
flyAll = flypos(fly)
F = [faste(p, flyAll, innR, uteS) for p in pts]
def score(v):
    s=[]
    for p,f in zip(pts,F):
        kj, ret = variable(p, v); ff=dict(f); ff['kjoretid']=kj; ff['retning']=ret; x=1
        for k in IDS: w=v[k]; x*=1-w+w*ff[k]
        s.append(x)
    s=np.array(s); return s/s.max()
REL = {k: score(v) for k, v in FORHAND.items()}
tre = json.load(open('/home/user/test/data/raw/magnus/public/data/treslag.json'))['celler']
vind = json.load(open('/home/user/test/data/raw/magnus/public/data/vind.json'))['celler']
h891 = json.load(open('/home/user/test/data/raw/magnus/public/data/hoyde891.json'))['punkter']
fs891 = json.load(open('/home/user/test/data/raw/magnus/public/data/fellesskap891.json'))['celler']
H = np.array(h891)
def near(arr, p, dl, dn):
    best=None; bd=1e9
    for c in arr:
        if abs(c[0]-p[0])<=dl and abs(c[1]-p[1])<=dn:
            d=avstand(p,(c[0],c[1]))
            if d<bd: bd=d; best=c
    return best
P = {
 'Digeråsen tip': (61.1788, 11.2639), 'Kroktjennet ~891 moh': (61.2405, 11.01), 'Birkebeinervegen (retracted)': (61.36168, 10.84625),
 'Birkebeinerveien terrain hit (retracted)': (61.4495, 10.9752), 'Prøysenstua': (60.912, 10.8076), 'Tretopphyttene': (60.9748, 10.9167),
 'Benningstad': (60.7685, 11.3575), 'Haslemoen': (60.66, 11.87), 'NOZ56U at FLY_PUNKT': (60.8705, 11.2481), 'NOZ9EG at FLY_PUNKT2': (61.216, 10.896),
 'SAS50J 25.09 17:22': (60.59, 11.536), 'Gålaveien (dn terrain)': (61.4725, 10.9677), 'Madsskardveien (dn terrain)': (61.4747, 11.0966),
 'Tolvmilskogen (dn)': (60.69, 12.35), 'Jomfrua/Tjuven/Danseren': (61.2279, 10.90754), 'Texas, Våler': (60.87812, 12.21229),
 'default.no fusion #1 alle (61.45,11.1)': (61.45, 11.1), 'fellesskap891 centroid': tuple(np.mean(np.array(fs891),axis=0)),
}
for name, p in P.items():
    i = min(range(len(pts)), key=lambda i: avstand(p,(pts[i]['lat'],pts[i]['lon'])))
    g = pts[i]; f = F[i]
    t = near(tre, p, 0.02, 0.04); w = near(vind, p, 0.2, 0.4)
    nh = sum(1 for c in h891 if avstand(p,(c[0],c[1]))<=5)
    nhs = sum(1 for c in h891 if c[4]==1 and avstand(p,(c[0],c[1]))<=5)
    sky = any(ipoly(p,r) for r in SKYDEKKE+TAAKE); sol = any(ipoly(p,r) for r in SOL_I_DAG)
    uk = uteD.get(nokkel(*p))
    print(f"{name:40s} ({p[0]:.4f},{p[1]:.4f}) cell {g['lat']:.1f},{g['lon']:.1f} drive {g['sek']/3600:.2f}h snap {g['snap']}m | rel fakta {REL['fakta'][i]:.2f} alt {REL['alt'][i]:.2f} innl {REL['innlandet'][i]:.2f} fly {REL['fly'][i]:.2f} | flyKm {f['flyKm']:.1f} | point: windyBlue={sky} sol23={sol} utelukket={uk} | treslag {t[2] if t else None} (furu {t[3] if t else '-'} gran {t[4] if t else '-'} lauv {t[5] if t else '-'}) | wind1749 {w[2] if w else None} m/s | h891 cells<=5km {nh} (SE-road {nhs})")
