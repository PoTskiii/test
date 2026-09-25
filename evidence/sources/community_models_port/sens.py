import sys; import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magnus_model import *
import numpy as np, collections
dt, fly, inn, ute = load()
pts=[dict(lat=a,lon=b,sek=c,meter=d,snap=e) for a,b,c,d,e in dt]
innR=[[(la,lo) for lo,la in poly[0]] for poly in inn['coordinates']]
uteS=set(nokkel(a,b) for a,b,_ in ute)
FA=[faste(p,flypos(fly),innR,uteS) for p in pts]
F2=[faste(p,flypos(fly,only={'NOZ56U','NOZ9EG'}),innR,uteS) for p in pts]
# alternative epoch: default.no midpoint 21:31:28 for two planes
F3=[faste(p,flypos(fly,only={'NOZ56U','NOZ9EG'},peketid='21:31:28'),innR,uteS) for p in pts]
def run(F,v):
    s=[]
    for p,f in zip(pts,F):
        kj,ret=variable(p,v); ff=dict(f); ff['kjoretid']=kj; ff['retning']=ret; x=1
        for k in IDS: w=v[k]; x*=1-w+w*ff[k]
        s.append(x)
    s=np.array(s); rel=s/s.max(); o=np.argsort(-s)
    top=[]
    for i in o:
        if all(avstand((pts[i]['lat'],pts[i]['lon']),(pts[j]['lat'],pts[j]['lon']))>=40 for j in top): top.append(i)
        if len(top)>=5: break
    return ', '.join(f"{pts[i]['lat']:.1f},{pts[i]['lon']:.1f}({rel[i]:.2f})" for i in top), sum(rel>=0.9), sum(rel>=0.6)
base=FORHAND['fakta']
for name, F, mod in [
  ('fakta as coded', FA, {}),
  ('fakta, solidag=0', FA, {'solidag':0}),
  ('fakta, skyfri=0', FA, {'skyfri':0}),
  ('fakta, two planes only', F2, {}),
  ('fakta, two planes, solidag=0', F2, {'solidag':0}),
  ('fakta, two planes @21:31:28', F3, {}),
  ('fakta, two planes @21:31:28, solidag=0', F3, {'solidag':0}),
  ('fakta + utelukket 0.8', FA, {'utelukket':0.8}),
  ('fakta + innlandet 1', FA, {'innlandet':1}),
]:
    v=dict(base); v.update(mod); t,n9,n6=run(F,v); print(f'{name:40s} n>=0.9:{n9:3d} n>=0.6:{n6:3d} top: {t}')
