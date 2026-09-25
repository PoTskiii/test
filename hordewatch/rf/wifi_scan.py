"""Passive WiFi survey for the Hordejakten uplink search.

Cross-platform, **receive-only** WiFi scanner. It never associates with, probes,
or transmits to any network: it reads the beacons every access point already
broadcasts to the air (SSID, BSSID, channel, RSSI), tags the ones that look like
the box's uplink or a nearby crew camp, logs each observation with a GPS fix to
CSV, tells you whether a chosen AP is getting *warmer or colder* as you walk, and
- once you have samples from a few spots - estimates the transmitter location by
RSSI multilateration (via :mod:`hordewatch.rf.foxhunt`).

Why WiFi helps find the box
---------------------------
The forest stream is uplinked over Starlink or a 4G/5G router. Both broadcast
WiFi you can hear:
* A Starlink kit's router SSID defaults to ``STARLINK`` (or ``STARLINK-XXXX`` /
  ``Starlink-…`` on newer Gen-3 units) unless the crew renamed it. Its BSSID OUI
  is often SpaceX-registered.
* Field 4G/5G routers (Teltonika RUTx, Peplink/Pepwave, Huawei, generic MiFi)
  broadcast management SSIDs like ``RUT…``, ``Teltonika…``, ``Pepwave_…``,
  ``HUAWEI-…``.
* A crew camp/vehicle leaks phones, a GoPro/DJI camera AP, a personal hotspot.
2.4 GHz beacons carry ~50-200 m through forest (much less than open air, more
than 5 GHz); so a hit at all means you are close.

Norwegian legal / ethical context (plain words)
------------------------------------------------
Ekomloven: *receiving* radio signals is generally allowed, but you may not
*use or pass on the content* of communications not meant for you, and you must
not interfere. This tool only records the beacon metadata every AP publicly
advertises (SSID/BSSID/RSSI/channel) - it does not connect, does not capture
traffic, does not crack anything. Do not connect to a network you find. Respect
the organisers' rules; on private land during hunting season wear high-vis.

Platforms & commands (all read-only "list what's on the air"):
* Linux:   ``nmcli -t -f SSID,BSSID,CHAN,FREQ,SIGNAL,SECURITY dev wifi list``
           or ``iw dev <if> scan`` (real dBm; needs root/cap).
* macOS:   legacy ``airport -s``; on 14+ ``wdutil info`` / CoreWLAN.
* Windows: ``netsh wlan show networks mode=bssid``.
* Android: Termux ``termux-wifi-scaninfo`` (+ ``termux-location`` for GPS).

Every scan command is run defensively; a missing tool logs once and yields [].
"""
from __future__ import annotations

import csv
import json
import logging
import platform
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

log = logging.getLogger("hordewatch.rf.wifi")

UTC = timezone.utc


# --------------------------------------------------------------------------- interesting SSIDs / OUIs
# (label, compiled pattern). Ordered; a SSID may match several.
_SSID_RULES = [
    ("starlink", re.compile(r"^\s*starlink", re.I)),
    ("starlink", re.compile(r"\bstarlink\b", re.I)),
    ("cellular_router:teltonika", re.compile(r"\b(rut\d|teltonika)", re.I)),
    ("cellular_router:peplink", re.compile(r"\b(pepwave|peplink|pep[_-])", re.I)),
    ("cellular_router:huawei", re.compile(r"^\s*huawei[-_]", re.I)),
    ("cellular_router:zte", re.compile(r"\b(zte|mf\d{2,})", re.I)),
    ("cellular_router:mifi", re.compile(r"\b(mifi|mobile\s*hotspot|4g[-_ ]?wifi|5g[-_ ]?wifi)", re.I)),
    ("cellular_router:netgear_nighthawk_m", re.compile(r"\bnighthawk[- ]?m", re.I)),
    ("camera:gopro", re.compile(r"\bgopro", re.I)),
    ("camera:dji", re.compile(r"\b(dji|osmo|mavic|mini\s?\d)", re.I)),
    ("camera:insta360", re.compile(r"insta360", re.I)),
    ("phone_hotspot", re.compile(r"\b(iphone|androidap|galaxy|samsung|pixel)\b", re.I)),
    ("horde", re.compile(r"horde", re.I)),
    ("crew_hint", re.compile(r"\b(nrk|produksjon|crew|camp|regi|opptak)\b", re.I)),
]

