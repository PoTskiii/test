# default.no mirror: full catalogue and interpretation

*Compiled 2026-09-25 (evening, CEST). Everything here comes from local mirrors. default.no itself is blocked from this machine, so this document describes default.no **as fetched by MagnusPladsen on 24.09 at 18:36 CEST** (map layers) and **23.09** (audio, bird and plane pages). Newer default.no runs, if there are any, are not covered.*

Evidence classes used throughout. They follow the task's rigour rules and are never upgraded:

- **(a) primary**: Anja's whiteboard, what is visible or audible on the stream, organizer statements, and app answers. In this source such evidence only appears **as quoted by default.no or by magnus**, so it is second-hand.
- **(b) community observation**: for example ADS-B tracks, field checks, and radar or station readings.
- **(c) interpretation**.
- **(d) model output**: default.no's fusion grids, site finder, plan, and similarity scores.

Almost everything in this mirror is (d) or (c).

Paths are relative to `/home/user/test/`. Time bases: *stream time* is the clock shown on the livestream, and *real time* is wall clock. Both are CEST (UTC+2) unless marked Z.

---

## 0. Key results

1. **default.no's fusion model ranks the Glomma valley between Rena and Evenstad first** (Stor-Elvdal/Åmot). The top cell is **61.45 N, 11.10 E**, with posterior share **0.127** (`data/raw/magnus/public/data/defaultno/omrader.json` rank 1, updated 2026-09-24T18:06:17). In `fusjon/alle.json` (18:31:43) the same cell has 11 % of the probability within 10 km and 28.9 % within 25 km. The next areas are 60.70/11.60 (p 0.056), 60.95/11.30 (p 0.054), 58.55/6.10 (p 0.044, Rogaland), 61.20/10.90 (p 0.035), and 61.75/11.10 (p 0.020). The ten fusion areas together hold only 0.382 of the mass, and the other 24 "areas" are hypotheses (p = 0). [d]
2. **default.no's site finder had one best point: 61.44874, 10.97747** on Birkebeinerveien. It is 605 moh, 556 m from the road, +75.3 m uphill, with pine, 215 m to the nearest clear-cut, and score 0.995. Its abs = 0.12638 is the highest of all 126 sites. **MagnusPladsen deleted this site from the mirror on 25.09 14:12, together with 8 other Birkebeinerveien sites, 4 plan stops and 3 field notes. The commit is `e431102` "Remove everything about Birkebeinervegen", and it gives no reason.** I recovered the originals from git into `evidence/sources/defaultno_recovered/`. mkekeoooo identifies this same point as "A1" (`data/raw/mkekeoooo/README.md:17`). default.no's own `rejected.json` has the note «61.4495, 10.9763 (bom)»: «Bom på veien 23.09, bare sett fra veien. Ikke ferdig sjekket.» So the site was **not fully checked** as of 24.09 18:36. [d + b]
3. **default.no's 40-stop field plan** (generated 24.09 17:04) puts stop 1 at **Madsskardveien øst for Glomma, 61.452, 11.146**. You park at 61.45283, 11.14854 on a service road and walk 163 m at 236° (+20.1 m). The plan's note says «boksen staar i moden skog 15-22 m med lysning» and that every stop passes the three plane sightings within 5°. [d/c]
4. **What default.no treats as evidence.** It uses three plane reactions: 21.09 at 21:29 (stream), and 22.09 at 20:32 and 20:34 (SAS39A, then NOZ55J, southbound into Gardermoen). It also uses «INGEN FLY» by day, dry camera glass while 796 of 831 stations got rain, sun and sun-path fits, station-weather similarity, satellite clouds, pine/forest (NIBIO SR16), weak lingonberry/heath, drive time 3–8.5 h from Oslo, and military ranges («INGEN SKYTING»). These premises are shared with other community models, so they are **not independent confirmations**. [c]
5. **Data-quality problems found in this audit** (details in section 20):
   - The sites/logging PNG overlays for area ranks 1–14, 61 and 62 are **registered to the wrong bounds**. For example, `logging_01.png` and `sites_01.png` belong to a box centred on 61.45/11.00, not 61.45/11.10.
   - `fusjon/alle.json` ("Alt bevis") contains **no sun, sun-path or aircraft-sound term**. The "Uten lyd og sol" variant does contain sun terms.
   - The station-weather "similarity" ranks coastal Northern Norway highest.
   - The 21:29 pointing may have been toward a **shooting star** (default.no osint_notes as cited in `data/raw/mk_bevis/bevis/claude-2026-09-25/README.md:62`).
   - Stream audio is a **replayed loop** (default.no dupedaudio).
6. **The unnamed aircraft «@@@@@@@@» (B738, heading 182°) in `flyhendelser.json` is NOZ9EG (LN-NIQ, hex 4791ac).** I verified this myself against the adsb.lol trace in `data/raw/mk_bevis/bevis/claude-2026-09-25/adsb/trace_4791ac.json`. default.no's "pek" point 61.2916, 10.902, 24 775 ft matches the trace at 19:29:29Z (61.287, 10.9016, baro 24 700 ft, track 182.3°). [b, my verification]

---

## 1. Provenance and fetch chain

| item | value | provenance |
|---|---|---|
| Upstream | default.no/map.php (open-data search log by "BobTheShoplifter" on Discord) | `data/raw/magnus/src/lib/defaultno.ts:1`, `data/raw/magnus/src/components/AnalysePanel.tsx:100` |
| Map layers fetched | «hentet 24.09 kl. 18:36» | `data/raw/magnus/src/data/defaultno_mer.json:2`, `defaultno.ts:1` |
| Audio, bird and plane pages fetched | «Hentet 23.09» (dupedaudio.php, clips.php, plane.php) | `data/raw/magnus/src/data/analyse.json` → `kreditering.defaultno` |
| Commits adding the data | 7d0554e (24.09 18:44), 1125b60 (18:52), 71778ff (19:02), 1ce4c01 (19:04) | `git log` in `data/raw/magnus` |
| **Mirror edit** | **e431102 (25.09 14:12) "Remove everything about Birkebeinervegen".** Rewrote `pins.json` (13→10), `plan.json` (40→36 stops, n 40→36) and `steder.json` (126→117 sites). No other file under `public/data/defaultno` has changed since 71778ff. | `git show e431102`, `git diff --stat 71778ff HEAD` |
| Recovered originals | `evidence/sources/defaultno_recovered/{pins,plan,steder}.json` = `git show e431102^:public/data/defaultno/<f>.json`. sha256: pins ea2dab1c…, plan fa8117b2…, steder 17e06d6e… | this audit |
| Decoder | `evidence/sources/defaultno_decode.py` (self-test passes) | this audit |

Internal timestamps:
- steder/omrader 2026-09-24T18:06:17
- plan 24.09 17:04
- flylyd 18:31:31
- fusjon: alle 18:31:43, fly 18:31:52, flyskog 18:31:54, utenlyd 18:37:58, stille 18:38:04, stilleskog 18:38:06, utenmerker 18:38:09; **utenfly 24.09 13:21:48 (older)**; **utenflylyd 22.09 14:29:42 (much older)**
- regn 18:25:24
- met 18:07:43
- vegkamera 18:30:58
- radar 20260924T163500Z (= 18:35 CEST)
- vaer dato 2026-09-24

---

## 2. File inventory (all files under `data/raw/magnus/public/data/defaultno/` and the two src/data files)

