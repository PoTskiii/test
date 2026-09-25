# Non-default.no datasets in the MagnusPladsen map (`public/data/*.json`): catalogue, decoding and localisation stats

**Scope.** This covers every JSON file in `/home/user/test/data/raw/magnus/public/data/` that is not in the `defaultno/` sub-folder (14 files). The mirror is MagnusPladsen/hordejakten-2026, commits up to 25.09.2026 21:04 CEST, and it is read-only. For each file I give the provenance (git commit plus the loader code in `src/`), the schema, what each field means, the grid and extent, the value distributions, caveats and a Python recipe to decode it. I then overlay all the layers on the 810–891 moh points and count what survives each combination of constraints.

**Author and date.** Written 25.09.2026 in the evening, CEST. All computations use `/home/user/test/.venv/bin/python`. The analysis scripts are copied to `/home/user/test/evidence/sources/other_datasets_scripts/`. There is a per-point overlay table (see §6) and three figures in `/home/user/test/evidence/sources/other_datasets_figs/`.

**Evidence classes used below.**
- **[P]** Primary: Anja's whiteboard ("tavla"), what can be seen on the stream, organizer statements, and replies from the Horde app or Horde AI.
- **[C]** Community observation or data product: a map someone drew, an ADS-B extract, and so on.
- **[I]** Interpretation or theory.
- **[M]** Model output. This includes derived grids that the magnus app computes from an interpretation.

Every dataset in this folder is **[C]** or **[M]**. None of them is primary evidence. Several are built directly on top of an **[I]**, for example "2,7 eiffeltårn = 810–891 moh" or "INGEN SKYTING = no hunting".

**Time convention.** All clock times are CEST (UTC+2). "Stream time" means the time the stream shows. "Real time" means wall-clock time. The stream delay is not known. The magnus app says «trolig 20 sek–1 min forsinket (vi tipper)» (`src/data/lag.ts:838`). default.no measured about 22 s (`mk_bevis/.../README.md`, adsb section).

---

## 0. Key findings (read this first)

1. **`fly_2130.json` timestamps are 46 s early (a new finding).** I compared all 10 samples of NOZ9EG and NOZ56U in `fly_2130.json` against the full-resolution adsb.lol `trace_full` files on the evidence branch (`mk_bevis/bevis/claude-2026-09-25/adsb/trace_4791ac.json`, `trace_47a3b0.json`). Every labelled position matches the trace position and barometric altitude **46.0 ± 0.5 s later** than the label. For each point the best-match distance is 4–46 m.
   - The magnus app treats the labels as real time (`src/lib/fly.ts:1`, `PEKETID_EKTE = '21:29:15'`). Its "positions when she pointed" are therefore really the positions at about 21:30:01 real time.
   - For NOZ9EG this puts the pointing position about 9.5 km too far south. For NOZ56U it puts it about 8 km too far north.
   - The true positions at real 21:29:16 (stream 21:29:38 minus a 22 s delay) are:
     - NOZ9EG (LN-NIQ, hex 4791ac): **61.3171 N, 10.9040 E**, 25,920 ft geometric altitude.
     - NOZ56U (LN-ENN, hex 47a3b0): **60.7394 N, 11.2220 E**, 20,655 ft geometric altitude.
   - I only have full traces for these two aircraft. The other 47 tracks share the same five snapshot labels, so they probably have the same offset, but I have not verified that. **[C]**, verified against raw ADS-B.
2. **`hoyde891.json` fields.** Each point is `[lat, lon, moh, metres to nearest drivable road, road-to-SE flag 0/1]` on a 0.005° × 0.01° grid (about 556 m × 540 m, about 0.30 km² per point). It holds only points at 790–911 moh that are at most 900 m from a road. The field meanings come from the comment at `src/components/Kart.tsx:106`: «Punkter mellom 790 og 911 moh nær vei: [lat, lon, moh, meter til vei, vei mot sørøst (0/1)]». The layer rests on the **[I]** that Horde AI's «2,7 eiffeltårn stablet oppå hverandre» [P, organizer app] means an elevation.
   - The file has 17,234 points. 14,579 are at 800–900 m and **12,011 at 810–891 m**.
   - Inside Innlandet (simplified polygon) there are **8,667 points at 810–891 m, all within 900 m (so within 1 km) of a road**. That is about 2,600 km². Of these, 6,185 have a road to the SE, 6,244 are within 500 m of a road and 1,894 within 100 m.
   - 427 points (277 of them at 810–891 m) lie **in Sweden** outside `norge.json`, at 61.57–62.77 N, 12.07–12.59 E. They should be discarded.
   - The file only covers lon 8.48–12.59 E, which is 90.4 % of Innlandet's area. Western Skjåk, Lom, Lesja and Vang, and the far eastern strip of Trysil and Engerdal, are not covered.
3. **Most of the community's focus area has no 810–891 m terrain near a road.** The focus area is Hamar–Løten–Elverum under NOZ56U, plus the Kongsvinger–Rena area that was clear on satellite on 23.09.
   - There are **zero** 810–891 m points in Hamar, Løten, Stange, Elverum, Gjøvik, Østre and Vestre Toten, Våler, Åsnes, Grue, Nord-Odal, Sør-Odal, Kongsvinger and Eidskog.
   - None of the 810–891 m points fall inside the hand-drawn "sol i dag" (satellite-clear 23.09) polygons.
   - The nearest 810–891 m point to NOZ56U, at either its true or its label position when she pointed, is 61.04 N, 11.26 E (Åmot). That is 33.5 km away at the true time and 25.3 km at the label time, and would put the aircraft 9° and 13° above the horizon.
   - So **"elevation 810–891 moh" and "NOZ56U was straight overhead" cannot both be true.** The same holds for SAS50J on 25.09 at 17:22: the nearest 810–891 m point was 37–59 km away, at 5–10° elevation.
4. **Under NOZ9EG there is a small set of candidate points.**
   - Using true (trace) times for real 21:28:38–21:29:23 (stream delay 15–60 s), 126 points at 810–891 m in Innlandet see NOZ9EG at ≥45° elevation. 53 see it at ≥60° and 27 at ≥70°.
   - NOZ56U gives **zero** points at ≥30° for any delay.
   - With the 22 s delay, 9 points see NOZ9EG at ≥60°. All are in Stor-Elvdal kommune (the area west of Rena, south of Messelt) and all are open on the community map.
   - The tightest cluster sits at 61.355–61.410 N, 10.88–10.99 E (centroid 61.386, 10.926). It has 36 points and 97 % of them have a road to the SE. It sees 89° at 45–60 s delay. See Fig. 2.
   - This is geometry only. Whether she pointed at an aircraft at all is disputed: the bevis README notes she may have been pointing at a shooting star. **[C]/[I]**
5. **Other aircraft were also overhead 810–891 m terrain at the corrected time** (real 21:29:00–21:29:23):
   - NOZ68L, 37,000 ft, over Tolga and Os: 146 points at ≥45°.
   - WIF149, 16,000 ft, over Nord-Aurdal (Valdres): 41 points at ≥45°. These are all in cells the community map excludes.
   - Two claims in the magnus map therefore depend on which region you look at: that only NOZ56U and NOZ9EG were overhead, and that only the Hamar–Rena corridor fits.
6. **`treslag.json` (NIBIO SR16).** Each cell holds the share of pine, spruce and deciduous in a 0.02° × 0.04° cell, plus a similarity score. I reverse-engineered the score exactly: **score = 1 − ½·(|furu−0.40| + |gran−0.25| + |lauv−0.35|)**, which is the same as the histogram intersection. The largest error is 0.01.
   - Only cells with a score ≥0.55 are stored (4,139 of the 9,240 in the grid).
   - Coverage is 59.81–62.19 N, 9.82–12.86 E, which is only 59 % of Innlandet. Valdres, western Gudbrandsdalen, Lesja and Folldal north of 62.2 N are not covered.
   - SR16 "dominant species" gives a deciduous share of 0.04 in the median cell. The 35 % birch target therefore favours birch-dominated belts, meaning lowland Ringerike/Modum and the subalpine zone in Alvdal, Tynset, Engerdal and Rendalen.
   - The best cells in Innlandet (score ≥0.94) are 61.57 N 9.86 E (Sør-Fron, 0.98), 62.11 N 10.98 E (Rendalen, 0.98), 62.19 N 10.54 E (Alvdal, 0.96), 62.11 N 10.70 E (Alvdal, 0.95), 62.19 N 11.02 E (Tynset, 0.95), 61.83 N 10.54 E (Stor-Elvdal, 0.94), 62.15 N 10.86 E (Tynset, 0.94) and 62.03 N 12.02 E (Engerdal, 0.94).
   - The NOZ9EG-overhead cluster only scores 0.60–0.64, below the app's 0.65 display threshold.
7. **`utelukket.json` (the community exclusion map) leaves more open than its caption says.**
   - The caption at `src/data/lag.ts:681` says only «stripa Hamar–Løten–Rena–Koppang, Ringsakfjellet/Rudshøgda og Gjøvik/Toten» remains.
   - In the grid, 1,267 land cells are open. They include large parts of Rendalen (107 cells), Engerdal (73), Trysil (62), Stor-Elvdal (62), Røros (48), Ringerike (45) and Åmot (45), and even Telemark and Agder coast cells.
   - Of the 8,667 points at 810–891 m in Innlandet, 2,528 are open, 850 are "C" (mountain birch) and 5,289 are "R".
8. **`fellesskap891.json` agrees poorly with `hoyde891.json`.** The community 800–900 map has 634 cells. Only 144 of them coincide with a `hoyde891` point, and 107 with one at 810–891 m. The median distance to the nearest 790–911 m near-road point is 1.07 km. Either the community map ignored road distance, or its georeferencing is off by more than the stated ±500 m.

---

## 1. Catalogue overview

Commit dates are local time (+0200). Loader references are `file:line` in `/home/user/test/data/raw/magnus/`.

| File | Bytes | Added (git) | Loader | What it is | Class |
|---|---|---|---|---|---|
| `drivetime.json` | 53,531 | c0c849b 23.09 14:30 | `src/App.tsx:90-93`, `src/lib/modell.ts:123,153` | OSRM car drive time from Oslo sentrum, 0.1° × 0.2° grid | [M] |
| `norge.json` | 131,456 | c0c849b 23.09 14:30 | `src/App.tsx:94-97` | Simplified Norway outline, used to shade "utenfor Norge" | [C] |
| `fly_2130.json` | 10,131 | ecf0260 23.09 14:42 | `src/App.tsx:118-121`, `src/lib/fly.ts`, `src/components/Kart.tsx:457-496` | ADS-B tracks of 49 aircraft, labelled 21:28:14–21:34:17 on 21.09 | [C] (labels 46 s early, see §3) |
| `innlandet.json` | 3,168 | 520fd05 23.09 14:49 | `src/App.tsx:98-101`, `src/components/Kart.tsx:620-630`, `src/lib/modell.ts:136` | Simplified Innlandet county polygon | [C] |
| `bokstaver.json` | 35,270 | 06b82f0 23.09 16:01; aa81ebf 23.09 17:56 | `src/components/Bokstavord.tsx:44` | Anagrams and place names from the referral letters N O R H E I M S U D | [M] |
| `utelukket.json` | 81,254 | 6763e06 23.09 19:08; b55eafc 19:13; fc71636 20:03 | `src/App.tsx:106-109`, `src/components/Kart.tsx:497-513`, `src/lib/modell.ts:119,137-143` | Community exclusion map, georeferenced from an image, 0.05° × 0.1° | [C]/[I] |
| `kommunevurdering.json` | 301,587 | 1971621 23.09 19:22 | `src/App.tsx:102-105`, `src/components/Kart.tsx:601-618` | hordejakten.vercel.app verdict per municipality | [I] (third-party) |
| `fellesskap891.json` | 9,290 | b03c6a9 24.09 18:32 | `src/App.tsx:114-117`, `src/components/Kart.tsx:584-599` | Community "800–900 moh + aircraft + forest + no firing range" map, 0.005° × 0.01° | [C]/[I] |
| `hoyde891.json` | 406,746 | e537086 24.09 19:49 | `src/App.tsx:110-113`, `src/components/Kart.tsx:106,515-533` | 790–911 moh within 900 m of a road, with a road-to-SE flag | [M] on [I] |
| `verneomrader_jakt.json` | 918,007 | e96bf5c 25.09 08:23 | `src/lib/verneomrader.ts:39` | Protected areas, each classified by hunting rule from its verneforskrift | [C]/[I] |
| `vind.json` | 8,831 | 01ab80d 25.09 11:29 | `src/lib/vind.ts:9` | open-meteo (MET Nordic) 10 m wind at 23.09 17:49, 0.2° × 0.4° | [M] |
| `storvilt.json` | 402,884 | bb53374 25.09 15:47 | `src/lib/storvilt.ts:10` | Statskog big-game hunting fields (Geonorge) | [C] |
| `shoplifter.json` | 12,658 | 37bd161 25.09 17:54; 72f623a 18:44; 91da5a7 19:44 | `src/components/Anagram.tsx:62` | Anagram lists for the whiteboard letters «THILPRTE OESHF» | [M] |
| `treslag.json` | 137,878 | ae6dc67 25.09 19:19 | `src/lib/treslag.ts:10` | NIBIO SR16 species shares per 0.02° × 0.04° cell, scored against 40/25/35 | [M] |

