#!/usr/bin/env bash
# hordewatch_all.sh - start the hordewatch runner (ingest + analyzers + bridges) and the dashboard,
# each supervised (restart with exponential backoff), with logs under data/hordewatch/logs/.
#
# Usage:
#   scripts/hordewatch_all.sh [-c hordewatch.yaml] [-p 8787] [--host 127.0.0.1]
#                             [--no-runner] [--no-dashboard] [--start-ollama] [--dry-run]
#
# Environment: PYTHON (interpreter), HORDEWATCH_CONFIG, HORDEWATCH_PORT, HORDEWATCH_LOG_DIR,
#              HORDEWATCH_NTFY_TOPIC (push alerts to ntfy; see hordewatch/dashboard/notify.py)
#
# Stop with Ctrl-C (or kill the script): both services get SIGTERM and are waited for.
# Logs: <log dir>/runner.log, dashboard.log (and ollama.log with --start-ollama); rotated to *.1 at
# start when larger than 50 MB. Follow them with:  tail -F data/hordewatch/logs/*.log
set -u

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT" || exit 1

PY=${PYTHON:-}
if [ -z "$PY" ]; then
  if [ -x "$ROOT/.venv/bin/python" ]; then PY="$ROOT/.venv/bin/python"; else PY=$(command -v python3 || true); fi
fi
[ -n "$PY" ] || { echo "hordewatch_all: no python found (set PYTHON=...)" >&2; exit 1; }

CONFIG=${HORDEWATCH_CONFIG:-}
if [ -z "$CONFIG" ] && [ -f "$ROOT/hordewatch.yaml" ]; then CONFIG="$ROOT/hordewatch.yaml"; fi
PORT=${HORDEWATCH_PORT:-8787}
HOST=127.0.0.1
RUN_RUNNER=1
RUN_DASH=1
START_OLLAMA=0
DRY=0
LOG_DIR=${HORDEWATCH_LOG_DIR:-$ROOT/data/hordewatch/logs}

usage() { sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'; }
while [ $# -gt 0 ]; do
  case "$1" in
    -c|--config) CONFIG=$2; shift 2 ;;
    -p|--port) PORT=$2; shift 2 ;;
    --host) HOST=$2; shift 2 ;;
    --no-runner) RUN_RUNNER=0; shift ;;
    --no-dashboard) RUN_DASH=0; shift ;;
    --start-ollama) START_OLLAMA=1; shift ;;
    --log-dir) LOG_DIR=$2; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "hordewatch_all: unknown option $1" >&2; usage >&2; exit 2 ;;
  esac
done
if [ -n "$CONFIG" ] && [ ! -f "$CONFIG" ]; then echo "hordewatch_all: config $CONFIG not found" >&2; exit 2; fi

say() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] hordewatch_all: $*"; }

# ------------------------------------------------------------------ settings from the runner config
CFG_INFO=$("$PY" - "$CONFIG" <<'PYEOF' 2>/dev/null
import sys
from hordewatch.runner import load_config
c = load_config(sys.argv[1] or None)
vlm = c.get("vlm") or {}
src = c.get("source") or {}
print(c["db"])
print(vlm.get("url", "http://localhost:11434") if "vlm" in (c.get("analyzers") or []) else "")
print(vlm.get("model", "llava:7b"))
print(src.get("type", "live"))
PYEOF
)
if [ -z "$CFG_INFO" ]; then echo "hordewatch_all: cannot load the hordewatch config with $PY (missing deps? pip install -r requirements-hordewatch.txt)" >&2; exit 1; fi
DB=$(echo "$CFG_INFO" | sed -n 1p)
VLM_URL=$(echo "$CFG_INFO" | sed -n 2p)
VLM_MODEL=$(echo "$CFG_INFO" | sed -n 3p)
SRC_TYPE=$(echo "$CFG_INFO" | sed -n 4p)

RUNNER_CMD=("$PY" -m hordewatch.runner)
[ -n "$CONFIG" ] && RUNNER_CMD+=(--config "$CONFIG")
DASH_CMD=("$PY" -m hordewatch.dashboard --db "$DB" --host "$HOST" --port "$PORT")
[ -n "$CONFIG" ] && DASH_CMD+=(--config "$CONFIG")

