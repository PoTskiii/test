"""Local vision-LLM analyzer (analyzer name: ``vlm``).

Uses a *local* multimodal model - by default Ollama with ``llava:7b`` - to do what
hand-written CV cannot: read messy handwriting, and describe the scene in a
structured way (sky state, precipitation, sunlight, what Anja is doing, new
objects, readable signs). Everything runs on the user's machine; no cloud.

Backends (config ``vlm`` section, overridable per analyzer):
  * ``ollama``  - POST {url}/api/chat  {"model", "messages": [{"content", "images": [b64]}],
                  "format": "json", "stream": false}. Ping: GET {url}/api/tags (also checks that the
                  model is pulled: ``ollama pull llava:7b``).
  * ``openai``  - OpenAI-compatible /v1/chat/completions with an ``image_url`` data-URI part
                  (llama.cpp ``llama-server --mmproj``, LM Studio, vLLM, LocalAI). Ping: GET /v1/models.
  * ``auto``    - try ollama first, then openai.

When it runs
  (a) On ``ctx.consume('whiteboard')`` (the whiteboard analyzer saw a board): the
      rectified board crop (``ctx.state['whiteboard']['crop']``, else the frame) is sent
      with :data:`WHITEBOARD_PROMPT` - exact transcription, Norwegian letters, line breaks,
      arrows and numbers kept, JSON answer.
  (b) Every ``scene_every_s`` seconds of *stream* time (default 600 s): the frame is sent
      with :data:`SCENE_PROMPT`, a structured JSON weather/scene report.

Non-blocking design
  CPU inference of a 7B VLM takes 10-120 s, so ``on_frame`` only downsizes the image
  (a few ms) and puts a job on a bounded queue; one worker thread talks HTTP. Results
  come back through a second queue and are turned into Observations on the *next*
  ``on_frame``/``on_tick`` call, stamped with the real time of the frame they describe
  (``Observation.ts`` = frame.real_ts, not the time the model answered). If the queue
  is full, scene jobs are dropped (whiteboard jobs evict a queued scene job).

Outputs
  * ``vlm_description`` (always) - value {prompt, text (raw answer), model, parsed, latency_s}.
  * whiteboard job -> ``whiteboard_text`` (analyzer 'vlm', source 'vlm'); an event is added
    only when the transcription is legible and not similar to any earlier board in the DB.
    The text is also exposed in ``ctx.state['vlm_whiteboard'][track_id]`` so the OCR
    analyzer can attach it as ``vlm_text``.
  * scene job -> low-confidence structured kinds that other fusers can use:
    ``cloud_fraction`` (method 'vlm'), ``fog``, ``rain_visual``, ``direct_sun``,
    ``gesture_point_up`` (arm angle unknown: None; triggers 'aircraft_check'),
    ``object_appeared`` (label from the model, bbox None). ``ctx.state['vlm_scene']``
    holds the last parsed scene.

Robust parsing
  :func:`extract_json` pulls the first balanced JSON object out of chatty output
  (code fences, prose, trailing commas, single quotes, Python literals).

Failure modes / caveats
  Small VLMs hallucinate - confidences are capped low (<= 0.6 for transcriptions,
  0.2-0.35 for scene fields) and every VLM result is marked ``method/source = 'vlm'``.
  LLaVA-7B is weak at reading handwriting and often "normalises" spelling; prefer a
  stronger local model if the machine allows (qwen2.5-vl:7b, llama3.2-vision:11b,
  minicpm-v). Night IR frames are monochrome - the model is told so.
"""
from __future__ import annotations

import base64
import json
import logging
import queue
import re
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Optional

import cv2
import numpy as np

from ..types import Observation, iso
from .base import Analyzer, Context

log = logging.getLogger("hordewatch.vlm")