Only one build script is in the repo: `scripts/build_drivetime.py` (see §2.3). The builders for `hoyde891`, `treslag`, `vind`, `storvilt`, `verneomrader_jakt`, `utelukket`, `fellesskap891`, `bokstaver` and `shoplifter` are **not** in git; `git log --all` shows only `scripts/build_drivetime.py` was ever committed. So everything below about how those files were built comes from the layer texts in `src/data/lag.ts`, the commit messages, and reverse-engineering the data.

---

## 2. Per-dataset details

### 2.1 `hoyde891.json`: 790–911 moh near a road ("2,7 eiffeltårn")

**Provenance.** Commit e537086, 24.09.2026 19:49. The commit message reads: "17 234 spots at 790–911 moh within 900 m of a drivable road (OSM), 12 041 of them with a road to the SE («kom fra den veien ←»); heights from Kartverket DTM".

The layer text is at `src/data/lag.ts:232-244`:
> «Rutene viser skog og mark mellom 790 og 911 moh som ligger høyst 900 m fra en bilvei eller skogsbilvei, så man rekker å bære kassen dit på 5–10 min. Sterk farge betyr at veien ligger mot sørøst, slik Anja skrev («KOM FRA DEN VEIEN ←», ca. 130°). … Høyde fra Kartverket (1 m-modell) i et rutenett på ca. 500 m, veier fra OpenStreetMap. Mot: Hagina så 25.09 at bjørka er for langt på høsten allerede på ca. 510 moh ved Sjusjøen, så 810–891 moh i det området passer dårlig.»

The source is given as «Høydedata © Kartverket (terrengmodell 1 m). Veier © OpenStreetMap-bidragsytere. Tallet fra Horde AI i appen 24.09.»

**The underlying primary evidence [P, organizer app]** is at `src/data/innhold.ts:358-365`, id `eiffel`. If you write «Hordeminus» to Horde AI, it answers «2,7 eiffeltårn stablet oppå hverandre». When asked what that means, it says it is just the phrase it was told to use for that word. When asked to summarise, the bot works out 891 m (330 m tower) or about 875 m (324 m tower) itself, «og sier at den ikke vet noe om hvor boksen er. Det er altså bare chatboten som regner, ikke et nytt hint.»

Reading this as **an elevation in moh is an [I]**. The same card lists the alternatives: «Det kan også være en avstand, for eksempel fra bilveien, eller en kode: 0810 og 0891». The layer also uses 790–911 rather than 810–891, which adds ±20 m of slack. The road-to-SE flag is a second **[I]**, built on the reading of «KOM FRA DEN VEIEN ←» as about 130° (`src/data/lag.ts:860`).

**Schema.** `{dlat: 0.005, dlon: 0.01, punkter: [[lat, lon, moh, road_m, se], …]}` with 17,234 entries. The field meanings are documented at `src/components/Kart.tsx:106`: «[lat, lon, moh, meter til vei, vei mot sørøst (0/1)]». The renderer at `src/components/Kart.tsx:522` reads `[la, lo, z, , so]` and skips field 4.

| # | Field | Meaning | Range / distribution |
|---|---|---|---|
| 0 | lat | Cell centre latitude (°N), grid anchored at 59.79 in 0.005° steps | 59.79–62.805; 602 distinct values |
| 1 | lon | Cell centre longitude (°E), grid anchored at 8.48 in 0.01° steps | 8.48–12.59; 412 distinct values |
| 2 | moh | Terrain height (m) sampled from Kartverket DTM at the cell centre (a point sample, not a cell mean) | 790–911 (integers, 122 distinct); p5/25/50/75/95 = 796/821/849/878/904 |
| 3 | road_m | Distance (m) to the nearest drivable road or forest road (OSM highway tags not documented) | 0–900; p5/25/50/75/95 = 20/125/310/549/818. Histogram per 100 m: 3,583 / 2,596 / 2,226 / 2,022 / 1,682 / 1,536 / 1,354 / 1,170 / 1,061 / 4 (exactly 900) |
| 4 | se | 1 if a road lies to the south-east of the point. The bearing window is **not documented**; the stated target is about 130° | 1: 12,041; 0: 5,193 |

**Grid.** 0.005° lat × 0.01° lon, about 556 m × 540 m at 61 N, about 0.30 km² per point. The file lists only points that pass the filter (height band plus road ≤900 m). The overall extent is 59.79–62.805 N, 8.48–12.59 E. There are no duplicate coordinates.

**Elevation bins (all 17,234 points).**

| Band (m) | 790–800 | 800–810 | 810–830 | 830–860 | 860–875 | 875–891 | 891–900 | 900–911 |
|---|---|---|---|---|---|---|---|---|
| Points | 1,298 | 1,347 | 2,943 | 4,582 | 2,242 | 2,143 | 1,184 | 1,442 |

- **800–900 m:** 14,579 points in total; 10,512 in Innlandet; 7,510 in Innlandet with a road to the SE.
- **810–891 m:** 12,011 points in total; **8,667 in Innlandet**; 6,185 in Innlandet with a road to the SE.
- **Distance to road, 810–891 m in Innlandet:** ≤100 m: 1,894 (1,748 with SE road). ≤250 m: 3,835 (3,367). ≤500 m: 6,244 (5,054). ≤900 m: 8,667 (6,185).
- **Within ±5 m of the three candidate heights:** 810 m: 1,561 (1,123 in Innlandet). 875 m: 1,585 (1,225). 891 m: 1,412 (1,057).
- **Outside Norway:** 427 points (277 at 810–891 m) fall outside `norge.json`, at 61.565–62.765 N, 12.07–12.59 E, in Härjedalen, Sweden (for example 62.7 N 12.5 E, 65 points). These are invalid because the terms say the box is in Norway. Another 45 points inside Norway fall into no municipality polygon (slivers).
- **Coverage gap:** the bounding box covers 47,084 of Innlandet's 52,084 km² (90.4 %). Innlandet land west of 8.48 E and east of 12.59 E is not sampled.

**Geographic spread (810–891 m, all points).**
- **Top municipalities (n, of which in Innlandet, of which with SE road):**
  - Tynset 595 (594, 361)
  - Nord-Aurdal 577 (576, 493)
  - Røros 573 (3, 332)
  - Gausdal 535 (535, 376)
  - Ringebu 472 (472, 372)
  - Rendalen 470 (470, 265)
  - Nord-Fron 453 (453, 369)
  - Tolga 439 (439, 288)
  - Sør-Aurdal 432 (432, 317)
  - Stor-Elvdal 409 (409, 260)
  - Folldal 350
  - Nore og Uvdal 334
  - Gol 329
  - Øyer 328
  - Os 314
  - Sweden or no kommune 307
  - Etnedal 299
  - Nesbyen 298
  - Nordre Land 289
  - Engerdal 270
  - Vågå 252
  - Alvdal 242
  - Øystre Slidre 241
  - Vestre Slidre 235
  - Sør-Fron 224
  - Lesja 194
  - Ringsaker 187 (120 with SE road)
  - Tinn 179
  - Flå 179
  - Sel 176
  - Oppdal 174
  - Trysil 170
  - Hemsedal 159
  - Holtålen 146
  - Ål 126
  - Rollag 111
  - Lillehammer 111
  - Sunndal 103
  - Åmot 101
  - Lom 94
- **Verdicts from `kommunevurdering.json`:**
  - All 810–891 m points: usikkert 8,854; lite sannsynlig 2,828; utelukket 22; none 307.
  - In Innlandet: usikkert 8,641, lite sannsynlig 5, none 21.
- **Clusters.** Connected components using 8-neighbour adjacency: 1,197 in total. 41 have ≥50 points, 241 have ≥10, and 416 are singletons. The table below lists every cluster with ≥50 points. The "open" column is the share of points in a cell that is open on the community exclusion map.

| n | lat range | lon range | centroid | % Innlandet | % in Norway | % SE road | % community-open | main municipalities |
|---|---|---|---|---|---|---|---|---|
| 802 | 60.730–60.985 | 8.66–9.39 | 60.848, 8.987 | 51 | 100 | 80 | 0 | Nord-Aurdal 303; Gol 245; Hemsedal 151 |
| 407 | 61.235–61.630 | 10.18–10.57 | 61.420, 10.379 | 100 | 100 | 76 | 45 | Ringebu 247; Øyer 160 |
| 386 | 60.610–60.800 | 9.29–9.62 | 60.698, 9.450 | 87 | 100 | 73 | 0 | Sør-Aurdal 335; Nesbyen 40; Gol 7 |
| 274 | 61.070–61.285 | 9.82–10.19 | 61.169, 10.012 | 100 | 100 | 77 | 0 | Gausdal 191; Lillehammer 61; Nordre Land 19 |
| 220 | 60.915–61.045 | 9.61–9.93 | 60.994, 9.734 | 100 | 100 | 81 | 0 | Etnedal 161; Nordre Land 59 |
| 209 | 61.585–61.825 | 8.90–9.11 | 61.739, 8.999 | 100 | 100 | 79 | 0 | Vågå 158; Lom 46 |
| 188 | 61.295–61.425 | 9.75–10.11 | 61.348, 9.906 | 100 | 100 | 70 | 21 | Gausdal 178; Sør-Fron 10 |
| 164 | 62.515–62.675 | 11.11–11.29 | 62.590, 11.203 | 50 | 100 | 68 | 0 | Røros 84; Os 80 |
| 158 | 61.145–61.245 | 8.88–9.31 | 61.201, 9.105 | 100 | 100 | 76 | 0 | Øystre Slidre 158 |
| 157 | 61.125–61.240 | 10.52–10.82 | 61.177, 10.717 | 100 | 100 | 63 | 82 | Ringsaker 119; Lillehammer 35; Øyer 2 |
| 149 | 61.035–61.200 | 9.30–9.62 | 61.115, 9.481 | 100 | 100 | 80 | 0 | Nord-Aurdal 64; Etnedal 55; Øystre Slidre 30 |
| 131 | 61.620–61.785 | 9.62–9.95 | 61.731, 9.783 | 100 | 100 | 85 | 0 | Nord-Fron 97; Sel 18; Sør-Fron 16 |
| 130 | 60.970–61.085 | 9.17–9.39 | 61.040, 9.296 | 100 | 100 | 91 | 0 | Nord-Aurdal 107; Øystre Slidre 23 |
| 125 | 62.000–62.125 | 9.78–10.12 | 62.069, 9.957 | 100 | 100 | 65 | 0 | Folldal 93; Dovre 30 |
| 114 | 62.525–62.665 | 11.93–12.32 | 62.620, 12.103 | 0 | 43 | 66 | 100 | Sweden 65; Røros 49 |
| 106 | 61.435–61.545 | 9.55–9.78 | 61.505, 9.665 | 100 | 100 | 83 | 0 | Nord-Fron 76; Sør-Fron 30 |
| 105 | 60.440–60.545 | 8.77–9.03 | 60.500, 8.869 | 0 | 100 | 77 | 0 | Nesbyen 77; Nore og Uvdal 28 |
| 105 | 62.520–62.605 | 10.05–10.31 | 62.555, 10.171 | 97 | 100 | 59 | 0 | Tynset 102; Rennebu 3 |
| 95 | 62.140–62.245 | 9.59–9.86 | 62.191, 9.727 | 100 | 100 | 89 | 0 | Folldal 83; Dovre 11 |
| 90 | 61.660–61.775 | 10.44–10.64 | 61.710, 10.545 | 100 | 100 | 71 | 100 | Ringebu 60; Stor-Elvdal 30 |
| 90 | 62.230–62.345 | 8.67–8.83 | 62.276, 8.738 | 100 | 100 | 72 | 0 | Lesja 90 |
| 83 | 62.275–62.395 | 10.97–11.37 | 62.346, 11.138 | 100 | 100 | 47 | 19 | Tolga 81; Tynset 2 |
| 82 | 61.570–61.680 | 9.76–10.02 | 61.619, 9.860 | 100 | 100 | 87 | 13 | Nord-Fron 45; Sør-Fron 37 |
| 82 | 62.210–62.295 | 10.18–10.42 | 62.255, 10.310 | 100 | 100 | 66 | 0 | Folldal 53; Alvdal 22; Tynset 4 |
| 80 | 61.485–61.575 | 9.18–9.28 | 61.519, 9.226 | 100 | 100 | 75 | 0 | Nord-Fron 73; Sel 4 |
| 77 | 62.550–62.645 | 10.83–10.98 | 62.601, 10.905 | 100 | 100 | 65 | 0 | Os 77 |
| 73 | 61.335–61.400 | 11.44–11.55 | 61.370, 11.498 | 100 | 100 | 64 | 100 | Åmot 73 |
| 71 | 62.440–62.530 | 10.72–10.85 | 62.486, 10.777 | 100 | 100 | 75 | 0 | Tolga 71 |
| 70 | 62.730–62.805 | 10.99–11.14 | 62.763, 11.059 | 0 | 100 | 60 | 0 | Holtålen 70 |
| 68 | 62.050–62.130 | 10.32–10.44 | 62.093, 10.375 | 100 | 100 | 75 | 0 | Alvdal 68 |
| 64 | 61.235–61.305 | 10.60–10.76 | 61.279, 10.704 | 100 | 100 | 62 | 83 | Øyer 62 |
| 60 | 62.690–62.765 | 12.45–12.58 | 62.729, 12.506 | 0 | **0** | 60 | 100 | Sweden 60 |
| 58 | 62.615–62.655 | 11.46–11.56 | 62.633, 11.510 | 0 | 100 | 60 | 3 | Røros 58 |
| 58 | 62.650–62.735 | 11.26–11.35 | 62.692, 11.309 | 0 | 100 | 79 | 0 | Røros 55; Holtålen 3 |
| 56 | 59.945–60.000 | 9.04–9.22 | 59.974, 9.121 | 0 | 100 | 66 | 100 | Rollag 54; Tinn 2 |
| 56 | 60.610–60.655 | 8.60–8.91 | 60.628, 8.744 | 0 | 100 | 62 | 0 | Ål 41; Nesbyen 9; Gol 6 |
| 55 | 62.130–62.205 | 10.78–10.88 | 62.169, 10.831 | 100 | 100 | 67 | 56 | Tynset 55 |
| 54 | 61.900–61.980 | 11.42–11.52 | 61.941, 11.454 | 100 | 100 | 63 | 100 | Rendalen 54 |
| 53 | 60.260–60.340 | 8.96–9.08 | 60.302, 9.030 | 0 | 100 | 94 | 0 | Nore og Uvdal 53 |
| 52 | 61.590–61.640 | 10.00–10.16 | 61.612, 10.081 | 100 | 100 | 96 | 83 | Ringebu 52 |
| 50 | 62.410–62.450 | 10.58–10.74 | 62.432, 10.654 | 100 | 100 | 84 | 0 | Tolga 36; Tynset 14 |

