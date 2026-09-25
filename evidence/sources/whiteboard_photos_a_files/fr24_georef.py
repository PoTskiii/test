from PIL import Image
import numpy as np
R=6378137.0
def merc(lat,lon):
    return np.radians(lon)*R, np.log(np.tan(np.pi/4+np.radians(lat)/2))*R
def inv(mx,my):
    return np.degrees(2*np.arctan(np.exp(my/R))-np.pi/2), np.degrees(mx/R)
towns={'rena':(61.1348,11.3649),'elverum':(60.8819,11.5623),'gjovik':(60.7957,10.6916),'biri':(60.9571,10.6143),
       'kongsv':(60.1905,11.9977),'drammen':(59.7439,10.2045),'beito':(61.2466,8.9097)}
px={'fr24-2509-sas364.jpg':{'rena':(545.7,191.3),'elverum':(580.6,285.9),'gjovik':(418.6,319.7),'biri':(411.0,257.2),'kongsv':(658.9,536.5),'drammen':(335.1,696.6),'beito':(106.4,150.1)},
    'fr24-2509-sas50j.jpg':{'rena':(485.8,161.1),'elverum':(527.8,269.5),'gjovik':(340.8,308.7),'biri':(323.3,236.3),'kongsv':(616.8,562.9)}}
res={}
for f,P in px.items():
    names=list(P)
    M=np.array([merc(*towns[n]) for n in names]); X=np.array([P[n] for n in names])
    # similarity fit: x = s*mx + tx ; y = -s*my + ty
    A=[];b=[]
    for (mx,my),(x,y) in zip(M,X):
        A.append([mx,1,0]); b.append(x)
        A.append([-my,0,1]); b.append(y)
    sol,*_=np.linalg.lstsq(np.array(A),np.array(b),rcond=None)
    s,tx,ty=sol
    pred=np.c_[s*M[:,0]+tx, -s*M[:,1]+ty]
    print(f,'scale m/px',1/s,'resid px',np.round(np.hypot(*(pred-X).T),1))
    res[f]=(s,tx,ty)
    a=np.asarray(Image.open(f).convert('RGB')).astype(int)
    r,g,bb=a[...,0],a[...,1],a[...,2]
    red=(r>200)&(g<110)&(bb<110)
    ys,xs=np.where(red)
    cx,cy=xs.mean(),ys.mean()
    lat,lon=inv((cx-tx)/s,-(cy-ty)/s)
    print(' red icon centroid px',round(cx,1),round(cy,1),'->',round(lat,4),round(lon,4),'n',len(xs), 'bbox',xs.min(),xs.max(),ys.min(),ys.max())
    # track pixels: bluish/cyan/green line: saturated, b or g high, not yellow planes
    trk=((bb>180)&(r<120)&(g<200)) | ((g>200)&(r<120)&(bb>100))
    ys,xs=np.where(trk)
    rows={}
    for x,y in zip(xs,ys): rows.setdefault(y,[]).append(x)
    out=[]
    for y in sorted(rows):
        xm=np.mean(rows[y]); lat,lon=inv((xm-tx)/s,-(y-ty)/s)
        out.append((y,xm,lat,lon))
    out=np.array(out)
    for q in out[::15]: print('  track y=%d x=%.1f lat=%.4f lon=%.4f'%tuple(q))
    np.save('/home/user/test/evidence/sources/whiteboard_photos_a_files/'+f[:-4]+'_track.npy',out)

from scipy import ndimage
print('--- yellow planes')
for f,(s,tx,ty) in res.items():
    a=np.asarray(Image.open(f).convert('RGB')).astype(int)
    r,g,bb=a[...,0],a[...,1],a[...,2]
    yel=(r>200)&(g>170)&(bb<90)
    lab,n=ndimage.label(yel)
    for i in range(1,n+1):
        ys,xs=np.where(lab==i)
        if len(xs)<25: continue
        cx,cy=xs.mean(),ys.mean()
        lat,lon=inv((cx-tx)/s,-(cy-ty)/s)
        print(f[10:16],'px(%.0f,%.0f) n=%d -> %.4f N %.4f E'%(cx,cy,len(xs),lat,lon))
print('--- dim yellow top plane in sas50j')
f='fr24-2509-sas50j.jpg'; s,tx,ty=res[f]
a=np.asarray(Image.open(f).convert('RGB')).astype(int)
w=a[50:105,455:515]; r,g,bb=w[...,0],w[...,1],w[...,2]
m=(r>140)&(g>120)&(bb<80)
ys,xs=np.where(m); cx,cy=455+xs.mean(),50+ys.mean()
print('px',cx,cy,len(xs), inv((cx-tx)/s,-(cy-ty)/s))
# icon orientation via PCA
X=np.c_[xs-xs.mean(),ys-ys.mean()]
