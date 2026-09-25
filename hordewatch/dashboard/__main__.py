"""Start the dashboard:  .venv/bin/python -m hordewatch.dashboard --db data/hordewatch/hordewatch.sqlite --port 8787

Options can come from the runner's hordewatch.yaml (``--config``): ``db``, ``archive_dir``, ``camera``,
``clock`` and the optional ``dashboard`` section (host, port, sun_ref, media_roots, ntfy{...}).
Command-line flags win over the config file. Binds to 127.0.0.1 by default: the API can acknowledge
alerts and override calibration, so expose it (``--host 0.0.0.0``) only on a trusted network or
behind an authenticating reverse proxy.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m hordewatch.dashboard", description="hordewatch live dashboard")
    ap.add_argument("--config", help="hordewatch.yaml (same file as the runner)")
    ap.add_argument("--db", help="SQLite data table (default: config db or data/hordewatch/hordewatch.sqlite)")
    ap.add_argument("--output", help="hordejakt output dir with map.html / hotspots.json (default: output/)")
    ap.add_argument("--archive-dir", help="frame archive dir (default: config archive_dir)")
    ap.add_argument("--layers-dir", help="live evidence layers dir (default: data/hordewatch/layers)")
    ap.add_argument("--host", help="bind address (default 127.0.0.1)")
    ap.add_argument("--port", type=int, help="port (default 8787)")
    ap.add_argument("--ntfy-topic", default=os.environ.get("HORDEWATCH_NTFY_TOPIC"),
                    help="push new alerts to this ntfy topic (env HORDEWATCH_NTFY_TOPIC)")
    ap.add_argument("--ntfy-server", default=os.environ.get("HORDEWATCH_NTFY_SERVER"), help="ntfy server (default https://ntfy.sh)")
    ap.add_argument("--public-url", help="URL of this dashboard for notification clicks")
    ap.add_argument("--log-level", default="info")
    return ap


def resolve_settings(a) -> dict:
    """Merge CLI flags, the config file and defaults into create_app/uvicorn arguments."""
    from ..runner import load_config
    from .. import ROOT
    cfg = load_config(a.config) if a.config else load_config(None)
    dash = dict(cfg.get("dashboard") or {})
    ntfy = dict(dash.get("ntfy") or {})
    if a.ntfy_topic:
        ntfy["topic"] = a.ntfy_topic
    if a.ntfy_server:
        ntfy["server"] = a.ntfy_server
    host = a.host or dash.get("host") or "127.0.0.1"
    port = int(a.port or dash.get("port") or 8787)
    if ntfy.get("topic") and not ntfy.get("click_url"):
        ntfy["click_url"] = a.public_url or f"http://{'localhost' if host in ('0.0.0.0', '127.0.0.1') else host}:{port}/"
    dash["ntfy"] = ntfy
    cfg["dashboard"] = dash

    def rel(p):
        if p is None:
            return None
        p = Path(p)
        return p if p.is_absolute() else (Path.cwd() / p if (Path.cwd() / p).exists() else ROOT / p)

    db = rel(a.db or cfg.get("db"))
    return {"db_path": db, "output_dir": rel(a.output) if a.output else ROOT / "output",
            "archive_dir": rel(a.archive_dir) if a.archive_dir else None,
            "layers_dir": rel(a.layers_dir) if a.layers_dir else None, "config": cfg, "host": host, "port": port}


def main(argv=None):
    a = build_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, a.log_level.upper(), logging.INFO),
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    s = resolve_settings(a)
    try:
        import uvicorn
    except ImportError:  # pragma: no cover
        sys.exit("uvicorn is not installed: pip install -r requirements-hordewatch.txt")
    from .app import create_app
    app = create_app(s["db_path"], s["output_dir"], archive_dir=s["archive_dir"], layers_dir=s["layers_dir"],
                     config=s["config"])
    logging.getLogger("hordewatch.dashboard").info("dashboard on http://%s:%d/  (db %s)", s["host"], s["port"], s["db_path"])
    uvicorn.run(app, host=s["host"], port=s["port"], log_level=a.log_level.lower(), timeout_graceful_shutdown=3)


if __name__ == "__main__":
    main()
