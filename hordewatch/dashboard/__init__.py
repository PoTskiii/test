"""hordewatch dashboard: FastAPI JSON/SSE API + single-page UI (static/index.html).

    .venv/bin/python -m hordewatch.dashboard --db data/hordewatch/hordewatch.sqlite --port 8787

See app.py for the design; notify.py for optional ntfy push alerts.
"""


def create_app(*args, **kwargs):
    """Lazy wrapper around :func:`hordewatch.dashboard.app.create_app` (keeps package import light)."""
    from .app import create_app as _create_app
    return _create_app(*args, **kwargs)
