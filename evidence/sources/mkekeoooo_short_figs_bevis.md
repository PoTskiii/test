# mkekeoooo/hordejakten-2026: short report, figure gallery and Claude "bevis" branch

Source dossier compiled 2026-09-25 (evening CEST). This covers three things. First, the 12-page short report
`rapport/Hordejakten_2026_kortrapport.pdf`. Second, the figure gallery `figurer/` (all 15 PNGs viewed). Third, every
file on the branch `bevis/claude-2026-09-25`, which holds the ADS-B, horizon, canopy and sun-sequence scripts and results.
The full 22-page report is covered in a separate dossier (`mkekeoooo_full_report.md`). I cite it here only where it
explains a figure or a script parameter, and I mark those citations **[full report p.N]**.

## 0. Provenance, versions, conventions

| Item | Value |
|---|---|
| Short report | `/home/user/test/data/raw/mkekeoooo/rapport/Hordejakten_2026_kortrapport.pdf`: 12 pages, ReportLab, PDF CreationDate 2026-09-25 08:20:13 UTC, title "Hordejakten 2026 – samlet rapport", author "Hordejakten 2026 – åpen analyse". Text extracted with pypdf; the embedded images are the same as the PNGs in `figurer/`. |
| Main-branch mirror | `/home/user/test/data/raw/mkekeoooo` at commit `d1fbac0` (2026-09-25 04:43 PDT = 13:43 CEST). |
| Bevis mirror | `/home/user/test/data/raw/mk_bevis`, detached at `4baabc5` (2026-09-25 04:09 PDT = 13:09 CEST) |
| **Newer upstream (checked live via `git ls-remote` + clone into scratchpad)** | Bevis branch is now at `e8178da` (13:57 PDT = **22:57 CEST**). It adds `solkart-2509/` (see §4.7). Main is now at `b067a04` (**23:23 CEST**). The README has a new headline: direct sun around 17:00 CEST on 25.09 (see §6). The local mirrors do **not** contain these commits. |
| Authorship | KILDER.md:3: «Rapportene er satt sammen av Claude på grunnlag av brukerens arbeid og utveksling med Codex.» The bevis README describes itself as «Bevispakke – Claude (Opus 5.5), 25.09.2026». Everything here is AI-assisted community analysis (evidence classes (b) to (d)), not organizer data. |
| Time zones | CEST = UTC+2. The report's whiteboard times are labelled «strømtid» (stream time). The bevis ADS-B scripts use real time = stream time − delay, with delay 15–50 s (default.no measured about 22 s). The morning minute clips are default.no's labels («klokkeslett er slik de er merket»), not corrected for delay. |
| Re-runs by me | `adsb/fly_2109.mjs` and `adsb/tilt_2129.mjs` re-ran offline (Node 22) and produced **byte-identical** output to the published `*_resultat.txt`. `horisont/sun.mjs` (NOAA) re-run for key times: see §4.4. The horizon, canopy and grense scripts need `hoydedata.no` / `ws.geonorge.no`, which are blocked here, so they were **not** re-run. PRESISERINGER.md:9-10 says Codex re-ran `fly_2109.mjs` and `horisont_api.mjs` and got the same results. |

Evidence classes used below: **(a) primary** covers whiteboard text, what is visible on stream, and organizer
statements. **(b) community observation** covers measurements on stream frames and ADS-B tracks. **(c) interpretation**.
**(d) model output** covers DTM/DOM tests, MET model data and fusion grids.

---

## 1. Key takeaways

1. **Nothing is confirmed.** Short report p.1: «Ingen plassering er bekreftet». Main README (both versions):
   «Ingen plassering eller region er bekreftet». The five-site list is a historical **inspection order**
   («kontrollrekkefølge, ikke sannsynligheter»), and since 25.09 it has been explicitly «under revisjon».
2. **Camera model, used by all the geometry.** Heading **219.2–219.6° true**; the bevis scripts use 219.4°. Focal length is
   **f = 1068 px at 1280 wide (= 1602 px at 1920)** and the horizontal FOV is **≈62°**, covering azimuth
   **188.7–250.5°**. The camera sits about 5 m NE of the box (whiteboard «KAMERA 41 ØST»; the scripts use 39°), about
   1.5 m above ground. The report gives 1.1–1.9 m. The ground under the box front is **4.3–5.9 m** from the camera.
   The camera is fixed: the 10:15 and 15:01 frames align to under 1 px, and the night camera is the same frame zoomed ×2.45.
3. **Morning sun sequence 21.09**, measured on default.no minute clips and marked [verifisert] by Claude. The crown/stem
   patch top-right of frame (azimuth 238–250°, elevation +8.5 to +18.6° from the camera) gets **direct sun from 07:47**.
   The crown/sky ratio goes 0.32 → 0.39 → 0.53 → 0.66 between 07:44 and 07:50. The patch stays lit until 08:00 and is dark
   again at 08:30. The ground 4.6–7.5 m in front gets **no direct sun up to 08:00**. Faint warm spots on stems centre-left
   at 07:40–07:44 are marked [vurdering]. First direct sun anywhere in the frame is therefore **no later than 07:47**. The
   report's 07:51 came from default.no.
4. **Sun limit that does not depend on which surface was lit** (`grense_2*.mjs`, DTM only). This finds the lowest
   height above ground at which terrain lets the 07:50 sun through, for any point in the field of view. Results:
   Jernvinneveien 5a **38.2 m** (light sector 39.1 m), 5b **32.4 m**, 5c **17.3 m** (18.5 m), A1 **32.3 m**,
   Myklebysæterveien control **0.0 m**. Trees there are ≈12–21 m (p90/p99), so **5a, 5b and the exact A1 point cannot
   have had any sunlit surface in view at 07:50**, given the camera model and sun timing. 5c is borderline. On the
   27 v6 camera positions, all A2, Messelt and P7 points need 0–4.9 m, which is unconstrained. The A1 points need
   5.8–54.0 m.
5. **Terrain horizon toward the 07:51 sun** (az 98.8°, 5.7° high), from 1.5 m eye height (`horisont_api`, reproduced by
   Codex). Values: 5a 8.4°, 5b 7.3°, 5c 6.6°, cand. 4 3.8°, cand. 2 1.8°, cand. 1 0.5°, Messelt −0.4/−0.5°. From
   `terrain.mjs`: A1 11.1° at the ground and 7.2° from 20 m; A2 2.6°.