WHITEBOARD_PROMPT = """You are transcribing a hand-written whiteboard held up to a camera by a woman sitting \
inside a transparent box in a Norwegian forest (a treasure-hunt livestream). The text is written in \
NORWEGIAN (bokmål), often in capital letters, and may contain the letters Æ Ø Å, numbers, arrows, \
compass directions (NORD, SØR, ØST, VEST), times (e.g. 14:30) and small drawings.

Transcribe the board EXACTLY as written:
- keep the original line breaks (one list item per written line, top to bottom);
- keep numbers, punctuation and arrows exactly (use the characters → ← ↑ ↓ ↗ ↘ ↙ ↖ for arrows);
- use Æ Ø Å where written (a slashed O is Ø, an A with a ring is Å);
- do NOT translate, correct spelling, guess missing words or add commentary;
- write ? for a character you cannot read.

Answer with ONLY this JSON object and nothing else:
{"lines": ["first line", "second line"], "text": "all lines joined with \\n", "language": "no|en|mixed", \
"legible": true, "confidence": 0.0, "drawings": "short description of any drawing/arrow/map, or empty"}"""

SCENE_PROMPT = """This is one frame from a fixed outdoor livestream camera in a Norwegian forest. The camera \
looks at a transparent box standing in heather/moss among trees; a woman (Anja) lives inside the box. \
If the image is black-and-white it is the night-time infrared mode.

Describe ONLY what is actually visible. Answer with ONLY this JSON object and nothing else:
{"sky": "clear|partly|overcast|fog|night|not_visible",
 "precipitation": "none|drizzle|rain|snow|sleet|unknown",
 "sunlight_direct": true,
 "shadows_direction": "left|right|towards_camera|away_from_camera|none",
 "anja_activity": "short phrase, e.g. sitting, sleeping, writing, pointing, holding board, not visible",
 "pointing_up": false,
 "objects_new": ["unusual objects outside the box, e.g. sign, balloon, drone, person, animal, vehicle"],
 "signs_text": ["any readable text on signs or boards"],
 "hands_or_signs_near_box": false,
 "notable": "anything unusual in one sentence, or empty"}"""

_SKY_FRACTION = {"clear": 0.05, "partly": 0.5, "overcast": 0.95, "fog": 1.0}


# ------------------------------------------------------------------------------------------ JSON
def _balanced_objects(text: str):
    """Yield substrings that are balanced {...} blocks (string-literal aware)."""
    i = 0
    n = len(text)
    while i < n:
        start = text.find("{", i)
        if start < 0:
            return
        depth, j, in_str, esc, quote = 0, start, False, False, ""
        while j < n:
            ch = text[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == quote:
                    in_str = False
            elif ch in "\"'":
                in_str, quote = True, ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    yield text[start:j + 1]
                    break
            j += 1
        else:
            yield text[start:]      # unterminated: let the repair step try
            return
        i = start + 1 if depth else j + 1


def _repair_json(s: str) -> str:
    s = s.strip()
    s = re.sub(r",\s*([}\]])", r"\1", s)                                  # trailing commas
    s = re.sub(r"\bTrue\b", "true", s)
    s = re.sub(r"\bFalse\b", "false", s)
    s = re.sub(r"\bNone\b", "null", s)
    if "'" in s and '"' not in s:
        s = s.replace("'", '"')
    s = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)", r'\1"\2"\3', s)  # unquoted keys
    opens = s.count("{") - s.count("}")
    if opens > 0:
        s += "}" * opens
    return s


def extract_json(text) -> Optional[dict]:
    """Return the first JSON object found in a model answer, or None."""
    if isinstance(text, dict):
        return text
    if not text:
        return None
    t = str(text)
    fence = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    candidates = []
    if fence:
        candidates.append(fence.group(1))
    candidates.append(t)
    for c in candidates:
        c = c.strip()
        try:
            v = json.loads(c)
            if isinstance(v, dict):
                return v
        except Exception:
            pass
        for block in _balanced_objects(c):
            for attempt in (block, _repair_json(block)):
                try:
                    v = json.loads(attempt)
                    if isinstance(v, dict):
                        return v
                except Exception:
                    continue
    return None


def _as_bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("true", "yes", "ja", "y", "1"):
            return True
        if s in ("false", "no", "nei", "n", "0", "none", ""):
            return False
    return None


def _as_list(v):
    if v is None:
        return []
    if isinstance(v, str):
        v = [x.strip() for x in re.split(r"[;,\n]", v) if x.strip()]
    if not isinstance(v, list):
        return []
    out = [str(x).strip() for x in v if str(x).strip()]
    return [x for x in out if x.lower() not in ("none", "n/a", "nothing", "no", "empty", "unknown")]