**Coarse blocks, 0.25° lat × 0.5° lon, 810–891 m (top 10).**
| Block | Points |
|---|---|
| 60.75–61.00 N, 9.0–9.5 E | 534 |
| 61.00–61.25 N, 9.5–10.0 E | 457 |
| 61.25–61.50 N, 10.0–10.5 E | 440 |
| 60.75–61.00 N, 8.5–9.0 E | 439 |
| 60.50–60.75 N, 9.0–9.5 E | 416 |
| 61.00–61.25 N, 9.0–9.5 E | 384 |
| 62.50–62.75 N, 11.0–11.5 E | 363 |
| 61.50–61.75 N, 9.5–10.0 E | 350 |
| 60.75–61.00 N, 9.5–10.0 E | 325 |
| 61.50–61.75 N, 9.0–9.5 E | 290 |

**Community-focus municipalities (790–911 m points / 810–891 m points / with SE road / community-open).**

| Municipality | 790–911 | 810–891 | SE road | Open |
|---|---|---|---|---|
| Løten | 1 | 0 | 0 | 0 |
| Hamar | 0 | 0 | 0 | 0 |
| Stange | 0 | 0 | 0 | 0 |
| Elverum | 0 | 0 | 0 | 0 |
| Åmot | 132 | 101 | 60 | 101 |
| Ringsaker | 250 | 187 | 120 | 187 |
| Gjøvik | 0 | 0 | 0 | 0 |
| Østre Toten | 1 | 0 | 0 | 0 |
| Vestre Toten | 0 | 0 | 0 | 0 |
| Stor-Elvdal | 608 | 409 | 260 | 336 |
| Øyer | 479 | 328 | 240 | 108 |
| Lillehammer | 178 | 111 | 80 | 9 |
| Trysil | 267 | 170 | 106 | 170 |
| Rendalen | 690 | 470 | 265 | 470 |
| Engerdal | 416 | 270 | 138 | 270 |
| Våler, Åsnes, Grue, Nord-Odal, Sør-Odal, Kongsvinger, Eidskog | 0 | 0 | 0 | 0 |

**Caveats.**
- Each value is a single DTM sample at the cell centre. A 0.3 km² cell with a steep slope can contain 810–891 m ground even when its centre sample is outside the band, and the reverse. The band 790–911 partly absorbs this.
- The OSM road classes and the exact SE bearing window are undocumented.
- The Innlandet polygon is simplified (200 vertices), so border cells may be misassigned.
- The 427 Swedish points must be dropped.

**Decode recipe.**
```python
import json, numpy as np
d = json.load(open('/home/user/test/data/raw/magnus/public/data/hoyde891.json'))
a = np.array(d['punkter'], float)          # columns: lat, lon, moh, road_m, se
lat, lon, moh, road_m, se = a.T
cells = [((la - d['dlat']/2, lo - d['dlon']/2), (la + d['dlat']/2, lo + d['dlon']/2)) for la, lo in a[:, :2]]  # cell bounds as in Kart.tsx:523-526
band = (moh >= 810) & (moh <= 891)
# drop points outside Norway:
from shapely.geometry import shape, Point; from shapely.prepared import prep
no = prep(shape(json.load(open('/home/user/test/data/raw/magnus/public/data/norge.json'))['geometry']))
in_no = np.array([no.contains(Point(x, y)) for y, x in zip(lat, lon)])
```

### 2.2 `treslag.json`: NIBIO SR16 tree-species shares versus «35 % bjørk, 25 % gran, 40 % furu»

**Primary evidence [P, whiteboard].** Magnus mirror image `public/img/tavle-2509-treslag.jpg`. The overlay stamp reads «2026-09-25 18:13:23» with a "TavlAI" label; which clock that stamp uses is not stated. The whiteboard text, as I read it from the image, is:

> «KANSKJE / 35% BJØRK / 25% GRAN / 40% FURU / AKKURAT RUNDT MEG»

The same text is in `src/data/innhold.ts:233-240` (id `treslag`, «Anja skrev kl. 18:13»). Note that she writes «KANSKJE» (maybe).

**Provenance.** Commit ae6dc67, 25.09 19:19: "Share of pine, spruce and deciduous per ~2×2 km cell, counted from NIBIO's SR16 dominant-species map (96 WMS tiles over Eastern Norway), scored against 40/25/35". The layer text at `src/data/lag.ts:689-702` gives the source as «NIBIO: SR16 skogressurskart (dominerende treslag), hentet 25.09.2026», and adds «SR16 viser treslaget som dominerer i hver bestand, så andelene er grove». The display classes are in `src/lib/treslag.ts:12-16`: ≥0.85 «Svært lik», 0.75–0.85 «Lik», 0.65–0.75 «Litt lik». Cells below 0.65 are not drawn.

**Schema.** `{mal: {furu: 0.4, gran: 0.25, lauv: 0.35}, dlat: 0.02, dlon: 0.04, kilde: "NIBIO SR16 (dominerende treslag), hentet 25.09.2026", celler: [[lat, lon, score, furu, gran, lauv], …]}` with 4,139 cells. The loader type is at `src/lib/treslag.ts:7`.

| Field | Meaning | Distribution (p5/25/50/75/95) |
|---|---|---|
| lat, lon | Cell centre on a 0.02° × 0.04° grid (about 2.2 km × 2.2 km), 120 × 77 nodes | lat 59.81–62.19, lon 9.82–12.86 |
| score | Similarity to the target. Reverse-engineered exactly as **1 − ½·(\|f−0.40\| + \|g−0.25\| + \|l−0.35\|)** = Σ min(share, target). Max abs error 0.01 (rounding) | 0.55–0.98; 0.56/0.62/0.66/0.695/0.82 |
| furu | Share of forest pixels whose dominant species is pine | 0.00–0.85; 0.08/0.31/0.44/0.60/0.80 |
| gran | Share with spruce dominant | 0.00–0.70; 0.12/0.31/0.46/0.58/0.68 |
| lauv | Share with deciduous (mostly birch) dominant | 0.00–0.80; 0.00/0.01/0.04/0.17/0.48 |

The three shares sum to 0.99–1.01. **Only cells with score ≥0.55 are stored** (4,139 of 9,240 grid nodes), so a missing cell means score <0.55, no forest, or outside Norway.

**What drives the score.** The correlation between score and lauv is +0.32, with gran −0.29, and with furu ≈0. Cells scoring ≥0.85 average furu 0.37, gran 0.29, lauv 0.33. Only 719 cells have lauv ≥0.25. Because SR16 records the *dominant* species per stand, birch that grows mixed in pine or spruce stands is invisible. A 35 % deciduous target therefore selects birch-dominated landscapes: lowland deciduous forest (Ringerike, Modum, Øvre Eiker, the Oslo fringe) and the **subalpine birch belt** (Alvdal, Tynset, Rendalen, Engerdal, Stor-Elvdal).

This works against `utelukket.json`, which excludes "fjellbjørk" (mountain birch):
| Community map class | Cells | Mean score | Share ≥0.75 | Share ≥0.85 |
|---|---|---|---|---|
| Open | 2,428 | 0.668 | 13.6 % | 3.5 % |
| R | 421 | 0.699 | 27.1 % | 5.2 % |
| C | 1,290 | 0.658 | 8.1 % | 1.1 % |

**Counts.**
| Threshold | All cells | In Innlandet |
|---|---|---|
| ≥0.65 | 2,775 | 2,063 |
| ≥0.75 | 549 | 360 |
| ≥0.85 | 122 | 69 |
| ≥0.90 | 53 | 28 |
| ≥0.95 | 15 | 6 |

**Best-matching cells** (score, furu/gran/lauv, municipality and its Vercel verdict):
- 60.25, 11.70: 0.98 (0.42/0.23/0.35), Sør-Odal, usikkert
- 60.19, 10.22: 0.98, Ringerike, utelukket
- 61.57, 9.86: 0.98 (0.40/0.27/0.33), Sør-Fron, usikkert
- 62.11, 10.98: 0.98 (0.38/0.25/0.37), Rendalen, usikkert
- 60.19, 10.18: 0.97, Ringerike
- 60.11, 10.26: 0.97, Hole
- 62.19, 10.54: 0.96, Alvdal
- 59.95, 9.82: 0.96, Modum
- 60.21, 10.34: 0.96, Ringerike
- 60.11, 10.14: 0.95, Ringerike
- 62.11, 10.70: 0.95, Alvdal
- 62.19, 11.02: 0.95, Tynset
- 60.03, 10.02: 0.95, Modum
- 60.01, 10.02: 0.95, Modum
- 59.85, 10.82: 0.95, Oslo
- 59.93, 9.94: 0.94, Modum
- 61.83, 10.54: 0.94, Stor-Elvdal
- 62.15, 10.86: 0.94, Tynset
- 60.25, 12.06: 0.94, Kongsvinger
- 62.03, 12.02: 0.94, Engerdal
- 62.05, 11.98: 0.93, Engerdal
- 61.21, 11.10: 0.93 (0.33/0.26/0.42), Åmot
- 61.77, 12.10: 0.93, Engerdal
- 59.95, 12.22: 0.93, Eidskog
- 61.75, 12.14: 0.93, Engerdal
- 61.55, 11.02: 0.91, Stor-Elvdal
- 61.83, 10.58: 0.91, Stor-Elvdal
- 60.57, 12.06: 0.91, Åsnes
- 61.59, 9.82: 0.91, Nord-Fron
- 61.83, 10.62: 0.91, Stor-Elvdal
- 61.81, 10.42: 0.90, Stor-Elvdal
- 62.07, 11.10: 0.90, Rendalen
- 61.53, 11.06: 0.90, Stor-Elvdal
- 61.73, 11.90: 0.90, Engerdal
- 62.03, 12.18: 0.90, Engerdal
- 60.23, 11.62: 0.90, Sør-Odal
- 60.83, 11.38: 0.89, Løten
- 60.59, 11.94: 0.89, Åsnes
- 61.73, 9.94: 0.89, Sør-Fron
- 60.61, 11.90: 0.88, Våler

