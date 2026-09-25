# Hints B: the second half of the community hint database (MagnusPladsen map, `innhold.ts` lines 470–880)

**Scope.** This file extracts every entry in the second half of the `HINT` array in
`/home/user/test/data/raw/magnus/src/data/innhold.ts`. Lines 470–878 hold 43 entries, from `lydtett` to
`tommer`. Line 878 closes the array, and line 880 is the header comment of the `TAVLE` (whiteboard) log.

**Mirror state.** The mirror (MagnusPladsen/hordejakten-2026) is at HEAD `68faa86`, committed
2026-09-25 21:04:38 +0200. The file has 107 commits. Every entry's full revision history was rebuilt
from git (see section 5, and `hints_b_checks/hint_hist.txt`).

**Author of this extraction.** Written by an automated agent on 2026-09-25 (evening CEST). The
analysis is in English. Norwegian primary text is quoted verbatim in «» or '…' exactly as it appears
in the source.

**What each record field means in the source.** Each HINT record has these fields:

- `tekst`: what the map authors present as the observation. This field often mixes primary evidence
  with the community's own reading of it.
- `betydning`: the map authors' interpretation.
- `status`: one of `lost` (solved), `bekreftet` (confirmed), `tolkning` (interpretation), `usikker`
  (uncertain) or `apen` (unsolved). This is the map authors' own label, not ours.
- `kilde`: the source.
- `dato`: the date.
- `pos` / `fokus`: a map point.
- `lag`: the map layers the entry switches on.
- `lenke`: a link.

**Caution.** A `bekreftet` label means *the map authors* consider the item confirmed. Several
`bekreftet` items rest on community reports ("meldt av fellesskapet") or on paraphrase with no verbatim
quote. Each entry below carries our own evidence classification.

**Times.** The TAVLE header (innhold.ts:880) says the whiteboard times are stream time:
«Tider er streamtid (trolig 20 sek–1 min forsinket, vi tipper)». So they are probably 20 s to 1 min
behind real time; that is the authors' guess. Git commit times are real time, CEST (+0200). They give an
upper bound on when a piece of evidence first appeared in this repo.

**Our checks.** Our own verification calculations are labelled **[model output: this agent]**. The
scripts are saved in `/home/user/test/evidence/sources/hints_b_checks/`:

| Script | What it checks |
|---|---|
| `sun.py` / `sun2.py` | NOAA solar position, sunrise and solar noon |
| `fly.py` | ADS-B interpolation, distances and elevation angles |
| `line118.py` / `line118b.py` | The 118° line from Bergen |
| `poly.py` | Point-in-polygon tests against the hand-drawn cloud and sun polygons |
| `hist.py` → `hint_hist.txt` | Per-hint git change log for **all** hints, both halves of the array |

---

## 0. Quick index (43 entries)

| # | id | lines | status (source's label) | date | source (`kilde`) | map point |
|---|---|---|---|---|---|---|
| 1 | lydtett | 470–479 | bekreftet | 23.09 | Tavla | layer `solidag` |
| 2 | kamera41 | 480–488 | bekreftet | 23.09 | Tavla («KAMERA 41 ØST») + default.no | – |
| 3 | solmiddag | 489–497 | tolkning | 23.09 | Sun angle on the stream (community) | – |
| 4 | soloppgang | 498–506 | bekreftet | 23.09 | Anja | – |
| 5 | hytter | 507–518 | usikker | 23.09 | Booking calendar, tretopphytter.no | pos [60.9748, 10.9167] |
| 6 | bergen118 | 519–529 | tolkning | 23.09 | Chat | pos [60.3896, 5.3297] |
| 7 | terje | 530–538 | lost | – | Horde app | (fokus 'horde' removed 25.09) |
| 8 | genser | 539–546 | lost | – | Stream | – |
| 9 | morse | 547–554 | lost | – | Stream | – |
| 10 | caesar | 555–563 | lost | 23.09 | Stream | – |
| 11 | dyr | 564–574 | tolkning | 23.09 | Stream | fokus proysen [60.912, 10.8076] |
| 12 | ekorn | 575–583 | bekreftet | – | Horde app | layer teorier |
| 13 | dyreoversikt | 584–593 | tolkning | 25.09 | Compiled by the community 25.09 | layer dn_orrfugl |
| 14 | orrfugl | 594–603 | bekreftet | 25.09 | Horde app (reported by the community) | layer dn_orrfugl |
| 15 | grevling | 604–613 | bekreftet | 25.09 | Horde Rewards (reported by the community) | – |
| 16 | and | 614–622 | bekreftet | – | YouTube _KVnuWlzVsE | – |
| 17 | skilt | 623–631 | tolkning | 23.09 | Stream | – |
| 18 | bjorneparken | 632–641 | tolkning | – | Horde advertising | fokus [60.4343, 9.4493] |
| 19 | ikkeoy | 642–651 | bekreftet | – | Finn.no | fokus notteroy [59.21, 10.42] |
| 20 | spill-dart | 652–661 | bekreftet | 23.09 | Kodejakten source code | – |
| 21 | spill-alle | 662–671 | bekreftet | 23.09 | Kodejakten source code | – |
| 22 | regel-kontor | 672–679 | bekreftet | – | Jaktvettreglene (Horde) | – |
| 23 | regel-jakt | 680–687 | bekreftet | – | Jaktvettreglene (Horde) | – |
| 24 | regel-konvolutt | 688–695 | bekreftet | – | Terms of Hordejakten 2026 | – |
| 25 | regel-anja | 696–703 | bekreftet | – | Hordejakten, «Derfor gjør vi dette» | – |
| 26 | kodejakten | 704–712 | bekreftet | – | horde.no/secret/kodejakten (source code) | – |
| 27 | hohoh | 713–720 | usikker | – | Horde page | – |
| 28 | skyer | 721–730 | tolkning | 21.09 | Tavla (19:00 and 19:50) + Windy | layer skydekke |
| 29 | skyanalyse | 731–741 | usikker | 22.09 | Community | pos [58.7, 8.27] |
| 30 | fly | 742–752 | tolkning | 21.09 | Tavla («FLY») + ADS-B | pos [60.8705, 11.2481] |
| 31 | terreng | 753–762 | bekreftet | 21.09 | Tavla + Børsen interview | layer felt |
| 32 | innlandet | 763–773 | tolkning | 23.09 | Discord and chat + default.no | pos [61.25, 10.95] |
| 33 | rudshogda | 774–784 | tolkning | 23.09 | Community + own searches + default.no | fokus proysenstjerna [60.9115, 10.806] |
| 34 | digeras | 785–795 | usikker | 23.09 | Chat | fokus digeras [61.1788, 11.2639] |
| 35 | sofa | 796–804 | usikker | 23.09 | @Hordeapp in YouTube chat | – |
| 36 | vinduslos | 805–813 | bekreftet | 23.09 | Anja | – |
| 37 | hytte | 814–822 | tolkning | 23.09 | Anja + community | – |
| 38 | video2309 | 823–832 | bekreftet | 23.09 | YouTube 1raIm3ANsAI | – |
| 39 | pluss5 | 833–841 | apen | 23.09 | Stream + Horde video 23.09 | – |
| 40 | koder | 842–850 | apen | 23.09 | App, stream and chat | – |
| 41 | plakat | 851–859 | usikker | 23.09 | Stream | – |
| 42 | hintvideo | 860–869 | bekreftet | 22.09 | YouTube H_-0LbPSu5s | – |
| 43 | tommer | 870–877 | usikker | – | Stream (via default.no) | – |

**Status counts in this half:**

| Status | Count |
|---|---|
| bekreftet | 19 |
| tolkning | 11 |
| usikker | 7 |
| lost | 4 |
| apen | 2 |

**By topic:**

| Topic | Entries |
|---|---|
| Location (weather, sun, flights, terrain, vegetation) | lydtett, kamera41, solmiddag, soloppgang, skyer, skyanalyse, fly, terreng, innlandet, rudshogda, digeras, video2309, hintvideo, tommer, hytter, vinduslos, hytte, bergen118, bjorneparken, ikkeoy, dyr, ekorn, dyreoversikt, orrfugl, grevling, and, skilt |
| Codes and locks | terje, genser, morse, caesar, spill-dart, spill-alle, kodejakten, hohoh, pluss5, koder, plakat |
| Rules | regel-kontor, regel-jakt, regel-konvolutt, regel-anja |
| Chatter | sofa |

---

## 1. Per-entry extraction

Each entry has the same parts:

- **Primary evidence (verbatim)**
- **Evidence class**
- **Interpretation (verbatim + English)**
- **Places / coordinates**
- **Revision history**
- **Verification / issues**, where we checked something

### 1. `lydtett`: «LYDTETT · SOL · VINDSTILLE» (17:49). innhold.ts:470–479

**Status and provenance**
- Status: `bekreftet`. Source: 'Tavla'. Date: 23.09.
- Layer: `solidag`.
- Added in commit df596d3 at 23.09 18:01:37 CEST, 12 minutes after the whiteboard.

**Primary evidence**
- `tekst`: 'Anja skrev kl. 17:49: «LYDTETT», «SOL» og «VINDSTILLE».' In English: Anja wrote at 17:49 "SOUNDPROOF", "SUN" and "CALM".
- Also logged in TAVLE at innhold.ts:917: `{ t: '23.09 17:49', tekst: 'LYDTETT · SOL · VINDSTILLE' }`. That is stream time, so real time is about 17:48–17:49 CEST.
- **Evidence class:** primary_whiteboard.
- Related whiteboards:
  - 21.09 18:44: «KUPERT TERRENG · MYE LYNG · HØRER IKKE MYE FRA BOKSEN» (innhold.ts:885).
  - 24.09: «INGEN LYD I BOKSEN OVERHODET, JEG HAR KUN DERE Å UNDERHOLDE MEG. INGENTING ANNET» (innhold.ts:970).

**Interpretation (`betydning`, verbatim)**

> 'Lydtett forklarer hvorfor hun ikke hører tog, bil eller skyting, og at lyden på streamen ikke kan brukes. Sol kl. 17:49 23.09 betyr at stedet ikke var overskyet på ettermiddagen, som passer med de klare områdene på satellitt (Kongsvinger–Rena). Vindstille gir et nytt værhint: sjekk vind fra værstasjoner kl. 17–18 i kandidatområdene.'

In English:
- The box being soundproof explains why she hears no train, car or shooting, and why the stream audio is unusable.
- Sun at 17:49 on 23.09 means the site was not overcast that afternoon, which fits the clear satellite areas (Kongsvinger–Rena).
- "Calm" is a new weather clue: check station winds at 17–18 in the candidate areas.

**Places:** Kongsvinger–Rena, via the SOL_I_DAG polygon [0] (innhold.ts:1148).

**Issues**
- The step from "box is soundproof" to "stream audio unusable" is a non sequitur. The stream microphone is presumably outside the box, and a soundproof box only limits what *Anja* hears.
- On 25.09 Alf said on TikTok live «Det er ekte lyd på streamen». That was relayed in chat and not checked word for word (see the `tiktok2509` entry, first half).
- Other entries in the file use the "calm at 17:49" test:
  - It is cited in favour of Brumunddal and Lillehammer (FOLK_TROR, innhold.ts:1268, 1280).
  - It is cited against Brauta, where the wind was about 4 m/s (the `haaland-brauta` entry).
  - The wind data for that test is in `public/data/vind.json`, which we did not inspect.

### 2. `kamera41`: camera at 41° (northeast). innhold.ts:480–488

**Status and provenance**
- Status: `bekreftet`. Date: 23.09.
- Source: 'Tavla («KAMERA 41 ØST») + default.no. Takk til default.no.'
- Added in commit 7983773 at 23.09 15:45:19 CEST, so the whiteboard appeared before 15:45 on 23.09.

