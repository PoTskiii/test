"""Core data types shared by every hordewatch module."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import numpy as np

UTC = timezone.utc

# Controlled vocabulary for Observation.kind. Add new kinds here (and in CONTRACT.md).
KINDS = {
    # vision
    "whiteboard_text": "Text Anja shows on the whiteboard; value={text, lines, lang, ocr_conf, vlm_text}",
    "whiteboard_visible": "A whiteboard is held up (trigger for OCR/VLM); value={bbox}",
    "vlm_description": "Free-text scene description from the local vision LLM; value={prompt, text, model}",
    "scene_change": "Significant change vs. reference frame; value={score, bbox_list}",
    "object_appeared": "New/removed object (sign, hand, balloon...); value={label, bbox, appeared: bool}",
    "gesture_point_up": "Anja points up/at the sky; value={arm_angle_deg_from_vertical, side, bbox}",
    "person_count": "People visible in frame; value={n}",
    "ir_mode_switch": "Camera switched day<->IR/night mode (light-level threshold, dusk/dawn timing); "
                      "value={to_ir: bool, from, to, onset_window: [prev_ts, ts], detected_ts}",
    # sky / light / weather (vision)
    "sky_photometry": "Sky-region statistics; value={luma, r, g, b, cct_k, sat, region}",
    "scene_photometry": "Whole-frame / ground statistics; value={luma, exposure_hint, ir_mode: bool}",
    "cloud_fraction": "Estimated cloud cover in visible sky; value={fraction, method}",
    "direct_sun": "Direct sunlight on scene (hard shadows / sunlit patches); value={present: bool, sunlit_fraction}",
    "sun_pixel": "Sun disk / flare position in the image; value={x, y, radius, saturated: bool}",
    "shadow_direction": "Dominant cast-shadow direction in image; value={angle_deg_image, strength}",
    "rain_visual": "Rain seen (drops on roof/lens, streaks); value={present: bool, intensity}",
    "condensation": "Condensation/frost on box roof/walls; value={present: bool, fraction}",
    "fog": "Fog/mist visibility reduction; value={present: bool, contrast_drop}",
    "temperature": "Temperature read on stream (whiteboard/thermometer/VLM); value={temp_c, where: 'inside'|'outside', source}"
                   " -- used by the weather bridge vs MET Nordic 2 m air temperature",
    "night_light_event": "Artificial light (torch, headlights, lamp) at night; value={luma_delta, bbox, colour}",
    "aircraft_light": "Blinking/moving point light in sky; value={track: [[t,x,y]...], blink_hz}",
    "star_field": "Point sources consistent with stars; value={n_stars, points: [[x,y,flux]...]}",
    "moon_pixel": "Moon position/phase in image; value={x, y, radius, illum}",
    "plate_solution": "Astrometric solution of a frame; value={ra_deg, dec_deg, scale_arcsec_px, rot_deg, stars: [...]}",
    # audio
    "audio_aircraft": "Jet/prop noise; value={peak_ts, snr_db, duration_s, doppler_hint}",
    "audio_rain": "Rain on roof/canopy; value={intensity}",
    "audio_wind": "Wind noise; value={level_db}",
    "audio_vehicle": "Road vehicle / engine; value={snr_db}",
    "audio_train": "Railway; value={snr_db}",
    "audio_gunshot": "Impulsive shot-like sound; value={peak_db}",
    "audio_chainsaw": "Chainsaw/forestry machine; value={snr_db}",
    "audio_bird": "Bird species (BirdNET or heuristic); value={species, conf}",
    "audio_voice": "Speech (Anja/crew); value={snr_db, speaker_hint}",
    "audio_bells": "Church bells; value={snr_db}",
    "audio_loop": "Audio segment repeats an earlier one (replayed audio); value={ref_ts, lag_s, corr}",
    "av_offset": "Audio-video offset estimate; value={offset_s, method}",
    # stream / timing
    "stream_health": "Ingest stats; value={bitrate_kbps, fps, dropped, stall_s, resolution}",
    "stream_latency": "Estimated latency live-edge -> real time; value={latency_s, method}",
    "stream_stall": ("One ingest disruption (analyzers/stream_health); ts = estimated on-site start; "
                     "value={kind: upstream|gap|local|decoder|reconnect|skip, start, end, duration_s, onsite_start, "
                     "onsite_method, phase_mod_period_s, seq, detail}"),
    "uplink_signature": ("Uplink type inferred from stall timing (Starlink 15 s slot periodicity vs cellular); "
                         "value={verdict: starlink_like|cellular_like|unknown, n_events, rayleigh_p, phase_s, "
                         "best_period_s, interval_multiple_frac, lag_ls_power, ...}"),
    "clock_seen":"A clock/time visible or written (whiteboard); value={shown_time, real_ts}",
    # derived / bridges
    "aircraft_match": "Aircraft matched to a gesture/sound event; value={callsign, icao, alt_ft, elev_deg, az_deg}",
    "weather_match": "Observed weather matched to radar/analysis; value={product, cells: n}",
    "astro_fix": "Location constraint from astronomy; value={method, lat, lon, sigma_km, grid_path}",
    # astro inputs (hordewatch/astro)
    "twilight_marker": ("Sky-brightness threshold crossing or IR-mode switch at dusk/dawn (fixed solar depression); "
                        "value={event: 'dusk'|'dawn', series, threshold, method}"),
    "camera_vertical": ("Level reference for the camera: image segments of world-vertical structures (trunks, posts, "
                        "hanging cords = plumb lines) and/or families of world-horizontal parallel edges; "
                        "value={segments: [[x1,y1,x2,y2(,sigma_deg)]...], kind: 'trunk'|'post'|'plumb'|'auto_lines', "
                        "sigma_deg, horizontal_families: [[[x1,y1,x2,y2]...]...], family_sigma_deg, w, h}"),
    # blinking lights (hordewatch/blink.py, analyzers/blink_watch.py)
    "blinking_light": ("Point light analysed over a full-frame-rate burst; value={x, y, frame_size, verdict, "
                       "morse_text, groups, period_s, duty, n_flashes, clip}"),
}


@dataclass
class StreamClock:
    """Maps local capture time to estimated real (on-site) time.

    real_ts = capture_ts - latency_s, where latency covers encoder + uplink
    (Starlink/4G) + YouTube ingest/transcode + player buffer. Typical YouTube
    live latency: normal 15-45 s, low-latency 5-10 s, ultra-low 2-5 s.
    """
    latency_s: float = 30.0
    latency_sigma_s: float = 15.0
    audio_offset_s: float = 0.0  # audio_real = video_real + audio_offset_s (replayed audio may differ)

    def real_ts(self, capture_ts: datetime) -> datetime:
        return capture_ts - timedelta(seconds=self.latency_s)


@dataclass
class Frame:
    index: int
    capture_ts: datetime          # UTC, when we received it (or replay-declared)
    real_ts: datetime             # UTC, estimated on-site time
    image: np.ndarray             # H x W x 3 uint8, RGB
    source: str = "live"          # 'live' | 'replay:<file>'
    path: Optional[str] = None    # saved JPEG path if archived
    id: Optional[int] = None      # DB id once stored

    @property
    def h(self):
        return self.image.shape[0]

    @property
    def w(self):
        return self.image.shape[1]


@dataclass
class AudioChunk:
    index: int
    capture_ts: datetime          # UTC of first sample
    real_ts: datetime
    samples: np.ndarray           # float32 mono in [-1, 1]
    sr: int = 16000
    source: str = "live"
    path: Optional[str] = None
    id: Optional[int] = None

    @property
    def duration_s(self):
        return len(self.samples) / float(self.sr)


@dataclass
class Observation:
    kind: str
    ts: datetime                  # UTC real (on-site) time of the observed phenomenon
    value: dict
    analyzer: str
    confidence: float = 0.5
    frame_id: Optional[int] = None
    audio_id: Optional[int] = None
    ts_capture: Optional[datetime] = None
    notes: str = ""
    id: Optional[int] = None

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"unknown observation kind {self.kind!r}; add it to hordewatch.types.KINDS")

    def value_json(self):
        return json.dumps(self.value, default=_json_default, ensure_ascii=False)


def _json_default(o: Any):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(type(o))


def utcnow():
    return datetime.now(UTC)


def iso(ts: datetime) -> str:
    return ts.astimezone(UTC).isoformat(timespec="milliseconds")


def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s).astimezone(UTC)