**Clusters of cells scoring ≥0.75** (8-connected, 189 clusters, largest first):
| n | Area | Municipalities | Max score |
|---|---|---|---|
| 58 | 59.91–60.31 N, 9.82–10.38 E | Ringerike / Modum / Hole (excluded or lite sannsynlig) | 0.98 |
| 27 | 60.61–60.87 N, 11.18–11.38 E | Stange 14, Løten 11 (the Løten–Stange forest) | 0.89 |
| 17 | 59.91–60.05 N, 11.30–11.58 E | Aurskog-Høland, Lillestrøm, Nes | |
| 15 | 62.11–62.19 N, 10.74–11.06 E | Tynset | 0.95 |
| 13 | 62.09–62.19 N, 10.34–10.58 E | Alvdal | 0.96 |
| 11 | 59.81–59.87 N, 9.82–9.94 E | Øvre Eiker | |
| 11 | 59.93–60.01 N, 12.06–12.22 E | Eidskog | |
| 10 | 61.73–61.79 N, 10.94–11.06 E | Rendalen / Stor-Elvdal | 0.86 |
| 9 | 60.21–60.25 N, 9.86–10.10 E | Ringerike | |
| 8 | 60.53–60.65 N, 11.86–11.98 E | Åsnes / Våler | |
| 7 | 61.49–61.61 N, 12.34–12.42 E | Trysil | |
| 7 | 61.75–61.81 N, 11.98–12.14 E | Engerdal | |

**Caveats.**
- Coverage stops at 9.82 E and 62.19 N, which is **58.8 % of Innlandet** (30,607 of 52,084 km²). Valdres, Gausdal-west, Vågå, Lom, Lesja and Folldal-north have no data.
- There are 3,999 hoyde891 points at 810–891 m in Innlandet within the treslag bounding box, but only 1,881 of them have a stored score. The rest scored <0.55 or have no forest.
- The scale does not match: her estimate is «AKKURAT RUNDT MEG» (tens of metres), while each cell is about 5 km².

**Decode recipe.**
```python
t = json.load(open('/home/user/test/data/raw/magnus/public/data/treslag.json'))
c = np.array(t['celler'])   # lat, lon, score, furu, gran, lauv
recomputed = 1 - 0.5*(abs(c[:,3]-.40) + abs(c[:,4]-.25) + abs(c[:,5]-.35))   # == c[:,2] within 0.01
lookup = {(round(r[0],2), round(r[1],2)): r for r in c}   # key = cell centre; nearest centre: lat0 + round((la-lat0)/0.02)*0.02 with lat0=59.81, lon0=9.82
```

### 2.3 `drivetime.json` and `scripts/build_drivetime.py`: OSRM drive time from Oslo

**Provenance.** Commit c0c849b, 23.09 14:30, "Scaffold … with drive-time data" and "Add build script for the drive-time grid (scripts/build_drivetime.py)". The layer text is at `src/data/lag.ts:185-202`, with the source given as «OSRM (router.project-osrm.org), beregnet 23.09». It says: «Grå ruter ligger mer enn 3 km fra nærmeste bilvei. OSRM regner ofte litt tregere enn Google, så se på tallene som ±30 min. Anja sov og vet ikke hvor lenge de kjørte».

**How the script works** (`/home/user/test/data/raw/magnus/scripts/build_drivetime.py`):
- It is run as `python scripts/build_drivetime.py <fylker.geojson>`. The county file it needs is not in the repo.
- It unions the counties with `make_valid(...).buffer(0)` and tests grid points against the prepared union.
- Origin: `OSLO = (10.7522, 59.9139)` (lon, lat), which is Oslo sentrum.
- Grid: `LAT0, LAT1, DLAT = 57.9, 66.0, 0.1`; `LON0, LON1, DLON = 4.6, 15.2, 0.2`. That is 4,428 nodes, and only the 1,873 inside Norway are kept.
- It sends batches of `CHUNK = 99` destinations to `https://router.project-osrm.org/table/v1/driving/{Oslo;pts}?sources=0&annotations=duration,distance`, with 5 retries and a 1.2 s pause between batches.
- Each output row is `[lat, lon, round(duration s), round(distance m), round(destinations[j].distance)]`. The last value is **snap_m**, the distance from the grid point to the road point OSRM snapped it to.
- Coordinates are rounded to 2 decimals.
- It writes `data/drivetime.json` (under ROOT/data, not public/data), so the file was moved by hand. It also writes `norge.json`: the union simplified with `simplify(0.01, preserve_topology=True)`, polygons with area ≤0.002 deg² dropped, and coordinates rounded to 3 decimals.
- A comment says «Kun Sør-Norge + Midt-Norge er relevant for kjøretid < ~10 t», but the grid still runs to 66.0 N.

**Schema.** `{kilde: "OSRM (router.project-osrm.org), bil, fra Oslo sentrum", origo: [59.9139, 10.7522], dlat: 0.1, dlon: 0.2, felt: ["lat","lon","sek","meter","snap_m"], punkter: [...]}` with 1,873 points. `sek` is never null. The App maps it to `{lat, lon, sek, meter, snap}` (`src/App.tsx:90-93`).

**Distributions.**
- Extent: lat 58.1–66.0, lon 4.8–14.6.
- Hours: min 0.09, p5 1.48, p25 3.67, median 5.91, p75 8.11, p95 12.99, max 19.75.
- Route length: 4.3–1,032.7 km (median 363.7).
- snap_m: median 713 m, p75 2,180 m, p95 7,673 m, max 22,558 m. 632 points have snap >1,500 m and 363 have snap >3,000 m.
- Histogram (hours, number of points):

| 0–1 | 1–2 | 2–3 | 3–4 | 4–5 | 5–6 | 6–7 | 7–8 | 8–9 | 9–11 | 11–20 |
|---|---|---|---|---|---|---|---|---|---|---|
| 37 | 146 | 163 | 196 | 201 | 214 | 220 | 211 | 159 | 110 | 216 |

- **Innlandet (433 points):** 1.27–6.86 h, median 3.79. Histogram: 1–2 h 48, 2–3 h 93, 3–4 h 90, 4–5 h 104, 5–6 h 79, 6–7 h 19, ≥7 h 0. 53 points have snap >3 km.
- There are 696 points at ≥7 h and 221 at 6.5–7.5 h, mostly western Norway, Trøndelag and Nordmøre.
- **Reference places** (nearest grid node):

| Place | Grid node | Hours | km |
|---|---|---|---|
| Hamar | (60.8, 11.0) | 1.69 | 131 |
| Løten | (60.8, 11.4) | 1.71 | 126 |
| Elverum | (60.9, 11.6) | 1.89 | 145 |
| Rudshøgda | | 1.82 | 146 |
| Gjøvik | | 2.10 | 125 |
| Rena | (61.1, 11.4) | 2.38 | 171 |
| Lillehammer | | 2.48 | 183 |
| Sjusjøen | | 2.58 | 179 (snap 1,441 m) |
| Trysil | | 3.07 | 213 |
| Koppang | (61.6, 11.0) | 3.32 | 232 |
| Fagernes | | 3.46 | 195 |
| Beitostølen | | 3.71 | 217 |
| Froland | | 3.78 | 271 |
| Tynset | | 4.78 | 320 |
| Røros | | 5.67 | 374 |
| Norheimsund | | 6.47 | 376 |
| Bergen | | 8.11 | 467 |

- For hoyde891 points at 810–891 m in Innlandet (nearest drive node): 2.08–7.19 h, median 3.79 h.

**Primary context [P, whiteboard, and news interview].** From `src/data/innhold.ts:112-122` (id `reise`):
- Whiteboard, 21.09 18:31: «INGEN FLY · INGEN SKYTING · OSLO, SØN KL 04.00 · CA 5–10 MIN Å GÅ FRA BIL» (`innhold.ts:882`).
- Børsen reports she slept most of the trip, «aner ikke hvor lenge de kjørte», and thinks it was about 7 hours.
- The site flags this as an open question: «tavla sier søndag, men Børsen skriver … "siden mandag morgen"».

A literal 7 h drive does not fit Innlandet, whose maximum is 6.86 h. The magnus model defaults the drive-time weight to 0 (`src/lib/modell.ts:50,56`).

**How the model uses it** (`src/lib/modell.ts`):
- `vei = 1` if snap ≤1,500 m, otherwise `exp(-(snap-1500)/2000)` (line 123).
- `kjoretid = gauss(sek/3600 − timer, slingring)` (line 153).
- Grey cells in the drive-time layer are snap >3,000 m (`src/components/Kart.tsx:98-104`).

**Decode recipe.**
```python
d = json.load(open('/home/user/test/data/raw/magnus/public/data/drivetime.json'))
a = np.array(d['punkter'], float)        # lat, lon, sek, meter, snap_m
hours = a[:,2]/3600; km = a[:,3]/1000; snap = a[:,4]
# cell = lat±0.05, lon±0.1 (Kart.tsx HALV_LAT/HALV_LON)
```

### 2.4 `fly_2130.json`: ADS-B tracks around the 21.09 «FLY» moment

**Provenance.** Commit ecf0260, 23.09 14:42, "Add 49 aircraft tracks around 21:29". `kilde: "ADS-B fra adsb.lol, hentet ut av default.no (event_planes.json)"`, `tid: "ekte tid 21.09, CEST"`, `felt: ["tid","lat","lon","fot"]`. The loader is `src/lib/fly.ts`, whose line 1 says «Tider i sporet er ekte tid (CEST)». The rendering is in `src/components/Kart.tsx:457-496`.

**Primary evidence [P].**
- Whiteboard log `src/data/innhold.ts:894`: `{ t: '21.09 21:30', tekst: 'FLY (pekte opp, litt mot sørøst)' }`. The part in parentheses is the site's own description of her gesture, not text on the whiteboard.
- The hint card (`innhold.ts:742-751`): «Anja pekte rett opp kl. 21:29:38 og skrev «FLY» kl. 21:30 (streamtid)».
- `src/lib/fly.ts:12-14`: «Anja pekte opp 21:29:38 og skrev «FLY» 21:30:12–21:30:30 (streamtid)». It sets `PEKETID_EKTE = '21:29:15'` and `VINDU_SEK = 60`.
- **Competing reading** [C, from `mk_bevis/.../README.md`, adsb section, citing default.no osint_notes]: «kl. 21:27:42 signaliserte hun et stjerneskudd, og kl. 21:29:10 ba chatten henne peke dit. Pekingen 21:29:38–53 kan altså gjelde stjerneskuddet og ikke et fly.»

**Schema.** `fly[]` has 49 entries of `{kallesignal, type, spor: [[hh:mm:ss, lat, lon, fot], …]}`. Every track shares the snapshot labels **21:28:14, 21:29:48, 21:31:16, 21:32:50, 21:34:17**. These are about 88–94 s apart, so linear interpolation is used between them. How many labels each track has: 5 labels for 39 tracks, 4 for 4, 3 for 2, and 2 for 4. `fot` is **barometric** altitude in feet: it matches field 3 of the trace, not alt_geom. Ground aircraft are included with negative or near-zero altitude, for example SAS291 at Bergen (−225 ft) and DOC at 62.463 N 6.312 E.

**Tracks at label 21:29:15** (interpolated). Positions are label-time and, by finding 1, about 46 s early. The magnus app computes these with the same interpolation (`src/lib/fly.ts:17-32`). Course is taken from the first to the last point.

