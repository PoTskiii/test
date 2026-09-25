"""hordewatch.astro - location evidence from the sky seen by the stream camera.

Modules
  ephem.py     offline skyfield (DE421 bundled) apparent places + vectorised topocentric
               alt/az for thousands of candidate sites, refraction, Moon parallax.
  camera.py    pinhole camera (heading/pitch/roll, f, principal point, k1), plumb-line and
               level-line residuals, Hough plumb-line detector.  Explains the key degeneracy.
  stars.py     bundled Hipparcos catalogue (HYG v4.1, V <= 5), triangle matcher, plate
               summaries, astrometry.net wrapper (fails soft).
  twilight.py  dusk/dawn threshold-crossing markers from photometry and the twilight
               timing likelihood (no camera geometry needed).
  solver.py    batched Levenberg-Marquardt profile likelihood over a lat/lon grid for
               sun / moon / star pixels, layer writing for hordejakt.layers.live, and the
               AstroBridge analyzer ('astro_bridge', on_tick every 10 min).

The one thing to remember: sun, moon and star positions in the image fix the camera's
orientation relative to the rotating Earth to ~0.01 deg, but the *site* only as well as we
know where "straight up" is in the image.  1 deg of pitch/roll error = 111 km (celestial
navigation without a horizon).  Level references - hanging cords / objects (plumb lines,
~0.1 deg), tree trunks (~1-2 deg each), levelled box edges - are therefore first-class
inputs (Observation kind ``camera_vertical``, or DB calibration ``camera_attitude``).
Twilight timing needs no level reference but is limited in longitude by the dusk/dawn
asymmetry of the view; stream latency maps 1:1 onto longitude (1 min = 0.25 deg).
"""
