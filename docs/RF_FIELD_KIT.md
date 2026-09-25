# RF & field-search kit — finding the Hordejakten 2026 box by its radio

The forest box streams 24/7. That stream has to leave the forest over a radio
link, and radio links leak. This kit is the **passive, receive-only** half of the
search: while the localisation engine (`hordejakt`) narrows the map down to a
handful of hotspots, you drive and walk those hotspots with a scanner, listen for
the uplink, and let the direction-finding tools walk you in. Nothing here
transmits.

- `hordewatch/rf/wifi_scan.py` — passive WiFi survey (Starlink/4G-router/camera APs), CSV+GPS logging, warmer/colder trend, RSSI location estimate.
- `hordewatch/rf/sdr_survey.py` — sweep the mobile **uplink** bands with an SDR and detect a steady streaming carrier.
- `hordewatch/rf/foxhunt.py` — turn bearings or RSSI samples into a location fix + map links.
- `hordewatch/rf/coverage.py` — a low-weight "cellular uplink" evidence layer + the Starlink-vs-cellular discriminator.

---

## 0. Legal & safety — read first

**Norwegian law (ekomloven / lov om elektronisk kommunikasjon).** *Receiving*
radio signals is generally allowed. What is **not** allowed is to **use or pass on
the content** of communications that are not meant for you, and you must **never
interfere** with, jam, or disrupt a transmission. This kit only records the
metadata that transmitters already broadcast openly to everyone — a WiFi
beacon's SSID/BSSID/channel, and raw received power vs. frequency. It does **not**:

- connect to, authenticate to, or probe any network;
- capture, decode, or store the *content* of any traffic;
- transmit anything (no jamming, no deauth, no active probing).

Do not connect to a network you find, even an open one. Do not attempt to decode
the video/telemetry. If you locate the stream link, that is a *map hint*, not an
invitation to touch the equipment.

**Physical safety.** It is hunting season (elg/rådyr). Wear **high-visibility
clothing**, make noise, and stay off active hunting ground. Much of the likely
area is **private land** — respect *allemannsretten*'s limits (no motor traffic
off-road, no camping right by cabins, close gates). Follow the organisers'
published rules for the hunt; if they forbid a search method, that overrides
anything here.

---

## 1. What link are they using, and what does it look like on the air?

Two realistic uplinks out of a forest:

### Starlink (most likely for a true dead-zone site)
- A dish + a router. The **router broadcasts WiFi** — default SSID `STARLINK`
  (older) or `STARLINK-XXXX` / `Starlink-…` (Gen-3), unless the crew renamed it.
  BSSID OUI is often SpaceX-registered (e.g. `F8:0C:F3`).
- The **dish uplink is Ku-band ~14.0–14.5 GHz**, a *steered phased-array beam*
  aimed at whichever satellite is scheduled — not at you. Sidelobes on the
  ground are weak and the beam hops constantly.
- **You cannot practically detect the Ku uplink** with hobby gear (see §2, Ku
  note). You detect Starlink by its **router WiFi** and by its **stream-health
  fingerprint** (§4).

### 4G/5G router (Teltonika RUTx, Peplink/Pepwave, Huawei, MiFi)
- Continuous ~3–8 Mbit/s uplink ⇒ a **strong, steady, high duty-cycle uplink
  carrier** in a Norwegian operator uplink band. This is directly detectable
  with an SDR (§2–3) if you get within ~0.5–2 km.
- The router also broadcasts WiFi (`RUT…`, `Pepwave_…`, `HUAWEI-…`).
- Norwegian uplink (device→tower) bands to sweep:

  | Band | Uplink (MHz) | Tech | RTL-SDR v4 can tune? |
  |------|--------------|------|----------------------|
  | B28  | 703–733      | LTE/NR | yes |
  | B20  | 832–862      | LTE    | yes |
  | B8   | 880–915      | LTE/GSM| yes |
  | B3   | 1710–1785    | LTE    | **no** (>1.766 GHz) |
  | B1   | 1920–1980    | LTE/NR | **no** |
  | B7   | 2500–2570    | LTE    | **no** |
  | n78  | 3400–3800    | NR TDD | **no** (and TDD ⇒ bursty by design) |

### Out of scope: people and their devices
This kit only looks for the *stream equipment* (Starlink router, field cellular
router, camera access point). It does not tag, follow or locate anyone's phone,
hotspot, Bluetooth device or vehicle — not the crew's, not other searchers'.
If a signal turns out to be a person's device, ignore it.

---

## 2. Shopping list

