import json, gzip, datetime as dt
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection

D = '/home/user/test/data/raw/magnus/public/data/'
S = '/tmp/claude-0/-home-user-test/cdc3054c-9af4-5a32-8665-8227f802a011/scratchpad/'  # working dir for .npz intermediates (hoyde_analysis.py -> overlay.py -> combos.py/figs.py)
OUT = '/home/user/test/evidence/sources/other_datasets_figs/'
import os; os.makedirs(OUT, exist_ok=True)
ADSB = '/home/user/test/data/raw/mk_bevis/bevis/claude-2026-09-25/adsb/'
J = lambda f: json.load(open(D + f))
o = dict(np.load(S + 'overlay.npz'))
lat, lon, z, se, ucls = o['lat'], o['lon'], o['z'], o['se'], o['ucls']
b810 = (z >= 810) & (z <= 891)

INK, INK2, GRID = '#0b0b0b', '#52514e', '#d9d8d3'
BLUE, ORANGE, AQUA, RED = '#2a78d6', '#eb6834', '#1baf7a', '#e34948'
plt.rcParams.update({'font.size': 9, 'axes.edgecolor': GRID, 'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2})

def outline(ax, f, **kw):
    g = J(f)['geometry']
    for poly in g['coordinates']:
        r = np.array(poly[0]); ax.plot(r[:, 0], r[:, 1], **kw)

tz = dt.timezone(dt.timedelta(hours=2))
def trace(fn):
    j = json.loads(gzip.decompress(open(ADSB + fn, 'rb').read()))
    T = np.array([j['timestamp'] + p[0] for p in j['trace']])
    return T, np.array([p[1] for p in j['trace']]), np.array([p[2] for p in j['trace']])
tr = {'NOZ9EG': trace('trace_4791ac.json'), 'NOZ56U': trace('trace_47a3b0.json')}
ts = lambda h, m, s: dt.datetime(2026, 9, 21, h, m, s, tzinfo=tz).timestamp()
fly = {f['kallesignal']: f for f in J('fly_2130.json')['fly']}

# ---------- Figure 1: overview ----------
fig, ax = plt.subplots(figsize=(8.5, 8.5))
cells = [Rectangle((x[1] - 0.05, x[0] - 0.025), 0.1, 0.05) for x in J('utelukket.json')['celler'] if x[2] == 'R']
ax.add_collection(PatchCollection(cells, facecolor='#f3d6d5', edgecolor='none', zorder=0))
cells = [Rectangle((x[1] - 0.05, x[0] - 0.025), 0.1, 0.05) for x in J('utelukket.json')['celler'] if x[2] == 'C']
ax.add_collection(PatchCollection(cells, facecolor='#d3eef3', edgecolor='none', zorder=0))
outline(ax, 'norge.json', color=INK2, lw=0.6, zorder=1)
outline(ax, 'innlandet.json', color=INK, lw=1.4, ls='--', zorder=3)
m = b810 & (ucls != 'open')
ax.scatter(lon[m], lat[m], s=1.2, c='#a8a7a1', lw=0, zorder=2, label='810–891 moh ≤900 m from road, community-excluded cell')
m = b810 & (ucls == 'open')
ax.scatter(lon[m], lat[m], s=1.6, c=BLUE, lw=0, zorder=2, label='810–891 moh ≤900 m from road, community-map open')
fk = np.array(J('fellesskap891.json')['celler'])
ax.scatter(fk[:, 1], fk[:, 0], s=2, c=ORANGE, marker='s', lw=0, zorder=4, label='fellesskap891 (community 800–900 moh map)')
for cs, (T, LA, LO) in tr.items():
    w = (T > ts(21, 26, 0)) & (T < ts(21, 36, 0))
    ax.plot(LO[w], LA[w], color=INK, lw=1.2, zorder=5)
    t = ts(21, 29, 16); ax.plot(np.interp(t, T, LO), np.interp(t, T, LA), 'o', ms=6, mfc=INK, mec='white', zorder=6)
    ax.annotate(f'{cs}\n21:29:16 (true)', (np.interp(t, T, LO), np.interp(t, T, LA)), xytext=(6, 4), textcoords='offset points', fontsize=8, color=INK)
for cs in ['NOZ68L', 'WIF149']:
    s = np.array([[p[1], p[2]] for p in fly[cs]['spor']])
    ax.plot(s[:, 1], s[:, 0], color=INK2, lw=0.9, ls=':', zorder=5)
    ax.annotate(cs, (s[0, 1], s[0, 0]), xytext=(4, -10), textcoords='offset points', fontsize=8, color=INK2)
ax.set_xlim(8.3, 12.9); ax.set_ylim(59.7, 62.9); ax.set_aspect(1 / np.cos(np.radians(61.3)))
ax.grid(color=GRID, lw=0.4); ax.set_xlabel('Longitude (°E)'); ax.set_ylabel('Latitude (°N)')
ax.set_title('hoyde891 810–891 moh points vs community maps and ADS-B\n'
             'pink = utelukket R, cyan = C (fjellbjørk); dashed = Innlandet;\nblack = adsb.lol traces 21:26–21:36; dotted = fly_2130 NOZ68L, WIF149',
             fontsize=9, color=INK, loc='left')
leg = ax.legend(loc='lower right', fontsize=7.5, markerscale=5, frameon=True)
leg.get_frame().set_edgecolor(GRID)
fig.tight_layout(); fig.savefig(OUT + 'fig1_overview.png', dpi=150); plt.close(fig)

# ---------- Figure 2: NOZ9EG corridor zoom ----------
fig, ax = plt.subplots(figsize=(8, 7.5))
box = (lat > 61.05) & (lat < 61.55) & (lon > 10.55) & (lon < 11.25)
m = box & b810 & (se == 0)
ax.scatter(lon[m], lat[m], s=10, facecolor='white', edgecolor=BLUE, lw=0.8, zorder=2, label='810–891 moh, no road to SE (se=0)')
m = box & b810 & (se == 1)
ax.scatter(lon[m], lat[m], s=10, c=BLUE, lw=0, zorder=2, label='810–891 moh, road to SE (se=1)')
m = (fk[:, 0] > 61.05) & (fk[:, 1] > 10.55)
ax.scatter(fk[m, 1], fk[m, 0], s=14, c=ORANGE, marker='s', alpha=0.55, lw=0, zorder=1, label='fellesskap891 cell')
T, LA, LO = tr['NOZ9EG']
w = (T > ts(21, 27, 30)) & (T < ts(21, 31, 30))
ax.plot(LO[w], LA[w], color=INK, lw=1.4, zorder=4, label='NOZ9EG full-res trace (adsb.lol)')
for sec, lab in [(38, '21:28:38 (60 s delay)'), (53, '21:28:53 (45 s)'), (76, '21:29:16 (22 s)'), (83, '21:29:23 (15 s)')]:
    t = ts(21, 28, 0) + sec
    x, y = np.interp(t, T, LO), np.interp(t, T, LA)
    ax.plot(x, y, 'o', ms=6, mfc=INK, mec='white', zorder=6)
    ax.annotate(lab, (x, y), xytext=(8, 0), textcoords='offset points', fontsize=8, color=INK, va='center')
first = True
for p in fly['NOZ9EG']['spor'][:2]:
    ax.plot(p[2], p[1], 'x', ms=8, mew=2, color=RED, zorder=7, label='fly_2130.json NOZ9EG sample (label time)' if first else None); first = False
    h, mi, se_ = map(int, p[0].split(':')); true = dt.datetime(2026, 9, 21, h, mi, se_) + dt.timedelta(seconds=46)
    ax.annotate(f"label {p[0]}\n= true ~{true.strftime('%H:%M:%S')}", (p[2], p[1]), xytext=(-12, 0), textcoords='offset points', fontsize=7.5, color=RED, va='center', ha='right')
# 60-degree radius ring at 22 s delay (~4.6 km)
t = ts(21, 29, 16); cx, cy = np.interp(t, T, LO), np.interp(t, T, LA)
th = np.linspace(0, 2 * np.pi, 200); r = 4.6
ax.plot(cx + r / (111.32 * np.cos(np.radians(cy))) * np.cos(th), cy + r / 111.32 * np.sin(th), color=INK2, lw=0.8, ls=':', zorder=3)
ax.annotate('≥60° elevation\nring (22 s delay)', (cx + 0.03, cy - 0.075), fontsize=7.5, color=INK2)
ax.set_xlim(10.55, 11.25); ax.set_ylim(61.05, 61.55); ax.set_aspect(1 / np.cos(np.radians(61.3)))
ax.grid(color=GRID, lw=0.4); ax.set_xlabel('Longitude (°E)'); ax.set_ylabel('Latitude (°N)')
ax.set_title('NOZ9EG corridor: adsb.lol true positions vs fly_2130.json labels\nwith hoyde891 810–891 moh points and fellesskap891 cells',
             fontsize=9, color=INK, loc='left')
leg = ax.legend(loc='lower left', fontsize=7.5, frameon=True); leg.get_frame().set_edgecolor(GRID)
fig.tight_layout(); fig.savefig(OUT + 'fig2_noz9eg_corridor.png', dpi=150); plt.close(fig)

# ---------- Figure 3: treslag score ----------
t = np.array(J('treslag.json')['celler'])
fig, ax = plt.subplots(figsize=(8, 7.5))
cmap = matplotlib.colors.LinearSegmentedColormap.from_list('g', ['#e8f3ec', '#1baf7a', '#0b4d34'])
sc = ax.scatter(t[:, 1], t[:, 0], c=t[:, 2], s=6, marker='s', cmap=cmap, vmin=0.55, vmax=1.0, lw=0, zorder=1)
outline(ax, 'innlandet.json', color=INK, lw=1.2, ls='--', zorder=3)
top = t[t[:, 2] >= 0.9]
ax.scatter(top[:, 1], top[:, 0], s=16, facecolor='none', edgecolor=INK, lw=0.7, zorder=4, label='score ≥ 0.90')
ax.set_xlim(9.7, 12.95); ax.set_ylim(59.75, 62.25); ax.set_aspect(1 / np.cos(np.radians(61)))
cb = fig.colorbar(sc, ax=ax, shrink=0.7); cb.set_label('similarity to 40% furu / 25% gran / 35% lauv (1 − ½·L1)')
ax.grid(color=GRID, lw=0.4); ax.set_xlabel('Longitude (°E)'); ax.set_ylabel('Latitude (°N)')
ax.set_title('treslag.json (NIBIO SR16 dominant species, 0.02° × 0.04° cells; only score ≥ 0.55 stored)', fontsize=9, color=INK, loc='left')
leg = ax.legend(loc='lower right', fontsize=8); leg.get_frame().set_edgecolor(GRID)
fig.tight_layout(); fig.savefig(OUT + 'fig3_treslag.png', dpi=150); plt.close(fig)
print('ok')
