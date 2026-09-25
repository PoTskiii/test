"""Optional phone/desktop push of new hordewatch events via ntfy (https://ntfy.sh or a self-hosted server).

Enable in hordewatch.yaml::

    dashboard:
      ntfy:
        topic: hordewatch-<long random string>   # ntfy.sh topics are PUBLIC: whoever guesses it reads it
        server: https://ntfy.sh                  # or your own ntfy server
        token: null                              # access token for protected topics (Authorization: Bearer)
        click_url: http://my-laptop:8787/        # opened when the notification is tapped
        kinds: null                              # only these event kinds (null = all)
        exclude_kinds: [calibration_manual]
        priority: {whiteboard_text: 5, engine_ranking_change: 4}

or ``python -m hordewatch.dashboard --ntfy-topic ...`` / env ``HORDEWATCH_NTFY_TOPIC``.

Method
  A daemon thread polls the ``events`` table (id > cursor) every ``poll_s`` and publishes each new
  event as JSON to the server root (``POST {server}/`` with ``{"topic", "title", "message", "priority",
  "tags", "click"}``). JSON publishing is used instead of the header API because titles contain
  Norwegian letters and HTTP headers are latin-1 only.

Delivery rules
  * The cursor lives in the calibration table (``dashboard_state:ntfy_cursor``) so a dashboard restart
    neither re-sends old alerts nor loses the ones that arrived while it was down. On the very first
    start the cursor is set to the current maximum: the historical backlog is never pushed.
  * Backlog after downtime is capped (``max_backlog``, default 10 newest; the rest become one
    "… and N more" message) and events older than ``max_age_s`` (default 1 h) are skipped: a stale
    push is noise.
  * Rate limit: at most ``max_per_minute`` pushes; excess events in a burst are folded into a summary.

Failure modes (all soft)
  No network / DNS / HTTP error: logged once per ``warn_every_s`` (clear message, no traceback spam),
  the cursor is *not* advanced, and the thread retries with exponential backoff up to 5 min. This dev
  container blocks the network entirely, so here it just logs and keeps trying.
"""
from __future__ import annotations

import json
import logging
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Callable, Optional

log = logging.getLogger("hordewatch.dashboard.notify")

CURSOR_KEY = "dashboard_state:ntfy_cursor"
DEFAULT_PRIORITY = {"whiteboard_text": 5, "whiteboard_text_vlm": 4, "engine_ranking_change": 4, "aircraft_layer": 3,
                    "latency_calibrated": 3, "astro": 3, "engine_run_failed": 2, "calibration_manual": 1}
DEFAULT_TAGS = {"whiteboard_text": ["memo"], "whiteboard_text_vlm": ["memo", "robot"],
                "engine_ranking_change": ["world_map"], "aircraft_layer": ["airplane"], "astro": ["star"],
                "latency_calibrated": ["stopwatch"], "engine_run_failed": ["warning"]}


# ntfy's JSON API wants an integer priority 1..5; the header API's names are accepted in the config too
PRIORITY_NAMES = {"min": 1, "low": 2, "default": 3, "high": 4, "max": 5, "urgent": 5}
TOPIC_RE = re.compile(r"^[-_A-Za-z0-9]{1,64}$")      # what ntfy.sh accepts as a topic name


def _priority(x, default: int = 3) -> int:
    """Coerce a config priority (1-5 or min/low/default/high/max/urgent) to ntfy's integer 1..5.
    A value ntfy would reject (HTTP 400) is a poison message: the cursor would never advance again."""
    if isinstance(x, str):
        x = PRIORITY_NAMES.get(x.strip().lower(), x)
    try:
        return int(min(5, max(1, int(x))))
    except (TypeError, ValueError):
        return default


def _http_post_json(url: str, payload: dict, token: Optional[str] = None, timeout: float = 10.0) -> int:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status


