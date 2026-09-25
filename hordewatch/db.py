"""SQLite "data table" for everything hordewatch observes.

Tables
  frames(id, idx, capture_ts, real_ts, source, path, w, h)
  audio(id, idx, capture_ts, real_ts, source, path, sr, duration_s)
  observations(id, ts, ts_capture, kind, analyzer, confidence, value, frame_id, audio_id, notes, created)
  calibration(key, value, updated)          -- e.g. latency_s, audio_offset_s, camera model
  events(id, ts, kind, summary, value, status, created)   -- human-facing alerts
All timestamps are ISO-8601 UTC strings. WAL mode so the dashboard can read
while the runner writes.
"""
import json
import sqlite3
import threading
from pathlib import Path

from .types import AudioChunk, Frame, Observation, iso, parse_iso, utcnow

SCHEMA = """
CREATE TABLE IF NOT EXISTS frames(
  id INTEGER PRIMARY KEY, idx INTEGER, capture_ts TEXT, real_ts TEXT, source TEXT, path TEXT, w INTEGER, h INTEGER);
CREATE INDEX IF NOT EXISTS frames_ts ON frames(real_ts);
CREATE TABLE IF NOT EXISTS audio(
  id INTEGER PRIMARY KEY, idx INTEGER, capture_ts TEXT, real_ts TEXT, source TEXT, path TEXT, sr INTEGER, duration_s REAL);
CREATE INDEX IF NOT EXISTS audio_ts ON audio(real_ts);
CREATE TABLE IF NOT EXISTS observations(
  id INTEGER PRIMARY KEY, ts TEXT, ts_capture TEXT, kind TEXT, analyzer TEXT, confidence REAL,
  value TEXT, frame_id INTEGER, audio_id INTEGER, notes TEXT, created TEXT);
CREATE INDEX IF NOT EXISTS obs_kind_ts ON observations(kind, ts);
CREATE TABLE IF NOT EXISTS calibration(key TEXT PRIMARY KEY, value TEXT, updated TEXT);
CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY, ts TEXT, kind TEXT, summary TEXT, value TEXT, status TEXT DEFAULT 'new', created TEXT);
"""


class DB:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.con = sqlite3.connect(self.path, check_same_thread=False)
        self.con.execute("PRAGMA journal_mode=WAL")
        self.con.executescript(SCHEMA)
        self.con.commit()

    # --- writes
    def add_frame(self, f: Frame) -> int:
        with self._lock:
            cur = self.con.execute(
                "INSERT INTO frames(idx, capture_ts, real_ts, source, path, w, h) VALUES (?,?,?,?,?,?,?)",
                (f.index, iso(f.capture_ts), iso(f.real_ts), f.source, f.path, f.w, f.h))
            self.con.commit()
            f.id = cur.lastrowid
            return f.id

    def add_audio(self, a: AudioChunk) -> int:
        with self._lock:
            cur = self.con.execute(
                "INSERT INTO audio(idx, capture_ts, real_ts, source, path, sr, duration_s) VALUES (?,?,?,?,?,?,?)",
                (a.index, iso(a.capture_ts), iso(a.real_ts), a.source, a.path, a.sr, a.duration_s))
            self.con.commit()
            a.id = cur.lastrowid
            return a.id

    def add_observation(self, o: Observation) -> int:
        with self._lock:
            cur = self.con.execute(
                "INSERT INTO observations(ts, ts_capture, kind, analyzer, confidence, value, frame_id, audio_id, notes, created)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (iso(o.ts), iso(o.ts_capture) if o.ts_capture else None, o.kind, o.analyzer, float(o.confidence),
                 o.value_json(), o.frame_id, o.audio_id, o.notes, iso(utcnow())))
            self.con.commit()
            o.id = cur.lastrowid
            return o.id

    def add_event(self, ts, kind, summary, value=None):
        with self._lock:
            cur = self.con.execute("INSERT INTO events(ts, kind, summary, value, created) VALUES (?,?,?,?,?)",
                                   (iso(ts), kind, summary, json.dumps(value or {}, ensure_ascii=False), iso(utcnow())))
            self.con.commit()
            return cur.lastrowid

    def set_calibration(self, key, value):
        with self._lock:
            self.con.execute("INSERT INTO calibration(key, value, updated) VALUES (?,?,?) "
                             "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated=excluded.updated",
                             (key, json.dumps(value), iso(utcnow())))
            self.con.commit()

    # --- reads
    def calibration(self, key, default=None):
        r = self.con.execute("SELECT value FROM calibration WHERE key=?", (key,)).fetchone()
        return json.loads(r[0]) if r else default

    def observations(self, kind=None, since=None, until=None, limit=None):
        q, args = "SELECT id, ts, ts_capture, kind, analyzer, confidence, value, frame_id, audio_id, notes FROM observations WHERE 1=1", []
        if kind:
            kinds = [kind] if isinstance(kind, str) else list(kind)
            q += " AND kind IN (%s)" % ",".join("?" * len(kinds))
            args += kinds
        if since:
            q += " AND ts >= ?"
            args.append(iso(since))
        if until:
            q += " AND ts <= ?"
            args.append(iso(until))
        q += " ORDER BY ts"
        if limit:
            q += f" LIMIT {int(limit)}"
        out = []
        for r in self.con.execute(q, args):
            out.append({"id": r[0], "ts": parse_iso(r[1]), "ts_capture": parse_iso(r[2]) if r[2] else None,
                        "kind": r[3], "analyzer": r[4], "confidence": r[5], "value": json.loads(r[6]),
                        "frame_id": r[7], "audio_id": r[8], "notes": r[9]})
        return out

    def frame_path(self, frame_id):
        r = self.con.execute("SELECT path FROM frames WHERE id=?", (frame_id,)).fetchone()
        return r[0] if r else None