# ------------------------------------------------------------------------------------------ HTTP
def _http_json(url, payload=None, timeout=10.0, use_proxy_env=False, api_key=None):
    # The VLM server is local: by default ignore HTTP(S)_PROXY so localhost is not sent to a proxy.
    handlers = [] if use_proxy_env else [urllib.request.ProxyHandler({})]
    opener = urllib.request.build_opener(*handlers)
    data = None
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = "Bearer " + str(api_key)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
    with opener.open(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", "replace")
    return json.loads(body) if body.strip() else {}


def _encode_jpeg(rgb: np.ndarray, quality=85) -> str:
    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, int(quality)])
    if not ok:
        raise RuntimeError("jpeg encode failed")
    return base64.b64encode(buf.tobytes()).decode("ascii")


def _downscale(rgb: np.ndarray, max_side: int) -> np.ndarray:
    h, w = rgb.shape[:2]
    s = max_side / float(max(h, w))
    if s >= 1.0:
        return np.ascontiguousarray(rgb).copy()
    return cv2.resize(rgb, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA)


class VLMClient:
    """Minimal client for Ollama and OpenAI-compatible vision chat endpoints."""

    def __init__(self, backend="ollama", url="http://localhost:11434", model="llava:7b", timeout_s=180.0,
                 ping_timeout_s=2.0, temperature=0.0, max_tokens=512, keep_alive="30m", use_proxy_env=False,
                 api_key=None):
        self.backend = (backend or "ollama").lower()
        self.url = (url or "http://localhost:11434").rstrip("/")
        self.model = model
        self.timeout_s = float(timeout_s)
        self.ping_timeout_s = float(ping_timeout_s)
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.keep_alive = keep_alive
        self.use_proxy_env = bool(use_proxy_env)
        self.api_key = api_key
        self.reason = ""

    def _oa(self, path):
        base = self.url[:-3] if self.url.endswith("/v1") else self.url
        return base + "/v1" + path

    def ping(self) -> bool:
        backends = ["ollama", "openai"] if self.backend == "auto" else [self.backend]
        errors = []
        for b in backends:
            try:
                if b == "ollama":
                    tags = _http_json(self.url + "/api/tags", timeout=self.ping_timeout_s, use_proxy_env=self.use_proxy_env)
                    names = {m.get("name") for m in tags.get("models", [])} | {m.get("model") for m in tags.get("models", [])}
                    names |= {n.split(":")[0] + ":latest" for n in list(names) if n and ":" not in n}
                    want = self.model if ":" in self.model else self.model + ":latest"
                    if tags.get("models") is not None and want not in names and self.model not in names:
                        self.reason = (f"ollama at {self.url} is up but model {self.model!r} is not pulled "
                                       f"(have {sorted(n for n in names if n)}); run: ollama pull {self.model}")
                        return False
                else:
                    _http_json(self._oa("/models"), timeout=self.ping_timeout_s, use_proxy_env=self.use_proxy_env,
                               api_key=self.api_key)
                self.backend = b
                return True
            except Exception as e:
                errors.append(f"{b}: {e}")
        self.reason = f"VLM server unreachable at {self.url} ({'; '.join(errors)})"
        return False

    def chat(self, prompt: str, image_b64: str) -> str:
        if self.backend == "openai":
            payload = {"model": self.model, "temperature": self.temperature, "max_tokens": self.max_tokens,
                       "messages": [{"role": "user", "content": [
                           {"type": "text", "text": prompt},
                           {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + image_b64}}]}]}
            r = _http_json(self._oa("/chat/completions"), payload, timeout=self.timeout_s,
                           use_proxy_env=self.use_proxy_env, api_key=self.api_key)
            msg = (r.get("choices") or [{}])[0].get("message", {})
            content = msg.get("content", "")
            if isinstance(content, list):
                content = "".join(p.get("text", "") for p in content if isinstance(p, dict))
            return content or ""
        payload = {"model": self.model, "stream": False, "format": "json", "keep_alive": self.keep_alive,
                   "options": {"temperature": self.temperature, "num_predict": self.max_tokens},
                   "messages": [{"role": "user", "content": prompt, "images": [image_b64]}]}
        r = _http_json(self.url + "/api/chat", payload, timeout=self.timeout_s, use_proxy_env=self.use_proxy_env)
        if "message" in r:
            return r["message"].get("content", "") or ""
        return r.get("response", "") or ""