**Primary evidence**
- TAVLE at innhold.ts:916: `{ t: '23.09', tekst: 'KAMERA 41 ØST' }`. **Class:** primary_whiteboard. No exact time is logged.
- The `tekst` field also contains the community reading: 'Anja skrev «KAMERA 41 ØST». Kameraet står altså nordøst for kassen og filmer mot ca. 221° (sørvest).' The words "står altså nordøst … filmer mot 221°" are interpretation. They assume "41" is a bearing from the box to the camera.

**Interpretation (verbatim)**

> 'Stemmer nesten helt med default.no, som regnet ut kameraretningen fra sola alene (219–220°). Da er sollyset på streamen trolig ekte, og sol-hintene (soloppgang, sola i sør, sol 23.09) blir mer til å stole på.'

In English: this nearly matches default.no's sun-only camera heading (219–220°). So the stream sunlight is probably real, and the sun-based hints become more trustworthy.

**Verification**
- The default.no mirror (`src/data/defaultno_mer.json` → `solbane`) supports it:
  - Window: 21.09 16:20–17:40, 40 points.
  - Best fit: heading 219.6°, pitch 0.2°, f = 1068 px, rms 3.296.
  - Across the latitudes tried, the heading ranges 219.4–219.7°.
- The mk_bevis README (`bevis/claude-2026-09-25/README.md:14`) also uses heading 219.4°.
- 41° + 180° = 221°, which agrees with 219.5° to within about 1.5°. This makes the whiteboard reading consistent with the sun fit. These are two independent sources.

**Issue: magnetic vs true north is unspecified**
- The `retning118` entry (first half) says a compass on Østlandet reads about 4° low ('kompass viser ca. 4° for lite på Østlandet'). On that basis the community corrected the sign bearing from 118° to a true 122–124°.
- They did **not** apply the same correction to "41". If 41 is magnetic, the true bearing to the camera is about 45°, so the view direction is about 225°. That is about 5° off the sun fit.
- The good agreement slightly favours a true-north reading, for example a phone compass, or else an imprecise number.
- History: after commit 4a22327 on 25.09, 'sol i dag' in `betydning` was renamed to 'sol 23.09'.

### 3. `solmiddag`: sun due south at 13:02–13:08 (longitude about 11–12° E). innhold.ts:489–497

**Status and provenance**
- Status: `tolkning`. Source: 'Solvinkel på streamen (fellesskapet)'. Date: 23.09.
- Added in commit 86d52b8 at 23.09 15:22:56.

**Primary evidence**
- The only primary basis is the stream image of the sun. The measurement is a community one: 'Kl. 13:20 sto sola i ca. 184° og 28–31° over horisonten.'
- **Class:** community_observation, a measurement from the stream image. The rest of `tekst` is interpretation:

> 'Da sto den rett i sør ca. kl. 13:02–13:08. Det skjer bare rundt 11–12° øst: Østerdalen, Solør og Trysil. Høyden passer med 59–62° nord.'

**Interpretation (verbatim)**

> 'Peker mot østlige Innlandet. Valdres (13:16), Agder (13:17) og Hardanger (13:28) passer dårlig. Bygger på sollyset i bildet, som noen mener kan være falskt.'

**Verification [model output: this agent, NOAA algorithm]**

Solar noon on 23.09, CEST:

