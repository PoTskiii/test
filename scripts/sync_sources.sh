#!/usr/bin/env bash
# Pull/refresh the community mirrors that carry default.no's open data.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/raw
sync() { # url dir [branch]
  if [ -d "data/raw/$2/.git" ]; then git -C "data/raw/$2" fetch --depth 1000 origin "${3:-main}" && git -C "data/raw/$2" reset --hard FETCH_HEAD
  else git clone --depth 1000 ${3:+--branch "$3"} "$1" "data/raw/$2"; fi
}
sync https://github.com/MagnusPladsen/hordejakten-2026 magnus main
sync https://github.com/mkekeoooo/hordejakten-2026 mkekeoooo main
sync https://github.com/mkekeoooo/hordejakten-2026 mk_bevis bevis/claude-2026-09-25
echo "synced: $(ls data/raw)"