# ------------------------------------------------------------------ preflight hints (never fatal)
hints() {
  if [ "$SRC_TYPE" = "live" ]; then
    command -v ffmpeg >/dev/null 2>&1 || say "HINT: ffmpeg not found - the live source needs it (apt install ffmpeg)"
    if ! command -v yt-dlp >/dev/null 2>&1 && ! "$PY" -c 'import yt_dlp' >/dev/null 2>&1 && ! command -v streamlink >/dev/null 2>&1; then
      say "HINT: neither yt-dlp nor streamlink found - pip install yt-dlp (needed to resolve the YouTube live URL)"
    fi
  fi
  if [ -n "$VLM_URL" ]; then
    if command -v curl >/dev/null 2>&1 && curl --noproxy '*' -fsS --max-time 2 "$VLM_URL/api/tags" >/dev/null 2>&1; then
      say "local VLM reachable at $VLM_URL (model $VLM_MODEL)"
    elif [ "$START_OLLAMA" = 1 ]; then
      say "starting ollama (log: $LOG_DIR/ollama.log)"
    else
      say "HINT: the 'vlm' analyzer expects a local vision LLM at $VLM_URL, which is not answering."
      say "      CPU is fine:  ollama serve &  ollama pull $VLM_MODEL   (or rerun this script with --start-ollama)"
      say "      Until then the VLM analyzer stays idle; OCR, photometry, audio and bridges still run."
    fi
  fi
  "$PY" -c 'import pytesseract' >/dev/null 2>&1 || command -v tesseract >/dev/null 2>&1 || \
    say "note: tesseract not installed - OCR uses RapidOCR only (optional: apt install tesseract-ocr tesseract-ocr-nor)"
}

if [ "$DRY" = 1 ]; then
  echo "ROOT=$ROOT"
  echo "PYTHON=$PY"
  echo "CONFIG=${CONFIG:-<defaults>}"
  echo "DB=$DB"
  echo "LOG_DIR=$LOG_DIR"
  [ "$RUN_RUNNER" = 1 ] && echo "runner: ${RUNNER_CMD[*]}"
  [ "$RUN_DASH" = 1 ] && echo "dashboard: ${DASH_CMD[*]}  ->  http://$HOST:$PORT/"
  [ "$START_OLLAMA" = 1 ] && echo "ollama: ollama serve"
  hints
  exit 0
fi

mkdir -p "$LOG_DIR"
rotate() { local f=$1; if [ -f "$f" ] && [ "$(wc -c <"$f")" -gt 52428800 ]; then mv -f "$f" "$f.1"; fi; }

STOPPING=0
PIDS=()

# supervise NAME LOGFILE CMD...: run CMD, restart on exit with backoff 5 s .. 5 min (reset after 10 min up)
supervise() {
  local name=$1 log=$2; shift 2
  local child=0 backoff=5 t0 rc
  trap 'if [ "$child" -gt 0 ]; then kill -TERM "$child" 2>/dev/null; wait "$child" 2>/dev/null; fi; exit 0' TERM INT
  while true; do
    rotate "$log"
    t0=$(date +%s)
    say "starting $name: $*" >>"$log"
    "$@" >>"$log" 2>&1 &
    child=$!
    wait "$child"; rc=$?
    child=0
    if [ $(( $(date +%s) - t0 )) -gt 600 ]; then backoff=5; fi
    say "$name exited with code $rc; restarting in ${backoff}s" >>"$log"
    sleep "$backoff" &
    wait $!
    backoff=$(( backoff * 2 )); [ "$backoff" -gt 300 ] && backoff=300
  done
}

cleanup() {
  [ "$STOPPING" = 1 ] && return
  STOPPING=1
  say "stopping (${PIDS[*]:-})"
  for p in "${PIDS[@]:-}"; do [ -n "$p" ] && kill -TERM "$p" 2>/dev/null; done
  for p in "${PIDS[@]:-}"; do [ -n "$p" ] && wait "$p" 2>/dev/null; done
  say "stopped"
  exit 0
}
trap cleanup INT TERM

hints

if [ "$START_OLLAMA" = 1 ] && [ -n "$VLM_URL" ]; then
  if command -v ollama >/dev/null 2>&1; then
    if ! curl --noproxy '*' -fsS --max-time 2 "$VLM_URL/api/tags" >/dev/null 2>&1; then
      supervise ollama "$LOG_DIR/ollama.log" ollama serve &
      PIDS+=($!)
      ( sleep 8; ollama list 2>/dev/null | grep -q "${VLM_MODEL%%:*}" || { say "pulling $VLM_MODEL (one-time, several GB)"; ollama pull "$VLM_MODEL" >>"$LOG_DIR/ollama.log" 2>&1; } ) &
    fi
  else
    say "HINT: --start-ollama given but 'ollama' is not installed: https://ollama.com/download"
  fi
fi

if [ "$RUN_RUNNER" = 1 ]; then
  supervise runner "$LOG_DIR/runner.log" "${RUNNER_CMD[@]}" &
  PIDS+=($!)
  say "runner started (log: $LOG_DIR/runner.log)"
fi
if [ "$RUN_DASH" = 1 ]; then
  supervise dashboard "$LOG_DIR/dashboard.log" "${DASH_CMD[@]}" &
  PIDS+=($!)
  say "dashboard: http://$HOST:$PORT/  (log: $LOG_DIR/dashboard.log)"
fi
[ ${#PIDS[@]} -gt 0 ] || { say "nothing to run"; exit 0; }
say "follow the logs with:  tail -F $LOG_DIR/*.log   - Ctrl-C stops everything"
while true; do wait; [ "$STOPPING" = 1 ] && break; sleep 1; done