| Callsign | Type | Position at 21:29:15 | Altitude (ft) | Course |
|---|---|---|---|---|
| WIF18H | E290 | 66.726, 13.811 | 41,000 | 35 |
| SAS4124 | A20N | 63.059, 11.734 | 39,041 | 11 |
| SAS4098 | A20N | 63.538, 11.958 | 39,009 | 20 |
| NOZ36S | B738 | 64.569, 12.786 | 39,000 | 20 |
| ICE344 | B38M | 62.095, 15.028 | 37,016 | 106 |
| **NOZ68L** | B738 | **62.350, 11.566** | **37,000** | **6** |
| RYR313 | B738 | 59.325, 11.889 | 37,000 | 77 |
| RYR60WC | B738 | 58.205, 5.586 | 37,000 | 75 |
| SAS71G | A20N | 59.001, 5.358 | 36,984 | 132 |
| NOZ385 | B738 | 62.887, 11.650 | 36,000 | 197 |
| THY29M | A359 | 58.131, 10.137 | 36,000 | 324 |
| SAS4497 | A20N | 65.244, 11.797 | 35,991 | 188 |
| SAS27E | A20N | 64.172, 12.464 | 35,009 | 20 |
| FIN7PW | A321 | 57.744, 4.744 | 35,000 | 62 |
| THY11 | B789 | 61.401, 8.358 | 31,984 | 315 |
| SAS1488 | A20N | 60.209, 12.840 | 28,726 | 99 |
| RANGR91 | C30J | 60.807, 5.130 | 28,000 | 207 |
| WIF9AL | E290 | 61.240, 6.474 | 26,897 | 207 |
| **NOZ9EG** | B738 | **61.2167, 10.8960** | **23,504** | **184** (descending 25,775 → 10,750) |
| SAS4898 | CRJ9 | 60.420, 6.945 | 23,267 | 94 |
| WIF7D | DH8D | 61.944, 6.012 | 22,377 | 213 |
| **NOZ56U** | B738 | **60.8132, 11.2367** | **22,245** | **6** (climbing 19,325 → 32,675) |
| AKK2 | BE20 | 62.678, 11.958 | 21,357 | 345 |
| SAS4189 | E190 | 59.692, 5.180 | 16,842 | 170 |
| SAS1475 | A320 | 59.934, 11.409 | 16,355 | 169 |
| **WIF149** | DH8A | **60.848, 8.921** | **16,000** | **301** |
| WIF5B | DH8D | 59.182, 5.569 | 14,541 | 351 |
| NOZ6TD | B738 | 59.517, 6.668 | 14,162 | 243 |
| WIF1HX | DH8A | 60.355, 10.044 | 14,162 | 119 |
| MOZ866 | CL35 | 63.033, 11.298 | 12,340 | 15 |
| NOZ3ET | B738 | 63.218, 11.415 | 8,682 | 357 |
| SAS380 | A20N | 63.364, 11.525 | 6,015 | 310 |
| NOZ636 | B738 | 60.217, 5.783 | 5,676 | 269 |
| NSZ3234 | B38M | 59.950, 11.015 | 4,920 | 6 |
| BNOV | BE20 | 62.640, 6.478 | 3,472 | 245 |
| SAS80M | A20N | 60.041, 11.030 | 3,158 | 16 |
| HEP01 | A169 | 60.099, 10.485 | 1,976 | 19 |
| LNOZD | R44 | 59.837, 10.362 | 1,800 | 232 |
| WIF12F | DH8D | 63.457, 10.939 | 1,225 | 334 |
| NOZ5BR | B738 | 60.169, 11.104 | 565 | 2 |
| SAS223 | E195 | 58.235, 8.127 | 446 | 217 |
| NOZ386 | B738 | 60.199, 11.084 | 400 | 11 |
| WIF42G | DH8C | 63.457, 10.941 | 300 | 264 |
| DOC51 | EC45 | 65.511, 12.368 | 268 | 60 |
| SAS291 | A20N | 60.294, 5.220 | −225 | 105 |

KLM1226, WIF83M, SAS40G and DOC have no position at 21:29:15.

**Finding 1: the timestamps are shifted.** For each `fly_2130` sample I found when the full-resolution adsb.lol trace passes that point (evidence branch, `mk_bevis/bevis/claude-2026-09-25/adsb/trace_4791ac.json` is NOZ9EG / LN-NIQ, `trace_47a3b0.json` is NOZ56U / LN-ENN; both are gzip JSON in readsb `trace_full` format, about 10 s sampling).

| Aircraft | Label | Label position (ft) | Trace reaches it at | Offset (position / altitude) |
|---|---|---|---|---|
| NOZ9EG | 21:28:14 | 61.3538, 10.9068 (25,775) | 21:29:00.4 | +46.0 / +46.5 s |
| NOZ9EG | 21:29:48 | 61.1425, 10.8901 (22,275) | 21:30:32.6 | +46.5 / +46.5 s |
| NOZ9EG | 21:31:16 | 60.9573, 10.8753 (18,850) | 21:32:01.9 | +46.0 / +46.0 s |
| NOZ9EG | 21:32:50 | 60.767, 10.84 (14,450) | 21:33:33.1 | +45.0 / +45.0 s |
| NOZ9EG | 21:34:17 | 60.5951, 10.8107 (10,750) | 21:35:03.7 | +46.5 / +46.0 s |
| NOZ56U | 21:28:14 | 60.7137, 11.2168 (19,325) | 21:28:58.0 | +46.5 / +46.5 s |
| NOZ56U | 21:29:48 | 60.8671, 11.2475 (23,825) | 21:30:30.9 | +46.5 / +46.5 s |
| NOZ56U | 21:31:16 | 61.0157, 11.2778 (26,800) | 21:32:03.2 | +46.0 / +46.5 s |
| NOZ56U | 21:32:50 | 61.1823, 11.3122 (29,600) | 21:33:32.5 | +45.0 / +45.0 s |
| NOZ56U | 21:34:17 | 61.3382, 11.3437 (32,675) | 21:35:07.8 | +46.0 / +45.5 s |

The mean offset is **+46.0 s (s.d. 0.5 s)**. At the label time itself the trace is 7.4–9.5 km away from the labelled position. The cause is unknown; the labels are probably snapshot times while the positions are ~46 s newer. It may also affect default.no's own aircraft analyses that use `event_planes.json`.

As a result, the app's constants are too late along each track:
- `FLY_PUNKT` (`innhold.ts:1167-1168`, «Der NOZ56U var da Anja skrev «FLY» (ekte tid ca. 21:29:50)», pos 60.8705, 11.2481, 23,892 ft) is really where NOZ56U was at about 21:30:36.
- `FLY_PUNKT2` (`innhold.ts:1177-1178`, NOZ9EG «ca. 21:29:15», 61.216, 10.896, 23,500 ft) is really where NOZ9EG was at about 21:30:01.

**True positions from the traces** (interpolated; baro / geometric altitude in ft):

| Real time | NOZ9EG | NOZ56U |
|---|---|---|
| 21:28:38 (60 s delay) | 61.4045, 10.9106 (26,619 / 27,420) | 60.6775, 11.2096 (18,132 / 18,536) |
| 21:28:53 (45 s) | 61.3697, 10.9080 (26,047 / 26,846) | 60.7019, 11.2144 (18,924 / 19,343) |
| 21:29:00 | 61.3537, 10.9068 | 60.7133, 11.2167 |
| 21:29:08 (30 s) | 61.3354, 10.9054 (25,508 / 26,242) | 60.7264, 11.2193 (19,733 / 20,193) |
| 21:29:15 | 61.3194, 10.9042 (25,235 / 25,960) | 60.7378, 11.2216 (20,115 / 20,590) |
| 21:29:16 (22 s) | 61.3171, 10.9040 (25,195 / 25,920) | 60.7394, 11.2220 (20,180 / 20,655) |
| 21:29:23 (15 s) | 61.3012, 10.9027 (24,930 / 25,655) | 60.7509, 11.2243 (20,652 / 21,127) |
| 21:29:38 (0 s) | 61.2673, 10.9000 | 60.7750, 11.2291 |
| 21:29:50 | 61.2406, 10.8979 | 60.7946, 11.2330 |
| 21:30:00 | 61.2183, 10.8961 | 60.8108, 11.2362 |

These agree with the evidence branch's own result at 22 s: «NOZ9EG … 61.317 N 10.904 E, 25920 ft geom» and «NOZ56U … 60.739 N 11.222 E, 20655 ft geom» (`mk_bevis/.../adsb/fly_2109_resultat.txt`).

**Radius for a given elevation angle** (horizontal distance at which the aircraft is at that angle above the horizon, at the 22 s delay):
- NOZ9EG: ≥60° within 4.6 km, ≥45° within 7.9 km.
- NOZ56U: ≥60° within 3.6 km, ≥45° within 6.3 km.

**Decode recipe** (with the correction):
```python
f = json.load(open('/home/user/test/data/raw/magnus/public/data/fly_2130.json'))
def sek(s): h,m,x = map(int, s.split(':')); return h*3600+m*60+x
OFFSET = 46   # s; label + 46 s = true time (verified for NOZ9EG, NOZ56U only)
def pos(fl, true_hms):
    t = sek(true_hms) - OFFSET; s = fl['spor']
    for a, b in zip(s, s[1:]):
        ta, tb = sek(a[0]), sek(b[0])
        if ta <= t <= tb:
            k = 0 if tb == ta else (t-ta)/(tb-ta)
            return [a[i] + k*(b[i]-a[i]) for i in (1, 2, 3)]   # lat, lon, baro ft
# Better: for NOZ9EG/NOZ56U use the raw traces: json.loads(gzip.decompress(open(p,'rb').read())); t = j['timestamp']+row[0]; lat=row[1]; lon=row[2]; baro=row[3]; geom=row[10]
```

### 2.5 `fellesskap891.json`: the community's 800–900 moh map

**Provenance.** Commit b03c6a9, 24.09 18:32, "the community's 800–900 moh map (georeferenced)". `kilde`: «Fellesskapets kart 24.09: 800–900 moh OG flyene passer OG skog OG utenfor skytefelt. Stedfestet fra bilde, ca. ±500 m.» The layer text is at `src/data/lag.ts:666-675`: «Det meste ligger vest for Rena, mellom Rena og Evenstad/Koppang», with the source «Delt i chatten 24.09». The original image is not in the repo.

**Schema.** `{kilde, dlat: 0.005, dlon: 0.01, celler: [[lat, lon], …]}` with 634 cells, drawn as 0.005° × 0.01° rectangles (`src/components/Kart.tsx:584-599`). There is no value field, only presence. The grid is aligned with hoyde891.

**Extent.** 61.16–61.58 N, 10.72–11.19 E, centroid 61.339, 10.916. The densest 0.1° × 0.2° blocks:
| Block (lower-left corner) | Cells |
|---|---|
| 61.4 N, 10.8 E | 95 |
| 61.5 N, 10.8 E | 94 |
| 61.2 N, 11.0 E | 76 |
| 61.3 N, 11.0 E | 55 |
| 61.1 N, 11.0 E | 52 |
| 61.3 N, 10.8 E | 52 |
| 61.1 N, 10.8 E | 50 |

The kommuner are Ringsaker, Stor-Elvdal and Øyer.

**Agreement with hoyde891.**
- 144 of the 634 cells coincide exactly with a hoyde891 point; 107 coincide with one at 810–891 m.
- Distance from each community cell to the nearest hoyde891 790–911 m point: median 1.07 km, p75 1.70 km, p90 2.73 km, max 9.16 km. 274 cells are within 0.6 km and 371 within 1.2 km.
- There is no clear systematic shift. The best shift on the grid only raises the overlap from 144 to 182.
- Where the two do coincide: heights 791–910 m (median 866 m), road distance 6–897 m (median 367 m).
- Most likely the community map did not require a road within 900 m, and/or its georeferencing error is larger than ±500 m. **[C]**

**Decode.** `cells = np.array(json.load(open(p))['celler'])` gives lat/lon centres of 0.005° × 0.01° cells.

### 2.6 `utelukket.json`: community exclusion map (red = excluded, light blue = mountain birch)

**Provenance.**
- 6763e06, 23.09 19:08: "Georeference the shared exclusion map and store it as a 0.05° grid". The first version also had a pink «ingen sopp» (no mushrooms) class.
- **Correction:** b55eafc, 23.09 19:13: "Remove the pink "no mushrooms" exclusion, which was not correct". The hint card says «(Det rosa «ingen sopp»-laget er tatt ut, det var ikke korrekt.)» (`src/data/innhold.ts:456`).
- fc71636, 23.09 20:03: "Fill Norwegian land west of 8.4° E with red cells, since the image never covered it".