class NtfyNotifier:
    CONFIG_KEYS = {"topic", "server", "token", "click_url", "kinds", "exclude_kinds", "priority", "poll_s",
                   "max_backlog", "max_age_s", "max_per_minute", "warn_every_s"}

    def __init__(self, db_path, topic: str, server: str = "https://ntfy.sh", token: Optional[str] = None,
                 click_url: Optional[str] = None, kinds=None, exclude_kinds=("calibration_manual",), priority=None,
                 poll_s: float = 5.0, max_backlog: int = 10, max_age_s: float = 3600.0, max_per_minute: int = 12,
                 warn_every_s: float = 600.0, post: Optional[Callable] = None):
        if not topic:
            raise ValueError("ntfy topic required")
        if not TOPIC_RE.match(str(topic)):
            raise ValueError(f"invalid ntfy topic {topic!r}: use 1-64 of A-Z a-z 0-9 _ - (ntfy rejects others)")
        self.db_path = str(db_path)
        self.topic = str(topic)
        self.server = str(server or "https://ntfy.sh").rstrip("/")
        self.token = token
        self.click_url = click_url
        self.kinds = set(kinds) if kinds else None
        self.exclude = set(exclude_kinds or ())
        self.priority = {k: _priority(v) for k, v in {**DEFAULT_PRIORITY, **(priority or {})}.items()}
        self.poll_s = float(poll_s)
        self.max_backlog = int(max_backlog)
        self.max_age_s = float(max_age_s)
        self.max_per_minute = int(max_per_minute)
        self.warn_every_s = float(warn_every_s)
        self._post = post or (lambda payload: _http_post_json(self.server + "/", payload, self.token))
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._sent_times: list = []
        self._last_warn = 0.0
        self.last_error: Optional[str] = None
        self.sent = 0

    # ------------------------------------------------------------------ cursor
    def _con(self):
        con = sqlite3.connect(self.db_path, timeout=10.0)
        con.row_factory = sqlite3.Row
        return con

    def _get_cursor(self, con) -> Optional[int]:
        r = con.execute("SELECT value FROM calibration WHERE key=?", (CURSOR_KEY,)).fetchone()
        try:
            return int(json.loads(r[0])) if r else None
        except (TypeError, ValueError):
            return None

    def _set_cursor(self, con, v: int):
        con.execute("INSERT INTO calibration(key, value, updated) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET "
                    "value=excluded.value, updated=excluded.updated",
                    (CURSOR_KEY, json.dumps(int(v)), datetime.now(timezone.utc).isoformat(timespec="milliseconds")))
        con.commit()

    # ------------------------------------------------------------------ one step (unit-testable)
    def payload(self, ev) -> dict:
        kind = ev["kind"] or "event"
        p = {"topic": self.topic, "title": f"hordewatch: {kind}"[:120], "message": (ev["summary"] or kind)[:3500],
             "priority": _priority(self.priority.get(kind, 3)), "tags": list(DEFAULT_TAGS.get(kind, ["bell"]))}
        if self.click_url:
            p["click"] = self.click_url
        return p

    def _wanted(self, ev) -> bool:
        k = ev["kind"]
        return (self.kinds is None or k in self.kinds) and k not in self.exclude

    def step(self, now: Optional[float] = None) -> int:
        """Push events newer than the cursor. Returns the number of messages sent; raises on post errors
        (the cursor then stays where it was)."""
        now = time.time() if now is None else now
        con = self._con()
        try:
            cur = self._get_cursor(con)
            mx = con.execute("SELECT MAX(id) FROM events").fetchone()[0] or 0
            if cur is None:                    # first start: never push the historical backlog
                self._set_cursor(con, mx)
                return 0
            if mx <= cur:
                return 0
            rows = con.execute("SELECT id, ts, kind, summary, created FROM events WHERE id > ? ORDER BY id", (cur,)).fetchall()
            fresh = []
            for r in rows:
                if not self._wanted(r):
                    continue
                try:
                    t = datetime.fromisoformat(r["created"] or r["ts"]).timestamp()
                except (TypeError, ValueError):
                    t = now
                if now - t <= self.max_age_s:
                    fresh.append(r)
            self._sent_times = [t for t in self._sent_times if now - t < 60.0]
            budget = max(0, self.max_per_minute - len(self._sent_times))
            if fresh and budget == 0:
                return 0                       # rate limited: keep the cursor, fold them next minute
            # the newest `cap` go out individually; one slot is reserved for a summary of the rest
            cap = min(self.max_backlog, budget if len(fresh) <= budget else budget - 1)
            send = fresh[len(fresh) - cap:] if cap > 0 else []
            folded = fresh[: len(fresh) - len(send)]
            n = 0
            if folded:
                kinds = sorted({r["kind"] for r in folded})
                self._post({"topic": self.topic, "title": f"hordewatch: {len(folded)} more alerts",
                            "message": f"{len(folded)} older/burst alerts not pushed individually ({', '.join(kinds)[:300]}); "
                                       f"see the dashboard.", "priority": 3, "tags": ["bell"],
                            **({"click": self.click_url} if self.click_url else {})})
                self._sent_times.append(now)
                n += 1
            for r in send:
                self._post(self.payload(r))
                self._sent_times.append(now)
                n += 1
                self._set_cursor(con, r["id"])  # per message: a failure mid-batch resends only the rest
            self._set_cursor(con, rows[-1]["id"])
            self.sent += n
            return n
        finally:
            con.close()

    # ------------------------------------------------------------------ thread
    def _run(self):
        backoff = self.poll_s
        while not self._stop.is_set():
            try:
                self.step()
                self.last_error = None
                backoff = self.poll_s
            except (urllib.error.URLError, OSError, ValueError, sqlite3.Error) as e:
                self.last_error = str(e)
                if time.time() - self._last_warn > self.warn_every_s:
                    self._last_warn = time.time()
                    log.warning("ntfy push to %s failed (%s); will retry with backoff - alerts stay in the dashboard",
                                self.server, e)
                backoff = min(300.0, max(self.poll_s, backoff * 2))
            except Exception as e:  # never kill the dashboard
                self.last_error = str(e)
                log.exception("ntfy notifier error: %s", e)
                backoff = min(300.0, max(self.poll_s, backoff * 2))
            self._stop.wait(backoff)

    def start(self):
        if self._thread is None or not self._thread.is_alive():
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, name="ntfy", daemon=True)
            self._thread.start()
            log.info("ntfy push enabled: %s/%s", self.server, self.topic[:4] + "…")

    def stop(self, timeout: float = 2.0):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout)