### Budget (≈ 0 kr, phone only)
- A phone WiFi analyser app (Android: *WiFiAnalyzer* [open source], or **Termux**
  + `termux-api` for `termux-wifi-scaninfo` + `termux-location`, which feed
  `wifi_scan.py` directly). iOS sandboxes WiFi scanning — use *AirPort Utility*'s
  scanner or an Android phone.
- Good for: finding the `STARLINK`/router/camera **WiFi** at 50–200 m, and RSSI
  multilateration by walking (§3). This alone can crack a site.

### Mid (≈ 300–500 kr, RTL-SDR)
- **RTL-SDR Blog v4** + a wideband whip/telescopic antenna. Software: `rtl_power`
  (ships with rtl-sdr tools) or `SoapyPower`.
- **Important limit:** the v4 tunes only up to **~1.766 GHz**, so it covers the
  **B28/B20/B8 uplinks (700–915 MHz) only** — not B3/B1/B7/n78. In rural Norway
  the streaming router is *most likely* on 700/800/900 MHz anyway (best range),
  so this is usually enough to catch a cellular uplink.

### Better (≈ 3 000–5 000 kr, HackRF/bladeRF + directional antenna)
- **HackRF One** (1 MHz–6 GHz) or **bladeRF** + a **log-periodic (LPDA) or Yagi**
  covering ~700–2700 MHz. Software: `hackrf_sweep` (fast full-band power sweep)
  or `SoapyPower`.
- Covers *all* the LTE/NR uplink bands, and the directional antenna gives you
  **bearings** for `foxhunt.bearing_intersection` (much faster than RSSI
  walking). This is the serious kit.

### Ku-band (Starlink dish) — why an LNB+finder is **not** reliable
You might think: point a satellite LNB + "sat finder" at the dish to detect the
14 GHz uplink. Don't rely on it:
- The uplink is a **narrow steered beam aimed at the satellite**, ~30–60° up —
  *not* radiating sideways at you; ground sidelobes are weak.
- The beam **hops** to a new satellite on a 15 s schedule, so there is no steady
  tone to peak on.
- A cheap sat finder measures **broadband power on the Ku *downlink* (10.7–12.75
  GHz)**, not the 14 GHz uplink, and has no frequency selectivity — it will peak
  on the sun, on any VSAT/TV LNB, on warm ground.
- Consumer LNBs are tuned to the downlink band; you'd need a proper 14 GHz feed +
  a real spectrum analyser to see the uplink, and even then only in the beam.

**So:** detect Starlink by its **router WiFi** (`wifi_scan.py`) and by the
**stream-health timing fingerprint** (§4), not by trying to hear 14 GHz.

Accessories worth having: a GPS puck for `gpsd` (so every sample is
geotagged), a power bank, offline `norgeskart` map tiles, and a compass (correct
for **magnetic declination ~ +2–3° in SE Norway, 2026** before feeding bearings
to the foxhunt tool — enter *true* bearings).

---

## 3. Field procedure — from the car, then on foot

1. **Plan from the map.** Run `hordejakt` to get `output/hotspots.csv`. Search the
   hotspots **in probability order** (see §5). Note the roads that pass near each.
2. **Drive-survey (coarse).** Start a logger and drive the forest roads near a
   candidate at 30–50 km/h with the antenna on the roof/dash:
   - WiFi: `python -m hordewatch.rf.wifi_scan --csv survey.csv --interval 3`
     (uses `gpsd`/Termux for GPS; pass `--lat/--lon` to place fixes manually).
   - SDR: sweep an uplink band to CSV, then
     `python -m hordewatch.rf.sdr_survey --analyze sweep.csv`.
   You are looking for **any** flagged WiFi (`STARLINK*`, `RUT*`, `Pepwave*`,
   `HUAWEI-*`, GoPro/DJI, `Horde…`) or a **persistent uplink carrier**.
3. **Bracket the peak.** When something appears, note where RSSI/carrier power is
   strongest along the road. `wifi_scan --track <BSSID>` prints a warmer/colder
   arrow live.
4. **Walk the gradient (fine).** Park, go on foot toward rising signal. Sample at
   several spots **all around** the suspected point (good angular spread), logging
   each with GPS. 5–10 m of tree trunk kills 2.4 GHz fast, so signal changes
   quickly on foot — that is your friend.
5. **Solve.**
   - RSSI: `foxhunt.rssi_multilaterate([(lat,lon,rssi)…])` or
     `wifi_scan.locate_from_log(csv, ssid_regex="STARLINK")`.
   - Directional antenna: take a bearing from ≥2 well-separated spots and use
     `foxhunt.bearing_intersection([(lat,lon,bearing)…])`. Spread the fixes in
     angle — bearings all taken from one road are near-parallel and the fix is
     smeared along the line (the tool flags `near_parallel`).
   Both print `norgeskart` + Google Maps links and a 1-σ uncertainty (which is
   *optimistic* in forest multipath — treat it as "search this radius").

