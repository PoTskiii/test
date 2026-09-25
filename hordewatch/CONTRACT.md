# hordewatch contract

Every module builder must follow this. Read `types.py`, `db.py`, `analyzers/base.py`, `runner.py` first.

## Time
* All DB timestamps are UTC ISO strings. Norway is CEST = UTC+2 during the hunt.
* `capture_ts` = when our machine received the frame/sample. `real_ts` = estimated on-site time
  = capture_ts − `StreamClock.latency_s`. Observations carry the *real* time of the phenomenon (`Observation.ts`).
* Latency (YouTube + encoder + Starlink/4G uplink) is unknown a priori (≈15–45 s for normal-latency YouTube).
  It is calibrated into the `calibration` table (`latency_s`, `audio_offset_s`) by the aircraft bridge
  (ADS-B truth vs. audio/gesture events), by visible/written clocks, and by the live-edge offset reported by
  yt-dlp/streamlink. Replayed/looped audio (default.no found repeats 22–48 h apart) means audio time can be
  unrelated to video time: audio analyzers must tag `audio_loop` and never assume sync.

## Sources (hordewatch/ingest)
`make_source(source_cfg, clock, cfg)` returns an iterable of `("frame", Frame)` and `("audio", AudioChunk)`
items in capture order, plus `.close()`.
* `type: live` — resolve the YouTube live HLS URL with yt-dlp (or streamlink), decode with ffmpeg:
  one RGB frame every `frame_interval_s`, 16 kHz mono float32 audio chunks of `audio_chunk_s`.
  Reconnect with backoff; emit stream_health info into `ctx.state['ingest']`.
* `type: replay` — local video files (e.g. default.no cuts `YYYYMMDDHHMM_YYYYMMDDHHMM.mp4`, whose names give the
  real start/end in local time) or image folders + WAVs; timestamps derived from filenames or a `start_utc` key.
  Must work fully offline — this is what tests use.
* Frames are archived as JPEG every `archive_every_n_frames` (and always when an analyzer requests via
  `ctx.state['archive_next']=True`) under `archive_dir/YYYYMMDD/`.

## Analyzers
Subclass `analyzers.base.Analyzer`; return `Observation` objects with a `kind` from `types.KINDS`
(add new kinds there and document them). CPU only, graceful when optional deps are missing,
deterministic unit tests on synthetic images/audio under `tests/`.

## Bridges (turn observations into location evidence)
Output location likelihoods as `.npz` grids on the hordejakt analysis grid
(`hordejakt.grid.GRID`: lat 58–64.5 step 0.005, lon 4.5–13.5 step 0.01) holding `loglik` (NaN = no info)
plus JSON metadata `{name, reliability, independence_group, description, sources}` under
`data/hordewatch/layers/`. The hordejakt layer `hordejakt.layers.live` loads every grid found there, so new
evidence reaches the posterior without code changes.

## Network
This dev container blocks everything except GitHub/PyPI/npm. Live parts (YouTube, adsb.lol, MET, Ollama) run
on the user's machine; every network call must fail soft with a clear log message, and tests must not need
the network.