# ------------------------------------------------------------------------------------------ analyzer
class VLMAnalyzer(Analyzer):
    name = "vlm"
    wants_frames = True
    min_interval_s = 0.0
    tick_interval_s = 2.0

    DEFAULTS = {"backend": "ollama", "url": "http://localhost:11434", "model": "llava:7b",
                "scene_every_s": 600.0, "timeout_s": 180.0, "ping_timeout_s": 2.0, "max_side": 1024,
                "board_max_side": 1024, "jpeg_quality": 85, "queue_max": 4, "temperature": 0.0,
                "max_tokens": 512, "keep_alive": "30m", "use_proxy_env": False, "api_key": None,
                "dedup_sim": 0.8, "fail_backoff_s": 300.0}

    def __init__(self, config=None):
        super().__init__(config)
        cfg = dict(config or {})
        g = cfg.pop("_global", {}) or {}
        self.p = {**self.DEFAULTS, **(g.get("vlm") or {}), **cfg}
        self.client = VLMClient(backend=self.p["backend"], url=self.p["url"], model=self.p["model"],
                                timeout_s=self.p["timeout_s"], ping_timeout_s=self.p["ping_timeout_s"],
                                temperature=self.p["temperature"], max_tokens=self.p["max_tokens"],
                                keep_alive=self.p["keep_alive"], use_proxy_env=self.p["use_proxy_env"],
                                api_key=self.p["api_key"])
        self._jobs: queue.Queue = queue.Queue(maxsize=int(self.p["queue_max"]))
        self._results: queue.Queue = queue.Queue()
        self._worker: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._busy = threading.Event()
        self._last_scene_ts: Optional[datetime] = None
        self._fails = 0
        self._backoff_until = 0.0
        self._known_boards = None
        self._available = None

    # ------------------------------------------------------------------ lifecycle
    def available(self) -> bool:
        if self._available is None:
            ok = self.client.ping()
            if not ok:
                log.warning("VLM analyzer disabled: %s. Start a local server, e.g. `ollama serve` and "
                            "`ollama pull %s`, or set vlm.backend=openai for llama.cpp/LM Studio.",
                            self.client.reason, self.p["model"])
            else:
                log.info("VLM backend %s at %s, model %s", self.client.backend, self.client.url, self.client.model)
            self._available = ok
        return self._available

    def _ensure_worker(self):
        if self._worker is None or not self._worker.is_alive():
            self._stop.clear()
            self._worker = threading.Thread(target=self._run, name="hordewatch-vlm", daemon=True)
            self._worker.start()

    def close(self):
        self._stop.set()
        try:
            self._jobs.put_nowait(None)
        except queue.Full:
            pass

    def flush(self, timeout=30.0) -> bool:
        """Wait until the job queue is empty and the worker idle (tests / shutdown)."""
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            if self._jobs.unfinished_tasks == 0 and not self._busy.is_set():
                return True
            time.sleep(0.02)
        return False

    def _run(self):
        while not self._stop.is_set():
            try:
                job = self._jobs.get(timeout=0.5)
            except queue.Empty:
                continue
            if job is None:
                self._jobs.task_done()
                break
            self._busy.set()
            try:
                t0 = time.monotonic()
                b64 = _encode_jpeg(job["image"], self.p["jpeg_quality"])
                text = self.client.chat(job["prompt"], b64)
                job["answer"] = text
                job["latency_s"] = time.monotonic() - t0
                job["parsed"] = extract_json(text)
                job.pop("image", None)
                self._results.put(job)
                self._fails = 0
            except Exception as e:
                self._fails += 1
                if self._fails >= 3:
                    self._backoff_until = time.monotonic() + float(self.p["fail_backoff_s"])
                log.warning("VLM request failed (%s job, %d consecutive): %s", job.get("kind"), self._fails, e)
            finally:
                self._busy.clear()
                self._jobs.task_done()

    # ------------------------------------------------------------------ submission
    def _submit(self, job) -> bool:
        self._ensure_worker()
        try:
            self._jobs.put_nowait(job)
            return True
        except queue.Full:
            if job["kind"] != "whiteboard":
                log.debug("VLM queue full; dropping %s job", job["kind"])
                return False
            # evict one queued scene job to make room for the (more important) board
            kept, evicted = [], False
            while True:
                try:
                    j = self._jobs.get_nowait()
                except queue.Empty:
                    break
                self._jobs.task_done()
                if not evicted and j is not None and j["kind"] == "scene":
                    evicted = True
                    continue
                kept.append(j)
            for j in kept:
                self._jobs.put_nowait(j)
            try:
                self._jobs.put_nowait(job)
                return True
            except queue.Full:
                log.warning("VLM queue full of board jobs; dropping one")
                return False

    def on_frame(self, frame, ctx: Context):
        out = self._drain(ctx)
        meta = {"ts": frame.real_ts, "ts_capture": frame.capture_ts, "frame_id": frame.id, "frame_index": frame.index}
        if ctx.consume("whiteboard"):
            wb = ctx.state.get("whiteboard") or {}
            crop = wb.get("crop")
            img = crop if isinstance(crop, np.ndarray) and crop.size else frame.image
            if isinstance(crop, np.ndarray) and wb.get("ts") is not None:
                meta["ts"] = wb["ts"]
                meta["frame_id"] = wb.get("frame_id", frame.id)
            job = {"kind": "whiteboard", "prompt": WHITEBOARD_PROMPT, "track_id": wb.get("track_id"),
                   "image": _downscale(img, self.p["board_max_side"]), "bbox": wb.get("bbox"), **meta}
            self._submit(job)
        every = float(self.p["scene_every_s"])
        if every >= 0 and time.monotonic() >= self._backoff_until:
            due = self._last_scene_ts is None or (frame.real_ts - self._last_scene_ts).total_seconds() >= every
            if due and self._jobs.qsize() == 0:
                if self._submit({"kind": "scene", "prompt": SCENE_PROMPT,
                                 "image": _downscale(frame.image, self.p["max_side"]), **meta}):
                    self._last_scene_ts = frame.real_ts
        return out

    def on_tick(self, ctx: Context):
        return self._drain(ctx)

    # ------------------------------------------------------------------ results -> observations
    def _drain(self, ctx):
        out = []
        while True:
            try:
                job = self._results.get_nowait()
            except queue.Empty:
                break
            try:
                out += self._to_observations(job, ctx)
            except Exception as e:  # pragma: no cover - never kill the runner
                log.warning("VLM result handling failed: %s", e)
        return out

    def _obs(self, kind, job, value, conf, notes=""):
        return Observation(kind=kind, ts=job["ts"], value=value, analyzer=self.name, confidence=float(conf),
                           frame_id=job.get("frame_id"), ts_capture=job.get("ts_capture"), notes=notes)

    def _to_observations(self, job, ctx):
        parsed = job.get("parsed")
        out = [self._obs("vlm_description", job, {"prompt": job["kind"], "text": job.get("answer", ""),
                                                  "model": self.client.model, "backend": self.client.backend,
                                                  "parsed": parsed, "latency_s": round(job.get("latency_s", 0), 2)},
                         0.3 if parsed else 0.15)]
        if job["kind"] == "whiteboard":
            out += self._board_obs(job, parsed or {}, ctx)
        else:
            out += self._scene_obs(job, parsed or {}, ctx)
        return out

    def _board_obs(self, job, parsed, ctx):
        lines = _as_list(parsed.get("lines")) if isinstance(parsed.get("lines"), list) else []
        text = parsed.get("text") if isinstance(parsed.get("text"), str) else ""
        if not text and lines:
            text = "\n".join(lines)
        if not lines and text:
            lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not text and not parsed and job.get("answer"):
            text = job["answer"].strip()          # model ignored the JSON instruction
            lines = [l.strip() for l in text.splitlines() if l.strip()]
        try:
            from .whiteboard import board_similarity, fix_norwegian
            lines = [fix_norwegian(l)[0] for l in lines]
            text = "\n".join(lines) if lines else text
        except Exception:  # pragma: no cover
            board_similarity = None
        legible = _as_bool(parsed.get("legible"))
        try:
            mconf = float(parsed.get("confidence"))
        except (TypeError, ValueError):
            mconf = 0.5
        if not text.strip():
            return []
        conf = float(np.clip(0.25 + 0.35 * np.clip(mconf, 0, 1), 0.1, 0.6)) * (0.5 if legible is False else 1.0)
        is_new = None
        if board_similarity is not None and legible is not False:
            known = self._known_board_texts(ctx)
            best = max((board_similarity(text, k) for k in known), default=0.0)
            is_new = best < float(self.p["dedup_sim"])
            if is_new and ctx.db is not None:
                try:
                    ctx.db.add_event(job["ts"], "whiteboard_text_vlm",
                                     "VLM read whiteboard: " + text.replace("\n", " / "),
                                     {"text": text, "lines": lines, "model": self.client.model,
                                      "track_id": job.get("track_id")})
                except Exception as e:  # pragma: no cover
                    log.warning("VLM add_event failed: %s", e)
            self._known_boards.append(text)
        ctx.state.setdefault("vlm_whiteboard", {})[job.get("track_id")] = {"text": text, "ts": job["ts"]}
        value = {"text": text, "lines": lines, "lang": parsed.get("language") or "nb", "ocr_conf": None,
                 "vlm_text": text, "source": "vlm", "model": self.client.model, "legible": legible,
                 "model_confidence": mconf, "drawings": parsed.get("drawings") or "", "track_id": job.get("track_id"),
                 "bbox": job.get("bbox"), "is_new": is_new}
        return [self._obs("whiteboard_text", job, value, conf, notes="vlm transcription")]

    def _known_board_texts(self, ctx):
        if self._known_boards is None:
            self._known_boards = []
            if ctx.db is not None:
                try:
                    self._known_boards = [o["value"].get("text", "") for o in ctx.db.observations(kind="whiteboard_text")
                                          if (o["value"] or {}).get("text")]
                except Exception:  # pragma: no cover
                    pass
        return self._known_boards

    def _scene_obs(self, job, p, ctx):
        out = []
        base = {"method": "vlm", "model": self.client.model}
        sky = str(p.get("sky", "")).strip().lower()
        ctx.state["vlm_scene"] = {**p, "ts": job["ts"]}
        if sky in _SKY_FRACTION:
            out.append(self._obs("cloud_fraction", job, {"fraction": _SKY_FRACTION[sky], "label": sky, **base}, 0.25))
        if sky == "fog":
            out.append(self._obs("fog", job, {"present": True, "contrast_drop": None, **base}, 0.25))
        prec = str(p.get("precipitation", "")).strip().lower()
        if prec in ("drizzle", "rain", "snow", "sleet"):
            intensity = {"drizzle": 0.2, "rain": 0.6, "snow": 0.5, "sleet": 0.5}[prec]
            out.append(self._obs("rain_visual", job, {"present": True, "intensity": intensity, "type": prec, **base}, 0.3))
        elif prec == "none":
            out.append(self._obs("rain_visual", job, {"present": False, "intensity": 0.0, "type": "none", **base}, 0.2))
        sun = _as_bool(p.get("sunlight_direct"))
        if sun is not None and sky not in ("night",):
            out.append(self._obs("direct_sun", job, {"present": sun, "sunlit_fraction": None,
                                                     "shadows_direction": p.get("shadows_direction"), **base}, 0.25))
        if _as_bool(p.get("pointing_up")):
            out.append(self._obs("gesture_point_up", job, {"arm_angle_deg_from_vertical": None, "side": None,
                                                           "bbox": None, "activity": p.get("anja_activity"), **base},
                                 0.3))
            ctx.trigger("aircraft_check")
            ctx.state.setdefault("aircraft_check_requests", []).append(
                {"ts": iso(job["ts"]), "source": "vlm", "frame_id": job.get("frame_id")})
            del ctx.state["aircraft_check_requests"][:-50]
        for label in _as_list(p.get("objects_new"))[:5]:
            out.append(self._obs("object_appeared", job, {"label": label, "bbox": None, "appeared": True, **base}, 0.2))
        if _as_bool(p.get("hands_or_signs_near_box")):
            out.append(self._obs("object_appeared", job, {"label": "hands_or_signs_near_box", "bbox": None,
                                                          "appeared": True, "signs_text": _as_list(p.get("signs_text")),
                                                          **base}, 0.25))
        return out