### What to expect at what range (order of magnitude, forest terrain)
- **WiFi 2.4 GHz** router beacon: audible ~50–200 m through trees (much less than
  the ~1 km line-of-sight in the open); 5 GHz maybe half that. A hit ⇒ you're
  close.
- **LTE uplink** (phone/router at up to +23 dBm): detectable ~**0.5–2 km**
  depending on terrain, canopy and whether you have line-of-sight to the site.
  700/800 MHz reaches furthest. Expect the carrier to *fade in and out* with
  terrain as you drive — the **steadiness over time at one spot** is the
  discriminator, not the absolute level.

---

## 4. Which uplink is it? (stream-health discriminator)

Independently of any RF gear, the **timing of stream stalls** distinguishes the
two links, and `hordewatch/analyzers/stream_health.py` already emits an
`uplink_signature` verdict from it. In short (`coverage.discriminator_note()`):

- **Starlink →** short (≤15 s) micro-stalls whose on-site start times cluster on
  the **global 15 s satellite-reallocation clock** (`unix_time mod 15 ≈ 12 s`),
  plus extra whole-slot outages when a branch blocks the scheduled satellite, and
  outages that **correlate with rain**. A Rayleigh test at period 15 s + an
  inter-interval "multiple of 15 s" test + a Lomb–Scargle line at 1/15 Hz all
  firing ⇒ `starlink_like`.
- **Cellular →** longer, aperiodic congestion/handover stalls and bitrate dips
  concentrated in the **evening busy hour** (Europe/Oslo); no 15 s periodicity ⇒
  `cellular_like`.

Use the verdict to **gate the search**: if `starlink_like`, don't waste time
sweeping LTE uplinks (hunt the router WiFi + expect a poor-coverage site); if
`cellular_like`, the SDR sweep and the coverage layer become worthwhile.

---

## 5. Combining RF with the probability map

- **Search order.** Take `output/hotspots.csv` from `hordejakt` (ranked by
  posterior mass). Budget your hours by probability: spend the first hours on the
  top hotspots, and re-rank whenever a new stream observation shifts the
  posterior. A simple rule: *expected time-to-find is minimised by visiting
  candidates in descending probability-per-unit-drive-time*, so prefer a slightly
  lower-probability hotspot that sits right on a road you're already driving over
  a marginally higher one 40 minutes away.
- **The coverage layer.** `coverage.build_layer(masts=…)` writes
  `data/hordewatch/layers/coverage_4g.npz`, which `hordejakt.layers.live` picks up
  automatically. It encodes *"if the uplink is cellular, the box is inside
  4G/5G coverage"* at a deliberately **low reliability (0.3)** — Starlink is
  equally plausible and would *prefer* a dead zone, so this layer may only nudge
  the map, never dominate it. Raise or drop it with `coverage.apply_verdict()`
  once `uplink_signature` has spoken. Real coverage input comes from Nkom's
  *Finnsenderen* transmitter register / *dekningskart*, or operator coverage maps
  (endpoints documented in `coverage.COVERAGE_ENDPOINTS`); all live fetches fail
  soft, so on a machine without network you pass the mast list explicitly.
- **RF fixes as evidence.** A confident foxhunt fix is a point with an
  uncertainty radius; overlay it on `output/map.html`. If it lands on or near a
  top hotspot, that hotspot jumps to the front of the queue. (RF fixes are *not*
  auto-fused into the posterior — they're strong enough on their own to redirect
  the physical search.)

---

## 6. Quick reference

```bash
# Passive WiFi survey, log to CSV, then locate a Starlink AP from the log
python -m hordewatch.rf.wifi_scan --csv survey.csv --interval 3 --track F8:0C:F3:11:22:33
python -m hordewatch.rf.wifi_scan --csv survey.csv --count 1 --locate 'STARLINK|RUT|Pepwave'

# Sweep an uplink band with whatever SDR tool is installed, detect a steady carrier
python -m hordewatch.rf.sdr_survey --band B20 --out sweep.csv
python -m hordewatch.rf.sdr_survey --analyze sweep.csv

# Foxhunt from a CSV of lat,lon,bearing and/or lat,lon,rssi
python -m hordewatch.rf.foxhunt fixes.csv           # bearings if present, else RSSI

# Print the Starlink-vs-cellular discriminator and (try to) build the coverage layer
python -m hordewatch.rf.coverage
```

All modules degrade gracefully when a tool (nmcli/iw/netsh/airport/termux,
hackrf_sweep/rtl_power/soapy_power, gpsd) or `requests` is missing: they log a
clear message and return empty rather than crash, and none of them need the
network to run their offline analysis.
