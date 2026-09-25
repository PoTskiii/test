import math, datetime as dt
def solpos(lat, lon, t_utc):
    # NOAA algorithm
    jd = (t_utc - dt.datetime(2000,1,1,12)).total_seconds()/86400 + 2451545.0
    T = (jd-2451545.0)/36525
    L0 = (280.46646 + T*(36000.76983+T*0.0003032))%360
    M = 357.52911 + T*(35999.05029-0.0001537*T)
    e = 0.016708634 - T*(0.000042037+0.0000001267*T)
    Mr=math.radians(M)
    C = math.sin(Mr)*(1.914602-T*(0.004817+0.000014*T))+math.sin(2*Mr)*(0.019993-0.000101*T)+math.sin(3*Mr)*0.000289
    tl = L0+C
    om = 125.04-1934.136*T
    lam = tl-0.00569-0.00478*math.sin(math.radians(om))
    eps0 = 23+(26+((21.448-T*(46.815+T*(0.00059-T*0.001813))))/60)/60
    eps = eps0+0.00256*math.cos(math.radians(om))
    dec = math.degrees(math.asin(math.sin(math.radians(eps))*math.sin(math.radians(lam))))
    y = math.tan(math.radians(eps/2))**2
    L0r=math.radians(L0)
    eot = 4*math.degrees(y*math.sin(2*L0r)-2*e*math.sin(Mr)+4*e*y*math.sin(Mr)*math.cos(2*L0r)-0.5*y*y*math.sin(4*L0r)-1.25*e*e*math.sin(2*Mr))
    mins = t_utc.hour*60+t_utc.minute+t_utc.second/60
    tst = mins + eot + 4*lon
    ha = tst/4-180
    latr=math.radians(lat); decr=math.radians(dec); har=math.radians(ha)
    cz = math.sin(latr)*math.sin(decr)+math.cos(latr)*math.cos(decr)*math.cos(har)
    z = math.degrees(math.acos(cz))
    az = (math.degrees(math.atan2(math.sin(har), math.cos(har)*math.sin(latr)-math.tan(decr)*math.cos(latr)))+180)%360
    return 90-z, az, eot, dec
def noon(lon, date):
    _,_,eot,_ = solpos(60, lon, dt.datetime(date.year,date.month,date.day,11,0))
    m = 720 - 4*lon - eot
    return m
def sunrise(lat, lon, date, h0=-0.833):
    # iterate minutes
    t = dt.datetime(date.year,date.month,date.day,3,0)
    prev=None
    for i in range(0,8*60*6):
        tt = t+dt.timedelta(seconds=10*i)
        a,_,_,_=solpos(lat,lon,tt)
        if a>=h0: return tt
    return None
d=dt.date(2026,9,23)
print('Solar noon CEST (23.09):')
for name,lon in [('11E',11.0),('11.5E',11.5),('12E',12.0),('Valdres 9.2',9.2),('Agder 8.3',8.3),('Hardanger 6.2',6.2),('Hardanger 6.0',6.0)]:
    m=noon(lon,d)+120
    print(f'  {name}: {int(m//60):02d}:{m%60:04.1f}')
print('Sun at 13:20 CEST 23.09:')
for name,lat,lon in [('Rena',61.13,11.37),('Løten',60.82,11.35),('Solør 60.6/12.0',60.6,12.0),('Trysil',61.31,12.26),('Ringsaker',60.9,10.9),('Valdres',61.0,9.2)]:
    a,az,_,_=solpos(lat,lon,dt.datetime(2026,9,23,11,20))
    print(f'  {name}: alt {a:.1f} az {az:.1f}')
print('Sunrise CEST (21-23.09), h0=-0.833:')
for name,lat,lon in [('Solør/Flisa',60.61,12.01),('Kongsvinger',60.19,12.0),('Løten',60.82,11.35),('Rena',61.13,11.37),('Røros',62.57,11.38),('Ringsaker/Brumunddal',60.88,10.94),('Rudshøgda',60.91,10.81),('Valdres/Fagernes',60.99,9.23),('Agder/Evje',58.59,7.8),('Agder/Froland',58.53,8.63),('Hardanger/Norheimsund',60.37,6.15),('Digeråsen',61.1788,11.2639)]:
    out=[]
    for day in (21,22,23):
        s=sunrise(lat,lon,dt.date(2026,9,day))
        s2=s+dt.timedelta(hours=2)
        out.append(s2.strftime('%H:%M:%S'))
    print(f'  {name}: '+' '.join(out))