# BSSID OUI prefixes (upper-case, ':' separated first three octets) -> label.
_OUI = {
    # SpaceX / Starlink (a subset of publicly seen Starlink router OUIs)
    "F8:0C:F3": "starlink", "34:6F:24": "starlink", "F0:9F:C2": "starlink_or_ubnt",
    # GoPro
    "D4:D9:19": "camera:gopro", "F6:DD:9E": "camera:gopro",
    # DJI
    "60:60:1F": "camera:dji", "34:D2:62": "camera:dji",
    # Teltonika
    "00:1E:42": "cellular_router:teltonika",
    # Huawei (very common; weak signal only)
    "00:E0:FC": "cellular_router:huawei",
}


def flag_ssid(ssid: Optional[str], bssid: Optional[str] = None) -> List[str]:
    """Return interest tags for an AP (empty if nothing notable)."""
    tags: List[str] = []
    s = ssid or ""
    for label, pat in _SSID_RULES:
        if pat.search(s) and label not in tags:
            tags.append(label)
    if not s.strip():
        tags.append("hidden_ssid")
    if bssid:
        oui = ":".join(bssid.upper().split(":")[:3])
        lab = _OUI.get(oui)
        if lab and lab not in tags:
            tags.append(f"oui:{lab}")
    return tags


# --------------------------------------------------------------------------- data model
@dataclass
class WifiAP:
    ssid: str
    bssid: str
    rssi_dbm: Optional[float]
    channel: Optional[int]
    freq_mhz: Optional[int] = None
    band: Optional[str] = None
    security: str = ""
    ts: str = ""
    lat: Optional[float] = None
    lon: Optional[float] = None
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.freq_mhz and not self.channel:
            self.channel = freq_to_channel(self.freq_mhz)
        if self.channel and not self.freq_mhz:
            self.freq_mhz = channel_to_freq(self.channel)
        if not self.band:
            self.band = channel_band(self.channel, self.freq_mhz)
        if not self.tags:
            self.tags = flag_ssid(self.ssid, self.bssid)
        if not self.ts:
            self.ts = datetime.now(UTC).isoformat(timespec="seconds")

    @property
    def interesting(self) -> bool:
        return bool([t for t in self.tags if t != "hidden_ssid"])


CSV_FIELDS = ["ts", "lat", "lon", "ssid", "bssid", "rssi_dbm", "channel", "freq_mhz",
              "band", "security", "tags"]


def channel_band(channel, freq_mhz=None) -> Optional[str]:
    if freq_mhz:
        if 2400 <= freq_mhz < 2500:
            return "2.4GHz"
        if 4900 <= freq_mhz < 5900:
            return "5GHz"
        if 5925 <= freq_mhz <= 7125:
            return "6GHz"
    if channel is None:
        return None
    if channel <= 14:
        return "2.4GHz"
    if channel <= 177:
        return "5GHz"
    return "6GHz"


def channel_to_freq(ch: int) -> Optional[int]:
    if ch is None:
        return None
    if 1 <= ch <= 13:
        return 2407 + 5 * ch
    if ch == 14:
        return 2484
    if 32 <= ch <= 177:
        return 5000 + 5 * ch
    return None


def freq_to_channel(mhz: int) -> Optional[int]:
    if mhz is None:
        return None
    if mhz == 2484:
        return 14
    if 2412 <= mhz <= 2472:
        return (mhz - 2407) // 5
    if 5000 <= mhz <= 5900:
        return (mhz - 5000) // 5
    if 5955 <= mhz <= 7115:
        return (mhz - 5950) // 5      # 6 GHz 20 MHz channels
    return None


def pct_to_dbm(pct: float) -> float:
    """nmcli/netsh report signal quality 0-100 %. Convert to an approximate dBm
    (linear map -100 dBm at 0 % to -50 dBm at 100 %, the common WLAN heuristic)."""
    pct = max(0.0, min(100.0, float(pct)))
    return round(pct / 2.0 - 100.0, 1)


# --------------------------------------------------------------------------- parsers
def _split_nmcli_terse(line: str) -> List[str]:
    """Split an nmcli ``-t`` line on ':' while respecting '\\:' escapes (BSSIDs)."""
    out, cur, esc = [], [], False
    for c in line:
        if esc:
            cur.append(c)
            esc = False
        elif c == "\\":
            esc = True
        elif c == ":":
            out.append("".join(cur))
            cur = []
        else:
            cur.append(c)
    out.append("".join(cur))
    return out


