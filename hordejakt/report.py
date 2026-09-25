"""Self-contained Leaflet map of the posterior and hotspots."""
import base64
import io
import json

import numpy as np


def _png(post, bbox_idx):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import cm
    from PIL import Image
    i0, i1, j0, j1 = bbox_idx
    sub = post[i0:i1, j0:j1]
    v = np.log10(np.maximum(sub, 1e-12))
    hi = np.percentile(v[np.isfinite(v)], 99.9)
    lo = hi - 3.0
    x = np.clip((v - lo) / (hi - lo), 0, 1)
    rgba = (cm.magma(x) * 255).astype(np.uint8)
    rgba[..., 3] = (np.where(x > 0.05, 60 + 170 * x, 0)).astype(np.uint8)
    img = Image.fromarray(rgba[::-1])  # north up
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def write_map(grid, post, spots, path, summary):
    # crop to where the mass is
    mask = post > post.max() * 1e-3
    ii, jj = np.where(mask)
    i0, i1 = max(ii.min() - 5, 0), min(ii.max() + 6, grid.nlat)
    j0, j1 = max(jj.min() - 5, 0), min(jj.max() + 6, grid.nlon)
    png = _png(post, (i0, i1, j0, j1))
    south = grid.lats[i0] - grid.dlat / 2
    north = grid.lats[i1 - 1] + grid.dlat / 2
    west = grid.lons[j0] - grid.dlon / 2
    east = grid.lons[j1 - 1] + grid.dlon / 2
    pts = [{"rank": k + 1, **{kk: s[kk] for kk in ("lat", "lon", "p_within_1.5km", "groups", "norgeskart")}}
           for k, s in enumerate(spots)]
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Hordejakt posterior</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css">
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
<style>html,body,#m{{height:100%;margin:0}} .lbl{{font:600 12px system-ui;color:#fff;background:#b91c1c;border-radius:9px;padding:1px 5px}}</style>
</head><body><div id="m"></div><script>
const m=L.map('m').fitBounds([[{south},{west}],[{north},{east}]]);
L.tileLayer('https://cache.kartverket.no/v1/wmts/1.0.0/topo/default/webmercator/{{z}}/{{y}}/{{x}}.png',{{maxZoom:18,attribution:'&copy; Kartverket'}}).addTo(m);
L.imageOverlay('data:image/png;base64,{png}',[[{south},{west}],[{north},{east}]],{{opacity:.75}}).addTo(m);
const P={json.dumps(pts)};
for(const p of P){{const g=Object.entries(p.groups).map(([k,v])=>k+': '+v).join('<br>');
L.marker([p.lat,p.lon],{{icon:L.divIcon({{className:'',html:'<span class=lbl>'+p.rank+'</span>'}})}}).addTo(m)
.bindPopup('<b>#'+p.rank+'</b> '+p.lat.toFixed(4)+', '+p.lon.toFixed(4)+'<br>P(within 1.5 km)='+(100*p['p_within_1.5km']).toFixed(2)+'%<br><small>'+g+'</small><br><a target=_blank href="'+p.norgeskart+'">Norgeskart</a>');}}
</script></body></html>"""
    path.write_text(html)
