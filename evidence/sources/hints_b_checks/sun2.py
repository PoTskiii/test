import datetime as dt, math
exec(open('/home/user/test/evidence/sources/hints_b_checks/sun.py').read().split("d=dt.date(2026,9,23)")[0])
for h in (0,300,600,900):
    dip = 1.76*math.sqrt(h)/60 if h>0 else 0
    s=sunrise(61.13,11.37,dt.date(2026,9,23),-0.833-dip)
    print(f'Rena 23.09, eye height {h} m above an open sea-level-like horizon (dip {dip:.2f} deg): sunrise {(s+dt.timedelta(hours=2)).strftime("%H:%M:%S")} CEST')
for lon in (9.0,10.0,10.5,11.0,11.5,12.0,12.5):
    a,az,_,_=solpos(61.0,lon,dt.datetime(2026,9,23,11,20))
    print(f'lat 61, lon {lon}: az {az:.2f} alt {a:.2f} at 13:20 CEST 23.09')
