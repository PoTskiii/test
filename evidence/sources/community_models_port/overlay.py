import sys, json, math
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magnus_model import *
import numpy as np
B='/home/user/test/data/raw/magnus/public/data/'
h=json.load(open(B+'hoyde891.json'))['punkter']
tre=json.load(open(B+'treslag.json')); T={(round(a,2),round(b,2)):(s,f,g,l) for a,b,s,f,g,l in tre['celler']}
vind=json.load(open(B+'vind.json'))['celler']; V={(round(a,1),round(b,1)):(v,k) for a,b,v,k in vind}
ute=json.load(open(B+'utelukket.json'))['celler']; U={nokkel(a,b):k for a,b,k in ute}
fs=set((round(a,3),round(b,3)) for a,b in json.load(open(B+'fellesskap891.json'))['celler'])
N56=(60.8132,11.2367); N9E=(61.2167,10.896); SAS50=(60.59,11.536)
def tkey(la,lo):
    # treslag grid: lat step .02 (odd hundredths e.g. 59.99,60.01), lon step .04 starting 9.82
    a=round(round((la-59.81)/0.02)*0.02+59.81,2); b=round(round((lo-9.82)/0.04)*0.04+9.82,2); return (a,b)
def vkey(la,lo):
    return (round(round(la/0.2)*0.2,1), round(round((lo-4.8)/0.4)*0.4+4.8,1))
rows=[]
for la,lo,z,vm,se in h:
    p=(la,lo)
    t=T.get(tkey(la,lo)); w=V.get(vkey(la,lo))
    d56=avstand(p,N56); d9=avstand(p,N9E)
    rows.append(dict(lat=la,lon=lo,moh=z,vei=vm,se=se,tre=t[0] if t else None,vind=w[0] if w else None,
        sky=any(ipoly(p,r) for r in SKYDEKKE+TAAKE), sol=any(ipoly(p,r) for r in SOL_I_DAG), ute=U.get(nokkel(la,lo)),
        d56=d56,d9=d9,dfly=min(d56,d9)))
print('hoyde891 cells', len(rows))
def filt(r, need_tre=0.75, maxfly=15, maxwind=4, nosky=True, noute=True, se=True):
    return (r['tre'] is not None and r['tre']>=need_tre) and r['dfly']<=maxfly and (r['vind'] is not None and r['vind']<maxwind) and (not nosky or not r['sky']) and (not noute or r['ute'] is None) and (not se or r['se']==1)
for kw in [dict(), dict(nosky=False), dict(need_tre=0.65), dict(need_tre=0.65,nosky=False), dict(maxfly=25,need_tre=0.65,nosky=False)]:
    sel=[r for r in rows if filt(r,**kw)]
    print('\nfilter',kw,'->',len(sel))
    from collections import Counter
    c=Counter((round(r['lat'],1),round(r['lon'],1)) for r in sel)
    print('  clusters (0.1deg):', sorted(c.items(), key=lambda kv:-kv[1])[:15])
    for r in sorted(sel, key=lambda r:(-r['tre'], r['dfly']))[:12]:
        print(f"   {r['lat']:.3f},{r['lon']:.3f} {r['moh']:.0f} moh vei {r['vei']:.0f} m SE={r['se']} tre {r['tre']} vind {r['vind']} dNOZ56U {r['d56']:.1f} dNOZ9EG {r['d9']:.1f} sky={r['sky']} sol={r['sol']} ute={r['ute']}")
# overlap with fellesskap891
print('\nfellesskap891 cells', len(fs))
print('with treslag value', sum(1 for r in rows if r['tre'] is not None), 'tre>=0.75', sum(1 for r in rows if (r['tre'] or 0)>=0.75), 'with vind', sum(1 for r in rows if r['vind'] is not None))
print('dfly<=15', sum(1 for r in rows if r['dfly']<=15), 'dfly<=15 & SE', sum(1 for r in rows if r['dfly']<=15 and r['se']==1))
sel=[r for r in rows if r['dfly']<=15]
from collections import Counter
print(sorted(Counter((round(r['lat'],1),round(r['lon'],1)) for r in sel).items(), key=lambda kv:-kv[1])[:20])
print('tre scores among dfly<=15:', Counter(r['tre'] for r in sel).most_common(10))
print('vind among dfly<=15:', Counter(r['vind'] for r in sel).most_common(10))
print('sky among dfly<=15:', Counter(r['sky'] for r in sel))
# tre>=0.75 cells: where?
s2=[r for r in rows if (r['tre'] or 0)>=0.75]
print('tre>=.75 clusters', sorted(Counter((round(r['lat'],1),round(r['lon'],1)) for r in s2).items(), key=lambda kv:-kv[1])[:15])
print('tre>=.75 min dfly', min(r['dfly'] for r in s2) if s2 else None)
for nm,P in [('NOZ56U@21:29:15',N56),('NOZ56U@21:29:50 FLY_PUNKT',(60.8705,11.2481)),('NOZ9EG@21:29:15',N9E),('SAS50J 25.09',SAS50),('NOZ56U@21:31:28',(61.037,11.2822))]:
    ds=sorted((avstand(P,(r['lat'],r['lon'])),r['lat'],r['lon'],r['moh']) for r in rows)
    n10=sum(1 for d in ds if d[0]<=10); n20=sum(1 for d in ds if d[0]<=20)
    print(nm,'nearest 790-911moh-near-road cell', [round(x,3) for x in ds[0]], 'n<=10km',n10,'n<=20km',n20)
print([ (r['lat'],r['lon'],r['moh'],r['vei'],r['se'],r['tre'],r['vind'],r['sky'],r['sol'],r['ute']) for r in rows if avstand((61.037,11.2822),(r['lat'],r['lon']))<=20])
