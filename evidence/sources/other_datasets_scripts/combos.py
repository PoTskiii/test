import numpy as np
from collections import Counter
import scipy.ndimage as ndi
S = '/tmp/claude-0/-home-user-test/cdc3054c-9af4-5a32-8665-8227f802a011/scratchpad/'  # working dir for .npz intermediates (hoyde_analysis.py -> overlay.py -> combos.py/figs.py)
o = dict(np.load(S + 'overlay.npz'))
g = lambda k: o[k]
lat, lon, z, road, se = g('lat'), g('lon'), g('z'), g('road'), g('se')
b810 = (z >= 810) & (z <= 891)
inn = g('ininn'); openu = g('ucls') == 'open'; C = g('ucls') == 'C'; Rr = g('ucls') == 'R'
print('ucls among 810-891 in Innlandet:', Counter(g('ucls')[b810 & inn]))
print('fellesskap891 overlap: all pts', g('infk').sum(), ' 810-891', (g('infk') & b810).sum(), ' of 634 community cells')
print('treslag coverage among 810-891 in Inn:', (g('tcover') & b810 & inn).sum(), ' with a stored score:', (~np.isnan(g('tscore')) & b810 & inn).sum())
ts = g('tscore')
for th in [0.65, 0.75, 0.85]:
    print(f'  tscore>={th}:', (b810 & inn & (ts >= th)).sum())
print('storvilt:', (b810 & inn & g('insv')).sum())
print('vern classes:', Counter(g('vcls')[b810 & inn]))
wv = g('wv')
print('wind <2:', (b810 & inn & (wv < 2)).sum(), ' 2-4:', (b810 & inn & (wv >= 2) & (wv < 4)).sum(), ' >=4:', (b810 & inn & (wv >= 4)).sum())
dh = g('dh'); print('drive hours among 810-891 Inn pct', np.nanpercentile(dh[b810 & inn], [0, 25, 50, 75, 100]).round(2))
d56, e56, d9, e9 = g('d56'), g('e56'), g('d9'), g('e9')
dmin = np.minimum(d56, d9); emax = np.maximum(e56, e9)
for km in [3, 5, 10, 15, 20]:
    print(f'within {km} km (horiz) of NOZ56U or NOZ9EG true pos 21:28:38-21:29:23:', (b810 & (dmin <= km)).sum(), ' in Inn', (b810 & inn & (dmin <= km)).sum())
for el in [30, 45, 60, 70]:
    print(f'max elevation >= {el} deg:', (b810 & (emax >= el)).sum(), ' in Inn', (b810 & inn & (emax >= el)).sum(), ' NOZ56U', (b810 & (e56 >= el)).sum(), ' NOZ9EG', (b810 & (e9 >= el)).sum())

def summarize(m, name, top=12):
    print(f'\n=== {name}: n={m.sum()}')
    if m.sum() == 0: return
    print('  kommuner', Counter(g('kn')[m]).most_common(12))
    grid = np.zeros((int(round((lat.max() - lat.min()) / 0.005)) + 1, int(round((lon.max() - lon.min()) / 0.01)) + 1), bool)
    ii = np.round((lat - lat.min()) / 0.005).astype(int); jj = np.round((lon - lon.min()) / 0.01).astype(int)
    grid[ii[m], jj[m]] = True
    lab, n = ndi.label(grid, structure=np.ones((3, 3)))
    L = lab[ii, jj]
    print('  clusters', n)
    for l, s in Counter(L[m]).most_common(top):
        mm = m & (L == l)
        print(f'   n={s:4d} lat {lat[mm].min():.3f}-{lat[mm].max():.3f} lon {lon[mm].min():.2f}-{lon[mm].max():.2f} cen ({lat[mm].mean():.3f},{lon[mm].mean():.3f}) z {int(z[mm].min())}-{int(z[mm].max())} road med {int(np.median(road[mm]))} SE {100*se[mm].mean():.0f}% dmin {dmin[mm].min():.1f} km emax {emax[mm].max():.0f}deg tscore {np.nanmax(ts[mm]) if (~np.isnan(ts[mm])).any() else float("nan"):.2f} wind {wv[mm].mean():.1f} drive {np.nanmean(dh[mm]):.1f}h {Counter(g("kn")[mm]).most_common(2)}')

base = b810 & inn
summarize(base & openu, 'A: 810-891, Innlandet, community-map open')
summarize(base & openu & (se == 1), 'B: A + road to SE')
summarize(base & openu & (se == 1) & ~g('insv'), 'C: B + not in Statskog moose field')
summarize(base & openu & (dmin <= 15), 'D: A + within 15 km of NOZ56U/NOZ9EG true pos at pointing window')
summarize(base & (emax >= 45), 'E: 810-891 Innlandet with elevation>=45 deg to NOZ56U/NOZ9EG in window')
summarize(base & (ts >= 0.75), 'F: 810-891 Innlandet with treslag>=0.75')
summarize(base & openu & (ts >= 0.75), 'G: F + community-map open')
summarize(base & openu & (se == 1) & (ts >= 0.65) & (wv < 4) & ~g('insv'), 'H: open+SE+treslag>=0.65+wind<4+no moose field')
summarize(b810 & g('infk'), 'I: 810-891 points inside the community 800-900 map (fellesskap891)')
