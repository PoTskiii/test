"""Engine bridge: re-run the hordejakt localisation engine periodically and alert on ranking changes.

Every ``every_min`` minutes (default 10) the bridge re-runs hordejakt so that
new live layers (aircraft, weather, astro fixes ...) reach the posterior. The
engine runs in a *subprocess* (``python -m hordejakt.cli`` or
``hordejakt.scenarios``) so its ~1-2 GB of grids never live in the monitor
process, and the subprocess is polled on later ticks (on_tick never blocks).
A run is skipped when no layer file changed since the last run, unless
``force_every_min`` (default 60) has passed.

After each run the new top hotspots are compared with the previous run
(``compare_rankings``, pure and unit-tested). A change is *material* when
  * the top cell moved more than ``move_km`` (default 5 km), or
  * one of the new top ``top_k`` (default 3) spots lies more than ``same_km``
    (default 3 km, > the engine's 2 km hotspot separation) from every previous
    top-k spot, i.e. a new area entered the top 3.
Material changes become ``engine_ranking_change`` events for the dashboard;
every run is archived as output/history/<UTC stamp>_hotspots.json with the
top-N hotspots, credible areas, live layers present and the detected changes.

Tests (or other callers) can pass ``run_fn`` (callable -> {"hotspots": [...],
"summary": {...}}) to replace the subprocess; it runs synchronously.
Failure modes: engine exception/timeout -> ``engine_run_failed`` event (at most
once per hour) and the previous ranking stays the baseline.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

from hordejakt.geo import haversine

from ..analyzers.base import Analyzer
from .common import OUTPUT, ROOT, dumps, from_unix, layers_dir, resolve_path, setting

log = logging.getLogger("hordewatch.bridges.engine")

DEFAULTS = {"every_min": 10.0, "force_every_min": 60.0, "mode": "cli", "top": 40, "compare_top": 10, "top_k": 3,
            "move_km": 5.0, "same_km": 3.0, "timeout_s": 1800.0, "only_if_changed": True, "keep_history": 2000}


def compare_rankings(prev, new, top=10, top_k=3, move_km=5.0, same_km=3.0):
    """Compare two ranked hotspot lists [{lat, lon, ...}, ...] (best first).

    Returns (material: bool, changes: list[dict]). Change types:
      top_moved     the #1 spot moved > move_km
      new_top_area  a new top-k spot is > same_km from every previous top-k spot
                    (prev_rank = rank of the nearest previous spot within same_km, if any)
      reshuffle     < half of the new top-``top`` lie within same_km of a previous top-``top`` spot
                    (informational, not material on its own)
    """
    if not prev:
        return (bool(new), [{"type": "first_run", "n": len(new)}] if new else [])
    if not new:
        return True, [{"type": "empty_ranking"}]
    changes = []

    def dist(a, b):
        return float(haversine(a["lat"], a["lon"], b["lat"], b["lon"]))

    d0 = dist(prev[0], new[0])
    if d0 > move_km:
        changes.append({"type": "top_moved", "km": round(d0, 2), "from": [prev[0]["lat"], prev[0]["lon"]],
                        "to": [new[0]["lat"], new[0]["lon"]]})
    for r, s in enumerate(new[:top_k], 1):
        dmin = min(dist(s, p) for p in prev[:top_k])
        if dmin > same_km:
            near = [(dist(s, p), k) for k, p in enumerate(prev, 1)]
            dn, kn = min(near)
            changes.append({"type": "new_top_area", "rank": r, "lat": s["lat"], "lon": s["lon"], "km_to_prev_top": round(dmin, 2),
                            "prev_rank": kn if dn <= same_km else None,
                            "p_within_1.5km": s.get("p_within_1.5km")})
    kept = sum(1 for s in new[:top] if any(dist(s, p) <= same_km for p in prev[:top]))
    overlap = kept / max(min(top, len(new)), 1)
    if overlap < 0.5:
        changes.append({"type": "reshuffle", "overlap": round(overlap, 2)})
    material = any(c["type"] in ("top_moved", "new_top_area") for c in changes)
    return material, changes


def layers_fingerprint(d: Path) -> str:
    h = hashlib.sha1()
    if d.exists():
        for p in sorted(d.glob("*.npz")):
            st = p.stat()   # ns mtime: a same-size rewrite within one second must still count as a change
            h.update(f"{p.name}:{st.st_size}:{st.st_mtime_ns}".encode())
    return h.hexdigest()


class EngineBridge(Analyzer):
    """See module docstring. Config keys: DEFAULTS plus run_fn, history_dir, hotspots_path, python."""
    name = "engine_bridge"
    tick_interval_s = 60.0

    def __init__(self, config=None):
        super().__init__(config)
        self._proc = None
        self._proc_t0 = 0.0
        self._log_f = None
        self._last_run = 0.0
        self._last_fp = None
        self._last_fail_event = 0.0
        self.prev = None

    def get(self, k):
        return setting(self.config, k, DEFAULTS.get(k))

    @property
    def history_dir(self) -> Path:
        d = resolve_path(self.get("history_dir") or OUTPUT / "history")
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _hotspots_path(self):
        if self.get("hotspots_path"):
            return resolve_path(self.get("hotspots_path"))
        return OUTPUT / ("scenario_hotspots.json" if self.get("mode") == "scenarios" else "hotspots.json")

    def load_previous(self):
        if self.prev is None:
            files = sorted(self.history_dir.glob("*_hotspots.json"))
            if files:
                try:
                    self.prev = json.loads(files[-1].read_text()).get("hotspots", [])
                except Exception:
                    self.prev = []
            else:
                self.prev = []
        return self.prev

    # ------------------------------------------------------------- running
    def _due(self, now):
        since = now - self._last_run
        if since < float(self.get("every_min")) * 60.0:
            return False
        if self.get("only_if_changed") and self._last_fp is not None:
            fp = layers_fingerprint(layers_dir(self.config))
            if fp == self._last_fp and since < float(self.get("force_every_min")) * 60.0:
                return False
        return True

    def _start_subprocess(self):
        mod = "hordejakt.scenarios" if self.get("mode") == "scenarios" else "hordejakt.cli"
        cmd = [self.get("python") or sys.executable, "-m", mod]
        if mod == "hordejakt.cli":
            cmd += ["--top", str(int(self.get("top")))]
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        self._log_f = open(self.history_dir / "engine_last.log", "w")
        self._proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=self._log_f, stderr=subprocess.STDOUT, env=env)
        self._proc_t0 = time.time()
        log.info("engine run started: %s (pid %s)", " ".join(cmd), self._proc.pid)

    def _poll_subprocess(self):
        """None while running, else (ok, result|error)."""
        rc = self._proc.poll()
        if rc is None:
            if time.time() - self._proc_t0 > float(self.get("timeout_s")):
                self._proc.kill()
                try:
                    self._proc.wait(timeout=10)   # reap it (no zombie, log file complete)
                except Exception:
                    pass
                rc = -9
            else:
                return None
        self._proc = None
        if self._log_f:
            self._log_f.close()
        if rc != 0:
            tail = (self.history_dir / "engine_last.log").read_text()[-1500:]
            return False, f"engine exited with {rc}: {tail}"
        try:
            return True, json.loads(self._hotspots_path().read_text())
        except Exception as e:
            return False, f"cannot read engine output: {e}"

    def run_once(self, ctx):
        """Synchronous run through run_fn (tests) -> handled result."""
        try:
            res = self.config["run_fn"]()
            return self.handle(ctx, True, res)
        except Exception as e:
            return self.handle(ctx, False, f"{e.__class__.__name__}: {e}")

    def on_tick(self, ctx):
        now = time.time()
        if self._proc is not None:
            r = self._poll_subprocess()
            if r is not None:
                self.handle(ctx, *r)
            return []
        if not self._due(now):
            return []
        self._last_run = now
        self._last_fp = layers_fingerprint(layers_dir(self.config))
        if self.config.get("run_fn"):
            self.run_once(ctx)
        else:
            try:
                self._start_subprocess()
            except Exception as e:
                self.handle(ctx, False, f"cannot start engine: {e}")
        return []

    # ------------------------------------------------------------- results
    def handle(self, ctx, ok, res):
        now = time.time()
        if not ok:
            log.warning("engine run failed: %s", str(res)[:300])
            if now - self._last_fail_event > 3600:
                self._last_fail_event = now
                ctx.db.add_event(from_unix(now), "engine_run_failed", str(res)[:300], {"error": str(res)[:2000]})
            return {"ok": False, "error": res}
        spots = res.get("hotspots", [])
        summary = res.get("summary", {})
        prev = self.load_previous()
        material, changes = compare_rankings(prev, spots, top=int(self.get("compare_top")), top_k=int(self.get("top_k")),
                                             move_km=float(self.get("move_km")), same_km=float(self.get("same_km")))
        live = [L["name"] for L in summary.get("layers", []) if str(L.get("name", "")).startswith("hw_")]
        rec = {"ts": from_unix(now).isoformat(), "mode": self.get("mode"), "material": material, "changes": changes,
               "credible_km2": summary.get("credible_km2") or res.get("credible_km2"),
               "live_layers": live, "hotspots": spots[: int(self.get("top"))]}
        ms = int(now * 1000)
        while True:  # unique, lexically time-ordered name even for runs within the same millisecond
            path = self.history_dir / f"{from_unix(ms / 1000.0):%Y%m%dT%H%M%S}{ms % 1000:03d}Z_hotspots.json"
            if not path.exists():
                break
            ms += 1
        path.write_text(dumps(rec, indent=1))
        self._prune()
        if material and prev:
            parts = []
            for c in changes:
                if c["type"] == "top_moved":
                    parts.append(f"top spot moved {c['km']:.1f} km to {c['to'][0]:.4f},{c['to'][1]:.4f}")
                elif c["type"] == "new_top_area":
                    was = f"was #{c['prev_rank']}" if c["prev_rank"] else "new"
                    parts.append(f"#{c['rank']} {c['lat']:.4f},{c['lon']:.4f} ({was})")
            ctx.db.add_event(from_unix(now), "engine_ranking_change", "hotspot ranking changed: " + "; ".join(parts),
                             {"changes": changes, "history": str(path), "top": spots[:3]})
        self.prev = spots
        return {"ok": True, "material": material, "changes": changes, "history": str(path)}

    def _prune(self):
        files = sorted(self.history_dir.glob("*_hotspots.json"))
        for p in files[: max(0, len(files) - int(self.get("keep_history")))]:
            try:
                p.unlink()
            except OSError:
                pass
