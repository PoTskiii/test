import sys, math
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from magnus_model import ipoly, SKYDEKKE, TAAKE, SOL_I_DAG, gauss
T = [  # id, senter, radiusKm, kjoretid, prior
 ('loten',(60.87,11.25),20,1.75,1),('rena',(61.35,11.1),35,3.2,1),('rudshogda',(60.912,10.808),10,1.95,1),
 ('ringsaker',(61.08,10.89),20,2.4,1),('solor',(60.64,11.95),20,2.55,1),('gjovik',(60.8,10.6),25,2.1,1),
 ('roros',(62.7,11.2),50,6.7,1),('valdres',(60.85,9.2),50,3.2,1),('agder',(58.65,8.8),50,3.5,1),
 ('hardanger',(60.3707,6.1453),35,6.55,1),('annet',None,0,None,4)]
def andel(t, ringer):
    _, s, r, _, _ = t
    if not s: return 1
    la, lo = s; dLat = r/111; dLon = dLat/math.cos(math.radians(la)); k=a=0
    for i in range(-7,8):
        for j in range(-7,8):
            if i*i+j*j > 49: continue
            p = (la+i/7*dLat, lo+j/7*dLon); a += 1
            if any(ipoly(p, rr) for rr in ringer): k += 1
    return k/a
tab = lambda d: (lambda t: d.get(t[0], 1))
B = [ # id, folk?, standardPa, faktor
 ('kjoretid',False,False, lambda t: 1 if t[3] is None else 0.5+0.5*gauss(t[3]-7,2)),
 ('mandag',False,False, lambda t: 0.7 if t[3] is None else (1.5 if t[3]<=2.5 else 0.8 if t[3]<=3.3 else 0.1)),
 ('blatt',False,True, lambda t: 0.7 if t[0]=='annet' else 0.05+0.95*(1-andel(t, SKYDEKKE+TAAKE))),
 ('solidag',False,True, lambda t: 0.6 if t[0]=='annet' else 0.4+1.2*andel(t, SOL_I_DAG)),
 ('soloppgang',False,True, tab(dict(rudshogda=0.95,gjovik=0.9,valdres=0.5,agder=0.4,hardanger=0.2,annet=0.7))),
 ('solmiddag',False,True, tab(dict(ringsaker=0.95,rudshogda=0.95,gjovik=0.9,valdres=0.4,agder=0.3,hardanger=0.1,annet=0.6))),
 ('froland',False,True, tab(dict(agder=0.15))),
 ('hagina-bjork',True,True, tab(dict(ringsaker=0.6,loten=1.1,rudshogda=1.1))),
 ('brumunddal',True,True, tab(dict(ringsaker=1.2,rudshogda=1.1))),
 ('discord2509',True,True, tab(dict(ringsaker=1.3,rena=1.15,solor=1.1))),
 ('regn1105',True,True, tab(dict(rena=1.4,loten=1.1,rudshogda=1.05,ringsaker=1.05))),
 ('frolandekorn',True,False, tab(dict(agder=2.5))),
 ('fjellmark',False,True, tab(dict(ringsaker=1.4,rena=1.2,roros=1.3,loten=1.0,rudshogda=0.6,gjovik=0.7,solor=0.8,agder=0.8))),
 ('bokstaver',False,True, tab(dict(hardanger=2))),
 ('fly',False,True, tab(dict(loten=3,ringsaker=2.5,rudshogda=1.6,rena=1.3,solor=0.7,gjovik=0.8,roros=0.7,valdres=0.8,agder=0.6,hardanger=0.6,annet=0.7))),
 ('defaultno',False,True, tab(dict(rena=1.5,loten=1.2,ringsaker=1.2,rudshogda=1.1,agder=1.3,valdres=1.1,roros=1.1,hardanger=0.8))),
 ('terreng',False,True, tab(dict(rena=1.5,loten=1.4,ringsaker=1.3,rudshogda=1.2,solor=1.5,gjovik=1.2,roros=1.3,agder=1.3,valdres=1.1,hardanger=0.6))),
 ('konsensus',True,True, tab(dict(loten=1.2,rena=1.2,ringsaker=1.2,rudshogda=1.2,solor=1.2,gjovik=1.2,roros=1.1,valdres=1.1))),
 ('gjovikvaer',True,True, tab(dict(gjovik=1.5))),
 ('folk_utelukket',True,True, tab(dict(rudshogda=1.0,gjovik=0.96,rena=0.94,ringsaker=0.85,loten=0.79,roros=0.28,solor=0.26,valdres=0.15,agder=0.13,hardanger=0.1,annet=0.5))),
 ('folk_digeras',True,True, tab(dict(rena=1.4,loten=1.1))),
 ('folk_flisa',True,True, tab(dict(solor=1.2))),
 ('folk_tretopp',True,True, tab(dict(ringsaker=0.8))),
 ('folk_ingenhytte',True,True, tab(dict(ringsaker=0.8))),
 ('folk_rudshogda',True,True, tab(dict(rudshogda=1.5))),
 ('stjerne',False,True, tab(dict(rudshogda=1.2))),
 ('folk_benny',True,True, tab(dict(loten=1.05))),
 ('proysen',False,True, tab(dict(rudshogda=2.2,ringsaker=1.4,loten=1.1,rena=1.05))),
 ('ekorn',False,True, tab(dict(agder=1.1,ringsaker=1.1,rudshogda=1.2))),
 ('bjorneparken',False,True, tab(dict(valdres=1.4))),
 ('bergen',False,True, tab(dict(hardanger=1.3))),
 ('skyanalyse',False,False, tab(dict(agder=2))),
 ('retning',False,False, tab(dict(valdres=1.8))),
]
def std(modus): return {b[0] for b in B if b[2] and (modus=='alt' or not b[1])}
def pct(aktive):
    raa = []
    for t in T:
        x = t[4]
        for b in B:
            if b[0] in aktive: x *= b[3](t)
        raa.append(x)
    s = sum(raa); return {t[0]: 100*r/s for t, r in zip(T, raa)}
if __name__ == '__main__':
    for t in T:
        if t[1]: print(t[0], 'andel blått+tåke', round(andel(t, SKYDEKKE+TAAKE),3), 'andel sol23.09', round(andel(t, SOL_I_DAG),3), 'blatt f', round(0.05+0.95*(1-andel(t,SKYDEKKE+TAAKE)),3), 'sol f', round(0.4+1.2*andel(t,SOL_I_DAG),3))
    def show(name, akt):
        p = pct(akt); print('\n==', name, f'({len(akt)} active)'); 
        for k, v in sorted(p.items(), key=lambda kv: -kv[1]): print(f'   {k:10s} {v:6.2f}%')
    show('ALT mode defaults (app default on load)', std('alt'))
    show('HINT mode defaults (only own-observed)', std('hint'))
    a = std('alt'); show("ALT minus 'fly' table", a - {'fly'})
    show("ALT minus all 'folk' + minus proysen/stjerne/ekorn/bjorneparken/bergen/bokstaver (symbolic)", std('hint') - {'proysen','stjerne','ekorn','bjorneparken','bergen','bokstaver'})
    show("ALT + mandag", a | {'mandag'})
    show("ALT + kjoretid", a | {'kjoretid'})
    # per-theory product of each factor under ALT
    print('\nper-factor multipliers (ALT defaults):')
    for t in T:
        fs = [(b[0], round(b[3](t),3)) for b in B if b[0] in a and abs(b[3](t)-1) > 1e-9]
        prod = t[4]
        for _, f in fs: prod *= f
        print(t[0], 'prior', t[4], 'raw product', round(prod,4), fs)
