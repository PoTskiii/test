import numpy as np
from pyproj import Geod
g=Geod(ellps='WGS84')
places={'Hamar':(60.7945,11.0680),'Elverum':(60.8819,11.5623),'Stange':(60.7154,11.1913),'Løten':(60.8176,11.3458),'Rena':(61.1348,11.3649),'Kongsvinger':(60.1905,11.9977),'OSL':(60.1976,11.1004)}
pts={'SAS50J @ ~17:21:30 (sas50j shot)':(60.5768,11.5316),'SAS50J @ ~17:21:47 (sas364 shot)':(60.6085,11.5375),
     'SAS364 @ ~17:21:47 (sas364 shot)':(61.3732,11.3647),'SAS364 @ ~17:21:30 (sas50j shot)':(61.3325,11.3645),
     'Unknown N-bound jet @17:21:30':(60.7420,11.3322),'Unknown N-bound jet @17:21:47':(60.7790,11.3316)}
for n,(la,lo) in pts.items():
    ds=[]
    for p,(pla,plo) in places.items():
        az,baz,d=g.inv(plo,pla,lo,la); ds.append((d/1000,p,az%360))
    ds.sort()
    print(n, la, lo, '; '.join('%.1f km %s of %s'%(d,('az%.0f'%az),p) for d,p,az in ds[:3]))
# ADS-B time interpolation
tr=[("17:21:03",60.5292,11.5304,20825),("17:21:21",60.561,11.5341,21525),("17:22:41",60.7043,11.5471,24100)]
def t2s(t):h,m,s=map(int,t.split(':'));return h*3600+m*60+s
def s2t(s):return '%02d:%02d:%04.1f'%(s//3600,(s%3600)//60,s%60)
for lat in (60.5768,60.6085):
    for a,b in zip(tr,tr[1:]):
        if a[1]<=lat<=b[1]:
            f=(lat-a[1])/(b[1]-a[1]); ts=t2s(a[0])+f*(t2s(b[0])-t2s(a[0])); alt=a[3]+f*(b[3]-a[3]); lon=a[2]+f*(b[2]-a[2])
            print('lat',lat,'-> ADS-B time',s2t(ts),'alt ft %.0f'%alt,'lon %.4f'%lon)
# speeds between screenshots (17 s)
for n,(p1,p2) in {'SAS50J':((60.5768,11.5316),(60.6085,11.5375)),'SAS364':((61.3325,11.3645),(61.3732,11.3647)),'unknown':((60.7420,11.3322),(60.7790,11.3316))}.items():
    az,b,d=g.inv(p1[1],p1[0],p2[1],p2[0]); print(n,'moved %.1f km az %.0f'%(d/1000,az%360),'-> %.0f m/s if 17 s'%(d/17))
# SAS364 track lon at Elverum/Løten/Rena latitudes
tk=np.load('/home/user/test/evidence/sources/whiteboard_photos_a_files/fr24-2509-sas364_track.npy')
tk=tk[(tk[:,1]>535)&(tk[:,1]<560)&(tk[:,2]>60.25)]
for lat in (60.40,60.60,60.8176,60.8819,61.0,61.1348,61.30):
    i=np.argmin(abs(tk[:,2]-lat)); lo=tk[i,3]
    print('SAS364 track at lat %.3f: lon %.3f'%(lat,lo), end=' ')
    for p in ('Elverum','Løten','Rena'):
        pla,plo=places[p]; az,b,d=g.inv(plo,pla,lo,pla); print('| %.1f km %s of %s'%(d/1000,'E' if lo>plo else 'W',p),end=' ')
    print()
