#!/usr/bin/env python3
"""Mirror default.no: every page, every linked data file (the downloads at the
bottom of the page included) and, optionally, the video cuts.

Needs outbound access to default.no (this cloud environment blocks it unless
the environment's network access allows the domain).

    .venv/bin/python scripts/fetch_default_no.py            # pages + data
    .venv/bin/python scripts/fetch_default_no.py --video    # also /cuts/*.mp4

Output: data/raw/defaultno_live/<UTC stamp>/ with the files under their URL
paths, plus manifest.json (url, path, bytes, sha256, content-type) and
links.txt (every URL discovered, including off-site ones).
"""
import argparse
import hashlib
import json
import re
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests

BASE = "https://default.no/"
ROOT = Path(__file__).resolve().parent.parent
PAGE_EXT = {"", ".php", ".html", ".htm"}
DATA_EXT = {".json", ".geojson", ".csv", ".tsv", ".txt", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg",
            ".zip", ".gz", ".tif", ".tiff", ".kml", ".kmz", ".gpx", ".npz", ".npy", ".parquet", ".xlsx",
            ".pdf", ".md", ".js", ".css", ".wav", ".mp3", ".ogg", ".m3u8", ".xml"}
VIDEO_EXT = {".mp4", ".webm", ".mov", ".ts"}
# quoted relative/absolute paths inside inline JS/JSON, e.g. fetch('data/x.json')
QUOTED = re.compile(r"""["'`]((?:https?://default\.no)?/?[A-Za-z0-9_./%-]+\.(?:%s))(?:\?[^"'`]*)?["'`]"""
                    % "|".join(sorted(e.lstrip(".") for e in DATA_EXT | VIDEO_EXT | {".php"})))
ATTR = re.compile(r"""(?:href|src|data-src|poster|action)\s*=\s*["']([^"'#]+)["']""", re.I)


def ext_of(url):
    p = urlparse(url).path
    return Path(p).suffix.lower()


def same_site(url):
    return urlparse(url).netloc in ("default.no", "www.default.no")


def local_path(out, url):
    u = urlparse(url)
    p = u.path.lstrip("/") or "index.html"
    if p.endswith("/"):
        p += "index.html"
    if u.query:
        p += "__" + re.sub(r"[^A-Za-z0-9_.=-]", "_", u.query)[:120]
    return out / p


def discover(text, page_url):
    found = set()
    for m in ATTR.finditer(text):
        found.add(urljoin(page_url, m.group(1).strip()))
    for m in QUOTED.finditer(text):
        found.add(urljoin(page_url, m.group(1)))
    return {urldefrag(u)[0] for u in found if u.startswith(("http://", "https://"))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", action="store_true", help="also download video cuts (large)")
    ap.add_argument("--max", type=int, default=5000, help="max files")
    ap.add_argument("--delay", type=float, default=0.2, help="politeness delay between requests (s)")
    a = ap.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "data" / "raw" / "defaultno_live" / stamp
    out.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    s.headers["User-Agent"] = "hordejakt-mirror/1.0 (personal analysis; polite)"

    queue = deque([BASE, urljoin(BASE, "map.php")])
    seen, manifest, all_links = set(), [], set()
    while queue and len(manifest) < a.max:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        e = ext_of(url)
        if e in VIDEO_EXT and not a.video:
            continue
        try:
            r = s.get(url, timeout=60)
        except requests.RequestException as ex:
            print(f"ERR {url}: {ex}", file=sys.stderr)
            continue
        ct = r.headers.get("content-type", "")
        print(f"{r.status_code} {len(r.content):>9} {url}")
        if r.status_code != 200:
            continue
        dest = local_path(out, url)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.content)
        manifest.append({"url": url, "path": str(dest.relative_to(out)), "bytes": len(r.content),
                         "sha256": hashlib.sha256(r.content).hexdigest(), "content_type": ct})
        if "html" in ct or "javascript" in ct or "json" in ct or e in PAGE_EXT | {".js", ".json"}:
            links = discover(r.text, url)
            all_links |= links
            for l in sorted(links):
                if same_site(l) and l not in seen and (ext_of(l) in PAGE_EXT | DATA_EXT | VIDEO_EXT):
                    queue.append(l)
        time.sleep(a.delay)

    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    (out / "links.txt").write_text("\n".join(sorted(all_links)))
    latest = out.parent / "latest"
    if latest.is_symlink() or latest.exists():
        latest.unlink()
    latest.symlink_to(out.name)
    print(f"\n{len(manifest)} files -> {out}")


if __name__ == "__main__":
    main()
