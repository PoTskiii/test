"""Fine-scale refinement (1-10 m) inside the coarse engine's top cells.

Modules
-------
raster  Raster container (numpy array + affine transform, EPSG:25833) and
        EPSG:25833 <-> WGS84 helpers.
fetch   Defensive fetchers for Kartverket DTM/DOM (Geonorge WCS, høydedata
        point API), OpenStreetMap (Overpass), NIBIO SR16 and adsb.lol traces,
        with retries, an on-disk cache in data/cache/ and a clear error when
        the network blocks a host.
score   Per-pixel site scores for the on-stream constraints, candidate
        extraction, parking/walk analysis and the morning-sun horizon check.
cli     ``python -m hordejakt.refine.cli --hotspots output/hotspots.json``.
"""