def parse_nmcli(text: str) -> List[WifiAP]:
    """Parse ``nmcli -t -f SSID,BSSID,CHAN,FREQ,SIGNAL,SECURITY dev wifi list``.

    SIGNAL is a 0-100 % quality (converted to approximate dBm). FREQ is like
    ``2412 MHz``. Hidden networks have an empty SSID field.
    """
    aps = []
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        f = _split_nmcli_terse(raw)
        if len(f) < 6:
            continue
        ssid, bssid, chan, freq, signal, security = f[0], f[1], f[2], f[3], f[4], ":".join(f[5:])
        try:
            ch = int(chan) if chan.strip() else None
        except ValueError:
            ch = None
        mhz = None
        m = re.search(r"(\d+)", freq)
        if m:
            mhz = int(m.group(1))
        rssi = pct_to_dbm(float(signal)) if signal.strip().replace(".", "").isdigit() else None
        aps.append(WifiAP(ssid=ssid, bssid=bssid.upper(), rssi_dbm=rssi, channel=ch,
                          freq_mhz=mhz, security=security.strip()))
    return aps


def parse_iw(text: str) -> List[WifiAP]:
    """Parse ``iw dev <if> scan`` output (real dBm)."""
    aps = []
    cur = None

    def flush():
        nonlocal cur
        if cur and cur.get("bssid"):
            aps.append(WifiAP(ssid=cur.get("ssid", ""), bssid=cur["bssid"].upper(),
                              rssi_dbm=cur.get("rssi"), channel=cur.get("channel"),
                              freq_mhz=cur.get("freq"), security=cur.get("security", "")))
        cur = None

    for line in text.splitlines():
        s = line.strip()
        mb = re.match(r"BSS\s+([0-9a-fA-F:]{17})", s)
        if mb:
            flush()
            cur = {"bssid": mb.group(1)}
            continue
        if cur is None:
            continue
        m = re.match(r"signal:\s*(-?\d+(?:\.\d+)?)\s*dBm", s)
        if m:
            cur["rssi"] = float(m.group(1))
        elif s.startswith("SSID:"):
            cur["ssid"] = s[5:].strip()
        elif s.startswith("freq:"):
            cur["freq"] = int(float(s.split(":", 1)[1].strip()))
        elif "DS Parameter set: channel" in s:
            m = re.search(r"channel\s+(\d+)", s)
            if m:
                cur["channel"] = int(m.group(1))
        elif s.startswith("RSN:") or s.startswith("WPA:"):
            cur["security"] = (cur.get("security", "") + " " + s.split(":", 1)[0]).strip()
    flush()
    return aps


def parse_netsh(text: str) -> List[WifiAP]:
    """Parse Windows ``netsh wlan show networks mode=bssid``.

    Each SSID block lists one or more BSSIDs with a Signal % and a Channel.
    Signal % is converted to approximate dBm.
    """
    aps = []
    ssid = None
    auth = ""
    pending = {}

    def flush():
        if pending.get("bssid"):
            aps.append(WifiAP(ssid=ssid or "", bssid=pending["bssid"].upper(),
                              rssi_dbm=pct_to_dbm(pending["signal"]) if "signal" in pending else None,
                              channel=pending.get("channel"), security=auth))
        pending.clear()

    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"SSID\s+\d+\s*:\s*(.*)$", s)
        if m:
            flush()
            ssid = m.group(1).strip()
            auth = ""
            continue
        m = re.match(r"Authentication\s*:\s*(.*)$", s)
        if m:
            auth = m.group(1).strip()
            continue
        m = re.match(r"BSSID\s+\d+\s*:\s*([0-9a-fA-F:]{17})", s)
        if m:
            flush()
            pending["bssid"] = m.group(1)
            continue
        m = re.match(r"Signal\s*:\s*(\d+)%", s)
        if m:
            pending["signal"] = float(m.group(1))
            continue
        m = re.match(r"Channel\s*:\s*(\d+)", s)
        if m:
            pending["channel"] = int(m.group(1))
    flush()
    return aps


def parse_termux(text_or_obj) -> List[WifiAP]:
    """Parse ``termux-wifi-scaninfo`` JSON (Android). rssi is real dBm,
    frequency in MHz."""
    data = text_or_obj if isinstance(text_or_obj, (list, dict)) else json.loads(text_or_obj)
    if isinstance(data, dict):
        data = data.get("networks", [data])
    aps = []
    for e in data:
        mhz = e.get("frequency_mhz") or e.get("frequency")
        if mhz and mhz > 100000:      # some builds report Hz
            mhz = int(mhz / 1000)
        aps.append(WifiAP(ssid=e.get("ssid", "").strip('"'), bssid=str(e.get("bssid", "")).upper(),
                          rssi_dbm=_num(e.get("rssi") or e.get("level")),
                          channel=e.get("channel"), freq_mhz=int(mhz) if mhz else None))
    return aps


