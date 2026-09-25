import json, math
d=json.load(open('/home/user/test/data/raw/magnus/public/data/fly_2130.json'))
tr={f['kallesignal']:f['spor'] for f in d['fly']}
def ts(s):
    h,m,x=map(int,s.split(':')); return h*3600+m*60+x
def pos(cs,t):
    sp=tr[cs]
    for a,b in zip(sp,sp[1:]):
        ta,tb=ts(a[0]),ts(b[0])
        if ta<=t<=tb:
            f=(t-ta)/(tb-ta)
            return [a[i]+f*(b[i]-a[i]) for i in (1,2,3)]
    return None
def dist(p,q):
    R=6371.0
    la1,lo1,la2,lo2=map(math.radians,(p[0],p[1],q[0],q[1]))
    a=math.sin((la2-la1)/2)**2+math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2*R*math.asin(math.sqrt(a))
def bearing(p,q):
    la1,lo1,la2,lo2=map(math.radians,(p[0],p[1],q[0],q[1]))
    y=math.sin(lo2-lo1)*math.cos(la2); x=math.cos(la1)*math.sin(la2)-math.sin(la1)*math.cos(la2)*math.cos(lo2-lo1)
    return (math.degrees(math.atan2(y,x))+360)%360
def elev(site,p):
    dk=dist(site,p); hk=p[2]*0.3048/1000
    return math.degrees(math.atan2(hk,dk))
sites={'Digeråsen':(61.1788,11.2639),'Tretopphyttene':(60.9748,10.9167),'Prøysenstua':(60.912,10.8076),'Haslemoen/Flisa':(60.66,11.87),'Nittedalen':(60.07,10.87),'Benningstad':(60.7685,11.3575),'FLY_PUNKT':(60.8705,11.2481),'Løten sentrum':(60.818,11.337)}
for label,t in [('point 21:28:53 (45s delay)',ts('21:28:53')),('point 21:28:38 (60s)',ts('21:28:38')),('point 21:29:18 (20s)',ts('21:29:18')),('21:29:50',ts('21:29:50')),('21:31:00',ts('21:31:00')),('21:32:50',ts('21:32:50'))]:
    print('==',label)
    for cs in ('NOZ56U','NOZ9EG'):
        p=pos(cs,t)
        print(f'  {cs} at {p[0]:.4f},{p[1]:.4f} {p[2]:.0f} ft')
        for s,q in sites.items():
            print(f'     {s}: {dist(q,p):.1f} km, elev {elev(q,p):.1f} deg, bearing from site {bearing(q,p):.0f}')
# min distance of NOZ9EG from tretopp / proysen across track
import numpy as np
for cs in ('NOZ56U','NOZ9EG'):
    for s,q in sites.items():
        best=min(((dist(q,pos(cs,t)),t) for t in range(ts('21:28:14'),ts('21:34:17'))),key=lambda x:x[0])
        h=best[1]; print(f'min {cs}-{s}: {best[0]:.1f} km at {h//3600:02d}:{h%3600//60:02d}:{h%60:02d}')
