import numpy as np, datetime as dt
def sunpos(lat,lon,t_utc):
    jd=(t_utc-dt.datetime(2000,1,1,12))/dt.timedelta(days=1)+2451545.0
    T=(jd-2451545.0)/36525
    L0=(280.46646+T*(36000.76983+0.0003032*T))%360
    M=357.52911+T*(35999.05029-0.0001537*T)
    e=0.016708634-T*(0.000042037+0.0000001267*T)
    C=np.sin(np.radians(M))*(1.914602-T*(0.004817+0.000014*T))+np.sin(np.radians(2*M))*(0.019993-0.000101*T)+np.sin(np.radians(3*M))*0.000289
    tl=L0+C; om=125.04-1934.136*T; lam=tl-0.00569-0.00478*np.sin(np.radians(om))
    eps0=23+(26+(21.448-T*(46.815+T*(0.00059-T*0.001813)))/60)/60; eps=eps0+0.00256*np.cos(np.radians(om))
    dec=np.degrees(np.arcsin(np.sin(np.radians(eps))*np.sin(np.radians(lam))))
    y=np.tan(np.radians(eps/2))**2
    eot=4*np.degrees(y*np.sin(2*np.radians(L0))-2*e*np.sin(np.radians(M))+4*e*y*np.sin(np.radians(M))*np.cos(2*np.radians(L0))-0.5*y*y*np.sin(4*np.radians(L0))-1.25*e*e*np.sin(2*np.radians(M)))
    mins=t_utc.hour*60+t_utc.minute+t_utc.second/60
    tst=(mins+eot+4*lon)%1440; ha=tst/4-180
    la=np.radians(lat); d=np.radians(dec); h=np.radians(ha)
    zen=np.arccos(np.sin(la)*np.sin(d)+np.cos(la)*np.cos(d)*np.cos(h))
    az=(np.degrees(np.arctan2(np.sin(h),np.cos(h)*np.sin(la)-np.tan(d)*np.cos(la)))+180)%360
    return 90-np.degrees(zen), az
for lat,lon in [(60.9,11.4),(59.7,9.6),(61.3,10.5)]:
    t=dt.datetime(2026,9,25,12,0)
    while True:
        alt,az=sunpos(lat,lon,t)
        if az>=221: break
        t+=dt.timedelta(minutes=1)
    print(lat,lon,'sun az 221 at',(t+dt.timedelta(hours=2)).strftime('%H:%M CEST'),'alt %.1f'%alt)
