"""hordewatch — continuous monitoring of the Hordejakten livestream.

Pipeline:  ingest (live stream or replayed files)
        -> Frame / AudioChunk objects with capture and estimated real timestamps
        -> analyzers (CPU; OCR, local vision LLM, photometry, audio, astro...)
        -> Observation rows in SQLite (the "data table")
        -> bridges turn observations into location evidence (ADS-B, MET radar,
           astro likelihood grids) and re-run the hordejakt engine
        -> dashboard.

Contract: hordewatch/CONTRACT.md. Everything time-related is UTC in the
database; stream latency is handled explicitly (see types.StreamClock).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