6. **Canopy (crown-transmission) tests do not discriminate** (the authors' own verdict: «testen ikke skiller»).
   **K0–K4 forest requirements re-checked at the published coordinates give only 0–4 of 25 neighbourhood positions
   passing.** Candidate 1's own box site fails K0 (median canopy 10.4 m where the box should be in an opening).
7. **The 21.09 21:29 pointing gesture** (stream 21:29:38; ~21:29:16 real time with a 22 s delay). NOZ9EG (LN-NIQ, B738,
   southbound descent to OSL along about 10.90–10.93°E) was 20–33° high over **all** Evenstad-area candidates. None had an
   aircraft near the zenith. NOZ9EG had passed closest 26–64 s **earlier**. The tilt model (camera heading 219.4°) gives
   **no location with the observed 10–20° left lean at the measured 22 s delay**, for either aircraft. Matches appear
   only at other delays (15 s: cand. 1, 2, 4; 30 s: Løten for NOZ56U; 45 s: A1, Sjusjøen).
   The gesture may concern a **shooting star** instead: she signalled «stjerneskudd» at 21:27:42 and chat asked her to
   point at 21:29:10. The authors now agree the gesture **alone neither selects nor excludes a region**, and they withdrew
   the earlier inference of aircraft elevation from arm angle.
8. **Two whiteboard quotes are corrected** by the bevis re-reading. 21.09 18:44 reads «STARTET 07 00 / **UJEVNT** TERRENG,
   MYE LYNG / HØRER IKKE MYE FRA BOKSEN»; the report had «KUPERT TERRENG». 21.09 19:38 reads «4 STORE STEINER **TIL
   VENSTRE**, KUN STEIN DER». A 22.09 18:56–19:05 set adds «JA, FØLES SOM FJELLUFT», «GIKK IKKE PÅ STI, MEN KUPERT
   TERRENG» and «BLANDET SKOG, VELDIG HØYE TRÆR, KUPERT TERRENG, SOM GÅR SLAKT SLIK:» with a drawn gentle hump.
9. **Newest (upstream only, after the mirror).** Direct sun around 17:00 CEST on 25.09 (14:33–15:22Z, a «solstjerne»
   in their live frames) is documented by both Codex and Claude, and «Antakelsen om en helt overskyet ettermiddag er
   trukket tilbake». Their MTG satellite clear/cloud map shows no clear-compatible (green) pixels at any Evenstad-area
   candidate. Those areas are red or yellow (conflict or undecided). Green areas lie NE (Røros, Engerdal) and SE of
   Oslo/Kongsvinger. They state the satellite comparison **selects no region yet** and Østerdalen **is not excluded**.

---

## 2. The short report (`Hordejakten_2026_kortrapport.pdf`, 12 pp., dated 25.09.2026)

### 2.1 p.1: "Kort fortalt" ranking (historic inspection order, all in Stor-Elvdal near Evenstad)

| # | Place | Box (approx.) | Nearest road point | Walk | Report's reason (quote condensed) |
|---|---|---|---|---|---|
| 1 | Myklebysæterveien vest | **61.3995, 11.0316**, 594 moh | 61.3992, 11.0409 | ≈500 m west, 30 m up | «Består alle modelltestene: terreng, skog, adkomst, morgensol og temperatur. Fem naboposisjoner består; veien kommer fra øst; ingen bekk eller bygning nær.» |
| 2 | Madsskardveien, traktorvei | **61.4443, 11.1234**, 598 moh | 61.4421, 11.1301 | ≈440 m NW, 45 m up | «Består alt, og veien ligger nøyaktig i retningen Anja tegnet («KOM FRA DEN VEIEN ←»). Bare to posisjoner, så resultatet er tynt.» |
| 3 | Sørlige Messelt | **61.4571, 10.8362** (898 moh) and **61.4545, 10.8406** (876 moh) | 61.4543, 10.8435 | ≈500 m and 155 m | «Høyden passer «2,7 Eiffeltårn» (891 og 875 m), og veiretningen stemmer. Men værmodellen gir ca. 3 °C kaldere enn Anja oppga.» |
| 4 | Madsskardveien øst | **61.4518, 11.1428**, 647 moh | 61.4483, 11.1433 | ≈400 m N, 21 m up | «Består alt, og ligger i default.no sitt beste område. Veien kommer fra sør, og det er en bekk 41 m unna.» |
| 5 | Jernvinneveien | **61.4351, 11.1435**, 556 moh | 61.4335, 11.1433 | ≈190 m N, 15 m up | «Flest posisjoner som består, og beste temperatursamsvar. Men det er nær vei og bekk, og veien kommer fra sør.» |

The same page says:

- Excluded or weakened: «kandidatene vest for Glomma ved Birkebeinerveien og Gålaveien. Terrenget der ville skygget
  for morgensola kl. 07.51, og ett av stedene krever kryssing av Nørdre Eldåa.»
- Caveats: whiteboard interpretation; «første solflekk» at 07:51, which was «målt av default.no, ikke kontrollert i
  originalopptaket»; temperatures might be box air; lidar possibly from 2016; possible felling since. «Hvis
  07.51-målingen er feil, kommer Birkebeinerveien (61.449, 10.977) tilbake som et godt alternativ».

### 2.2 p.2: Figure 1 (= `oversikt_temp.png`) and table of contents

MET Nordic modelled air temperature on 21.09 at 19:35, with a black 8 °C isoline. The report text says «Messelt (3)
ligger på den kalde siden; stedene øst for Glomma og Myklebysæterveien ligger nær linjen.»

### 2.3 p.3: Whiteboard / primary hints as the report lists them (class (a), transcribed by the authors)

| Time (stream) | Board text (report's transcription) | Use in report |
|---|---|---|
| 21.09 18.31 | «INGEN FLY · INGEN SKYTING · OSLO, SØN KL 04.00 · CA 5–10 MIN Å GÅ FRA BIL» | walk from car; no shooting range |
| 21.09 18.36–18.38 | «INGEN FERGE · KUN BIL» and «TROR DET VAR OPPOVER · SISTE 5–10 MIN» | uphill approach |
| 21.09 18.44 | «KUPERT TERRENG · MYE LYNG · HØRER IKKE MYE FRA BOKSEN» **(corrected by bevis to «UJEVNT TERRENG», §4.1)** | terrain type |
| 21.09 18.57 | «PRESENNING · MER ÅPEN SKOG TIL HØYRE FOR MEG» | forest structure («uklar retning») |
| 21.09 19.00 and 19.50 | «INGEN SKYER NÅ» and «KLAR HIMMEL» | cloud |
| 21.09 19.35 | «CA 12 °C (DAGEN) · NÅ CA 8–11 °C» | temperature |
| 21.09 19.38 | «4 STORE STEINER, KUN STEIN DER» **(bevis: «4 STORE STEINER TIL VENSTRE, KUN STEIN DER»)** | not used; not visible in lidar |
| drawing | «KOM FRA DEN VEIEN ←», with the camera about 41° east of north as seen from the box | road direction ≈130°, camera toward ≈221° |
| 22.–23.09 | «NULL REGN»; «SOLA VAR OPPE FØR 07»; «SOL · VINDSTILLE» | dry first days |
| 23.09 evening | «TYPISK FJELLMARK», «IKKE VANN», «GIKK 2 MIN INN I SKOGEN», «ISH 16°» | terrain, water, access |
| 22.09 21.36 | «DET ER INGEN LYS RUNDT KASSEN» | no lights nearby |
| 24.09 11.05 | rain («gjengitt av andre, ikke sett på tavla av oss») | low weight |
| 25.09 08.46 | «Overskyet. Flyene er så langt unna at de er umulige å se.» (gjengitt) | low weight |

Other hints on p.3:

- Horde sound hint 24.09 = **orrfugl på høstleik** (black grouse autumn lek). This is organizer media.
- «HORDEMINUS» in the app's AI assistant gives «2,7 eiffeltårn stablet oppå hverandre». That is 810, 875 or 891 m
  (300, 324 or 330 m tower), either altitude or a lock code.
- Anja mentioned «gule og grønne fugler».
- An app prize item «kombinerer bever og olivenolje». This is **corrected in PRESISERINGER.md:30**: the picture shows a
  **grevling** (badger), the name is «Olivenoljestativ», it costs 100 000 poeng, and the freight text reads «Nesten Helt
  Hjem». These come from third-party screenshots on praktiskinfo.no and were not checked in the app.

### 2.4 p.3: Method

- «Kameraet peker mot ca. 220° (sørvest) og har ca. 62° synsfelt.»
- Kartverket DTM1/DOM, 1 m; canopy height = DOM − DTM.
- Grid search: «alle mulige kameraplasser med 10 m avstand testet (7 525 per område, 13 områder), og treffene er
  forfinet med 2 m avstand».
- OSM for roads, streams and buildings; MET Nordic analysis (1 km, hourly); MET radar; NOAA sun per minute.

### 2.5 p.4: Camera image facts (Figure 2 = `fig_kjennetegn_1045.png`, Figure 3 = `fig_stubbe_sammenligning.png`)

- «bakken rett under kassens forkant ligger 4,3–5,9 m fra kameraet. Kameraet står 1,1–1,9 m over bakken.»
- Birch on the right: its base is «antagelig 12–45 m unna, anslått fra stammebredden».
- The clearing behind the box is heather out to an edge of young forest. It is used as a sight-line requirement, but at
  no known distance.
- **Retraction.** The bright «stubbe» behind the box had been used to derive 17–44 m. Morning diffuse-light frames
  show the bright patch exists only in afternoon sun, «trolig motlyst løv» (probably backlit foliage). The distance was
  withdrawn and all sites rejected because of it were reinstated.
- The camera is stationary: the 10:15 and 15:01 frames overlay with under 1 px error. The night camera is the same
  frame magnified ≈2.45×, so there is «ingen parallakse». The full report p.11 adds that 114 of 127 SIFT matches agree.

### 2.6 p.5: Terrain and forest model (class (d))

- Terrain rays: ground under box at 4.3–5.9 m; ground edge behind box at 8–250 m; birch foot at 12–45 m.
- Five lidar forest zones: open at the box (<3 m); a clearing right behind; trees ≥10 m to the left and right; tall
  trees (≥12 m) 25–70 m behind. The exact K0–K4 definitions are in §4.5.9.
- «Uten den feilaktige stubbeavstanden skiller terrenget nesten ingenting: 1 000–7 500 av 7 525 posisjoner per område
  består. Skogtesten gjør hovedjobben.»

Positions passing successive filters (grid counts, «ikke sannsynligheter»):

| Area | Terrain + forest | Access | Morning sun | Access + sun | + temperature |
|---|---|---|---|---|---|
| Birkebeinerveien (A1) | 10 | 3 | 0 | 0 | 0 |
| Gålaveien (A2) | 20 | 2 | 12 | 0 | 0 |
| Sørlige Messelt | 8 | 2 | 7 | 2 | 0 |
| Nordlige Messelt | 6 | 3 | 6 | 3 | 0 |
| Punkt 7 / P2 | 3 | 3 | 2 | 2 | 0 |
| H2 | 0 | – | – | – | – |
| E1 Madsskardveien øst | 6 | 4 | 5 | 4 | 4 |
| E2 Jernvinneveien | 47 | 28 | 31 | 21 | 21 |
| E3 Madsskardveien | 25 | 4 | 22 | 3 | 3 |
| E4 Ole Evenstads vei | 40 | 26 | 8 | 7 | 0 |
| E5 Madsskardveien nord | 17 | 17 | 2 | 2 | 2 |
| E6 Myklebysæterveien | 9 | 5 | 9 | 5 | 5 |

Filter definitions:

- Access: road or tractor road 100–900 m away, ≥5 m climb from the road, no river crossing.
- Morning sun: eastern terrain horizon «høyst ca. 6,5°».
- Temperature: modelled day 10–14 °C and 7–12 °C at 19:35.
- «Null skogtreff ved H2 er et modellresultat, ikke en fysisk utelukkelse.»
- Trunk matching is weak in dense forest. Recommended sites have 8–10 of 10 trunks with a lidar tree in the right
  direction and distance.

### 2.7 p.5–6: Sun (Figure 4 = `sol_og_temp.png`)

- «default.no målte at den første direkte solflekken i bildet kom kl. 07.51 den 21.09, og at sola var sterkest
  08.25–09.55.» Their 10:15–10:45 frames show only diffuse light.
- At 07:51 the sun is at azimuth 98.8° and 5.7° high. My NOAA re-run gives 98.9° and 5.77° refracted (5.62° geometric),
  which confirms it.
- Evening sun at 17:23 is 12.9° high toward 246° (my check: 246.7°, 12.8°), «skiller ingen steder».
- Caveat: the first sun spot is not necessarily the first sun on the ground, and it was not checked in the original.
- Night: a flagged «billys» (car light) on 22.09 at 21:35 was a 55 s light change on the left side, «Mest sannsynlig …
  en lampe ved utstyret». At the same moment Anja held up «DET ER INGEN LYS RUNDT KASSEN».

### 2.8 p.6: Weather (class (d) model versus class (a) board values)

| Place | Model day max 21.09 | Model at 19:35 | Anja | Match |
|---|---|---|---|---|
| Birkebeinerveien (A1) | 12.0 °C | 8.0 °C | ca. 12 / 8–11 °C | ✓ |
| Gålaveien (A2) | 14.0 | 9.2 | | ~ |
| Sørlige Messelt (3) | 8.8–9.6 | 5.3–5.8 | | ✗ |
| Punkt 7 | 9.5 | 6.4 | | ✗ |
| Myklebysæterveien (1) | 11.9 | 8.1 | | ✓ |
| Madsskardveien (2, 4) | 11.5–11.6 | 7.5–7.6 | | ✓ |
| Jernvinneveien (5) | 12.9 | 8.4 | | ✓ |

- Caveat: «ISH 16°» on the evening of 23.09 is high for the season, so some values may be box air.
- A combined test of all seven weather statements nationwide gave **2 hits, far north in Nordland**. It was therefore
  not used, because «SOL» and «VINDSTILLE» cannot be mapped to model values.
- Rain 24.09 11:05 is second-hand. MET radar is blocked in much of Glommadalen and there is no clear echo at the sites.
  Not used.

### 2.9 p.7: Access (Figure 5 = `bro_sjekk_A2.png`)

- Criteria: road 100–900 m, ≥5 m climb, no river crossing. The «KOM FRA DEN VEIEN ←» direction (≈130°, from the
  left of the image = SE) is a soft criterion.
- Former main point **C07 at Gålaveien**: Nørdre Eldåa runs in a ravine about 24 m below the end of the tractor road,
  and there is no bridge in the lidar. «Det betyr ikke alene at vading er eneste vei, men stedet er nedprioritert.»

### 2.10 p.7: Region

- default.no's best area is Glommadalen between Rena and Evenstad (**61.35–61.47 N, 10.97–11.15 E**). Its best cell is
  **61.45, 11.10**, near sites 2, 4 and 5.
- The planes Anja reacted to (21.09 21:29 and 22.09 20:32–20:35) were «innflyginger sørover gjennom Østerdalen».
- The report used this only to choose where to look: «ikke som bevis på et bestemt punkt».

### 2.11 p.7–8: Checklist matrix (✓ fits / ~ partly / ✗ poorly)

| Criterion | 1 Mykleby | 2 Madsskard | 3 S-Messelt | 4 Madsskard øst | 5 Jernvinne | P2 Punkt 7 | A1 Birkebeiner |
|---|---|---|---|---|---|---|---|
| Morning sun 07:51 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| Temperature 21.09 | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✓ |
| Road 5–10 min uphill | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | ~ |
| Road direction ≈130° | ✓ | ✓ | ✓ | ~ | ~ | ~ | ✗ |
| No stream/river <100 m | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ |
| No building <300 m | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Several neighbour positions pass | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✓ |
| Trunks in right direction | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ~ |
| Height hint 810/875/891 moh | ✗ | ✗ | ✓ | ✗ | ✗ | ~ | ✗ |
| In default.no best area | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |

Three of these entries have since been challenged (details in §7):

- Candidate 1 road direction ✓: the road bearing is actually about 94° (PRESISERINGER.md:12).
- Jernvinneveien morning sun ✓: the published 5a/5b/5c horizons are 8.4, 7.3 and 6.6°, and grense_2 shows no sunlit
  surface is possible at 5a/5b.
- Candidate 1 forest: K0 fails at the published coordinate.

### 2.12 p.8–9: Quality control

Premise → effect if wrong:

- 07:51 first sun (default.no, not checked in the original) → «Birkebeinerveien kommer tilbake, trolig foran Messelt».
- Temperatures are outdoor air → if not, «Messelt og punkt 7 styrkes».
- Height hint is altitude → «Er det en låskode, faller Messelts særstilling».
- DOM up to date → felling may have removed trees; Global Forest Watch shows new felling near several sites.
- Camera calibration / forest thresholds → hit counts change, «men sjelden hvilke områder som består».
- «KOM FRA DEN VEIEN ←» means SE → soft criterion, affects order only.
- OSM complete → unmapped bridges or roads could change access.
- Flight analysis points to Østerdalen → «Er den feil, kan kassen være et helt annet sted; vi har bare undersøkt 13
  områder på 1,6 × 1,6 km».

Errors found and corrected:

1. Stump distance 17–44 m withdrawn.
2. Ray stepping changed from 25 cm to 1 cm (it had caused false edge hits).
3. Robustness was merged with a maximum instead of a union; fixed.
4. Tractor roads had been treated as drivable; they are now reported separately, and missing data gives «ukjent».
5. «alle» positions at Gålaveien failing morning sun was wrong. Correct: **none of the positions there with access
   pass**.

Not done:

- Field visit.
- «Originalkontroll av morgensola 07.45–08.00».
- The full rain window 24.09 10:55–11:15.
- Hint-video original frames (download refused).
- DOM vintage check.

Unresolved hints:

- «Gule og grønne fugler» fits common autumn conifer-forest species: grønnsisik, korsnebb (females and young are
  yellow-green), kjøttmeis, fuglekonge. default.no found furukorsnebb, kjøttmeis and blåmeis in day-1 audio. The full
  report p.6 notes that per default.no the stream audio is a looped 24-hour recording.
- The beaver/olive-oil item: not used.

### 2.13 p.9–11: Field maps (the same PNGs as `figurer/kart_*`)

What to look for on site: «en liten lysning med kassen, en skrå død stamme bak, en bjørk med skjev nedre stamme til
høyre og tette mørke stammer til venstre (figur 2)». All exact coordinates printed on the maps are in §3.3.

### 2.14 p.11–12: Sources

Horde campaign page, rules and terms (horde.no/gjeldfri/hordejakten); YouTube EQHgfmZicc8; default.no clip archive,
whiteboard log, flight analysis and notes; Kartverket DTM1/DOM (NHM); MET Nordic (thredds) and radar mosaic; OSM (ODbL);
MagnusPladsen community map; Dagbladet/Børsen. «Denne rapporten er uavhengig og har ingen tilknytning til Horde.»

---

## 3. Figures (`figurer/README.md` and all 15 PNGs)

`figurer/README.md:3`: «Illustrasjonene er modellresultater eller registrerte bildeobservasjoner; de dokumenterer
ikke i seg selv plasseringen.» `:40`: «Gamle figurmarkeringer skal ikke gjeninnføre den tilbaketrukne B3-avstanden på
17–44 m.»

Status labels in the README:

- `sol_og_temp.png`: «Betingede modelltester; morgensol og temperaturreferanse er usikre».
- `syntetisk_utsyn_kronebase40.png`: «Illustrasjon med antatt kronebase; ikke en uavhengig bekreftelse».
- `flykart_83ruter.png`: «Historisk scenario avgrenset av høydehint og flyantakelser».
- `fig_stammeplassering.png`: «Utforskende».
- `fig_lyshendelse.png`: «Lysendring uten dokumentert geografisk retning».
- `bro_sjekk_A2.png`: «ingen dokumentert trygg rute».

### 3.1 `fig_kjennetegn_1045.png`: the frame from 21.09 10:45, with ten landmarks (class (b), azimuths from the camera model)

The image is 1600×900; the report's version is 1900×1068. The price sign reads «1 116 897 KR» and the «Horde» logo sits
in front of the box.

| ID | Description (verbatim) | Azimuth |
|---|---|---|
| O1 | «Skrå død stamme/stang bak boksen» | ca. 218° |
| O2 | «Synlig bakkekant bak boksen (lyng → ung skog)» | ca. 219° |
| O3 | «Tørr grein/liten gadd ved bakkekanten» | ca. 223° |
| O4 | «Her sto «stubben» kl. 15.01 – finnes ikke i diffust lys» | ca. 220° |
| O5 | «Høy stamme rett bak boksen» | ca. 222° |
| O6 | «Bjørk med skjev nedre stamme» | ca. 238° |
| O7 | «Stor mørk stamme høyre» | ca. 241° |
| O8 | «Store mørke stammer venstre» | ca. 190° |
| O9 | «Stor stamme venstre-midt» | ca. 201° |
| O10 | «Høye furuer med himmel mellom stammene» (top centre) | ca. 219° |

These are the field-recognition cues: a small clearing, heather that slopes up to an edge of young forest about level
with the box's middle, tall pines with sky between them behind, a birch with a crooked lower trunk right, and dense dark
trunks left.

### 3.2 `fig_bildemaling.png`: measured ground points (1280×720, f = 1068 px)

Caption: «Røde streker: pikselusikkerhet. Vinkelspenn dekker begge kalibreringene (219,6°/+0,2° og 219,2°/−0,9°), f =
1068 px, full bildestråle.» The calibrations are heading/pitch pairs, from sun-path fits at 59.5°N and 61.5°N
respectively [full report p.10].

| Point | Pixel (x, y) [full report p.10] | Azimuth | Elevation (figure label) | Elevation [full report table] | Distance |
|---|---|---|---|---|---|
| M0 ground at box | 617, 630 ± 5 | 218° | −15.3…−13.7° | same | 4.3–5.9 m (box width 2.0 ± 0.2 m) |
| B1 trunk foot left | 80, 490 ± 12 | 192° | −7.5…−5.4° | same | not measured |
| B2 trunk foot left-mid | 400, 490 ± 12 | 207° | (label hidden by blur box) | −8.3…−6.0° | not measured |
| B3 back edge of clearing | 640, 402 ± 5 | 219° | **−3.7…−2.0°** | **−3.4…−1.8°** | unknown (17–44 m withdrawn) |
| B4 birch foot | 996, 498 ± 8 | 238° | −8.2…−6.4° | same | 12–45 m (from trunk width) |
| B5 ground line right | 1200, 505 ± 12 | 247° | −8.2…−6.1° | same | not measured |

My check: azimuth = 219.4° + atan((x − 640)/1068) reproduces all the listed azimuths (M0 218.2°, B1 191.7°, B4 237.8°,
B5 247.1°). The small B3 mismatch between the figure and the full-report table is noted in §7.

### 3.3 Field maps (terrain shading, 5 m contours, canopy ≥2 m in green, OSM roads in red with dashed tractor roads, streams in blue, camera and FOV in orange, nearest road point as a red square; «Veipunkter er ikke bekreftede parkeringsplasser. Prikkede forbindelser kan være luftlinjer»)

| Map | Points printed on map | Road point | Box→road bearing / straight line (my pyproj calc) |
|---|---|---|---|
| `kart_1_E6.png` «1 · Myklebysætervegen vest (E6)» | **1: 61.39950, 11.03156**; **1b: 61.39770, 11.03178**. «Fem posisjoner består innenfor ca. 200 m; 1 og 1b markerer ytterpunktene» | 61.39921, 11.04086 | 1: 93.7°, 498 m; 1b: 70.9°, 513 m |
| `kart_2_E3.png` «2 · Madsskardvegen, traktorveg (E3)» | **2: 61.44432, 11.12340** | 61.44206, 11.13007 (end of a dashed tractor road) | 125.3°, 436 m |
| `feltsone_Messelt_S1_S2_N1_N2.png`. Four control points from the same road end (tractor road **OSM 632102560**) | **S1: 61.45713, 10.83615**; **S2: 61.45448, 10.84063**; **N1: 61.45998, 10.84925** (label partly covered; last digits «4925» legible); **N2: 61.45986, 10.85133**. N1/N2 are «svakere, over åpen myr» | 61.45425, 10.84350 | S1 129.3°, 507 m; S2 99.5°, 155 m; N1 205.7°, 708 m; N2 213.7°, 752 m |
| `kart_4_E1.png` «4 · Madsskardvegen øst (E1)» | **4a: 61.45182, 11.14283**; **4b: 61.45179, 11.13851** | 61.44828, 11.14333 (on a paved road, south) | 4a 176.1°, 395 m; 4b 146.7°, 468 m |
| `kart_5_E2.png` «5 · Jernvinnevegen (E2)» | **5a: 61.43511, 11.14349**; **5b: 61.43444, 11.13907**; **5c: 61.43531, 11.13483** | 61.43345, 11.14330 | 5a 183.1°, 185 m; 5b 116.0°, 251 m; 5c 114.6°, 497 m |

Note: S1 (61.45713, 10.83615) is the **same point as v6 camera C23** (61.45712966, 10.83614627) and ≈ G16. S2 ≈ G18
(61.45446, 10.84064).

### 3.4 `bro_sjekk_A2.png`: access at A2

Three panels over a 360 × 360 m window: DTM1 hillshade, DOM hillshade, and DOM−DTM (0–20 m). They show the end of the
tractor road (red square), C07 (orange) and Nørdre Eldåa (blue). The title asks «Ser vi en bro i DOM?»: no bridge is
visible. C07 sits on the north side of the ravine. There, DOM−DTM shows tall trees (15–20 m, yellow) around a treeless
opening (dark) with scattered single trees, so C07 is at the edge of an open patch. The road end is on the south side,
in medium forest.

### 3.5 `fig_stubbe_sammenligning.png`: withdrawal of B3

Crops at x 800–1150, y 400–750 (1920 px scale): 15:01 (1280 scaled ×1.5), 10:15 and 10:45. The bright «stubbe» at
x ≈ 950–975 is present only at 15:01. Full report p.10: brightness is flat in the morning but «40–52 mot 25–30 i
ettermiddagssola». The original stump assumption was 0.25–0.5 m wide and 13–16 px, which gave 17–44 m.

### 3.6 `fig_stammeplassering.png`: trunk placement (exploratory)

Cyan marks trunks measured in the day frame. Red marks lidar trees (local top points ≥8 m within 40 m) in the computed
direction. Scores:

- **C07 (A2): 8/10**
- G02/F01 representative (A2): 6/10
- **C23 (S-Messelt): 8/10**
- G16/F17 representative (S-Messelt): 10/10

### 3.7 `syntetisk_utsyn_kronebase40.png`: synthetic views (illustration)

Built from DTM1 + DOM («DOM-årgang ikke verifisert»). Blue is sky, brown is ground, green is canopy, and lighter means
farther (log scale 1–300 m). «Nederste 40 % av kronehøyden regnet som gje[nnomsiktig]» (the lower 40 % of crown height
is treated as transparent). The dashed outline is the box, which does not exist in DOM.

Panels:

- The day frame 21.09 «nominelt 15.01.06», brightened.
- C06 (A2): camera 1.76 m.
- C07 (A2): 1.58 m.
- F01, local best (A2): 1.56 m.
- C23 (S-Messelt): 1.87 m.
- F17, local best (S-Messelt): 1.78 m.
- All panels use calibration K1, with the horizontal axis spanning 189–251°.

Observation: C06's view is almost entirely near canopy, which is inconsistent with the visible clearing. C07, F01 and C23
show a ground line with canopy above, roughly like the photo. The full report p.13 says: «De bygger på samme data som
testen og er ikke en uavhengig bekreftelse.»

### 3.8 `fig_lyshendelse.png`: the night light event of 22.09 about 21:35

- Light level against file offset: «steg ned 49,8–50,3 s og gradvis opp ca. 101–105 s, nesten bare i venstre kant».
  The left edge drops about −14 units; the right and top-centre drop about −2.5, then recover to about +1.
- A ratio image (150 s / 80 s) shows an increase at the left edge.
- A simultaneous whiteboard (median of 100 frames) reads «DET ER INGEN LYS RUNDT KASSEN».
- In the night crop, lights are reflected in the box glass, and the red area on the left is where the light changed.
- The report concludes it is probably an equipment lamp and gives no direction to road or house.

### 3.9 `sol_og_temp.png` (= report Figure 4)

Left panel: eastern terrain horizon (96–102°) per area. Grey marks all positions, green those with access, and orange is
the sun at 07:51 (5.7°). Values read from the plot for positions with access:

- A1 ≈10, 10 and 15.6°: all above the line.
- A2 ≈9.4 and 12.7°: above.
- S-Messelt ≈−2.5 and −1.8°.
- N-Messelt ≈0.3 and 0.8°.
- Punkt 7 ≈−4, −3.5 and 7.4°.
- E1 ≈−0.8, 1.2, 2.0 and 5.4°.
- E2 about 3–11.4°: many positions, spread on both sides of the line.
- E3 ≈−3.2, −1.2, 6.0 and 9°.
- E4 ≈4–19.5°.
- E5 ≈6–14.8°.
- E6 ≈−2.2 to −0.5°: all well below.

Right panel: modelled temperature (■ day max, ● 19:35) against the board's «NÅ CA 8–11 °C» band and the «CA 12 °C
(DAGEN)» line. E4 Ole Evenstads vei has the highest day max, ≈15.2 °C.

### 3.10 `oversikt_temp.png` (= report Figure 1)

MET Nordic at 19:35 on 21.09 over 61.25–61.60 N, 10.6–11.4 E, with an 8 °C isoline. It marks points 1–5, A1, A2, P7,
H2 and Evenstad. Digitised: **H2 ≈ 61.355, 10.990** (±0.003°; not given as a number anywhere in the text). P7 ≈ 61.3745,
10.977, which matches v6 G15 at 61.37447, 10.97722. The west-of-Glomma plateau is cold (3–7 °C); the valley and east
side are 8–11 °C.

### 3.11 `flykart_83ruter.png`: the first flight analysis (historical, superseded)

The model: 17 234 cells of about 500 × 500 m in the 790–911 moh band, at most 900 m from a road, tested against three
flights. The thresholds were ≥35°, ≥25° and ≥25° elevation. Full report p.5 lists the flights as:

- 21.09 21:29–21:34: NOZ56U or NOZ9EG.
- 22.09 20:32–20:34: SAS39A, Bodø–Oslo, southbound down Østerdalen.
- 22.09 20:34–20:36: NOZ55J, Bodø–Oslo, about 21 000 ft.

Only 83 cells passed, «alle i ett høydedrag vest for Glomma mellom Mykleby og Evenstad». I digitised the axes-calibrated
markers:

- 76 orange cells are visible, and 7 more are hidden under the red circles, making 83. The grid is 0.005° lat × 0.01°
  lon, over 61.30–61.405 N and 10.88–11.08 E.
- «Mine søkepunkter 1–7» (old search points):
  - 1: 61.310, 10.970
  - 2: 61.320, 10.970
  - 3: 61.335, 10.950
  - 4: 61.310, 11.000
  - 5: 61.340, 10.980
  - 6: 61.365, 10.988 (next to «Myklebysætra (ca.)» at about 61.364, 10.994)
  - 7: 61.375, 10.980, which matches P7.
- «Myklebysjøen (989 moh)» at about 61.319, 10.902.
- **default.no's 40 stops** (blue diamonds, ±0.001°): 61.5149/11.0453, 61.4880/11.0453, 61.4739/11.1090,
  61.4730/10.9690, 61.4730/11.0500, 61.4730/11.0963, 61.4730/11.1389, 61.4709/10.9802, 61.4680/11.0331,
  61.4640/11.0841, 61.4629/10.9601, 61.4629/10.9760, 61.4629/11.1033, 61.4559/11.0631, 61.4530/10.9521,
  61.4530/11.1333, **61.4519/11.1459 («default.no stopp 1»)**, 61.4469/10.9648, 61.4449/11.1193, 61.4400/10.9512,
  61.4389/11.1253, 61.4359/11.1370, 61.4339/11.0879, 61.4290/10.9498, 61.4290/11.0982, 61.4258/11.0121,
  61.4258/11.1272, 61.4218/11.0570, 61.4050/11.0322, 61.4018/11.0542, 61.3949/11.0341, 61.3929/11.0490,
  61.3888/11.0149, 61.3868/11.1403, 61.3839/11.0078, 61.3810/11.1211, 61.3769/11.0200, 61.3758/11.1431,
  61.3668/11.0870, 61.3478/10.9901.
- Full report p.9 gives stop 1 as 61.4520, 11.1460 (Madsskardveien east of Glomma), essentially report candidate 4.

The full report p.6 has a later refinement. With original ADS-B and per-day delays, the two 22.09 flights point
different ways: NOZ55J favours the north (Gålaveien, Birkebeinerveien, Messelt) and SAS39A the south (Myklebysætra, H2,
P7). This depends on reaction times, a 25° threshold and a 15–50 s delay, «og ingen av disse er sikkert dokumentert».
«armens retning kan ikke brukes, fordi dybden er usynlig.»

---

## 4. Bevis branch `bevis/claude-2026-09-25/`: file by file

Commit history (mirror):

- `b370c19` 03:11 PDT: «Bevispakke (skript, data, målinger) fra Claude for #1, #2 og #5 – stillbilder holdt tilbake».
- `547239f` 03:19: «K0-K4-reproduksjon og åpningstest ved publiserte koordinater (#8)».
- `57cd0b2` 04:02: «Sol-grense uavhengig av belyst flate (#2) og tilt-tabell for 21.29-gesten (#9)».
- `4baabc5` 04:09: «Morgensolgrense på v6-kameraposisjoner (#8)».
- Upstream only: `e8178da` 13:57 PDT (22:57 CEST): «Solkart 25.09 14:30–15:10Z …(#10)».

The GitHub issues #1–#10 themselves could not be read, because the API is not enabled for this session. They are known
only through README and commit summaries.

### 4.1 `README.md`: claims and their tags

- :3: «Hver påstand er merket [verifisert], [ikke verifisert] eller [vurdering].» Runs on Node 18+ with no dependencies.
- :5: stills are **withheld**: `sekvens.jpg`, `f_*.jpg` and `tavler/`, because Anja is visible. Clips are identified by
  SHA-256.
- :8-10: sources are default.no minute clips of Horde's stream (labelled 2026-09-21 and 2026-09-22), downloaded 25.09;
  adsb.lol `globe_history trace_full` (ODbL) for hex 4791ac and 47a3b0 on 2026-09-21; and Kartverket NHM DTM1/DOM1 via
  `ws.geonorge.no/hoydedata/v1` and `hoydedata.no/arcgis/rest/services/NHM_{DTM,DOM}_25833/ImageServer`.
- :13-16: the sun sequence uses frames at 07:40, 07:44, 07:47, 07:49, 07:50 and 08:00 (plus 08:30), each taken 30 s into
  its minute clip.
  - Orange frame = crown and stems top right, x 1500–1920 and y 0–300 of 1920×1080. That is «asimut 238–250° og +8,5
    til +18,6°, med f = 1602 px … og kurs 219,4°». I verified the mapping: 219.4 + atan(540/1602) = 238.0°;
    219.4 + atan(960/1602) = 250.3°; atan(540/1602) = 18.6°; atan(240/1602) = 8.5°.
  - Cyan = sky reference. White = ground 4.6–7.5 m in front (y 860–1060 → −11.3 to −18.0° at 1.5 m height).
- :19-24 **[verifisert på disse klippene]**:
  - «Forholdet krone/himmel er 0,29–0,33 fram til 07.44, og stiger til 0,39 (07.47), 0,53 (07.49) og 0,66 (07.50).
    Det holder seg på 0,58–0,68 til 08.00 og er nede i 0,29 kl. 08.30.»
  - «Himmelreferansen og bakken går litt *ned* … (himmel 83 → 78, bakke 21 → 18). Økningen er altså lokal».
  - «skarpt avgrenset, varmt lys på stammen og grangreinene til høyre fra 07.47. Det er tegn på direkte sol.»
  - «Bakken får ikke direkte sol før 08.00.»
  - **[vurdering]:** «Svake varme flekker på enkelte stammer midt/venstre finnes allerede 07.40–07.44 … Første direkte
    sol et sted i bildet kan altså være tidligere enn 07.47, men ikke senere.»
- :26 **[ikke verifisert]**: the original video. «Klippene er default.nos opptak, og strømforsinkelse og klokkeslett er
  slik de er merket.» Mean colour (R/B) does not rise, so colour is not used as evidence.
- :29-35: whiteboards read by Claude (class (a), read from withheld stills):
  - `2109_1844_UJEVNT.png` (clip b18-44-14): «STARTET 07 00 / UJEVNT TERRENG, MYE LYNG / HØRER IKKE MYE FRA BOKSEN»
  - `2109_1938_4_STORE_STEINER_TIL_VENSTRE.png` (clip b19-38-13): «4 STORE STEINER TIL VENSTRE, KUN STEIN DER»
  - `2209_1856-1905_FJELLUFT_STI_BLANDET_SKOG.png`: «JA, FØLES SOM FJELLUFT» · «GIKK IKKE PÅ STI, MEN KUPERT
    TERRENG» · «BLANDET SKOG, VELDIG HØYE TRÆR, KUPERT TERRENG, SOM GÅR SLAKT SLIK:», plus «en tegnet slak kul»
  - «…DER JEG GIKK I GÅR» (24.09) is **not** included and is still [ikke verifisert].
- :38-41: horizon and canopy files (see §4.5). «Resultatene viser at testen **ikke skiller**» (the canopy tests). Raster
  values were checked against the point API: **DOM 604.19 / DTM 593.79 at candidate 1**, which implies about 10.4 m of
  canopy exactly at the candidate 1 coordinate and agrees with kkrav's K0 value of 10.4 m.
- :44-48: `fly_2109.mjs` uses `alt_geom` (field 10, GNSS feet) and not the barometric level. It subtracts site elevation,
  includes Earth curvature, interpolates, and uses delays of 15, 22, 30, 45 and 50 s from stream 21:29:38, «da hun
  begynner å peke. default.no målte ca. 22 s.»
- :51-58 **[verifisert]**: at 22 s, NOZ9EG is at 33° from Kand. 1, 24° from Messelt, 20–26° from the other candidates and
  7° from Løten. NOZ56U is at 28° from Løten.
- :60: «Ingen kandidat har et fly i nærheten av «rett opp» i det øyeblikket hun peker. Ved 45 s er kandidat 1 på 46°.
  Tallene i #1 (47° mot Messelts maks på 63°) blandet et øyeblikksbilde og et maksimum, og brukte 45 s. Det er **feil
  sammenligningsgrunnlag**, som Codex påpekte.» This is a self-retraction.
- :62 **[verifisert i default.no osint_notes]**: «kl. 21:27:42 signaliserte hun et stjerneskudd, og kl. 21:29:10 ba
  chatten henne peke dit. Pekingen 21:29:38–53 kan altså gjelde stjerneskuddet og ikke et fly.»

### 4.2 `kildeklipp_sha256.txt`: source clip identities (18 files)

Minute clips from 21.09: `07-20.mp4`, `07-30`, `07-40`, `07-44`, `07-47`, `07-49`, `07-50`, `07-51`, `07-52`, `07-53`,
`07-55`, `08-00` and `08-30`.

Whiteboard clips from 21.09: `b18-44-14.mp4` and `b19-38-13.mp4`.

Stills from 22.09: `s22_18-56-41.png`, `s22_18-57-41.png` and `s22_19-05-42.png`.

Example hashes: `07-47.mp4` is `7339fd71…286df` and `08-00.mp4` is `bbaefbc6…bd5be`. The full list is in the file. They
allow matching against default.no's clip archive (in the MagnusPladsen mirror or elsewhere).

### 4.3 `sol/maling.csv` + `sol/rgb.mjs`: the sun-sequence photometry (class (b))

`rgb.mjs` averages R, G and B over a raw rgb24 crop piped from `ffmpeg -ss 30 … -vf crop=… -f rawvideo -pix_fmt rgb24`.

| time (clip label) | crown R | G | B | R/B | sky Y | ground R | G | B | **crown/sky** |
|---|---|---|---|---|---|---|---|---|---|
| 07:20 | 24.1 | 23.6 | 23.7 | 1.02 | 81.5 | 20.6 | 20.6 | 20.5 | 0.29 |
| 07:30 | 28.0 | 27.2 | 27.4 | 1.02 | 83.2 | 20.7 | 20.8 | 20.6 | 0.33 |
| 07:40 | 26.7 | 26.1 | 26.4 | 1.01 | 83.3 | 21.6 | 21.7 | 21.5 | 0.32 |
| 07:44 | 27.7 | 26.5 | 27.8 | 1.00 | 83.2 | 21.4 | 21.4 | 21.2 | 0.32 |
| **07:47** | 32.2 | 31.3 | 33.0 | 0.98 | 81.7 | 20.5 | 20.5 | 20.4 | **0.39** |
| 07:49 | 40.6 | 41.9 | 44.0 | 0.92 | 79.0 | 18.9 | 18.9 | 18.8 | 0.53 |
| 07:50 | 50.4 | 52.0 | 53.6 | 0.94 | 78.2 | 18.7 | 18.7 | 18.5 | 0.66 |
| 07:51 | 48.2 | 48.8 | 50.4 | 0.96 | 77.4 | 18.1 | 18.1 | 18.0 | 0.63 |
| 07:52 | 46.6 | 49.8 | 50.7 | 0.92 | 79.1 | 18.4 | 18.4 | 18.3 | 0.62 |
| 07:53 | 49.5 | 53.9 | 53.5 | 0.93 | 77.1 | 18.0 | 18.0 | 17.9 | 0.68 |
| 07:55 | 44.7 | 45.5 | 46.5 | 0.96 | 77.6 | 18.2 | 18.2 | 18.1 | 0.58 |
| 08:00 | 45.4 | 48.9 | 49.2 | 0.92 | 78.7 | 18.6 | 18.6 | 18.5 | 0.61 |
| 08:30 | 21.6 | 21.5 | 22.3 | 0.97 | 74.5 | 20.6 | 20.4 | 20.4 | 0.29 |

Interpretation, which is theirs and which I agree with:

- A step starts between 07:44 and 07:47 and saturates by 07:50. The ground stays flat, so it gets no direct sun up to
  08:00.
- The patch is dark again by 08:30, so the lit patch was fed through a temporary gap in the east.
- The sun moves from 98.1°/5.3° at 07:47 to 100.9°/6.8° at 08:00 and 107.7°/10.2° at 08:30 (see §4.4).
- This contrasts with default.no's «strongest 08:25–09:55», which likely refers to other parts of the frame.

### 4.4 NOAA sun (`horisont/sun.mjs`): my re-run at 61.43 N, 11.08 E, 21.09.2026 (CEST, refracted elevation)

| time | az | el | | time | az | el |
|---|---|---|---|---|---|---|
| 07:20 | 92.1 | 2.23 | | 07:51 | 98.9 | 5.77 |
| 07:40 | 96.5 | 4.50 | | 07:55 | 99.8 | 6.23 |
| 07:44 | 97.4 | 4.96 | | 08:00 | 100.9 | 6.80 |
| 07:47 | 98.1 | 5.30 | | 08:25 | 106.5 | 9.67 |
| 07:49 | 98.5 | 5.54 | | 08:30 | 107.7 | 10.23 |
| 07:50 | **98.7** | 5.65 | | 17:23 | 246.7 | 12.84 |

Further results from the same re-run:

- 10:15: az 132.6°, el 21.0°. 10:45: az 140.2°, el 23.4°. 15:01: az 211.4°, el 25.6°.
- Flat-horizon sunrise at Evenstad: 21.09 06:59, 22.09 07:00, 23.09 07:02, 24.09 07:05, 25.09 07:07 CEST, az 87.5–90°.
  This is consistent with the full report's 23.09 value of 07:01–07:04, and with «SOLA VAR OPPE FØR 07» not
  discriminating.
- 21.09 at 21:29 CEST: sun at −15.5°. It is dark, so aircraft lights and a shooting star would be visible.
- 25.09 14:33–15:22Z (16:33–17:22 CEST) at Evenstad: az 234.6 → 246.1°, el 16.5 → 11.4°. That is **inside the camera's
  field of view** (188.7–250.5°), so a sun star in the frame is geometrically possible (§4.7).
- **Flag (my finding).** `grense_2.mjs`, `grense_2b.mjs` and `grense_v6.mjs` use `SAZ = 97.9` and label it «kl. 07.50
  (asimut 97,9°, 5,65° refraktert)». NOAA gives 97.9–98.1° at **07:47** but **98.7°** at 07:50; `terrain_resultat.txt:1`
  itself prints «07:47 az 98.1». The azimuth is therefore about 0.8° early for 07:50, while the elevation (5.65°) is
  correct for 07:50. This probably has minor effect, since the ridge sampling line shifts about 11 m at 800 m, but it
  is not verified.

### 4.5 `horisont/`: terrain, canopy and sun-limit scripts (class (d); DTM/DOM from Kartverket NHM)

Common conventions in these scripts:

- `utm.mjs` does WGS84↔UTM33 (Krüger, 3-term).
- `fetch.mjs` pulls raw F32 exports from the NHM ImageServer, bilinear, «de siste W·H/8 bytene er en maskeband».
- `gdir()` gives the local grid direction of a true azimuth.
- **Camera = published coordinate (box) + 5 m toward 39°**, at 1.5 m eye height, except grense_v6, which uses v6 camera
  coordinates directly.
- Refraction coefficient k = 0.13; Earth radius 6 371 000 m.
- Rays are sampled with fine DTM1 up to 950–1200 m, then a 20 m DTM out to 20 km.

#### 4.5.1 `horisont_api.mjs` → `horisont_api_resultat.txt` (point API only; reproduced by Codex)

This takes the maximum elevation angle along a geodesic at **az 98.8° (the 07:51 sun)**, from 1.5 m eye height. Steps
are 25 m out to 3 km, then 100 m out to 20 km. Curvature and refraction are included.

| Site | Ground moh | Horizon | Obstacle at |
|---|---|---|---|
| 1 Myklebysæterveien vest | 593.8 | **0.5°** | 3200 m, 623 moh |
| 2 Madsskardveien traktorvei | 597.6 | **1.8°** | 2425 m, 677 moh |
| 3 Sørlige Messelt S1 | 898.1 | **−0.4°** | 18 500 m, 789 moh |
| 3 Sørlige Messelt S2 | 876.6 | **−0.5°** | 17 700 m, 747 moh |
| 4 Madsskardveien øst | 646.4 | **3.8°** | 1475 m, 745 moh |
| 5a Jernvinneveien | 555.8 | **8.4°** | 800 m, 676 moh |
| 5b Jernvinneveien | 542.5 | **7.3°** | 1050 m, 679 moh |
| 5c Jernvinneveien | 528.0 | **6.6°** | 1300 m, 681 moh |

The sun is at 5.7° (07:51) or 6.8° (08:00), so 5a and 5b are terrain-shadowed at ground/eye level until after 08:00, and
5c until about 08:00.

#### 4.5.2 `terrain.mjs` → `terrain_resultat.txt` (1 m DTM raster; camera = box + 5 m @39°)

Sun (header line): 07:47 az 98.1°, el 5.30°; 07:50 el 5.65°; 08:00 az 100.9°, el 6.80°.

| Site | Horizon from 1.5 m, az 97/99/101 | From 20 m (crown height) | Blocking ridge @20 m, az 99 | 5×5 neighbourhood (10 m) min/max @20 m |
|---|---|---|---|---|
| 1 Myklebysæterveien vest | 0.8/0.5/1.1 | 0.3/0.1/0.7 | 3210 m, 623 moh (site 594) | 0.1/0.3 |
| 2 Madsskardveien traktorvei | 2.0/1.8/1.7 | 1.6/1.4/1.3 | 2430 m, 676 (597) | 1.4/1.5 |
| 3a S-Messelt S1 | −0.7/−0.5/−0.5 | −0.8/−0.5/−0.6 | 18 450 m, 776 (897) | −0.5/−0.5 |
| 3b S-Messelt S2 | −0.5/−0.5/−0.3 | −0.6/−0.5/−0.4 | 17 630 m, 751 (876) | −0.6/−0.5 |
| 4 Madsskardveien øst | 3.5/3.6/3.7 | 2.8/2.9/3.0 | 1570 m, 748 (648) | 2.9/3.1 |
| 5 Jernvinneveien | 8.3/8.4/8.4 | **7.0/7.1/7.1** | 817 m, 679 (556) | 6.9/7.4 |
| A1 Birkebeinerveien | **11.0/11.1/11.0** | **6.7/7.2/7.1** | **269 m**, 659 (605) | 6.3/7.7 |
| A2 Gålaveien C07 | 2.8/2.6/2.6 | 2.5/2.3/1.8 | 8130 m, 717 (365) | 2.2/2.4 |

At both Jernvinneveien and A1 the horizon is still above the 07:50 sun (5.65°) even from 20 m, across the whole
neighbourhood.

#### 4.5.3 `e2check.mjs` (no committed result file)

This re-checks 5a, 5b and 5c at az 96, 98.8 and 101 with the raster, and profiles the point API at 200, 400, 600, 800,
1000 and 1500 m along 98.8°. It was used to cross-validate the raster method against the API. The output is not
published.

#### 4.5.4 `canopy2.mjs` → `canopy2_resultat.txt`: crown-patch sunlight via camera rays (opaque DOM)

Method:

- 13 azimuths (238–250°) × 11 elevations (8.5–18.6°) = 143 camera rays per position. The first DOM hit with
  canopy >2 m within 120 m is the «patch» point.
- Ground points are at 4.6, 5.5, 6.5 and 7.5 m for az 190–250° (step 4°), +0.3 m.
- Each point is traced toward the sun at 07:40, 07:44, 07:47, 07:50, 08:00 and 08:30, over DOM (≤950 m) and DTM beyond,
  skipping the first 2 m.
- Consistency rule: patchN ≥ 40; patch lit <15 % at 07:40; ≥20 points brighter by 07:50; ground lit <15 % at 08:00.
- Tested over a 5×5 neighbourhood at 10 m spacing.

Share of the patch in direct sun at the centre position, in %, at 07:40/44/47/50/08:00/08:30:

| Site | pos OK/25 | centre patch lit % | centre ground lit % | patchN |
|---|---|---|---|---|
| 1 Mykleby | 0 | 0 0 0 0 0 0 | 0 0 0 0 0 0 | 143 |
| 2 Madsskard | 0 | 55 55 59 53 55 34 | 0 0 0 0 0 0 | 143 |
| 3a S1 | **1** (offset E0, N+20) | 0 0 0 0 0 0 | 0… | 143 |
| 3b S2 | 0 | 0… | 0… | 143 |
| 4 Madsskard øst | 0 | 0… | 0… | 143 |
| 5 Jernvinne | 0 | 0… | 0… | 143 |
| A1 | 0 | 0… | 0… | 143 |
| A2 C07 | 0 | 1 4 7 8 66 67 | 0 0 0 0 0 2 | 143 |

The authors' verdict (README :40) is that the test **does not discriminate**. With opaque 1 m DOM, a ray from a crown
point toward a 5–6° sun almost always hits another crown. At Madsskard (2) the patch is lit already at 07:40, and at A2
it is lit only at 08:30.

#### 4.5.5 `canopy3.mjs` → `canopy3_resultat.txt`: sensitivity (medians over 25 positions)

This adds binary lit share with a 5 or 10 m own-crown skip, and porous-crown transmission T = exp(−L/15), where L is the
metres of sun ray below the DOM surface within 400 m. It also reports the share of patch points **terrain**-blocked at
07:50. Times are 07:40, 07:47, 07:50, 08:00 and 08:30.

| Site | skip5 lit % | skip10 lit % | **T %** | terrain-blocked @07:50 |
|---|---|---|---|---|
| 1 Mykleby | 0 0 0 0 0 | 0 0 0 0 0 | 39 37 39 41 42 | 0 % |
| 2 Madsskard | 0… | 0… | 56 55 56 58 70 | 0 % |
| 3a S1 | 0… | 0… | 41 39 42 40 50 | 0 % |
| 3b S2 | 0… | 0… | 35 40 40 44 57 | 0 % |
| 4 Madsskard øst | 0… | 0… | 11 14 19 30 44 | 0 % |
| 5 Jernvinne | 0… | 0… | **0 0 0 0 23** | **100 %** |
| A1 | 0… | 0… | **0 0 0 0 0** | NaN % (my reading: some neighbourhood positions had no crown hits in the patch, which is consistent with A1's low canopy) |
| A2 C07 | 0 0 0 0 0 | 0 0 0 0 38 | 51 55 56 64 83 | 0 % |

Reading:

- Transmission shows **no step between 07:40 and 07:50** at any site, whereas the observation shows a sharp step, so the
  model does not reproduce the event.
- The robust signal is the terrain column. At Jernvinneveien every crown-patch point is terrain-shadowed at 07:50, and
  A1 gets zero transmission at all times.

#### 4.5.6 `grense_2.mjs` → `grense_2_resultat.txt`: the sun limit independent of which surface was lit (DTM only)

For each point in the field of view (az 188–250° every 2°, 5–150 m every 5 m, which is 960 points), the script finds the
lowest height above ground z* at which the terrain lets the 07:50 sun through. If min z* exceeds the tallest tree, no
surface in the image could have been sunlit then.

| Site | Lowest height needed | where (az, range) |
|---|---|---|
| 5a Jernvinneveien | **38.2 m** | 232°, 150 m |
| 5b Jernvinneveien | **32.4 m** | 250°, 15 m |
| 5c Jernvinneveien | **17.3 m** | 214°, 80 m |
| A1 Birkebeinerveien | **32.3 m** | 188°, 120 m |
| 1 Myklebysæterveien (control) | **0.0 m** | 188°, 5 m |

#### 4.5.7 `grense_2b.mjs` → `grense_2b_resultat.txt`: the same, restricted to the observed light sector az 238–250° (390 points)

- 5c: **18.5 m** (249°, 65 m)
- 5b: **32.4 m** (250°, 15 m)
- 5a: **39.1 m** (238°, 150 m)

Compare with kkrav's view p99 canopy at 5a of 15.9 m (p90 12.6 m).

- 5a and 5b need surfaces two or more times taller than any tree, so they are inconsistent with the observed 07:47–07:50
  crown light.
- 5c needs ≥18.5 m trees at 65 m, which is plausible only for the tallest trees and borderline.

#### 4.5.8 `grense_v6.mjs` + `punkter_v6.csv` → `grense_v6_resultat.txt`: the limit at the report's own v6 camera positions (no +5 m)

| id | area | lat | lon | min height needed in light sector @07:50 |
|---|---|---|---|---|
| C06 | A2 | 61.46235821 | 10.97495372 | 0.0 m (238°, 5 m) |
| C07 | A2 | 61.46254284 | 10.97511774 | 0.0 (238°, 15 m) |
| C23 | M_61.455_10.840 | 61.45712966 | 10.83614627 | 0.0 |
| G01 | A2 | 61.46155565 | 10.96940245 | 0.0 |
| G02 | A2 | 61.46248690 | 10.97504982 | 0.0 (238°, 10 m) |
| **G03** | **A1** | 61.45156098 | 10.97210562 | **54.0** (238°, 40 m) |
| G04 | A2 | 61.46323636 | 10.98276887 | 0.0 |
| **G05** | **A1** | 61.44499574 | 10.97473768 | **20.8** (248°, 115 m) |
| G06 | A2 | 61.46606120 | 10.97432492 | 0.0 |
| G07 | M_61.455_10.840 | 61.45498664 | 10.84898097 | 0.0 |
| G08 | A2 | 61.46249872 | 10.98275126 | 0.0 (240°, 115 m) |
| **G09** | **A1** | 61.45294069 | 10.97853232 | **16.5** (242°, 65 m) |
| G10 | A2 | 61.46589838 | 10.97915615 | 0.0 |
| G11 | A2 | 61.46199060 | 10.98259133 | 4.9 (250°, 150 m) |
| G12 | A2 | 61.46171153 | 10.98349153 | 2.5 (238°, 45 m) |
| **G13** | **A1** | 61.44856281 | 10.98471837 | **5.8** (250°, 100 m) |
| G14 | A2 | 61.46582856 | 10.97375371 | 0.0 |
| G15 | P7 | 61.37446824 | 10.97722068 | 0.0 |
| G16 | M_61.455_10.840 | 61.45711061 | 10.83611124 | 0.0 |
| G17 | A2 | 61.46334804 | 10.98046231 | 0.0 (248°, 145 m) |
| G18 | M_61.455_10.840 | 61.45446203 | 10.84063536 | 0.0 |
| G19 | M_61.460_10.850 | 61.45677174 | 10.85557731 | 0.0 |
| G20 | A2 | 61.46492173 | 10.98078535 | 0.0 (238°, 20 m) |
| **G21** | **A1** | 61.45073889 | 10.98169609 | **25.1** (250°, 10 m) |
| **G22** | **A1** | 61.45257416 | 10.97991937 | **20.9** (250°, 15 m) |
| G23 | A2 | 61.46182184 | 10.97201704 | 0.0 |
| G24 | M_61.460_10.850 | 61.46226205 | 10.84988654 | 0.0 |

Reading:

- This bounds only terrain. All A2, Messelt and P7 v6 positions pass trivially, since the terrain lets the sun reach
  ground level.
- All six A1 positions need surfaces 5.8–54 m high. G13 (5.8 m) and G09 (16.5 m) remain physically possible given tall
  enough trees; G03 (54 m) is impossible, and G05, G21 and G22 (21–25 m) are unlikely.
- The earlier report narrative that A2 fails morning sun is **not** supported at these positions on terrain alone. The
  report's A2 failure came from the combined «access + sun» filter (PRESISERINGER.md:23).

#### 4.5.9 `kkrav.mjs` → `kkrav_resultat.txt`: K0–K4 forest requirements re-run at the published coordinates

Definitions (full report p.12, «låst før de ble kjørt»):

- **K0** (box site): 212–226°, 3–7 m, median <3 m.
- **K1** (clearing): 213–226°, 8–17 m, median <3 m.
- **K2** (left): 190–207°, 3–20 m, p90 ≥10 m.
- **K3** (right): 232–250°, 5–25 m, p90 ≥10 m.
- **K4** (background): 213–226°, 25–70 m, p90 ≥12 m.

The camera is at box + 5 m toward 39°, tested over a 5×5 (10 m) neighbourhood. The script also reports p90/p99 canopy
over the whole view (188–250°, 5–70 m) as a check on «veldig høye trær».

| Site | pass/25 | centre K0 / K1 / K2 / K3 / K4 (value, m) | view p90 / p99 canopy |
|---|---|---|---|
| 1 Myklebysæterveien vest | **0** | **✗10.4** / ✓0.2 / ✓15.6 / ✓11.5 / ✓17.9 | 17.3 / 21.3 m |
| 2 Madsskardveien traktorvei | 1 | ✓0.1 / ✓0.1 / ✓13.9 / ✓12.2 / ✓12.4 | 12.2 / 16.9 |
| 3a S-Messelt S1 | 2 | ✗8.0 / ✗6.9 / ✓17.5 / ✗5.9 / ✓13.5 | 12.8 / 18.5 |
| 3b S-Messelt S2 | 0 | ✓0.7 / ✗4.2 / ✗8.9 / ✗5.5 / ✓13.2 | 11.7 / 17.7 |
| 4 Madsskardveien øst | 1 | ✓0.5 / ✓2.8 / ✓14.7 / ✓16.5 / ✓18.0 (centre passes all) | 14.8 / 20.2 |
| 5a Jernvinneveien | 2 | ✗12.4 / ✓3.0 / ✓11.0 / ✓12.2 / ✓12.8 | 12.6 / 15.9 |
| A1 Birkebeinerveien | 0 | ✓0.9 / ✓0.4 / ✗5.6 / ✗2.8 / ✗1.8 | **2.3 / 9.1** |
| A2 Gålaveien C07 | **4** | ✓0.0 / ✓0.1 / ✓13.2 / ✓14.7 / ✓13.3 (centre passes all) | 15.5 / 20.3 |

Reading:

- The published «Kassen (ca.)» coordinates do **not** reproduce the report's forest pass. The report's grid positions
  must differ, or the coordinates are rounded.
- Candidate 1 fails K0 at every neighbourhood position.
- A1 is essentially treeless in view (p99 9.1 m), which fits the main README: «Det eksakte A1-punktet har svak
  skogstøtte». Codex found 0 of 25 positions passing at A1.
- A2 C07 and Madsskard øst are the best forest matches at the published points.

#### 4.5.10 `opening.mjs` → `opening_resultat.txt`: openness around the camera

Each cell gives the share of CHM <3 m and the median CHM, per sector and band (10–50 | 50–150 | 150–300 m).

| Site | E 80–115° (toward morning sun) | SE 115–150° (road direction ≈130°) | N 330–30° | View SW 188–250° |
|---|---|---|---|---|
| 1 Mykleby | 72%/0m 87%/0m 50%/3m | 51%/3m 81%/0m 68%/1m | 48%/3m 38%/5m 44%/4m | 26%/9m 33%/6m 64%/1m |
| 2 Madsskard | 63%/2m 61%/1m 72%/1m | 65%/1m 69%/1m 66%/1m | 36%/5m 35%/5m 61%/1m | 33%/6m 29%/6m 28%/6m |
| 3a S1 | 59%/1m 55%/2m 82%/0m | 60%/1m 59%/2m 70%/0m | 69%/0m 73%/0m 73%/0m | 56%/2m 62%/1m 68%/1m |
| 3b S2 | 71%/0m 73%/0m 74%/0m | 61%/1m 72%/0m 72%/0m | 53%/2m 69%/1m 82%/0m | 48%/3m 75%/0m 76%/0m |
| 4 Madsskard øst | 69%/1m 76%/0m 66%/1m | 63%/1m 60%/2m 52%/3m | 92%/0m 82%/0m 68%/1m | 19%/7m 51%/3m 67%/1m |
| 5a Jernvinne | 47%/3m 45%/4m 32%/6m | 38%/6m 31%/6m 39%/5m | 42%/4m 56%/2m 63%/2m | 42%/5m 29%/7m 35%/5m |
| A1 | 49%/3m 96%/0m 85%/0m | 84%/0m 96%/0m 87%/0m | 45%/4m 83%/0m 96%/0m | **98%/0m** 74%/1m 32%/5m |
| A2 C07 | 49%/3m 46%/4m 41%/4m | 63%/2m 39%/5m 43%/4m | 99%/0m 88%/0m 82%/0m | 36%/6m 18%/6m 34%/5m |

At A1, the SW view out to 50 m is 98 % open (CHM <3 m). That conflicts with the dense stems at 190–201° and 238–241° in
the image, unless the DOM predates the trees or the coordinate is off.

### 4.6 `adsb/`: the 21.09 21:29 gesture

**Data.** `trace_4791ac.json` is gzip JSON (59 KB → 347 KB): hex 4791ac, **LN-NIQ**, B738 «BOEING 737-800», callsign
**NOZ9EG**, readsb 3.16.15, day timestamp 1789948800 = 2026-09-21 00:00Z, 1643 points from 14:23:43Z to 19:49:36Z.
`trace_47a3b0.json` (178 KB → 1.06 MB) is hex 47a3b0, **LN-ENN**, B738, callsign **NOZ56U**, 5075 points from 05:04:20Z
to 20:43:44Z.

Point layout: `[t_offset_s, lat, lon, alt_baro_ft|"ground", gs_kt, track, flags, baro_rate, {detail}|null, source,
alt_geom_ft, geom_rate, ias, …]`. Sampling in 19:25–19:36Z is 119–129 points, with no gap above 16.4 s, so linear
interpolation is safe.

**Tracks around the event (my extraction; real time Z, add 2 h for CEST):**

- **NOZ9EG** comes from the north at FL360: 19:22Z at 62.34 N, 11.21 E. Descent starts at 19:24:20Z. The track turns
  from 194.7° to 182°, then runs along **≈10.90–10.93°E**:
  - 19:28:03Z: 61.4845 N, 10.9168 E, 28 750 ft geometric (at Evenstad latitude, about 9 km west of Evenstad).
  - 19:29:00Z: 61.3526, 10.9067, 26 550 ft.
  - 19:29:55Z: 61.2280, 10.8969, 24 350 ft.
  - It continues past Sjusjøen and Rudshøgda toward OSL, reaching 6250 ft by 19:39:49Z at 60.19 N.
- **NOZ56U** departs OSL (airborne 19:21:53Z), climbs north over Hamar and Løten, then east of Rena:
  - 19:29:21Z: 60.748, 11.224, 21 000 ft.
  - 19:32:26Z: 61.059, 11.287, 28 225 ft.
  - 19:35:46Z: 61.414, 11.360, 34 925 ft.
  - 19:36:33Z: 61.494, 11.377, 36 400 ft.
  - Northbound at 5.7°.

**`fly_2109.mjs` → `fly_2109_resultat.txt`** (re-run by me: identical). Elevation (°) from each site at the same
instant = stream 21:29:38 − delay:

| Site (moh) | NOZ9EG 15 s | 22 | 30 | 45 | 50 | max in stream 21:29:40–21:34:00 (22 s) | NOZ56U 15 | 22 | 30 | 45 | 50 | max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 Myklebysæterveien (594) | 29 | **33** | 37 | 46 | 48 | 32° @21:29:40 | 4 | 4 | 4 | 4 | 3 | 17° @21:34:00 |
| 2 Madsskardveien (598) | 20 | 22 | 24 | 28 | 30 | 21° | 4 | 4 | 4 | 3 | 3 | 16° |
| 3 S-Messelt S1 (898) | 21 | 24 | 27 | 35 | 38 | 23° | 4 | 3 | 3 | 3 | 3 | 12° |
| 3 S-Messelt S2 (877) | 22 | 24 | 27 | 36 | 40 | 23° | 4 | 3 | 3 | 3 | 3 | 12° |
| 4 Madsskardveien øst (646) | 19 | 20 | 22 | 26 | 27 | 20° | 4 | 4 | 4 | 3 | 3 | 16° |
| 5a Jernvinneveien (556) | 20 | 22 | 24 | 28 | 29 | 21° | 4 | 4 | 4 | 3 | 3 | 17° |
| A1 Birkebeinerveien (605) | 23 | 26 | 29 | 38 | 42 | 25° | 4 | 4 | 4 | 3 | 3 | 14° |
| A2 Gålaveien C07 (365) | 22 | 24 | 28 | 36 | 39 | 24° | 4 | 4 | 4 | 3 | 3 | 14° |
| Sjusjøen (850) | 22 | 21 | 20 | 18 | 18 | 24° @21:30:12 | 5 | 5 | 4 | 4 | 4 | 13° |
| Rudshøgda (300) | 10 | 9 | 9 | 9 | 8 | **59° @21:32:46** | 12 | 11 | 11 | 10 | 9 | 17° @21:31:36 |
| Løten (250) | 7 | 7 | 7 | 7 | 7 | 11° | 31 | **28** | 25 | 20 | 19 | **49° @21:30:32** |
| Elverum S (default.no #1) (250) | 5 | 5 | 5 | 5 | 5 | 7° | 16 | 16 | 16 | 15 | 15 | 16° @21:30:00 |

At 22 s, NOZ9EG is at 61.317 N, 10.904 E, 25 920 ft geometric. NOZ56U is at 60.739 N, 11.222 E, 20 655 ft.

**My supplementary computation** (same data and functions). This is each aircraft's maximum elevation over real time
21:20–21:40 CEST and when it occurred:

- NOZ9EG:
  - cand. 1: 50° at 21:28:38 real, az 275°, 6.5 km
  - cand. 2: 36° at 21:28:16
  - S-Messelt S1: 62° at 21:28:16, az 92°, 4.2 km
  - cand. 4: 33° at 21:28:12
  - 5a: 33° at 21:28:20
  - A1: 67° at 21:28:18, 3.4 km
  - A2 C07: 69° at 21:28:12, 3.2 km

  So NOZ9EG passed abeam of every Evenstad-area site **26–64 s before** the gesture started (21:29:16 real at 22 s delay)
  and was receding south when she pointed.
- NOZ56U peaks later: cand. 1 30° at 21:35:38 real; cand. 2 38° at 21:36:02; cand. 4 40° at 21:36:06; 5a 41° at
  21:35:56; S1 19°; A1 26°; A2 27°. It passes about 12–21 km east, **after** the gesture window.

**`tilt_2129.mjs` → `tilt_2129_resultat.txt`** (re-run by me: identical). This is Codex's projection model (#9). With a
level camera at heading C = 219.4°, a direction of elevation h and azimuth A appears in the image at an angle from
vertical of tilt = atan2(cos h · sin(A − C), sin h); negative means toward the left of the image. The **observed value
(per default.no) is 10–20° from vertical, leaning to camera-left.** ✓ marks |tilt| between 5 and 25° toward the left.

| Site | NOZ9EG 15 s | 22 s | 30 s | 45 s |
|---|---|---|---|---|
| 1 Myklebysæterveien | **✓ −13°** (h29, A212) | −4° (h33, A217) | +5° (h37, A223) | +21° (h46, A243) |
| 2 Madsskardveien | **✓ −8°** (h20, A216) | 0° (h22, A220) | +10° | +25° |
| 3 S-Messelt S1 | −63° (h21, A168) | −61° | −58° | −51° |
| 4 Madsskardveien øst | **✓ −6°** (h19, A217) | +3° | +12° | +27° |
| A1 Birkebeinerveien | −46° (h23, A194) | −41° | −34° | **✓ −20°** (h38, A203) |
| Koppang | −61° | −59° | −56° | −48° |
| Rena | +77° | +77° | +77° | +78° |
| Løten | +82° | +82° | +82° | +82° |
| Elverum S | +84° | +84° | +84° | +84° |
| Sjusjøen | −44° | −38° | −31° | **✓ −15°** (h18, A45) |
| Osen/Trysil-vest | +84° | +84° | +84° | +84° |
| Trysil | +83° | +83° | +83° | +83° |
| Engerdal | +58° | +60° | +62° | +65° |
| Finnskogen | +87° | +87° | +87° | +87° |

For NOZ56U the only ✓ is **Løten at 30 s (−11°, h25, A214)**. Others: Løten 15 s +4°, 22 s −3°, 45 s −25° (at the edge).
Trysil is +35/+30/+23/+8°. All Østerdalen candidates are at −84 to −86° (aircraft low in the south).

Reading (mine; the numbers are theirs):

- At default.no's measured 22 s delay, **no tested site produces the observed left lean for either aircraft**.
- ✓ results appear only at 15, 30 or 45 s, so the tilt test is delay-sensitive and does not discriminate robustly.
- Combined with the «stjerneskudd» ambiguity (README :62), this is consistent with the authors' joint position that the
  gesture does not select a region.

### 4.7 Upstream only (not in mirror): `solkart-2509/` (commit `e8178da`, 22:57 CEST 25.09, issue #10)

**`solkart.mjs`.** Its question: «hvor var det klart mens stedet hadde direkte sol 25.09 kl. 14:33–15:22Z (egne
livebilder, solstjerne)?»

- Input: EUMETSAT MTG FCI `mtg_fd:vis06_hrfi` via WMS, for time steps 14:30, 14:40, 14:50, 15:00 and 15:10Z. «FCI
  skanner Norge ca. 8 min inn i hvert steg.»
- Clear-sky baseline per pixel = the minimum value at the same time step on 21–24.09. The excess on 25.09 is computed
  against it.
- Colouring: green = excess ≤15 in at least 4 of 5 steps (compatible); red = ≥30 in at least 4 of 5 (conflict); yellow
  = otherwise.
- Box 58.8–63.6 N, 6.0–13.2 E, 900×1245 px (≈430 m/px).
- No result text was committed. I could not re-run it, because EUMETSAT is blocked.

**`solkart_2509.png`** (viewed): «25.09 14.30–15.10Z grønn = klart (forenlig) rød = sky (konflikt) gul = uavklart».

- Large red (cloud) areas cover the west and centre (Gol, Fagernes, Otta, Lillehammer, a band through
  Lillehammer–Gjøvik–Oslo-west and toward Tynset).
- Green (clear) areas: NE around Røros and north of Engerdal; the SE corner (south of Kongsvinger / east of Oslo toward
  the Swedish border); small patches west of Otta and near Oppdal.
- Mostly yellow: Rena, Elverum, Hamar and Oslo.

My pixel sampling in 9×9 px (≈3.9 km) windows found **no green** at any report candidate. Counts are Y (yellow) / R (red)
per window:

| Location | Y | R |
|---|---|---|
| cand. 1 | 66 | 11 |
| cand. 2 | 31 | 38 |
| S-Messelt | 36 | 45 |
| cand. 4 | 49 | 28 |
| 5a | 55 | 17 |
| A1 | 64 | 17 |
| A2 | 70 | 11 |
| P7 | 67 | 14 |
| default.no top cell | 30 | 45 |
| Evenstad | 12 | 20 |

Engerdal had some green (17 G / 15 Y) and Røros 8 G / 24 Y. Town samples are partly contaminated by label boxes.

**`ct_1450.png`** (viewed): MTG true colour (left) and cloud type (right) at 14:50Z. Norway is mostly cloud-covered. Dark
cloud-free lanes run roughly N–S from south-east of Tynset past Engerdal and just east of Koppang–Evenstad to
Rena–Elverum, then from Hamar toward Oslo, with a clear area SE of Oslo.

**Main README `b067a04` (23:23 CEST).** «**Ny avklaring 25.09: Direkte sol rundt kl. 17.00 CEST er dokumentert av både
Codex og Claude.** Antakelsen om en helt overskyet ettermiddag er trukket tilbake. Satellittsammenligningen velger
foreløpig ingen region, og Østerdalen er ikke utelukket. Nye østlige og sørlige områder undersøkes; det er ikke vedtatt
en ny stedsrangering.» It links issue #10 comment 5839791607 and the ZIP `Hordejakten_landsok_solsikt_25sep.zip`, which
was not downloaded.

Caveats, all mine:

- There is a parallax offset between the satellite view and the ground for high clouds.
- «≥4 of 5 steps» covers the whole 40-minute window, while direct sun may have lasted only part of it.
- A sun visible through a local cloud gap will not appear at 430 m pixel resolution.

---

## 5. Synthesis: the camera-geometry model as used across the report and bevis scripts

| Parameter | Value | Source |
|---|---|---|
| Camera location | ≈5 m from the box toward ≈41° (NE); scripts use 39° | board «KAMERA 41 ØST» [full report p.10]; `terrain.mjs:17` etc. |
| Heading | 219.6° (sun-path fit at 59.5°N) / 219.2° (at 61.5°N); bevis uses 219.4°; short report text «ca. 220°», table «ca. 221°» | full report p.4, p.10; bevis README :14; short report p.3 |
| Pitch | +0.2° or −0.9° (the two calibrations) | `fig_bildemaling.png` caption |
| Focal length | 1068 px @1280 = 1602 px @1920 | report; bevis README :14 |
| FOV | ≈62° horizontal, az 188.7–250.5° | full report p.10 |
| Camera height | model 0.3–3 m; solutions 1.1–1.9 m; synthetic views 1.56–1.87 m; scripts 1.5 m | short report p.4; `syntetisk_utsyn`; scripts |
| Ground at box front | 4.3–5.9 m (M0, −15.3 to −13.7°) | short report p.4 |
| Box width | 2.0 ± 0.2 m | full report p.10 |
| Birch foot (B4, 238°) | 12–45 m (from trunk width) | short report p.4 |
| Clearing edge (B3, 219°) | 8–250 m (17–44 m withdrawn) | short report p.5 |
| Stability | 10:15 and 15:01 frames within 1 px (114/127 SIFT); night = day ×2.45 | short report p.4; full report p.11 |
| Direct-sun events in frame | 21.09: crowns/stems top right (238–250°, +8.5 to +18.6°) **from 07:47** (step 07:44→07:50), still lit at 08:00, dark by 08:30; possible faint stem spots 07:40–07:44 [vurdering]; ground (4.6–7.5 m) **not lit through 08:00**; default.no «first sun spot 07:51», strongest 08:25–09:55; 10:15–10:45 diffuse; last evening sun spot **17:23** (sun 246°/12.9°). 25.09: direct sun / sun star about 16:33–17:22 CEST (az 234.6–246.1°, el 16.5–11.4°, inside the FOV) | bevis `sol/maling.csv`, README :19-24; short report p.5-6; upstream README / solkart |
| Pointing gesture | stream 21:29:38–53 on 21.09; arm 10–20° from vertical, leaning image-left (default.no measurement) | `tilt_2129.mjs:3`; bevis README :48, :62 |

---

## 6. Solid versus withdrawn: the authors' own ledger

**Considered solid ([verifisert], reproduced, or stated as an agreed clarification):**

- The sun-step photometry on default.no clips: crown/sky 0.32 → 0.66 between 07:44 and 07:50, ground flat, local
  rather than an exposure change. Also: direct sun on the right-hand stem and branches from 07:47, and no ground sun
  before 08:00 (bevis README :19-23).
- The flight elevation table at fixed delays. Codex re-ran it (PRESISERINGER.md:9: «bekrefter beregningen under dens
  premisser, ikke at gesten gjaldt dette flyet»).
- The terrain horizons 8.4 / 7.3 / 6.6° at 5a / 5b / 5c from 1.5 m. Codex reproduced these with obstacles at 800, 1050
  and 1300 m (PRESISERINGER.md:10). Whether they exclude a site depends on which surface was lit (#2).
- The shooting-star ambiguity of the gesture (verified in default.no osint_notes).
- The camera does not move, so there is no parallax baseline. The Codex package adds that hint-video frames are zoom or
  crop only, «ikke gir en påvist stereobaseline for treavstander» (README :25).
- Direct sun around 17:00 CEST on 25.09, documented by both (upstream README).

**Withdrawn or corrected:**

- B3 «stubbe» distance 17–44 m. It was «trolig motlyst løv», and the rejected sites were reinstated (short report p.4,
  p.8; figures README :40).
- «47° mot Messelts maks på 63°» from #1: «feil sammenligningsgrunnlag» (bevis README :60).
- «En arm nesten loddrett i bildet er ikke en måling av flyets høydevinkel. Claude har trukket tilbake den slutningen»;
  the gesture alone «ikke alene velger eller utelukker region» (README :14, #9).
- Weather exclusions of the west and south were model-based and unverified; «brukes ikke som harde grenser» (README :14).
- Temperature is not a hard filter; no correction is documented (README :15; PRESISERINGER.md:8).
- The historical ranking is not a current ranking. «Regionen må holdes åpen», and the new flight table «bekrefter ikke
  Evenstad som region» (README :13; PRESISERINGER.md:7).
- Candidate 1's road bearing is ≈94°, which is no unconditional match to the ≈130° hint (README :18; PRESISERINGER.md:12).
- The exact A1 point has weak forest support; 0/25 positions pass at Codex (README :19).
- Bever corrected to **grevling** (badger) in the app item (PRESISERINGER.md:30).
- Report-internal fixes: 25 cm → 1 cm steps; robustness max → union; tractor roads not treated as drivable; «alle»
  Gålaveien positions failing sun corrected to «none with access pass».
- «Antakelsen om en helt overskyet ettermiddag er trukket tilbake» (25.09, upstream README).
- Canopy/transmission tests are declared non-discriminating (bevis README :40).
- Repeated coordinates are not independent confirmations: 61°26′55,3″N 10°58′39,0″E = 61.44869, 10.97750 = default.no's
  site-finder top at A1 (README :17).

**Still open (their own list):** the morning-sun geometry (#2: ground versus stem versus crown); the temperature
measurement point; DOM vintage; the region; field verification; original-video control of 07:45–08:00; whether the
olive-oil / olivine idea (Åheim/Almklovdalen, README :23) means anything.

---

## 7. Contradictions and discrepancies I found

1. **Board 21.09 18:44.** The report has «KUPERT TERRENG · MYE LYNG · …», while the bevis re-reading has «STARTET 07 00 /
   UJEVNT TERRENG, MYE LYNG / HØRER IKKE MYE FRA BOKSEN». «KUPERT TERRENG» does appear in a 22.09 board («GIKK IKKE PÅ
   STI, MEN KUPERT TERRENG»).
2. **Board 21.09 19:38.** The report has «4 STORE STEINER, KUN STEIN DER»; the bevis reading has «4 STORE STEINER **TIL
   VENSTRE**, KUN STEIN DER».
3. **First direct sun.** The report says 07:51 (default.no); bevis says ≤07:47 on crowns and stems, with the step starting
   after 07:44.
4. **Jernvinneveien.** The short report marks morning sun ✓ and lists 31 positions passing (horizon ≤6.5°). The published
   5a/5b/5c points have horizons of 8.4/7.3/6.6°. grense_2/2b show 5a/5b need 32–39 m surfaces, and canopy3 has terrain
   blocking 100 % at 07:50. The report's grid positions may differ from the three map markers.
5. **Candidate 1 «består alle modelltestene».** At the published coordinate: K0 median 10.4 m (DOM 604.19 − DTM 593.79)
   and 0/25 neighbourhood positions pass. Road bearing is 93.7°, not ≈130°. The «flest treff» claim conflicts with the
   table (E6 has 5 against E2's 21; PRESISERINGER.md:36).
6. **Madsskardveien (2).** «Bare to posisjoner» against 3 in the table (PRESISERINGER.md:37). The road bearing of 125.3°
   does match ≈130°.
7. **B3 elevation.** The figure label is −3.7…−2.0°; the full-report table is −3.4…−1.8°.
8. **Camera heading wording.** 219.2–219.6° (fit), 219.4° (bevis), «ca. 220°» (short report method), «ca. 221°» (short
   report hint table). The camera offset is 41° on the board and 39° in the scripts. Both are minor.
9. **Sun azimuth in the grense scripts.** They use 97.9° for 07:50; NOAA gives 98.7° (97.9–98.1° is 07:47). This is my
   finding and its impact is unquantified.
10. **Region.** The report's conclusion was «Østerdalen rundt Evenstad». The current README says the region must be kept
    open; the 25.09 satellite map shows the Evenstad candidates as not clear-compatible; and Østerdalen is «ikke
    utelukket».
11. **A2.** The short report says A2 is «utelukket/svekket» by morning sun. The v6 terrain limit is 0.0 m at every A2
    camera, so the sun reaches the ground there. The short-report table itself shows 12 A2 positions pass sun; they fail
    only in combination with access (PRESISERINGER.md:23).
12. **25.09 weather.** The report quotes «Overskyet» for 08:46 (reported second-hand). Direct sun is now documented
    around 17:00 CEST the same day. This is not strictly a contradiction (morning versus afternoon), but a
    whole-day-overcast assumption was withdrawn.

---

## 8. Candidate coordinate register (everything numeric found in these sources)

| Name | lat | lon | Source | Status |
|---|---|---|---|---|
| 1 Myklebysæterveien vest | 61.39950 | 11.03156 | kart_1_E6; short report p.1 | historic #1; K0 fails at the published point; horizon 0.5°; road bearing 94° |
| 1b | 61.39770 | 11.03178 | kart_1_E6 | southern extreme of the 5 passing positions |
| road point 1 | 61.39921 | 11.04086 | kart_1_E6 | not a confirmed parking spot |
| 2 Madsskardveien traktorvei | 61.44432 | 11.12340 | kart_2_E3 | historic #2; 1/25 K-pass; horizon 1.8° |
| road point 2 | 61.44206 | 11.13007 | kart_2_E3 | |
| 3 S-Messelt S1 (= C23) | 61.45713 | 10.83615 | feltsone map; v6 | historic #3; 898 moh; horizon −0.4°; 2/25 K-pass; cold per MET |
| 3 S-Messelt S2 (≈ G18) | 61.45448 | 10.84063 | feltsone map | 876 moh; 0/25 K-pass |
| N1 N-Messelt | 61.45998 | 10.84925 | feltsone map (partly obscured label) | weaker, over open bog |
| N2 N-Messelt | 61.45986 | 10.85133 | feltsone map | weaker |
| Messelt road end (OSM 632102560) | 61.45425 | 10.84350 | feltsone map | |
| 4a Madsskardveien øst | 61.45182 | 11.14283 | kart_4_E1 | historic #4; centre passes K0–K4; horizon 3.8° |
| 4b | 61.45179 | 11.13851 | kart_4_E1 | |
| road point 4 | 61.44828 | 11.14333 | kart_4_E1 | |
| 5a Jernvinneveien | 61.43511 | 11.14349 | kart_5_E2 | horizon 8.4°; sun limit 38–39 m, so inconsistent with 07:47–07:50 sun |
| 5b | 61.43444 | 11.13907 | kart_5_E2 | horizon 7.3°; limit 32.4 m, inconsistent |
| 5c | 61.43531 | 11.13483 | kart_5_E2 | horizon 6.6°; limit 17.3–18.5 m, borderline |
| road point 5 | 61.43345 | 11.14330 | kart_5_E2 | |
| A1 Birkebeinerveien (default.no site-finder top) | 61.4487 | 10.9775 | short report; README (61°26′55,3″N 10°58′39,0″E) | horizon 11.1°; limit 32.3 m; view nearly treeless in DOM; 0/25 K-pass |
| A2 Gålaveien C07 | 61.46254 | 10.97512 | v6; short report 61.4625, 10.9751 | best K-match (4/25); terrain lets sun through; access over Nørdre Eldåa ravine undocumented |
| C06 (A2) | 61.46236 | 10.97495 | v6 | synthetic view shows almost all near canopy |
| P7 / G15 | 61.37447 | 10.97722 | v6 | cold per MET; terrain OK |
| H2 | ≈61.355 | ≈10.990 | digitised from oversikt_temp | 0 forest hits (model) |
| v6 G01–G24 | see §4.5.8 | | punkter_v6.csv | |
| default.no best cell | 61.45 | 11.10 | short report p.7 | model output |
| default.no stop 1 | 61.4520 | 11.1460 | full report p.9; flykart | ≈ candidate 4 |
| default.no 40 stops | see §3.11 | | flykart_83ruter (digitised) | historic |
| Old search points 1–7 | see §3.11 | | flykart_83ruter | historic, superseded |
| Myklebysætra (ca.) | ≈61.364 | ≈10.994 | flykart | landmark |

---

## 9. Open questions

- The exact pixel position of the 25.09 «solstjerne». With the camera model, the sun's image position gives az/el
  through a canopy gap, and so a hard horizon/canopy constraint at 16:33–17:22 CEST. Has anyone measured it?
- The 21.09 21:29 gesture: an aircraft or the shooting star? What is the true stream delay for that specific event?
- Would grense_2/2b change materially with the correct 07:50 azimuth (98.7° instead of 97.9°)?
- DOM acquisition year at each candidate, and felling since.
- Temperatures: outside air or box air?
- «KOM FRA DEN VEIEN ←»: drawn from the camera's viewpoint (meaning SE) or from Anja's (meaning NW)?
- «2,7 eiffeltårn»: altitude or lock code?
- The olive-oil / badger app item.
- The contents of issues #1–#10 and the Codex ZIPs, which are not accessible here.
- Whether the original 07:40–08:00 stream (not default.no clips) confirms the 07:47 onset.
