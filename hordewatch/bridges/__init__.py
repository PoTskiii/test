"""Bridges: turn hordewatch observations into location evidence and keep the engine current.

* adsb.AircraftBridge ('aircraft_bridge')  gesture/light/audio events x ADS-B -> aircraft_<event>.npz; stream latency
* met.WeatherBridge ('weather_bridge')     rain/cloud/sun/fog/condensation/temperature x MET Norway -> weather_<kind>_<date>.npz
* engine.EngineBridge ('engine_bridge')    periodic hordejakt re-run in a subprocess + ranking-change events
* defaultno.DefaultNoPoller                periodic default.no mirror + diff -> events (new cuts, files, site lists)
Shared plumbing (layer writer, paths, state) is in common.py.
"""
