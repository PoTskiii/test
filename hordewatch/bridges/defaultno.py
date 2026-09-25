"""default.no poller: mirror the community site periodically and turn *changes* into events.

default.no (the largest community analysis site) publishes minute cuts of the
stream (``/cuts/YYYYMMDDHHMM_YYYYMMDDHHMM.mp4``, local time), JSON data layers
(sites, rejected areas, weather, flights ...) and pages. New cuts are replay
input for hordewatch (fill gaps in our own capture); new or changed data files
are things a human should look at quickly.

Mechanics
* Every ``every_min`` (default 30) the poller runs scripts/fetch_default_no.py
  in a subprocess (never blocking the monitor; polled on later ticks). The
  script writes data/raw/defaultno_live/<UTC stamp>/ with manifest.json (url, path,
  bytes, sha256, content_type) and links.txt (every URL seen, cut URLs included
  even without --video).
* The new snapshot is diffed with the previous *good* one (``diff_snapshots``,
  pure): new/removed/changed files by sha256, new cut URLs (parsed to real
  start/end times), and for changed JSON files an itemised diff of every list of
  records (sites, pins, areas: identity = id/name/title + rounded coordinates),
  so an event reads "steder.json: +2 (Ormsetra, Skramstad), -1 (Løten)".
* A snapshot with < 20 % of the previous file count is a failed fetch (network
  blocked, site down): it is never used as a baseline, and a
  ``defaultno_fetch_failed`` event is raised at most every 6 h.

Events: defaultno_snapshot (first run), defaultno_new_cuts, defaultno_new_files,
defaultno_data_changed, defaultno_removed_files, defaultno_fetch_failed.

Not in hordewatch.runner.ANALYZERS yet (owned elsewhere); register it with
``"defaultno_poller": "hordewatch.bridges.defaultno:DefaultNoPoller"`` or run it
standalone: ``python -m hordewatch.bridges.defaultno --every 30``.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from ..analyzers.base import Analyzer
from ..types import UTC
from .common import OSLO, ROOT, from_unix, load_state, resolve_path, save_state, setting

log = logging.getLogger("hordewatch.bridges.defaultno")

SNAP_DIR = ROOT / "data" / "raw" / "defaultno_live"
SCRIPT = ROOT / "scripts" / "fetch_default_no.py"
CUT_RE = re.compile(r"(\d{12})_(\d{12})\.(?:mp4|webm|mov|ts)$")
ID_KEYS = ("id", "navn", "name", "title", "tittel", "label", "k", "kallesignal", "sted")
LAT_KEYS = ("lat", "latitude", "breddegrad")
LON_KEYS = ("lon", "lng", "longitude", "lengdegrad")


# =========================================================================== pure diffing
def parse_cut(url):
    """Cut URL -> {url, name, start_local, end_local, start_utc, end_utc} or None."""
    m = CUT_RE.search(url.split("?")[0])
    if not m:
        return None
    a, b = (datetime.strptime(x, "%Y%m%d%H%M").replace(tzinfo=OSLO) for x in m.groups())
    return {"url": url, "name": Path(url.split("?")[0]).name, "start_local": a.isoformat(), "end_local": b.isoformat(),
            "start_utc": a.astimezone(UTC).isoformat(), "end_utc": b.astimezone(UTC).isoformat()}


def item_identity(it):
    """Stable identity of a JSON record: first id-like field + rounded coordinates."""
    if isinstance(it, dict):
        ident = next((str(it[k]) for k in ID_KEYS if k in it and isinstance(it[k], (str, int, float))), None)
        lat = next((it[k] for k in LAT_KEYS if isinstance(it.get(k), (int, float))), None)
        lon = next((it[k] for k in LON_KEYS if isinstance(it.get(k), (int, float))), None)
        if lat is None and isinstance(it.get("geometry"), dict):
            c = it["geometry"].get("coordinates")
            if isinstance(c, list) and len(c) >= 2 and all(isinstance(v, (int, float)) for v in c[:2]):
                lon, lat = c[0], c[1]
        coord = f"@{lat:.3f},{lon:.3f}" if lat is not None and lon is not None else ""
        if ident or coord:
            return (ident or "") + coord
    if isinstance(it, list) and len(it) >= 2 and all(isinstance(v, (int, float)) for v in it[:2]):
        return "@" + ",".join(f"{v:.3f}" for v in it[:2])
    return json.dumps(it, sort_keys=True, ensure_ascii=False)[:200]


def _label(ident):
    return ident.split("@")[0] or ident


def record_lists(obj, prefix=""):
    """{path: list} for every list of records (dicts, or coordinate lists) inside a JSON document."""
    out = {}
    if isinstance(obj, list):
        if obj and all(isinstance(x, (dict, list)) for x in obj):
            out[prefix or "."] = obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            out.update(record_lists(v, f"{prefix}.{k}" if prefix else k))
    return out


def json_diff(old, new, max_items=20):
    """Itemised diff of two JSON documents: per record list, added/removed/modified
    identities; plus changed scalar top-level keys."""
    out = {"lists": {}, "scalars": []}
    lo, ln = record_lists(old), record_lists(new)
    for path in sorted(set(lo) | set(ln)):
        a = {item_identity(x): x for x in lo.get(path, [])}
        b = {item_identity(x): x for x in ln.get(path, [])}
        add = [k for k in b if k not in a]
        rem = [k for k in a if k not in b]
        mod = [k for k in b if k in a and a[k] != b[k]]
        if add or rem or mod:
            out["lists"][path] = {"added": add[:max_items], "removed": rem[:max_items], "modified": mod[:max_items],
                                  "n_added": len(add), "n_removed": len(rem), "n_modified": len(mod),
                                  "n_old": len(a), "n_new": len(b)}
    if isinstance(old, dict) and isinstance(new, dict):
        for k in sorted(set(old) | set(new)):
            va, vb = old.get(k), new.get(k)
            if not isinstance(va, (dict, list)) and not isinstance(vb, (dict, list)) and va != vb:
                out["scalars"].append({"key": k, "old": va, "new": vb})
    return out


def load_snapshot(d: Path):
    d = Path(d)
    man = json.loads((d / "manifest.json").read_text()) if (d / "manifest.json").exists() else []
    links = (d / "links.txt").read_text().split() if (d / "links.txt").exists() else []
    return {"dir": d, "files": {m["url"]: m for m in man}, "links": set(links) | {m["url"] for m in man}}


def diff_snapshots(old_dir, new_dir, min_ratio=0.2):
    """Compare two fetch_default_no.py snapshots. Returns a dict with keys
    ok, new_files, removed_files, changed_files, new_cuts, json_changes."""
    new = load_snapshot(new_dir)
    if old_dir is None:
        return {"ok": bool(new["files"]), "first": True, "n_files": len(new["files"]), "new_files": [],
                "removed_files": [], "changed_files": [], "json_changes": {},
                "new_cuts": sorted((c for c in map(parse_cut, new["links"]) if c), key=lambda c: c["name"])}
    old = load_snapshot(old_dir)
    if len(new["files"]) < min_ratio * max(len(old["files"]), 1):
        return {"ok": False, "reason": f"snapshot has {len(new['files'])} files vs {len(old['files'])} before"}
    of, nf = old["files"], new["files"]
    added = sorted(u for u in nf if u not in of)
    removed = sorted(u for u in of if u not in nf)
    changed = sorted(u for u in nf if u in of and nf[u].get("sha256") != of[u].get("sha256"))
    old_cuts = {c["name"] for c in map(parse_cut, old["links"]) if c}
    new_cuts = sorted((c for c in map(parse_cut, new["links"]) if c and c["name"] not in old_cuts), key=lambda c: c["name"])
    jc = {}
    for u in changed + added:
        if not u.split("?")[0].endswith((".json", ".geojson")):
            continue
        try:
            nb = json.loads((Path(new_dir) / nf[u]["path"]).read_text())
            ob = json.loads((Path(old_dir) / of[u]["path"]).read_text()) if u in of else None
        except Exception as e:
            jc[u] = {"error": str(e)}
            continue
        jc[u] = json_diff(ob if ob is not None else {}, nb)
    return {"ok": True, "first": False, "n_files": len(nf), "new_files": added, "removed_files": removed,
            "changed_files": changed, "new_cuts": new_cuts, "json_changes": jc}


def diff_events(diff):
    """Turn a diff into [(kind, summary, value)] events."""
    ev = []
    if not diff.get("ok"):
        return [("defaultno_fetch_failed", f"default.no fetch looks incomplete: {diff.get('reason', '')}", diff)]
    if diff.get("first"):
        ev.append(("defaultno_snapshot", f"first default.no snapshot: {diff['n_files']} files, {len(diff['new_cuts'])} cuts",
                   {"n_files": diff["n_files"], "n_cuts": len(diff["new_cuts"])}))
        return ev
    if diff["new_cuts"]:
        c = diff["new_cuts"]
        ev.append(("defaultno_new_cuts", f"{len(c)} new default.no cuts ({c[0]['name']} .. {c[-1]['name']})", {"cuts": c}))
    data_new = [u for u in diff["new_files"] if not CUT_RE.search(u.split("?")[0])]
    if data_new:
        ev.append(("defaultno_new_files", f"{len(data_new)} new files on default.no: " + ", ".join(Path(u).name for u in data_new[:8]),
                   {"urls": data_new}))
    for u, d in diff["json_changes"].items():
        if "error" in d:
            continue
        parts = []
        for path, l in d["lists"].items():
            s = []
            if l["n_added"]:
                s.append(f"+{l['n_added']} ({', '.join(_label(x) for x in l['added'][:4])})")
            if l["n_removed"]:
                s.append(f"-{l['n_removed']} ({', '.join(_label(x) for x in l['removed'][:4])})")
            if l["n_modified"]:
                s.append(f"~{l['n_modified']}")
            parts.append(f"{path}: " + " ".join(s))
        if d["scalars"]:
            parts.append("keys changed: " + ", ".join(x["key"] for x in d["scalars"][:6]))
        if parts:
            ev.append(("defaultno_data_changed", f"{Path(u.split('?')[0]).name}: " + "; ".join(parts)[:400], {"url": u, "diff": d}))
    other = [u for u in diff["changed_files"] if u not in diff["json_changes"]]
    if other:
        ev.append(("defaultno_data_changed", f"{len(other)} other files changed: " + ", ".join(Path(u).name for u in other[:8]),
                   {"urls": other}))
    if diff["removed_files"]:
        ev.append(("defaultno_removed_files", f"{len(diff['removed_files'])} files removed from default.no",
                   {"urls": diff["removed_files"]}))
    return ev


# =========================================================================== poller
class DefaultNoPoller(Analyzer):
    """Periodic default.no mirror + diff (see module docstring).
    Config: every_min (30), cmd (list; default runs scripts/fetch_default_no.py), video (False),
    snapshots_dir, timeout_s (3600), max_files (5000), async (True)."""
    name = "defaultno_poller"
    tick_interval_s = 60.0

    def __init__(self, config=None):
        super().__init__(config)
        self._proc = None
        self._t0 = 0.0
        self._last = 0.0
        self._last_fail_event = 0.0

    def get(self, k, d=None):
        return setting(self.config, k, d)

    @property
    def snap_dir(self) -> Path:
        return resolve_path(self.get("snapshots_dir", SNAP_DIR))

    def command(self):
        cmd = self.get("cmd")
        if cmd:
            return list(cmd)
        c = [sys.executable, str(SCRIPT), "--max", str(int(self.get("max_files", 5000))), "--delay", "0.2"]
        if self.get("video", False):
            c.append("--video")
        return c

    def snapshots(self):
        if not self.snap_dir.exists():
            return []
        return sorted(p for p in self.snap_dir.iterdir() if p.is_dir() and not p.is_symlink() and re.match(r"\d{8}T\d{6}Z", p.name))

    def _start(self):
        self.snap_dir.mkdir(parents=True, exist_ok=True)
        self._logf = open(self.snap_dir / "poller_last.log", "w")
        self._proc = subprocess.Popen(self.command(), cwd=str(ROOT), stdout=self._logf, stderr=subprocess.STDOUT,
                                      env={**os.environ, "PYTHONPATH": str(ROOT)})
        self._t0 = time.time()

    def _finished(self):
        rc = self._proc.poll()
        if rc is None and time.time() - self._t0 < float(self.get("timeout_s", 3600)):
            return None
        if rc is None:
            self._proc.kill()
            rc = -9
        self._proc = None
        self._logf.close()
        return rc

    def process_new(self, ctx, rc=0):
        """Diff the newest snapshot against the last good one and emit events. Returns the events."""
        state = load_state(ctx.db, self.name, {})
        snaps = self.snapshots()
        base = state.get("baseline")
        newest = snaps[-1] if snaps else None
        now = time.time()
        if newest is None or newest.name == base:
            diff = {"ok": False, "reason": f"fetch produced no new snapshot (exit {rc})"}
        else:
            base_dir = self.snap_dir / base if base and (self.snap_dir / base).exists() else None
            try:
                diff = diff_snapshots(base_dir, newest)
            except Exception as e:
                diff = {"ok": False, "reason": f"diff failed: {e}"}
        events = diff_events(diff)
        for kind, summary, value in events:
            if kind == "defaultno_fetch_failed":
                if now - self._last_fail_event < 6 * 3600:
                    continue
                self._last_fail_event = now
                log.warning("default.no: %s", summary)
            ctx.db.add_event(from_unix(now), kind, summary, value)
        if diff.get("ok"):
            state["baseline"] = newest.name
            state["last_ok"] = now
        elif newest is not None and newest.name != base:
            self._discard_if_empty(newest)
        save_state(ctx.db, self.name, state)
        return events

    def _discard_if_empty(self, d: Path):
        try:
            man = json.loads((d / "manifest.json").read_text()) if (d / "manifest.json").exists() else []
            if not man and all(p.name in ("manifest.json", "links.txt") for p in d.iterdir()):
                for p in d.iterdir():
                    p.unlink()
                d.rmdir()
        except OSError:
            pass

    def on_tick(self, ctx):
        now = time.time()
        if self._proc is not None:
            rc = self._finished()
            if rc is not None:
                self.process_new(ctx, rc)
            return []
        if now - self._last < float(self.get("every_min", 30)) * 60.0:
            return []
        self._last = now
        if self.get("async", True):
            try:
                self._start()
            except Exception as e:
                log.warning("default.no poller could not start the fetch: %s", e)
        else:
            try:
                rc = subprocess.run(self.command(), cwd=str(ROOT), capture_output=True, timeout=float(self.get("timeout_s", 3600)),
                                    env={**os.environ, "PYTHONPATH": str(ROOT)}).returncode
            except Exception as e:
                log.warning("default.no fetch failed: %s", e)
                rc = -1
            self.process_new(ctx, rc)
        return []


def main(argv=None):
    ap = argparse.ArgumentParser(prog="hordewatch.bridges.defaultno")
    ap.add_argument("--db", default=str(ROOT / "data" / "hordewatch" / "hordewatch.sqlite"))
    ap.add_argument("--every", type=float, default=30.0, help="minutes between fetches")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--video", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    from ..analyzers.base import Context
    from ..db import DB
    from ..types import StreamClock
    ctx = Context(db=DB(a.db), config={}, clock=StreamClock())
    p = DefaultNoPoller({"every_min": a.every, "async": False, "video": a.video})
    while True:
        p._last = 0.0
        p.on_tick(ctx)
        for kind, summary in ctx.db.con.execute("SELECT kind, summary FROM events ORDER BY id DESC LIMIT 5"):
            print(kind, summary)
        if a.once:
            break
        time.sleep(a.every * 60.0)


if __name__ == "__main__":
    main()
