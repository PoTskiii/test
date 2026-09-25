"""Bird species from the stream audio with BirdNET (analyzer name: ``birds``). Optional.

Why: the species heard describe the habitat and region. Coastal vs inland, spruce/pine vs
birch, wetland, altitude: e.g. ptarmigan (fjellrype) and bluethroat (blåstrupe) mean
mountain/birch zone, Eurasian curlew (storspove) bogs, jackdaw (kaie) villages. The dates
matter too: late-September migration, and nocturnal flight calls of thrushes are heard.

Backend: `birdnetlib` (BirdNET-Analyzer v2.4 global 6K model, bundled in the wheel) + a
TFLite runtime (`tflite-runtime`, or `tensorflow` / `ai-edge-litert` as birdnetlib supports).
They are *not* installed in the dev container (TFLite is heavy). ``available()`` returns
False with a clear log message and the analyzer is skipped. On the monitoring machine:

    pip install birdnetlib tflite-runtime librosa     # (or tensorflow instead of tflite-runtime)

Processing: each chunk is resampled to 48 kHz, which BirdNET needs. birdnetlib's
RecordingBuffer does *not* resample: it cuts 3 s windows at the given rate and the model has a
fixed 144000-sample input. The chunk is analysed in 3 s windows, and detections with confidence
>= ``min_conf`` (0.5) become ``audio_bird`` observations (one per species per chunk, the
best window). The observation confidence is conf * 0.8, a conservative discount for
stream-compressed audio.
Options: ``lat``/``lon`` (default None = no location filter; a filter centred on a guessed
point would bias the species list, and hence the location evidence, towards that guess),
``use_date`` (week-of-year filter, default True, only applied with lat/lon), ``sensitivity``,
``overlap_s``, ``min_interval_s`` (default 0 = every chunk; raise it on a slow CPU;
BirdNET costs ~0.1 s per 3 s window).

Limits: the stream is 16 kHz by default (``source.audio_sr``), so content above 8 kHz is gone.
Very high songs (goldcrest/fuglekonge 7-9 kHz) are weakened, and BirdNET confidence drops
somewhat. AAC compression adds artefacts. Replayed audio (``audio_loop``) repeats old birds.
"""
from __future__ import annotations

import contextlib
import io
import logging
from datetime import timedelta

import numpy as np

from ..types import Observation
from .audio_events import prepare_samples, resample
from .base import Analyzer, Context

log = logging.getLogger("hordewatch.birds")

BIRDNET_SR = 48000

DEFAULTS = {"min_conf": 0.5, "lat": None, "lon": None, "use_date": True, "sensitivity": 1.0,
            "overlap_s": 0.0, "conf_scale": 0.8, "min_interval_s": 0.0}

INSTALL_HINT = ("pip install birdnetlib tflite-runtime librosa (or tensorflow instead of tflite-runtime) "
                "on the monitoring machine")


class BirdAnalyzer(Analyzer):
    name = "birds"
    wants_audio = True
    min_interval_s = 0.0

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.p = dict(DEFAULTS)
        self.p.update({k: v for k, v in (config or {}).items() if k != "_global"})
        self.min_interval_s = float(self.p.get("min_interval_s") or 0.0)
        self._bn = None
        self._RecordingBuffer = None
        self._checked = False
        self._ok = False
        self.reason = ""

    def available(self) -> bool:
        if self._checked:
            return self._ok
        self._checked = True
        try:
            from birdnetlib import RecordingBuffer
            from birdnetlib.analyzer import Analyzer as BNAnalyzer
        except Exception as e:
            self.reason = f"birdnetlib not importable ({type(e).__name__}: {e}); {INSTALL_HINT}"
            log.warning("birds: BirdNET unavailable - %s", self.reason)
            return False
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                self._bn = BNAnalyzer()
        except Exception as e:
            self.reason = f"BirdNET model could not be loaded ({type(e).__name__}: {e}); {INSTALL_HINT}"
            log.warning("birds: BirdNET unavailable - %s", self.reason)
            return False
        self._RecordingBuffer = RecordingBuffer
        self._ok = True
        log.info("birds: BirdNET ready (min_conf %.2f, location filter %s)", float(self.p["min_conf"]),
                 "off" if self.p.get("lat") is None else f"{self.p['lat']},{self.p['lon']}")
        return True

    def on_audio(self, chunk, ctx: Context):
        if not self.available():
            return []
        x = prepare_samples(chunk.samples, chunk.sr)
        if x is None or len(x) < 16000 * 1.5:
            return []
        y = resample(x, 16000, BIRDNET_SR).astype(np.float32)
        kw = {"min_conf": float(self.p["min_conf"]), "sensitivity": float(self.p["sensitivity"]),
              "overlap": float(self.p["overlap_s"])}
        if self.p.get("lat") is not None and self.p.get("lon") is not None:
            kw.update(lat=float(self.p["lat"]), lon=float(self.p["lon"]))
            if self.p.get("use_date"):
                kw["date"] = chunk.real_ts
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                rec = self._RecordingBuffer(self._bn, y, BIRDNET_SR, **kw)
                rec.analyze()
                dets = list(rec.detections)
        except Exception as e:
            log.warning("birds: BirdNET analysis failed: %s", e)
            return []
        best: dict = {}
        for d in dets:
            conf = float(d.get("confidence", 0.0))
            if conf < float(self.p["min_conf"]):
                continue
            key = d.get("scientific_name") or d.get("common_name")
            if key not in best or conf > float(best[key].get("confidence", 0.0)):
                best[key] = d
        cap_off = (chunk.capture_ts - chunk.real_ts).total_seconds() if chunk.capture_ts else 0.0
        out = []
        loop = ctx.state.get("audio_loop_active") if ctx is not None else None
        for key, d in sorted(best.items(), key=lambda kv: -float(kv[1]["confidence"])):
            conf = float(d["confidence"])
            st = float(d.get("start_time") or 0.0)
            ts = chunk.real_ts + timedelta(seconds=st)
            v = {"species": d.get("common_name") or key, "scientific_name": d.get("scientific_name"),
                 "conf": round(conf, 3), "start_s": st, "end_s": float(d.get("end_time") or st + 3.0),
                 "label": d.get("label"), "model": "BirdNET-Analyzer 2.4 (birdnetlib)",
                 "location_filter": kw.get("lat") is not None, "sr_in": int(chunk.sr or 16000)}
            c = conf * float(self.p["conf_scale"])
            if (loop and isinstance(loop, dict) and ts.timestamp() <= float(loop.get("until", 0)) + 30.0
                    and ts.timestamp() >= float(loop.get("since", loop.get("until", 0))) - 60.0):
                v["loop_suspect"] = True
                c = min(c, 0.3)
            out.append(Observation(kind="audio_bird", ts=ts, value=v, analyzer=self.name, confidence=round(c, 3),
                                   audio_id=getattr(chunk, "id", None), ts_capture=ts + timedelta(seconds=cap_off)))
        return out
