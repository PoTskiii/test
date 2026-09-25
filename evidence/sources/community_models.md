# Community models: how the MagnusPladsen map computes its probability layers

Hordejakten 2026 · compiled 2026-09-25 (evening, CEST) · task `community-models`

Source mirror: `/home/user/test/data/raw/magnus` (MagnusPladsen/hordejakten-2026). Repo head is `68faa86` (2026-09-25 21:04:38 +0200), 150 commits, first commit `e1b59cf` (2026-09-23 14:15). All file:line references below are relative to that mirror unless stated otherwise.

Reproduction code: `/home/user/test/evidence/sources/community_models_port/`. It contains a faithful Python port (`magnus_model.py`, `run_model.py`, `teorier_port.py`), probes and sensitivity runs (`probe.py`, `sens.py`, `overlay.py`) with saved outputs (`*.out`, `magnus_model_results.json`), and `validate_original.ts`. That last file bundles the **original TypeScript** with esbuild. Its output matched the Python port exactly: same top areas, same relative scores, same theory percentages.

Evidence classes used below: **(a) primary** (whiteboard, stream, organizer, app), **(b) community observation**, **(c) interpretation/theory**, **(d) model output**. Nearly everything in this report is (c) or (d). Primary quotes are given verbatim in Norwegian where the model depends on them.

---

## 0. Summary of findings

1. **The map has two separate, unconnected models.**
   - **(A)** The grid "Sannsynlighetskart" (`src/lib/modell.ts`). It works on 1,873 OSRM grid points of 0.1° lat × 0.2° lon (≈11 × 11 km). Each point gets a product of 12 weighted factors, `Π(1 − w + w·f)`, which is then normalised to the best cell.
   - **(B)** The "Teorier" percentages (`src/data/teorier.ts`). There are 11 hand-defined circles. Each one gets a prior times 33 hand-set likelihood multipliers ("BEVIS"), and the results are normalised to 100 %.
   - The two models share only some polygons (Windy clouds, fog, sun on 23.09). Otherwise they are independent.
2. **Many of the most informative clues the site collected never enter either model.** They are drawn only as visual layers:
   - the Horde-AI altitude «2,7 eiffeltårn» (810/891 moh);
   - the tree mix «35% BJØRK · 25% GRAN · 40% FURU»;
   - «VINDSTILLE»;
   - the 25.09 17:22 SAS50J pointing;
   - «INGEN SKYTING», logging («HOGD»), and road direction («KOM FRA DEN VEIEN ←»);
   - no water, no cabin.
3. **The grid's "fly" factor does not use the two planes the UI describes.**
   - The UI names NOZ56U and NOZ9EG, but the code uses every aircraft in `fly_2130.json` (49 tracks, 38 of them above 3,000 ft in the window). That gives 465 positions for 21:28:15–21:30:15 real time, every 10 s.
   - The result is that ~9 % of all grid cells score ≥ 0.5 on "fly". Near Gardermoen, Holtålen, Østfold and elsewhere cells score 1.0. With only the two named planes, 0.9 % of cells would score ≥ 0.5.
4. **The default map (preset «Bekreftet: vær, sol og fly», `fakta`) has one best cell, (60.9, 11.4) east of Løten.** That result is fragile:
   - The cell wins only because it sits just inside the hand-drawn «Sol 23.09» polygon, which was "grovt tegnet ut fra en beskrivelse". The polygon halves the score of every cell outside it.
   - With that polygon switched off, 25 cells tie at ≥ 90 %. They include cells beside Oslo/Gardermoen and in Østfold and Holtålen.
5. **The hand-drawn Windy "blue" band acts as a hard veto (weight 1, factor 0) in all presets except `norheimsund`.** The band runs from Lillehammer over northern Ringsakfjellet, Evenstad and Koppang towards Sweden. The test is done at the cell centre only. It zeroes:
   - default.no's #1 fusion area (61.45, 11.1, Rena–Evenstad);
   - Gålaveien and Madsskardveien;
   - Birkebeinervegen;
   - 337 of the 634 cells (53 %) of the community «800–900 moh + fly + skog» map (`fellesskap891.json`), which the same site publishes.
6. **Theory percentages at app load** (mode «Alt vi har», 28 of 33 BEVIS active) are Løten 36.4 %, Rena 22.1 %, Rudshøgda 21.1 %, Ringsaker 11.9 %, Solør 3.5 %, Gjøvik 2.4 %, «Annet» 1.6 %, Røros 0.9 %. Valdres, Agder and Hardanger are each below 0.1 %.
   - The single ×3 "fly" multiplier for Løten decides the ranking. Without it Rena leads, at 29.0 %.
   - Rudshøgda's 21 % comes largely from a stack of correlated Prøysen clues (×2.2 × 1.2 × 1.5 × 1.2 ≈ ×4.75). It also benefits from a 10-km circle getting the same prior as the 50-km circles.
7. **Stale or retracted inputs are still active by default.**
   - «Vervebokstavene = NORHEIMSUND?» gives Hardanger ×2, although the site itself marks the letters as solved = HORDE MINUS (status `lost`).
   - «Kode 5008 = Horde AS i Bergen» gives ×1.3.
   - The `DEFAULTNO` candidate list dates from 22.09 16:42. Three inconsistent descriptions of "default.no's top candidate" exist in the code.
   - The UI still says the stream is «bekreftet 45 sek forsinket» (confirmed 45 s delayed), which was retracted on 25.09. The model uses a 23-s offset.
8. **Retractions in git history:**
   - The "no mushrooms" exclusion was removed as incorrect (23.09).
   - The 45-s delay was downgraded to a guess (25.09).
   - Unverified app screenshots were demoted: FROLAND→«Ekornet kan klatre» and LD6788→«ENKODE» (24.09).
   - **Everything about Birkebeinervegen/Birkebeinerveien was removed on 25.09 14:12 without a stated reason.** That includes 9 default.no "site finder" sites with scores up to 0.995 at 61.4487, 10.9775, and 4 search stops.

---

## 1. Files read and how the site is wired