`kilde`: «Fellesskapets utelukkingskart 23.09: rødt = utelukket, lyseblått = fjellbjørk. Stedfestet fra bilde, ca. ±10 km. Vest for bildet (vest for 8,4° Ø) er fylt inn som utelukket.» The layer text (`src/data/lag.ts:676-688`) says: «Det som står igjen er stripa Hamar–Løten–Rena–Koppang, Ringsakfjellet/Rudshøgda og Gjøvik/Toten … Bildet dekket bare Østlandet».

**Schema.** `{kilde, dlat: 0.05, dlon: 0.1, celler: [[lat, lon, 'R'|'C'], …]}` with 5,166 cells: R 4,843, C 323. Only excluded cells are listed; anything absent is open. The model looks cells up with `utelukkNokkel = round(lat/0.05)*0.05 (2 dp), round(lon/0.1)*0.1 (1 dp)` (`src/lib/modell.ts:119`). The model factor is `1 − (excluded among centre + 4 neighbours)/5` (`modell.ts:137-143`). Cells are drawn as ±0.025° / ±0.05° (`src/components/Kart.tsx:497-513`).

**Extent.**
- All cells: 58.0–63.3 N, 4.6–12.6 E.
- C: 60.0–61.7 N, 9.9–12.6 E. The largest groups are 60.0–60.5 N 11–12 E (70), 60.0–60.5 N 12–13 E (47), 61.0–61.5 N 10–11 E (62), 60.5–61.0 N 12–13 E (45), 60.5–61.0 N 11–12 E (39), 61.0–61.5 N 12–13 E (31).
- 445 listed cells fall on sea or outside `norge.json`.

**Open land.** Norway-land nodes on the 0.05° × 0.1° lattice from 58.0–63.3 N, 4.6–12.6 E:
- 5,988 land cells: 1,267 open, 319 C, 4,402 R.
- Open cells span 58.3–63.0 N, 8.4–12.6 E. 683 of them are in Innlandet.
- Open cells by kommune: Rendalen 107, Engerdal 73, Trysil 62, Stor-Elvdal 62, Røros 48, Ringerike 45, Åmot 45, Ringsaker 36, Ringebu 35, Notodden 31, Larvik 28, Gran 26, Skien 25, Søndre Land 24, Kongsberg 23, Stange 23, Tinn 21, Flesberg 20, Østre Toten 20, Gjøvik 19, Modum 17, Alvdal 17, Os 17, Hamar 14, Tolga 14, Løten 8, Tynset 8, and others.
- The largest connected open area covers 1,154 cells (58.95–62.85 N, 8.7–12.6 E). The others are Agder (58 cells: Froland 12, Grimstad 10, Åmli 9 …), Aurskog-Høland/Eidskog (27), Halden (7), Trysil-east (6), and some tiny ones.
- **So the grid leaves open much more than the caption's "strip".** Either the image left those areas uncoloured, or they were outside its frame without being filled in. Only the west-of-8.4 E fill was applied.

The site's derived "open shares" (`innhold.ts:457`) are «Rudshøgda 100 %, Gjøvik 95 %, Rena 93 %, Ringsaker 83 %, Løten 77 %» **[M]**.

**Decode.**
```python
u = json.load(open(p)); ex = {(f"{round(la/0.05)*0.05:.2f}", f"{round(lo/0.1)*0.1:.1f}"): k for la, lo, k in u['celler']}
cls = lambda la, lo: ex.get((f"{round(la/0.05)*0.05:.2f}", f"{round(lo/0.1)*0.1:.1f}"), 'open')
```

### 2.7 `kommunevurdering.json`: municipality verdicts from hordejakten.vercel.app

**Provenance.** Commit 1971621, 23.09 19:22. `kilde: "hordejakten.vercel.app, 23.09"`. The layer text is at `src/data/lag.ts:738-751`: «Hver kommune vurdert av administratoren på hordejakten.vercel.app, et uavhengig fanprosjekt … Ingen kommune er satt til «sannsynlig» ennå. Hentet 23.09.» This is a third party's **[I]**.

**Schema.** A GeoJSON FeatureCollection of 350 MultiPolygon features with `properties: {navn, v}`, where `v` is one of `utelukket` (164), `lite sannsynlig` (123) or `usikkert` (63). Coordinates have 3 decimals, 16,692 vertices in total. Norway has 357 municipalities, so about 7 appear to be missing (not checked).

**Verdicts.**
- `usikkert` (63): Alvdal, Bamble, Dovre, Drangedal, Eidskog, Elverum, Engerdal, Etnedal, Folldal, Fyresdal, Gausdal, Gjøvik, Gran, Grue, Hamar, Hjartdal, Kongsvinger, Kragerø, Kviteseid, Lesja, Lillehammer, Lom, Løten, Midt-Telemark, Nissedal, Nome, Nord-Aurdal, Nord-Fron, Nord-Odal, Nordre Land, Notodden, Os, Porsgrunn, Rendalen, Ringebu, Ringsaker, Sel, Seljord, Siljan, Skien, Skjåk, Stange, Stor-Elvdal, Søndre Land, Sør-Aurdal, Sør-Fron, Sør-Odal, Tinn, Tokke, Tolga, Trysil, Tynset, Vang, Vestre Slidre, Vestre Toten, Vinje, Vågå, Våler, Åmot, Åsnes, Østre Toten, Øyer, Øystre Slidre.
- **All 46 Innlandet municipalities are `usikkert`,** so the file does not discriminate at all inside Innlandet.
- `lite sannsynlig` includes Røros, Holtålen, Oppdal, Rennebu, Midtre Gauldal, Tydal, Gol, Hemsedal, Ål, Hol, Nesbyen, Flå, Nore og Uvdal, Rollag, Flesberg, Kongsberg, Sigdal, Krødsherad, Modum, Hole, Øvre Eiker, Drammen, Lier, Bergen, Voss, Kvam and others.
- `utelukket` includes all of Agder (including Froland), Oslo, Akershus (Lillestrøm, Ullensaker, Nes, Eidsvoll, Hurdal, Nannestad, Gjerdrum, Nittedal, Lunner, Jevnaker), Ringerike, Østfold, Vestfold coastal municipalities, Rogaland, and Nord-Norge.

**Decode.** Use shapely `shape(f['geometry'])` for each feature, with `f['properties']['navn']` and `f['properties']['v']`.

### 2.8 `vind.json`: model wind at 23.09 17:49

**Primary evidence [P, whiteboard].** 23.09 17:49: «LYDTETT · SOL · VINDSTILLE» (`src/data/innhold.ts:472-478`, 917).

**Provenance.** Commit 01ab80d, 25.09 11:29. `tid: "2026-09-23 17:49"`, `kilde: "open-meteo historisk varsel (10 m)"`. The layer text is at `src/data/lag.ts:752-765`: «Modellvind fra open-meteo (historisk varsel, MET Nordic), hentet 25.09 … Inne i tett skog er det ofte roligere enn modellen sier, så 2–4 m/s er ikke utelukket. Rutene er ca. 22 × 22 km.» The display classes (`src/lib/vind.ts:12-16`) are: <2 m/s «passer med «vindstille»», 2–4 «mulig i le inne i skogen», ≥4 «passer dårlig».

**Schema.** `{tid, dlat: 0.2, dlon: 0.4, kilde, celler: [[lat, lon, wind_ms_10m, gust_ms], …]}` with 449 cells on a 27 × 21 lattice (567 nodes; the rest are presumably sea or outside the query).

**Distributions.**
- Extent: 58.0–63.2 N, 4.8–12.8 E.
- Wind: p0 0.3, p5 0.9, p25 1.9, median 2.7, p75 4.0, p95 7.0, max 14.6 m/s.
- Gust: 1.2 / 2.6 / 4.3 / 5.5 / 7.2 / 11.56 / 19.2 m/s.
- Classes: <2 m/s 128 cells, 2–4 m/s 203, ≥4 m/s 118.
- **In Innlandet** (107 cells): <2: 37, 2–4: 54, ≥4: 16, median 2.4 m/s.
- Reference cells (wind, gust in m/s):

| Place | Cell | Wind | Gust |
|---|---|---|---|
| Hamar / Løten | 60.8, 11.2 | 1.2 | 3.0 |
| Brumunddal / Gjøvik | 60.8, 10.8 | 1.1 | 3.1 |
| Rena | 61.2, 11.2 | 1.2 | 3.9 |
| Elverum | 60.8, 11.6 | 2.0 | 5.5 |
| Sjusjøen | 61.2, 10.8 | 2.7 | 5.5 |
| Koppang | 61.6, 11.2 | 2.7 | 5.1 |
| Tynset | 62.2, 10.8 | 3.3 | 6.5 |

- The NOZ9EG-overhead cluster (61.36–61.41 N, 10.88–10.99 E) falls in a cell with 4.2 m/s, which the app classes as «passer dårlig». Note the scale mismatch: the cell is about 22 km across, while her observation is at one sheltered forest spot. **[M]**

**Decode.** `w = np.array(json.load(open(p))['celler'])` gives columns lat, lon, wind, gust. Each cell is centre ± 0.1° lat and ± 0.2° lon.

### 2.9 `storvilt.json`: Statskog big-game hunting fields (Geonorge)

**Provenance.** Commit bb53374, 25.09 15:47: "Statskog's big-game hunting fields (192 in southern Norway, from Geonorge). Hunters' names and phones are dropped". `kilde: "Statskog: Storviltjaktfelt (Geonorge), hentet 25.09.2026"`.

The layer text (`src/data/lag.ts:703-712`) calls this «fakta», but the exclusion logic is **[I]**: «Elgjakta startet 25.09, og den foregår med rifle. Kassen står ikke i farlig terreng, så områder med elgjakt er lite sannsynlige … Elgjakt på privat grunn finnes ikke som åpne kartdata». The box was placed on or before 21.09, before moose season started, so a hunting field says nothing about where it was placed. At most it is Horde's safety consideration.

**Schema.** A FeatureCollection of 192 features (169 Polygon, 23 MultiPolygon) with `properties: {navn, status}`. `status` is 1.0 for 190 features and NaN for 2 features named «Test», which are junk.

**Statistics.**
- Extent: 58.524–63.419 N, 5.299–12.871 E.
- Total area after union: about 4,665 km² (EPSG:25833). About 2,162 km² of that lies inside Innlandet, which is 4.2 % of Innlandet's 52,084 km².
- Field area: min 1.3, p25 13.4, median 19.3, p75 33.5, max 194.5 km².
- 98 fields have their representative point in Innlandet.
- Largest fields:

| Field | km² | Location |
|---|---|---|
| Dovrefjell Nord elg og hjort | 194.5 | 62.250, 9.405 |
| Kongsvold utmåling elg og hjort | 133.3 | |
| Videdalen | 131.9 | |
| Ljøsnåa Feragen | 131.4 | 62.538, 12.007 |
| Storevatn og Bossfjell | 125.3 | |
| **Messelt villrein** | **110.3** | **61.449, 10.855** |
| Hjortejakt Gjerstad | 110.0 | |
| Hjerkinn Utmåling elg og hjort | 106.9 | |
| Grøndalen | 54.5 | 61.782, 11.602 |

- 262 hoyde891 points at 810–891 m in Innlandet lie inside a field.
- Note that "Messelt villrein" sits right next to the NOZ9EG corridor.

**Decode.** Use `make_valid(shape(f['geometry']))`. It is needed because the raw union raises a GEOS TopologyException at 9.6045 E, 62.2564 N.

### 2.10 `verneomrader_jakt.json`: protected areas classified by hunting rule

**Primary evidence [P, whiteboard].** «INGEN SKYTING», 21.09 18:31 (`innhold.ts:882`). Reading it as "no hunting allowed here" is an **[I]**.

**Provenance.** Commit e96bf5c, 25.09 08:23: "Each verneområde near the search area is classed from its own verneforskrift on Lovdata: all hunting banned, partly banned, allowed or unclear." The layer text is at `src/data/lag.ts:713-737`, with the source «Miljødirektoratet (Naturbase) og verneforskriftene på Lovdata, hentet 24.09.2026». The loader is `src/lib/verneomrader.ts`.