def parse_airport(text: str) -> List[WifiAP]:
    """Parse legacy macOS ``airport -s`` columns SSID BSSID RSSI CHANNEL ... .
    (deprecated on macOS 14+, kept for older machines / Hackintosh)."""
    aps = []
    lines = [l for l in text.splitlines() if l.strip()]
    for line in lines:
        m = re.search(r"([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})\s+(-?\d+)\s+(\d+)", line)
        if not m:
            continue
        bssid, rssi, chan = m.group(1), int(m.group(2)), int(m.group(3))
        ssid = line[:m.start()].strip()
        aps.append(WifiAP(ssid=ssid, bssid=bssid.upper(), rssi_dbm=float(rssi), channel=chan))
    return aps


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- live scan
def _run(cmd, timeout=20) -> Optional[str]:
    exe = cmd[0]
    if shutil.which(exe) is None:
        log.warning("wifi scan: '%s' not found on PATH", exe)
        return None
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception as e:  # pragma: no cover - platform tool failures
        log.warning("wifi scan: '%s' failed: %s", exe, e)
        return None


def scan(iface: Optional[str] = None) -> List[WifiAP]:
    """Run the platform's scan command and return parsed APs (passive, read-only).
    Returns [] and logs when no scanner is available."""
    sysname = platform.system()
    if sysname == "Linux":
        out = _run(["nmcli", "-t", "-f", "SSID,BSSID,CHAN,FREQ,SIGNAL,SECURITY", "dev", "wifi", "list"])
        if out:
            return parse_nmcli(out)
        out = _run(["iw", "dev", iface or "wlan0", "scan"])
        if out:
            return parse_iw(out)
    elif sysname == "Darwin":
        ap = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        out = _run([ap, "-s"]) if shutil.which(ap) or _exists(ap) else None
        if out:
            return parse_airport(out)
        log.warning("wifi scan: macOS 14+ removed 'airport'; use a WiFi Explorer-class app or Termux on a phone")
    elif sysname == "Windows":
        out = _run(["netsh", "wlan", "show", "networks", "mode=bssid"])
        if out:
            return parse_netsh(out)
    else:  # Android/Termux
        out = _run(["termux-wifi-scaninfo"])
        if out:
            return parse_termux(out)
    return []


def _exists(p):
    import os
    return os.path.exists(p)


# --------------------------------------------------------------------------- GPS
def get_gps() -> Optional[tuple]:
    """Best-effort current (lat, lon). Tries gpsd (localhost:2947) then Termux
    ``termux-location``; returns None if neither is available."""
    try:
        import socket
        s = socket.create_connection(("127.0.0.1", 2947), timeout=2)
        s.sendall(b'?WATCH={"enable":true,"json":true};\n')
        s.settimeout(3)
        buf = b""
        for _ in range(20):
            buf += s.recv(4096)
            for ln in buf.split(b"\n"):
                try:
                    j = json.loads(ln)
                except Exception:
                    continue
                if j.get("class") == "TPV" and j.get("lat") is not None:
                    s.close()
                    return float(j["lat"]), float(j["lon"])
        s.close()
    except Exception:
        pass
    out = _run(["termux-location", "-p", "gps"], timeout=30)
    if out:
        try:
            j = json.loads(out)
            return float(j["latitude"]), float(j["longitude"])
        except Exception:
            pass
    return None


# --------------------------------------------------------------------------- logging & trend
class WifiLogger:
    """Append parsed APs to a CSV with GPS + timestamp."""

    def __init__(self, path):
        import os
        self.path = str(path)
        self._new = not os.path.exists(self.path) or os.path.getsize(self.path) == 0
        self._fh = open(self.path, "a", newline="")
        self._w = csv.writer(self._fh)
        if self._new:
            self._w.writerow(CSV_FIELDS)

    def log(self, aps: List[WifiAP], lat=None, lon=None, ts=None):
        ts = ts or datetime.now(UTC).isoformat(timespec="seconds")
        for a in aps:
            self._w.writerow([ts, "" if lat is None else f"{lat:.6f}", "" if lon is None else f"{lon:.6f}",
                              a.ssid, a.bssid, "" if a.rssi_dbm is None else a.rssi_dbm,
                              a.channel or "", a.freq_mhz or "", a.band or "", a.security,
                              "|".join(a.tags)])
        self._fh.flush()

    def close(self):
        self._fh.close()