| File | Role |
|---|---|
| `src/lib/modell.ts` (213 lines) | Grid model: factors, weights (`Vekter`), presets (`FORHAND`), scoring (`poeng`), normalisation (`beregn`), colour classes (`klasse`), top areas (`toppOmrader`). |
| `src/data/teorier.ts` (456 lines) | Theory circles (`TEORIER_LISTE`), evidence multipliers (`BEVIS`), `standardBevis`, `sannsynligheter`. |
| `src/data/innhold.ts` | Constants used by both models: `OSLO`, `BERGEN`, `SOL_I_DAG`, `TAAKE`, `SKYDEKKE`, `DEFAULTNO`, `SKYANALYSE`, `TEORIER` (Norheimsund pos), `FLY_PUNKT`, `FLY_PUNKT2`, `STREAM.forsinkelseSek`. |
| `src/lib/fly.ts` | ADS-B interpolation, `PEKETID_EKTE = '21:29:15'`, `VINDU_SEK = 60`, altitude cut 3000 ft. |
| `src/lib/geo.ts` | Haversine distance (R = 6371 km), bearing, destination, cross-track (`tversAvstand`), point-in-polygon, sector. |
| `src/data/lag.ts` | Layer catalogue and legend text (905 lines). The merkelapp tags are `fakta`, `beregnet`, `tolkning` and `teori`. |
| `src/data/kartmarkorer.ts` | Groups hint and "folk tror" markers by position rounded to 0.01° (~1 km). |
| `src/lib/{hoyde,treslag,vind,storvilt,verneomrader,stedsnavn,defaultno}.ts` | Visual layer loaders and popups. None of them feeds the scores. |
| `scripts/build_drivetime.py` | Builds `public/data/drivetime.json` (OSRM table API) and `norge.json`. |
| `api/kodejakten.ts`, `api/tiktok.ts` | Vercel edge proxies (status of Horde's code game; Horde TikTok-live status). They are not model inputs. |
| `src/App.tsx` L45–156 | Loads the data and builds the `Kontekst`. Default weights = `FORHAND[0]` (`fakta`), theory mode = `'alt'`. |
| `src/components/Kart.tsx` | Draws the model cells, the click popup and the field sector. |
| `src/components/LagPanel.tsx` | Weight sliders from 0 to 100 % in steps of 5. Drive-time sliders: hours 1–11 (step 0.5) and ± 0.5–3 h (step 0.25). |
| `src/components/TeoriPanel.tsx`, `AnalysePanel.tsx` | UI for theory % and for default.no / vercel analysis text. |

**Data flow** (`src/App.tsx` L88–155):
- `drivetime.json` becomes `punkter`.
- `fly_2130.json` goes through `posisjonerRundtPeking` to give `flyPos`.
- `innlandet.json` gives `innlandet`. Only the outer ring `poly[0]` of each polygon is used (L148), so holes are ignored.
- `utelukket.json` gives a set of keys built with `utelukkNokkel`.
- `beregn(punkter, vekter, kontekst)` is recomputed on every weight change.
- `sannsynligheter(aktiveBevis)` is computed separately.

---

## 2. Model A: the grid «Sannsynlighetskart» (`src/lib/modell.ts`)

### 2.1 Grid (`scripts/build_drivetime.py`, `public/data/drivetime.json`)

- **Origin:** `OSLO = (lon 10.7522, lat 59.9139)`, i.e. Oslo sentrum (`build_drivetime.py` L14; `innhold.ts` L13).
- **Build box:** lat 57.9–66.0 in steps of 0.1°, lon 4.6–15.2 in steps of 0.2° (L15–16).
- **Kept points:** only those inside the union of county polygons. The Norway polygon comes from a user-supplied fylker GeoJSON (README suggests `robhop/fylker-og-kommuner`).
- **Result:** 1,873 points, spanning lat 58.1–66.0 and lon 4.8–14.6.
  - Nothing north of 66.0° N is in the grid. Northern Nordland, Troms and Finnmark can never score.
- **Drive times:** OSRM demo server `router.project-osrm.org/table/v1/driving`, called in chunks of 99, from Oslo to each point.
- **Fields:** `[lat, lon, sek, meter, snap_m]`. `snap_m` is the distance from the grid point to where OSRM snapped it onto the road network.
  - Snap statistics: median 713 m, 75th percentile 2,180 m, maximum 22,558 m.
  - 632 points have snap > 1.5 km. 363 have snap > 3 km.
  - No point has null `sek`.
- **Layer text:** «OSRM regner ofte litt tregere enn Google, så se på tallene som ±30 min» (`lag.ts` L190). Source: «OSRM … beregnet 23.09» (L200).
- **Cell size and pixel test:** each cell is about 11 × 11 km (`lag.ts` L127). Each factor is evaluated **only at the cell centre** (the grid point). The click popup snaps to the nearest grid point within 12 km (`Kart.tsx` L336).

### 2.2 Scoring formula

- Per cell (`modell.ts` L164–171): `poeng = Π over 12 factors of (1 − w_i + w_i · f_i)`, where `f_i ∈ [0,1]` and the slider weight is `w_i ∈ [0,1]`.
- The header comment at L1–2 reads: «hver rute får en poengsum = produktet av faktorene. En faktor med vekt w bidrar med (1 - w + w * f), så w = 0 betyr «ignorer hintet».»
- `relativ = poeng / max(poeng)` (L179–188). All colours are relative to the single best cell.
- **Colour classes** (`klasse`, L194–200, `Kart.tsx` L453). Opacities are 0.75 / 0.62 / 0.52 / 0.45.

| relativ | class | legend (`lag.ts` L128–133) |
|---|---|---|
| ≥ 0.90 | 0 | «Passer svært godt» |
| ≥ 0.60 | 1 | «Passer godt» |
| ≥ 0.35 | 2 | «Passer middels» |
| ≥ 0.15 | 3 | «Passer litt» |
| < 0.15 | hidden | — |

- **«Beste områder»** (`toppOmrader`, L203–213): the top 6 cells by score. Each must be ≥ 40 km from the others already chosen. The loop stops when `relativ < 0.01`.
- A factor at weight 1 with `f = 0` gives a hard zero. The slider help text makes this explicit: «100 % betyr at steder som ikke passer, blir helt utelukket» (`LagPanel.tsx` L180).
- This is a naive-Bayes-like product. The weights are not likelihood ratios. They are linear mixing coefficients between "ignore" (1) and "trust fully" (f).

### 2.3 The 12 factors: formulas, thresholds, data, and what constraint they encode

`gauss(x, σ) = exp(−½ (x/σ)²)` (L109). All distances are great-circle distances (`geo.ts`, R = 6371 km).

| id (UI name) | Formula (file:line) | Data | Encodes (claimed source) | Evidence class |
|---|---|---|---|---|
| `vei` («Nær bilvei») | 1 if snap ≤ 1500 m, else `exp(−(snap−1500)/2000)` (L123) | `snap_m` from OSRM | «CA 5–10 MIN Å GÅ FRA BIL» (whiteboard 21.09 18:31) | a (quote) → d (the 1.5 km/2 km constants are arbitrary) |
| `skyfri` («Utelukk skyer og tåke») | 0 if the cell centre is inside any `SKYDEKKE` or `TAAKE` ring, else 1 (L124) | `SKYDEKKE` (`innhold.ts` L1188–1191), `TAAKE` (L1154–1156) | «INGEN SKYER NÅ» 19:00, «KLAR HIMMEL» 19:50 on 21.09. Windy screenshot blue areas «tegnet for hånd … (feil under ca. 10 km)». Fog report from one Nord-Odal local on 23.09 | c (hand-drawn Windy + one chat user) |
| `solidag` («Sol 23.09 (satellitt)») | 1 inside `SOL_I_DAG`, else 0 (L135) | `SOL_I_DAG` 3 rings (`innhold.ts` L1147–1151) | «Formiddagen 23.09 var det skyer over store deler av Norge på satellitt, mens Anja hadde sol» (hint `solidag`, status `tolkning`, L48–57). Polygons «Grovt tegnet ut fra en beskrivelse, ikke fra selve bildet» | c |
| `fly` («Fly rett over kl. 21:29») | `gauss(min distance to any flyPos, 10 km)`; `1` if flyPos is empty (L132–134) | `fly_2130.json`: 49 aircraft, 5 fixes each at 21:28:14 / 21:29:48 / 21:31:16 / 21:32:50 / 21:34:17 real time, «ekte tid 21.09, CEST», «ADS-B fra adsb.lol, hentet ut av default.no (event_planes.json)». `posisjonerRundtPeking` (`fly.ts` L35–46): every plane, linear interpolation, t = 21:29:15 ± 60 s every 10 s, keep if > 3000 ft | Anja «pekte rett opp kl. 21:29:38 og skrev «FLY» kl. 21:30 (streamtid)» (hint `fly`, status `tolkning`, `innhold.ts` L743–752). Comment L131: «Pekte rett opp: flyet var trolig innen noen få km horisontalt. 10 km gir rom for tidsusikkerhet.» | b/c (gesture ↔ ADS-B match) + d |
| `innlandet` | 1 inside the Innlandet polygon (outer ring only), else 0; 1 if the polygon did not load (L136) | `public/data/innlandet.json` (simplified, 1 polygon, 1 ring) | «Fellesskapet er sikre på Innlandet» (FAKTORER L35; hint `innlandet` status `tolkning`, «Det er null tvil, været, sola, skogen og alt.») | c (community consensus) |
| `utelukket` («Fellesskapets utelukkingskart») | Checks 5 keys: the centre and ±0.05° lat, ±0.1° lon; `f = 1 − (#excluded)/5` (L137–143). Key = `round(lat/0.05)·0.05` to 2 decimals, `round(lon/0.1)·0.1` to 1 decimal (L119) | `utelukket.json`: 5,166 cells of 0.05° × 0.1°, 4,843 `R` (red, excluded) and 323 `C` (light blue, «fjellbjørk»). Kilde: «Fellesskapets utelukkingskart 23.09 … Stedfestet fra bilde, ca. ±10 km. Vest for bildet (vest for 8,4° Ø) er fylt inn som utelukket.» | community map shared in chat 23.09 | c |
| `defaultno` («default.no-kandidater») | `max over 5 candidates of gauss(d, 25 km)` (L130) | `DEFAULTNO` (`innhold.ts` L1159–1165), «Toppkandidater fra default.no sin fusjonsmodell (22.09 kl. 16:42; klare celler i kveld 23.09)»: #1 (60.9, 11.2) «Hamar øst mot Løten (skog)»; #2 (61.3, 11.2) «Rena og Åsta»; #3 (61.5, 11.0) «Koppang»; #4 (60.6, 12.35) «Finnskogen (Solør)»; #5 (61.3, 12.3) «Trysil» | default.no fusion output | d (stale) |
| `bokstaver` («Bokstavene: Norheimsund») | `gauss(d to Norheimsund (60.3707, 6.1453), 20 km)` (L125–126) | `TEORIER` entry `norheimsund` | referral letters N O R H E I M S U D | c (**obsolete**: the same site marks the letters solved as HORDE MINUS) |
| `bergen` («118°-linja fra Bergen») | Cross-track distance from Horde AS (60.3896, 5.3297) along 118°. If along-track > 0: `gauss(xt, max(8 km, along·tan 5°))`, else 0 (L127–128) | `BERGEN` (`innhold.ts` L15) | «ØST CA 118 · RETNING SKILT»; 5008 = Horde's postcode | c |
| `retning` («298°-linja fra Oslo») | As above but from `OSLO` along 298°. With `retningBegge`, also 118°. σ = max(8 km, along·tan 5°) (L154–160) | `OSLO` | «Teori: 118° er retningen mot Oslo» | c |
| `skyanalyse` («Skyanalyse (Agder)») | `gauss(d to (58.7, 8.27), 35 km)` (L129) | `SKYANALYSE` (`innhold.ts` L1181, «lest av bildet, ±15 km», inner 12 km, outer 45 km) | community cloud/plane-timing map (hint `skyanalyse`, status `usikker`) | c |
| `kjoretid` («Kjøretid fra Oslo») | `gauss(sek/3600 − timer, slingring)`; 0 if unknown (L153) | `sek` from OSRM | Anja «tror selv det var ca. 7 timer» but «aner ikke hvor lenge de kjørte» (hint `reise`) | a (her statement) + c |

**Factor coverage over the 1,873 cells** (Python port, `run_model.out`):
- `vei` ≥ 0.5 in 80 % of cells.
- `skyfri` = 0 in 42.6 %.
- `solidag` = 1 in only 8.4 %.
- `innlandet` = 1 in 23.1 %.
- `utelukket` = 1 in 33.2 % and = 0 in 58.6 %.
- `fly` ≥ 0.5 in 9.1 % of cells with all planes, and 0.9 % with only NOZ56U and NOZ9EG.
- `defaultno` ≥ 0.5 in 4.8 %.

### 2.4 Presets («FORHAND», `modell.ts` L45–107)

The default on load is `FORHAND[0]` = `fakta` (`App.tsx` L54). Weights in %. "timer/σ" apply only when `kjoretid` > 0.

| preset id / name | vei | skyfri | solidag | fly | innlandet | utelukket | defaultno | kjoretid (timer, σ) | retning | bokstaver | bergen | skyanalyse | turns on layers |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `fakta` «Bekreftet: vær, sol og fly» (default) | 80 | 100 | 50 | 70 | 0 | 0 | 0 | 0 (7, 2) | 0 | 0 | 0 | 0 | — |
| `alt` «Alt vi har» | 80 | 100 | 40 | 60 | 50 | 80 | 30 | 0 (7, 2) | 0 | 0 | 0 | 0 | — |
| `innlandet` | 80 | 100 | 70 | 50 | 100 | 0 | 30 | 0 (5, 2.5) | 0 | 0 | 0 | 0 | innlandet |
| `norheimsund` | 80 | **0** | 0 | 0 | 0 | 0 | 0 | 0 (7, 1.5) | 0 | 100 | 0 | 0 | teorier |
| `retning` «Retningsteorien» | 80 | 100 | 0 | 0 | 0 | 0 | 0 | 30 (7, 1.5) | 90 | 0 | 0 | 0 | retning |
| `fly` «Flyet kl. 21:29» | 80 | 100 | 70 | 100 | 0 | 0 | 0 | 0 (5, 2) | 0 | 0 | 0 | 0 | fly |
| `kort` «Kortere tur (3–5 t)» | 80 | 100 | 0 | 0 | 0 | 0 | 40 | 100 (4, 1) | 0 | 0 | 0 | 0 | — |
| `agder` «Agder-teorien» | 80 | 100 | 0 | 0 | 0 | 0 | 0 | 0 (4, 1.5) | 0 | 0 | 0 | 90 | skyanalyse |
| `defaultno` «Som default.no» | 80 | 100 | 0 | 0 | 0 | 0 | 100 | 0 (3.5, 2) | 0 | 0 | 0 | 0 | defaultno |

The `fakta` description reads: «Standard. Bare det som er bekreftet av Anja og målinger: nær bilvei, klar himmel (Windy og tåka), sol 23.09 (satellitt) og flyet hun pekte på kl. 21:29 (ADS-B). Ikke default.no, fellesskapets kart, Innlandet eller kjøretid.» (L49).
- Note: three of its four inputs (`skyfri`, `solidag`, `fly`) come from hints the site itself labels `tolkning` (interpretation).
- Git: `63416f0` (25.09 11:07) introduced this preset as the default. The previous «Bare bekreftet» preset used only `vei` 0.8 and `skyfri` 1.

### 2.5 Reproduced outputs (current data, original TS = Python port)

Top 6 areas (≥ 40 km apart), `relativ` in brackets, and counts per class:

| preset | top areas | #cells ≥0.9 / 0.6–0.9 / 0.35–0.6 / 0.15–0.35 |
|---|---|---|
| `fakta` (default) | **60.9,11.4 (1.00)**; 60.2,12.4 (0.78); 60.0,11.0 (0.61); 62.8,11.6 (0.61); 59.3,11.8 (0.61); 60.3,10.2 (0.61) | 1 / 14 / 147 / 679 |
| `alt` | **60.9,11.2 (1.00)**; 61.4,11.0 (0.86); 62.3,11.4 (0.60); 60.4,10.2 (0.59); 61.2,12.2 (0.45); 64.1,12.4 (0.35). Class-0 cells: 60.7/60.8/60.9, 11.2 | 3 / 16 / 46 / 177 |
| `innlandet` | 60.9,11.4 (1.00); 60.2,12.4 (0.67); 60.6,12.4 (0.59); 61.2,12.2 (0.57); 60.5,11.6 (0.46); 61.4,11.0 (0.31) | 1 / 5 / 46 / 66 |
| `fly` | 60.9,11.4 (1.00); 60.2,12.4 (0.65); 60.0,11.0 (0.41); 62.8,11.6 (0.41); 59.3,11.8 (0.40); 60.3,10.2 (0.40) | 1 / 2 / 26 / 85 |
| `kort` | 61.5,11.2 (1.00); 61.4,12.6 (0.93); 61.5,10.4 (0.88); 61.9,11.0 (0.78); 61.7,12.0 (0.75); 61.9,10.2 (0.70) | 5 / 140 / 148 / 158 |
| `defaultno` | 60.9,11.2 (1.00); 61.3,11.2 (1.00); 60.6,12.4 (0.99); 61.3,12.4 (0.98); 61.6,10.6 (0.63); 61.7,11.4 (0.47) | 17 / 47 / 44 / 32 |
| `retning` | 60.4,8.8 (1.00); 60.0,10.4 (0.98); 60.2,9.6 (0.97); 60.5,8.0 (0.82); … | 8 / 13 / 14 / 15 |
| `agder` | 58.7,8.2 (1.00); 58.9,8.8 (0.61); 58.5,8.8 (0.60); … | 7 / 26 / 35 / 37 |
| `norheimsund` | 60.4,6.2 (1.00); 60.4,5.4 (0.12); … | 2 / 3 / 10 / 17 |

The default best cell is (60.9, 11.4), centred ~10 km east of Løten.
- OSRM drive 1.85 h, snap 574 m.
- Nearest plane position 7.9 km away (NOZ56U).
- Inside `SOL_I_DAG` ring 0.
- Inside Innlandet.
- 3 of its 5 community-exclusion keys are excluded (`utelukket` f = 0.4). This does not matter in `fakta`, where that weight is 0.

### 2.6 Sensitivity (our runs: `sens.out`)

| variant of `fakta` | #cells ≥ 0.9 | top 5 |
|---|---|---|
| as coded | 1 | 60.9,11.4 · 60.2,12.4 (0.78) · 60.0,11.0 · 62.8,11.6 · 59.3,11.8 |
| `solidag` = 0 | **25** | 60.0,11.0 (Lillestrøm/Gardermoen side) · 62.8,11.6 (Holtålen) · 59.3,11.8 (Østfold) · 60.3,10.2 · 60.8,11.2, all ≈1.00 |
| `skyfri` = 0 | 1 | 62.6,6.4 (Sunnmøre!) · 60.9,11.4 (0.87) · … |
| fly = only NOZ56U + NOZ9EG | 1 | 60.9,11.4 · 61.2,10.8 (0.56) · 60.5,11.6 (0.37) |
| two planes, `solidag` = 0 | 5 | 60.8,11.2 · 61.2,10.8 (0.93) |
| two planes at 21:31:28 (default.no epoch, see §6) | 2 | 61.1,11.4 · 60.8,10.8 (0.54) |
| two planes at 21:31:28, `solidag` = 0 | 7 | 60.8,10.8 · 61.1,11.4 (0.92) |
| + `utelukket` 0.8 | 15 | 60.3,10.2 · 60.8,11.2 · 64.1,12.4 (Namdalen) · 64.7,12.8 · 61.2,10.8 |
| + `innlandet` 1 | 1 | 60.9,11.4 · 60.2,12.4 · 61.2,10.8 |

What this shows:
- The single "best" cell depends on the hand-drawn sun polygon and the time assumed for the pointing.
- The "fly" factor, as coded, does not discriminate: it rewards cells under any airliner.
- The community exclusion map treats the area north of its image (≳ 63.3° N) as open, so Namdalen rises when it is weighted.

### 2.7 How named places score (our probe: `probe.out`)

Values are from the nearest grid cell. "Point" checks are exact at the given coordinate.

| place (coords) | cell | drive | snap | rel `fakta` | rel `alt` | point in Windy blue? | in Sol 23.09? | nearest `fly` pos |
|---|---|---|---|---|---|---|---|---|
| Digeråsen tip (61.1788, 11.2639) | 61.2,11.2 | 2.89 h | 168 m | 0.30 | 0.55 | no | yes | 16.4 km |
| Kroktjennet ~891 moh (61.2405, 11.01) | 61.2,11.0 | 2.63 h | 3,173 m | 0.30 | 0.48 | no | no | 5.7 km |
| Birkebeinervegen, Ringsakfjellet (61.36168, 10.84625), retracted | 61.4,10.8 | 3.69 h | 429 m | **0.00** | **0.00** | yes | no | 7.8 km |
| Birkebeinerveien ridge (61.4495, 10.9752), retracted | 61.4,11.0 | 3.27 h | 576 m | 0.51 | 0.86 | yes (point) / no (cell centre) | no | 7.3 km |
| Prøysenstua (60.912, 10.8076) | 60.9,10.8 | 1.82 h | 63 m | 0.23 | 0.43 | no | no | 21.2 km |
| Tretopphyttene (60.9748, 10.9167) | 61.0,11.0 | 2.28 h | 797 m | 0.41 | 0.70 | no | no | 11.3 km |
| Benningstad (60.7685, 11.3575) | 60.8,11.4 | 1.71 h | 83 m | 0.47 | 0.65 | no | no | 9.0 km |
| Haslemoen (60.66, 11.87) | 60.7,11.8 | 2.19 h | 41 m | 0.37 | 0.21 | no | yes (exclusion key = `C`) | 31.7 km |
| NOZ56U @21:29:50 = `FLY_PUNKT` (60.8705, 11.2481) | 60.9,11.2 | 1.79 h | 72 m | 0.60 | 1.00 | no | no | 2.9 km |
| NOZ9EG @21:29:15 = `FLY_PUNKT2` (61.216, 10.896) | 61.2,10.8 | 2.58 h | 1,441 m | 0.56 | 0.84 | no | no | 5.1 km |
| SAS50J 25.09 17:22 (60.59, 11.536) | 60.6,11.6 | 2.29 h | 369 m | 0.41 | 0.58 | no | no | 24.5 km |
| default.no fusion #1 (61.45, 11.1) / Gålaveien / Madsskardveien | 61.5,11.0 | 3.52 h | 31 m | **0.00** | **0.00** | cell centre yes | no | 17.2 km |
| Tolvmilskogen (60.69, 12.35) | 60.7,12.4 | 2.84 h | 15 m | 0.37 | 0.34 | no | yes (exclusion key = `C`) | 54 km |
| `fellesskap891` centroid (61.339, 10.916) | 61.3,11.0 | 3.26 h | 4,661 m | 0.20 | 0.34 | yes | no | 5.2 km |

---

## 3. Model B: theory percentages (`src/data/teorier.ts`)

### 3.1 Formula

- `sannsynligheter` (L452–456): `raw_t = prior_t · Π_{b ∈ aktive} faktor_b(t)`, then `pct_t = 100 · raw_t / Σ raw`.
- The header comment (L1–3) reads: «Prosentene regnes som i et enkelt Bayes-oppsett: forhåndsvekt × produktet av hint-faktorene, normalisert til 100 %.»
- The UI says: «Faktorene er skjønn, ikke fasit» (TeoriPanel L341) and «Prosentene er et anslag basert på skjønn, ikke fasit» (L267–269).
- **Modes** (`standardBevis`, L447–449):
  - «Alt vi har» uses every BEVIS with `standardPa: true` (28).
  - «Bare hint» also drops `kilde: 'folk'` (15 remain).
  - The app loads in mode `'alt'` (`App.tsx` L55–56).
  - Switching mode resets the toggles to that mode's defaults (L347–349).
- `andelInnenfor(t, rings)` (L170–186) is the share of a theory circle inside polygons. It uses a 15 × 15 lattice clipped to the circle (149 points). `dLat = r/111`, `dLon = dLat/cos(lat)`.

### 3.2 Theories (`TEORIER_LISTE`, L26–153)

| id | name | centre | r (km) | drive (h, OSRM) | prior | linked preset |
|---|---|---|---|---|---|---|
| loten | «Hamar–Løten–Elverum (under flyet)» – «Der NOZ56U var da Anja pekte opp» | 60.87, 11.25 | 20 | 1.75 | 1 | fly |
| rena | «Rena–Evenstad (Åmot og Stor-Elvdal)» – «default.no sin toppkandidat» | 61.35, 11.10 | 35 | 3.2 | 1 | innlandet |
| rudshogda | «Rudshøgda (Prøysen-teorien)» | 60.912, 10.808 | 10 | 1.95 | 1 | — |
| ringsaker | «Ringsaker (under NOZ9EG)» – «Sjusjøen–Brumunddal, Tretopphyttene» | 61.08, 10.89 | 20 | 2.4 | 1 | — |
| solor | «Flisa og Haslemoen (Solør)» | 60.64, 11.95 | 20 | 2.55 | 1 | — |
| gjovik | «Gjøvik og Toten» | 60.80, 10.60 | 25 | 2.1 | 1 | — |
| roros | «Nord-Østerdalen og Røros» | 62.70, 11.20 | 50 | 6.7 | 1 | — |
| valdres | «Valdres og Hallingdal» | 60.85, 9.20 | 50 | 3.2 | 1 | retning |
| agder | «Indre Agder» – «Gjerstad og Vegårshei (Froland er ute)» | 58.65, 8.80 | 50 | 3.5 | 1 | agder |
| hardanger | «Norheimsund og Hardanger» | 60.3707, 6.1453 | 35 | 6.55 | 1 | norheimsund |
| annet | «Et helt annet sted» | — | — | — | **4** | — |

Circle overlaps with the polygons (our computation):

| theory | share in Windy blue + fog | `blatt` factor | share in Sol 23.09 | `solidag` factor |
|---|---|---|---|---|
| Løten | 0 | 1.0 | 0.315 | 0.779 |
| Rena | 0.336 | 0.681 | 0.121 | 0.545 |
| Rudshøgda | 0 | 1.0 | 0 | 0.40 |
| Ringsaker | 0.128 | 0.879 | 0.013 | 0.416 |
| Solør | 0 | 1.0 | 1.0 | 1.60 |
| Gjøvik | 0.007 | 0.994 | 0 | 0.40 |
| Røros | 0.121 | 0.885 | 0 | 0.40 |
| Valdres | 0.369 | 0.649 | 0 | 0.40 |
| Agder | 0 | 1.0 | 0 | 0.40 |
| Hardanger | 1.0 | 0.05 | 0 | 0.40 |

### 3.3 All 33 BEVIS (evidence multipliers)

"Std" means on by default. "folk" means counted only in «Alt vi har». Multipliers not listed are 1.

| # | id (line) | title (verbatim) | folk | Std | multipliers |
|---|---|---|---|---|---|
| 1 | kjoretid (L190) | «Kjøretid ca. 7 t (hun sov)» | | off | `0.5 + 0.5·gauss(kjoretid − 7, 2)`; annet 1 |
| 2 | mandag (L197) | «Hentet mandag kl. 04:00, ikke søndag» | | off | drive ≤ 2.5 h → 1.5; ≤ 3.3 h → 0.8; else 0.1; annet 0.7 |
| 3 | blatt (L206) | «Blått på Windy og tåka i Odal er utelukket» | | on | `0.05 + 0.95·(1 − share in SKYDEKKE∪TAAKE)`; annet 0.7 |
| 4 | solidag (L212) | «Sol 23.09 mens det var skyet nesten overalt» | | on | `0.4 + 1.2·share in SOL_I_DAG`; annet 0.6 |
| 5 | soloppgang (L222) | «Sola var oppe før kl. 07 (Anja)» | | on | rudshogda 0.95, gjovik 0.9, valdres 0.5, agder 0.4, hardanger 0.2, annet 0.7 |
| 6 | solmiddag (L231) | «Sola i sør kl. 13:02–13:08 (lengdegrad 11–12° øst)» | | on | ringsaker 0.95, rudshogda 0.95, gjovik 0.9, valdres 0.4, agder 0.3, hardanger 0.1, annet 0.6 |
| 7 | froland (L238) | «Været i Froland stemmer ikke» | | on | agder 0.15 |
| 8 | hagina-bjork (L245) | «Bjørka er for langt på høsten på 510 moh ved Sjusjøen (Hagina)» | folk | on | ringsaker 0.6, loten 1.1, rudshogda 1.1 |
| 9 | brumunddal (L254) | «Anja er fra Brumunddal («nesten hjemme»?)» | folk | on | ringsaker 1.2, rudshogda 1.1 |
| 10 | discord2509 (L261) | «Discord 25.09: Ringsaker–Rena, og Finnskogen» | folk | on | ringsaker 1.3, rena 1.15, solor 1.1 |
| 11 | regn1105 (L269) | «Regn hos Anja og i Rena kl. 11:05 (24.09)» | folk | on | rena 1.4, loten 1.1, rudshogda 1.05, ringsaker 1.05 |
| 12 | frolandekorn (L277) | «Skjermbilde: appen svarer på «FROLAND» (ikke bekreftet)» | folk | off | agder 2.5 |
| 13 | fjellmark (L285) | «Typisk fjellmark» (Anja) | | on | ringsaker 1.4, rena 1.2, roros 1.3, loten 1.0, rudshogda 0.6, gjovik 0.7, solor 0.8, agder 0.8 |
| 14 | bokstaver (L292) | «Vervebokstavene = NORHEIMSUND?» | | on | hardanger 2 |
| 15 | fly (L299) | «Et fly rett over kl. 21:29 (NOZ56U eller NOZ9EG)» | | on | loten 3, ringsaker 2.5, rudshogda 1.6, rena 1.3, solor 0.7, gjovik 0.8, roros 0.7, valdres 0.8, agder 0.6, hardanger 0.6, annet 0.7 |
| 16 | defaultno (L307) | «default.no sin fusjonsmodell» | | on | rena 1.5, loten 1.2, ringsaker 1.2, rudshogda 1.1, agder 1.3, valdres 1.1, roros 1.1, hardanger 0.8 |
| 17 | terreng (L314) | «Furumo, lyng, bærlyng og tømmerdrift» | | on | rena 1.5, loten 1.4, ringsaker 1.3, rudshogda 1.2, solor 1.5, gjovik 1.2, roros 1.3, agder 1.3, valdres 1.1, hardanger 0.6 |
| 18 | konsensus (L321) | «Nesten alle i chatten er sikre på Innlandet» | folk | on | loten/rena/ringsaker/rudshogda/solor/gjovik 1.2, roros/valdres 1.1 |
| 19 | gjovikvaer (L329) | «Vær og sol passer i Gjøvik» | folk | on | gjovik 1.5 |
| 20 | folk_utelukket (L338) | «Fellesskapets utelukkingskart (fjellbjørk)» | folk | on | rudshogda 1.0, gjovik 0.96, rena 0.94, ringsaker 0.85, loten 0.79, roros 0.28, solor 0.26, valdres 0.15, agder 0.13, hardanger 0.1, annet 0.5 |
| 21 | folk_digeras (L346) | «Flere tipper Digeråsen (Løten/Åmot)» | folk | on | rena 1.4, loten 1.1 |
| 22 | folk_flisa (L354) | «Én tipper Flisa og Haslemoen» | folk | on | solor 1.2 |
| 23 | folk_tretopp (L362) | «Tretopphyttene er sjekket, uten funn» | folk | on | ringsaker 0.8 |
| 24 | folk_ingenhytte (L370) | «Horde unngår hytter i år» | folk | on | ringsaker 0.8 |
| 25 | folk_rudshogda (L378) | «Mange leter ved Rudshøgda nå» | folk | on | rudshogda 1.5 |
| 26 | stjerne (L386) | «Stjerne: Prøysenstjerna og «ser stjernene»» (explanation: «Tynn kobling») | | on | rudshogda 1.2 |
| 27 | folk_benny (L393) | «Reven heter Benny» (Benningstad i Løten) | folk | on | loten 1.05 |
| 28 | proysen (L401) | «Dyrene i boksen er Prøysen-figurer» | | on | rudshogda 2.2, ringsaker 1.4, loten 1.1, rena 1.05 |
| 29 | ekorn (L408) | «Ekornet (Froland, Tretopphyttene)» | | on | agder 1.1, ringsaker 1.1, rudshogda 1.2 |
| 30 | bjorneparken (L415) | «Reklamefarger som Bjørneparken (Flå)» | | on | valdres 1.4 |
| 31 | bergen (L422) | «Kode 5008 = Horde AS i Bergen» | | on | hardanger 1.3 |
| 32 | skyanalyse (L429) | «Skyanalyse-kartet (Agder)» | | off | agder 2 |
| 33 | retning (L436) | «Skiltet (118°) peker mot Oslo» | | off | valdres 1.8 |

Note on #20: the percentages in its explanation («Åpent: Rudshøgda 100 %, Gjøvik 95 %, Rena 93 %, Ringsaker 83 %, Løten 77 %, Røros 20 %, Solør 18 %») are hard-coded into the multiplier table. They are not recomputed from `utelukket.json`.

### 3.4 Output percentages (original TS = Python port)

| theory | «Alt vi har» (app default) | «Bare hint» | Alt minus `fly` | Hint minus symbolic (proysen, stjerne, ekorn, bjorneparken, bergen, bokstaver) | Alt + `mandag` | Alt + `kjoretid` |
|---|---|---|---|---|---|---|
| Løten | **36.39** | **34.13** | 20.65 | **38.65** | **42.16** | **34.32** |
| Rena | 22.14 | 10.82 | **28.98** | 12.83 | 13.68 | 23.56 |
| Rudshøgda | 21.09 | 11.46 | 22.44 | 4.51 | 24.44 | 20.07 |
| Ringsaker | 11.93 | 23.10 | 8.12 | 18.68 | 13.82 | 11.67 |
| Solør | 3.52 | 10.63 | 8.56 | 13.24 | 2.18 | 3.49 |
| Gjøvik | 2.38 | 1.71 | 5.06 | 2.13 | 2.76 | 2.28 |
| Annet | 1.57 | 3.91 | 3.82 | 4.87 | 0.85 | 2.87 |
| Røros | 0.90 | 3.64 | 2.20 | 4.54 | 0.07 | 1.64 |
| Valdres | 0.07 | 0.56 | 0.16 | 0.50 | 0.05 | 0.08 |
| Agder | 0.01 | 0.05 | 0.02 | 0.06 | 0.00 | 0.01 |
| Hardanger | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

Raw products in «Alt» mode (prior × all active multipliers ≠ 1):
- **Løten 5.72**: solidag 0.779, hagina 1.1, regn 1.1, **fly 3**, defaultno 1.2, terreng 1.4, konsensus 1.2, folk_utelukket 0.79, digerås 1.1, benny 1.05, proysen 1.1.
- **Rena 3.48**: blatt 0.681, solidag 0.545, discord 1.15, regn 1.4, fjellmark 1.2, fly 1.3, defaultno 1.5, terreng 1.5, konsensus 1.2, folk_utelukket 0.94, digerås 1.4, proysen 1.05.
- **Rudshøgda 3.31**: solidag 0.4, soloppgang 0.95, solmiddag 0.95, hagina 1.1, brumunddal 1.1, regn 1.05, fjellmark 0.6, fly 1.6, defaultno 1.1, terreng 1.2, konsensus 1.2, **folk_rudshogda 1.5, stjerne 1.2, proysen 2.2, ekorn 1.2**.
- **Ringsaker 1.87**: blatt 0.879, solidag 0.416, solmiddag 0.95, hagina 0.6, brumunddal 1.2, discord 1.3, regn 1.05, fjellmark 1.4, fly 2.5, defaultno 1.2, terreng 1.3, konsensus 1.2, folk_utelukket 0.85, tretopp 0.8, ingenhytte 0.8, proysen 1.4, ekorn 1.1.
- **Solør 0.55**: solidag 1.6, discord 1.1, fjellmark 0.8, fly 0.7, terreng 1.5, konsensus 1.2, **folk_utelukket 0.26**, flisa 1.2.
- **Gjøvik 0.37**.
- **Røros 0.14**.
- **Valdres 0.0116**.
- **Agder 0.0008**.
- **Hardanger ≈ 0**: blatt 0.05, sol 0.4, soloppgang 0.2, solmiddag 0.1, bokstaver 2, …
- **Annet 0.247**: prior 4 × blatt 0.7 × solidag 0.6 × soloppgang 0.7 × solmiddag 0.6 × fly 0.7 × folk_utelukket 0.5.

---

## 4. Layers that are drawn but NOT scored

These carry some of the strongest clues. None of them enters `beregn` or `sannsynligheter`.

| layer (lag.ts line) | data | computation / thresholds | primary clue |
|---|---|---|---|
| `hoyde891` «810–891 moh nær vei» (L232–244) | `hoyde891.json`: 17,234 points on a 0.005° × 0.01° grid (~550 m), `[lat, lon, moh, m to road, road-to-SE flag]`. Extent 59.79–62.805 N, 8.48–12.59 E | Keeps «skog og mark mellom 790 og 911 moh som ligger høyst 900 m fra en bilvei eller skogsbilvei». Colours: < 830 purple, 830–860 lilac, ≥ 860 blue (`Kart.tsx` L522–523). Strong opacity if the road lies to the SE («KOM FRA DEN VEIEN ←», ca. 130°): 69.9 % of points. Height from Kartverket DTM 1 m sampled at ~500 m; roads from OSM. Build script **not in repo** | Horde AI answer to HORDEMINUS: «2,7 eiffeltårn stablet oppå hverandre» (hint `eiffel`, status `bekreftet`, `innhold.ts` L357–365). 2.7 × 300 = 810 m, 2.7 × 330 = 891 m, 2.7 × 324 = 875 m |
| `fellesskap891` (L666–675) | `fellesskap891.json`: 634 cells of 0.005° × 0.01°, 61.16–61.58 N, 10.72–11.19 E | «800–900 moh, der flyene Anja så passer over, med skog og utenfor skytefelt … Stedfestet fra bildet, ca. ±500 m.» Shared in chat 24.09 | same |
| `treslag` (L689–702) | `treslag.json`: 4,139 cells of 0.02° × 0.04° (~2 × 2 km), extent 59.81–62.19 N, 9.82–12.86 E; `[lat, lon, score, furu, gran, lauv]`; target `mal = {furu 0.4, gran 0.25, lauv 0.35}`; NIBIO SR16 «dominerende treslag», fetched 25.09 | **Score = 1 − ½ Σ \|p_i − mal_i\|** (1 − total-variation distance). We inferred this: it reproduces 0.68, 0.66 and 0.81 for the first three cells. Classes: ≥ 0.85 (122 cells), ≥ 0.75 (549), ≥ 0.65 (2,775) (`treslag.ts` L12–16). Minimum stored score is 0.55 | «KANSKJE 35% BJØRK · 25% GRAN · 40% FURU · AKKURAT RUNDT MEG» (25.09 18:13) |
| `vind` (L752–765) | `vind.json`: 449 cells of 0.2° × 0.4° (~22 km), `[lat, lon, m/s, gust]`, time «2026-09-23 17:49», «open-meteo historisk varsel (10 m)», MET Nordic | < 2 m/s «passer med «vindstille»» (128 cells), 2–4 m/s «mulig i le» (203), ≥ 4 m/s «passer dårlig» (118) (`vind.ts` L12–16). In the eastern interior most cells are 1–3 m/s, so it hardly discriminates. The Ringsakfjellet/Evenstad band shows 2.7–4.4 m/s | «LYDTETT · SOL · VINDSTILLE» (23.09 17:49) |
| `storvilt` (L703–712) | `storvilt.json`: 192 Statskog storviltjaktfelt | Popup says «Kassen står ikke i farlig terreng, så dette området er lite sannsynlig» | Horde/Alf: «aldri noe farlig» (TikTok 25.09, relayed) |
| `jaktfritt`, `jaktfritt_bare` (L713–737) | `verneomrader_jakt.json`: 862 protected areas, hunting class read from each regulation: forbudt / delvis / tillatt / ukjent | Visual only | «INGEN SKYTING» (21.09 18:31) |
| `dn_skytefelt` (L306) | default.no `skytefelt.json` (Forsvarsbygg) | default.no penalises cells inside by e^−3 (see §6). Magnus draws them only | «INGEN SKYTING» |
| `utelukket` (L676–688) | as in §2.3 | Visual always. Scored only in the `alt` preset (w 0.8) | community |
| `kommuner` (L738–751) | `kommunevurdering.json`: 350 municipalities from hordejakten.vercel.app, 23.09: 63 «usikkert», 123 «lite sannsynlig», 164 «utelukket» | Visual only | community |
| `felt` «Søkesektor fra parkering» (L855–867) | — | Sector from a draggable parking pin: bearing 300° ± 25°, 0.3–0.9 km (`Kart.tsx` L715). Text: «Fra bilen ligger kassen altså mot ca. 300° (±25°, nordvest), 300–900 m unna, oppover og uten sti» | «KOM FRA DEN VEIEN ←», «ØST CA 118 · RETNING SKILT», «CA 5–10 MIN Å GÅ FRA BIL» |
| `retning` lines (L203–217) | — | 298°/118° from Oslo ± 5°; 118° from Horde Bergen, plus «korrigert for misvisning (ca. 123°)». The scored factor uses 118° true only, with no declination | «ØST CA 118 · RETNING SKILT», «118–120 GR ØST» |
| `fly`/`fly_alle` (L826–854) | `fly_2130.json`; `FLY_2509` (SAS50J 25.09 17:17–17:27, `innhold.ts` L1638–1641) | 10-km rings around `FLY_PUNKT`, `FLY_PUNKT2` and SAS50J (60.59, 11.536) (`Kart.tsx` L490–493). **The SAS50J sighting is not scored anywhere** | 21.09 21:29 pointing; 25.09 17:22 pointing |

---

## 5. Retractions, corrections and inconsistencies in the Magnus repo (git history)

| commit (CEST) | change | relevance |
|---|---|---|
| `b55eafc` 23.09 19:13 | «Remove the pink "no mushrooms" exclusion, which was not correct». Open shares were recomputed (Gjøvik 95 %, Røros 20 %) | community exclusion retracted in part |
| `fc71636` 23.09 20:03 | «Mark everything west of the community exclusion map as excluded» | a fill-in assumption, not evidence |
| `893318a` 24.09 19:55 | «Stop marking unverified things as confirmed»: FROLAND/«Ekornet kan klatre» and LD6788/«ENKODE» demoted to «Usikker» (screenshots from chat). «The sign pointed 118–120°; «mot kassen» was an interpretation and is removed». «Sure facts: she walked 5–10 min from the car and *thinks* it was uphill; the door lock has 5 or 6 digits» | downgrade of the app-screenshot claims |
| `01ab80d` 25.09 11:29 | «Stream delay is now «trolig 20 sek–1 min (vi tipper)», not 45 s» | But `StreamPanel.tsx` L16 still says «Streamen er bekreftet {45} sek forsinket», and `STREAM.forsinkelseSek: 45` remains (`innhold.ts` L10) |
| `63416f0` 25.09 11:07 | New default preset «Bekreftet: vær, sol og fly» | the default map now includes fly and sun polygons |
| `e431102` 25.09 14:12 | «Remove everything about Birkebeinervegen». Removed: the tip, the news item, the theory evidence, the terrain pin (`DEFAULTNO_TERRENG` «Birkebeinerveien» 61.4495, 10.9752), the fjellmark mention, and «Birkebeinerveien search stops, places and field notes from our copy of default.no data». **No reason given** | see §7 |
| `337ddc2` | «Remove the Horde AI «grevling» reply: it was not repeatable in a new chat» | app-response retraction |
| `6cddb71` 23.09 15:46 | «Rule out Froland: the weather does not match» | Agder ×0.15 |

**Internal time inconsistency for the 21.09 pointing** (`fly.ts` L12–13, `innhold.ts` L749, L1086, L1167, L1177):
- Stream time of the pointing: 21:29:38. «FLY» was written at 21:30:12–21:30:30 (stream time).
- The scored model uses `PEKETID_EKTE = '21:29:15'`, an implied 23-s delay, with a window of ±60 s.
- The Digeråsen popup uses «21:28:53 ekte tid» (45-s delay).
- `FLY_PUNKT` (60.8705, 11.2481) is «ekte tid ca. 21:29:50».
- `FLY_PUNKT2` (61.216, 10.896) is «ca. 21:29:15».
- default.no's own solve used a different epoch (§6).

**Three inconsistent statements of "default.no's #1":**
- `lag.ts` L794: «Merk at nr. 1 bare er ca. 3,5 t fra Oslo». But `DEFAULTNO[0]` (60.9, 11.2) is 1.79 h by OSRM.
- `teorier.ts` L309: «Nr. 1 er Rena/Åmot, nr. 2 Risør/Gjerstad».
- `innhold.ts` L1160: #1 «Hamar øst mot Løten (skog)».
- The mirrored default.no fusion `alle.json` (24.09 18:31) has #1 = 61.45, 11.1.

---

## 6. default.no data mirrored inside Magnus (model outputs, for context)

Fetched 24.09 18:36 («hentet 24.09 kl. 18:36», `defaultno.ts` L1).

- **Fusion model** (`public/data/defaultno/fusjon/*.json`, grid lat0 57.8, dlat 0.05, lon0 4.3, dlon 0.1 ≈ 5 × 5 km).
  - Colours: top 2 % / 15 % / 40 % (`defaultno.ts` L58–59).
  - The popup shows «Straff per bevis (0 = passer)» (penalty per evidence, lower = better). `m10`/`m25` = «Sannsynlighet innen 10 km / 25 km».
  - Evidence list for `alle` (updated 2026-09-24T18:31:43+02:00):
    - «weather (400 stations)»
    - «prior (mostly flat / no ferry: west-coast routes penalised)»
    - «drive from Oslo 3-8.5 h soft (~162-458 km straight line)»
    - «live MET now (81 points, 0 raining, 4.8-16.5 C)»
    - «skytefelt (Forsvarsbygg): 68 ranges, 77 cells inside penalised e^-3»
    - «plane sighting (3 event(s), 125 aircraft tracked)»
    - «INGEN FLY by day: 1255 aircraft 07:00-18:31, cost per >= 40 deg pass»
    - «rain elsewhere since stream start: 796 wet of 831 stations, radar 76 snapshots»
    - «satellite clouds (4 passes)»
    - «tyttebær (GBIF dry-heath share, weak)»
    - «furu (NIBIO SR16 pine share + forest cover)»
- **Top areas of `alle`:**

| rank | lat, lon | m10 | m25 |
|---|---|---|---|
| 1 | 61.45, 11.1 | 0.110 | 0.289 |
| 2 | 60.95, 11.3 | 0.078 | 0.265 |
| 3 | 60.7, 11.6 | 0.060 | 0.171 |
| 4 | 60.5, 5.1 | 0.015 | — |
| 5 | 61.75, 11.1 | — | — |
| 6 | 59.9, 11.2 | — | — |
| 7 | 61.1, 11.0 | 0.045 | 0.232 |
| 8 | 58.5, 6.3 | — | — |

- **Other variants' top area:**
  - `utenlyd` (without sound and sun): 61.45, 11.1 (m10 0.164).
  - `utenmerker`: 61.4, 11.1.
  - `fly` (planes only): 67.8, 15.5 (non-discriminating).
  - `flyskog`: 58.55, 6.1.
  - `stille`: 61.35, 11.0.
  - `stilleskog`: 60.55, 6.5.
  - `utenfly` (13:21): 61.45, 5.6.
  - `utenflylyd` (22.09 14:29): 61.75, 8.4.
- **`steder.json`:** camera `retning` 219.0°, 34 search areas, 117 sites (126 before the Birkebeiner removal). Area share `p`:

| area # | lat, lon | p |
|---|---|---|
| 1 | 61.45, 11.1 | 0.127 |
| 2 | 60.7, 11.6 | 0.056 |
| 3 | 60.95, 11.3 | 0.054 |
| 5 | 58.55, 6.1 | 0.044 |
| 9 | 61.2, 10.9 | 0.035 |

- **`plan.json`:** generated «2026-09-24 17:04». Note: «alle klarer de tre flyene hun saa (innen 5 grader), rangert etter site finder-score, fusjon og skogtype fra laser (hogstflater/jorder nedprioritert, moden skog opp); sjekkede stopp ligger sist; boksen staar i moden skog 15-22 m med lysning». 40 stops before the removal, 36 after.
- **`defaultno_mer.json` observations:**
  - Event 1: «Hun peker opp 21:29:38, skriver «FLY» 21:30:12, og lyden er sterkest 21:33:20.» Window 21:29:40–21:34:00, minimum elevation 25°.
  - Its solve record (`lost[0]`) is `utc 2026-09-21T19:31:28+00:00` = **21:31:28 CEST**, «125 fly», «948 ruter».
  - That equals the midpoint of 21:29:40–21:34:00 minus 22 s. This is our inference; the same −22 s offset fits events 2 and 3 exactly (20:32:40 → 20:32:18; 20:34:40 → 20:34:18).
  - So default.no scored the planes ~2 min later than Magnus does. At 21:31:28, NOZ56U was at 61.037, 11.282 (27,157 ft) and NOZ9EG at 60.933, 10.871 (18,288 ft). At 21:29:15 they were at 60.813, 11.237 and 61.217, 10.896.
- **Sun path:** «beste 59.5» (rms 3.296, heading 219.6°). Latitudes 59.0–60.5 differ by < 0.04 rms, so this is a weak constraint.
- **«INGEN FLY» rarity top cell:** 61.3, 11.0 (2 day passes ≥ 40°; 21:30 plane at 55.4°).
- **Flylyd best cell:** 60.0, 9.9. The site itself says «Lyden kan være spilt av på nytt».
- **Sound loop** (`analyse.json`): 604 minutes checked against 52.86 h; 227 minutes have a copy with r > 0.8; lags 23.9 h (290), 47.9 h (48).

---

## 7. The Birkebeinervegen / Birkebeinerveien removal (retraction without reason)

What was deleted in `e431102` (diffed against `e431102~1`):

- **Magnus "Hva folk tror" entry:** «Birkebeinervegen over Ringsakfjellet (Ringsaker–Rena)», pos 61.36168, 10.84625. It read: «Birkebeinervegen går over fjellet mellom Ringsaker, Stor-Elvdal og Øyer, ca. 720–1040 moh. Det er 341 steder på 810–891 moh nær vei her, 233 av dem med vei mot sørøst. Passer godt med 2,7 eiffeltårn, og området er ikke utelukket.»
- **`DEFAULTNO_TERRENG`:** «Birkebeinerveien» 61.4495, 10.9752 (Rena/Åmot).
- **9 default.no "site finder" sites** on Birkebeinerveien (tertiary road). Scores 0.748–0.995, e.g. 61.44874, 10.97747: score 0.995, 605 moh, 556 m from road, rise 75.3 m, relief «match», furu true. The Rena/Birkebeinerveien sites sit at ~575–606 moh. That is **not** 810–891.
- **4 default.no plan stops «Birkebeinerveien vest/nord»:**

| rank | lat, lon | site_score | fusion | plane_shortfall | dayplanes | walk |
|---|---|---|---|---|---|---|
| 10 | 61.447, 10.965 | 0.77 | 1.15 | 0 | 3 | 82 m @ 45° |
| 18 | 61.453, 10.952 | — | — | — | — | — |
| 20 | 61.429, 10.95 | — | — | — | — | 537 m @ 99°, +74 m |
| 38 | 61.44, 10.951 | — | — | — | — | — |

- **default.no field pins:**
  - «BOM / privat vei (23.09 ca 00:30) - Birkebeinerveien-avkjoring mot 61.4495,10.9752. Ga forbi bommen til fots, 500 m»
  - «privat vei - pin Birkebeinerveien-ryggen, ikke sjekket til fots»
  - «PLAN 7 Birkebeinerveien pin: bom 61.4452,10.9756, ga 500 m NNO forbi bommen (sjekket bare fra veien)»

Status: removed from the Magnus mirror with no stated reason. The originals presumably still exist on default.no (not verifiable from here; default.no is blocked). As of 23.09 ~00:30 the ridge pin was «ikke sjekket til fots». We treat this as an open, unexplained lead, not as evidence.

---

## 8. Critical assessment

### 8.1 The "fly" factor does not do what it says (major)

- `posisjonerRundtPeking` (`fly.ts` L35–46) takes **all** aircraft in `fly_2130.json`. The UI text and the `fly` layer describe only the two planes NOZ56U and NOZ9EG. The FAKTORER text is generic: «Nær sporet til et fly som var i lufta da Anja pekte opp».
- That is 38 contributing aircraft and 465 positions, including approaches and departures at Gardermoen above 3,000 ft.
- Consequences:
  - The cells at 60.0, 11.0 (Gardermoen/Lillestrøm side), 62.8, 11.6, 59.3, 11.8 and 64.1, 12.4 get fly ≈ 1.0.
  - 9.1 % of Norway's cells score ≥ 0.5, against 0.9 % with the two named planes.
  - The 25.09 whiteboard «FLYENE ER SÅ LANGT UNNA AT DET ER UMULIG Å SE PÅ DAGEN…» and 23.09 «LITE MED FLY HER» argue against low approach traffic. Commit `01ab80d` itself says «planes are far up, not low approaches».
- **Geometry.** The factor uses horizontal distance only, with σ = 10 km. «Pekte rett opp» with a plane at ~23,000 ft (7 km) and 10 km offset means an elevation of ~35°. default.no required ≥ 25° and scored at a different epoch.
- **Interpolation.** Linear interpolation between fixes ~90 s apart (≈ 20 km per segment) is acceptable for cruise, but not for turning traffic.

### 8.2 Hard veto from a hand-drawn Windy screenshot, tested at cell centres (major)

- `skyfri` has weight 100 % in 8 of 9 presets. Any cell whose centre falls in `SKYDEKKE` or `TAAKE` becomes exactly 0.
- The polygons were traced by hand from a Windy screenshot. The site admits «(feil under ca. 10 km)» and calls the Lillehammer–Sweden band «mest usikkert» (`lag.ts` L223).
- The band zeroes, at cell level:
  - default.no's #1 area (cell 61.5, 11.0 contains 61.45, 11.1, Gålaveien and Madsskardveien);
  - the Birkebeinervegen/Ringsakfjellet cells (61.4, 10.8; 61.3, 10.6–10.8);
  - 53 % (337/634) of the community `fellesskap891` cells;
  - 970 of the 2,850 `hoyde891` cells in the core box 60.5–62.0 N / 10.3–12.3 E.
- Windy shows **model** cloud or precipitation, not observations. "Blue on Windy" at one moment is weak evidence against a clear sky at a point.
- In the theory model the same band enters as `blatt`, with a floor of 0.05. That is less harsh.

### 8.3 The default "best cell" is a polygon-edge artifact (major)

- `SOL_I_DAG` was «Grovt tegnet ut fra en beskrivelse (Kongsvinger–Rena mot Sverige, deler av Vestfold, Trondheim–Ålesund), ikke fra selve bildet» (`lag.ts` L766–775). It is a binary factor at w = 0.5.
- Cells just inside its west edge (60.9, 11.4) beat cells just outside by ×2. With the polygon switched off, 25 cells tie at ≥ 90 % (§2.6).
- The Trondheim–Ålesund ring (ring 2) overlaps the Windy blue polygon, which the code comment acknowledges.

### 8.4 Double counting

- **Grid model:**
  - `alt` stacks `fly` (0.6) and `defaultno` (0.3). default.no's fusion already contains «plane sighting (3 event(s)…)» and satellite clouds, so the plane and sky evidence enters twice.
  - `innlandet` (0.5) is itself justified by «flyet over Hamar/Løten, klar himmel på Østlandet, furumo … og default.no sin topp-kandidat» (hint `innlandet`). It re-counts fly, sky and default.no.
  - `utelukket` (0.8) is a community map partly based on weather/vegetation, and it overlaps `skyfri`.
- **Theory model:**
  - Plane: `fly` (Løten ×3, Ringsaker ×2.5), then `defaultno` (built on the planes), then `konsensus` (explicitly «Bygger mest på de samme hintene»), plus `folk_digeras`, whose argument is the NOZ56U overhead time.
  - Sun/longitude: `soloppgang`, `solmiddag`, `solidag` and `blatt` all encode east-vs-west and are multiplied independently (Hardanger 0.05 × 0.4 × 0.2 × 0.1).
  - Prøysen theme: `proysen` ×2.2, `stjerne` ×1.2, `folk_rudshogda` ×1.5 and `ekorn` ×1.2 give ≈ ×4.75 for Rudshøgda from one correlated idea. `folk_rudshogda` («Mange leter ved Rudshøgda nå») counts popularity as evidence.
  - Rena: `discord2509`, `folk_digeras`, `regn1105` and `defaultno` are all partly the same community momentum.
  - Tretopphyttene: `folk_tretopp` and `folk_ingenhytte` (each ×0.8) penalise one sub-site but are applied to the whole 20-km Ringsaker circle.
  - Terrain: `terreng` and `fjellmark` are two terrain-type readings of overlapping whiteboard content.

### 8.5 Arbitrary weights, priors and constants

- **Priors.** Theory priors are all 1 regardless of circle size. That covers radii from 10 km (Rudshøgda, 314 km²) to 50 km (Røros, Valdres, Agder, 7,854 km²), so prior density per km² differs 25×. «Annet» gets a flat 4 and fixed multipliers (0.7, 0.6, 0.7, 0.6, 0.7, 0.5) not derived from any area computation.
- **Grid constants.**
  - Road-snap threshold 1.5 km and decay 2 km.
  - σ = 10 km (fly), 20 km (Norheimsund), 25 km (default.no), 35 km (Agder).
  - Direction σ = max(8 km, along·tan 5°).
  - Preset weights like 0.8/0.7/0.5.
  - None of these is calibrated. The code says: «Faktorene er skjønn, ikke fasit».
- **Labels.** «Bekreftet» (the default) contains three `tolkning`-status inputs. «Bare hint» (theory) includes `defaultno` (a model output), `bokstaver` (obsolete) and `fly` (an interpretation).

### 8.6 Missing constraints (never scored)

- **Altitude.** 810/891 (or 875) moh from Horde AI «2,7 eiffeltårn» exists only as a layer. The site calls the hint `bekreftet` and says «Mest trolig står kassen ca. 810 eller 891 moh».
- **Tree mix.** 35/25/40 (layer only).
- **Wind.** «VINDSTILLE» 23.09 17:49 (layer only).
- **Second pointing.** SAS50J 25.09 17:22 (drawn only).
- **Other whiteboard clues:**
  - «INGEN SKYTING»: firing ranges and hunting (layers only).
  - «DET HAR VÆRT HOGD TIDLIGERE DER JEG GIKK»: logging (default.no layer only).
  - «KOM FRA DEN VEIEN ←»: road to the SE, used only as a colour flag in `hoyde891`; the mirror ambiguity is ignored.
  - «INGEN VANN ELLER VANNLYDER».
  - «INGEN HYTTE I NÆRHETEN».
  - «INGEN FERIST SOM JEG MERKA».
  - «INGEN STIER».
  - «GRÅVÆR HELE DAGEN» (24.09), «OVERSKYET» (25.09), «INGEN TÅKE» (25.09 09:49).
  - Rain at 11:05 (24.09): only as a theory multiplier.
- **Organizer statements.** Alf's «aldri noe farlig, som å krysse en elv» and the rule that the box is in Norway, not on an island and not in dangerous terrain.
- **Camera heading.** 41°/221° is used only as an argument that the sunlight is real.
- **Drive time.** Correctly excluded by default. The `mandag` alternative (pickup Monday 04:00, stream start 06:50 → < 3 h) is off.

### 8.7 Resolution and proxy problems

- **Cell size.** An 11 × 11 km cell is judged by one centre point: road snap, polygons and exclusion keys. A cell can be zeroed although most of it is outside a polygon (e.g. 61.5, 11.0), or pass although most of it is inside.
- **Road network.** OSRM's car profile routes on public and service roads, but not on `highway=track` (skogsbilvei/traktorvei). So `snap_m` overstates the distance to the nearest drivable forest road. The `vei` factor then penalises exactly the forest areas the box is likely in.
- **Map extents.** The grid stops at 66.0° N. `innlandet` ignores polygon holes.
- **Exclusion map fill-in.** `utelukket.json` fills west of 8.4° E as excluded but leaves the uncovered north (> ~63.3° N) and the far east as open. Its «fjellbjørk» (`C`) class covers large lowland areas of Solør/Finnskogen/Kongsvinger (≈60.0–61.4 N, 11.4–12.6 E). Mountain birch there, at ~200–400 moh, is implausible, which suggests a georeferencing or legend-reading error. The Magnus text itself says the map was «Stedfestet fra et bilde … (±10 km)».
- **Neighbour rule.** The `utelukket` 5-key rule uses the centre and ±0.05° lat, ±0.1° lon. It gives only partial penalties (0.2 steps), so the factor is an ad-hoc smoothing.

### 8.8 What the models are good for

- The code is transparent: every weight is visible and adjustable.
- The site separates `folk` from its own observations and credits its sources.
- It has corrected itself several times (§5).
- The treslag, hoyde891 and vind layers are well-built data products. They could be fused properly (see §9).

---

## 9. Our overlay of the unused Magnus layers (model output, ours; `overlay.out`)

Method: every `hoyde891` point (790–911 moh, ≤ 900 m from road) was joined to:
- the nearest `treslag` cell;
- the `vind` cell;
- distance to NOZ56U/NOZ9EG at 21:29:15;
- the Windy, sun and exclusion flags.

This is exploratory. We did no new data acquisition.

- **Within 10 km of NOZ56U at 21:29:15 (60.813, 11.237):** 0 altitude cells, and none within 20 km. The nearest is 24.1 km away (61.03, 11.26, 791 moh).
- **Near NOZ56U at 21:29:50 (`FLY_PUNKT`):** the nearest is 17.7 km. The Løten/Hamar lowland (~200–500 moh) is incompatible with the 810–891 moh reading.
- **At default.no's epoch 21:31:28:** NOZ56U was 0.7 km from an 803 moh cell (61.035, 11.27). There are 4 cells within 10 km: 61.03, 11.26 (791); 61.035, 11.27 (803); 61.04, 11.26 (810); 61.04, 11.27 (806). They are 457–856 m from road, and none is in Windy blue.
- **Within 10 km of NOZ9EG at 21:29:15 (61.217, 10.896):** 215 altitude cells (668 within 20 km). The cluster sits on Ringsakfjellet, 61.1–61.3 N, 10.6–11.0 E, and 251 of the 460 cells within 15 km are inside the Windy blue band.
  - The best tree-mix matches there are only 0.69, e.g. 61.155, 10.87 (863 moh), 61.16, 10.87 (871 moh), 61.15, 10.86 (836 moh). All have the road to the SE, wind 2.7 m/s, and are outside the Windy band at point level.
  - SR16 shows spruce-dominated stands at that height.
- **Near SAS50J 25.09 17:22 (60.59, 11.536):** 0 altitude cells within 20 km; the nearest is 34.9 km.
- **Tree mix ≥ 0.75 at 810–891 moh:** these cells are ≥ 35 km from both 21.09 pointing positions. They cluster at 61.6–62.1 N (Nord-Østerdalen/Rondane fringe) and 61.8, 12.0.

Implication (interpretation): no single area satisfies all four readings together:
- **Altitude** 810/891, taken literally as moh;
- **overhead planes**: NOZ56U, NOZ9EG, or SAS50J;
- **tree mix** 35/25/40;
- **Windy exclusion.**

At least one of these readings must be wrong or loosely applied. The Ringsakfjellet/NOZ9EG cluster is the only place where altitude, road direction and a pointing plane coincide. Anyone using it must accept that the Windy blue band is wrong there, and that the SR16-derived tree mix is a poor proxy.

---

## 10. Contradictions found

1. **Plane set.** The UI says the fly factor uses NOZ56U and NOZ9EG. The code uses all 38 aircraft above 3,000 ft.
2. **Stream delay.**
   - `StreamPanel.tsx` L16 says «bekreftet 45 sek forsinket».
   - fly.ts, lag.ts and innhold.ts say «trolig 20 sek–1 min (vi tipper)».
   - The model uses 23 s (21:29:15). The Digeråsen text uses 45 s (21:28:53). `FLY_PUNKT` is 21:29:50. default.no scored at 21:31:28 (inferred).
3. **"default.no #1".**
   - Hamar øst mot Løten (`innhold.ts` L1160).
   - Rena/Åmot, with #2 Risør/Gjerstad (`teorier.ts` L309).
   - «ca. 3,5 t fra Oslo» (`lag.ts` L794), which matches neither.
   - The mirrored fusion `alle` (24.09 18:31) has #1 = 61.45, 11.1.
4. **Theory «Rena–Evenstad» vs the grid.** The theory model credits Rena ×1.5 for default.no. The grid hard-zeroes the cell holding default.no's #1 (61.5, 11.0) via the Windy band.
5. **Community map vs model.** The site publishes `fellesskap891` («800–900 moh … flyene … skog») as a layer, yet 53 % of it is hard-excluded by the site's own default model.
6. **`bokstaver`.** Marked solved (HORDE MINUS, status `lost`), but still gives Hardanger ×2 by default. The grid still has a `bokstaver` factor with a Norheimsund preset.
7. **Birkebeiner.** The Birkebeinervegen tip was presented on 25.09 as «Passer godt med 2,7 eiffeltårn, og området er ikke utelukket». It was removed ~3 h later without a reason. The Birkebeinerveien (Rena) sites are ~600 moh, so the altitude argument applied only to the Ringsakfjellet road.
8. **«Fjellbjørk» over Solør/Finnskogen lowland** in `utelukket.json`. This is botanically implausible, and it drives Solør ×0.26 in the theory model.

---

## 11. Open questions

- Why was everything about Birkebeinervegen/Birkebeinerveien removed on 25.09 14:12? Was the ridge pin (61.4495, 10.9752) ever checked on foot?
- Which epoch and delay is right for the 21.09 pointing? 23 s, 45 s, or default.no's window midpoint (21:31:28)? The answer moves the NOZ56U "overhead" point by ~25 km along its track (60.81 → 61.04 N).
- Should the fly constraint use the elevation angle (≥ 25°, as default.no does) and only aircraft matching «pekte opp, litt mot sørøst»?
- How was `hoyde891.json` built? The script is not in the repo. Which OSM road classes count as «bilvei eller skogsbilvei»? How exactly is the SE-road flag defined?
- How was `treslag.json` aggregated from SR16? Dominant species per stand makes birch shares unreliable.
- What did the original community exclusion image show as «lyseblått»? Is the georeferencing over Solør correct?
- Where is the original Windy screenshot, and for what model and time? How robust is the Lillehammer–Sweden band?
- Is the SOL_I_DAG polygon reproducible from an actual 23.09 satellite image (NASA GIBS or MODIS) rather than from a verbal description?

---

## 12. Reproduction

```
cd /home/user/test/evidence/sources/community_models_port
/home/user/test/.venv/bin/python run_model.py      # grid presets, top areas, class counts, factor coverage
/home/user/test/.venv/bin/python teorier_port.py   # theory % in all modes + per-factor breakdown
/home/user/test/.venv/bin/python probe.py          # named places
/home/user/test/.venv/bin/python sens.py           # sensitivity variants
/home/user/test/.venv/bin/python overlay.py        # hoyde891 x treslag x vind x planes overlay
# validate against the ORIGINAL TypeScript (see header of validate_original.ts)
```

`magnus_model.py` is a line-by-line port. The constants are copied from `innhold.ts` L13, L15, L1147–1191 and `teorier.ts` L26–441. It uses JS rounding for `utelukkNokkel` and the same point-in-polygon and cross-track formulas.