**Schema.** A FeatureCollection of 862 features (774 Polygon, 88 MultiPolygon). `properties: {navn, verneform, jakt: 'forbudt'|'delvis'|'tillatt'|'ukjent', setning (quoted sentence from the regulation), url (lovdata)}`.
- `jakt`: tillatt 670, delvis 102, forbudt 45, ukjent 45.
- `verneform`: Naturreservat 676, Naturminne 78, Landskapsvernomraade 54, Dyrefredningsomrade 14, Nasjonalpark 12, Biotopvern 6, Plantefredningsomraade 6, BiotopvernVilt 5, Dyrelivsfredning 4, LandskapsvernomraadePlantelivsfredning 3, Plantelivsfredning 2, one each of the others.
- Extent: 59.639–62.977 N, 7.309–12.825 E.

**Areas by class** (union, km²; the part inside Innlandet in brackets): forbudt 107.1 (37.2); delvis 824.7 (748.9); tillatt 19,618.7 (10,929.2); ukjent 36.5 (28.9).

**`forbudt` areas are tiny wetlands, deltas and Oslo-fjord islets**, which fits poorly with dry pine heath and «INGEN VANN ELLER VANNLYDER» (22.09 19:19). The largest are:

| Area | km² | Location | Regulation sentence |
|---|---|---|---|
| Nordre Øyeren NR | 62.6 | | «I reservatet er all jakt forbudt.» |
| Lågendeltaet NR | 7.03 | 61.111, 10.445 | |
| Åkersvika NR | 4.26 | 60.787, 11.103 | |
| Gjesåssjøen | 4.16 | | |
| Dokkadeltaet | 3.73 | | |
| Totenvika | 3.24 | | |
| Seimsjøen | 3.22 | | |
| Vikersund-Bergsjø | 3.12 | | |
| Risheimøyi | 2.22 | | |
| Hundorp | 1.63 | | |
| Gardsjøen | 1.21 | | |
| Jarenvatnet | 1.05 | | |
| Lomendeltaet | 0.96 | | |
| Trettenstryka | 0.93 | | |
| Svennesvollene NR | 0.72 | 60.968, 10.614 | |
| Våletjern NR | 0.12 | 60.708, 11.219 | |
| Tuftelia NR | 0.07 | 60.677, 8.745 | «All jakt er forbudt.» |

About 25 of the 45 are Oslo-area islets and shore reserves.

**Largest `delvis` (partly banned) areas:**
| Area | km² | Location | Regulation sentence |
|---|---|---|---|
| Hemmeldalen NR | 250.9 | 61.256, 11.007 | «Jakt og fangst etter viltloven, med unntak for ande- og vadefugler.» |
| Hynna NR | 64.2 | 61.244, 9.910 | |
| Kvisleflået og Hovdlia | 56.8 | | |
| Hersjømyrin | 45.0 | | |
| Lille Sølensjø | 34.9 | | |
| Brumundsjøen-Harasjømyra | 25.5 | 61.044, 11.112 | |
| Lavsjømyrene-Målikjølen | 25.3 | 60.994, 11.225 | «Jakt fra og med 10. september til og med 31. mars.» |
| Røssjøen | 24.1 | | |
| Gutulia NP | 22.6 | | |

Among hoyde891 points at 810–891 m in Innlandet: 7,640 lie in no protected area, 901 in `tillatt`, 125 in `delvis`, 1 in `ukjent`, and **0 in `forbudt`**.

**Decode.** Use `make_valid(shape(...))`. The loader shows the strictest class on top: tillatt < ukjent < delvis < forbudt.

### 2.11 `innlandet.json`

Commit 520fd05, 23.09 14:49. The file is a GeoJSON Feature with `properties: {navn: "Innlandet"}` and a MultiPolygon made of 1 polygon with 200 vertices, simplified to 3 decimals. Bounds: 7.343–12.871 E, 59.841–62.696 N. The area is 52,084 km² in EPSG:25833, against roughly 52,000 km² officially (approximate recollection, not checked here), so it is fine as a mask.

The layer text (`lag.ts:176-184`) says «Fellesskapet er nå sikre på at kassen står her». That is the community's belief **[I]**, not a fact. Source: «Fylkesgrenser fra Kartverket (forenklet)». It is used as a model factor at `src/lib/modell.ts:136`.

### 2.12 `norge.json`

Commit c0c849b, 23.09 14:30, output of `build_drivetime.py`. The file is a Feature (empty properties) with a MultiPolygon of 159 polygons and 8,472 vertices. Bounds: 4.642–31.059 E, 57.98–71.185 N. It was simplified with tolerance 0.01° and islands with area ≤0.002 deg² were dropped. It is used only to shade «Utenfor Norge» (`lag.ts:880-887`, «Ifølge vilkårene står kassen et sted i Norge»). Here I also used it to flag the 427 Swedish hoyde891 points.

### 2.13 `bokstaver.json`: referral-letter anagrams (N O R H E I M S U D)

Commits 06b82f0 (23.09 16:01) and aa81ebf (17:56). `kilde`: «Ordliste: LibreOffice nb_NO + OpenSubtitles-frekvens. Stedsnavn: GeoNames.» The loader type is at `src/components/Bokstavord.tsx:22`: `{kilde, alleTi[], ord[], alleOrd[], lange[], steder[]}`.

- `alleTi`: 552 full 10-letter multi-word anagrams, for example «HUS MINE ORD», «HEI MUS NORD», «HUMOR SIDEN».
- `ord`: 260 common words.
- `alleOrd`: 579 words.
- `lange`: 33 long words, for example MONSIEUR, HUSMOREN, MINUSORD, NORDISME, RHODIUM, SIDEROM.
- `steder`: 171 GeoNames places. Each entry is `{navn, lengde, antall, pos[lat,lon], teori|null, km|null, rest, restOrd[]}`, where `km` is the distance to the theory centre and `rest` the leftover letters.
  - 21 have a theory: Agder 5, Gjøvik/Toten 3, Røros 3, Valdres 3, Løten/Elverum 2, Rena/Åmot 2, Solør 2, Hardanger 1.
  - Examples: Nordhue (60.994, 11.338; Løten/Elverum, 15 km; rest IMS), Disen (60.798, 11.098; rest HMORU gives HUMOR), Osheim (61.428, 11.708; Rena/Åmot), Smerud (60.65, 11.783; Solør).

**Superseded.** Horde AI's answer to «Hordeminus» confirms the letters make HORDE MINUS (`innhold.ts:130`, [P, organizer app]). Everything in this file is a pre-24.09 word search **[M]** with no localisation value, apart from the GeoNames coordinates.

### 2.14 `shoplifter.json`: anagrams of the whiteboard letters «THILPRTE OESHF»

Commits 37bd161 (25.09 17:54), 72f623a (18:44) and 91da5a7 (19:44).
- `bokstaver: "THILPRTEOESHF"` (13 letters).
- `fasit: "THE SHOPLIFTER, FILTER THE SHOP og HELHET FOR TIPS"`.
- `hele_en`: 60 full English anagrams, for example FILTER THE SHOP, LEFT OTHER SHIP, FOREST HELP HIT, FRESH PILOT THE.
- `hele_no`: 61 Norwegian ones, for example HELHET FOR TIPS, HOFTER SHEP TIL.
- `ord_no`, `ord_en`: 40 each.
- `alle_ord`: 800.
- `steder`: 30 GeoNames places, `{navn, pos, type}`, for example Riseloftet, Prestholt, Holseter (60.355, 11.333), Perslett (61.194, 8.993), and «The Thief» (a hotel in Oslo).

The loader type is at `src/components/Anagram.tsx:9-18`.

The primary whiteboard text «THILPRTE OESHF» is in the mirror image `public/img/tavle-2509-shoplifter.jpg` [P]. Reading it as a nod to BobTheShoplifter (default.no) is **[I]**, as the Anagram.tsx text itself says. The file has no localisation value **[M]**.

---

## 3. Localisation overlay: every layer on the hoyde891 points

**What I computed.** For each of the 17,234 hoyde891 points I attached:
- in Innlandet / in Norway;
- municipality and Vercel verdict;
- `utelukket` class;
- whether it is inside a fellesskap891 cell;
- treslag score (nearest cell centre);
- inside a storvilt field;
- verneområde hunting class;
- wind at 23.09 17:49 and drive hours from Oslo (nearest node);
- inside the hand-traced Windy cloud polygons `SKYDEKKE` (`innhold.ts`), a community **[I]**;
- the minimum horizontal distance and maximum elevation angle to NOZ9EG and NOZ56U over **real 21:28:38–21:29:23**, which is stream 21:29:38 minus a delay of 15–60 s. For this I used the adsb.lol traces with GNSS altitude, the point's own height, and earth curvature.

The output is `/home/user/test/evidence/sources/other_datasets_overlay.csv` (17,234 rows; columns listed in §6).

**Base set: 810–891 moh, in Innlandet, within 900 m of a road: 8,667 points.**
| Constraint (on top of the base set) | Points |
|---|---|
| utelukket: R / C / open | 5,289 / 850 / **2,528** |
| inside the treslag bbox / with a stored score (≥0.55) / ≥0.65 / ≥0.75 / ≥0.85 | 3,999 / 1,881 / 1,075 / 542 / 127 |
| inside a storvilt field | 262 |
| verneområde: none / tillatt / delvis / ukjent / forbudt | 7,640 / 901 / 125 / 1 / 0 |
| wind 23.09 17:49: <2 / 2–4 / ≥4 m/s | 2,352 / 5,190 / 1,125 |
| drive hours (nearest node): min / p25 / median / p75 / max | 2.08 / 3.27 / 3.79 / 4.70 / 7.19 |
| inside the Windy cloud polygons / inside the "sol i dag" polygons | 2,335 / **0** |
| open on the community map and not in a Windy cloud polygon | 1,911 |
| horizontal distance to NOZ9EG or NOZ56U (true position) ≤3 / 5 / 10 / 15 / 20 km | 31 / 78 / 172 / 316 / 459 |
| maximum elevation ≥30° / 45° / 60° / 70° (all from NOZ9EG; NOZ56U gives 0 at every threshold) | 243 / 126 / 53 / 27 |

**Instantaneous elevation by stream delay** (810–891 m points in Innlandet):

| Delay | Real time | NOZ9EG position | Points at ≥60° | Points at ≥45° | NOZ56U points at ≥45° |
|---|---|---|---|---|---|
| 15 s | 21:29:23 | 61.3012, 10.9027 | 3 (all community-open) | 62 | 0 |
| 22 s | 21:29:16 | 61.3171, 10.9040 | 9 (all open, 5 with SE road) | 60 | 0 |
| 30 s | 21:29:08 | 61.3354, 10.9054 | 9 | 58 | 0 |
| 45 s | 21:28:53 | 61.3697, 10.9080 | 30 (29 with SE road) | 58 | 0 |
| 60 s | 21:28:38 | 61.4045, 10.9106 | 34 | 63 | 0 |

All of these points are in Stor-Elvdal kommune.

**All 49 aircraft with the corrected time** (labels + 46 s, which only lets me cover real 21:29:00–21:29:23), counting 810–891 m points in Innlandet that see some aircraft above 3,000 ft:

| Threshold | Points | By aircraft | By municipality |
|---|---|---|---|
| ≥30° | 593 | NOZ68L 235, NOZ9EG 215, WIF149 140, THY11 3 | Nord-Aurdal 138, Tolga 138, Stor-Elvdal 92, Øyer 88, Os 60, Ringsaker 35, Rendalen 30, Engerdal 7 |
| ≥45° | 283 | NOZ68L 146, NOZ9EG 96, WIF149 41 | |
| ≥60° | 63 | NOZ68L 36, NOZ9EG 21, WIF149 6 | |

How these groups line up with the other layers (≥45°):
- NOZ9EG, 96 points: all community-open; 62 inside the Windy cloud polygon; 66 with SE road.
- NOZ68L, 146 points: Tolga 97 and Os 49; all open; 70 in cloud.
- WIF149, 41 points: Nord-Aurdal; all "R".

For comparison, if you treat the labels as real time as the app does (labels 21:28:15–21:30:15): 433 points at ≥45°, with NOZ9EG 186, NOZ68L 168, WIF149 79, and Ringsaker gaining 94 points. **So the 46 s shift moves the favoured area under NOZ9EG from Ringsaker/Sjusjøen northwards to Stor-Elvdal (Messelt/Åsta west).**