| Longitude | Solar noon |
|---|---|
| 11°E | 13:08.4 |
| 11.5°E | 13:06.4 |
| 12°E | 13:04.4 |
| 9.2°E (Valdres) | 13:15.6 |
| 8.3°E (Agder) | 13:19.2 (the hint's 13:17 implies about 8.8°E) |
| 6.2°E (Hardanger) | 13:27.6 |

Sun position at 13:20 on 23.09:

| Place | Azimuth | Altitude |
|---|---|---|
| Rena | 183.7° | 28.6° |
| Løten | 183.7° | 28.9° |
| Solør (60.6 N, 12.0 E) | 184.5° | 29.1° |
| Trysil | 184.7° | 28.4° |
| Ringsaker | 183.2° | 28.9° |
| Valdres | 181.3° | 28.8° |

These agree with the "184°, 28–31°" measurement.

**Sensitivity [model output]**
- At 13:20 at 61°N, azimuth moves only about 1.14° per degree of longitude:
  - 9°E → 181.0°
  - 10°E → 182.2°
  - 11°E → 183.3°
  - 12°E → 184.5°
  - 12.5°E → 185.0°
- To separate 11–12°E from Valdres needs an azimuth accurate to about ±0.6°. That is tighter than the camera-heading uncertainty: 219.4–221°, or about 225° if "41" is magnetic.
- **This clue is therefore weak.** A 2° error moves the longitude estimate by roughly 1.7°.
- The date of the 13:20 measurement is not given (only 'dato 23.09').

### 4. `soloppgang`: the sun was up before 07. innhold.ts:498–506

**Status and provenance**
- Status: `bekreftet`. Source: 'Anja'. Date: 23.09.
- Added in commit 86d52b8 at 23.09 15:22:56.

**Primary evidence**
- TAVLE at innhold.ts:906: `{ t: '23.09', tekst: 'SOLA VAR OPPE FØR 07' }`, with no exact time. **Class:** primary_whiteboard.
- `tekst`: 'Anja sa at sola var oppe før kl. 07.'
- It is **not stated which morning** she meant (21, 22 or 23.09), or whether she meant the sun disc or daylight.

**Interpretation (verbatim)**

> 'Soloppgang før 07:00 skjer bare øst for ca. 11° øst disse dagene: Solør 06:55, Løten, Rena og Røros 06:57–06:58, Ringsaker 06:59. Valdres (07:06), Agder (07:08) og Hardanger (07:18) er for sent. I skog kommer sola enda senere, så stedet ligger trolig langt øst.'

**Verification [model output: this agent]**

Sunrise in CEST on a flat, sea-level horizon (h0 = −0.833°):

| Place | 21.09 | 22.09 | 23.09 |
|---|---|---|---|
| Solør/Flisa | 06:53:30 | 06:55:50 | 06:58:20 |
| Kongsvinger | 06:53:40 | 06:56:00 | 06:58:20 |
| Løten | 06:56:00 | 06:58:30 | **07:00:50** |
| Rena | 06:55:50 | 06:58:20 | **07:00:50** |
| Røros | 06:55:10 | 06:57:50 | **07:00:30** |
| Brumunddal | 06:57:40 | **07:00:10** | **07:02:30** |
| Rudshøgda | 06:58:10 | **07:00:40** | **07:03:00** |
| Digeråsen | 06:56:10 | 06:58:40 | **07:01:10** |
| Fagernes (Valdres) | 07:04:30 | 07:06:50 | 07:09:20 |
| Froland | 07:07:50 | 07:10:00 | 07:12:10 |
| Evje | 07:11:10 | 07:13:20 | 07:15:30 |
| Norheimsund | 07:17:00 | 07:19:30 | 07:21:50 |

**Findings**
- The hint's figures match **22.09** to within about 1 minute, not 23.09.
- If Anja meant the morning of 23.09, Løten, Rena, Røros and Digeråsen are borderline on a flat horizon (about 07:01). Ringsaker and Rudshøgda fail by 2–3 minutes. Only Solør and Kongsvinger (06:58) pass.
- Elevation and horizon shift sunrise by several minutes either way. From 600 m with an open horizon the sun rises about 6 minutes earlier (Rena 06:54:50); forest or terrain makes it later.
- **Weak, ambiguous clue.** It should not be used as a hard cutoff.

### 5. `hytter`: rented cabins nearby? (Tretopphyttene). innhold.ts:507–518

**Status and provenance**
- Status: `usikker`. Source: 'Bookingkalender på tretopphytter.no'. Date: 23.09.
- pos [60.9748, 10.9167] (this is "Utsiktsredet", Danseråsvegen). Layer: `hytter`.
- Link: https://tretopphytter.no/. Added in 86d52b8 on 23.09 15:22; pos added in 41304dc on 23.09 19:04.

**Primary evidence:** none about the hunt. The booking calendar is community research (community_observation):

> 'Tretopphyttene har 8 hytter i Ringsaker. Bjørkhytta (Danseråsen) er booket sammenhengende fra 23.09 til 11.10. Flere andre er opptatt 24.–27.09.'

**Interpretation (verbatim)**

> 'Trolig ikke relevant. Horde er mer forsiktige med hytter i år, fordi folk fant bookingene sist. Anja har også sagt at hun var et sted uten vinduer og wifi, mens Tretopphyttene har store vinduer og takvinduer. Hyttene ligger som et eget kartlag for sikkerhets skyld.'

**Cabin coordinates** (HYTTER, innhold.ts:1444–1453; occupancy per the booking calendar for 23–27.09):

| Cabin | Place | Position | Occupancy |
|---|---|---|---|
| Bjørkhytta | Danseråsen | [60.9914, 10.8841] | «Opptatt sammenhengende 23.09–11.10» |
| Granhytta | Danseråsen | [60.9902, 10.8866] | 23.09 and 25.09–03.10 |
| Utsiktsredet | Danseråsvegen | [60.9748, 10.9167] | 24–26.09 |
| Himmelhytta | Klufttjernet | [60.9978, 10.8777] | 24–28.09 |
| Furuhytta | Sør-Mesna | [61.0747, 10.8309] | 23–27.09 |
| Forest View | Høgbrennvegen | [60.9811, 10.9401] | 24, 26, 27.09 |
| Lerkhytta | Veldre (approximate) | [60.93, 10.9] | 25–27.09 |
| Klatrehytta | Helgøya | [60.7388, 10.9798] | 25–27.09 |

**Retraction / updates**
- lag.ts:872 says: «Alle er sjekket av en i chatten, uten funn.»
- The first-half `tretopp` entry was retitled «Tretopphyttene i Ringsaker (sjekket, ikke der)» in ce85e10 on 23.09 15:51.
- Whiteboard, 24.09 17:20 (innhold.ts:965): «INGEN HYTTE I NÆRHETEN SOM JEG VET OM ELLER SER».
- **Net: effectively ruled out** (community field check plus Anja's whiteboard).

### 6. `bergen118`: does the Horde sign point 118° from Bergen? innhold.ts:519–529

**Status and provenance**
- Status: `tolkning`. Source: 'Chat'. Date: 23.09.
- pos [60.3896, 5.3297] (Horde AS, Lars Hilles gate 20A, 5008 Bergen). Layer: `retning`.
- Added in cf75140 on 23.09 15:05.

**Primary evidence:** only the sign bearing «ØST CA 118 · RETNING SKILT» (TAVLE innhold.ts:900, time unknown) and «118–120 GR ØST» (innhold.ts:905, 23.09). Everything else is theory (community_interpretation):

> 'Noen har trukket 118°-linja fra Horde AS i Bergen (postnummer 5008) i stedet for fra Oslo. Den går forbi Odda, over søndre Hardangervidda og gjennom Telemark (Vinje, Seljord, Drangedal) til kysten ved Kragerø.'

**Interpretation (verbatim)**

> 'Kobler 5008 og 118° sammen. Linja går ca. 20 km fra Tokke, der kassen stod i 2023. Vestlige del var blå på Windy, men Telemark-delen er fri. Slå på «118°-linja fra Bergen» i modellen for å teste.'

**Verification [model output]:** distance from each place to the 118° geodesic from [60.3896, 5.3297]:

| Place | Distance |
|---|---|
| Odda | 0.8 km |
| Seljord | 3.0 km |
| Bennyøy | 3.2 km |
| Vinje centre | 7.5 km |
| Tokke (Magnus point [59.444, 7.989]) | 19.6 km |
| Drangedal | 21.6 km |
| Kragerø | **32.6 km** |

- The line reaches the coast near about 59.04 N, 9.95 E (Langesund/Porsgrunn–Larvik), **not at Kragerø**.
- A rhumb line gives Kragerø 42 km. Correcting to a true 122° geodesic brings Tokke within 6.8 km and Drangedal within 3.8 km.

**Weight: very low.**
- The sign bearing is a local direction at the box.
- The line crosses areas that the sun clues (solar noon at about 7–9°E) and the flight tracks argue against.
- The sign was removed at 19:12 on 23.09.

### 7. `terje`: code 5008 (Kredittskår + «terje»). innhold.ts:530–538

**Status and provenance**
- Status: `lost`. Source: 'Horde-appen'. No date.
- Layer: `steder`. The original `fokus: 'horde'` was removed in 63416f0 on 25.09 11:07 ("Show only confirmed things on the map by default").
- Added in c0c849b on 23.09 14:30, the repo's first commit, so this was known before then.

**Primary evidence (organizer_app)**

> 'Trykk «Kredittskår», hold fingeren på tallet og skriv «terje». Da kommer «Du fant et hint! 5008».'

**Interpretation (verbatim)**

> '5008 er postnummeret til Horde AS i Bergen (Lars Hilles gate 20A). Det kan også være koden til en av låsene. Butikken i appen selger også «T-skjorte i Terje-modell» (grønn, «Terje lurer ikke meg») til 1 116 897 mynter, samme sum som i kassen, med teksten «de som kjøpte denne sist, økte kredittscoren sin betraktelig. Tilfeldig? Neppe.» Den har ligget der en stund og er selve hintet til å prøve «terje» i Kredittskår.'

**Primary check (image `public/img/app-terje-tskjorte.jpg`, a phone screenshot at 12:22, date not shown)**
- The app item «T-skjorte i Terje-modell», price 1 116 897 (coins).
- Full verbatim description:

> «Terje-tskjorten er endelig tilbake, i limited edition grønn. H-logo på brystet, med "Terje lurer ikke meg". Denne ble svært populær under forrige Hordejakt, og vi ble utsolgt på under et døgn. Det går rykter om at de som kjøpte denne sist, økte kredittscoren sin betraktelig. Tilfeldig? Neppe.»

**Revision (retraction)**
- The separate hint `terje-tskjorte` was added in 7e3690f on 25.09 12:43 as a new 25.09 find.
- It was removed in 2f86bbf on 25.09 13:01 ("The Terje T-shirt is not new: fold it into the «terje» hint") and folded into this entry.

**Codes derived from this entry** (KODER, innhold.ts:1237, 1247, 1248):
- 5008, labelled «hoy» (high).
- Variants 5013 (+5), 0553 (+5 on each digit), 5528 (00 → 52).
- Door variants 50085 and 55285.

### 8. `genser`: numbers on the sweater = GJELDFRI. innhold.ts:539–546

**Status and provenance:** status `lost`. Source: 'Stream'. In the file since c0c849b on 23.09 14:30.

**Primary evidence (primary_stream_visual)**
- '7 10 5 12 / 4 6 18 9 med A=1 gir G J E L / D F R I.'
- The night-camera frame `public/img/tavle-1912-skilt-borte.jpg` (overlay 2026-09-23 19:12:22) partly shows «7 10 !12» / «6 18 9» on the sweater.

**Interpretation:** 'Et kampanjeord. Sier ingenting om stedet.' In English: a campaign word; says nothing about the location.

**Check:** 7=G, 10=J, 5=E, 12=L, 4=D, 6=F, 18=R, 9=I → GJELDFRI ("debt-free"). This matches Horde's campaign URL horde.no/gjeldfri/hordejakten, cited in mkekeoooo KILDER.md.

### 9. `morse`: Morse code on the trousers = PREMIE. innhold.ts:547–554

- Status: `lost`. Source: 'Stream'.
- **Primary:** 'Prikkene og strekene nedover buksa er morse for «PREMIE».' (primary_stream_visual as decoded by the community; we did not verify it.)
- **Interpretation:** 'Et kampanjeord. Sier ingenting om stedet.'

### 10. `caesar`: letters on the trousers (MT WI JO FP YJ …). innhold.ts:555–563

**Status and provenance:** status `lost`. Source: 'Stream'. Date: 23.09.

**Primary evidence** (stream visual; the decoding is a community solution):

> 'Cæsar-chiffer med forskyvning 5: MT WI JO FP YJ S@ MT … blir HO RD EJ AK TE N@ HO … = HORDEJAKTEN@HO…, trolig hordejakten@horde.no (som ville stått MTWIJ.ST på buksa).'

**Interpretation:** 'En minikonkurranse (20 000 Horde-poeng til første løser). Sier ingenting om stedet.'

**Check:** a shift of −5 gives M→H T→O W→R I→D J→E O→J F→A P→K Y→T J→E S→N. "horde.no" shifted +5 is "mtwij.st". Correct.

**Revision:** the original (c0c849b) read only 'HORDEJAKTEN@… (en e-postadresse)'. It was extended in a49eadd on 23.09 15:34.

**Related:** BOKSTAV_LESNINGER at innhold.ts:1364–1369 uses this +5 cipher to read «MINUS HORDE» as "decode with −5". The map authors rate that reading 'sterk' (strong); it is an interpretation.

### 11. `dyr`: fox, squirrel and crow in the box. innhold.ts:564–574

**Status and provenance:** status `tolkning`. Source: 'Stream'. Date: 23.09. fokus 'proysen' = Prøysenstua, Rudshøgda [60.912, 10.8076]. Layers: `steder`, `teorier`.

**Primary evidence (primary_stream_visual, partly)**

> 'Det har kommet en rev, et ekorn og en kråke inn i boksen. 23.09 ble det satt en rev inn i buret.'

In English: a fox, a squirrel and a crow have come into the box; on 23.09 a fox was put into the cage.

- The fox plush is visible in `public/img/tavle-laser.jpg`.
- TAVLE at innhold.ts:904 (23.09): «REVEN HETER BENNY».
- **Issue:** the squirrel and crow "in the box" are not corroborated anywhere else in the file. The 25.09 overview (`dyreoversikt`) sources the squirrel to the app's referral screen, not the box, and does not list a crow at all. The claim dates from the first commit (c0c849b on 23.09 14:30). **Treat "squirrel and crow in the box" as unverified.**

**Interpretation (verbatim, current)**

> 'Rev, kråke og ekorn er alle med i Alf Prøysens «Sirkus Mikkelikski» (Mikkel Rev, Frøken Kråke og ekornet Nøtteliten). Det peker mot Prøysen og Rudshøgda i Ringsaker. Kan også være «What does the fox say» (Ylvis).'

**Revisions**
- c0c849b: 'Kan peke på «What does the fox say» (Ylvis) eller «Reven og kråka» (Alf Prøysen fra Ringsaker). I visa er ostebiten det tredje elementet. Froland har ekorn i kommunevåpenet.'
- 58e737c on 23.09 14:59: added 'nabo til Hamar og Løten'.
- aa81ebf on 23.09 17:56: replaced by the Sirkus Mikkelikski reading. The Froland coat-of-arms remark was dropped.

**Caution:** the Kodejakten figure named "Alf" is Horde's man, not Alf Prøysen (the `kodejakten` entry says so explicitly).

### 12. `ekorn`: «Verv en venn» → «Hint-hint» with a squirrel. innhold.ts:575–583

**Status and provenance:** status `bekreftet`. Source: 'Horde-appen'. Layer: `teorier`. In the file since the first commit.

**Primary evidence (organizer_app)**

> 'Trykk «Verv en venn» i appen. På slutten dukker det opp «Hint-hint» med bilde av et ekorn.'

**Interpretation (verbatim)**

> 'Ekorn finnes over hele landet, så det kan bare bety at det er ekorn der kassen står. Ekornet går likevel igjen i flere teorier (Froland, Lillehammer, Tretopphyttene, ordspill på «nøtt»). Ekorn ble også jaktet og solgt som kjøtt og pels i Innlandet, av romanifolk (tatere) og fattige bønder. Det knytter ekornet til både «jakten» og Innlandet.'

**Revisions**
- 85d9ded on 23.09 15:17 added the Innlandet hunting link.
- 9ea67b3 on 23.09 15:23, "Weaken the squirrel clue", added the opening caveat.

**Related (not in this half)**
- `frolandekorn`: an **unverified** screenshot showing FROLAND → «Ekornet kan klatre». It was downgraded from bekreftet to usikker in 893318a on 24.09 19:55.
- Lillehammer's 2026 squirrel mascot "Lille" (TEORIER, innhold.ts:1138).
- Places: Froland [58.53, 8.63] (ruled out); Lillehammer [61.115, 10.466]; Tretopphyttene [60.9748, 10.9167].

### 13. `dyreoversikt`: the animal hints so far. innhold.ts:584–593

**Status and provenance:** status `tolkning`. Source: 'Samlet av fellesskapet 25.09'. Date: 25.09. Layer: `dn_orrfugl`.

**Primary evidence as compiled** (a mix of organizer_app, organizer_media and stream_visual):

> 'Ekorn: «Hint-hint» med ekorn i vervemenyen i appen. Stokkand: ett bilde i den første promovideoen. Rev: revebamsen i boksen. Orrfugl: orrfuglleik-lyd når man rister appen. Grevling eller vaskebjørn: et utstoppet dyr som støtter opp olivenolja i Horde Rewards. Det ligner Erling Haalands vaskebjørn fra Texas.'

**Interpretation (verbatim)**

> 'Alle fem finnes vanlig i skogen på Østlandet, så hvert dyr alene sier lite. Orrfuglen er mest stedbundet: orrfuglen leker på myrer og i åpen skog i høyden, ofte rundt 600–900 moh i Innlandet, og det passer med 810–891 moh. Slå på «default.no: orrfugl» for å se hvor orrfugl er observert. Alf sa på TikTok-live 25.09 at reven og anda «kanskje» har med hint å gjøre.'

**Notes**
- The 810–891 moh figure comes from the `eiffel` hint (first half): Horde AI answers «2,7 eiffeltårn stablet oppå hverandre» to «Hordeminus», and 2.7 × 300 or 330 m = 810 or 891 m. That height is an interpretation.
- The Alf quote is an organizer statement relayed through chat. The `tiktok2509` entry is marked «gjengitt i chatten (ikke sjekket ordrett)».
- **Revision:** 67eb8d0 on 25.09 11:01 changed "grevling" to "grevling eller vaskebjørn", adding the Haaland raccoon reading.

### 14. `orrfugl`: black-grouse lek sound when shaking the app. innhold.ts:594–603

**Status and provenance:** status `bekreftet`. Source: 'Horde-appen (meldt av fellesskapet)'. Date: 25.09. Layer: `dn_orrfugl`.

**Primary evidence** (organizer_app, reported by the community; not stated that the authors verified it themselves):

> 'Rister man telefonen med Horde-appen åpen, spilles lyden av orrfugl som leker (spiller).'

**Interpretation:** 'Orrfuglen leker på myrer, islagte vann og i glissen skog, ofte i høyden. Kan peke mot fjellskog og myrer, for eksempel rundt 810–891 moh. Se kartlaget «default.no: orrfugl».'

**Related:** the lag.ts:401–404 layer 'dn_orrfugl' is titled 'Orrfugl, lyden 24.09 kan være spill'. That suggests default.no's BirdNET run may have heard a black grouse on the stream on 24.09, which we have not verified.

### 15. `grevling`: stuffed animal in Horde Rewards, badger or Haaland's raccoon? innhold.ts:604–613

**Status and provenance:** status `bekreftet` (the object exists; its identity is disputed). Source: 'Horde Rewards i appen (meldt av fellesskapet)'. Date: 25.09.

**Primary evidence (organizer_app, reported by the community)**

> 'I Horde Rewards står et utstoppet dyr og støtter opp en flaske olivenolje. Det har blitt kalt en grevling, men fellesskapet mener det ligner veldig på den utstoppede vaskebjørnen Erling Haaland kjøpte.'

**Interpretation (verbatim)**

> 'Under fotball-VM 2026 kjøpte Haaland en utstoppet vaskebjørn på Wild Bill\'s Western Store i Dallas, Texas, og bar den gjennom Gardermoen (Nettavisen). Er dyret en vaskebjørn, kan det være et nikk til Haaland eller til Texas, og da henger det sammen med «Eiffeltårnet i Texas»-teorien (Texas og Kompassen i Våler). Er det en grevling, lever den mest i lavlandet og sjelden høyt til fjells. Uklart hva som stemmer.'

Link: https://www.nettavisen.no/sport/utsolgt-for-utstoppet-vaskebjorn-etter-haaland-besok/s/5-95-3148456

**Places**
- «Texas», Våler i Solør [60.87812, 12.21229], about 348 moh.
- «Kompassen», Våler [60.87639, 12.31426], about 302 moh.
- Brauta, Ringebu [61.43659, 10.1854], about 190 moh (from the `haaland-brauta` entry; STEDER at innhold.ts:1068).

**Revision**
- 10c2793 on 25.09 11:00 added it as 'Utstoppet grevling i Horde Rewards'.
- 67eb8d0 on 25.09 11:01 changed it to the grevling/vaskebjørn question.

**Related retraction**
- The `hordeai-grevling` hint was added in 996369d on 25.09 14:29. It reported Horde AI saying «1 Hordeminus = 3,4 grevlinger».
- It was **removed** in 337ddc2 on 25.09 14:56: «it was not repeatable in a new chat».

**Cross-source: mkekeoooo PRESISERINGER.md, "Appvaren med olivenolje"**
- Two third-party product screenshots (praktiskinfo.no/hordejakten-2026) show:
  - the animal is **a badger** («grevling»);
  - the item name is «Olivenoljestativ»;
  - the price is 100 000 points;
  - the shipping text is «**Nesten Helt Hjem**».
- These screenshots were not checked directly in the app.
- An earlier mention of a beaver (bever) in that archive was corrected there.
- «Nesten Helt Hjem» echoes the "nesten hjemme" / Brumunddal tip in FOLK_TROR at innhold.ts:1279–1283 (commit 4dd298c).

### 16. `and`: a mallard in the first promo video (one frame). innhold.ts:614–622

**Status and provenance:** status `bekreftet`. Source: 'YouTube _KVnuWlzVsE'. Link: https://www.youtube.com/watch?v=_KVnuWlzVsE&t=13s.

**Primary evidence (organizer_media)**

> 'En and dukker opp i ett enkelt bilde helt nederst til høyre, ca. 00:15, mens Anja står på hendene.'

The species ("stokkand", mallard) is the community's identification.

**Interpretation:** 'Enda et dyr i rekken: ekorn, stokkand, rev, orrfugl og grevling. Se «Dyrehintene så langt».'

**Revision:** 10c2793 on 25.09 11:00 changed the title from 'En and i YouTube-video (ett bilde)' to 'En stokkand i den første promovideoen (ett bilde)'. The earlier betydning was 'Enda et dyr i rekken rev, ekorn, kråke og and.'

**Organizer comment** (second-hand, `tiktok2509`): «Har reven og anda noe med hint å gjøre? Ja, kanskje.»

**Related:** the Kroktjennet/Hemmeldalen theory cites the nature-reserve regulations mentioning ande- og vadefugler (FOLK_TROR, innhold.ts:1317–1320).

### 17. `skilt`: the Horde sign and the hands. innhold.ts:623–631

**Status and provenance:** status `tolkning`, raised from `usikker` in bdffb03 on 23.09 15:15. Source: 'Stream'. Date: 23.09.

**Primary evidence (primary_stream_visual + primary_whiteboard)**

> 'Foran kassen står et «Horde»-skilt båret av to hender. Det peker mot venstre i bildet, og Anja har bekreftet at det peker ca. 118° øst-sørøst.'

Whiteboards:
- innhold.ts:900, time unknown: «ØST CA 118 · RETNING SKILT».
- innhold.ts:905, 23.09: «118–120 GR ØST».
- innhold.ts:930, 23.09 19:12: «SKILTET ER BORTE · VET IKKE HVOR». The photo `tavle-1912-skilt-borte.jpg` has the overlay 2026-09-23 19:12:22; it reads «SKILTET ER BORTE[,] VET IKKE HVOR».

**Interpretation (verbatim)**

> 'Skiltet står vest-nordvest for kassen og peker mot den, så det viser veien inn. Håndsymbolene er ikke løst, og hendene ser ut til å ha endret stilling i løpet av 23.09, så de kan være et hint som oppdateres. To teorier fra Discord: fingrene er romertall (den første viser VII = 7), eller binærtall der hver finger opp er 1. Begge kan gi sifre til en kode. Skiltet ble fjernet kl. 19:12 den 23.09.'

**Revisions (the direction logic flipped several times)**
1. c0c849b: 'peker mot venstre i bildet'; 'Kameraet ser mot sørvest, så venstre i bildet er omtrent sørøst.'
2. 58e737c: 'samme vei som parkeringen (118°). Skiltet kan altså vise veien inn.'
3. 4e26d93 (23.09 14:59) added the Roman-numeral and binary theories. cf75140 added 'hendene ser ut til å ha endret stilling'.
4. bdffb03 (15:15): the direction was confirmed by Anja and the status raised to tolkning.
5. 86d52b8 (15:22): 'Skiltet står vest-nordvest for kassen og peker mot den'. This comes from the community sketch.
6. 405c497 (19:15): added 'Skiltet ble fjernet kl. 19:12 den 23.09.'

**Contradiction (unresolved in the file)**
- On 24.09 the `komfra` hint recorded the whiteboard «KOM FRA DEN VEIEN ← · INGEN STIER» (innhold.ts:960), with the arrow pointing left in the image, which is about 130° (SE).
- From that it concluded the car and road are **southeast** of the box, and one walks about 300° (NW) from the car. `komfra` itself says 'Merk at dette snur den gamle tolkningen'.
- The `skilt` betydning ("sign stands WNW of the box, points to it, shows the way in") was **not** updated. It implies an approach from the WNW, which conflicts with `komfra`.

**Later developments (first-half entries)**
- `skilt-tilbake` (usikker, 25.09): a wooden arrow sign reading «HORDE» appears to the right of the box, pointing left, in the 25.09 16:20–17:03 balloon video (https://default.no/cuts/202609251620_202609251703.mp4). Image `stream-2509-skilt-tilbake.jpg` confirms a wooden «HORDE» arrow at the right of the frame.
- `hand-tilbake` (25.09): one open hand is back in the heather in front of the box (`stream-2509-hand.jpg`).

**Geometry:** with the camera looking at about 221°, "left in the image" is about 131°. That is consistent with 118–120°, allowing for a possible magnetic offset of about 4°.

### 18. `bjorneparken`: advertising colours resemble Bjørneparken. innhold.ts:632–641

- Status: `tolkning`. Source: 'Horde-reklame'. fokus Bjørneparken, Flå [60.4343, 9.4493]. Layer: `steder`.
- **Primary:** Horde's advertising, with a community colour comparison:

> 'Magenta og lysegrønt i Hordes reklame er nesten identisk med logoen og parkkartet til Bjørneparken i Flå.'

- **Interpretation:** 'En mulig pekepinn mot Flå og Hallingdal.'
- **Weight: very low.** Nothing corroborates it. Flå (9.45°E) conflicts with the sun clues and the flight tracks. It is unchanged since the first commit.

### 19. `ikkeoy`: Finn.no ad «Ikke en øy». innhold.ts:642–651

- Status: `bekreftet`. Source: 'Finn.no'. fokus notteroy = Nøtterøy [59.21, 10.42], marked `utelukket` (ruled out). Layer: `teorier`.
- **Primary:** 'En annonse på Finn.no har løsningen «Ikke en øy».'
  - Class: organizer_media, presumed. The file does not say the ad is Horde's, and no ad URL is given.
- **Interpretation:** 'Kassen står ikke på en øy. Det stemmer med «INGEN FERGE» på tavla og taler mot Nøtterøy-teorien.'
- TAVLE at innhold.ts:883 (21.09 18:36): «INGEN FERGE · KUN BIL · VET IKKE ANG. TUNELLER».
- SIKRE_FAKTA at innhold.ts:1457: 'Kassen står i Norge, ikke på en øy og ikke i farlig terreng.'
- Related: Bennyøy (a holm in Nome [59.2666, 9.1327]) is undermined by this entry.

### 20. `spill-dart`: Kodejakten game 4, how to solve the dartboard. innhold.ts:652–661

- Status: `bekreftet`. Source: 'Kildekoden til Kodejakten'. Date: 23.09. Link: https://horde.no/secret/kodejakten. Added in 41304dc on 23.09 19:04.
- **Primary (organizer web app source code, read by the community):**

> 'Fargene betyr: blå = pluss, gul = minus, rosa = gange, lilla = dele (lånt fra spillet Blue Prince). Start med tallet i midten, og gå utover én ring om gangen. Hvert farget felt peker på et tall (1–20) langs kanten, som brukes med ringens regnetegn. Svaret er alltid mellom 1 og 999.'

- **Interpretation / rules:** 'Du må ha fire riktige skiver på rad. Svarer du feil, får du en ny skive og starter på null. Gjelder når Horde skrur på serveren.'

### 21. `spill-alle`: Kodejakten, the four games. innhold.ts:662–671

- Status: `bekreftet`. Source: 'Kildekoden til Kodejakten'. Date: 23.09. Link as above.
- **Primary (source code):**

> '1) Kill the Bill: hold fingeren på skjermen for å flytte og skyte. Nivåer: Regningsbunken, Purringene og bossen Hovedkravet (1 116 897). 2) Bill Runner: tapp for å hoppe over regningene fram til kassen. 3) Flappy-Alf: tapp for å flakse gjennom regningsbunkene, åpningene blir mindre. 4) Dartskiven. Fremgangen lagres, så du kan ta pauser.'

- **Interpretation:** 'Alle fire må klares i én økt. Da viser siden «Låsen er åpen: dette er koden til den ene hengelåsen på kassen». Hjelpeknappen sier bare «Tips: Vær bedre».'

### 22. `regel-kontor`: Horde says nobody at the office knows where the box is. innhold.ts:672–679

- Status: `bekreftet`. Source: 'Jaktvettreglene (Horde)'.
- **Primary (organizer_statement, verbatim):**

> «Ingen på Hordekontoret vet hvor kassen befinner seg. Det er kun de som er på stedet med Anja som vet noe. De får du ikke tak i.»

- **Interpretation:** 'Det nytter ikke å spørre Horde-ansatte. Hint om stedet kommer via appen, streamen og Anja.'

### 23. `regel-jakt`: «Ikke kle deg ut som elg, hjort eller storfugl». innhold.ts:680–687

- Status: `bekreftet`. Source: 'Jaktvettreglene (Horde)'.
- **Primary (organizer_statement):** «Ikke kle deg ut som elg, hjort eller storfugl. Det er jaktsesong.»
- **Interpretation (verbatim):**

> 'Kassen står i skog der det jaktes. I Ringsaker er skogsfugljakta åpen 14.–24.09, og elgjakta starter fredag 25.09. Bruk synlige klær (oransje eller refleks).'

- The Ringsaker dates are a community claim that we did not verify. Nationally, forest-grouse hunting normally opens on 10.09, so "14.–24.09" may describe a local or state-land rule.
- The rule itself is generic safety text. "The box is in hunted forest" is inference.
- Alf on TikTok, 25.09 (second-hand): 'Husk at det er jaktsesong, og gå i tydelige klær.' (innhold.ts:1635).
- SISTE_NYTT at innhold.ts:1486–1488: 11 moose collisions in one hour around Elverum, reported in chat.

### 24. `regel-konvolutt`: the terms, an envelope in the box and no cash. innhold.ts:688–695

- Status: `bekreftet`. Source: 'Vilkår for Hordejakten 2026'.
- **Primary (organizer_statement; paraphrase with a quoted fragment):**

> 'For å vinne må du låse opp alle låsene med kodene fra appen og «følge instruksjonene du finner i konvolutten i kassen». Boksen inneholder ikke fysiske kontanter. Flere kan finne kassen samtidig: Horde har et køsystem der man prøver kodelåsene etter tur.'

- **Interpretation:** 'Premien utbetales via bankoverføring. Den som først åpner alle låsene, vinner. Å komme først fram garanterer ikke seier.'
- Related:
  - `regel-ko` (first half, bekreftet since 094b3b8 on 25.09 11:16): queue plus a 5-hour quarantine if you fail the locks (Alf on TikTok live, 25.09).
  - The phrase «kodene fra appen» matches Horde's comment «Hint til hva kodene kan være ligger i appen 💙» (the `kodeniappen` entry).

### 25. `regel-anja`: «Anja er på publikums lag». innhold.ts:696–703

- Status: `bekreftet`. Source: 'Hordejakten, «Derfor gjør vi dette»'.
- **Primary (organizer_statement, verbatim):**

> «Anja kan kommunisere med omverdenen fra første minutt, om enn litt kryptisk i starten. Hun får etterhvert flere hjelpemidler å kommunisere med. Anja er på publikums lag. Hun har ikke fått noen føringer fra Horde om hva hun kan, eller ikke kan si.»

- **Interpretation:** 'Tavla er den viktigste kilden: Anja svarer ærlig på det hun ser og hører. Stem inn nye hjelpemidler i appen, det gir henne flere måter å fortelle på.'
- Related whiteboard, 24.09 (innhold.ts:940): «HJELPER VELDIG AT JEG KAN SE DET DERE SKRIVER <3». She reads the chat.

### 26. `kodejakten`: four games give the code to one padlock. innhold.ts:704–712

- Status: `bekreftet`, raised from `apen` in 125f83f on 23.09 18:01. Source: 'horde.no/secret/kodejakten (kildekoden)'. Link: https://horde.no/secret/kodejakten.
- **Primary (organizer web app, read by the community):**

> 'Fire spill: «Kill the Bill» (skyt regninger), «Bill Runner» (hopp over regninger), «Flappy-Alf» og «Dartskiven». Figuren heter Alf, med ansiktet til Horde-mannen fra videoen, ikke Alf Prøysen. Når alle fire er klart, viser siden «Låsen er åpen: Dette er koden til den ene hengelåsen på kassen.» Koden ligger ikke i nettsiden, serveren gir den først når alle fire er godkjent.'

- **Community observation / interpretation:**

> 'Serveren som gir koden er ikke skrudd på ennå: alle API-kall (start/verify) svarer «not_configured» (503) per 23.09. Ingen kan altså få en kode fra Kodejakten nå, uansett. Når den åpner: gir én av kodene, ikke et sted. …Hjelpeteksten er bare «Tips: Vær bedre».'

- **Revisions**
  - The first-commit text said 'skal gi en firesifret kode til en av låsene'.
  - 125f83f: source-code findings.
  - b7a2c7f on 23.09 18:17: the server is not live (503 not_configured).
- **Open:** whether the backend was switched on after 23.09 is not recorded in this file as of 25.09 21:04.

### 27. `hohoh`: «Ho Ho Hint Hint», 072 and 500. innhold.ts:713–720

- Status: `usikker`. Source: 'Horde-side' (unspecified page).
- **Primary (organizer page, paraphrased):** '072 er de siste sifrene i premien fra 2024 (1 093 072 kr). 500 er poengene man får for å verve.'
- **Interpretation:** 'Uklart om dette gjelder 2026-jakten.'
- These are 3-digit values, so they do not fit the 4- or 5-digit locks. KODER at innhold.ts:1251–1252 rates them «lav» (low).

### 28. `skyer`: clear sky, everything blue on Windy is ruled out. innhold.ts:721–730

- Status: `tolkning`. Source: 'Tavla (19:00 og 19:50) + Windy'. Date: 21.09. Layer: `skydekke`.
- **Primary (primary_whiteboard):**
  - innhold.ts:888, 21.09 19:00: «INGEN SKYER NÅ · SNART SOLNEDGANG».
  - innhold.ts:893, 21.09 19:50: «KLAR HIMMEL».
- **Community data:** the Windy screenshot:

> 'På Windy-kartet for samme periode er hele Vestlandet, Sørlandskysten, Trøndelag og et bånd fra Lillehammer mot Sverige blått.'

- **Interpretation:** 'Blå områder er utelukket. Det tar ut Vestlandet, også Norheimsund. Østlandet, Agder-innlandet og mesteparten av Innlandet er fortsatt med.'

**Polygons:** SKYDEKKE at innhold.ts:1188–1191, «Tegnet for hånd ut fra skjermbildet … (feil under ca. 10 km)».
- [0] covers Vestlandet, the Sørland coast and Trøndelag.
- [1] is the band from Lillehammer toward Sweden, «mest usikkert».

**Certainty upgrade (flag)**
- The original betydning (c0c849b) was: 'Skyede områder er mindre sannsynlige. **Tidspunktet for skjermbildet er ukjent, så sonen er grovt tegnet.**'
- In 520fd05 on 23.09 14:49 it became 'Blå områder er utelukket'. The caveat about the unknown screenshot time was dropped, and no new evidence is cited.

**Internal contradiction [model output: this agent, point-in-polygon]**
- The following fall **inside** band [1]:
  - Koppang [61.5716, 11.0433], default.no's nr. 3 on 22.09;
  - Gålaveien [61.4725, 10.9677], a default.no terrain hit;
  - Sjusjøen [61.18, 10.72];
  - Lillehammer.
- Other points are just outside it:
  - FLY_PUNKT2 of NOZ9EG, about 4 km;
  - Jomfrua, about 4 km;
  - Kroktjennet, about 7 km;
  - the `innlandet` pos, about 4.5 km;
  - Madsskardveien, about 0.3 km.
- The same file treats Sjusjøen and Ringsakfjellet as live candidates (`fly`, `fjellmark`, `utelukkingskart`). Either the band is wrong or the file's own "blue = ruled out" rule is not applied consistently.

**Revision:** in 520fd05 the tekst changed from 'tett skydekke langs kysten fra Stad til Trøndelag' to the current wording.

### 29. `skyanalyse`: the cloud-analysis map (red, green, pink and blue). innhold.ts:731–741

- Status: `usikker`. Source: 'Fellesskapet'. Date: 22.09. pos [58.7, 8.27]. Layer: `skyanalyse`.
- **Community model (community_interpretation):**

> 'Et kart basert på når Anja sa det var skyet, og når det gikk fly over henne. Rødt er kl. 12, grønt kl. 19–20 og rosa kl. 15–17 (22.09). Hvitt er fly sett, og blått er møtepunktet i Agder.'

- **Interpretation:** 'Peker mot indre Agder (Birkenes og Froland). Derfra er det bare ca. 4 t å kjøre fra Oslo, som strider mot 7 t i bilen. Ikke bekreftet.'
- SKYANALYSE at innhold.ts:1181: centre [58.7, 8.27], inner ring 12 km, outer ring 45 km. «Møtepunktet er lest av bildet, ±15 km».
- **Superseded / effectively retracted by later entries:**
  - `froland` (6cddb71, 23.09 15:46): Froland ruled out because the weather does not match. It was raining in Froland on the evening of 23.09 but not on the stream (01ab80d).
  - The Agder sun clues fail: sunrise about 07:08–07:15, solar noon about 13:17–13:19.
  - The "7 h in the car" premise was itself downgraded ('Kjøretiden er ikke et fakta', `reise` entry).
- Unchanged since the first commit apart from gaining a pos in 41304dc.

### 30. `fly`: planes seen and heard at 21:30. innhold.ts:742–752

- Status: `tolkning`. Date: 21.09. pos [60.8705, 11.2481]. Layer: `fly`.
- Source: 'Tavla («FLY») + ADS-B (adsb.lol via default.no). Takk til default.no.'

**Primary**
- TAVLE at innhold.ts:894: `{ t: '21.09 21:30', tekst: 'FLY (pekte opp, litt mot sørøst)' }`. **Class:** primary_whiteboard plus primary_stream_visual (the gesture).
- default.no's timeline (`defaultno_mer.json` → observasjoner.fly[0]) says: «Hun peker opp 21:29:38, skriver «FLY» 21:30:12, og lyden er sterkest 21:33:20.» These are stream times.

**The `tekst` field (verbatim; the flight IDs are a community observation from ADS-B):**

> 'Anja pekte rett opp kl. 21:29:38 og skrev «FLY» kl. 21:30 (streamtid). To fly var nær: NOZ56U nordover over Hamar, like ved Løten (ca. 24 000 fot), og NOZ9EG sørover over Ringsakfjellet ved Sjusjøen (ca. 23 500 fot). NOZ9EG passerte ca. 3 km fra Tretopphyttene kl. 21:31.'

**Interpretation (verbatim)**

> 'Kassen står trolig under ett av de to sporene: Løten–Elverum eller Ringsaker (Sjusjøen–Brumunddal). Fellesskapet: «Eneste stedene det er sol i Norge nå + eneste stedene det fløy fly over hodet hennes 21:29.» Streamen er trolig 20 sek–1 min forsinket (vi tipper).'

**Data**

`public/data/fly_2130.json` (ADS-B from adsb.lol, extracted by default.no; real time 21.09, CEST):

| Aircraft | Time | Lat | Lon | Altitude (ft) |
|---|---|---|---|---|
| NOZ56U B738 | 21:28:14 | 60.7137 | 11.2168 | 19 325 |
| NOZ56U B738 | 21:29:48 | 60.8671 | 11.2475 | 23 825 |
| NOZ56U B738 | 21:31:16 | 61.0157 | 11.2778 | 26 800 |
| NOZ56U B738 | 21:32:50 | 61.1823 | 11.3122 | 29 600 |
| NOZ56U B738 | 21:34:17 | 61.3382 | 11.3437 | 32 675 |
| NOZ9EG B738 | 21:28:14 | 61.3538 | 10.9068 | 25 775 |
| NOZ9EG B738 | 21:29:48 | 61.1425 | 10.8901 | 22 275 |
| NOZ9EG B738 | 21:31:16 | 60.9573 | 10.8753 | 18 850 |
| NOZ9EG B738 | 21:32:50 | 60.7670 | 10.8400 | 14 450 |
| NOZ9EG B738 | 21:34:17 | 60.5951 | 10.8107 | 10 750 |

- In default.no's `public/data/defaultno/flyhendelser.json`, NOZ56U is OSL–BOO. The southbound B738 has callsign **"@@@@@@@@"** and route null. So the "NOZ9EG" label is not in default.no's record; its origin in the map data is unclear.
- That event window (21:28:40–21:34:00) holds n = 69 aircraft. An earlier version of this hint said '49 fly var i lufta'.
- FLY_PUNKT at innhold.ts:1168: [60.8705, 11.2481], NOZ56U, 23 892 ft, «Der NOZ56U var da Anja skrev «FLY» (ekte tid ca. 21:29:50)».
- FLY_PUNKT2 at innhold.ts:1178: [61.216, 10.896], NOZ9EG, 23 500 ft, «ca. 21:29:15».

**Verification [model output: this agent]**
- NOZ9EG's closest approach to Tretopphyttene (Utsiktsredet [60.9748, 10.9167]) is 2.2 km at 21:31:07. That confirms "about 3 km at 21:31".
- At the pointing time, NOZ56U was:
  - with a 45 s delay (21:28:53 real): at 60.7773, 11.2295, 21 192 ft;
  - with a 20 s delay (21:29:18): at 60.8181, 11.2377;
  - with a 60 s delay (21:28:38): at 60.7529, 11.2246.

**Retraction / downgrade**
- Until 01ab80d (25.09 11:29), the betydning said 'Streamen er 45 sek forsinket (bekreftet)'.
- It now says 'trolig 20 sek–1 min forsinket (vi tipper)'. The "confirmed" 45 s was withdrawn.
- `STREAM.forsinkelseSek = 45` is still hard-coded at innhold.ts:10.
- FAKTA at innhold.ts:1197 now says '20 s–1 min … (vi tipper)'.

**Internal inconsistencies**
- The file mixes delay assumptions:
  - `digeras` and TEORIER use pointing at 21:28:53 real (45 s delay).
  - FLY_PUNKT uses writing at about 21:29:50 real, which is about a 22 s delay.
  - The Tretopp TEORIER text 'NOZ56U var ca. 21 km unna (19°) da Anja pekte opp' matches 21:29:50, not 21:28:53. At 21:28:53 it is 27.7 km and 13°.
- «rett opp» in `tekst` vs «pekte opp, litt mot sørøst» in TAVLE.

**Revisions**
- c0c849b: 'Beste treff i flydataene er NOZ56U fra Oslo til Bodø, i stigning'.
- ecf0260: '49 fly … over Løten'.
- e72a665 (23.09 15:41): second plane NOZ9EG added.
- a141dae (24.09 19:59): 'over Løten' became 'over Hamar, like ved Løten' after a Kartverket place-name check.

**Related (first half):** `fly2509`. On 25.09 at 17:22 stream time, Anja pointed up again while SAS50J (A320neo, OSL northbound) was over eastern Stange/Romedal/Løten at 21 000–23 000 ft, about 23 km east of NOZ56U's track. SAS364 was over Rena. Track at innhold.ts:1639–1642; images `fr24-2509-*.jpg`.

### 31. `terreng`: hilly terrain, heather, four large stones. innhold.ts:753–762

- Status: `bekreftet`. Source: 'Tavla + Børsen-intervju'. Date: 21.09. Layer: `felt`.

**Primary (primary_whiteboard + news_interview)**
- Whiteboards:
  - innhold.ts:882, 21.09 18:31: «INGEN FLY · INGEN SKYTING · OSLO, SØN KL 04.00 · CA 5–10 MIN Å GÅ FRA BIL».
  - innhold.ts:884, 18:38: «TROR DET VAR OPPOVER · SISTE 5–10 MIN».
  - innhold.ts:885, 18:44: «KUPERT TERRENG · MYE LYNG · HØRER IKKE MYE FRA BOKSEN».
  - innhold.ts:887, 18:57: «PRESENNING · MER ÅPEN SKOG TIL HØYRE FOR MEG».
  - innhold.ts:891, 19:38: «4 STORE STEINER, KUN STEIN DER».
- Børsen interview: https://borsen.dagbladet.no/nyheter/anja-29-snakker-ut-absurd/85185489 (URL from the `reise` entry).

**The `tekst` field (verbatim)**

> 'Ca. 5–10 min fra bilen, oppover. På siste etappe hadde hun sovemaske og headset og ble båret inn i skogen. Kupert terreng, mye lyng og furuskog. Fire store steiner, en presenning og mer åpen skog til høyre for henne.'

"furuskog" (pine forest) is not in any whiteboard text. It probably comes from video impressions.

**Interpretation (verbatim)**

> 'Hun hører ikke tog, bil eller skyting, og det var dugg på taket av kassen 07:00–09:40 (klar, fuktig natt). Hun ble båret, så avstanden er hennes følelse. Leter du i felt: 300–900 m fra en skogsbilvei, oppover, på lyngdekt furumo.'

**Revisions**
- The search band changed from 400–800 m to 300–900 m in 520fd05.
- The source changed from 'Tavla' to 'Tavla + Børsen-intervju', and the sleep-mask detail was added.
- The dew remark was added in fe51e10 (23.09 15:55, "clues from default.no"). The date of the dew is not given.

**Tension**
- The whiteboard says «Å GÅ» (to walk), but Børsen says she was carried.
- The later «GIKK 2 MIN INN I SKOGEN» (`gikk2min`) is read as the walk to a break location.
- Alf (TikTok, 25.09, second-hand): 'Man må kanskje gå litt, men aldri noe farlig, som å krysse en elv.'
- "Til høyre for meg" (to my right) depends on which way she was facing, which is unknown.

### 32. `innlandet`: the community is now sure it is Innlandet. innhold.ts:763–773

- Status: `tolkning`. Source: 'Discord og chat + default.no. Takk til default.no.' Date: 23.09. pos [61.25, 10.95]. Layer: `innlandet`.
- **Community consensus (community_interpretation):**

> 'De fleste som leter peker nå mot Innlandet: flyet over Hamar/Løten, klar himmel på Østlandet, furumo og tømmerdrift, og default.no sin topp-kandidat i Rena/Åmot. Fra chatten: «Det er null tvil, været, sola, skogen og alt.»'

- **Interpretation:** 'Innlandet er egen teori og eget kartlag. Velg «Innlandet» i modellen for å se de beste rutene der.'
- **Revisions**
  - Added in 520fd05 on 23.09 14:49.
  - The chat quote was added in 45200c5.
  - 'Løten' became 'Hamar/Løten' in a141dae.
  - The default.no credit was added in e4f04b5.
- Popularity is not evidence. mkekeoooo PRESISERINGER notes that shared coordinates can stem from the same model or website.

### 33. `rudshogda`: the Prøysen theory, Rudshøgda. innhold.ts:774–784

- Status: `tolkning`. Source: 'Fellesskapet + egne søk + default.no. Takk til default.no.' Date: 23.09.
- fokus Prøysenstjerna [60.9115, 10.806]; Prøysenstua [60.912, 10.8076]. Layers: `teorier`, `steder`. Added in aa81ebf on 23.09 17:56.

**The `tekst` field (community_interpretation; verbatim)**

> 'Mange leter nå ved Rudshøgda i Ringsaker, der Alf Prøysen vokste opp. Sammenhenger: (1) Dyrene i boksen, rev, kråke og ekorn, er alle med i Prøysens «Sirkus Mikkelikski»: Mikkel Rev, Frøken Kråke og ekornet Nøtteliten. (2) Bak Prøysenstua står Prøysenstjerna, en 27 m høy stjerne laget etter Prøysens julevers om stjerna, og Anja sier hun liker å se stjernene om natta. (3) Flyet NOZ9EG gikk ca. 6–11 km fra Prøysenstua kl. 21:31. (4) Ringsaker er default.no sin kandidat nr. 5 (Brøttum). (5) Blandingsskog med gran og bjørk, ca. 2 t fra Oslo.'

**Interpretation (verbatim)**

> 'Den tematisk sterkeste teorien: nesten alle dyre-hintene peker på Prøysen. Mot: da Anja pekte opp, var begge flyene ca. 30 km unna. Rudshøgda lå utenfor det som var klart på satellitt 23.09. Soloppgang ca. 07:00, akkurat på grensen. Prøysenstua er sjekket, men skogen rundt stjerna er det ikke.'

**Verification [model output: this agent]**
- (3) is misstated. By linear interpolation of the ADS-B fixes, NOZ9EG passed about **3.2 km** east of Prøysenstua at about 21:31:40. It was 9.6 km away at 21:31:00. "6–11 km" overstates the distance.
- Plane distances when she pointed (21:28:53, 45 s delay):
  - NOZ56U: 27.3 km away, 13.3° up;
  - NOZ9EG: 39.7 km away, 10.6° up.
  - So "ca. 30 km" is right for NOZ56U but low for NOZ9EG.
- Sunrise at Rudshøgda, flat horizon: 21.09 06:58:10, 22.09 07:00:40, 23.09 07:03:00. That is **after** 07:00 on 22 and 23.09.
- (4) is inconsistent with DEFAULTNO at innhold.ts:1159–1165 (22.09 16:42), where nr. 5 is Trysil. The Brøttum ranking is from an older default.no list.
- The "Anja likes to see the stars at night" statement has no whiteboard entry in TAVLE. It is unsourced here.
- The crow in (1) is uncorroborated (see `dyr`).

**Against the theory, from elsewhere in the file**
- `fjellmark` ('Det passer dårlig med lavlandet ved Rudshøgda').
- Point-in-polygon: Prøysenstua lies outside SOL_I_DAG [0] (the clear area on 23.09). This agrees with the hint's own "Mot".
- Prøysenstua was checked by one person in chat and nothing was found (the `tretopp` entry, ce85e10).

### 34. `digeras`: community tip, Digeråsen. innhold.ts:785–795

- Status: `usikker`. Source: 'Chat'. Date: 23.09.
- fokus 'digeras' [61.1788, 11.2639]. The DMS 61°10'43.84"N 11°15'50.13"E converts to 61.178844, 11.263925, which matches.
- Layers: `teorier`, `fly`. Added in 58e737c on 23.09 14:59.
- **Community tip:**

> 'Flere tipper 61°10\'43.84"N 11°15\'50.13"E og mener det «er så klink her». En skogkledd ås på 606 moh. mellom Løten og Åmot, ca. 2,5 t fra Oslo.'

- **Interpretation (verbatim):**

> 'Passer med lyden: NOZ56U var nesten rett over (74°) kl. 21:32:50, da rumlingen var høyest. Passer ikke med pekingen: da Anja pekte opp, var flyet 45 km sør og bare 8° over horisonten. Bruk «Sjekk et punkt» i Kart-fanen for å teste slike tips.'
- TEORIER at innhold.ts:1081–1087 adds: '2 t 35 min fra Oslo, i kanten av det som var klart på satellitt 23.09 … (21:28:53 ekte tid)'.

**Verification [model output]**
- At 21:28:53, NOZ56U was 44.7 km away at 8.2° elevation, bearing 182° (due south).
- At 21:32:50 it was 2.6 km away at 73.8°. **Confirmed.**
- With a 20 s delay: 40.1 km at 9.7°.
- Digeråsen lies inside the SOL_I_DAG [0] clear polygon.
- default.no's "sound strongest 21:33:20" (stream time) is about 21:32:20–21:33:00 real, consistent with the 21:32:50 overhead pass. That holds *if* the stream sound is live.
- 606 moh does not match the 810–891 moh reading of the Eiffel clue.
- Revision: 52c0b78 changed 'Noen tipper' to 'Flere tipper … «er så klink her»'.

### 35. `sofa`: Horde in the chat, «glad for å sitte i sofaen inne». innhold.ts:796–804

- Status: `usikker`. Source: '@Hordeapp i YouTube-chatten'. Date: 23.09.
- **Primary (organizer statement in chat; paraphrased, no verbatim quote):** 'Horde-kontoen skrev i chatten at vedkommende var glad for å sitte i sofaen inne.'
- **Interpretation:** 'Tyder på kaldt eller surt vær ute, men personen er trolig ikke ved kassen. Sier lite om stedet.'
- Negligible value. Consistent with `regel-kontor` (the office does not know the location).

### 36. `vinduslos`: the break location has no windows or wifi. innhold.ts:805–813

- Status: `bekreftet`. Source: 'Anja'. Date: 23.09. Added in 86d52b8.
- **Primary:** 'Anja har sagt at hun var et sted uten vinduer og uten wifi.'
  - Presumably a whiteboard or speech, but **there is no TAVLE entry and no verbatim quote**. Class: organizer_media/primary via Anja, paraphrased. Confidence is moderate.
- **Interpretation:** 'Trolig en container, campingvogn, telt eller lignende nær kassen, ikke en hytte. Det passer med at Horde unngår hytter i år, og ikke med Tretopphyttene, som har store vinduer.'
- Related:
  - `bindfold` (usikker): blindfolded every time she leaves the box, per hordejakten.vercel.app; downgraded in 893318a.
  - `gikk2min`.
  - 24.09 17:20 whiteboard «INGEN HYTTE I NÆRHETEN SOM JEG VET OM ELLER SER».

### 37. `hytte`: no cabin this year, a portable toilet. innhold.ts:814–822

- Status: `tolkning`. Source: 'Anja + fellesskapet'. Date: 23.09.
- **Primary (paraphrased, no quote):** 'Anja har bekreftet at doen er portabel.'
- **Community belief:** 'Fellesskapet tror Horde har droppet hytte helt i år, fordi folk fant bookingene i fjor.'
- **Interpretation:** 'Du trenger ikke lete etter en hytte eller et bygg. Se etter en åpen furumo nær en skogsbilvei, der et team kan bære inn utstyret.'
- Revision: 86d52b8 added the reason 'fordi folk fant bookingene i fjor'.
- Caution from mkekeoooo PRESISERINGER.md: 'Personell, strøm og nett beviser ikke at en hytte eller fast strømtilførsel ligger nær.'

### 38. `video2309`: new Horde video, «Hvordan går det med Anja?». innhold.ts:823–832

- Status: `bekreftet`. Source: 'YouTube 1raIm3ANsAI (23.09)'. Link: https://www.youtube.com/shorts/1raIm3ANsAI. SISTE_NYTT at innhold.ts:1618 times it at 23.09 15:30.
- **Primary (organizer_media):**

> 'Horde skriver: «Kjenner jeg dere riktig så vil dere overanalysere denne videoen». Videoen viser kassen forfra: blandingsskog med gran, furu og mange tynne bjørker med gule blader, flatt og mosegrodd underlag, en stige og en svart skjerm inne i kassen. «+5» står på ryggen av genseren. Nattbildene har tre lamper over kassen.'

- **Interpretation:** 'Bekrefter «+5» og blandingsskog med mye bjørk. Bjørk med gule blader passer med høstfarger i innlandet rundt 20. september. Ingen stedsnavn eller skilt synes.'
- Related later evidence:
  - Whiteboard 25.09 18:13 (innhold.ts:1051): «KANSKJE 35% BJØRK · 25% GRAN · 40% FURU · AKKURAT RUNDT MEG».
  - Whiteboard 25.09 10:38 (innhold.ts:1027): «IKKE TV, MEN PAD PÅ UTSIDEN AV GLASSET ←». This may be the "black screen".
  - Hagina's field observation (FOLK_TROR, innhold.ts:1273–1276): birch at about 510 moh near Sjusjøen is orange and thin, so autumn is further along there than on the stream.

### 39. `pluss5`: «+5» on the sweater. innhold.ts:833–841

- Status: `apen`. Source: 'Stream + Horde-video 23.09'. Date: 23.09. Added in 6a33959 on 23.09 15:32.
- **Primary (primary_stream_visual + organizer_media):** 'Genseren til Anja viser nå «+5» på ryggen. Det synes tydelig når hun står på hendene i Horde-videoen 23.09.'
- **Interpretation (verbatim):**

> 'Uløst. Mulige lesninger: samme Cæsar-forskyvning (+5) som på buksa, brukt på et nytt hint. Eller legg 5 til en kode: 5008 + 5 = 5013, eller +5 på hvert siffer = 0553. Eller temperaturen ute, ca. +5 °C. Prøvd på genser-tallene (7 10 5 12 4 6 18 9): +5 gir LOJQIKWN og −5 gir BEZGYAMD, så det gir ingen mening der.'

- **Check:** +5 gives L O J Q I K W N. −5 gives B E Z(wrap) G Y(wrap) A M D. Both correct.
- Derived code candidates (KODER): 8915, 0896, 8105, 5013, 0553, and the door candidates 50085 and 55285.
- Coincidence to note: the 25.09 09:58 whiteboard reads «SIKKERT 5° · TROR DET ER VARMERE» (innhold.ts:1017).
- Revisions: 015d617 added the LOJQIKWN/BEZGYAMD test; 66e31ce added the video source.

### 40. `koder`: possible lock codes. innhold.ts:842–850

- Status: `apen`. Source: 'Appen, stream og chat'. Date: 23.09. Added in 58e737c on 23.09 14:59.

**The `tekst` field (verbatim)**

> 'Det er 3 låser: 2 hengelåser med 4 siffer på pengeboksen, og 1 elektronisk lås med 5 siffer på døra (for Anja). Kandidater: 5008 (kredittskår + «terje»). 5528: plakaten foran kameraet ser ut til å vise kortstokker, ikke pengebunker, og en kortstokk har 52 kort, så «00» i 5008 kan være 52. 2188 (nevnt i chatten, ukjent kilde). Hendene under Horde-skiltet kan også være sifre, som romertall (første hånd VII = 7) eller binært. Kodejakten gir en kode. 072 og 500 fra «Ho Ho Hint Hint».'

**Interpretation (verbatim)**

> 'Koder, ikke steder. Anja har nå skrevet at døra har en elektronisk lås med 5 siffer, i tillegg til hengelåsene med 4 siffer. Ha med alle kandidatene når du drar ut. 5528 og 2188 er ubekreftet.'

**Primary whiteboards on the locks**
- innhold.ts:918, 23.09 evening: «ELEKTRONISK LÅS PÅ DØRA MED 5 SIFFER».
- innhold.ts:985, 24.09 08:24: «5 SIFFER · GANSKE SIKKER». The photo `tavle-5-siffer.jpg` has the overlay 2026-09-24 08:24:58 and reads «5 SIFFER / GANSKE SIKKER».
- innhold.ts:990, 24.09: «2x HENGELÅS 4 TALL · 1x KODELÅS 5–6 TALL · TROR 5». The photo `tavle-laser.jpg` shows «2x HENGELÅS 4 tall / 1x KODELÅS 5-6 tall / TROR 5» next to a box labelled «1116 897 KR».
- innhold.ts:1007, 25.09: «KAN IKKE TESTE KODER · INGEN HAR FUNNET BOKSEN».

**Revision history (lock count)**
1. 58e737c: 'Kassen har 2 hengelåser og døra 1, alle med 4 siffer'.
2. 3885ab8 (15:07): 'Kassen har 2 kodelåser med 4 siffer'.
3. 24c4d59 (23.09 19:10): the current 3-lock text.
4. c4c0aa3 (18:02): betydning now mentions the 5-digit door lock.

**Issues**
- The current tekst says the door has "5 siffer". It was not updated to the 24.09 «5–6 TALL · TROR 5». SIKRE_FAKTA at innhold.ts:1464 has the more accurate 'med 5 eller 6 siffer (Anja er «ganske sikker» på 5)'.
- Organizer: «Hint til hva kodene kan være ligger i appen 💙» (the `kodeniappen` entry, Horde in a comment field, 24.09).
- Alf (second-hand): «Kan være at noen av kodene allerede har kommet.»
- **Retraction:** the `vedkassen` hint was removed as a "fake item" in 094b3b8 on 25.09 11:16. It had said people were at the box trying codes: «Flere som har prøvd seg på koden ved boksen nå by the way. Vi vet hvor det her er hen.»

### 41. `plakat`: poster «Plutselig tilbake!». innhold.ts:851–859

- Status: `usikker`. Source: 'Stream'. Date: 23.09. Added in 520fd05.
- **Primary (primary_stream_visual, with a community reading):**

> 'En tegning av kassen med to hengelåser og bunker inni, med teksten «Plutselig tilbake!». Den står lent mot en trevegg. Bunkene kan være kortstokker og ikke pengebunker.'

- **Interpretation:** 'Er det kortstokker, kan det peke på tallet 52 og koden 5528 (se «Mulige koder»). Ingen kjent stedsinfo.'
- **Revision:** 58e737c changed "pengebunker" (money bundles) to "kan være kortstokker" (may be card decks). The earlier betydning, 'Trolig en kampanjeplakat…', was replaced.
- **Open question:** «lent mot en trevegg» (leaning against a wooden wall) implies a wooden structure in view. Is it the box platform, a camera housing, or a shed? This bears on the "no buildings" claims. `koder` also calls it «plakaten foran kameraet».

### 42. `hintvideo`: official hint video, «Trenger du et hint?». innhold.ts:860–869

- Status: `bekreftet`. Source: 'YouTube H_-0LbPSu5s'. Date: 22.09. Link: https://www.youtube.com/watch?v=H_-0LbPSu5s. Added in ecf0260.
- **Primary (organizer_media):**

> 'Bare 0–3 s og 10–12 s viser selve stedet, resten er arkivbilder. Kassen står på en lav plattform i blåbær- og tyttebærlyng, med gule bjørker og høye furuer bak.'

- **Interpretation:** 'Furumo med bjørk og bærlyng: typisk for Østlandet og indre Agder, mindre typisk for kysten.'

### 43. `tommer`: logging nearby. innhold.ts:870–877

- Status: `usikker`. Source: 'Stream (via default.no). Takk til default.no.' No date. Added in ecf0260.
- **Primary (paraphrased; relayed through default.no; no time or quote):** 'Anja har kjent lukt av tømmer, hørt dunking og sett en lastet tømmerbil.'
- **Interpretation / model:** 'Aktiv hogst i nærheten. default.no leter innen 800 m fra en hogstflate fra 2022 eller senere, eller 400 m fra en fra 2024–25 (Global Forest Watch). Se etter ferske hogstflater på satellittbilder i kandidatområdene.'
  - The 800 m / 400 m buffers are a model rule set by default.no.
  - Clearcut data is mirrored in `public/data/defaultno/hogst/`.
- Revision: fe51e10 on 23.09 15:55 added the default.no buffers.

**Tensions**
- How did she "see a loaded timber truck"?
  - She sees only forest and the camera from the box: «SER KUN SKOG OG KAMERA FRA BOKS» (innhold.ts:886).
  - The car windows were covered (SIKRE_FAKTA).
  - She is reportedly blindfolded when leaving the box.
  - If true, the sighting was probably at pickup or during the drive, and so not necessarily local.
- The 24.09 whiteboard «DET HAR VÆRT HOGD TIDLIGERE DER JEG GIKK I GÅR · GIKK DEN VEIEN →» (innhold.ts:995) describes **old** logging along her walk. That is not the same as *active* logging.
- Alf's statement that the sound is real does not validate "thumping", given default.no's loop finding.

---

## 2. Consolidated retractions, downgrades and corrections touching this half

1. **Stream delay.**
   - What changed: 'Streamen er 45 sek forsinket (bekreftet)' became 'trolig 20 sek–1 min forsinket (vi tipper)'.
   - Where: `fly` betydning, commit 01ab80d, 25.09 11:29.
   - Still unfixed: the hard-coded `STREAM.forsinkelseSek: 45` (innhold.ts:10).
2. **Windy blue areas.**
   - What changed: "less likely; screenshot time unknown, zone roughly drawn" became "blue areas are ruled out".
   - Where: `skyer`, 520fd05, 23.09 14:49.
   - This is a certainty **upgrade** with no new evidence, so treat it as reversed back to "less likely".
3. **Direction to the car.**
   - What changed: the car was first placed WNW of the box, then ESE (walk about 120° from the car; 86d52b8). It was flipped again to the car being SE of the box, walking about 300° NW (`komfra`, 4e65b1c, 24.09 18:35).
   - Still unfixed: the `skilt` betydning still carries the pre-flip wording.
4. **Lock configuration.**
   - What changed: "all 4 digits" became "2 code locks with 4 digits", then "2 × 4-digit padlocks + 1 × 5-digit electronic door lock".
   - The whiteboard later said «5–6 TALL · TROR 5» and «5 SIFFER · GANSKE SIKKER».
   - Where: `koder`, 58e737c → 3885ab8 → 24c4d59.
5. **Poster.**
   - What changed: "money bundles" became "maybe card decks" (the 5528 idea).
   - Where: `plakat`, 58e737c.
6. **Animals.**
   - The badger was relabelled "badger or raccoon" (67eb8d0).
   - The Prøysen reading moved from «Reven og kråka» to «Sirkus Mikkelikski» (aa81ebf).
   - The squirrel clue was weakened (9ea67b3).
   - The Horde AI «3,4 grevlinger» hint was **removed** as not repeatable (337ddc2).
   - mkekeoooo: third-party screenshots show a *badger*, item «Olivenoljestativ», 100 000 points, shipping «Nesten Helt Hjem». Its earlier "beaver" mention was corrected.
7. **Terje T-shirt.**
   - What changed: a separate "new" hint was removed and folded into `terje`, because the T-shirt is not new (2f86bbf).
8. **Tretopphyttene.**
   - Checked on site by a chatter with no finding (ce85e10).
   - Anja: «INGEN HYTTE I NÆRHETEN SOM JEG VET OM ELLER SER» (24.09 17:20).
9. **Froland / Agder (`skyanalyse`).**
   - Superseded by `froland` (ruled out on weather, 6cddb71; rain in Froland on the evening of 23.09, 01ab80d).
10. **`vedkassen`** ("people at the box trying codes").
    - Removed as a fake item (094b3b8, 25.09 11:16).
11. **Place-name correction.**
    - NOZ56U "over Løten" became "over Hamar, like ved Løten" (a141dae, Kartverket check), in `fly`, `innlandet` and `solidag`.
12. **Kodejakten.**
    - Status went from apen to bekreftet (source code read).
    - The API was not live on 23.09 (503 not_configured; b7a2c7f).
13. **Kamera/sun-light doubt (`lysfake`, first half).**
    - The fake-sunlight concern was weakened by `kamera41` agreeing with the default.no sun fit (7983773).
14. **Unverified app screenshots (first half, relevant to codes).**
    - `enkode` (LD6788 → «ENKODE») and `frolandekorn` were downgraded from bekreftet to usikker in 893318a on 24.09 19:55, with the source changed to «Skjermbilde delt i chatten (ikke sjekket selv)».

## 3. Places and coordinates mentioned in this half

| Place | Coordinates [lat, lon] | Where | Role |
|---|---|---|---|
| Utsiktsredet / Tretopphyttene (Danseråsvegen 173, Brumunddal) | 60.9748, 10.9167 | `hytter` pos; TEORIER tretopp | Checked, no finding |
| Bjørkhytta, Danseråsen | 60.9914, 10.8841 | HYTTER | Booked 23.09–11.10 |
| Other Tretopphyttene cabins | see §1.5 | HYTTER | Checked |
| Horde AS, Lars Hilles gate 20A, 5008 Bergen | 60.3896, 5.3297 | `bergen118` pos; BERGEN | Code 5008 origin; 118° line start |
| Tokke (2023 box area) | 59.444, 7.989 | STEDER | Prior year, 19.6 km from the 118° line |
| Prøysenstua, Rudshøgda | 60.912, 10.8076 | `dyr` fokus | Prøysen theory; checked |
| Prøysenstjerna (approximate) | 60.9115, 10.806 | `rudshogda` fokus | Forest around it not checked |
| Bjørneparken, Flå | 60.4343, 9.4493 | `bjorneparken` fokus | Weak colour theory |
| Nøtterøy | 59.21, 10.42 | `ikkeoy` fokus | Ruled out (not an island) |
| Skyanalyse meeting point, inner Agder | 58.7, 8.27 (rings 12 / 45 km, ±15 km) | `skyanalyse` pos | Superseded |
| NOZ56U when «FLY» was written (about 21:29:50 real) | 60.8705, 11.2481 | `fly` pos; FLY_PUNKT | Flight track |
| NOZ9EG at about 21:29:15 | 61.216, 10.896 | FLY_PUNKT2 | Flight track |
| Innlandet focus | 61.25, 10.95 | `innlandet` pos | Consensus region |
| Digeråsen (606 moh) | 61.1788, 11.2639 (61°10'43.84"N 11°15'50.13"E) | `digeras` | Fits the sound, not the pointing |
| Texas, Våler | 60.87812, 12.21229 | (via `grevling`) | Theory |
| Kompassen, Våler | 60.87639, 12.31426 | (via `grevling`) | Theory |
| Brauta, Ringebu | 61.43659, 10.1854 | (via `grevling` / `haaland-brauta`) | Theory, about 190 moh |
| Oslo (pickup) | 59.9139, 10.7522 | OSLO | Start |

**Place names with no coordinates in these entries:**
Kongsvinger, Rena, Elverum, Hamar, Løten, Sjusjøen, Brumunddal, Ringsakfjellet, Brøttum, Åmot, Østerdalen, Solør, Trysil, Røros, Valdres, Agder, Birkenes, Froland, Hardanger, Norheimsund, Odda, Hardangervidda, Vinje, Seljord, Drangedal, Kragerø, Hallingdal, Lillehammer, Gardermoen, Dallas (Texas).

## 4. Code candidates raised in this half

| Code | Origin | Rating |
|---|---|---|
| **5008** | App: Kredittskår + «terje». Also Horde's postcode. | KODER 'hoy' |
| 5013 / 0553 | 5008 with «+5» added | lav |
| 5528 | 5008 with 00 → 52 (card-deck poster) | middels |
| 2188 | Chat, source unknown | middels (unverified) |
| 7… | Sign hands as Roman numerals (VII) or binary | lav |
| 072 / 500 | «Ho Ho Hint Hint», only 3 digits | lav |
| Kodejakten code | One padlock; server was offline on 23.09 | – |

- Door candidates in BESTE_KODER (5 digits): 00891, 00810, 27000, 50085, 55285, 07250.
- Horde: «Hint til hva kodene kan være ligger i appen 💙».
- Terms: codes come «fra appen».

## 5. Internal contradictions and weak spots found in this half

1. The `skilt` betydning (approach from the WNW) conflicts with `komfra` (car to the SE, arrow ←, about 130°).
2. `skyer` says "blue = ruled out", but its own band polygon contains Sjusjøen, Koppang, Gålaveien and Lillehammer. The file treats several of these as live candidates.
3. `soloppgang` uses sunrise times that fit 22.09. For 23.09, Løten, Rena and Røros are at about 07:00–07:01, and Ringsaker and Rudshøgda at 07:02–07:03.
4. `rudshogda` point (3), "NOZ9EG 6–11 km from Prøysenstua", is contradicted by the same ADS-B data: the minimum is about 3.2 km. Its "default.no nr. 5 (Brøttum)" also conflicts with DEFAULTNO (nr. 5 = Trysil).
5. The delay assumption is inconsistent across entries: 45 s (digeras, TEORIER), about 22 s (FLY_PUNKT), and "20 s–1 min" (the current betydning).
6. `kamera41` gets no magnetic-declination correction, while the sign bearing got one.
7. `dyr` claims a squirrel and a crow were "in the box", which no other entry supports.
8. `koder` says the door has "5 digits", but the latest whiteboard says «5–6 TALL · TROR 5».
9. In `tommer`, a timber truck "seen" is hard to square with a blindfolded, covered-window journey.
10. In `lydtett`, "stream sound unusable" does not follow from a soundproof box.
11. `solmiddag` needs the azimuth to about ±0.6° to separate 11–12°E from Valdres. That is not justified by the camera calibration.
12. In `fly`, «rett opp» contradicts TAVLE «pekte opp, litt mot sørøst».
13. In `bergen118`, "…Drangedal … Kragerø" is loose. The geodesic reaches the coast near Langesund/Porsgrunn–Larvik; Drangedal is 21.6 km off and Kragerø 32.6 km off.
14. The NOZ9EG callsign is absent from default.no's `flyhendelser.json`, which lists "@@@@@@@@". The label needs a source.

## 6. Open questions

- Which morning did «SOLA VAR OPPE FØR 07» refer to, and does "oppe" mean the sun disc above the terrain or just daylight?
- Is «KAMERA 41 ØST» a magnetic or a true bearing? Is it the bearing from the box to the camera, or something else?
- What is the actual Windy screenshot time for the blue areas, and was the Lillehammer–Sweden band real?
- Where does the "NOZ9EG" identification of the southbound B738 come from?
- Is the Kodejakten backend live now (after 23.09)? What code does it give?
- Does the door lock have 5 or 6 digits?
- What is the "trevegg" (wooden wall) that the poster leans against?
- Is the Horde Rewards animal a badger or a raccoon, as seen directly in the app? What does the «Nesten Helt Hjem» shipping text mean?
- What exactly did Anja say about windows/wifi and the portable toilet, and when? There is no verbatim quote.
- What is the source and timing of the timber smell, the thumping and the "loaded timber truck"?
- Did the squirrel and crow ever appear inside the box?
- Do the sign's hands, which apparently changed during 23.09 and returned as a single open hand on 25.09, encode digits?
- Is the dew of 07:00–09:40 from 21.09 or 22.09?

## 7. Files and datasets used

| File | Contents |
|---|---|
| `/home/user/test/data/raw/magnus/src/data/innhold.ts` | HINT 46–878; TAVLE 881–1054; STEDER 1065–1078; TEORIER 1080–1140; SOL_I_DAG 1147–1151; DEFAULTNO 1159–1165; FLY_PUNKT 1168; FLY_PUNKT2 1178; SKYANALYSE 1181; SKYDEKKE 1188–1191; FAKTA 1195–1200; BESTE_KODER 1211–1233; KODER 1236–1255; FOLK_TROR 1258–1344; HYTTER 1444–1453; SIKRE_FAKTA 1456–1468; SISTE_NYTT 1471–1624; TIKTOK_2509 1627–1636; FLY_2509 1639–1642 |
| `/home/user/test/data/raw/magnus/src/data/lag.ts` | Map layer definitions: innlandet 176, retning 203, skydekke 219, dn_orrfugl 401, solidag 766, skyanalyse 776, steder 803, teorier 817, fly 826, felt 855, hytter 868 |
| `/home/user/test/data/raw/magnus/public/data/fly_2130.json` | ADS-B tracks for 21.09 21:28–21:34 |
| `/home/user/test/data/raw/magnus/public/data/defaultno/flyhendelser.json` | default.no flight events |
| `/home/user/test/data/raw/magnus/src/data/defaultno_mer.json` | default.no mirror, fetched 24.09 18:36: solbane heading, observasjoner |
| `/home/user/test/data/raw/magnus/public/img/` | Images viewed: tavle-laser.jpg, tavle-5-siffer.jpg, tavle-1912-skilt-borte.jpg, tavle-skisse*.jpg, stream-2509-hand.jpg, stream-2509-skilt-tilbake.jpg, app-terje-tskjorte.jpg |
| `/home/user/test/data/raw/mkekeoooo/PRESISERINGER.md`, `KILDER.md` | The olive-oil item note; independence caveats |
| `/home/user/test/data/raw/mk_bevis/bevis/claude-2026-09-25/README.md:14` | Heading 219.4° |
| `/home/user/test/evidence/sources/hints_b_checks/` | Our scripts and the full hint change log |
