import sys, json, math
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magnus_model import *
dt, fly, inn, ute = load()
pts = [dict(lat=a, lon=b, sek=c, meter=d, snap=e) for a,b,c,d,e in dt]
innR = [poly[0] for poly in inn['coordinates']]
innR = [[(lat, lon) for lon, lat in ring] for ring in innR]
uteS = set(nokkel(a, b) for a, b, _ in ute)
flyAll = flypos(fly)
fly2 = flypos(fly, only={'NOZ56U','NOZ9EG'})
print('grid points', len(pts), 'fly positions all', len(flyAll), 'two planes', len(fly2))
F = [faste(p, flyAll, innR, uteS) for p in pts]
F2 = [faste(p, fly2, innR, uteS) for p in pts]
import collections
def stats(name, arr):
    a = np.array(arr); print(f'{name}: mean {a.mean():.3f} frac>=0.5 {np.mean(a>=0.5):.3f} frac==1 {np.mean(a>=0.999):.3f} frac==0 {np.mean(a<=1e-3):.3f}')
for k in ['vei','skyfri','solidag','innlandet','utelukket','defaultno','skyanalyse','bokstaver','bergen','fly']:
    stats(k, [f[k] for f in F])
stats('fly(two planes only)', [f['fly'] for f in F2])

def score(F, v):
    s = []
    for p, f in zip(pts, F):
        kj, ret = variable(p, v)
        ff = dict(f); ff['kjoretid'] = kj; ff['retning'] = ret
        x = 1
        for k in IDS:
            w = v[k]; x *= 1 - w + w*ff[k]
        s.append(x)
    s = np.array(s); rel = s/s.max() if s.max() > 0 else s*0
    return s, rel

def topp(s, rel, n=6, minKm=40):
    order = np.argsort(-s, kind='stable'); valgt = []
    for i in order:
        if rel[i] < 0.01: break
        p = (pts[i]['lat'], pts[i]['lon'])
        if all(avstand(p, (pts[j]['lat'], pts[j]['lon'])) >= minKm for j in valgt): valgt.append(i)
        if len(valgt) >= n: break
    return valgt

out = {}
for navn, v in FORHAND.items():
    for lab, FF in [('as-coded(49 planes)', F), ('two-planes-only', F2)]:
        if lab == 'two-planes-only' and v['fly'] == 0: continue
        s, rel = score(FF, v)
        cls = collections.Counter(klasse(r) for r in rel)
        t = topp(s, rel)
        print(f'\n== preset {navn} [{lab}] classes: 0(>=90%)={cls[0]} 1={cls[1]} 2={cls[2]} 3={cls[3]} hidden={cls[-1]}; best raw={s.max():.4f}')
        for i in t:
            p = pts[i]; f = FF[i]
            print(f"   {p['lat']:.2f},{p['lon']:.2f} rel={rel[i]:.3f} drive={p['sek']/3600 if p['sek'] else None:.2f}h snap={p['snap']}m flyKm={f['flyKm']:.1f} sol={f['solidag']} inn={f['innlandet']} ute={f['utelukket']:.1f}")
        # list all class-0 cells
        c0 = [i for i in range(len(pts)) if klasse(rel[i]) == 0]
        if len(c0) <= 40:
            print('   class0 cells:', [(pts[i]['lat'], pts[i]['lon']) for i in c0])
        out[f'{navn}|{lab}'] = dict(top=[(pts[i]['lat'], pts[i]['lon'], round(float(rel[i]),3)) for i in t], n_class0=cls[0], n_class1=cls[1], n_class2=cls[2], n_class3=cls[3])
json.dump(out, open('magnus_model_results.json','w'), indent=1)