**Clusters that survive combinations of constraints** (8-connected on the hoyde891 grid). "SE" is the share with a road to the SE, "tre" the maximum treslag score, "vind" the mean wind at 23.09 17:49, "kjør" the drive hours.

- **A. Base set + community-open: 2,528 points, 315 clusters.** Municipalities: Rendalen 470, Ringebu 376, Stor-Elvdal 336, Engerdal 270, Ringsaker 187, Trysil 170, Tolga 139, Øyer 108, Alvdal 102, Åmot 101, Os 91, Tynset 75. Largest clusters:
  - 182 points, 61.43–61.63 N 10.18–10.50 E (Ringebu); closest aircraft 22.4 km, max 18°.
  - 128 points, 61.125–61.240 N 10.66–10.82 E (Ringsaker; Sjusjøen/Ringsakfjellet); closest 9.1 km, 38°.
  - 90 points, 61.66–61.775 N 10.44–10.64 E (Ringebu/Stor-Elvdal); tre 0.87.
  - 73 points, 61.335–61.40 N 11.44–11.55 E (Åmot, east of Rena); tre 0.86, vind 1.0.
  - 54 points, 61.90–61.98 N 11.42–11.52 E (Rendalen).
  - 53 points, 61.235–61.30 N 10.66–10.76 E (Øyer); closest 8.0 km, 41°.
  - 48 points, 61.27–61.335 N 10.70–10.84 E (Øyer/Stor-Elvdal); closest 3.8 km, **61°**.
  - 36 points, 61.355–61.41 N 10.88–10.99 E (Stor-Elvdal); SE 97 %, closest **0.1 km, 89°**, tre 0.64, vind 4.2, kjør 3.4 h.
- **B. A + road to SE: 1,565 points.** The NOZ9EG-overhead cluster 61.355–61.41 N 10.88–10.99 E keeps 35 points. The Ringsaker cluster near 61.125–61.165 N 10.85–10.89 E has 26 points with median road distance 93 m.
- **C. B + outside storvilt fields: 1,454 points.** Unchanged in the NOZ9EG corridor (34 points left).
- **D. A + within 15 km of the true NOZ9EG or NOZ56U position: 301 points, 25 clusters.** Stor-Elvdal 127, Øyer 108, Ringsaker 63. The main clusters:

| n | Area | Municipality | Closest (km) | Max elevation |
|---|---|---|---|---|
| 53 | 61.235–61.30 N, 10.66–10.76 E | Øyer | 8.0 | 41° |
| 48 | 61.27–61.335 N, 10.70–10.84 E | Øyer | 3.8 | 61° |
| 36 | 61.355–61.41 N, 10.88–10.99 E | Stor-Elvdal | 0.1 | 89° |
| 32 | 61.19–61.24 N, 10.73–10.79 E | Ringsaker | 9.1 | 38° |
| 20 | 61.30–61.34 N, 10.95–11.00 E | Stor-Elvdal | 2.4 | 72° |
| 15 | 61.44–61.46 N, 10.80–10.87 E | Stor-Elvdal, near Messelt | 5.5 | 54° |
| 15 | 61.48–61.505 N, 10.76–10.79 E | | 10.6 | 35° |
| 12 | 61.315–61.33 N, 10.66–10.70 E | | | |
| 10 | 61.20–61.215 N, 10.90–10.95 E | | | |

- **E. Maximum elevation to NOZ9EG ≥45°: 126 points, 10 clusters.** Stor-Elvdal 88, Øyer 31, Ringsaker 7.
  - 36 points: 61.355–61.41 N, 10.88–10.99 E.
  - 34 points: 61.27–61.305 N, 10.78–10.84 E.
  - 20 points: 61.30–61.34 N, 10.95–11.00 E.
  - 15 points: 61.44–61.46 N, 10.80–10.87 E.
  - 7 points: 61.42–61.43 N, 10.81–10.86 E.
  - 4 points: 61.245–61.26 N, 10.84–10.85 E.
  - 3 points: 61.24 N, 10.87–10.88 E.
  - 3 points: 61.42 N, 10.97–10.99 E.
  - 2 points: 61.335–61.34 N, 11.01–11.02 E.
  - 2 points: 61.425 N, 10.885 E.
- **F. treslag ≥0.75: 542 points.** Stor-Elvdal 100, Alvdal 90, Rendalen 89, Engerdal 85, Folldal 42, Ringebu 41, Tynset 40. Every cluster is ≥20 km from NOZ9EG, and most are 38–80 km away.
- **G. F + community-open: 394 points.** Best clusters: 62.02–62.07 N 11.09–11.16 E (Rendalen, tre 0.90); 61.775–61.815 N 11.96–12.00 E (Engerdal, 0.86, road 60 m); 61.745–61.775 N 10.97–11.04 E (Rendalen/Stor-Elvdal, 0.84, vind 1.8); 61.585–61.615 N 10.80–10.83 E (Stor-Elvdal, 0.85, 20.6 km from NOZ9EG).
- **H. Open + SE road + treslag ≥0.65 + wind <4 + outside storvilt: 408 points.** Engerdal 93, Rendalen 91, Stor-Elvdal 79, Ringebu 55, Tynset 28, Alvdal 24, Trysil 13, Ringsaker 9. The only cluster within about 20 km of NOZ9EG is 61.145–61.16 N 10.85–10.87 E (Ringsaker, 9 points, road median 48 m, tre 0.69, closest 15.8 km, 24°).
- **I. 810–891 m hoyde891 points inside fellesskap891 cells: 107 points.** Ringsaker 46, Stor-Elvdal 46, Øyer 14. Clusters: 61.165–61.215 N 10.72–10.79 E (38 points), 61.38–61.41 N 10.88–10.95 E (17 points, 89°), 61.295–61.32 N 10.74–10.78 E (11 points).

**No single cell satisfies everything.** The height, aircraft-overhead, community-open and SE-road constraints converge on **Stor-Elvdal between 61.30 and 61.46 N, 10.78–11.02 E** (west of Rena, south of Messelt) and on Øyer/Ringsakfjellet at 61.27–61.335 N 10.70–10.84 E. That area scores poorly on treslag (0.60–0.64), has 4+ m/s model wind at 23.09 17:49, and lies in the hand-traced Windy cloud band. **These are [M] results built on [I] inputs** (810–891 as moh, pointing at an aircraft, SE road). They are not facts.

---

## 4. Contradictions and corrections found

1. **`fly_2130.json` labels and adsb.lol times** (§2.4). The labels are 46 s earlier than the raw traces. The magnus app's `PEKETID_EKTE = '21:29:15'` positions and its `FLY_PUNKT`/`FLY_PUNKT2` constants sit about 8–9.5 km too far along each track. The app's statements «NOZ9EG sørover over Ringsakfjellet ved Sjusjøen» and «NOZ56U nordover over Hamar, like ved Løten» (`innhold.ts:749`) describe positions at about real 21:30:00–21:30:36. At real 21:29:16, NOZ9EG was over northern Ringsakfjellet / south-west Stor-Elvdal (61.317, 10.904) and NOZ56U over Stange/Ottestad (60.739, 11.222).
2. **810–891 moh versus NOZ56U overhead** (§0.3). No 810–891 m near-road point exists within 25 km of NOZ56U at either timing, and none within 36 km of SAS50J on 25.09 at 17:22. Hamar, Løten, Stange and Elverum have none at all.
3. **810–891 moh versus the satellite-clear area of 23.09** (`SOL_I_DAG`). None of the 8,667 Innlandet points fall in the clear polygons, and 2,335 fall inside the Windy cloud polygons. Both polygon sets are rough community drawings **[I]**: `SOL_I_DAG` is «Tegnet grovt ut fra en beskrivelse … ikke fra selve bildet» (`lag.ts:771`).
4. **The `utelukket` caption versus its grid** (§2.6). The caption lists a narrow strip, but the grid leaves Rendalen, Engerdal, Trysil, Tolga, Os, Røros, Ringerike, Telemark and others open.
5. **treslag versus utelukket-C** (§2.2). The 35 % birch target rewards birch-dominated, often subalpine, cells, while the community map excludes "fjellbjørk". Meanwhile the lag.ts note on hoyde891 cites Hagina: «bjørka er for langt på høsten allerede på ca. 510 moh ved Sjusjøen». That note is at `src/data/lag.ts:237`, recorded in commit 889d715 "pull down high terrain around Ringsakfjellet/Sjusjøen".
6. **fellesskap891 versus hoyde891** (§2.5). Poor overlap: median 1.07 km apart.
7. **hoyde891 includes Swedish terrain** (427 points; §2.1).
8. **The storvilt timing logic.** Moose hunting started on 25.09 and the box was placed around 21.09, so a hunting field does not bear on where the box was put. The app labels the layer «fakta» (`src/data/lag.ts:706`), but the exclusion is **[I]**.
9. **Recorded retractions in these datasets:**
   - The pink «ingen sopp» class was removed from `utelukket.json` because it «var ikke korrekt» (b55eafc).
   - "Everything west of 8.4° E" was added as excluded because the image never covered it (fc71636). That is a filled-in assumption, not an observation.
   - Birkebeinervegen was removed from the site entirely (e431102), which is outside these files.
10. **Stream-delay assumptions differ.** The app uses 20 s–1 min («vi tipper»), `fly.ts` hard-codes 21:29:15 (a 23 s delay), and the bevis branch uses default.no's ~22 s. The site's own texts are also inconsistent about when she pointed. `innhold.ts:1086` says «da Anja pekte opp (21:28:53 ekte tid)», which is a 45 s delay, while `fly.ts` uses 21:29:15.

---

## 5. Open questions

- Why are the default.no `event_planes.json` timestamps 46 s early? Is the offset the same for all 49 aircraft? Fetch adsb.lol traces for NOZ68L, WIF149, THY11, AKK2 and NOZ385 to check.
- Did she point at an aircraft at all, or at the shooting star (21:27:42 signal, chat request at 21:29:10)? If it was the star, every aircraft-overhead constraint disappears.
- What exactly is the "road to SE" rule in hoyde891 (bearing window, which OSM highway classes)? The build script is not published, so ask MagnusPladsen or rebuild it.
- Does «2,7 eiffeltårn» mean elevation at all? The alternatives are distance from the road, or codes 0810/0891. Horde AI itself says it is only a set phrase.
- treslag uses SR16 dominant species. Would SR16 species-volume shares, or the NIBIO SAT-SKOG/SR16 "treslag andel" rasters, give more realistic birch shares? Could the analysis also be extended west of 9.82 E and north of 62.2 N?
- Where exactly were the edges of the original community exclusion image (the image is not in the repo)? That would show which open cells were really "not assessed".
- Vercel's `kommunevurdering` is a 23.09 snapshot. Has it been updated since?

---

## 6. Derived files written by this task (inputs for other tools)

- `/home/user/test/evidence/sources/other_datasets_overlay.csv` has one row per hoyde891 point (17,234). Columns:
  - `lat, lon, moh, road_m, road_to_SE, in_innlandet, kommune, vercel_verdict, utelukket_cls (R/C/open), in_fellesskap891, treslag_score (NaN = not stored), in_storvilt, vern_jakt, wind_ms_2309_1749, drive_h_oslo`;
  - `NOZ56U_min_km, NOZ56U_max_elev_deg, NOZ9EG_min_km, NOZ9EG_max_elev_deg` over real 21:28:38–21:29:23 from the adsb.lol traces;
  - `in_norway, windy_cloud`.
- Figures in `/home/user/test/evidence/sources/other_datasets_figs/`:
  - `fig1_overview.png`: 810–891 m points (open vs excluded), the utelukket R and C cells, fellesskap891, and the NOZ9EG and NOZ56U traces with 21:29:16 true positions; NOZ68L and WIF149 dotted.
  - `fig2_noz9eg_corridor.png`: true positions at delays of 15, 22, 45 and 60 s against the fly_2130 label positions, the ≥60° ring, and hoyde891 points with and without an SE road.
  - `fig3_treslag.png`: the treslag score map with cells ≥0.90 ringed.
- Scripts in `/home/user/test/evidence/sources/other_datasets_scripts/`:
  - `hoyde_analysis.py` assigns Innlandet and municipality to each point and builds the cluster tables. It writes `hoyde_meta.npz` to the scratchpad.
  - `overlay.py` joins all layers and computes the aircraft geometry, writing `overlay.npz`.
  - `combos.py` computes the constraint combinations.
  - `figs.py` draws the figures.
