"""Faithful Python port of MagnusPladsen/hordejakten-2026 src/lib/modell.ts + src/data/teorier.ts
(commit 68faa86, 2026-09-25 21:04). Used to reproduce the probability grid and theory percentages."""
import json, math, sys
import numpy as np
R = 6371.0
ROOT = '/home/user/test/data/raw/magnus'
rad = math.radians; deg = math.degrees

def avstand(a, b):
    la1, lo1 = a; la2, lo2 = b
    dphi = rad(la2-la1); dl = rad(lo2-lo1)
    x = math.sin(dphi/2)**2 + math.cos(rad(la1))*math.cos(rad(la2))*math.sin(dl/2)**2
    return 2*R*math.asin(min(1, math.sqrt(x)))

def peiling(a, b):
    la1, lo1 = a; la2, lo2 = b
    p1, p2 = rad(la1), rad(la2); dl = rad(lo2-lo1)
    y = math.sin(dl)*math.cos(p2); x = math.cos(p1)*math.sin(p2) - math.sin(p1)*math.cos(p2)*math.cos(dl)
    return (deg(math.atan2(y, x)) + 360) % 360

def tvers(fra, kurs, p):
    d13 = avstand(fra, p)/R; t13 = rad(peiling(fra, p)); t12 = rad(kurs)
    xt = math.asin(math.sin(d13)*math.sin(t13-t12))
    at = math.acos(max(-1, min(1, math.cos(d13)/math.cos(xt))))
    return abs(xt)*R, (1 if math.cos(t13-t12) >= 0 else -1)*at*R

def ipoly(p, ring):
    la, lo = p; inne = False; j = len(ring)-1
    for i in range(len(ring)):
        yi, xi = ring[i]; yj, xj = ring[j]
        if (yi > la) != (yj > la) and lo < (xj-xi)*(la-yi)/(yj-yi)+xi: inne = not inne
        j = i
    return inne

gauss = lambda x, s: math.exp(-0.5*(x/s)**2)
OSLO = (59.9139, 10.7522); BERGEN = (60.3896, 5.3297)
SOL_I_DAG = [
 [[60.1, 11.85], [60.5, 11.6], [60.88, 11.35], [61.15, 11.2], [61.3, 11.35], [61.3, 12.1], [61.0, 12.45], [60.6, 12.6], [60.2, 12.55], [60.0, 12.2]],
 [[59.05, 9.95], [59.1, 10.55], [59.6, 10.45], [59.65, 10.0], [59.35, 9.8]],
 [[62.3, 5.9], [62.8, 6.2], [63.2, 8.0], [63.55, 10.0], [63.5, 10.7], [63.2, 10.6], [62.9, 9.0], [62.5, 7.2], [62.2, 6.3]]]
TAAKE = [[[60.1, 11.05], [60.08, 11.4], [60.18, 11.75], [60.3, 11.85], [60.48, 11.75], [60.5, 11.4], [60.35, 11.15], [60.2, 11.0]]]
SKYDEKKE = [
 [[63.685, 7.743], [63.766, 9.107], [63.966, 10.32], [64.119, 11.305], [63.953, 11.835], [63.618, 11.532], [63.347, 10.926], [63.074, 10.244], [62.833, 9.789], [62.449, 9.531], [62.061, 9.486], [61.704, 9.41], [61.379, 9.183], [61.087, 9.259], [60.867, 9.107], [60.607, 8.652], [60.533, 8.046], [60.346, 7.516], [60.044, 7.212], [59.664, 6.985], [59.279, 6.864], [58.889, 6.833], [58.574, 7.137], [58.336, 7.591], [58.177, 7.819], [58.017, 7.288], [58.257, 6.379], [58.653, 5.621], [59.356, 4.863], [60.421, 4.56], [61.452, 4.636], [62.309, 5.166], [63.074, 6.227], [63.483, 7.137]],
 [[60.94, 10.092], [61.014, 10.547], [61.596, 11.229], [62.168, 11.835], [62.729, 12.366], [63.347, 12.82], [63.719, 12.896], [63.739, 12.563], [63.005, 12.108], [62.379, 11.608], [61.812, 11.002], [61.233, 10.32], [61.051, 9.941]]]
NORHEIMSUND = (60.3707, 6.1453)
SKYANALYSE = (58.7, 8.27)
DEFAULTNO = [(60.9, 11.2), (61.3, 11.2), (61.5, 11.0), (60.6, 12.35), (61.3, 12.3)]

def jsround(x): return math.floor(x + 0.5)
def nokkel(lat, lon): return f"{jsround(lat/0.05)*0.05:.2f},{jsround(lon/0.1)*0.1:.1f}"

def hms2s(h):
    t, m, s = map(int, h.split(':')); return t*3600+m*60+s

def load():
    dt = json.load(open(f'{ROOT}/public/data/drivetime.json'))['punkter']
    fly = json.load(open(f'{ROOT}/public/data/fly_2130.json'))
    inn = json.load(open(f'{ROOT}/public/data/innlandet.json'))['geometry']
    ute = json.load(open(f'{ROOT}/public/data/utelukket.json'))['celler']
    return dt, fly, inn, ute