def rssi_trend(rssi_series, min_slope_db=0.5) -> dict:
    """Classify a time-ordered RSSI series for one BSSID as warmer/colder/steady.

    Fits a line to the last samples; a rising RSSI ("warmer", you are getting
    closer) vs falling ("colder"). Returns slope in dB/sample and an arrow.
    """
    import numpy as np
    y = np.asarray([v for v in rssi_series if v is not None], float)
    if len(y) < 2:
        return {"trend": "unknown", "slope_db": 0.0, "arrow": "?", "last": None}
    x = np.arange(len(y))
    slope = float(np.polyfit(x, y, 1)[0])
    if slope > min_slope_db:
        t, arrow = "warmer", "^^"
    elif slope < -min_slope_db:
        t, arrow = "colder", "vv"
    else:
        t, arrow = "steady", "=="
    return {"trend": t, "slope_db": round(slope, 2), "arrow": arrow,
            "last": float(y[-1]), "delta_db": round(float(y[-1] - y[0]), 1)}


def read_log(path, bssid=None, ssid_regex=None) -> List[dict]:
    """Read a survey CSV back into rows (optionally filtered by BSSID or SSID)."""
    rx = re.compile(ssid_regex, re.I) if ssid_regex else None
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            if bssid and r["bssid"].upper() != bssid.upper():
                continue
            if rx and not rx.search(r["ssid"]):
                continue
            rows.append(r)
    return rows


def locate_from_log(path, bssid=None, ssid_regex=None, n=2.7, fit_n=False):
    """RSSI-multilaterate a transmitter from a survey CSV (needs lat/lon/rssi in
    >= 3 rows for the chosen AP). Returns a :class:`hordewatch.rf.foxhunt.Fix`."""
    from . import foxhunt
    samples = []
    for r in read_log(path, bssid=bssid, ssid_regex=ssid_regex):
        if r.get("lat") and r.get("lon") and r.get("rssi_dbm"):
            try:
                samples.append((float(r["lat"]), float(r["lon"]), float(r["rssi_dbm"])))
            except ValueError:
                continue
    if len(samples) < 3:
        raise ValueError(f"only {len(samples)} usable samples; need >= 3 (walk to more spots)")
    return foxhunt.rssi_multilaterate(samples, n=n, fit_n=fit_n)


# --------------------------------------------------------------------------- CLI
def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Passive WiFi survey for the Hordejakten uplink search.")
    ap.add_argument("--csv", default="wifi_survey.csv", help="output CSV")
    ap.add_argument("--interval", type=float, default=5.0, help="seconds between scans")
    ap.add_argument("--count", type=int, default=0, help="number of scans (0 = until Ctrl-C)")
    ap.add_argument("--lat", type=float, help="manual latitude if no GPS")
    ap.add_argument("--lon", type=float, help="manual longitude if no GPS")
    ap.add_argument("--track", help="BSSID to print a warmer/colder trend for")
    ap.add_argument("--locate", metavar="SSID_REGEX",
                    help="after scanning, RSSI-multilaterate this SSID from --csv and print a map link")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    logger = WifiLogger(a.csv)
    hist = []
    i = 0
    try:
        while a.count == 0 or i < a.count:
            gps = None if (a.lat is None or a.lon is None) else (a.lat, a.lon)
            if gps is None:
                gps = get_gps()
            lat, lon = gps if gps else (None, None)
            aps = scan()
            logger.log(aps, lat, lon)
            flagged = [x for x in aps if x.interesting]
            print(f"[{i}] {len(aps)} APs, {len(flagged)} flagged"
                  + (f" @ {lat:.5f},{lon:.5f}" if lat is not None else " (no GPS)"))
            for x in sorted(flagged, key=lambda z: (z.rssi_dbm or -999), reverse=True):
                print(f"    {x.rssi_dbm!s:>6} dBm  ch{x.channel or '?':<4} {x.bssid}  {x.ssid!r}  {x.tags}")
            if a.track:
                for x in aps:
                    if x.bssid.upper() == a.track.upper():
                        hist.append(x.rssi_dbm)
                tr = rssi_trend(hist)
                print(f"    track {a.track}: {tr['arrow']} {tr['trend']} ({tr['slope_db']} dB/scan, last {tr['last']})")
            i += 1
            if a.count == 0 or i < a.count:
                time.sleep(a.interval)
    except KeyboardInterrupt:
        pass
    finally:
        logger.close()

    if a.locate:
        try:
            fix = locate_from_log(a.csv, ssid_regex=a.locate)
            print("\nLocation estimate:")
            print(fix.summary())
        except Exception as e:
            print(f"\nlocate failed: {e}")


if __name__ == "__main__":
    main()