| file | size B | loaded by | schema | what default.no/magnus says it means | class |
|---|---|---|---|---|---|
| omrader.json | 4997 | `defaultno.ts:130-136` (hogst frames) | `{note, updated, omrader[34]: {rank, lat, lon, posterior, bounds}}` | note: «score = road band x uphill x pine/forest x relief along the view x sun horizons; abs_score = score x fusion mass within 10 km of the area» | d |
| steder.json | 29326 (orig 31138) | `defaultno.ts:138-171` | `{retning:219.0, oppdatert, omrader[34]: {rank, lat, lon, p, b, sterk, mulig, furu, hogd22, hogd24, ekstra, merke}, steder[117] (orig 126): {lat, lon, score, abs, moh, vei_m, vei, veinavn, opp, relieff, furu, hogst_m, tog_m, omr}}` | «Grønne prikker er steder 5–10 min opp fra vei, med furu og terreng som ligner bildet» (`lag.ts:329-340`); areas «ca. 24 × 24 km, tykkere kant betyr mer sannsynlig» (`lag.ts:343-349`) | d |
| steder/sites_NN.png ×34 | 5–39 kB | `defaultno.ts:142-144` at steder.omrader[].b, opacity 0.6 | 600², 500², 400², 350², 300² or 250² px RGBA, ≈40 m/px (0.00036° lat) | red = «Sterkt treff», yellow = «Mulig treff», blue = «Riktig avstand fra vei» (`lag.ts:334-338`) | d |
| hogst/logging_NN.png ×34 | 0.7–51 kB | `defaultno.ts:130-136` at omrader.json bounds, opacity 0.8 | same sizes | yellow «Hogd 2016 eller senere», orange «2022 eller senere», red «2024–25», black line «Jernbane». Global Forest Watch (`lag.ts:315-326`) | b (GFW) |
| plan.json | 19089 (orig 21054) | `Kart.tsx:551-560` | `{generated, n, stops[36] (orig 40), route, routes[4], note}` | «Letelista til default.no: 40 steder rangert etter hvor godt de passer (skog, furu, stigning, fly, lite hus)» (`lag.ts:270-276`) | d/c |
| rejected.json | 3429 | `Kart.tsx:561-567` | `{areas[15]: {name, lat, lon, why, img}, note}` | note: «Steder folk har foreslått, sjekket mot de tre flyene hun så, INGEN FLY-regnskapet, regn og skytefelt. Grå = avvist, gul = svakere/ikke utelukket.» | c |
| pins.json | 1169 (orig 1567) | `Kart.tsx:568-574` | `[{lat, lon, note}]` ×10 (orig 13) | «Notater fra folk som har vært ute og lett: bommer, private veier og steder som er sjekket til fots» (`lag.ts:288-294`) | b |
| gasoner.json + gasoner/overlay_01..06.png | 1109; 240² px | `defaultno.ts:325-342` | `{band:[200,700], omrader[6]: {rank, lat, lon, b, vei_km, skog, km2, opp, tort}}` | «Skog en kort gåtur fra vei i seks områder. Rødt er målt fra ordentlig vei, blått fra alle veier inkludert traktorvei» (`lag.ts:352-361`) | d |
| fusjon/*.json ×9 | 8–17 kB | `defaultno.ts:84-105, 173-181` | grid + `{omrader[12]: {lat, lon, m10, m25, skog, deler{…}}, bevis[], oppdatert}` | «Alle bevisene til default.no vektet sammen, i ruter på ca. 5 × 5 km. Rødt er de beste 2 %, oransje topp 15 % og gult topp 40 %» (`lag.ts:540-551`) | d |
| sjelden.json | 11115 | `defaultno.ts:183-200` | grid + `{grad:40, antall:1255, topp[40]: {lat, lon, r, dag, e2130, e2028}}` | «Blått er der få fly gikk høyt over om dagen, men flyet 21:30 var høyt nok. Det passer med at Anja skrev «INGEN FLY» kl. 18:31» (`lag.ts:442-452`) | d |
| flylyd.json | 7183 | `defaultno.ts:202-205` | grid (0.1°×0.2°) + `{best{…}, hendelser:22, oppdatert}` | «Rødt er der flylydene på streamen passer best med flyene i lufta. Lyden kan være spilt av på nytt, så dette er usikkert» (`lag.ts:455-465`) | d |
| flyhendelser.json | 64754 | `defaultno.ts:301-316` | `{hendelser[3], fly[253]: {k, t, rute, sel, min, maks, fart, kurs, h, spor[[lat,lon]…], pek[lat,lon,ft]\|null, lyd[lat,lon,ft]\|null}}` | «Alle fly i lufta 21.09 21:30 og 22.09 20:33 og 20:35 … Rosa prikk er der flyet var da hun reagerte, så kassen bør ligge under et av sporene.» ADS-B from adsb.lol (`lag.ts:428-440`). Pop-ups: pek = «Her var flyet da hun reagerte», lyd = «Her var flyet ca. 35 sek før lyden var sterkest» (`defaultno.ts:313-314`) | b (tracks) + c (which plane) |
| regn.json | 23933 | `defaultno.ts:344-347` | grid + `{siden, stasjoner:831, vate:796, radar:76, oppdatert}` | «Blått har fått regn siden 21.09, mørkere betyr mer. Glasset foran kameraet har vært tørt, så blå områder passer dårlig.» Legend: «Over 6 mm», «0,3–6 mm» (`lag.ts:468-479`) | b (obs) → d (grid) |
| radar.json + radar.png | 55; 44405 (720² px) | `defaultno.ts:349-352` | `{b:[[58,7],[63,13]], tid:"20260924T163500Z"}` | «Grønt er lett regn, gult og rødt kraftig regn. Et øyeblikksbilde fra MET, ikke oppdatert.» (`lag.ts:480-491`) | b |
| met.json | 2506 | `defaultno.ts:266-278` | `{tid, punkter[81]: [lat, lon, temp °C, cloud %, precip mm, RH %]}` | «Vær i 81 punkter 24.09 kl. 18» (`lag.ts:493-504`) | b |
| vaer.json | 45327 | `defaultno.ts:280-299` | `{dato:"2026-09-24", stasjoner[400]: {navn, lat, lon, moh, score, dugg, regn, stigning}}` | «Rødt er værstasjoner der dugg, morgenregn og oppvarming ligner mest på det kameraet viser.» Frost/MET (`lag.ts:506-516`) | d |
| vegkamera.json | 61855 | `defaultno.ts:245-264` | `{bilde (URL prefix), tid, stasjoner[533]: {navn, lat, lon, vei, regn mm/h, temp, rf, kam[]}}` | «Blått hadde nedbør 24.09 kl. 18:30, gult var tørt og grått måler ikke» (`lag.ts:518-529`) | b |
| skytefelt.json | 15233 | `defaultno.ts:115-128` | `{note, felt[6]: {navn, type, status, ringer[[[lat,lon]…]]}}` | «Anja skrev «INGEN SKYTING». default.no regner med at kassen ikke står her.» (`defaultno.ts:123`) | b (Forsvarsbygg) + c |
| leder.json | 207573 | `defaultno.ts:236-243` | `{pilegrim[504 polylines], osterdal[256 polylines]}` | «Anja skrev «INGEN STIER», så kassen står neppe rett ved en merket led.» | b (OSM) + c |
| baer.json | 18697 | `defaultno.ts:207-216` | grid, levels 1–5 | «Rødt er tørr furumo med tyttebær og lyng, blått er frodigere blåbærskog. Bygget på funn i Artsdatabanken og et svakt bevis.» (`lag.ts:376-387`) | d (weak) |
| baerfunn.json | 206751 | `defaultno.ts:218-231` | `{tytte[3919]: [lat, lon, year], blaa[4466]}` | «registrert 2015–2026. Viser mest hvor folk har registrert funn» | b (GBIF) |
| fugl.json | 53118 | `defaultno.ts:233-234, 365-380` | `{steg:0.02, orr[1897]: [lat, lon, n], stor[1516], n_orr:33818, n_stor:13185}` | «default.no mener en lyd på streamen 24.09 kan være orrfugl som spiller» (`lag.ts:401-408`) | b (GBIF) + c |
| coop.json | 8155 | `Kart.tsx:575-581` | `{shops[60]: {name, lat, lon, brand, hours, addr}, note}` | «Anja skrev at pizzadressingen var fra Coop… Coop finnes nesten overalt» (`lag.ts:297-304`) | b (OSM) |
| pizza.json | 8909 | `defaultno.ts:318-323` | `[{navn, lat, lon, type, kjokken, sted, tid}]` ×65 | «Sier mest om hvor mannskapet kan ha spist» | b (OSM) |
| eiffel_band.json + .png | 230; 1100×1200 px | `Kart.tsx:543-550` | `{bounds:[[60.6,10.7],[61.8,12.4]], note}` | note: «terreng 800–900 moh (oransje) og 780–920 (gult), Kartverket DTM 100 m. 2,7 Eiffeltårn = 810–891 m avhengig av om man regner 300, 324 eller 330 m per tårn» | d |
| eiffel_road.json + .png | 278; 1100×1200 px | `Kart.tsx:543-550` | `{bounds (same), note, version:2}` | note: «800–900 m fra nærmeste vei: rødt = alle kjørbare veier inkl. skogsbilvei/traktorvei (OSM), gult = bare offentlig vei. Uten fly-/skogfilter, det ser du selv på kartet (tykkere strek 16:50)» | d |
| (tile layer) dn_satellitt | n/a | `defaultno.ts:354-361` | NASA GIBS `HLS_S30_Nadir_BRDF_Adjusted_Reflectance/default/2026-09-21/…Level12` | «Satellittbilde fra den klareste dagen (21.09)» | b |
| src/data/defaultno_mer.json | 13999 | `AnalysePanel.tsx:297-459` | text data from map.php (observations, lost, sol, solbane, hls, vaer, radar, regn, met, vegkamera, fugl, sjelden, flylyd, gasoner) | «Tekstdata fra default.no/map.php som ikke passer på kartet» | mixed |
| src/data/analyse.json | 7663 | `AnalysePanel.tsx:73-259` | audio loop, YAMNet tags, plane clips, BirdNET; also **non-default.no** vercel data (kommuner, vercelFakta) | see section 18 | mixed |

---

## 3. Grid format and exact decode recipe

All run-length grids use the same encoding (`data/raw/magnus/src/lib/defaultno.ts:38-56`):

```
type Grid = { lat0, dlat, lon0, dlon, lop: number[] }
for n in 0..len(lop) step 4:  [i, j, len, k] = lop[n:n+4]
  lat_centre = lat0 + i*dlat
  rectangle  = [lat_centre - dlat/2, lon0 + (j-0.5)*dlon]  ..  [lat_centre + dlat/2, lon0 + (j+len-0.5)*dlon]
  -> cells (i, j), (i, j+1), …, (i, j+len-1) all have level k; cell centre lon = lon0 + j'*dlon
cells not covered by any run = level 0 (not drawn)
```

Python (tested in `evidence/sources/defaultno_decode.py`):

```python
import json, numpy as np
d = json.load(open(path)); r = np.asarray(d['lop']).reshape(-1, 4)
L = np.zeros((r[:,0].max()+1, (r[:,1]+r[:,2]).max()), np.int8)
for i, j, n, k in r: L[i, j:j+n] = k
lat = d['lat0'] + i*d['dlat'];  lon = d['lon0'] + j*d['dlon']      # cell centres
value_at = lambda la, lo: L[round((la-d['lat0'])/d['dlat']), round((lo-d['lon0'])/d['dlon'])]
```

| grid | lat0 | dlat | lon0 | dlon | runs | cells stored | i range | j range | extent of stored centres | level counts | level meaning |
|---|---|---|---|---|---|---|---|---|---|---|---|
| fusjon/alle | 57.8 | 0.05 | 4.3 | 0.1 | 797 | 1738 | 10–146 | 4–98 | 58.30–65.10 N, 4.7–14.1 E | 1:1096, 2:556, 3:86 | 3 = best 2 %, 2 = top 15 %, 1 = top 40 % (`defaultno.ts:58-59`, colours #ff1e14/#ff9614/#ffdc14). Counts fit a domain of ≈4 300 cells: 86/4300 = 2.0 %, 642/4300 = 14.9 %, 1738/4300 = 40.4 % |
| fusjon/utenlyd | 〃 | 〃 | 〃 | 〃 | 437 | 972 | 11–146 | 8–98 | 58.35–65.10, 5.1–14.1 | 1:614, 2:306, 3:52 | same |
| fusjon/utenmerker | 〃 | | | | 850 | 2692 | 5–135 | 8–85 | 58.05–64.55, 5.1–12.8 | 1:1696, 2:865, 3:131 | same |
| fusjon/utenflylyd | 〃 | | | | 1211 | 2788 | 4–146 | 5–98 | 58.00–65.10, 4.8–14.1 | 1:1700, 2:936, 3:152 | same |
| fusjon/utenfly | 〃 | | | | 1434 | 2910 | 5–149 | 4–98 | 58.05–65.25, 4.7–14.1 | 1:1806, 2:910, 3:194 | same |
| fusjon/fly | 〃 | | | | 976 | 12574 | 4–267 | 4–267 | 58.00–71.15, 4.7–31.0 | 2:12312, 3:262 (no level 1) | same, but ties in a flat likelihood merge the 15 % and 40 % quantiles |
| fusjon/flyskog | 〃 | | | | 775 | 2417 | 4–133 | 4–75 | 58.00–64.45, 4.7–11.8 | 1:1511, 2:784, 3:122 | same |
| fusjon/stille | 〃 | | | | 1283 | 5367 | 9–267 | 6–267 | 58.25–71.15, 4.9–31.0 | 1:1883, 2:3227, 3:257 | same (ties) |
| fusjon/stilleskog | 〃 | | | | 741 | 2051 | 5–137 | 5–89 | 58.05–64.65, 4.8–13.2 | 1:1312, 2:637, 3:102 | same |
| flylyd | 57.8 | **0.1** | 4.3 | **0.2** | 693 | 984 | 2–123 | 2–101 | 58.0–70.1, 4.7–24.5 | 1:598, 2:336, 3:50 | same RANG_STIL (best 2/15/40 %) |
| sjelden | 57.8 | 0.05 | 4.3 | 0.1 | 770 | 1682 | 1–243 | 1–235 | 57.85–69.95, 4.4–27.8 (includes Sweden, Finland, Estonia) | 1:977, 2:368, 3:337 | 3 «Passer godt» (#0ea5e9, 0.65), 2 (#50c8ff, 0.4), 1 «Passer litt» (#50c8ff, 0.2) (`defaultno.ts:187`) |
| regn | 57.8 | 0.05 | 4.3 | 0.1 | 2178 | 13352 | 1–270 | 2–270 | 57.85–71.30, 4.5–31.3 | 1:2324, 2:3089, 3:7939 | rain since 21.09 04:50Z: 1 light (0.22) … 3 dark (0.65). The legend only states «0,3–6 mm» and «Over 6 mm», so the exact 1/2/3 thresholds are **not stated**. Absent = dry or outside the domain. Inside the fusion domain, 2272 cells are dry |
| baer | 57.8 | 0.05 | 4.3 | 0.1 | 1630 | 17530 | 0–270 | 0–270 | 57.8–71.3, 4.3–31.3 | 1:93, 2:440, 3:7856, 4:8861, 5:280 | colour v = (k−0.5)/5 → rgb(255v, 60, 255(1−v)). **5 = mostly tyttebær/lyng (dry pine heath)**, 1 = mostly blåbær (`defaultno.ts:207-216`, `lag.ts:381-385`) |

Cell size is 0.05° × 0.1°, about 5.6 km × 5.3 km at 61° N («ca. 5 × 5 km»). The flylyd cells are 0.1° × 0.2°, about 11 × 10.7 km.

**fugl.json** is not a run-length grid. Each entry `[lat, lon, n]` is the **south-west corner** of a 0.02° × 0.02° cell. The rectangle is `[lat, lon]`–`[lat+0.02, lon+0.02]`, and fill opacity is min(0.75, 0.15 + 0.6·ln(1+n)/ln(1+max)) (`defaultno.ts:365-380`).

---

## 4. Image overlays: bounds, colour keys and registration check

| overlay | bounds source | px | colour key (RGBA) |
|---|---|---|---|
| steder/sites_NN.png | steder.json omrader[rank].b | 600² (ranks 1–14, 72–74), 500² (31, 32, 81–83, 101, 102, 111, 112), 400² (61, 62), 350² (21, 22, 71), 300² (41), 250² (91, 121) | (230,40,40,200) strong · (250,200,40,140) possible · (40,110,230,60) road-distance band |
| hogst/logging_NN.png | omrader.json omrader[rank].bounds (identical to steder b) | same sizes | (255,210,60,90) cut ≥2016 · (255,120,20,150) ≥2022 · (230,20,20,200) 2024–25 · (40,40,40,255) railway |
| gasoner/overlay_0N.png | gasoner.json b | 240² | (200,30,30,170) from «ordentlig vei» · (30,100,220,110) and (30,100,220,50) from all roads incl. tractor roads |
| radar.png | radar.json b [[58,7],[63,13]] | 720² | (150,220,120,150) very light · (60,170,60,180) «Lett» · (255,230,0,200) «Moderat» · (255,140,0,220) · (220,20,20,240) «Kraftig» |
| eiffel_band.png | [[60.6,10.7],[61.8,12.4]] | 1100 w × 1200 h | (255,140,0,170) 800–900 moh · (255,220,0,90) 780–920 moh |
| eiffel_road.png | same | 1100 × 1200 | (230,0,0,170) 800–900 m from any drivable road incl. forest/tractor road · (255,204,0,120) from public road only |

Pixel decode: `lon = W + (x+0.5)/width·(E−W)`, `lat = N − (y+0.5)/height·(N−S)` (lat-linear).

**radar.png is lat-linear.** I checked this with airport icons baked into the image. Notodden airport (59.567 N, 9.212 E) appears at y≈490. Lat-linear predicts 494 and Mercator predicts 510. Torp (59.187 N, 10.259 E) appears at y≈548. Lat-linear predicts 549 and Mercator predicts 568. Leaflet stretches overlays in Web-Mercator, so the magnus map shows radar.png up to ~15 px (≈0.1°) too far south in mid-image.

For the 0.2° site and hogst boxes the lat-linear/Mercator difference is under 1 px. For eiffel_band it is about 5–6 px (≈600 m). The two 783-moh sites (61.346, 10.988) fall in the 780–920 band under both mappings, so the band is roughly registered.

**Registration defect (my finding).** For the hypothesis areas 21, 22, 31, 32, 41, 71–74, 81–83, 91, 101, 102, 111, 112 and 121, every steder site falls on a red "strong" pixel of its own sites PNG. The PNG strong/possible areas also equal the JSON `sterk` values: for example 22 gives 3.20 vs 3.18 km², 81 gives 2.54 vs 2.53 and 82 gives 3.16 vs 3.14. For **ranks 1–14, 61 and 62 this fails**:

- rank 6 PNG shows 4.22 km² strong but the JSON has sterk 0.00;
- rank 8 PNG shows 0.00 but the JSON has 4.21;
- rank 1's 54 sites hit red at their own bounds only once.

Two independent tests locate some of these PNGs.

- **Site test:** I shifted each PNG and counted sites on red pixels. `sites_01` fits at centre **61.45/11.00** (47 of 54 sites) and `sites_02` fits at **61.10/11.00** (11 of 13).
- **Clear-cut test:** I cross-correlated the clear-cut masks against a mosaic built from correctly registered logging PNGs:

| PNG | JSON centre | best-fit true centre | Dice score | overlap coverage |
|---|---|---|---|---|
| logging_01 | 61.45/11.10 | 61.45/11.00 | 0.70 | 0.99 |
| logging_02 | 60.70/11.60 | 61.10/11.00 | 0.86 | 0.56 |
| logging_10 | 58.75/8.90 | 60.90/11.00 | 0.63 | 0.87 |
| logging_11 | 61.45/11.00 | 60.82/10.85 (the rank-13 centre) | 0.58 | 0.79 |

- **Rail test:** with `logging_01` shifted −0.1° in longitude, the distance from each site to the drawn railway matches steder `tog_m`. The median error is 11 m (46 sites), against 4 157 m unshifted. The correctly registered 32, 71, 74 and 83 give 3–12 m unshifted.

PNGs 3–9, 12–14, 61 and 62 could not be placed. **So the numbered overlays for the fusion areas come from an older area ranking. Do not use them at their JSON bounds.** The site coordinates in steder.json are unaffected.

---

## 5. The fusion model

### 5.1 Evidence terms and penalty semantics

Each fusion area carries `deler`, the "penalty per evidence (0 = fits)". The pop-up reads «Straff per bevis (0 = passer)» (`defaultno.ts:99`). Term names are mapped in `defaultno.ts:67-82`:

| key | Norwegian label | evidence text in `bevis` (verbatim, alle.json unless noted) |
|---|---|---|
| sun | sol | `sun (3 obs)` (utenlyd, utenmerker, utenflylyd only) |
| sunpath | solbane | `sun path (40 frames, best lat 59.5)` (same three) |
| aircraft | flylyd | never present in any mirrored variant |
| weather | vær | `weather (400 stations)` |
| live | MET nå | `live MET now (81 points, 0 raining, 4.8-16.5 C)`; utenfly: `621 points, 5 raining, -0.5-16.9 C`; utenflylyd: `394 points, 13 raining, 1.3-17.7 C` |
| sighting | flyene hun så | `plane sighting (3 event(s), 125 aircraft tracked)`; utenflylyd: `1 event(s)` |
| rarity | INGEN FLY | `INGEN FLY by day: 1255 aircraft 07:00-18:31, cost per >= 40 deg pass` |
| satellite | satellittskyer | `satellite clouds (4 passes)`; utenfly `1 passes`; utenflylyd `2 passes` |
| prior | forhånd | `prior (mostly flat / no ferry: west-coast routes penalised)` |
| drive | kjøretid | `drive from Oslo 3-8.5 h soft (~162-458 km straight line)` |
| rain | regn | `rain elsewhere since stream start: 796 wet of 831 stations, radar 76 snapshots`; utenfly `794 of 830, radar 69`; utenflylyd `342 of 826, radar 3` |
| pine / furu | furu / furu (NIBIO) | `furu (NIBIO SR16 pine share + forest cover)` |
| berries | bær | `tyttebær (GBIF dry-heath share, weak)` |
| (skytefelt) | n/a | `skytefelt (Forsvarsbygg): 68 ranges, 77 cells inside penalised e^-3`. This is a multiplicative mask with no `deler` key; it appears only in alle and utenfly |

What I inferred from the numbers (interpretation, not documented by default.no):

- **The rarity penalty is dag/3, capped at 3.0.** Here `dag` is the number of daytime passes at ≥40° (sjelden.json). At 61.45/11.10, dag = 4 gives 1.333, and sjelden `r` = exp(−dag/3) (dag 2 → 0.513, 3 → 0.368, 4 → 0.264, 5 → 0.189). So the penalties behave like **negative log-likelihoods in nats**.
- Several terms cap at 3.0 (rarity, rain, sighting). sighting reaches 3.534 in one case and sun 4.745, so the caps differ by term.
- `sunpath` is nearly flat (3.30–3.86 everywhere), so it hardly discriminates. That fits default.no's own remark that solbane is «et svakt bevis» (`AnalysePanel.tsx:344-345`).
- `berries` is 0.0 at almost every listed area, so it is effectively unused.
- List order is **not** strictly by m10. The alle list goes m10 0.11, 0.078, 0.06, 0.015, 0.017, 0.011, 0.045…, so it is probably ordered by peak cell with non-maximum suppression. m10 and m25 are the posterior mass within 10 and 25 km.
- `skog` is the forest share of the cell.

### 5.2 Top-12 areas of every variant (all numbers verbatim; "sum" = sum of listed penalties, computed by me)

#### fusjon/alle.json — magnus label «Alt bevis» — oppdatert 2026-09-24T18:31:43.673615+02:00

bevis (verbatim): `weather (400 stations)`; `prior (mostly flat / no ferry: west-coast routes penalised)`; `drive from Oslo 3-8.5 h soft (~162-458 km straight line)`; `live MET now (81 points, 0 raining, 4.8-16.5 C)`; `skytefelt (Forsvarsbygg): 68 ranges, 77 cells inside penalised e^-3`; `plane sighting (3 event(s), 125 aircraft tracked)`; `INGEN FLY by day: 1255 aircraft 07:00-18:31, cost per >= 40 deg pass`; `rain elsewhere since stream start: 796 wet of 831 stations, radar 76 snapshots`; `satellite clouds (4 passes)`; `tyttebær (GBIF dry-heath share, weak)`; `furu (NIBIO SR16 pine share + forest cover)`

| # | lat, lon | m10 | m25 | skog | weather | live | sighting | rarity | satellite | prior | drive | rain | pine | berries | furu | sum |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 61.45, 11.1 | 0.11 | 0.289 | 0.985 | 1.265 | 0.0 | 0.0 | 1.333 | 1.863 | -0.0 | -0.0 | 1.1 | 0.307 | 0.0 | 0.0 | 5.868 |
| 2 | 60.95, 11.3 | 0.078 | 0.265 | 0.702 | 1.787 | 0.0 | 0.0 | 3.0 | 1.863 | -0.0 | 0.14 | 0.22 | 0.19 | 0.0 | 0.0 | 7.2 |
| 3 | 60.7, 11.6 | 0.06 | 0.171 | 0.918 | 1.438 | 0.5 | 0.13 | 3.0 | 1.875 | -0.0 | 0.304 | 0.0 | 0.242 | 0.0 | 0.0 | 7.489 |
| 4 | 60.5, 5.1 | 0.015 | 0.017 | 0.692 | 0.926 | 1.927 | 0.792 | 1.667 | 0.625 | 0.7 | -0.0 | 0.1 | 0.544 | 0.0 | 0.0 | 7.281 |
| 5 | 61.75, 11.1 | 0.017 | 0.094 | 0.945 | 1.11 | 0.0 | 2.045 | 3.0 | 1.378 | -0.0 | -0.0 | 0.2 | 0.221 | 0.0 | 0.0 | 7.954 |
| 6 | 59.9, 11.2 | 0.011 | 0.022 | 0.879 | 1.615 | 0.0 | 0.0 | 3.0 | 1.583 | -0.0 | 1.456 | 0.6 | 0.509 | 0.0 | 0.0 | 8.763 |
| 7 | 61.1, 11.0 | 0.045 | 0.232 | 0.879 | 2.262 | 0.06 | 1.02 | 1.0 | 1.633 | -0.0 | 0.065 | 1.9 | 0.157 | 0.0 | 0.309 | 8.406 |
| 8 | 58.5, 6.3 | 0.017 | 0.038 | 0.424 | 1.37 | 0.0 | 0.203 | 3.0 | 0.0 | 0.7 | -0.0 | 3.0 | 0.062 | 0.0 | 0.549 | 8.884 |
| 9 | 60.95, 11.8 | 0.027 | 0.098 | 0.777 | 2.037 | 0.06 | 1.716 | 3.0 | 1.875 | -0.0 | 0.083 | 0.0 | 0.159 | 0.0 | 0.073 | 9.003 |
| 10 | 60.55, 6.5 | 0.012 | 0.027 | 0.577 | 1.328 | 0.74 | 0.004 | 0.667 | 1.11 | 0.7 | -0.0 | 3.0 | 0.165 | 0.0 | 0.274 | 7.988 |
| 11 | 58.75, 9.1 | 0.007 | 0.007 | 0.524 | 1.138 | 0.0 | 3.534 | 3.0 | 1.045 | -0.0 | 0.0 | 0.0 | 0.221 | 0.0 | 0.0 | 8.938 |
| 12 | 60.3, 6.6 | 0.006 | 0.026 | 0.486 | 0.872 | 0.5 | 0.656 | 1.0 | 1.172 | 0.7 | -0.0 | 3.0 | 0.044 | 0.0 | 1.024 | 8.968 |

#### fusjon/utenlyd.json — magnus label «Uten lyd og sol» — oppdatert 2026-09-24T18:37:58.585943+02:00

bevis (verbatim): `sun (3 obs)`; `sun path (40 frames, best lat 59.5)`; `weather (400 stations)`; `prior (mostly flat / no ferry: west-coast routes penalised)`; `drive from Oslo 3-8.5 h soft (~162-458 km straight line)`; `live MET now (81 points, 0 raining, 4.8-16.5 C)`; `plane sighting (3 event(s), 125 aircraft tracked)`; `INGEN FLY by day: 1255 aircraft 07:00-18:31, cost per >= 40 deg pass`; `rain elsewhere since stream start: 796 wet of 831 stations, radar 76 snapshots`; `satellite clouds (4 passes)`; `tyttebær (GBIF dry-heath share, weak)`; `furu (NIBIO SR16 pine share + forest cover)`

| # | lat, lon | m10 | m25 | skog | sun | sunpath | weather | live | sighting | rarity | satellite | prior | drive | rain | pine | berries | furu | sum |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 61.45, 11.1 | 0.164 | 0.362 | 0.985 | 0.229 | 3.42 | 1.265 | 0.0 | 0.0 | 1.333 | 1.863 | -0.0 | -0.0 | 1.1 | 0.307 | 0.0 | 0.0 | 9.517 |
| 2 | 60.95, 11.3 | 0.083 | 0.297 | 0.702 | 0.133 | 3.37 | 1.787 | 0.0 | 0.0 | 3.0 | 1.863 | -0.0 | 0.14 | 0.22 | 0.19 | 0.0 | 0.0 | 10.703 |
| 3 | 60.7, 11.6 | 0.067 | 0.205 | 0.918 | 0.063 | 3.351 | 1.438 | 0.5 | 0.13 | 3.0 | 1.875 | -0.0 | 0.304 | 0.0 | 0.242 | 0.0 | 0.0 | 10.903 |
| 4 | 61.1, 11.0 | 0.053 | 0.271 | 0.879 | 0.234 | 3.384 | 2.262 | 0.06 | 1.02 | 1.0 | 1.633 | -0.0 | 0.065 | 1.9 | 0.157 | 0.0 | 0.309 | 12.024 |
| 5 | 59.9, 11.2 | 0.013 | 0.026 | 0.879 | 0.11 | 3.306 | 1.615 | 0.0 | 0.0 | 3.0 | 1.583 | -0.0 | 1.456 | 0.6 | 0.509 | 0.0 | 0.0 | 12.179 |
| 6 | 61.75, 11.1 | 0.015 | 0.08 | 0.945 | 0.256 | 3.456 | 1.11 | 0.0 | 2.045 | 3.0 | 1.378 | -0.0 | -0.0 | 0.2 | 0.221 | 0.0 | 0.0 | 11.666 |
| 7 | 60.95, 11.8 | 0.03 | 0.119 | 0.777 | 0.044 | 3.37 | 2.037 | 0.06 | 1.716 | 3.0 | 1.875 | -0.0 | 0.083 | 0.0 | 0.159 | 0.0 | 0.073 | 12.417 |
| 8 | 58.75, 9.1 | 0.005 | 0.005 | 0.524 | 1.087 | 3.304 | 1.138 | 0.0 | 3.534 | 3.0 | 1.045 | -0.0 | 0.0 | 0.0 | 0.221 | 0.0 | 0.0 | 13.329 |
| 9 | 61.25, 11.4 | 0.013 | 0.229 | 0.961 | 0.126 | 3.399 | 2.031 | 0.007 | 0.203 | 3.0 | 1.875 | -0.0 | 0.006 | 3.0 | 0.205 | 0.0 | 0.197 | 14.049 |
| 10 | 60.55, 6.5 | 0.003 | 0.005 | 0.577 | 4.722 | 3.339 | 1.328 | 0.74 | 0.004 | 0.667 | 1.11 | 0.7 | -0.0 | 3.0 | 0.165 | 0.0 | 0.274 | 16.049 |
| 11 | 60.45, 11.0 | 0.002 | 0.007 | 0.989 | 0.187 | 3.332 | 1.865 | 0.5 | 2.592 | 1.667 | 1.863 | -0.0 | 0.786 | 0.0 | 0.029 | 0.055 | 1.5 | 14.376 |
| 12 | 58.5, 6.3 | 0.002 | 0.004 | 0.424 | 4.745 | 3.311 | 1.37 | 0.0 | 0.203 | 3.0 | 0.0 | 0.7 | -0.0 | 3.0 | 0.062 | 0.0 | 0.549 | 16.94 |

#### fusjon/utenmerker.json — magnus label «Uten håndmerkede flylyder» — oppdatert 2026-09-24T18:38:09.338160+02:00

bevis (verbatim): `sun (3 obs)`; `sun path (40 frames, best lat 59.5)`; `weather (400 stations)`; `prior (mostly flat / no ferry: west-coast routes penalised)`; `drive from Oslo 3-8.5 h soft (~162-458 km straight line)`; `live MET now (81 points, 0 raining, 4.8-16.5 C)`; `plane sighting (3 event(s), 125 aircraft tracked)`; `satellite clouds (4 passes)`; `tyttebær (GBIF dry-heath share, weak)`; `furu (NIBIO SR16 pine share + forest cover)`

| # | lat, lon | m10 | m25 | skog | sun | sunpath | weather | live | sighting | satellite | prior | drive | pine | berries | furu | sum |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 61.4, 11.1 | 0.102 | 0.448 | 0.989 | 0.224 | 3.415 | 1.288 | 0.0 | 0.0 | 1.735 | -0.0 | -0.0 | 0.362 | 0.0 | 0.0 | 7.024 |
| 2 | 60.95, 11.3 | 0.042 | 0.181 | 0.702 | 0.133 | 3.37 | 1.787 | 0.0 | 0.0 | 1.863 | -0.0 | 0.14 | 0.19 | 0.0 | 0.0 | 7.483 |
| 3 | 61.2, 11.4 | 0.061 | 0.288 | 0.88 | 0.123 | 3.394 | 1.945 | 0.007 | 0.203 | 1.81 | -0.0 | 0.016 | 0.327 | 0.0 | 0.137 | 7.962 |
| 4 | 61.55, 10.7 | 0.03 | 0.205 | 0.922 | 0.4 | 3.431 | 1.485 | 0.0 | 0.49 | 1.875 | -0.0 | -0.0 | 0.409 | 0.0 | 0.0 | 8.09 |
| 5 | 60.7, 11.6 | 0.025 | 0.097 | 0.918 | 0.063 | 3.351 | 1.438 | 0.5 | 0.13 | 1.875 | -0.0 | 0.304 | 0.242 | 0.0 | 0.0 | 7.903 |
| 6 | 59.9, 11.2 | 0.016 | 0.038 | 0.879 | 0.11 | 3.306 | 1.615 | 0.0 | 0.0 | 1.583 | -0.0 | 1.456 | 0.509 | 0.0 | 0.0 | 8.579 |
| 7 | 58.5, 6.3 | 0.013 | 0.026 | 0.424 | 4.745 | 3.311 | 1.37 | 0.0 | 0.203 | 0.0 | 0.7 | -0.0 | 0.062 | 0.0 | 0.549 | 10.94 |
| 8 | 61.15, 10.9 | 0.028 | 0.209 | 0.873 | 0.275 | 3.389 | 2.529 | 0.0 | 1.02 | 1.85 | -0.0 | 0.044 | 0.046 | 0.0 | 0.0 | 9.153 |
| 9 | 61.8, 11.2 | 0.028 | 0.094 | 0.829 | 0.225 | 3.462 | 1.027 | 0.0 | 1.904 | 1.353 | -0.0 | -0.0 | 0.687 | 0.0 | 0.0 | 8.658 |
| 10 | 60.95, 11.8 | 0.012 | 0.086 | 0.777 | 0.044 | 3.37 | 2.037 | 0.06 | 1.716 | 1.875 | -0.0 | 0.083 | 0.159 | 0.0 | 0.073 | 9.417 |
| 11 | 60.45, 6.7 | 0.005 | 0.019 | 0.432 | 4.368 | 3.332 | 0.541 | 0.5 | 0.593 | 1.085 | 0.7 | -0.0 | 0.141 | 0.0 | 0.0 | 11.26 |
| 12 | 59.6, 11.0 | 0.005 | 0.021 | 0.817 | 0.144 | 3.299 | 1.335 | 0.0 | 2.045 | 1.25 | -0.0 | 1.203 | 0.29 | 0.0 | 0.0 | 9.566 |

#### fusjon/utenflylyd.json — magnus label «Uten flylyd (eldre)» — oppdatert 2026-09-22T14:29:42.667406+02:00

bevis (verbatim): `sun (3 obs)`; `sun path (40 frames, best lat 59.5)`; `weather (400 stations)`; `prior (mostly flat / no ferry: west-coast routes penalised)`; `drive from Oslo 3-8.5 h soft (~162-458 km straight line)`; `live MET now (394 points, 13 raining, 1.3-17.7 C)`; `plane sighting (1 event(s), 125 aircraft tracked)`; `INGEN FLY by day: 1255 aircraft 07:00-18:31, cost per >= 40 deg pass`; `rain elsewhere since stream start: 342 wet of 826 stations, radar 3 snapshots`; `satellite clouds (2 passes)`; `tyttebær (GBIF dry-heath share, weak)`; `furu (NIBIO SR16 pine share + forest cover)`

| # | lat, lon | m10 | m25 | skog | sun | sunpath | weather | live | sighting | rarity | satellite | prior | drive | rain | pine | berries | furu | sum |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 61.75, 8.4 | 0.034 | 0.077 | 0.81 | 2.269 | 3.456 | 0.377 | 0.0 | 0.0 | 1.333 | 0.357 | -0.0 | -0.0 | 0.0 | 0.253 | 0.0 | 0.493 | 8.538 |
| 2 | 61.45, 11.0 | 0.026 | 0.06 | 0.981 | 0.264 | 3.42 | 1.264 | 0.5 | 0.0 | 1.0 | 1.225 | -0.0 | -0.0 | 0.0 | 0.224 | 0.0 | 0.33 | 8.227 |
| 3 | 60.9, 8.9 | 0.019 | 0.059 | 0.586 | 1.585 | 3.366 | 0.244 | 0.427 | 0.002 | 1.0 | 0.025 | -0.0 | 0.011 | 0.0 | 0.006 | 0.0 | 1.5 | 8.166 |
| 4 | 61.0, 12.0 | 0.023 | 0.062 | 0.737 | 0.029 | 3.374 | 1.551 | 0.06 | 1.21 | 1.0 | 1.25 | -0.0 | 0.04 | 0.0 | 0.572 | 0.0 | 0.0 | 9.086 |
| 5 | 61.1, 11.0 | 0.017 | 0.06 | 0.879 | 0.234 | 3.384 | 1.794 | 1.127 | 0.0 | 1.0 | 0.892 | -0.0 | 0.065 | 0.0 | 0.157 | 0.0 | 0.309 | 8.962 |
| 6 | 64.1, 13.0 | 0.01 | 0.027 | 0.419 | 0.037 | 3.858 | 1.402 | 0.5 | 1.392 | 0.0 | 1.25 | -0.0 | 0.078 | 0.0 | 0.314 | 0.0 | 0.0 | 8.831 |
| 7 | 60.45, 12.6 | 0.009 | 0.021 | 0.577 | 0.083 | 3.332 | 0.928 | 0.5 | 1.369 | 1.0 | 0.843 | -0.0 | 0.146 | 0.0 | 0.281 | 0.0 | 0.33 | 8.812 |
| 8 | 60.35, 11.2 | 0.009 | 0.016 | 0.59 | 0.127 | 3.327 | 1.232 | 0.0 | 0.0 | 3.0 | 0.28 | -0.0 | 0.894 | 0.0 | 0.072 | 0.0 | 0.93 | 9.862 |
| 9 | 60.45, 10.1 | 0.007 | 0.012 | 0.954 | 0.587 | 3.332 | 1.132 | 0.427 | 0.203 | 3.0 | 0.0 | -0.0 | 0.658 | 0.0 | 0.496 | 0.0 | 0.0 | 9.835 |
| 10 | 61.85, 10.2 | 0.004 | 0.017 | 0.485 | 0.711 | 3.468 | 0.268 | 0.0 | 3.0 | 1.667 | 0.23 | -0.0 | -0.0 | 0.0 | 0.319 | 0.0 | 0.0 | 9.663 |
| 11 | 60.9, 11.3 | 0.006 | 0.038 | 0.942 | 0.131 | 3.366 | 0.755 | 0.0 | 0.0 | 3.0 | 1.25 | -0.0 | 0.178 | 0.0 | 0.298 | 0.0 | 0.197 | 9.175 |
| 12 | 62.2, 9.7 | 0.008 | 0.02 | 0.592 | 1.118 | 3.516 | 0.492 | 0.107 | 3.0 | 0.0 | 0.383 | -0.0 | -0.0 | 0.2 | 0.094 | 0.0 | 0.274 | 9.184 |

#### fusjon/utenfly.json — magnus label «Uten fly» — oppdatert 2026-09-24T13:21:48.390834+02:00

bevis (verbatim): `weather (400 stations)`; `prior (mostly flat / no ferry: west-coast routes penalised)`; `drive from Oslo 3-8.5 h soft (~162-458 km straight line)`; `live MET now (621 points, 5 raining, -0.5-16.9 C)`; `skytefelt (Forsvarsbygg): 68 ranges, 77 cells inside penalised e^-3`; `rain elsewhere since stream start: 794 wet of 830 stations, radar 69 snapshots`; `satellite clouds (1 passes)`; `tyttebær (GBIF dry-heath share, weak)`; `furu (NIBIO SR16 pine share + forest cover)`

| # | lat, lon | m10 | m25 | skog | weather | live | satellite | prior | drive | rain | pine | berries | furu | sum |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 61.45, 5.6 | 0.019 | 0.04 | 0.67 | 0.747 | 0.0 | 0.0 | 0.7 | -0.0 | 0.0 | 0.267 | 0.0 | 0.0 | 1.714 |
| 2 | 61.9, 6.0 | 0.023 | 0.05 | 0.503 | 1.136 | 0.0 | 0.0 | 0.7 | -0.0 | 0.0 | 0.021 | 0.0 | 0.0 | 1.857 |
| 3 | 60.9, 5.1 | 0.023 | 0.044 | 0.489 | 0.656 | 0.327 | 0.0 | 0.7 | -0.0 | 0.0 | 0.299 | 0.0 | 0.0 | 1.982 |
| 4 | 60.95, 6.0 | 0.007 | 0.025 | 0.559 | 0.33 | 0.0 | 0.0 | 0.7 | -0.0 | 0.0 | 0.053 | 0.023 | 0.887 | 1.993 |
| 5 | 61.6, 6.5 | 0.013 | 0.033 | 0.571 | 1.039 | 0.0 | 0.152 | 0.7 | -0.0 | 0.0 | 0.026 | 0.0 | 1.144 | 3.061 |
| 6 | 60.75, 6.5 | 0.006 | 0.023 | 0.901 | 0.916 | 0.0 | 0.255 | 0.7 | -0.0 | 0.0 | 0.237 | 0.0 | 0.699 | 2.807 |
| 7 | 59.8, 6.0 | 0.007 | 0.022 | 0.488 | 1.609 | 0.0 | 0.205 | 0.7 | -0.0 | 0.0 | 0.088 | 0.0 | 0.643 | 3.245 |
| 8 | 59.3, 6.2 | 0.01 | 0.015 | 0.732 | 0.801 | 0.5 | 0.51 | 0.7 | -0.0 | 0.0 | 0.117 | 0.0 | 0.073 | 2.701 |
| 9 | 59.5, 7.9 | 0.005 | 0.008 | 0.448 | 1.011 | 0.0 | 0.255 | 0.7 | -0.0 | 0.8 | 0.065 | 0.0 | 0.48 | 3.311 |
| 10 | 63.1, 9.4 | 0.005 | 0.013 | 0.56 | 0.621 | 0.5 | 1.99 | -0.0 | -0.0 | 0.0 | 0.206 | 0.0 | 0.073 | 3.39 |
| 11 | 60.5, 5.1 | 0.003 | 0.009 | 0.692 | 1.023 | 1.707 | 0.0 | 0.7 | -0.0 | 0.1 | 0.544 | 0.0 | 0.0 | 4.074 |
| 12 | 61.9, 10.1 | 0.005 | 0.017 | 0.625 | 0.442 | 0.5 | 2.5 | -0.0 | -0.0 | 0.0 | 0.541 | 0.0 | 0.0 | 3.983 |

#### fusjon/fly.json — magnus label «Bare flyene hun så» — oppdatert 2026-09-24T18:31:52.874968+02:00

bevis (verbatim): `plane sighting (3 event(s), 125 aircraft tracked)`

| # | lat, lon | m10 | m25 | skog | sighting | pine | sum |
|---|---|---|---|---|---|---|---|
| 1 | 67.8, 15.5 | 0.027 | 0.092 | 0.417 | 0.0 | 0.102 | 0.102 |
| 2 | 58.55, 6.1 | 0.028 | 0.081 | 0.412 | 0.0 | 0.101 | 0.101 |
| 3 | 67.5, 14.8 | 0.004 | 0.014 | 0.73 | 0.0 | 0.269 | 0.269 |
| 4 | 66.5, 14.2 | 0.023 | 0.121 | 0.449 | 0.0 | 0.0 | 0.0 |
| 5 | 60.45, 6.7 | 0.016 | 0.069 | 0.432 | 0.593 | 0.141 | 0.734 |
| 6 | 60.75, 11.3 | 0.028 | 0.136 | 0.744 | 0.0 | 0.336 | 0.336 |
| 7 | 60.95, 11.6 | 0.017 | 0.094 | 0.79 | 0.0 | 0.217 | 0.217 |
| 8 | 61.2, 11.1 | 0.022 | 0.118 | 0.478 | 0.0 | 0.136 | 0.136 |
| 9 | 59.9, 11.2 | 0.013 | 0.031 | 0.879 | 0.0 | 0.509 | 0.509 |
| 10 | 66.75, 13.7 | 0.016 | 0.114 | 0.608 | 0.0 | 0.022 | 0.022 |
| 11 | 61.45, 10.9 | 0.024 | 0.125 | 0.969 | 0.0 | 0.236 | 0.236 |
| 12 | 60.65, 5.4 | 0.012 | 0.02 | 0.756 | 0.002 | 0.545 | 0.547 |

#### fusjon/flyskog.json — magnus label «Flyene + skog» — oppdatert 2026-09-24T18:31:54.807864+02:00

bevis (verbatim): `drive from Oslo 3-8.5 h soft (~162-458 km straight line)`; `plane sighting (3 event(s), 125 aircraft tracked)`; `satellite clouds (4 passes)`; `tyttebær (GBIF dry-heath share, weak)`; `furu (NIBIO SR16 pine share + forest cover)`

| # | lat, lon | m10 | m25 | skog | sighting | satellite | drive | pine | berries | furu | sum |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 58.55, 6.1 | 0.13 | 0.349 | 0.412 | 0.0 | 0.0 | -0.0 | 0.101 | 0.0 | 0.429 | 0.53 |
| 2 | 60.65, 5.4 | 0.07 | 0.104 | 0.756 | 0.002 | 0.0 | -0.0 | 0.545 | 0.0 | 0.0 | 0.547 |
| 3 | 60.45, 6.5 | 0.034 | 0.1 | 0.41 | 0.0 | 0.995 | -0.0 | 0.026 | 0.0 | 0.2 | 1.221 |
| 4 | 61.4, 11.1 | 0.029 | 0.139 | 0.989 | 0.0 | 1.735 | -0.0 | 0.362 | 0.0 | 0.0 | 2.097 |
| 5 | 58.55, 6.5 | 0.03 | 0.195 | 0.582 | 1.904 | 0.0 | -0.0 | 0.062 | 0.0 | 0.0 | 1.966 |
| 6 | 60.95, 11.6 | 0.017 | 0.075 | 0.79 | 0.0 | 1.875 | 0.108 | 0.217 | 0.0 | 0.0 | 2.2 |
| 7 | 58.75, 8.9 | 0.01 | 0.022 | 0.661 | 1.061 | 1.057 | -0.0 | 0.489 | 0.0 | 0.0 | 2.607 |
| 8 | 61.2, 11.4 | 0.014 | 0.084 | 0.88 | 0.203 | 1.81 | 0.016 | 0.327 | 0.0 | 0.137 | 2.493 |
| 9 | 60.75, 11.3 | 0.022 | 0.093 | 0.744 | 0.0 | 1.875 | 0.317 | 0.336 | 0.0 | 0.0 | 2.528 |
| 10 | 61.55, 10.7 | 0.007 | 0.06 | 0.922 | 0.49 | 1.875 | -0.0 | 0.409 | 0.0 | 0.0 | 2.774 |
| 11 | 58.4, 6.4 | 0.016 | 0.181 | 0.593 | 1.166 | 0.0 | -0.0 | 0.046 | 0.0 | 1.213 | 2.425 |
| 12 | 61.15, 10.9 | 0.008 | 0.051 | 0.873 | 1.02 | 1.85 | 0.044 | 0.046 | 0.0 | 0.0 | 2.96 |

#### fusjon/stille.json — magnus label «Flyene + INGEN FLY» — oppdatert 2026-09-24T18:38:04.483870+02:00

bevis (verbatim): `plane sighting (3 event(s), 125 aircraft tracked)`; `INGEN FLY by day: 1255 aircraft 07:00-18:31, cost per >= 40 deg pass`

| # | lat, lon | m10 | m25 | skog | sighting | rarity | pine | sum |
|---|---|---|---|---|---|---|---|---|
| 1 | 61.35, 11.0 | 0.075 | 0.238 | 0.693 | 0.0 | 1.333 | 0.059 | 1.392 |
| 2 | 60.55, 6.6 | 0.059 | 0.113 | 0.6 | 0.004 | 0.667 | 0.22 | 0.891 |
| 3 | 60.3, 6.6 | 0.039 | 0.088 | 0.486 | 0.656 | 1.0 | 0.044 | 1.7 |
| 4 | 67.8, 14.9 | 0.032 | 0.072 | 0.623 | 0.884 | 1.333 | 0.186 | 2.403 |
| 5 | 61.1, 11.0 | 0.019 | 0.13 | 0.879 | 1.02 | 1.0 | 0.157 | 2.177 |
| 6 | 60.5, 5.1 | 0.004 | 0.014 | 0.692 | 0.792 | 1.667 | 0.544 | 3.003 |
| 7 | 67.5, 14.8 | 0.004 | 0.013 | 0.73 | 0.0 | 2.667 | 0.269 | 2.936 |
| 8 | 67.8, 15.5 | 0.02 | 0.069 | 0.417 | 0.0 | 3.0 | 0.102 | 3.102 |
| 9 | 61.6, 11.1 | 0.018 | 0.121 | 0.98 | 1.145 | 1.667 | 0.865 | 3.677 |
| 10 | 60.8, 11.5 | 0.018 | 0.092 | 0.975 | 0.0 | 3.0 | 0.543 | 3.543 |
| 11 | 66.5, 13.9 | 0.016 | 0.077 | 0.461 | 0.0 | 3.0 | 0.001 | 3.001 |
| 12 | 58.55, 6.2 | 0.016 | 0.054 | 0.583 | 0.0 | 3.0 | 0.036 | 3.036 |

#### fusjon/stilleskog.json — magnus label «Flyene + INGEN FLY + skog» — oppdatert 2026-09-24T18:38:06.397221+02:00

bevis (verbatim): `drive from Oslo 3-8.5 h soft (~162-458 km straight line)`; `plane sighting (3 event(s), 125 aircraft tracked)`; `INGEN FLY by day: 1255 aircraft 07:00-18:31, cost per >= 40 deg pass`; `satellite clouds (4 passes)`; `tyttebær (GBIF dry-heath share, weak)`; `furu (NIBIO SR16 pine share + forest cover)`

| # | lat, lon | m10 | m25 | skog | sighting | rarity | satellite | drive | pine | berries | furu | sum |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 60.55, 6.5 | 0.091 | 0.165 | 0.577 | 0.004 | 0.667 | 1.11 | -0.0 | 0.165 | 0.0 | 0.274 | 2.22 |
| 2 | 58.55, 6.1 | 0.091 | 0.244 | 0.412 | 0.0 | 3.0 | 0.0 | -0.0 | 0.101 | 0.0 | 0.429 | 3.53 |
| 3 | 60.65, 5.4 | 0.049 | 0.084 | 0.756 | 0.002 | 3.0 | 0.0 | -0.0 | 0.545 | 0.0 | 0.0 | 3.547 |
| 4 | 61.45, 11.1 | 0.076 | 0.192 | 0.985 | 0.0 | 1.333 | 1.863 | -0.0 | 0.307 | 0.0 | 0.0 | 3.503 |
| 5 | 61.1, 11.0 | 0.013 | 0.079 | 0.879 | 1.02 | 1.0 | 1.633 | 0.065 | 0.157 | 0.0 | 0.309 | 4.184 |
| 6 | 60.3, 6.6 | 0.045 | 0.122 | 0.486 | 0.656 | 1.0 | 1.172 | -0.0 | 0.044 | 0.0 | 1.024 | 3.896 |
| 7 | 62.5, 6.8 | 0.01 | 0.014 | 0.826 | 3.423 | 1.333 | 0.0 | -0.0 | 0.322 | 0.0 | 0.073 | 5.151 |
| 8 | 58.55, 6.5 | 0.021 | 0.136 | 0.582 | 1.904 | 3.0 | 0.0 | -0.0 | 0.062 | 0.0 | 0.0 | 4.966 |
| 9 | 60.95, 11.6 | 0.012 | 0.052 | 0.79 | 0.0 | 3.0 | 1.875 | 0.108 | 0.217 | 0.0 | 0.0 | 5.2 |
| 10 | 58.75, 8.9 | 0.007 | 0.015 | 0.661 | 1.061 | 3.0 | 1.057 | -0.0 | 0.489 | 0.0 | 0.0 | 5.607 |
| 11 | 60.75, 11.3 | 0.015 | 0.065 | 0.744 | 0.0 | 3.0 | 1.875 | 0.317 | 0.336 | 0.0 | 0.0 | 5.528 |
| 12 | 61.25, 11.4 | 0.013 | 0.11 | 0.961 | 0.203 | 3.0 | 1.875 | 0.006 | 0.205 | 0.0 | 0.197 | 5.486 |

### 5.3 Where each variant's "best 2 %" cells lie (level-3 clusters, 8-connected, computed from the grids)

| variant | largest level-3 clusters: n cells, centroid, lat range / lon range |
|---|---|
| alle | **50 @ 61.17/11.25 (60.80–61.55 N, 10.70–11.80 E)**; 10 @ 60.66/11.50; 6 @ 61.72/10.80; 2 each @ 61.88/11.25, 61.72/11.35, 61.72/11.10, 60.92/11.10, 58.72/9.10 |
| utenlyd | 25 @ 61.29/11.04 (61.05–61.55, 10.70–11.30); 10 @ 60.66/11.50; 9 @ 60.92/11.51; 2 @ 60.92/11.10; singles 61.75/11.10, 61.75/10.90, 61.40/10.70, 61.10/11.60 |
| utenmerker | **121 @ 61.28/11.18 (60.60–61.85, 10.70–11.80)**; 4 @ 59.95/11.18; 3 @ 58.53/6.33; 2 @ 60.12/11.15 |
| utenflylyd (22.09) | 37 @ 61.57/8.68 (Lesja/Lom); 23 @ 61.25/11.00; 20 @ 61.00/11.79; 7 @ 60.92/8.56; 6 @ 64.16/13.03 |
| utenfly (24.09 13:21) | 45 @ 60.84/12.09 (Solør/Finnskogen); 22 @ 61.86/11.62; 17 @ 60.93/4.93; 9 @ 61.83/10.33 |
| fly | 70 @ 66.68/14.11 (Saltfjellet); 52 @ 61.38/11.07; 52 @ 60.82/11.35; 31 @ 67.81/15.37; 24 @ 58.54/6.12; 18 @ 60.41/6.63 |
| flyskog | 37 @ 58.54/6.21; 30 @ 61.40/11.18; 23 @ 60.82/11.43; 10 @ 60.49/6.61; 9 @ 60.57/5.48 |
| stille | 62 @ 66.67/14.11; 58 @ 61.37/11.07; 44 @ 60.79/11.33; 33 @ 67.80/15.32; 24 @ 58.54/6.12 |
| stilleskog | 33 @ 61.38/11.10; 32 @ 58.56/6.16; 16 @ 60.50/6.53; 8 @ 60.58/5.46; 8 @ 60.31/6.60 |
| flylyd | 6 @ 62.42/10.93 (Tynset); 6 @ 61.78/11.13; 5 @ 61.80/10.50; the single best cell 60.0/9.9 is level 3 |
| sjelden | 69 @ 63.90/12.71; 63 @ 60.32/26.56 (Finland); 54 @ 60.70/21.14 (Åland/sea); 45 @ 65.23/11.60; the level-3 cells in southern Norway are scattered |

The plane-only variants (fly, stille) cannot tell apart the Østerdalen/Elverum corridor, Saltfjellet (66.5–67.9 N) and Sokndal/Rogaland (58.5 N, 6.1 E). Everything that separates them comes from weather, rain, satellite clouds, drive time and forest.

### 5.4 All grids sampled at key points (level; 0 = not in top 40 % / dry)

| point | alle | utenlyd | utenmerker | utenflylyd | utenfly | fly | flyskog | stille | stilleskog | flylyd | sjelden | regn | baer |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 61.45, 11.10 (default.no #1 cell) | 3 | 3 | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 2 | 2 | 1 | 3 |
| 61.452, 11.146 (plan stop 1) | 3 | 3 | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 2 | 2 | 1 | 3 |
| 61.38, 11.12 (Evenstad east/south) | 3 | 3 | 3 | 3 | 0 | 3 | 3 | 3 | 3 | 2 | 1 | 2 | 3 |
| 61.47, 10.97 (Gålaveien) | 3 | 3 | 3 | 3 | 1 | 3 | 3 | 3 | 3 | 2 | 2 | 2 | 3 |
| 60.95, 11.30 (Elverum/Løten) | 3 | 3 | 3 | 3 | 2 | 3 | 3 | 3 | 2 | 0 | 0 | 1 | 4 |
| 60.70, 11.60 (area 2) | 3 | 3 | 3 | 2 | 2 | 3 | 3 | 3 | 2 | 0 | 0 | 0 | 3 |
| 60.0, 9.9 (flylyd best) | 2 | 2 | 2 | 0 | 0 | 2 | 2 | 2 | 2 | 3 | 0 | 3 | 3 |
| 61.0, 10.7 (Sjusjøen) | 0 | 0 | 1 | 1 | 0 | 2 | 1 | 1 | 0 | 1 | 0 | 2 | 3 |
| 61.7255, 10.9594 (Atna) | 2 | 2 | 2 | 0 | 0 | 2 | 2 | 2 | 2 | 0 | 0 | 2 | 4 |
| 61.3045, 11.6283 (Rendalen) | 1 | 2 | 2 | 2 | 0 | 2 | 2 | 2 | 2 | 2 | 0 | 2 | 3 |
| 60.7, 12.4 (Finnskogen) | 2 | 2 | 1 | 2 | 3 | 2 | 0 | 1 | 1 | 0 | 0 | 0 | 3 |
| 58.6, 8.7 (Froland) | 0 | 0 | 0 | 2 | 1 | 2 | 2 | 2 | 2 | 0 | 0 | 3 | 3 |
| 58.55, 6.10 (area 5) | 2 | 1 | 2 | 0 | 1 | 3 | 3 | 3 | 3 | 0 | 0 | 3 | 4 |

### 5.5 How default.no's #1 moved over time (from secondary records)

| when | default.no #1 (and others) | source |
|---|---|---|
| 22.09 14:29 (fusjon/utenflylyd, "eldre kjøring") | 61.75/8.40 (Lesja/Dovre). rejected.json later says: «Lå som nr. 1 i en utdatert fusjonsvariant (22.09, uten fly). Ingen av flyene hun så var i nærheten.» | `data/raw/magnus/public/data/defaultno/fusjon/utenflylyd.json`, `data/raw/magnus/public/data/defaultno/rejected.json` |
| 22.09 16:42 | 1 «Hamar øst mot Løten (skog)» 60.9/11.2; 2 «Rena og Åsta» 61.3/11.2; 3 Koppang 61.5/11.0 («8,2 °C klart i kveld»); 4 Finnskogen (Solør) 60.6/12.35 («8,5 °C»); 5 Trysil 61.3/12.3 («6,1 °C») | `data/raw/magnus/src/data/innhold.ts:1158-1166` (magnus record) |
| 23.09 | «Deres nr. 1 er nå Løten/Elverum-skogen, nr. 2 Rena–Åsta.» The «Sett + hørt fly»-test keeps «bare ca. 10 % av landet: vestsiden av Østerdalen (Elverum–Rena–Koppang under NOZ56U/NOZ9EG), Røros–Gauldal–Meråker-korridoren og Hallingdal» | `innhold.ts:175-181` |
| 23.09 | «Ringsaker er default.no sin kandidat nr. 5 (Brøttum)» | `innhold.ts:780` |
| mk_bevis 25.09 | "Elverum S (default.no #1)" used as a reference location | `data/raw/mk_bevis/bevis/claude-2026-09-25/adsb/fly_2109_resultat.txt:16,31` |
| **24.09 18:06–18:38** | **61.45/11.10 (Rena–Evenstad)**, p 0.127 | `omrader.json`, `fusjon/alle.json` |

---

## 6. Search areas (34; `omrader.json` + `steder.json` `omrader`)

`ekstra = True` means «Hypotese: ikke fra fusjonsmodellen» (`defaultno.ts:165`). `merke` is the hypothesis tag. `sterk` and `mulig` are km² of strong and possible site-finder pixels, `furu` is km² of pine, and `hogd22`/`hogd24` are km² cut since 2022/2024. Each box is ≈24 × 24 km for ranks 1–14 and smaller for the hypothesis boxes.

| rank | centre lat,lon | posterior p | ekstra (hypothesis) | merke | sterk km² | mulig km² | furu km² | hogd22 km² | hogd24 km² | bounds [[S,W],[N,E]] |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 61.45, 11.1 | 0.127 | False |  | 1.02 | 4.9 | 110.0 | 15.3 | 10.2 | [[61.3419,10.8738],[61.5581,11.3262]] |
| 2 | 60.7, 11.6 | 0.056 | False |  | 3.01 | 8.9 | 139.6 | 31.5 | 16.6 | [[60.5919,11.3791],[60.8081,11.8209]] |
| 3 | 60.95, 11.3 | 0.054 | False |  | 0.03 | 1.5 | 68.2 | 24.6 | 12.2 | [[60.8419,11.0774],[61.0581,11.5226]] |
| 4 | 61.75, 11.1 | 0.02 | False |  | 0.04 | 0.4 | 155.0 | 10.2 | 6.2 | [[61.6419,10.8716],[61.8581,11.3284]] |
| 5 | 58.55, 6.1 | 0.044 | False |  | 0.21 | 0.6 | 37.6 | 2.5 | 1.9 | [[58.4419,5.8928],[58.6581,6.3072]] |
| 6 | 59.65, 5.2 | 0.005 | False |  | 0.0 | 0.0 | 43.1 | 0.4 | 0.2 | [[59.5419,4.9860],[59.7581,5.4140]] |
| 7 | 60.5, 6.6 | 0.017 | False |  | 0.0 | 0.0 | 30.9 | 3.0 | 1.3 | [[60.3919,6.3805],[60.6081,6.8195]] |
| 8 | 60.95, 11.8 | 0.019 | False |  | 4.21 | 13.8 | 143.6 | 34.6 | 17.6 | [[60.8419,11.5774],[61.0581,12.0226]] |
| 9 | 61.2, 10.9 | 0.035 | False |  | 0.53 | 2.3 | 17.6 | 4.2 | 1.7 | [[61.0919,10.6756],[61.3081,11.1244]] |
| 10 | 58.75, 8.9 | 0.005 | False |  | 1.44 | 5.4 | 187.9 | 18.0 | 10.9 | [[58.6419,8.6916],[58.8581,9.1084]] |
| 11 | 61.45, 11.0 | 0.0 | True |  | 1.08 | 4.9 | 88.1 | 13.1 | 8.6 | [[61.3419,10.7738],[61.5581,11.2262]] |
| 12 | 61.2, 11.0 | 0.0 | True |  | 0.55 | 2.3 | 29.5 | 5.5 | 2.6 | [[61.0919,10.7756],[61.3081,11.2244]] |
| 13 | 60.8216, 10.8501 | 0.0 | True |  | 0.34 | 2.6 | 11.2 | 13.8 | 6.4 | [[60.7135,10.6284],[60.9297,11.0718]] |
| 14 | 62.8677, 11.8817 | 0.0 | True |  | 0.0 | 0.0 | 2.1 | 0.3 | 0.3 | [[62.7596,11.6446],[62.9758,12.1188]] |
| 61 | 61.5236, 11.0389 | 0.0 | True | and | 0.06 | 0.7 | 20.8 | 3.0 | 2.0 | [[61.4786,10.9444],[61.5686,11.1334]] |
| 62 | 61.5487, 11.0842 | 0.0 | True | and | 0.04 | 0.4 | 24.8 | 3.4 | 2.4 | [[61.5037,10.9896],[61.5937,11.1788]] |
| 21 | 61.3246, 11.5936 | 0.0 | True | ekorn | 0.47 | 1.9 | 38.0 | 2.8 | 1.1 | [[61.2615,11.4622],[61.3877,11.7250]] |
| 22 | 60.6736, 12.3839 | 0.0 | True | ekorn | 3.18 | 9.0 | 45.9 | 9.5 | 5.3 | [[60.6105,12.2551],[60.7367,12.5127]] |
| 31 | 61.5, 8.9 | 0.0 | True | lat61 | 0.0 | 0.0 | 3.7 | 0.1 | 0.0 | [[61.4099,8.7112],[61.5901,9.0888]] |
| 32 | 61.45, 11.0 | 0.0 | True | lat61 | 0.94 | 3.9 | 58.7 | 9.7 | 6.3 | [[61.3599,10.8115],[61.5401,11.1885]] |
| 91 | 61.482124, 11.491675 | 0.0 | True | link1 | 0.0 | 0.1 | 15.0 | 3.5 | 1.2 | [[61.4371,11.3973],[61.5272,11.5860]] |
| 41 | 61.7181, 8.3486 | 0.0 | True | lom | 0.0 | 0.0 | 10.1 | 0.1 | 0.1 | [[61.6640,8.2345],[61.7722,8.4627]] |
| 81 | 59.15, 11.7 | 0.0 | True | noplanes | 2.53 | 9.4 | 111.3 | 14.6 | 9.1 | [[59.0599,11.5243],[59.2401,11.8757]] |
| 82 | 59.45, 11.7 | 0.0 | True | noplanes | 3.14 | 6.0 | 84.3 | 15.7 | 8.7 | [[59.3599,11.5228],[59.5401,11.8772]] |
| 83 | 61.4, 11.1 | 0.0 | True | noplanes | 0.56 | 2.6 | 62.3 | 9.7 | 6.6 | [[61.3099,10.9118],[61.4901,11.2882]] |
| 71 | 62.295, 10.754 | 0.0 | True | nordistuen | 0.48 | 1.1 | 33.7 | 4.6 | 2.5 | [[62.2319,10.6184],[62.3581,10.8896]] |
| 101 | 60.95, 10.95 | 0.0 | True | ringsaker | 0.5 | 3.1 | 23.9 | 16.1 | 8.5 | [[60.8599,10.7645],[61.0401,11.1355]] |
| 102 | 61.05, 10.9 | 0.0 | True | ringsaker | 1.11 | 3.7 | 31.3 | 14.2 | 7.2 | [[60.9599,10.7139],[61.1401,11.0861]] |
| 111 | 60.75, 10.85 | 0.0 | True | ringsaker2 | 0.07 | 0.7 | 5.6 | 7.4 | 3.4 | [[60.6599,10.6656],[60.8401,11.0344]] |
| 112 | 60.85, 11.0 | 0.0 | True | ringsaker2 | 0.4 | 2.5 | 9.8 | 10.3 | 5.2 | [[60.7599,10.8150],[60.9401,11.1850]] |
| 121 | 60.8, 10.84 | 0.0 | True | stavsjo_fine | 0.15 | 1.2 | 3.1 | 2.6 | 1.1 | [[60.7550,10.7477],[60.8450,10.9323]] |
| 72 | 61.46, 10.98 | 0.0 | True | wide | 1.0 | 4.7 | 87.0 | 12.8 | 8.4 | [[61.3519,10.7537],[61.5681,11.2063]] |
| 73 | 61.3, 11.1 | 0.0 | True | wide | 0.15 | 1.2 | 57.4 | 9.1 | 5.7 | [[61.1919,10.8749],[61.4081,11.3251]] |
| 74 | 61.55, 11.05 | 0.0 | True | wide | 0.5 | 2.3 | 146.6 | 13.5 | 8.6 | [[61.4419,10.8231],[61.6581,11.2769]] |

The sum of posterior over ranks 1–10 is 0.382. Hypothesis tags: `and` (61, 62), `ekorn` (21, 22), `lat61` (31, 32), `link1` (91), `lom` (41), `noplanes` (81–83), `nordistuen` (71), `ringsaker` (101, 102), `ringsaker2` (111, 112), `stavsjo_fine` (121), `wide` (72–74). The meaning of the tags is not documented in the mirror. They look like community theories: "ekorn" (squirrel hint), Lom, Ringsaker, Stavsjø, "noplanes" = Østfold 59.15–59.45 N.

---

## 7. Site finder: 126 concrete sites (original default.no list, recovered)

Method per `omrader.json` note: «score = road band x uphill x pine/forest x relief along the view x sun horizons; abs_score = score x fusion mass within 10 km of the area». I checked that abs = score × area p: 0.995 × 0.127 = 0.12637 and 0.995 × 0.056 = 0.05572. Hypothesis areas have p = 0, so abs = 0.

Per mkekeoooo: «Stedsfinneren deres scorer hver 40 m-rute på avstand fra vei, stigning, furu, relieff langs kameraretningen, solhorisont og hogst» (`data/raw/mkekeoooo/rapport/Hordejakten_2026_fullstendig_rapport.pdf` p. 9). `retning` = 219.0° is the camera heading used for the relief test. Field key: `opp` = rise from road (m), `relieff` = match/soft along 219°, `hogst_m` = distance to nearest clear-cut, `tog_m` = distance to railway. The magnus pop-up labels are in `defaultno.ts:152`.

All 126 sites have `furu = true`. `vei_m` ranges 200–881 m. 6 of 126 have relief "soft". Area 1 has 40 sites (37 in the mirror). Most other areas have 3 sites each; areas 32 and 41 have 2, and area 14 has 1.

| # (default.no order) | area | lat | lon | score | abs | moh | road dist m | road class | road name | rise m (opp) | relief | pine | nearest cut m | rail m | in magnus mirror? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 61.44874 | 10.97747 | 0.995 | 0.12638 | 605 | 556 | tertiary | Birkebeinerveien | 75.3 | match | True | 215 | 3833 | **REMOVED 25.09** |
| 2 | 1 | 61.46351 | 10.95862 | 0.895 | 0.11372 | 414 | 544 | unclassified | Gålaveien | 51.5 | match | True | 556 | 4298 | yes |
| 3 | 1 | 61.46243 | 10.97521 | 0.877 | 0.11136 | 366 | 520 | unclassified | Gålaveien | 13.6 | match | True | 735 | 3493 | yes |
| 4 | 1 | 61.43072 | 11.04684 | 0.858 | 0.10894 | 322 | 483 | tertiary | Storelvdalsveien | 66.0 | match | True | 283 | 1539 | yes |
| 5 | 1 | 61.47252 | 10.96767 | 0.837 | 0.10632 | 402 | 360 | unclassified | Gålaveien | 47.0 | match | True | 120 | 3681 | yes |
| 6 | 1 | 61.47468 | 11.09887 | 0.835 | 0.10606 | 686 | 566 | unclassified | Madsskardveien | 69.5 | match | True | 160 | 2558 | yes |
| 7 | 1 | 61.45306 | 11.14185 | 0.826 | 0.10488 | 652 | 522 | unclassified | Madsskardveien | 21.7 | match | True | 400 | 3960 | yes |
| 8 | 1 | 61.44514 | 11.11923 | 0.819 | 0.10402 | 621 | 512 | unclassified | Madsskardveien | 7.3 | match | True | 57 | 2490 | yes |
| 9 | 1 | 61.45270 | 11.14863 | 0.798 | 0.10136 | 647 | 483 | service |  | 41.7 | match | True | 369 | 4139 | yes |
| 10 | 1 | 61.45306 | 10.97747 | 0.786 | 0.0998 | 574 | 402 | tertiary | Birkebeinerveien | 56.6 | match | True | 595 | 3687 | **REMOVED 25.09** |
| 11 | 1 | 61.45631 | 11.06268 | 0.772 | 0.09803 | 329 | 447 | secondary | Ole Evenstads vei | 20.9 | match | True | 288 | 699 | yes |
| 12 | 1 | 61.43541 | 11.08831 | 0.758 | 0.09628 | 289 | 556 | secondary | Ole Evenstads vei | 20.1 | match | True | 80 | 626 | yes |
| 13 | 1 | 61.46640 | 11.07700 | 0.758 | 0.09626 | 628 | 544 | unclassified | Madsskardveien | 28.9 | match | True | 691 | 1737 | yes |
| 14 | 1 | 61.45342 | 11.13129 | 0.755 | 0.09592 | 685 | 560 | unclassified | Madsskardveien | 62.9 | match | True | 495 | 3499 | yes |
| 15 | 1 | 61.47108 | 10.98049 | 0.753 | 0.09569 | 409 | 360 | unclassified | Gålaveien | 56.2 | match | True | 544 | 3010 | yes |
| 16 | 1 | 61.46279 | 11.10339 | 0.752 | 0.09556 | 684 | 557 | unclassified | Madsskardveien | 71.8 | match | True | 735 | 2800 | yes |
| 17 | 1 | 61.44730 | 10.96541 | 0.748 | 0.09501 | 579 | 256 | tertiary | Birkebeinerveien | 28.7 | match | True | 240 | 4491 | **REMOVED 25.09** |
| 18 | 1 | 61.40477 | 11.03252 | 0.747 | 0.09487 | 590 | 573 | unclassified | Myklebysæterveien | 68.4 | match | True | 566 | 3819 | yes |
| 19 | 1 | 61.38423 | 11.00839 | 0.743 | 0.09439 | 664 | 522 | unclassified | Myklebysæterveien | 35.5 | match | True | 681 | 6385 | yes |
| 20 | 1 | 61.47324 | 11.14939 | 0.737 | 0.09362 | 755 | 512 | unclassified |  | 24.6 | match | True | 577 | 5115 | yes |
| 21 | 1 | 61.34604 | 10.98803 | 0.733 | 0.0931 | 783 | 506 | unclassified | Myklebysæterveien | 27.7 | match | True | 89 | 9982 | yes |
| 22 | 1 | 61.46820 | 11.03252 | 0.73 | 0.09273 | 304 | 330 | unclassified | Søstugutua | 38.2 | match | True | 342 | 488 | yes |
| 23 | 1 | 61.39216 | 11.04986 | 0.726 | 0.09217 | 594 | 495 | unclassified | Myklebysæterveien | 5.1 | match | True | 752 | 4316 | yes |
| 24 | 1 | 61.40225 | 11.05438 | 0.71 | 0.09022 | 548 | 560 | unclassified | Myklebysæterveien | 3.6 | match | True | 268 | 3268 | yes |
| 25 | 1 | 61.43649 | 11.13582 | 0.71 | 0.0902 | 532 | 362 | unclassified | Jernvinneveien | 14.1 | match | True | 233 | 2264 | yes |
| 26 | 1 | 61.37631 | 11.14336 | 0.709 | 0.09007 | 331 | 538 | unclassified |  | 6.6 | match | True | 322 | 1612 | yes |
| 27 | 1 | 61.39937 | 11.05363 | 0.703 | 0.08923 | 549 | 573 | unclassified | Myklebysæterveien | 4.0 | match | True | 233 | 3544 | yes |
| 28 | 1 | 61.46351 | 11.08379 | 0.7 | 0.08896 | 661 | 456 | unclassified | Madsskardveien | 59.7 | match | True | 573 | 1999 | yes |
| 29 | 1 | 61.46748 | 11.00990 | 0.7 | 0.0889 | 325 | 200 | unclassified | Gålaveien | 20.0 | match | True | 344 | 1576 | yes |
| 30 | 1 | 61.42712 | 11.01216 | 0.686 | 0.08708 | 679 | 526 | unclassified |  | 78.7 | match | True | 1414 | 3226 | yes |
| 31 | 1 | 61.43144 | 11.09661 | 0.68 | 0.08632 | 294 | 456 | secondary | Ole Evenstads vei | 27.0 | soft | True | 126 | 566 | yes |
| 32 | 1 | 61.39577 | 11.03478 | 0.68 | 0.08631 | 594 | 320 | unclassified | Myklebysæterveien | 16.6 | match | True | 358 | 4498 | yes |
| 33 | 1 | 61.38027 | 11.12149 | 0.677 | 0.086 | 361 | 561 | unclassified |  | 37.8 | match | True | 126 | 2008 | yes |
| 34 | 1 | 61.41991 | 11.05589 | 0.664 | 0.08438 | 349 | 632 | unclassified | Myklebysæterveien | 39.9 | match | True | 268 | 1754 | yes |
| 35 | 1 | 61.36730 | 11.09057 | 0.662 | 0.08409 | 547 | 600 | unclassified |  | 4.8 | soft | True | 342 | 4190 | yes |
| 36 | 1 | 61.38784 | 11.01367 | 0.66 | 0.08381 | 645 | 394 | unclassified | Myklebysæterveien | 18.7 | match | True | 794 | 5897 | yes |
| 37 | 1 | 61.39180 | 11.01894 | 0.653 | 0.08289 | 628 | 283 | unclassified |  | 16.5 | match | True | 288 | 5379 | yes |
| 38 | 1 | 61.38315 | 11.12300 | 0.646 | 0.08204 | 372 | 480 | unclassified |  | 56.9 | match | True | 215 | 1737 | yes |
| 39 | 1 | 61.37775 | 11.01970 | 0.643 | 0.08172 | 664 | 369 | unclassified | Myklebysæterveien | 32.3 | match | True | 641 | 6544 | yes |
| 40 | 1 | 61.47432 | 11.14034 | 0.641 | 0.08147 | 729 | 734 | unclassified |  | 17.0 | match | True | 769 | 4621 | yes |
| 41 | 2 | 60.66703 | 11.45089 | 0.995 | 0.05573 | 446 | 556 | track |  | 38.1 | match | True | 160 | 19069 | yes |
| 42 | 2 | 60.65622 | 11.48034 | 0.995 | 0.05573 | 446 | 556 | unclassified |  | 17.5 | match | True | 120 | 18227 | yes |
| 43 | 2 | 60.67207 | 11.46193 | 0.995 | 0.05571 | 400 | 544 | unclassified |  | 9.6 | match | True | 0 | 18283 | yes |
| 44 | 3 | 61.05793 | 11.14972 | 0.8 | 0.04318 | 636 | 680 | tertiary | Fjellvegen | 4.4 | match | True | 170 | 11120 | yes |
| 45 | 3 | 60.94441 | 11.09628 | 0.508 | 0.02745 | 603 | 561 | unclassified | Tørbustilvegen | 27.7 | match | True | 120 | 17891 | yes |
| 46 | 3 | 60.89865 | 11.09332 | 0.507 | 0.02735 | 471 | 566 | service |  | 5.8 | match | True | 120 | 17114 | yes |
| 47 | 4 | 61.67090 | 11.05622 | 0.7 | 0.014 | 645 | 755 | unclassified |  | 47.2 | soft | True | 369 | 7592 | yes |
| 48 | 4 | 61.67450 | 11.05394 | 0.645 | 0.01289 | 657 | 881 | unclassified |  | 55.6 | match | True | 691 | 7428 | yes |
| 49 | 4 | 61.65757 | 11.06384 | 0.628 | 0.01257 | 583 | 520 | unclassified |  | 3.1 | soft | True | 1103 | 8285 | yes |
| 50 | 5 | 58.45829 | 5.93804 | 0.866 | 0.03808 | 38 | 595 | service | Saurdalsveien | 16.2 | match | True | 556 | 1485 | yes |
| 51 | 5 | 58.46982 | 5.94494 | 0.836 | 0.03676 | 12 | 466 | service |  | 11.2 | match | True | 573 | 200 | yes |
| 52 | 5 | 58.46117 | 5.94771 | 0.796 | 0.03504 | 78 | 312 | service |  | 49.8 | match | True | 288 | 1160 | yes |
| 53 | 8 | 61.05432 | 11.66679 | 0.991 | 0.01884 | 307 | 560 | secondary | Julusdalsvegen | 10.6 | match | True | 268 | 23756 | yes |
| 54 | 8 | 61.05360 | 11.65937 | 0.918 | 0.01745 | 301 | 480 | secondary | Julusdalsvegen | 16.2 | soft | True | 200 | 23608 | yes |
| 55 | 8 | 61.03342 | 11.70389 | 0.912 | 0.01733 | 292 | 447 | unclassified | Linnerudvegen | 5.6 | match | True | 204 | 21969 | yes |
| 56 | 9 | 61.11550 | 11.00136 | 0.837 | 0.02929 | 628 | 537 | tertiary | Bjønnåsvegen | 15.2 | match | True | 89 |  | yes |
| 57 | 9 | 61.11081 | 10.98041 | 0.778 | 0.02721 | 691 | 645 | tertiary | Bjønnåsvegen | 65.7 | match | True | 57 |  | yes |
| 58 | 9 | 61.10865 | 11.04624 | 0.758 | 0.02653 | 573 | 544 | unclassified | Bjørgeligutua | 9.0 | match | True | 408 |  | yes |
| 59 | 10 | 58.83126 | 8.74127 | 0.895 | 0.00448 | 333 | 544 | unclassified | Spjotvasslia | 13.7 | match | True | 573 | 9498 | yes |
| 60 | 10 | 58.83162 | 8.73224 | 0.894 | 0.00447 | 344 | 557 | residential | Katterås hyttegrend | 35.2 | match | True | 792 | 9921 | yes |
| 61 | 10 | 58.84171 | 8.74822 | 0.89 | 0.00445 | 378 | 537 | unclassified | Spjotvasslia | 62.7 | match | True | 645 | 10018 | yes |
| 62 | 11 | 61.44874 | 10.97776 | 0.981 | 0.0 | 606 | 573 | tertiary | Birkebeinerveien | 74.1 | match | True | 215 | 3820 | **REMOVED 25.09** |
| 63 | 11 | 61.47324 | 10.96871 | 0.907 | 0.0 | 415 | 442 | unclassified | Gålaveien | 57.8 | match | True | 160 | 3640 | yes |
| 64 | 11 | 61.45162 | 10.97926 | 0.887 | 0.0 | 597 | 534 | tertiary | Birkebeinerveien | 75.1 | match | True | 488 | 3644 | **REMOVED 25.09** |
| 65 | 12 | 61.13640 | 10.97270 | 0.825 | 0.0 | 652 | 520 | service |  | 3.3 | match | True | 40 |  | yes |
| 66 | 12 | 61.11514 | 11.00187 | 0.819 | 0.0 | 627 | 512 | unclassified |  | 8.9 | match | True | 40 |  | yes |
| 67 | 12 | 61.10829 | 10.98317 | 0.803 | 0.0 | 672 | 609 | tertiary | Bjønnåsvegen | 47.7 | match | True | 40 |  | yes |
| 68 | 13 | 60.91511 | 10.95913 | 0.991 | 0.0 | 369 | 557 | service |  | 62.2 | match | True | 200 | 3683 | yes |
| 69 | 13 | 60.90574 | 11.02491 | 0.962 | 0.0 | 501 | 595 | service |  | 11.4 | match | True | 126 | 5458 | yes |
| 70 | 13 | 60.91692 | 10.96578 | 0.941 | 0.0 | 367 | 482 | unclassified |  | 18.6 | match | True | 179 | 4050 | yes |
| 71 | 14 | 62.97238 | 12.10572 | 0.41 | 0.0 | 744 | 447 | unclassified | Sylsjøvegen | 8.2 | match | True | 13181 |  | yes |
| 72 | 61 | 61.48774 | 11.04457 | 0.719 | 0.0 | 321 | 283 | trunk | Storelvdalsveien | 62.4 | match | True | 640 |  | yes |
| 73 | 61 | 61.51441 | 11.04532 | 0.645 | 0.0 | 301 | 215 | trunk | Storelvdalsveien | 41.5 | match | True | 362 |  | yes |
| 74 | 61 | 61.51765 | 11.04532 | 0.608 | 0.0 | 307 | 215 | trunk | Storelvdalsveien | 47.2 | match | True | 40 |  | yes |
| 75 | 62 | 61.51465 | 11.04525 | 0.66 | 0.0 | 299 | 233 | trunk | Storelvdalsveien | 39.3 | match | True | 362 | 1161 | yes |
| 76 | 62 | 61.51753 | 11.04525 | 0.63 | 0.0 | 305 | 233 | trunk | Storelvdalsveien | 45.7 | match | True | 57 | 1116 | yes |
| 77 | 62 | 61.50888 | 11.04676 | 0.566 | 0.0 | 297 | 240 | trunk | Storelvdalsveien | 38.1 | match | True | 200 | 1028 | yes |
| 78 | 21 | 61.31793 | 11.71714 | 0.997 | 0.0 | 485 | 447 | secondary | Slemdalsveien | 37.4 | match | True | 400 |  | yes |
| 79 | 21 | 61.34352 | 11.65931 | 0.977 | 0.0 | 505 | 431 | unclassified | Jensbuveien | 34.3 | match | True | 40 |  | yes |
| 80 | 21 | 61.36874 | 11.65030 | 0.897 | 0.0 | 472 | 447 | secondary | Slemdalsveien | 10.9 | match | True | 358 |  | yes |
| 81 | 22 | 60.69360 | 12.35042 | 0.997 | 0.0 | 297 | 453 | unclassified | Basbakkvegen | 36.7 | match | True | 0 |  | yes |
| 82 | 22 | 60.67090 | 12.38795 | 0.997 | 0.0 | 327 | 453 | unclassified | Tolvmilskogen | 19.5 | match | True | 339 |  | yes |
| 83 | 22 | 60.68964 | 12.36293 | 0.997 | 0.0 | 300 | 447 | unclassified | Basbakkvegen | 25.5 | match | True | 0 |  | yes |
| 84 | 32 | 61.45018 | 10.97700 | 0.978 | 0.0 | 597 | 468 | tertiary | Birkebeinerveien | 71.3 | match | True | 288 | 3808 | **REMOVED 25.09** |
| 85 | 32 | 61.43108 | 11.04713 | 0.913 | 0.0 | 320 | 447 | service |  | 62.1 | match | True | 256 | 1503 | yes |
| 86 | 91 | 61.45131 | 11.55998 | 0.529 | 0.0 | 662 | 418 | service |  | 11.2 | match | True | 400 |  | yes |
| 87 | 91 | 61.46645 | 11.57055 | 0.384 | 0.0 | 675 | 447 | service |  | 4.6 | match | True | 1970 |  | yes |
| 88 | 91 | 61.45780 | 11.57206 | 0.31 | 0.0 | 692 | 288 | service |  | 3.3 | match | True | 1288 |  | yes |
| 89 | 41 | 61.71828 | 8.34898 | 0.35 | 0.0 | 659 | 200 | unclassified | Galdhøpiggvegen | 26.0 | match | True | 312 |  | yes |
| 90 | 41 | 61.72405 | 8.37332 | 0.335 | 0.0 | 706 | 342 | unclassified | Myravegen | 47.9 | match | True | 1276 |  | yes |
| 91 | 81 | 59.18550 | 11.52537 | 0.942 | 0.0 | 95 | 402 | service |  | 5.3 | match | True | 291 |  | yes |
| 92 | 81 | 59.18153 | 11.53732 | 0.916 | 0.0 | 103 | 520 | service |  | 11.1 | match | True | 305 |  | yes |
| 93 | 81 | 59.17757 | 11.54294 | 0.893 | 0.0 | 107 | 456 | secondary | Håkenbyveien | 24.4 | match | True | 645 |  | yes |
| 94 | 82 | 59.42315 | 11.54509 | 0.997 | 0.0 | 184 | 447 | unclassified | Høytomtveien | 17.1 | match | True | 358 |  | yes |
| 95 | 82 | 59.39108 | 11.53871 | 0.993 | 0.0 | 143 | 456 | unclassified | Dalenveien | 17.6 | match | True | 165 |  | yes |
| 96 | 82 | 59.38315 | 11.54793 | 0.97 | 0.0 | 130 | 425 | unclassified | Dalenveien | 8.9 | match | True | 40 |  | yes |
| 97 | 83 | 61.44955 | 10.97616 | 0.844 | 0.0 | 593 | 447 | tertiary | Birkebeinerveien | 63.5 | match | True | 233 | 3872 | **REMOVED 25.09** |
| 98 | 83 | 61.47333 | 11.04994 | 0.838 | 0.0 | 390 | 442 | secondary | Ole Evenstads vei | 78.4 | match | True | 200 | 573 | yes |
| 99 | 83 | 61.47333 | 10.96864 | 0.831 | 0.0 | 419 | 442 | unclassified | Gålaveien | 60.7 | match | True | 160 | 3640 | yes |
| 100 | 71 | 62.28797 | 10.85825 | 0.997 | 0.0 | 504 | 447 | unclassified |  | 14.1 | match | True | 80 | 878 | yes |
| 101 | 71 | 62.28725 | 10.86523 | 0.988 | 0.0 | 542 | 440 | unclassified |  | 18.1 | match | True | 126 | 1221 | yes |
| 102 | 71 | 62.34599 | 10.86910 | 0.988 | 0.0 | 524 | 440 | primary | Rørosveien | 36.6 | match | True | 120 | 1414 | yes |
| 103 | 101 | 61.02694 | 10.96596 | 0.961 | 0.0 | 476 | 418 | unclassified |  | 8.4 | match | True | 379 |  | yes |
| 104 | 101 | 61.03450 | 10.95779 | 0.882 | 0.0 | 491 | 466 | tertiary | Åstdalsvegen | 22.0 | match | True | 165 |  | yes |
| 105 | 101 | 61.02982 | 10.96150 | 0.866 | 0.0 | 483 | 482 | tertiary | Åstdalsvegen | 19.8 | match | True | 495 |  | yes |
| 106 | 102 | 61.11396 | 11.00088 | 0.997 | 0.0 | 623 | 453 | unclassified |  | 7.0 | match | True | 144 |  | yes |
| 107 | 102 | 61.11793 | 10.99715 | 0.979 | 0.0 | 638 | 433 | tertiary | Bjønnåsvegen | 26.2 | match | True | 291 |  | yes |
| 108 | 102 | 61.09595 | 11.03884 | 0.903 | 0.0 | 589 | 369 | unclassified | Prestsetra | 20.0 | match | True | 377 |  | yes |
| 109 | 111 | 60.80568 | 10.95362 | 0.977 | 0.0 | 244 | 431 | unclassified |  | 56.8 | match | True | 179 |  | yes |
| 110 | 111 | 60.72784 | 10.98681 | 0.882 | 0.0 | 235 | 466 | secondary | Helgøyvegen | 22.5 | match | True | 80 |  | yes |
| 111 | 111 | 60.73613 | 10.99344 | 0.767 | 0.0 | 271 | 573 | service |  | 56.0 | match | True | 522 |  | yes |
| 112 | 112 | 60.90568 | 11.03218 | 0.99 | 0.0 | 442 | 442 | secondary | Kvemyrvegen | 38.4 | match | True | 89 |  | yes |
| 113 | 112 | 60.91649 | 10.96634 | 0.988 | 0.0 | 362 | 440 | unclassified |  | 12.6 | match | True | 204 |  | yes |
| 114 | 112 | 60.92009 | 10.95080 | 0.957 | 0.0 | 447 | 431 | tertiary | Dalaustvegen | 4.4 | match | True | 80 |  | yes |
| 115 | 121 | 60.81279 | 10.86844 | 0.838 | 0.0 | 322 | 442 | secondary | Årvollshøgda | 5.3 | match | True | 200 |  | yes |
| 116 | 121 | 60.81495 | 10.85957 | 0.816 | 0.0 | 306 | 480 | primary | Nesvegen | 57.8 | match | True | 179 |  | yes |
| 117 | 121 | 60.82505 | 10.86770 | 0.814 | 0.0 | 321 | 482 | service |  | 72.0 | match | True | 396 |  | yes |
| 118 | 72 | 61.44865 | 10.97736 | 0.995 | 0.0 | 602 | 556 | tertiary | Birkebeinerveien | 71.7 | match | True | 215 |  | **REMOVED 25.09** |
| 119 | 72 | 61.46306 | 10.96001 | 0.879 | 0.0 | 433 | 573 | unclassified | Gålaveien | 70.7 | match | True | 557 |  | yes |
| 120 | 72 | 61.46270 | 10.97585 | 0.877 | 0.0 | 363 | 520 | unclassified | Gålaveien | 8.3 | match | True | 716 |  | yes |
| 121 | 73 | 61.38414 | 11.00808 | 0.639 | 0.0 | 664 | 560 | unclassified | Myklebysæterveien | 34.8 | match | True | 744 |  | yes |
| 122 | 73 | 61.34595 | 10.98781 | 0.628 | 0.0 | 782 | 520 | unclassified | Myklebysæterveien | 30.0 | match | True | 215 |  | yes |
| 123 | 73 | 61.40505 | 11.03209 | 0.619 | 0.0 | 590 | 595 | unclassified | Myklebysæterveien | 74.5 | soft | True | 735 |  | yes |
| 124 | 74 | 61.44892 | 10.97700 | 0.976 | 0.0 | 603 | 522 | tertiary | Birkebeinerveien | 74.5 | match | True | 200 | 3835 | **REMOVED 25.09** |
| 125 | 74 | 61.47306 | 10.96944 | 0.907 | 0.0 | 410 | 442 | unclassified | Gålaveien | 46.2 | match | True | 200 | 3561 | yes |
| 126 | 74 | 61.46261 | 10.97549 | 0.877 | 0.0 | 364 | 520 | unclassified | Gålaveien | 11.2 | match | True | 662 | 3469 | yes |

Notes:
- Site #4 (61.43072, 11.04684, Storelvdalsveien, abs 0.10894) lies about 80 m from the pin «61.4307, 11.0483»: «privat vei - sjaforen er her NA (23.09 00:40), serviceveg av Storelvdalsveien, 410 m gange». rejected.json says «Sjekket på bakken natt til 23.09: bolighus 7 m unna, ikke boksen.» default.no left the site in the list. **Treat it as searched-empty (approximately).** [b]
- The removed Birkebeinerveien sites (#1, 10, 17, 62, 64, 84, 97, 118, 124) cluster at 61.447–61.453 N, 10.965–10.979 E, 574–606 moh, on the Birkebeinerveien (tertiary road) ridge west of Glomma. They sit next to rejected «61.4495, 10.9763 (bom)» and the removed pins «BOM / privat vei (23.09 ca 00:30) … Ga forbi bommen til fots, 500 m» and «privat vei - pin Birkebeinerveien-ryggen, ikke sjekket til fots».
- mkekeoooo later found **weak forest support** at exactly 61.4487, 10.9775 (low canopy values; none of 25 sample positions passes all forest requirements), but says it «utelukker ikke hele A1-området» (`data/raw/mkekeoooo/README.md:24`). Its report says A1 fails only on the 07:51 morning-sun test, which is itself unverified (report p. 1, 17). [c]

---

## 8. Field plan: 40 stops (original, recovered) and driving routes

`plan.json`, generated «2026-09-24 17:04». Note, verbatim: «alle klarer de tre flyene hun saa (innen 5 grader), rangert etter site finder-score, fusjon og skogtype fra laser (hogstflater/jorder nedprioritert, moden skog opp); sjekkede stopp ligger sist; boksen staar i moden skog 15-22 m med lysning».

My reading of the fields (interpretation):
- `plane_shortfall` = degrees below the sighting threshold (≤4.2, «innen 5 grader»).
- `dayplanes` = daytime passes ≥40° (INGEN FLY count).
- `fusion` appears to be a fusion penalty relative to the best cell (0 = best): all "ost for Glomma" stops at 61.43–61.48 N are 0.0, Gålaveien is 1.15, Myklebysæterveien 1.58, and southern Evenstad-øst 2.23.
- `canopy_*`, `mature` and `open` come from laser data.
- `checked` is empty for every stop.

| rank | name | box lat,lon | park lat,lon | road_type / road | walk | site_score | fusion | plane_shortfall | dayplanes | rise m | relief m | rail m | cut m | nearest bldg m | canopy med / p90 m | mature | open | terrain range 150 m | pine | checked |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Madsskardveien ost for Glomma | 61.452, 11.146 | 61.45283, 11.14854 | service / - | 163 m mot 236 grader, +20.1 m (163 m @ 236°) | 1.0 | 0.0 | 4.2 | 4 | 20.1 | 4.9 | 4409 | 322 | 2572 | 10.6 / 14.1 | 0.43 | 0.15 | 23.3 | True | - |
| 2 | Jernvinneveien ost for Glomma | 61.436, 11.137 | 61.43338, 11.13653 | track / Circular hike | 291 m mot 5 grader, +9.2 m (291 m @ 5°) | 0.84 | 0.0 | 0.0 | 4 | 9.2 | 11.2 | 2591 | 200 | 2029 | 10.9 / 16.6 | 0.33 | 0.0 | 53.4 | True | - |
| 3 | Ole Evenstads vei ost for Glomma | 61.434, 11.088 | 61.43136, 11.09041 | service / - | 320 m mot 336 grader, +18.8 m (320 m @ 336°) | 0.76 | 0.0 | 0.0 | 4 | 18.8 | 7.8 | 537 | 1101 | 271 | 12.6 / 16.8 | 0.54 | 0.33 | 28.6 | True | - |
| 4 | Ole Evenstads vei ost for Glomma | 61.429, 11.098 | 61.42917, 11.09892 | service / - | 53 m mot 249 grader, +10.5 m (53 m @ 249°) | 0.64 | 0.0 | 0.0 | 4 | 10.5 | 5.9 | 425 | 1391 | 315 | 16.3 / 19.5 | 0.83 | 0.05 | 29.2 | True | - |
| 5 | Jernvinneveien ost for Glomma | 61.439, 11.125 | 61.43927, 11.12846 | track / - | 186 m mot 261 grader, +71.2 m (186 m @ 261°) | 0.75 | 0.0 | 0.0 | 4 | 71.2 | 13.8 | 2188 | 761 | 1723 | 13.6 / 18.3 | 0.53 | 0.3 | 54.8 | True | - |
| 6 | Madsskardveien ost for Glomma | 61.445, 11.119 | 61.44879, 11.12543 | unclassified / Madsskardveien | 541 m mot 219 grader, +8.3 m (541 m @ 219°) | 0.84 | 0.0 | 0.0 | 4 | 8.3 | 4.5 | 2461 | 80 | 1591 | 8.7 / 15.3 | 0.25 | 0.05 | 19.8 | True | - |
| 7 | Madsskardveien ost for Glomma | 61.474, 11.109 | 61.48047, 11.11417 | track / - | 769 m mot 201 grader, +59.3 m (769 m @ 201°) | 0.73 | 0.0 | 4.2 | 4 | 59.3 | 11.0 | 3062 | 601 | 1540 | 15.6 / 17.9 | 0.74 | 0.03 | 40.8 | True | - |
| 8 | Gålaveien vest/nord | 61.463, 10.96 | 61.46819, 10.96282 | unclassified / Gålaveien | 595 m mot 195 grader, +70.7 m (595 m @ 195°) | 0.88 | 1.15 | 1.3 | 3 | 70.7 | 20.2 |  | 794 | 907 | 13.0 / 18.0 | 0.57 | 0.07 | 89.2 | True | - |
| 9 | Madsskardveien ost for Glomma | 61.464, 11.084 | 61.46565, 11.09156 | unclassified / Madsskardveien | 441 m mot 245 grader, +61.8 m (441 m @ 245°) | 0.76 | 0.0 | 4.2 | 4 | 61.8 | 13.6 | 2012 | 537 | 677 | 11.3 / 15.7 | 0.44 | 0.04 | 63.8 | True | - |
| 10 | Birkebeinerveien vest/nord **(removed from mirror 25.09)** | 61.447, 10.965 | 61.44648, 10.96392 | service / - | 82 m mot 45 grader, +28.7 m (82 m @ 45°) | 0.77 | 1.15 | 0.0 | 3 | 28.7 | 9.2 | 4491 | 360 | 290 | 12.1 / 15.1 | 0.5 | 0.14 | 32.9 | True | - |
| 11 | Madsskardveien ost for Glomma | 61.473, 11.096 | 61.47387, 11.08792 | unclassified / Madsskardveien | 439 m mot 103 grader, +74.2 m (439 m @ 103°) | 0.84 | 0.0 | 4.2 | 4 | 74.2 | 12.0 | 2519 | 160 | 1416 | 7.5 / 15.1 | 0.16 | 0.23 | 49.7 | True | - |
| 12 | track ost for Glomma | 61.426, 11.127 | 61.42513, 11.12809 | track / - | 113 m mot 329 grader, +18.4 m (113 m @ 329°) | 0.62 | 0.0 | 0.0 | 4 | 18.4 | 11.4 | 1043 | 256 | 1281 | 9.1 / 24.0 | 0.38 | 0.03 | 49.6 | True | - |
| 13 | Gålaveien vest/nord | 61.471, 10.98 | 61.47101, 10.98003 | service / - | 2 m mot 244 grader, +60.3 m (2 m @ 244°) | 0.81 | 1.15 | 1.3 | 3 | 60.3 | 18.6 | 3047 | 569 | 507 | 6.5 / 19.8 | 0.44 | 0.47 | 62.1 | True | - |
| 14 | Gålaveien vest/nord | 61.473, 10.969 | 61.47392, 10.96854 | track / - | 105 m mot 167 grader, +57.8 m (105 m @ 167°) | 0.99 | 1.15 | 1.3 | 3 | 57.8 | 20.0 | 3640 | 160 | 334 | 5.6 / 18.5 | 0.29 | 0.36 | 71.7 | True | - |
| 15 | Madsskardveien ost for Glomma | 61.453, 11.133 | 61.44849, 11.13235 | unclassified / Madsskardveien | 502 m mot 4 grader, +60.6 m (502 m @ 4°) | 0.89 | 0.0 | 4.2 | 4 | 60.6 | 8.4 | 4363 | 468 | 1874 | 4.9 / 12.2 | 0.09 | 0.29 | 33.6 | True | - |
| 16 | unclassified vest/nord | 61.426, 11.012 | 61.42573, 11.01313 | track / - | 67 m mot 297 grader, +79.9 m (67 m @ 297°) | 0.69 | 1.15 | 0.0 | 3 | 79.9 | 19.4 | 3312 | 1434 | 752 | 6.4 / 16.7 | 0.26 | 0.33 | 66.0 | True | - |
| 17 | unclassified ost for Glomma | 61.381, 11.121 | 61.38207, 11.12275 | track / - | 151 m mot 218 grader, +42.7 m (151 m @ 218°) | 0.68 | 2.23 | 0.0 | 5 | 42.7 | 11.1 |  | 144 | 1333 | 13.7 / 17.1 | 0.68 | 0.01 | 50.5 | True | - |
| 18 | Birkebeinerveien vest/nord **(removed from mirror 25.09)** | 61.453, 10.952 | 61.45271, 10.94002 | unclassified / Eldådalsveien | 636 m mot 87 grader, +1.9 m (636 m @ 87°) | 0.72 | 1.15 | 1.3 | 3 | 1.9 | 16.8 | 4981 | 1181 | 712 | 9.5 / 15.7 | 0.25 | 0.05 | 70.2 | True | - |
| 19 | Myklebysæterveien vest/nord | 61.405, 11.032 | 61.40683, 11.0399 | service / - | 466 m mot 244 grader, +71.7 m (466 m @ 244°) | 0.74 | 1.58 | 0.0 | 4 | 71.7 | 7.0 | 3821 | 566 | 887 | 6.9 / 16.1 | 0.23 | 0.42 | 25.9 | True | - |
| 20 | Birkebeinerveien vest/nord **(removed from mirror 25.09)** | 61.429, 10.95 | 61.42973, 10.94 | tertiary / Birkebeinerveien | 537 m mot 99 grader, +74.1 m (537 m @ 99°) | 0.65 | 1.79 | 0.0 | 17 | 74.1 | 20.4 | 5857 | 1722 | 2136 | 12.2 / 18.5 | 0.52 | 0.03 | 83.2 | True | - |
| 21 | Søstugutua vest/nord | 61.468, 11.033 | 61.46684, 11.03346 | track / - | 131 m mot 349 grader, +38.2 m (131 m @ 349°) | 0.77 | 1.15 | 4.2 | 3 | 38.2 | 16.6 | 488 | 688 | 125 | 7.9 / 22.3 | 0.3 | 0.15 | 55.7 | True | - |
| 22 | Ole Evenstads vei vest/nord | 61.456, 11.063 | 61.45669, 11.06686 | service / - | 218 m mot 249 grader, +20.9 m (218 m @ 249°) | 0.84 | 0.0 | 4.2 | 4 | 20.9 | 11.9 | 699 | 342 | 645 | 4.6 / 15.0 | 0.04 | 0.12 | 54.5 | True | - |
| 23 | Myklebysæterveien vest/nord | 61.384, 11.008 | 61.38457, 11.01799 | service / Myklebysæterveien | 535 m mot 263 grader, +35.3 m (535 m @ 263°) | 0.74 | 1.58 | 0.0 | 4 | 35.3 | 4.8 | 6392 | 1281 | 529 | 7.0 / 13.0 | 0.18 | 0.18 | 20.0 | True | - |
| 24 | Myklebysæterveien vest/nord | 61.393, 11.049 | 61.39603, 11.04919 | track / - | 337 m mot 182 grader, +3.2 m (337 m @ 182°) | 0.76 | 1.58 | 0.0 | 4 | 3.2 | 10.4 | 4271 | 662 | 1721 | 7.7 / 13.8 | 0.13 | 0.04 | 38.1 | True | - |
| 25 | Myklebysæterveien vest/nord | 61.395, 11.034 | 61.39635, 11.04069 | unclassified / Myklebysæterveien | 386 m mot 247 grader, +18.0 m (386 m @ 247°) | 0.74 | 1.58 | 0.0 | 4 | 18.0 | 2.1 | 4555 | 305 | 932 | 7.6 / 13.8 | 0.16 | 0.14 | 9.3 | True | - |
| 26 | Madsskardveien ost for Glomma | 61.463, 11.103 | 61.46265, 11.09281 | unclassified / Madsskardveien | 542 m mot 86 grader, +68.8 m (542 m @ 86°) | 0.76 | 0.0 | 4.2 | 4 | 68.8 | 14.7 | 2800 | 681 | 904 | 3.3 / 14.1 | 0.17 | 0.49 | 67.3 | True | - |
| 27 | unclassified ost for Glomma | 61.473, 11.139 | 61.4778, 11.12739 | track / - | 814 m mot 131 grader, +11.3 m (814 m @ 131°) | 0.76 | 0.0 | 4.2 | 4 | 11.3 | 4.3 | 4567 | 768 | 2734 | 5.8 / 13.1 | 0.16 | 0.34 | 24.8 | True | - |
| 28 | unclassified ost for Glomma | 61.376, 11.143 | 61.37958, 11.13591 | unclassified / - | 548 m mot 137 grader, +3.8 m (548 m @ 137°) | 0.79 | 2.23 | 0.0 | 5 | 3.8 | 13.9 | 1649 | 283 | 2085 | 7.8 / 15.8 | 0.23 | 0.37 | 45.6 | True | - |
| 29 | Myklebysæterveien vest/nord | 61.402, 11.054 | 61.40205, 11.05075 | track / - | 173 m mot 92 grader, +15.7 m (173 m @ 92°) | 0.71 | 2.23 | 0.0 | 5 | 15.7 | 14.5 | 3273 | 283 | 1318 | 10.8 / 11.8 | 0.35 | 0.09 | 58.8 | True | - |
| 30 | Storelvdalsveien vest/nord | 61.488, 11.045 | 61.48827, 11.04454 | service / - | 39 m mot 141 grader, +62.4 m (39 m @ 141°) | 0.72 | 1.98 | 4.2 | 4 | 62.4 | 15.3 |  | 640 | 184 | 11.7 / 21.2 | 0.49 | 0.27 | 65.8 | True | - |
| 31 | Myklebysæterveien vest/nord | 61.377, 11.02 | 61.3774, 11.01686 | track / - | 173 m mot 105 grader, +35.9 m (173 m @ 105°) | 0.69 | 1.58 | 0.0 | 4 | 35.9 | 6.4 | 6576 | 1771 | 624 | 7.1 / 10.7 | 0.06 | 0.03 | 20.6 | True | - |
| 32 | unclassified ost for Glomma | 61.387, 11.14 | 61.3861, 11.14462 | unclassified / - | 265 m mot 292 grader, +3.0 m (265 m @ 292°) | 0.61 | 2.23 | 0.0 | 5 | 3.0 | 7.4 | 821 | 761 | 2529 | 11.3 / 18.5 | 0.46 | 0.25 | 37.9 | True | - |
| 33 | unclassified ost for Glomma | 61.367, 11.087 | 61.3666, 11.08714 | track / - | 46 m mot 351 grader, +8.9 m (46 m @ 351°) | 0.63 | 1.91 | 0.0 | 5 | 8.9 | 12.7 |  | 544 | 737 | 6.4 / 14.7 | 0.26 | 0.31 | 60.8 | True | - |
| 34 | Gålaveien vest/nord | 61.463, 10.976 | 61.46118, 10.97655 | track / - | 204 m mot 352 grader, +8.3 m (204 m @ 352°) | 0.88 | 1.15 | 1.3 | 3 | 8.3 | 13.3 |  | 716 | 491 | 1.6 / 21.2 | 0.27 | 0.53 | 54.3 | True | - |
| 35 | Ole Evenstads vei vest/nord | 61.473, 11.05 | 61.47192, 11.04179 | secondary / Ole Evenstads vei | 452 m mot 75 grader, +78.4 m (452 m @ 75°) | 0.84 | 0.0 | 4.2 | 4 | 78.4 | 17.7 | 573 | 200 | 347 | 1.0 / 16.7 | 0.13 | 0.65 | 66.7 | True | - |
| 36 | Myklebysæterveien vest/nord | 61.389, 11.015 | 61.39203, 11.01064 | unclassified / - | 409 m mot 145 grader, +18.2 m (409 m @ 145°) | 0.71 | 1.58 | 0.0 | 4 | 18.2 | 6.9 | 5810 | 708 | 503 | 4.6 / 11.9 | 0.0 | 0.14 | 26.6 | True | - |
| 37 | Myklebysæterveien vest/nord | 61.348, 10.99 | 61.34785, 10.99014 | service / - | 19 m mot 336 grader, +30.8 m (19 m @ 336°) | 0.76 | 2.43 | 0.0 | 4 | 30.8 | 6.6 | 9775 | 5338 | 3760 | 4.7 / 12.3 | 0.11 | 0.38 | 23.9 | True | - |
| 38 | Birkebeinerveien vest/nord **(removed from mirror 25.09)** | 61.44, 10.951 | 61.44225, 10.947 | track / - | 327 m mot 140 grader, +39.6 m (327 m @ 140°) | 0.66 | 1.15 | 0.0 | 3 | 39.6 | 15.9 | 5424 | 1246 | 969 | 1.0 / 14.0 | 0.2 | 0.62 | 57.3 | True | - |
| 39 | Storelvdalsveien vest/nord | 61.515, 11.045 | 61.51455, 11.04383 | service / - | 80 m mot 51 grader, +39.3 m (80 m @ 51°) | 0.66 | 1.98 | 4.2 | 4 | 39.3 | 15.5 | 1161 | 362 | 3170 | 3.2 / 15.8 | 0.23 | 0.49 | 49.6 | True | - |
| 40 | Myklebysæterveien vest/nord | 61.422, 11.057 | 61.42246, 11.05432 | service / - | 151 m mot 110 grader, +15.2 m (151 m @ 110°) | 0.68 | 2.23 | 0.0 | 5 | 15.2 | 7.2 | 1562 | 362 | 146 | 2.1 / 17.0 | 0.25 | 0.58 | 40.9 | True | - |

Google Maps routes (verbatim, parking points in rank order):
- 1-10: https://www.google.com/maps/dir/61.45283,11.14854/61.43338,11.13653/61.43136,11.09041/61.42917,11.09892/61.43927,11.12846/61.44879,11.12543/61.48047,11.11417/61.46819,10.96282/61.46565,11.09156/61.44648,10.96392
- 11-20: https://www.google.com/maps/dir/61.47387,11.08792/61.42513,11.12809/61.47101,10.98003/61.47392,10.96854/61.44849,11.13235/61.42573,11.01313/61.38207,11.12275/61.45271,10.94002/61.40683,11.0399/61.42973,10.94
- 21-30: https://www.google.com/maps/dir/61.46684,11.03346/61.45669,11.06686/61.38457,11.01799/61.39603,11.04919/61.39635,11.04069/61.46265,11.09281/61.4778,11.12739/61.37958,11.13591/61.40205,11.05075/61.48827,11.04454
- 31-40: https://www.google.com/maps/dir/61.3774,11.01686/61.3861,11.14462/61.3666,11.08714/61.46118,10.97655/61.47192,11.04179/61.39203,11.01064/61.34785,10.99014/61.44225,10.947/61.51455,11.04383/61.42246,11.05432

(The URLs still contain the removed stops 10, 18, 20 and 38.)

Radar check by default.no: «radar … stopp 40, vate []». At 24.09 18:35 none of the 40 stops had rain (`defaultno_mer.json:405-418`).

Birds near stops (`defaultno_mer.json` → fugl.per_stopp; national totals n_orr 33 818, n_stor 13 185, orrfugl in 2026: 442). **Which plan version these ranks refer to is not stated.** The ranks do not obviously match plan.json.

| stop rank | orrfugl obs ≤1500 m | orrfugl birds | storfugl obs ≤1500 m | nearest orrfugl m |
|---|---|---|---|---|
| 1 | 8 | 14 | 6 | 340 |
| 2 | 0 | 0 | 1 | 1955 |
| 3 | 2 | 3 | 2 | 311 |
| 5 | 3 | 8 | 0 | 1157 |
| 7 | 5 | 10 | 5 | 154 |
| 8 | 1 | 1 | 1 | 916 |
| 9 | 0 | 0 | 1 | 1572 |
| 10 | 1 | 1 | 0 | 1147 |
| 11 | 1 | 2 | 0 | 967 |
| 13 | 1 | 1 | 1 | 1288 |
| 14 | 0 | 0 | 1 | 2261 |
| 16 | 2 | 2 | 2 | 892 |
| 18 | 2 | 2 | 2 | 863 |

---

## 9. Gå-soner (walk zones), `gasoner.json`

Band 200–700 m from road. Six ≈24-km boxes:

| rank | centre | bounds | road km in box | forest share 200–700 m from road (skog) | uphill share (opp) | candidate area km² | dry share (tort) |
|---|---|---|---|---|---|---|---|
| 1 | 61.2, 11.8 | [[61.0919,11.5756],[61.3081,12.0244]] | 723.4 | 0.416 | 0.533 | 127.9 | 0.76 |
| 2 | 60.95, 11.1 | [[60.8419,10.8774],[61.0581,11.3226]] | 1394.7 | 0.315 | 0.433 | 78.6 | 0.673 |
| 3 | 62.2, 11.4 | [[62.0919,11.1682],[62.3081,11.6318]] | 197.3 | 0.075 | 0.74 | 32.0 | 1.0 |
| 4 | 62.45, 11.0 | [[62.3419,10.7663],[62.5581,11.2337]] | 839.3 | 0.282 | 0.6 | 97.4 | 1.0 |
| 5 | 61.3, 11.2 | [[61.1919,10.9749],[61.4081,11.4251]] | 761.4 | 0.332 | 0.467 | 89.2 | 0.8 |
| 6 | 63.65, 12.2 | [[63.5419,11.9564],[63.7581,12.4436]] | 182.4 | 0.042 | 0.827 | 19.8 | 1.0 |

`defaultno_mer.json` repeats ranks 1–6 with the same vei_km, skog and km2 values.

---

## 10. Rejected areas (15), verbatim

| name | lat, lon | why (verbatim) | img |
|---|---|---|---|
| Froland (Agder) | 58.6, 8.7 | «Ingen av de tre flyene hun så var over 10° over horisonten. Feil landsdel for innflygingen til OSL.» | - |
| Telemark | 59.45, 8.9 | «Flyene hun så sto 5–15° over horisonten. Avvist på fly og regn (regnet mens kameraet var tørt).» | - |
| Nøtterøy / Revetal / Andebu (Vestfold) | 59.3, 10.2 | «Under ingen av flyhendelsene sto et fly høyt der. Regnet søndag/mandag mens glasset var tørt.» | img/60_vestfold_check.png |
| Storsjøen (Rendalen) | 61.5786, 11.3084 | «Innflygingen går vest for sjøen; 20:32/20:34-flyene sto 25–35° der mot 64–72° ved Evenstad. Svakere, ikke utelukket.» | - |
| Rendalen 61.30/11.63 | 61.3045, 11.6283 | «Flyene sto 15–25° over horisonten. Mye fugl, men ligger i kanten av Regionfelt Østlandet (skytefelt).» | - |
| Trysil | 61.31, 12.27 | «Flyene hun så sto under 12° over horisonten. Blåbær-land, ikke tyttebær. 5.9 mm regn siden søndag mens glasset var tørt.» | - |
| Finnskogen 60.70/12.40 | 60.7, 12.4 | «Alle tre flyene sto 3–4° over horisonten, 106–120 km unna. Høyeste fly i vinduene 9–12° (Helsingfors-fly).» | img/67_check_60p70_12p40.png |
| Kvam / Vinstra | 61.68746, 10.14689 | «Fly 9° / 11° / 11°. Vest for Østerdalen, utenfor innflygingen. Koordinaten er et jorde.» | img/68_four_points.png |
| Gausdal | 61.35129, 10.08446 | «Fly 10° / 16° / 18°. Feiler alle tre hendelsene.» | img/68_four_points.png |
| Øyer | 61.24385, 10.49094 | «Fly 19° / 12° / 12°. 34 høye dagfly passerte uten INGEN FLY-reaksjon (luftveien Oslo–Trondheim).» | img/68_four_points.png |
| Atna | 61.7255, 10.9594 | «20:32 og 20:34 stemmer (78°), men 21:29-flyet passerte Atna 2,5 min før hun pekte (da 9°). 22 høye dagfly uoppdaget.» | img/68_four_points.png |
| Lesja / Dovre 61.75/8.40 | 61.75, 8.4 | «Lå som nr. 1 i en utdatert fusjonsvariant (22.09, uten fly). Ingen av flyene hun så var i nærheten.» | - |
| Elverum sentrum / Terningmoen | 60.85, 11.5 | «Selve cellen ligger i Terningmoen skytefelt. Området rundt (Elverum–Solør) er fortsatt et B-område: flyene 28–49°, men 22–34 høye dagfly uoppdaget mot 4 ved Evenstad.» | - |
| 61.4307, 11.0483 (sjekket 23.09) | 61.4307, 11.0483 | «Sjekket på bakken natt til 23.09: bolighus 7 m unna, ikke boksen.» | - |
| 61.4495, 10.9763 (bom) | 61.4495, 10.9763 | «Bom på veien 23.09, bare sett fra veien. Ikke ferdig sjekket.» | - |

The `img` paths are relative to default.no and are not mirrored locally.

---

## 11. Field notes: pins (13 original; 10 in mirror)

| lat, lon | note (verbatim) | in mirror? |
|---|---|---|
| 61.4452, 10.9756 | «BOM / privat vei (23.09 ca 00:30) - Birkebeinerveien-avkjoring mot 61.4495,10.9752. Ga forbi bommen til fots, 500 m» | **REMOVED 25.09** |
| 61.4495, 10.9752 | «privat vei - pin Birkebeinerveien-ryggen, ikke sjekket til fots» | **REMOVED 25.09** |
| 61.4307, 11.0483 | «privat vei - sjaforen er her NA (23.09 00:40), serviceveg av Storelvdalsveien, 410 m gange» | yes |
| 61.376, 11.143 | «PLAN 1 Evenstad ost E1: parker 61.3796,11.1359 (skogsbilvei fra Hortaveien), ga 550 m SO (137 grader), flatt +4 m, furu, hogst 280 m» | yes |
| 61.382, 11.125 | «PLAN 2 Evenstad ost E2: traktorvei 61.3818,11.1244, 40 m NO» | yes |
| 61.387, 11.14 | «PLAN 3 Evenstad ost E4: parker 61.3861,11.1446, ga 265 m VNV (292 grader)» | yes |
| 61.372, 11.094 | «PLAN 4 Evenstad ost E3: traktorvei 61.3711,11.0934, 100 m N» | yes |
| 61.3954, 11.0343 | «PLAN 5 Snipperslaatten A: parker 61.3966,11.0405 Myklebysaeterveien, ga 355 m VSV (248), flatt» | yes |
| 61.4732, 10.9687 | «PLAN 6 Galaveien-ryggen: parker 61.4692,10.9676, ga 450 m N (8), +58 m» | yes |
| 61.4495, 10.9763 | «PLAN 7 Birkebeinerveien pin: bom 61.4452,10.9756, ga 500 m NNO forbi bommen (sjekket bare fra veien)» | **REMOVED 25.09** |
| 61.4628, 10.9755 | «PLAN 8 Galaveien sor: parker 61.4673,10.9753, ga 500 m S» | yes |
| 61.4682, 11.0325 | «PLAN 9 Sostugutua: parker 61.4653,11.0309, ga 335 m N (14)» | yes |
| 61.25, 11.0 | «PLAN 10 Elverum-stripa 61.15-61.30/11.0: bare hvis 1-9 er tomme; ingen konkrete steder enna» | yes |

"PLAN 1–10" in these pins is an **older plan (23.09)**, not plan.json: for example «PLAN 1 Evenstad ost E1» at 61.376, 11.143 is plan.json stop 28. «PLAN 10 Elverum-stripa 61.15-61.30/11.0: bare hvis 1-9 er tomme; ingen konkrete steder enna».

---

## 12. Flights: what default.no says she reacted to

### 12.1 Observations (`defaultno_mer.json` → observasjoner.fly and lost, lines 3-49)

| stream time | until | loudest sound | min elevation used | max altitude | default.no text (verbatim) | aircraft checked / cells passing |
|---|---|---|---|---|---|---|
| 2026-09-21 21:29:40 | 21:34:00 | 21:33:20 | 25° | n/a | «Hun peker opp 21:29:38, skriver «FLY» 21:30:12, og lyden er sterkest 21:33:20.» | 125 / 948 (utc field 19:31:28Z) |
| 2026-09-22 20:32:40 | n/a | n/a | 25° | 28 000 ft | «Første av to fly inn mot Gardermoen ned Østerdalen (SAS39A). Chatten skrev «FLYY». Svakere enn 20:35. 90–96 % skyer, så bare fly under 28 000 fot teller.» | 140 / 403 (utc 18:32:18Z = stream − 22 s) |
| 2026-09-22 20:34:40 | n/a | n/a | 25° | 28 000 ft | «Hun peker, setter seg opp og følger flyet sørover (NOZ55J, 21 000 fot). Chatten: «Fly blinker med farger». Overskyet, så ikke en satellitt.» | 144 / 391 (utc 18:34:18Z = stream − 22 s) |

For the 22.09 events the `utc` field is exactly the stream time minus 22 s, which is default.no's stream delay. mk_bevis confirms: «default.no målte ca. 22 s» (`…/claude-2026-09-25/README.md:48`). For 21.09 the utc is 19:31:28Z, i.e. **1 min 48 s after** the pointing time, and is unexplained (section 20).

### 12.2 ADS-B around the three events (`flyhendelser.json`)

Events:
- «21.09 21:29»: n = 69, window 21:28:40–21:34:00
- «22.09 20:32»: n = 89, window 20:31:10–20:34:10
- «22.09 20:34»: n = 95, window 20:33:10–20:36:10

That is 253 aircraft in total. 228 have `pek` (position at reaction). 62 have `lyd` (≈35 s before loudest sound), all in the 21.09 event.

For NOZ9EG, `pek` corresponds to ≈19:29:27Z and `lyd` to ≈19:32:24Z by trace matching, i.e. real time 21:29:27 and 21:32:24.

Aircraft nearest to 61.45/11.10 at the reaction moment. Elevation is from 61.45/11.10, flat earth, my calculation:

| event | callsign (k) | type | route | operator | alt min–max ft | kts | hdg | pek (lat, lon, ft) | dist pek→61.45/11.10 km | elev from 61.45/11.10 ° | lyd (lat, lon, ft) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 21.09 21:29 | @@@@@@@@ | B738 | - | - | 10725–31125 | 468 | 182 | [61.2916, 10.902, 24775] | 20.5 | 20.2 | [60.91, 10.8676, 18325] |
| 21.09 21:29 | NOZ56U | B738 | OSL-BOO | Norwegian Air Shuttle AOC AS | 11950–32850 | 364 | 5 | [60.745, 11.2231, 20430] | 78.7 | 4.5 | [61.0658, 11.288, 27647] |
| 21.09 21:29 | NOZ68L | B738 | OSL-EVE | Norwegian Air Shuttle AOC AS | 36975–37025 | 362 | 6 | [62.2929, 11.5522, 37000] | 96.7 | 6.7 | [62.5944, 11.6225, 37000] |
| 21.09 21:29 | WIF149 | DH8A | OSL-SOG | Wideroe | 16000–16025 | 215 | 300 | [60.8292, 8.9856, 16002] | 132.8 | 2.1 | [60.9242, 8.6514, 16000] |
| 21.09 21:29 | WIF1HX | DH8A | HOV-OSL | Wideroe | 5175–20275 | 295 | 119 | [60.3806, 9.9496, 15400] | 134.2 | 2.0 | [60.2597, 10.3893, 9565] |
| 21.09 21:29 | AKK2 | BE20 | - | - | 13450–25575 | 259 | 345 | [62.6312, 11.9856, 22382] | 139.2 | 2.8 | [62.8455, 11.8612, 17727] |
| 22.09 20:32 | SAS39A | A20N | BOO-OSL | Scandinavian Airlines System | 18950–33175 | 413 | 179 | [61.4831, 11.0543, 25750] | 4.4 | 60.7 | - |
| 22.09 20:32 | NOZ55J | B738 | BOO-OSL | Norwegian Air Shuttle AOC AS | 21150–37550 | 428 | 178 | [61.775, 10.961, 27950] | 36.9 | 13.0 | - |
| 22.09 20:32 | NOZ436 | B738 | OSL-MOL | Norwegian Air Shuttle AOC AS | 23275–33850 | 449 | 329 | [60.9481, 9.8983, 28430] | 85.2 | 5.8 | - |
| 22.09 20:32 | NOZ2KB | B738 | OSL-BOO | Norwegian Air Shuttle AOC AS | 13200–27175 | 392 | 2 | [60.6123, 11.3505, 21435] | 94.1 | 4.0 | - |
| 22.09 20:32 | SCO759R | CL35 | - | - | 3675–8325 | 258 | 55 | [60.4207, 11.0052, 5380] | 114.6 | 0.8 | - |
| 22.09 20:32 | SAS389 | A20N | TRD-OSL | Scandinavian Airlines System | 1500–6575 | 227 | 182 | [60.4142, 11.1986, 3675] | 115.3 | 0.6 | - |
| 22.09 20:34 | NOZ55J | B738 | BOO-OSL | Norwegian Air Shuttle AOC AS | 16400–30800 | 418 | 177 | [61.5448, 10.984, 23175] | 12.2 | 30.1 | - |
| 22.09 20:34 | SAS39A | A20N | BOO-OSL | Scandinavian Airlines System | 12100–28250 | 402 | 176 | [61.252, 11.0614, 20885] | 22.1 | 16.1 | - |
| 22.09 20:34 | NOZ2KB | B738 | OSL-BOO | Norwegian Air Shuttle AOC AS | 18975–31550 | 424 | 2 | [60.8435, 11.3716, 25795] | 69.0 | 6.5 | - |
| 22.09 20:34 | NOZ436 | B738 | OSL-MOL | Norwegian Air Shuttle AOC AS | 26150–36000 | 448 | 329 | [61.1659, 9.6357, 32215] | 84.3 | 6.6 | - |
| 22.09 20:34 | SCO759R | CL35 | - | - | 1450–6325 | 213 | 190 | [60.4318, 11.1983, 4415] | 113.3 | 0.7 | - |
| 22.09 20:34 | NJE759L | C56X | - | - | 3650–8475 | 253 | 77 | [60.3956, 10.9644, 4070] | 117.5 | 0.6 | - |

Reading (c):
- On **22.09 20:32**, SAS39A (BOO-OSL, A20N) was almost overhead 61.45/11.10: pek 61.4831, 11.0543 at 25 750 ft, which is 4.4 km away at ≈61° elevation.
- On **20:34**, NOZ55J (BOO-OSL, B738) was at 61.5448, 10.984 at 23 175 ft, 12.2 km away at ≈30°, while SAS39A was 22 km south at ≈16°.
- On **21.09 21:29**, the nearest aircraft was **NOZ9EG** (callsign blank as «@@@@@@@@» in the file; identity verified against `trace_4791ac.json`). It was southbound over Ringsakfjellet: pek 61.2916, 10.902 at 24 775 ft, 20.5 km from 61.45/11.10 at ≈20°. NOZ56U (OSL-BOO) was northbound over Hamar/Løten: pek 60.745, 11.2231 at 20 430 ft, 79 km away.
- mkekeoooo's report (p. 6) notes that on 22.09 «Er det NOZ55J hun så, favoriseres områdene nord (Gålaveien, Birkebeinerveien, Messelt). Er det SAS39A, favoriseres sør (Myklebysætra, H2 og punkt 7).» [c]

### 12.3 Caveats on the plane evidence (quoted)

- **Shooting star**: «kl. 21:27:42 signaliserte hun et stjerneskudd, og kl. 21:29:10 ba chatten henne peke dit. Pekingen 21:29:38–53 kan altså gjelde stjerneskuddet og ikke et fly.» (mk_bevis README:62, marked «[verifisert i default.no osint_notes]»). This is secondary, but it undermines event 1.
- **Pointing gesture**: «En arm nesten loddrett i bildet er ikke en måling av flyets høydevinkel» (mkekeoooo README:13, a retraction). default.no's 25° threshold is an assumption.
- mk_bevis finds that with a 22 s delay **no candidate** has a plane near "straight up" at 21:29:38. For example Myklebysæterveien vest sees NOZ9EG at 33° and Løten sees NOZ56U at 28° (`fly_2109_resultat.txt`).

---

## 13. «INGEN FLY» rarity (`sjelden.json`)

Premise (a, quoted): Anja wrote «INGEN FLY» at 18:31 on 21.09 (stream).

Model:
- It counts daytime passes of 1 255 aircraft between 07:00 and 18:31 that reached ≥40° elevation (`dag`).
- It also requires that the 21:30 plane was high enough (`e2130` = max elevation of the 21:30 plane; `e2028` = max elevation of a 20:28 plane).
- `r = exp(−dag/3)`.

Top 40 cells (the magnus map numbers the first 12):

| # | lat, lon | r | dag (planes ≥40° 07:00–18:31) | max elev 21:30 plane ° | max elev 20:28 plane ° |
|---|---|---|---|---|---|
| 1 | 61.3, 11.0 | 0.513 | 2 | 55.4 | 22.0 |
| 2 | 61.55, 7.6 | 0.368 | 3 | 29.9 | 5.2 |
| 3 | 60.9, 8.9 | 0.368 | 3 | 47.5 | 14.9 |
| 4 | 64.7, 11.4 | 0.368 | 3 | 46.8 | 10.0 |
| 5 | 60.5, 7.9 | 0.368 | 3 | 35.8 | 4.4 |
| 6 | 64.75, 11.4 | 0.368 | 3 | 45.3 | 9.5 |
| 7 | 64.75, 11.3 | 0.368 | 3 | 35.3 | 9.1 |
| 8 | 61.05, 11.0 | 0.368 | 3 | 45.0 | 14.0 |
| 9 | 60.5, 8.1 | 0.368 | 3 | 31.3 | 4.8 |
| 10 | 61.25, 11.0 | 0.368 | 3 | 53.5 | 21.6 |
| 11 | 61.2, 11.0 | 0.368 | 3 | 51.5 | 20.2 |
| 12 | 61.45, 11.0 | 0.368 | 3 | 38.1 | 22.5 |
| 13 | 61.1, 11.0 | 0.368 | 3 | 47.3 | 16.0 |
| 14 | 61.15, 11.0 | 0.368 | 3 | 49.2 | 18.1 |
| 15 | 60.5, 8.0 | 0.264 | 4 | 35.2 | 4.6 |
| 16 | 61.35, 11.0 | 0.264 | 4 | 57.7 | 22.2 |
| 17 | 61.4, 11.0 | 0.264 | 4 | 53.3 | 22.4 |
| 18 | 61.45, 11.1 | 0.264 | 4 | 30.4 | 28.8 |
| 19 | 61.0, 8.7 | 0.264 | 4 | 29.7 | 12.0 |
| 20 | 61.5, 8.7 | 0.264 | 4 | 25.3 | 6.8 |
| 21 | 61.5, 11.0 | 0.264 | 4 | 27.5 | 22.7 |
| 22 | 60.95, 8.9 | 0.264 | 4 | 27.7 | 16.1 |
| 23 | 60.95, 8.8 | 0.264 | 4 | 35.2 | 13.6 |
| 24 | 61.55, 8.6 | 0.264 | 4 | 25.2 | 6.1 |
| 25 | 60.95, 8.7 | 0.264 | 4 | 51.9 | 11.7 |
| 26 | 60.55, 6.7 | 0.264 | 4 | 25.6 | 6.5 |
| 27 | 60.9, 8.5 | 0.264 | 4 | 36.2 | 8.9 |
| 28 | 60.5, 7.7 | 0.189 | 5 | 36.4 | 4.6 |
| 29 | 60.5, 7.8 | 0.189 | 5 | 36.0 | 4.5 |
| 30 | 61.35, 11.1 | 0.189 | 5 | 37.4 | 28.8 |
| 31 | 61.4, 11.1 | 0.189 | 5 | 36.5 | 28.9 |
| 32 | 61.5, 7.6 | 0.189 | 5 | 25.1 | 4.9 |
| 33 | 61.45, 8.8 | 0.189 | 5 | 25.3 | 7.7 |
| 34 | 60.95, 11.0 | 0.189 | 5 | 40.3 | 11.0 |
| 35 | 61.6, 7.7 | 0.189 | 5 | 46.2 | 5.6 |
| 36 | 60.5, 8.2 | 0.189 | 5 | 26.1 | 5.0 |
| 37 | 60.95, 8.5 | 0.189 | 5 | 67.2 | 9.1 |
| 38 | 60.9, 11.0 | 0.189 | 5 | 37.6 | 9.8 |
| 39 | 60.9, 9.0 | 0.189 | 5 | 34.2 | 17.6 |
| 40 | 61.0, 11.0 | 0.189 | 5 | 42.6 | 12.3 |

61.45/11.10 is #18 (dag 4). The strip at 11.0 E between 61.05 and 61.50 N (Rena–Åsta–Evenstad west bank) has dag 2–4 and a 21:30 plane at 27–58°.

---

## 14. Aircraft-sound match (`flylyd.json`, `defaultno_mer.json` flylyd)

Best cell **60.0 N, 9.9 E** (Sokna/Hønefoss): score 3.156, mean slant range 33.13 km, 33 passes, 21 heard, 1 loud pass. The grid was updated 24.09 18:31:31. The layer text says «Lyden kan være spilt av på nytt, så dette er usikkert».

22 sound events. I inferred that `km` is measured to the best cell: the helicopter LNOZD (R44) lyd point 59.7808, 10.2514 is 31.2 km from 60.0/9.9, which matches.

| real time (CEST) | hand label | nearest aircraft | dist km (to best cell 60.0/9.9, inferred) | elevation ° |
|---|---|---|---|---|
| 2026-09-21 07:03:55 | plane | SAS4079 | 24.2 | 8.6 |
| 2026-09-21 08:12:50 | plane | SAS4773 | 17.8 | - |
| 2026-09-21 09:01:55 | plane | DTR546 | 25.7 | 6.7 |
| 2026-09-21 09:34:53 | plane | FIN8PN | 19.5 | - |
| 2026-09-21 10:54:18 | plane | WIF3W | 24.2 | 8.0 |
| 2026-09-21 11:03:18 | plane | WIF2B | 17.0 | 10.4 |
| 2026-09-21 11:29:01 | plane | SAS4497 | 36.7 | 2.8 |
| 2026-09-21 12:03:51 | plane | SAS80M | 21.5 | - |
| 2026-09-21 13:58:57 | - | - | - | - |
| 2026-09-21 14:07:26 | plane | LNFTS | 39.5 | 1.0 |
| 2026-09-21 14:09:32 | plane | WIF3W | 27.5 | 7.9 |
| 2026-09-21 14:23:30 | plane | SAS291 | 14.4 | - |
| 2026-09-21 15:09:19 | plane | HEP02 | 13.8 | 2.5 |
| 2026-09-21 15:45:32 | plane | NOZ56U | 8.5 | - |
| 2026-09-21 17:42:57 | plane | SAS291 | 14.0 | - |
| 2026-09-21 18:00:29 | plane | SAS2983 | 34.0 | 11.4 |
| 2026-09-21 18:02:05 | plane | LNBDL | 33.5 | 1.3 |
| 2026-09-21 18:19:57 | plane | SAS4040 | 29.6 | 6.8 |
| 2026-09-21 19:15:14 | plane | LNBDL | 29.7 | 1.4 |
| 2026-09-21 20:28:06 | plane | TVF64MW | 60.1 | 3.7 |
| 2026-09-21 21:33:12 | plane | LNOZD | 31.2 | 1.0 |
| 2026-09-21 22:32:01 | plane | NOZ638 | 51.2 | 9.5 |

Hand labels from default.no/plane.php (analyse.json; «Tidene er ekte tid», `AnalysePanel.tsx:177`): 27 clips, of which 25 are «plane», 1 «not» (07:59:20) and 1 «unsure» (08:30:20).

| time (real, per analyse.json) | label |
|---|---|
| 2026-09-21 07:03:55 | plane |
| 2026-09-21 07:59:20 | not |
| 2026-09-21 08:30:20 | unsure |
| 2026-09-21 09:01:55 | plane |
| 2026-09-21 09:34:53 | plane |
| 2026-09-21 10:54:18 | plane |
| 2026-09-21 11:03:18 | plane |
| 2026-09-21 11:29:01 | plane |
| 2026-09-21 11:29:02 | plane |
| 2026-09-21 12:03:51 | plane |
| 2026-09-21 13:58:57 | plane |
| 2026-09-21 14:07:25 | plane |
| 2026-09-21 14:07:26 | plane |
| 2026-09-21 14:07:38 | plane |
| 2026-09-21 14:07:47 | plane |
| 2026-09-21 14:09:32 | plane |
| 2026-09-21 15:09:19 | plane |
| 2026-09-21 15:10:09 | plane |
| 2026-09-21 15:45:32 | plane |
| 2026-09-21 17:42:57 | plane |
| 2026-09-21 18:00:29 | plane |
| 2026-09-21 18:02:05 | plane |
| 2026-09-21 18:19:57 | plane |
| 2026-09-21 19:15:14 | plane |
| 2026-09-21 20:28:06 | plane |
| 2026-09-21 21:33:12 | plane |
| 2026-09-21 22:32:01 | plane |

The best flylyd cell (60.0/9.9) is far from the fusion #1. Given the audio loop (section 18), default.no keeps this term **out of** every mirrored fusion variant: no `aircraft` key appears anywhere.

---

## 15. Sun (`defaultno_mer.json` sol, solbane; plus quotes)

| time (stream, 21.09) | solar elevation | tolerance | basis (verbatim) |
|---|---|---|---|
| 19:00:40 | 1° | ±2.5° | «Tavla: «sola går ned snart»» |
| 19:47:00 | −4.5° | ±2.0° | «Tavla: «MØRKT NÅ» (mørkt under trærne)» |
| 19:57:00 | −6° | ±2.0° | «Kameraet: himmelgløden mellom trærne er på det laveste» |

Sun-path fit, 21.09 16:20–17:40, 40 frames:

| lat | rms | f (px) | heading ° | pitch ° |
|---|---|---|---|---|
| 59.5 (best) | 3.296 | 1068 | 219.6 | 0.2 |
| 59.0 | 3.297 | 1068 | 219.7 | 0.5 |
| 60.0 | 3.309 | 1068 | 219.5 | −0.1 |
| 58.5 | 3.311 | 1068 | 219.7 | 0.7 |
| 60.5 | 3.335 | 1068 | 219.4 | −0.3 |

default.no/magnus: «Det passer best med ca. 59,5° nord, men forskjellen mellom breddegradene er liten, så dette er et svakt bevis.» The heading of 219.5–219.7° agrees with the whiteboard «KAMERA 41 ØST» (camera NE of the box, filming ≈221°) (`innhold.ts:481-488`).

Morning sun, **via mkekeoooo, unverified in the original video**: «default.no målte første direkte solflekk i bildet kl. 07.51 den 21.09, og at sola var sterkest 08.25–09.55» (report p. 8). Claude's re-measurement on default.no minute clips (mk_bevis README) found crown/trunk light from 07:47 and faint warm spots by 07:40–07:44, so first sun could be **earlier** than 07:51. mkekeoooo uses this sunfleck to exclude the Birkebeinerveien and Gålaveien sites. That exclusion depends on the 07:51 premise.

---

## 16. Weather

### 16.1 Rain since stream start (`regn.json`)

The count runs from 2026-09-21T04:50Z (06:50 CEST). 796 of 831 stations were wet, from 76 radar snapshots (updated 24.09 18:25). The premise is (a) via default.no: the glass in front of the camera stayed dry; the whiteboard said «NULL REGN» on 22 and 23.09 (mkekeoooo report p. 7).

The mkekeoooo report also quotes default.no: «Vestlandet, fjellet og Trøndelag 5–15 mm i samme periode, mens Østerdalen fikk 0–0,7 mm».

Grid cells absent from regn.json but inside the fusion domain count as dry: 2 272 cells. The main southern dry cluster is 53 cells centred 60.80/11.95 (60.55–61.15 N, 11.30–12.40 E: Elverum–Våler–Åsnes–Trysil south). 61.45/11.10 is level 1 (light), and the fusion `rain` penalty there is 1.1.

### 16.2 Radar snapshot 24.09 18:35 CEST (`radar.png`, `defaultno_mer.json:405-418`)

default.no regional values: «boksen (Rena-Evenstad)» 0.0, Koppang 0.0, Elverum 0.0, Ringsaker 0.0, Trysil 0.0, Lillehammer 0.0, Oslo 0.0 mm/h. Wet stops: none of 40.

My pixel check with lat-linear registration: 61.45/11.10 has no echo (3 of 49 px "very light"), and Koppang, Rena, Elverum, Trysil, Lillehammer and Ringsaker have none. Oslo has light to moderate rain. There is heavy rain over the Oslofjord/Vestfold (Larvik–Tønsberg), and bands near 62.1–62.3 N, 11.2–11.9 E (Tynset/Tolga) and around Fagernes.

### 16.3 MET "nå" 24.09 18:07:43 (`met.json`)

81 points on an irregular grid (lat 58.4–62.8, lon 5.0–11.8). 0 raining. Temperature 4.8–16.5 °C, cloud 0–100 %, RH 62.5–97.9 %. The run took 12.3 s.

Near the box: (61.4, 11.0) 9.9 °C, cloud 44.2 %, RH 70.1 %; (61.4, 11.2) 12.2 °C, 41.7 %, 66.4 %; (61.6, 11.0) 12.5 °C, 60.9 %, 63.4 %.

### 16.4 Station similarity to the camera, 24.09 (`vaer.json`, `defaultno_mer.json` vaer)

Camera-derived values for 24.09: `dugg` = false (no dawn dew), `tort` = null. Hourly camera brightness ("sol" = brightest pixels) and motion ("sving" = tree sway):

| hour | 'sol' (brightness of brightest pixels) | 'sving' (tree sway / motion) |
|---|---|---|
| 00 | 202.3 | 0.57 |
| 01 | 203.3 | 0.57 |
| 02 | 203.9 | 0.58 |
| 03 | 200.0 | 0.56 |
| 04 | 200.2 | 0.57 |
| 05 | 214.8 | 0.74 |
| 06 | 214.9 | 1.23 |
| 07 | 163.4 | 0.84 |
| 08 | 129.3 | 0.84 |
| 09 | 128.3 | 0.66 |
| 10 | 137.9 | 0.66 |
| 11 | 151.7 | 0.87 |
| 12 | 148.6 | 0.9 |
| 13 | 160.7 | 0.76 |
| 14 | 166.4 | 0.76 |
| 15 | 173.3 | 0.89 |
| 16 | 143.0 | 0.76 |
| 17 | 148.3 | 0.67 |
| 18 | 132.4 | 0.65 |

400 stations. score ranges 0.0–3.21 (median 1.24). magnus labels score as «Likhet med kameraet» with red = «ligner mest».

| station | lat, lon | moh | score | dugg (dew-point spread at dawn °C) | regn 07–12 mm | stigning to 11 °C |
|---|---|---|---|---|---|---|
| SKROVA FYR | 68.1535, 14.6485 | 14.0 | 3.21 | 2.0 | 0.0 | 0.3 |
| REIPÅ | 66.9035, 13.646 | 9.0 | 3.19 | 0.5 | 0.0 | -0.1 |
| OPSTVEIT | 59.8578, 6.017 | 38.0 | 3.18 | 1.2 | 0.0 | -0.5 |
| LØNSDAL STASJON | 66.7435, 15.4628 | 520.0 | 3.16 | 0.2 | 5.7 | -0.1 |
| REINHAUGEN | 70.3357, 28.9648 | 470.0 | 3.09 | -0.1 | 0.0 | 1.3 |
| FARKOLLEN | 69.8043, 28.9937 | 321.0 | 3.05 | 0.0 | 0.0 | 1.8 |
| SIHCCAJAVRI | 68.756, 23.5395 | 382.0 | 3.04 | 0.0 | 0.0 | 1.5 |
| NARVIK - FAGERNESFJELLET | 68.421, 17.4802 | 1000.0 | 3.01 | 2.0 | 0.0 | -0.5 |
| TRONDHEIM LH - GEVINGBERGET | 63.4405, 10.9088 | 150.0 | 2.98 | 0.1 | 0.0 | 1.1 |
| BØ I VESTERÅLEN III | 68.6072, 14.4347 | 8.0 | 2.97 | 2.3 | 0.2 | -0.1 |
| LAKSFORS | 65.6215, 13.2892 | 50.0 | 2.96 | 0.1 | 4.9 | 0.1 |
| MÆRE III | 63.9425, 11.4255 | 59.0 | 2.93 | 0.6 | 2.9 | 1.5 |
| KAUTOKEINO | 68.9964, 23.0349 | 307.0 | 2.93 | 0.3 | 7.2 | 1.2 |
| SUOLOVUOPMI - LULIT | 69.5797, 23.5345 | 381.0 | 2.91 | 0.1 | 3.1 | 1.9 |
| UTSIRA FYR | 59.3065, 4.8723 | 55.0 | 2.9 | 0.0 | 0.0 | 1.2 |
| KORGÅSEN | 69.9363, 28.3773 | 418.0 | 2.9 | -0.1 | 0.0 | 1.2 |
| STEINKJER - SØNDRE EGGE | 64.0217, 11.4493 | 6.0 | 2.87 | 0.5 | 2.3 | 1.2 |
| SELJELIA | 66.1317, 13.5867 | 126.0 | 2.84 | 0.3 | 6.0 | 0.7 |
| FLÅM - JOASETBERGI | 60.8625, 7.1603 | 860.0 | 2.84 | 0.3 | 0.0 | 0.8 |
| ARNØYA - TROLLTINDEN | 70.075, 20.431 | 850.0 | 2.83 | 3.0 | 0.0 | 1.2 |
| *(stations within 80 km of 61.45/11.10)* | | | | | | |
| EVENSTAD (3 km) | 61.4273, 11.0794 | 257.0 | 0.61 | 0.5 | 0.0 | 1.2 |
| RENA - ØRNHAUGEN (23 km) | 61.3764, 11.4994 | 872.0 | 2.35 | 0.1 | 0.2 | -0.5 |
| RENA FLYPLASS (33 km) | 61.1847, 11.3747 | 255.0 | 1.64 | 0.3 | 0.2 | -0.2 |
| RENA - SVESTAD (36 km) | 61.1479, 11.3562 | 260.0 | 1.76 | 0.1 | 0.2 | 0.1 |
| SJUSJØEN - STORÅSEN (38 km) | 61.1638, 10.7088 | 930.0 | 2.29 | 0.0 | 0.3 | -0.3 |
| FÅVANG (49 km) | 61.4582, 10.1872 | 200.0 | 0.54 | 1.5 | 0.2 | 0.8 |
| GAUSDAL - FOLLEBU (51 km) | 61.2265, 10.2614 | 375.0 | 1.3 | 0.4 | 0.4 | 0.1 |
| KVITFJELL (52 km) | 61.4647, 10.1266 | 1030.0 | 2.07 | -0.1 | 0.0 | 0.3 |
| LILLEHAMMER - SÆTHERENGEN (52 km) | 61.0917, 10.4762 | 240.0 | 1.66 | 0.0 | 0.4 | 0.6 |
| VENABU (57 km) | 61.6513, 10.1082 | 930.0 | 0.68 | 0.7 | 0.0 | 0.7 |
| BARKALD (61 km) | 61.992, 10.8864 | 452.0 | 0.77 | 0.8 | 0.0 | 1.0 |
| TRYSIL MOSANDEN (65 km) | 61.2956, 12.2758 | 360.0 | 1.75 | 0.1 | 0.9 | 0.2 |
| DREVSJØ (70 km) | 61.887, 12.0462 | 672.0 | 2.08 | -0.1 | 0.0 | 0.2 |
| HAMAR - STAVSBERG (70 km) | 60.818, 11.0697 | 221.0 | 2.36 | 0.5 | 0.7 | -1.3 |
| ILSENG (72 km) | 60.8028, 11.2028 | 182.0 | 2.75 | 0.4 | 0.6 | -0.2 |
| HAMAR II (72 km) | 60.8006, 11.0948 | 141.0 | 2.51 | 0.5 | 0.7 | -0.8 |
| KISE PÅ HEDMARK (77 km) | 60.7733, 10.8055 | 128.0 | 1.9 | 0.7 | 0.3 | -1.0 |
| ALVDAL (77 km) | 62.1093, 10.6268 | 478.0 | 0.83 | 1.5 | 0.0 | 0.9 |

**Caveat.** The highest "similarity" stations are coastal Northern Norway and Finnmark (Skrova fyr 3.21, Reipå, Opstveit, Lønsdal…). EVENSTAD itself scores only 0.61. Either the score is a **mismatch** metric and magnus misread it, or the 24.09 comparison carries little information. Its role in the fusion `weather` term is not documented.

### 16.5 Road-weather cameras 24.09 18:30:58 (`vegkamera.json`)

533 stations, 313 measuring precipitation, 6 wet:
- Melleby E18 59.5457/11.4559: 0.9 mm/h
- Arebekken F21 59.2544/11.6844: 3.5
- Bømlabrua F542 59.7371/5.3781: 2.2
- Krossleitet F560 60.3173/5.0785: 1.1
- Storsand F281 59.6415/10.6038: 80.3
- Folmo F175 60.1465/11.4939: 0.7

Nearest to 61.45/11.10: Koppang R3 (61.5747, 11.0046, 14.8 km) 0.0 mm/h, 10.1 °C, RH 73 %; Rena R3 (61.1215, 11.363) 0.0, 12.2 °C. Image URLs are `https://kamera.atlas.vegvesen.no/api/images/<kam id>`.

### 16.6 Satellite scenes around 61.44/11.10 (`defaultno_mer.json` hls)

| date | satellite | coverage | cloud share |
|---|---|---|---|
| 2026-09-21 | S2 | 0.99 | 0.22 |
| 2026-09-18 | S2 | 1.0 | 0.72 |
| 2026-09-18 | Landsat | 0.99 | 0.74 |
| 2026-09-17 | Landsat | 0.32 | 0.33 |
| 2026-09-16 | S2 | 1.0 | 0.79 |
| 2026-09-13 | S2 | 1.0 | 0.03 |
| 2026-09-11 | Landsat | 1.0 | 1.0 |
| 2026-09-10 | Landsat | 0.99 | 0.06 |
| 2026-09-09 | Landsat | 0.38 | 1.0 |
| 2026-09-08 | S2 | 1.0 | 0.24 |
| 2026-09-06 | S2 | 1.0 | 0.24 |
| 2026-09-05 | S2 | 1.0 | 0.08 |
| 2026-09-03 | Landsat | 0.98 | 0.38 |
| 2026-09-03 | S2 | 1.0 | 0.4 |
| 2026-09-02 | Landsat | 0.99 | 0.16 |
| 2026-09-01 | S2 | 1.0 | 0.05 |
| 2026-09-01 | Landsat | 0.32 | 0.05 |
| 2026-08-29 | S2 | 1.0 | 0.92 |
| 2026-08-27 | S2 | 1.0 | 0.58 |
| 2026-08-26 | S2 | 1.0 | 0.08 |
| 2026-08-26 | Landsat | 1.0 | 0.14 |
| 2026-08-25 | Landsat | 0.99 | 0.06 |
| 2026-08-24 | Landsat | 0.33 | 0.09 |
| 2026-08-24 | S2 | 1.0 | 0.19 |
| 2026-08-22 | S2 | 1.0 | 1.0 |
| 2026-08-19 | S2 | 1.0 | 0.12 |
| 2026-08-18 | Landsat | 1.0 | 0.14 |
| 2026-08-17 | S2 | 1.0 | 0.04 |
| 2026-08-17 | Landsat | 1.0 | 0.04 |
| 2026-08-16 | S2 | 1.0 | 0.76 |
| 2026-08-16 | Landsat | 0.34 | 0.81 |
| 2026-08-12 | S2 | 1.0 | 0.09 |

«Satellitt 21.09» tile layer: NASA GIBS HLS_S30 2026-09-21 (cloud share 0.22 in that scene; the clearest scene is 2026-09-13 at 0.03).

---

## 17. Terrain, forest and other layers

- **eiffel_band** (d): see note in section 2. The horde AI answer behind it (quoted by magnus): «2,7 eiffeltårn stablet oppå hverandre» for HORDEMINUS (`lag.ts:236`, class a via magnus). Orange covers 8.8 % of the 60.6–61.8/10.7–12.4 box and yellow 3.2 %. The bands are on the high ground both west (Ringsakfjellet/Sjusjøen) and east (Rendalen/Åmot/Trysil) of Glomma. There is almost nothing south of ≈61.1 N anywhere in the box.
- **eiffel_road** (d): the 800–900 m-from-road reading of 891. Red = all drivable roads including forest/tractor roads; yellow = public roads only. Version 2.
- **hogst** (b/c): GFW loss year. Magnus's paraphrase of default.no's search rule: «default.no leter innen 800 m fra en hogstflate fra 2022 eller senere, eller 400 m fra en fra 2024–25 (Global Forest Watch)» (`innhold.ts:876`). The primary behind it, via magnus: Anja «har kjent lukt av tømmer, hørt dunking og sett en lastet tømmerbil» (`innhold.ts:874`).
- **skytefelt** (b + c): Forsvarsbygg via Geonorge, 2025-12-19, «IKKE gå inn». Six polygons:
  - Steinsjøen skyte- og øvingsfelt: 60.517–60.570 N, 11.045–11.113 E
  - Rødsmoen: 61.147–61.259 / 11.358–11.499
  - Terningmoen, two rings: 60.818–60.884 / 11.466–11.564
  - Kittilbu kjøreløyper (øvingsfelt): 61.117–61.179 / 9.868–10.014
  - Regionfelt Østlandet: 61.201–61.424 / 11.420–11.690

  All have status «brukes». The fusion model uses «68 ranges, 77 cells inside penalised e^-3» nationally. The premise is (a) via default.no: «INGEN SKYTING».
- **leder** (b + c): 504 pilgrim-route polylines (9 941 pts) and 256 Østerdalsleden polylines (1 700 pts, 61.13–63.43 N, 10.32–11.49 E). The nearest Østerdalsleden point is **5.3 km** from 61.45/11.10. The premise is «INGEN STIER».
- **baer** (d, weak): 17 530 cells; level 5 (most lingonberry) in only 280 cells. East Norway is mostly level 3 (mixed), with level 4 north of ≈61.6 N.
- **baerfunn** (b): lingonberry 3 919 records (2015–2026, peak 2024: 597) and blueberry 4 466 (2024: 816), in the box 60.30–62.30 N, 9.50–12.80 E.
- **fugl** (b): 0.02° cells in 60.3–62.28 N, 9.5–12.78 E. Black grouse: 1 897 cells / 6 061 records in the box; top cells 60.98/12.48 (115), 61.26/10.54 (101), 61.18/11.40 (70), 61.04/12.58 (69), 61.52/9.70 (65). Capercaillie: 1 516 cells / 3 350; top 60.50/11.30 (46), 61.04/12.58 (30). default.no suggests a sound on 24.09 «kan være orrfugl som spiller» (c). mkekeoooo: «Orrfuglleiken er Artsdatabankens registrering ved Evenstadlia, gjengitt av default.no» (report p. 16).
- **coop** (b): 60 Coop shops in the «Innlandet-boksen» (Extra 34, Coop Prix 15, Mega 3, Obs 3, Marked 2, unnamed brand 2, "Coop" 1). The nearest to 61.45/11.10 is Coop Prix Koppang (61.57059, 11.05094), 13.7 km. The premise is «dressing fra Coop» (a via magnus).
- **pizza** (b): 65 OSM pizza places (60.33–61.89 N, 9.54–12.78 E). The nearest to 61.45/11.10 are Hev Mosetertoppen and Pellekroa at about 38 km.

---

## 18. Audio, bird and tag analysis (`analyse.json`, default.no pages fetched 23.09)

- **Loop** (d/b): 604 minutes compared against 52.86 h of audio (2 873 files). **227 minutes have a near-identical copy (corr > 0.8)**, and 451 have corr > 0.6.
  - Lag histogram: 23.9 h (290 hits), 47.9 h (48), 24.9 h (25), 22.0 h (20), 27.3 h (20). Updated 2026-09-23 12:27.
  - Examples (real time): 09-23 11:40:40 = 09-21 11:47:10 (0.999); 09-21 11:10:40 = 09-23 11:04:05 (0.996); 09-21 11:35:40 = 09-23 11:29:04 (0.996); 09-23 12:15:40 = 09-21 12:22:09 (0.996); 09-23 11:00:40 = 09-21 11:07:15 (0.995); 09-21 10:25:40 = 09-23 10:19:05 (0.993).
  - magnus's conclusion: «lyden er ikke direkte, den spilles av på nytt i loop» (`AnalysePanel.tsx:118-119`).
  - Organizer, via chat (not verified verbatim): Alf on TikTok 25.09 said «Det er ekte lyd på streamen. Men dere husker kanskje tidligere år, da drev vi å trollet litt med lyden.» On live vs delayed: «Ja, det må du prøve å finne ut av.» (`innhold.ts:342-345`).
- **YAMNet tags**: wind 9 173, speech 193, aircraft 49, aircraft_candidate 49, train 20, dog 16, siren 11, gunshot 10, bell 7, music 2. default.no's low-confidence detections on 21.09: «mulige tog (08:34, 11:29, 14:07), klokker (08:35, 14:00) og skudd (14:24, 14:54) … alle med lav sikkerhet (0,33–0,51)» (`innhold.ts:149`).
- **BirdNET** (53 Norwegian species; detections):

| Norwegian | Latin | detections |
|---|---|---|
| Kjøttmeis | Parus major | 966 |
| Blåmeis | Cyanistes caeruleus | 802 |
| Granmeis | Poecile montanus | 325 |
| Bokfink | Fringilla coelebs | 295 |
| Rødvingetrost | Turdus iliacus | 240 |
| Gråtrost | Turdus pilaris | 148 |
| Skjære | Pica pica | 125 |
| Dompap | Pyrrhula pyrrhula | 123 |
| Gråsisik | Acanthis flammea | 109 |
| Grankorsnebb | Loxia curvirostra | 96 |
| Furukorsnebb | Loxia pytyopsittacus | 48 |
| Kjernebiter | Coccothraustes coccothraustes | 47 |
| Svarttrost | Turdus merula | 46 |
| Flaggspett | Dendrocopos major | 45 |
| Trekryper | Certhia familiaris | 41 |
| Vintererle | Motacilla cinerea | 39 |
| Isfugl | Alcedo atthis | 39 |
| Sidensvans | Bombycilla garrulus | 32 |
| Rødtoppfuglekonge | Regulus ignicapilla | 27 |
| Svartrødstjert | Phoenicurus ochruros | 26 |
| Grønnspett | Picus viridis | 25 |
| Duetrost | Turdus viscivorus | 20 |
| Ringtrost | Turdus torquatus | 18 |
| Tretåspett | Picoides tridactylus | 17 |
| Nøtteskrike | Garrulus glandarius | 15 |
| Boltit | Eudromias morinellus | 15 |
| Rødstrupe | Erithacus rubecula | 13 |
| Kattugle | Strix aluco | 13 |
| Enkeltbekkasin | Gallinago gallinago | 12 |
| Trepiplerke | Anthus trivialis | 12 |
| Toppmeis | Lophophanes cristatus | 11 |
| Gulerle | Motacilla flava | 11 |
| Svartmeis | Periparus ater | 9 |
| Grønnfink | Chloris chloris | 9 |
| Grønnsisik | Spinus spinus | 9 |
| Låvesvale | Hirundo rustica | 8 |
| Fuglekonge | Regulus regulus | 7 |
| Bjørkefink | Fringilla montifringilla | 6 |
| Gransanger | Phylloscopus collybita | 6 |
| Steinskvett | Oenanthe oenanthe | 6 |
| Dvergspett | Dryobates minor | 6 |
| Ravn | Corvus corax | 6 |
| Rugde | Scolopax rusticola | 5 |
| Løvsanger | Phylloscopus trochilus | 5 |
| Jernspurv | Prunella modularis | 5 |
| Sibirpiplerke | Anthus hodgsoni | 4 |
| Taksvale | Delichon urbicum | 4 |
| Kråke | Corvus corone | 4 |
| Gråfluesnapper | Muscicapa striata | 4 |
| Lappiplerke | Anthus cervinus | 4 |
| Gråhegre | Ardea cinerea | 3 |
| Hortulan | Emberiza hortulana | 3 |
| Sothøne | Fulica atra | 3 |

  False, non-Norwegian species in the same output: Cape White-eye, Green-backed White-eye, Chestnut-faced Babbler, Downy Woodpecker, California Towhee, Wood Duck, American Three-toed Woodpecker, Purple Finch, Juniper Titmouse, Spotted Sandpiper, Crested Caracara, Cassia Crossbill, Northern Waterthrush, Black-throated Sparrow, Western Capercaillie, Ringed Kingfisher, Common Moorhen, Oak Titmouse, Golden-crowned Kinglet and Water Rail. Single species are therefore unreliable, and the audio may be replayed.

- **Not default.no** (also in analyse.json): the municipality assessment (usikkert 63, lite sannsynlig 123, utelukket 164) and the «vercelFakta» list come from hordejakten.vercel.app. They are listed here only so they are not mistaken for default.no output.

---

## 19. Cross-references in other local sources

| claim | where |
|---|---|
| «Deres fusjonsmodell har beste område i Glommadalen mellom Rena og Evenstad (61.35–61.47 N, 10.97–11.15 Ø), med 11 % av sannsynligheten innen 10 km og 29 % innen 25 km fra toppcellen 61.45, 11.10.» | mkekeoooo full report p. 9 |
| «Stedsfinneren … Den ga Birkebeinerveien (61.4487, 10.9775) øverst. Kjøreplanen på 40 stopp har Madsskardveien øst for Glomma (61.4520, 11.1460) som stopp 1.» | same |
| «Deres modell bygger imidlertid på noen av de samme usikre premissene: tørrvær og hvilket fly hun så. Prosenttallene er derfor ikke brukt som bevis for enkeltpunkter.» | same |
| Round 1 of mkekeoooo's own ranking = «Østsiden ved Madsskardveien (default.no stopp 1, 61.452, 11.146)» | report p. 17 |
| «Punktet 61°26′55,3″N 10°58′39,0″E samsvarer innen én meter med default.no sitt site finder-toppunkt ved A1. Samme kilde kan ligge bak flere forslag.» | mkekeoooo README:17 |
| default.no measured stream delay ≈22 s | mk_bevis README:48 |
| «ifølge default.no viser kildekartene til horde.no et kodespill (Kodejakten), men ingen stedstekst» | report p. 15 |
| Magnus site-finder "strong hits" list (current): Gålaveien 61.4725/10.9677, Madsskardveien 61.4747/11.0966, Tolvmilskogen 60.69/12.35, **Kirkesjøvegen 60.358/12.507** (not in the 24.09 steder list, so from an older run). Birkebeinerveien 61.4495/10.9752 was deleted in e431102 | `innhold.ts:1169-1175`, git |
| magnus hint: «default.no regnet ut kameraretningen fra sola alene (219–220°)» | `innhold.ts:88, 487` |
| The Tommsen B tip 61.4732/10.9687 is «rett ved default.no sine letestopp ved Gålaveien» | `innhold.ts:1296` |

---

## 20. Contradictions and data-quality issues

1. **Mirror edited.** magnus deleted all Birkebeinerveien items on 25.09 14:12 (e431102) with no reason given. That covers default.no's #1 site (abs 0.12638), 8 more sites, plan stops 10, 18, 20 and 38, and 3 pins. magnus's own layer texts still say «126 steder» (`lag.ts:331`) and «40 rangerte steder» (`lag.ts:272`), which match the original, not the edited files. Any engine should load `evidence/sources/defaultno_recovered/`.
2. **Overlay misregistration.** sites_NN and logging_NN for NN = 1–14, 61 and 62 do not belong to the steder/omrader bounds of the same rank (section 4). These overlays came from an older area list.
3. **Variant labels.** `fusjon/alle.json` (magnus: «Alt bevis») has no sun, sunpath or aircraft terms. `fusjon/utenlyd.json` (magnus: «Uten lyd og sol») **does** have sun and sunpath, and it lacks skytefelt. Either magnus's labels are wrong or default.no's variants differ from their names.
4. **Checked-negative site still ranked.** Site #4 (61.43072, 11.04684) remains at abs 0.10894 although the spot ~80 m away was ground-checked 23.09 («bolighus 7 m unna, ikke boksen»). plan.json `checked` is empty for all stops despite the note «sjekkede stopp ligger sist».
5. **Weather-similarity direction** is unclear (section 16.4).
6. **21.09 `lost.utc`** is 19:31:28Z, 1 min 48 s after the pointing time. The 22.09 events use stream − 22 s. The time base for event 1 is inconsistent or undocumented.
7. **Event labels.** The magnus legend says «21.09 21:30 og 22.09 20:33 og 20:35» (`lag.ts:431`), while the file names the events «21.09 21:29», «22.09 20:32» and «22.09 20:34». This is cosmetic.
8. **Skytefelt count.** The fusion text says 68 ranges and 77 cells; skytefelt.json has only 6 polygons (Innlandet box).
9. **Shooting-star ambiguity** for event 1 (section 12.3).
10. **Sound evidence.** The flylyd best cell 60.0/9.9 conflicts with the fusion #1. default.no itself flags the audio as replayed.
11. **HLS "klarest 21.09"** refers to the clearest scene during the hunt (0.22 cloud); 2026-09-13 (0.03) and 2026-09-01 (0.05) are clearer.
12. **Morning sunfleck 07:51** (default.no) vs Claude's 07:47 crown light and earlier possible warm spots (mk_bevis). This affects exclusions of west-of-Glomma sites.
13. **Weather cut-off.** default.no `rain` treats any station rain since 04:50Z as a penalty. mkekeoooo notes a possible rain window on 24.09 10:55–11:15 at the camera (matte, dewy patches on the glass; «ikke sikkert fallende regn»). The dry-glass premise may not hold for the whole period.
14. **Radar "Oslo 0.0".** default.no's radar summary gives «Oslo» 0.0 mm/h at 24.09 18:35. Sampling radar.png at 59.91/10.75 (lat-linear) shows light-green and yellow echoes (moderate rain) in the 7×7 px neighbourhood. default.no's "Oslo" sample point is not documented, so this may be a different location, or the regional values may come from a different product.

---

## 21. Open questions

- Why did magnus remove Birkebeinerveien 25.09 14:12? Was it field-checked after 24.09 18:36, or removed at someone's request? rejected.json (still present) says it was only seen from the road behind a barrier.
- Has default.no run newer fusion, site or plan versions after 24.09 18:36? default.no is not reachable from here, so a GitHub mirror refresh or search is needed.
- Where do sites/logging PNGs 3–9, 12–14, 61 and 62 really belong?
- What are the exact regn level thresholds, and is the vaer `score` similarity or mismatch?
- Which plan version do the `fugl.per_stopp` ranks refer to?
- What does 21.09 `lost.utc` = 19:31:28Z mean?
- What do the hypothesis tags mean (`and`, `lat61`, `link1`, `wide`, `nordistuen`, `stavsjo_fine`)?
- Is event 1 a plane or a shooting star? default.no's osint_notes are cited but not mirrored.

---

## 22. Candidate summary

Source abbreviations in `candidates[]`: `dn/…` = `data/raw/magnus/public/data/defaultno/…`, and `recovered/…` = `evidence/sources/defaultno_recovered/…` (pre-edit default.no copies).

The full list, with coordinates and scores, is in the structured output `candidates[]`: 34 areas, 126 sites, 40 plan stops, 6 walk zones, 12 × 9 fusion-variant areas, 15 rejected areas, 13 pins, the top-12 sjelden cells, the flylyd best cell and the historical rankings.

Short list of what default.no rates highest (24.09 18:36):

| rank basis | point | value |
|---|---|---|
| fusion area #1 | 61.45, 11.10 | p 0.127; m10 0.11; m25 0.289 |
| site finder, abs #1 | **61.44874, 10.97747 (Birkebeinerveien, 605 moh)** | score 0.995, abs 0.12638 (removed from mirror; only seen from road 23.09) |
| site finder, abs #2–5 | 61.46351/10.95862 (Gålaveien 414 moh); 61.46243/10.97521 (Gålaveien 366); 61.43072/11.04684 (Storelvdalsveien 322; *ground-checked negative ≈80 m away*); 61.47252/10.96767 (Gålaveien 402) | abs 0.1137, 0.1114, 0.1089, 0.1063 |
| plan stop 1 | 61.452, 11.146 (Madsskardveien), park 61.45283/11.14854 | site_score 1.0 |
| sjelden #1 | 61.30, 11.00 | dag 2, 21:30 plane 55.4° |
| flylyd best | 60.0, 9.9 | 21/33 passes heard (uncertain) |