def flypos(fly, only=None, peketid='21:29:15', vindu=60):
    midt = hms2s(peketid); out = []
    for f in fly['fly']:
        if only and f['kallesignal'] not in only: continue
        s = f['spor']
        for t in range(midt-vindu, midt+vindu+1, 10):
            for i in range(len(s)-1):
                a, b = hms2s(s[i][0]), hms2s(s[i+1][0])
                if a <= t <= b:
                    fr = 0 if b == a else (t-a)/(b-a)
                    pos = (s[i][1]+fr*(s[i+1][1]-s[i][1]), s[i][2]+fr*(s[i+1][2]-s[i][2]))
                    fot = s[i][3]+fr*(s[i+1][3]-s[i][3])
                    if fot > 3000: out.append(pos)
                    break
    return out

def faste(p, flyP, innR, uteS):
    pos = (p['lat'], p['lon'])
    vei = 1 if p['snap'] <= 1500 else math.exp(-(p['snap']-1500)/2000)
    skyfri = 0 if any(ipoly(pos, r) for r in SKYDEKKE+TAAKE) else 1
    bokstaver = gauss(avstand(pos, NORHEIMSUND), 20)
    tv, la = tvers(BERGEN, 118, pos)
    bergen = gauss(tv, max(8, la*math.tan(rad(5)))) if la > 0 else 0
    skyanalyse = gauss(avstand(pos, SKYANALYSE), 35)
    defaultno = max(gauss(avstand(pos, k), 25) for k in DEFAULTNO)
    flyKm = min((avstand(pos, f) for f in flyP), default=math.inf)
    fly = gauss(flyKm, 10) if flyP else 1
    solidag = 1 if any(ipoly(pos, r) for r in SOL_I_DAG) else 0
    innlandet = (1 if any(ipoly(pos, r) for r in innR) else 0) if innR else 1
    ute = 1
    if uteS:
        nb = [(0,0),(0.05,0),(-0.05,0),(0,0.1),(0,-0.1)]
        n = sum(1 for a,b in nb if nokkel(p['lat']+a, p['lon']+b) in uteS)
        ute = 1 - n/len(nb)
    return dict(vei=vei, skyfri=skyfri, skyanalyse=skyanalyse, defaultno=defaultno, fly=fly, bokstaver=bokstaver,
                innlandet=innlandet, solidag=solidag, bergen=bergen, utelukket=ute, flyKm=flyKm)

def variable(p, v):
    kj = 0 if p['sek'] is None else gauss(p['sek']/3600 - v['timer'], v['slingring'])
    ret = 0
    for kurs in ([298, 118] if v['retningBegge'] else [298]):
        tv, la = tvers(OSLO, kurs, (p['lat'], p['lon']))
        if la <= 0: continue
        ret = max(ret, gauss(tv, max(8, la*math.tan(rad(5)))))
    return kj, ret

IDS = ['vei','skyfri','skyanalyse','defaultno','fly','bokstaver','innlandet','solidag','bergen','utelukket','kjoretid','retning']
FORHAND = {
 'fakta': dict(kjoretid=0, timer=7, slingring=2, vei=0.8, skyfri=1, retning=0, retningBegge=False, skyanalyse=0, defaultno=0, fly=0.7, bokstaver=0, innlandet=0, solidag=0.5, bergen=0, utelukket=0),
 'alt': dict(kjoretid=0, timer=7, slingring=2, vei=0.8, skyfri=1, retning=0, retningBegge=False, skyanalyse=0, defaultno=0.3, fly=0.6, bokstaver=0, innlandet=0.5, solidag=0.4, bergen=0, utelukket=0.8),
 'innlandet': dict(kjoretid=0, timer=5, slingring=2.5, vei=0.8, skyfri=1, retning=0, retningBegge=False, skyanalyse=0, defaultno=0.3, fly=0.5, bokstaver=0, innlandet=1, solidag=0.7, bergen=0, utelukket=0),
 'norheimsund': dict(kjoretid=0, timer=7, slingring=1.5, vei=0.8, skyfri=0, retning=0, retningBegge=False, skyanalyse=0, defaultno=0, fly=0, bokstaver=1, innlandet=0, solidag=0, bergen=0, utelukket=0),
 'retning': dict(kjoretid=0.3, timer=7, slingring=1.5, vei=0.8, skyfri=1, retning=0.9, retningBegge=False, skyanalyse=0, defaultno=0, fly=0, bokstaver=0, innlandet=0, solidag=0, bergen=0, utelukket=0),
 'fly': dict(kjoretid=0, timer=5, slingring=2, vei=0.8, skyfri=1, retning=0, retningBegge=False, skyanalyse=0, defaultno=0, fly=1, bokstaver=0, innlandet=0, solidag=0.7, bergen=0, utelukket=0),
 'kort': dict(kjoretid=1, timer=4, slingring=1, vei=0.8, skyfri=1, retning=0, retningBegge=False, skyanalyse=0, defaultno=0.4, fly=0, bokstaver=0, innlandet=0, solidag=0, bergen=0, utelukket=0),
 'agder': dict(kjoretid=0, timer=4, slingring=1.5, vei=0.8, skyfri=1, retning=0, retningBegge=False, skyanalyse=0.9, defaultno=0, fly=0, bokstaver=0, innlandet=0, solidag=0, bergen=0, utelukket=0),
 'defaultno': dict(kjoretid=0, timer=3.5, slingring=2, vei=0.8, skyfri=1, retning=0, retningBegge=False, skyanalyse=0, defaultno=1, fly=0, bokstaver=0, innlandet=0, solidag=0, bergen=0, utelukket=0),
}

def klasse(r):
    return 0 if r >= 0.9 else 1 if r >= 0.6 else 2 if r >= 0.35 else 3 if r >= 0.15 else -1
