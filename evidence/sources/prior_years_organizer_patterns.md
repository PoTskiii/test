# Earlier Horde hunts (2023 and 2024; no hunt in 2025) and an organizer-behaviour prior for Hordejakten 2026

Compiled 2026-09-25, evening (Norway time), by the research subagent for prior years and organizer patterns.
This file supersedes and extends `evidence/sources/prior_years_early.md`, which an earlier subagent wrote in the same session. Section 13 lists what this pass re-confirmed independently and what it carries over unverified.

**Machine-readable companions:**
- `evidence/sources/prior_years_organizer_patterns_files/organizer_prior.json`: the numeric prior from §8.
- `evidence/sources/prior_years_organizer_patterns_files/prior_year_sites.geojson`: prior-year reference geometry, as polygon, border line, points and a bounding box. None of it is an exact find spot, because none was ever published.

---

## 0. Method, evidence grades and limits

### Tools

- **WebSearch** works server-side. This pass ran **41 successful queries**. They are listed in §14.
  - The session-wide limit of 200 searches ran out after query 41, so 3 further queries were refused. The earlier subagent had used about 60 queries.
- **WebFetch** was blocked for:
  - horde.no (`EGRESS_BLOCKED`)
  - sosialnytt.com (`EGRESS_BLOCKED`)
  - web.archive.org ("unable to fetch")

  No article body was read. Every news fact below comes from a search-engine summary of the article, and the article URL is given.
- **GitHub:**
  - GitHub search found `danielmb/hordejakten`, a stream recorder from the 2023 hunt, and cloned it (§3.8).
  - `mkekeoooo/hordejakten-2026` issue #9 ("Utenfor boksen: arrangørlogikk …") could not be opened. The API returned 403 because the repo is not enabled for this session. Its content is known only from search summaries.
- **Local data used:**
  - `data/raw/magnus/public/data/drivetime.json`: OSRM car times from Oslo sentrum on a 0.1° × 0.2° lattice.
  - `data/raw/magnus/public/data/kommunevurdering.json`: municipality polygons.
  - `data/raw/magnus/src/data/innhold.ts`: the hint database.
  - `data/raw/mkekeoooo/rapport/Hordejakten_2026_fullstendig_rapport.pdf`
  - `evidence/sources/whiteboard_log.md`

### Evidence grades used throughout

| Tag | Meaning |
|---|---|
| **[P]** | Primary organizer material: a Horde or Alf TikTok caption, a Horde press release, or an organizer quote carried in the news. |
| **[N]** | News outlet, known only through a search-engine summary. The article body was not read. |
| **[C]** | Community observation or claim, from GitHub repos, default.no via the mirrors, or chat relayed in `innhold.ts`. |
| **[I]** | My own inference or calculation. |
| **[W]** | 2026 whiteboard (*tavla*) text. This is primary 2026 evidence, quoted from `whiteboard_log.md` and `innhold.ts`. |

### Times

- All prior-year clock times are **real time, CEST**. The 2023 hunt ended 23 Oct 2023, before the switch to winter time on 29 Oct. The 2024 hunt was in May.
- Post times were decoded from TikTok video IDs: Unix seconds = ID >> 32. X/Twitter snowflakes were decoded the standard way. All decoded times are listed in §12.

### Known reliability problems with search summaries

The summarizer sometimes mixed years. It credited Sigurd and Hans Inge to Kongsberg, and it gave 1 078 218 kr as the 2024 prize. Both are wrong. Conflicts are resolved in §10.

---

## 1. Executive summary

1. **Only two earlier hunts exist.**
   - **2023, "Jakten på gjeldfriheten":** 17–23 Oct 2023, **Tokke municipality, Vest-Telemark**. The community places it at the Vinje/Tokke border.
   - **2024, "Hordejakten 2024":** 29 Apr – 5 May 2024, **"ved sølvgruvene på Kongsberg"**, Buskerud.
   - **No 2025 hunt.** Børsen: "har tidligere arrangert pengejakten to ganger, én gang i 2023 og én gang i 2024". 2026 is the third.
2. **No exact find coordinates, elevation, parking spot or walking distance was ever published** for either year. Both are known only at municipality or "near the silver mines" level.
3. **Both earlier sites share these features:**
   - forest;
   - in Telemark or Buskerud, south-west or west of Oslo, **not** in Vestland even though Horde is in Bergen;
   - **1.4–1.55 h (Kongsberg) and 3.2–3.8 h (Tokke) by car from Oslo** (OSRM);
   - both lie on the **E134** Drammen–Kongsberg–Seljord–Åmot–Haukeli corridor [I];
   - reachable by car plus a short walk: in 2023 a car horn on the road could be heard on the box microphone.
4. **Both hunts were found on day 6, over the weekend, after a late hint.**
   - 2023: about 5.8 days, found just before 02:00 on Mon 23 Oct.
   - 2024: about 5.9 days to find, on Sunday morning 5 May, and about 6.2 days to open.
   - For 2026 the same pace points at **Sat 26 – Sun 27 Sep**. Alf said on 25.09: «Kommer en del viktige hint nå i løpet av helgen».
5. **How the earlier hunts were actually cracked:**
   - **Live natural signals on the video.** Snow falling on the stream matched the weather where the finder was working, in Åmot, Vinje.
   - **Crowd analysis** of weather, wind, bird sounds, power lines and air traffic.
   - **Official hints** narrowed the area.
   - **Long field searches.** One finder searched for more than 16 hours.
   - **In 2023, the stream's live audio used as a proximity sensor.** Finders honked car horns and shouted. Sundklakk "heard his own honking on the livestream" and knew he was close.
6. **Known hint style:**
   - **numbers turned out to be lock codes** (2023 «2412»; 2024 a code word in a golden envelope; 2026 «terje»→5008 and «072» from the 2024 prize);
   - **pictograms or wordplay at municipality level** (2023: "kommunevåpen med dyr", municipal coats of arms with animals);
   - **literal landscape media** (2023: a video of power lines).
   - **No earlier hunt is known to have used an elevation hint.**
7. **Trolling and countermeasures:**
   - Alf admits «tidligere år, da drev vi å trollet litt med lyden».
   - Each year's winning technique was countered the next time:
     - live audio homing in 2023 became audio of uncertain liveness in 2026, with loops found by default.no;
     - cash in the box in 2023 became a code word in 2024;
     - several finders arriving at once in 2024 became a queue plus a 5-hour quarantine in 2026;
     - cabin bookings reportedly traced in the previous hunt meant no cabin in 2026 ([C]).
   - **No official text hint is known to have been false about location.** The misdirection has been noise (sound, drive time, blindfolding), not lies.
8. **Organizer-behaviour prior, headline numbers (§8):**
   - Distance to the nearest drivable road (including forest roads): **median about 420 m, P(≤1 km) ≈ 0.88**.
   - OSRM drive from Oslo: **P(1–4 h) ≈ 0.72**.
   - Forest ≈ 0.95. No dangerous terrain and no river crossing.
   - Official bare numbers: **P(lock code) ≈ 0.65 vs P(literal geography) ≈ 0.25**.
   - Found by Sun 27 Sep 23:59: **≈ 0.45**.

---

## 2. Summary table

| | **2023: "Jakten på gjeldfriheten"** | **2024: "Hordejakten 2024"** | **2025** | **2026 (ongoing; context)** |
|---|---|---|---|---|
| Prize | **1 078 218 kr** in cash at first. Removed on Thu 19 Oct (police agreement, safety) and replaced by a code word / bank transfer | **1 093 072 kr**, as a code word in a golden envelope and not cash ("for security reasons") | no hunt | **1 116 897 kr** in cash, plus a person (Anja) in a transparent box |
| Symbolism | Number of Norwegians with interest-bearing consumer debt | Same concept | – | Same concept |
| Launch | **Tue 17 Oct 2023**. First TikTok 07:03 CEST | **Mon 29 Apr 2024**. Alf TikTok 10:16 CEST; press release the same day | – | **Mon 21 Sep 2026**, stream about 06:50 |
| Found | **Mon 23 Oct 2023, just before 02:00 CEST** (a viewer TikTok "1 million er funnet" was posted 02:16) | **Sun 5 May 2024, morning.** Several finders. Opened and won in the afternoon | – | not found as of 25 Sep (day 5) |
| Time to find | about 5.8 days (about 139 h) | about 5.9 days to find, about 6.2 days to open | – | – |
| Place (as published) | «Tokke kommune i Telemark» / "den lille kommunen Tokke i Vest-Telemark". Community: «grensen Vinje/Tokke» | «ved sølvgruvene på Kongsberg»; «skauen på Kongsberg» | – | ? |
| Coordinates | **not published**. Reference: Vinje/Tokke border, lat 59.485–59.602 N, lon 7.55–8.25 E. Åmot (59.572, 7.990) lies about 1.2 km from the Tokke boundary | **not published**. Reference: silver-mine field, approx. bbox 59.60–59.69 N, 9.49–9.60 E [I] | – | – |
| Elevation | not published. [I] probably about 450–900 moh (snow on the stream in mid-October) | not published. The silver-mine field spans about 300–750 moh [N/I] | – | – |
| Terrain | forest with bog (*myr*) | forest (*skauen*) in the historic mining landscape | – | whiteboard: «KUPERT/UJEVNT TERRENG · MYE LYNG», «TYPISK FJELLMARK», mixed forest with birch |
| Access | car plus a short walk. Car horns from the road audible on the box microphone. About 15–20 people searched the same area at night | Several people reached the box the same Sunday morning [I: easy access] | – | whiteboard: «CA 5–10 MIN Å GÅ FRA BIL», «TROR DET VAR OPPOVER», «INGEN STIER» |
| OSRM car from Oslo [I] | 3.2–3.8 h, 190–226 km (border east of Åmot to Åmot). Up to 4.4 h at the far west end of the border | 1.4–1.55 h, 86–94 km | – | ? |
| Car from Bergen [I, rough, not routed] | about 4.5–5.5 h (straight line 175–190 km) | about 6–7 h (straight line about 250 km) | – | – |
| Winners | **Sigurd Sundklakk** (working in Åmot, Vinje) and **Hans Inge Josdal** (from Sirdal, per the earlier file). Strangers who teamed up and split 50/50 | **Joakim Kristiansen**: Nordmøre native living in Eastern Norway, in his 30s. The **third to arrive**; he waited and conferred with helpers by phone. (Laagendalsposten: "Tre menn fra Kongsberg …"; see §10) | – | – |
| Decisive methods | snow on the stream matched Åmot's weather; crowd analysis; hints; a field search of more than 16 h; honking and shouting heard on the live audio | small hints through the week "leading ever closer"; a late decisive hint (community); field search; **code locks decided the winner** | – | – |

---

## 3. The 2023 hunt: "Jakten på gjeldfriheten" (17–23 Oct 2023)

### 3.1 Timeline (CEST)

**Tue 17 Oct 2023, launch**
- 07:03. Horde TikTok, caption verbatim: «Jakten på gjeldfriheten er i gang! På et hemmelig sted i Norge har vi gjemt en drøy million kroner i kontanter. Tallet 1 078 218 tilsvarer antall nordmenn med rentebærende forbruksgjeld. Dette må vi gjøre noe med. Last ned Horde-appen og bli med i jakten på pengene! Følg med på horde.no/jakten #gjeldfrimedhorde #horde #hordeapp» [P] https://www.tiktok.com/@horde.app/video/7290788736235785505
- 13:55. Horde TikTok, verbatim: «Finn og vinn pengene. Følg hintene våre, og du kan finne og vinne drøye 1 million kroner! Pengene er gjemt et sted i Norge. **Du må finne kassen og åpne den med riktig kode.** Første til mølla vinner (dere kan jobbe i team) Se pengene live på streamen» [P] https://www.tiktok.com/@horde.app/video/7290894903142288672
  - **So the 2023 box already had code locks.** The earlier subagent's source says "two code locks" [N] https://www.nettavisen.no/okonomi/selskap-med-ellevilt-stunt-har-gjemt-over-n-million-kroner-i-skogen/s/5-95-1400158 (via prior_years_early.md L43).
- 20:15. Alf TikTok: «Les regler og vilkår på horde.no/jakten. Hint kommer gradvis i app, nyhetsbrev og Horde.plus» [P] https://www.tiktok.com/@alf.gunnar/video/7290992706124401952
- The box was placed on the **Tuesday**. «Alf Gunnar og kollegaene gjemte en million kroner i skogen»: the Horde team placed it themselves.
  - [N] https://www.kom24.no/alf-gunnar-og-kollegaene-gjemte-en-million-kroner-i-skogen-na-er-pengene-funnet/659296
  - [N] https://www.op.no/over-en-million-kroner-funnet-i-skogen-i-telemark/s/5-36-1509193

**Wed 18 Oct**
- Launch coverage.
  - [N] https://inyheter.no/18/10/2023/har-gjemt-en-million-kroner-i-norsk-skog/
  - [N] https://borsen.dagbladet.no/nyheter/har-gjemt-n-million-i-norsk-skog/80366517
- The whole marketing budget was in the box. Via prior_years_early.md, from the inyheter summary.

**Thu 19 Oct, cash removed**
- The cash was taken out of the box "på torsdag" for the safety of the searchers. It was replaced by a code word that entitles the finder to a bank transfer.
  - [N] https://www.kom24.no/alf-gunnar-anderse-horde-markedsforing/gjemte-en-million-kroner-i-skogen-na-er-pengene-fjernet/658791
  - [N] https://www.tv2.no/nyheter/innenriks/fjernet-en-million-kroner-fra-skogen/16143177/
- The earlier file adds that this was done in agreement with the police, and that a note with a code word was left in the plastic box. [N] https://borsen.dagbladet.no/nyheter/vill-pengejakt-tar-grep/80370921
- 14:06. TV2's TikTok: «Nå ligger det én million kroner gjemt i skogen. Og du kan finne de! Denne uken har app-selskapet «Horde» fra Bergen gjemt 1.078.218 kroner på et hemmelig sted i Norge.» https://www.tiktok.com/@tv2.no/video/7291639715088977184
- Same day, a GitHub user started recording the stream (§3.8).
- A new hint, «2412», is reported for the Thursday. [N] Børsen 2024 retrospective, via prior_years_early.md L50.

**Sun 22 Oct**
- 13:07. Horde TikTok: «Update på Hordejakten - millionen i skogen #jaktenpågjeldfriheten» [P] https://www.tiktok.com/@horde.app/video/7292737938960534816

**Night of Sun 22 → Mon 23 Oct, the find**
- Sundklakk and Josdal found the box **"like før klokken 02 natt til mandag"** (just before 02:00). [N] https://borsen.dagbladet.no/nyheter/fant-over-n-million-i-skogen/80385711
- Rha/noblad quote the headline «– I tre-tiden hørte vi folk som ropte og hoiet» and say "at three o'clock at night the winning pair found the box". See §10 for how this is reconciled.
  - [N] https://www.rha.no/fant-en-million-i-skogen-i-tre-tiden-horte-vi-folk-som-ropte-og-hoiet/s/5-70-476728
  - [N] https://www.noblad.no/fant-en-million-i-skogen-i-tre-tiden-horte-vi-folk-som-ropte-og-hoiet/s/5-56-746351
- **02:16.** Viewer TikTok "Jakten på gjeldfriheten. 1 million er funnet" (@crytomade). https://www.tiktok.com/@crytomade/video/7292941281032981793
- 03:44. Another viewer TikTok (@jaktjegeren). https://www.tiktok.com/@jaktjegeren/video/7292963813295508769 (via prior_years_early.md)

**Mon 23 Oct, 13:52**
- Horde TikTok: «Øyeblikket og følelsen når du finner millionen i skogen! Vi gratulerer til Hans Inge og Sigurd for strålende innsats i jakten på kassen. Vi ønsker også å takke alle som deltok og gjorde jakten nervepirrende hele veien til mål. Dette var stas, og hvem vet hva vi finner på neste gang.» [P] https://www.tiktok.com/@horde.app/video/7293120639622253856

**Wed 25 Oct, 10:25**
- Økonomiamatørene TikTok: «'Jakten på gjeldfriheten' er en ekstrem variant av tjenesten Horde Rewards … spesialepisode om 'millionen i skogen', hvor seerne også fikk mulighet til å stille spørsmål live.» [P] https://www.tiktok.com/@okonomiamatorene/video/7293809331521342753

**Organizer expectation versus reality**
- Horde had **hoped it would last until November**. [N] kom24 659296
- Horde's page described **new hints weekly** in the app, the newsletter and Horde Plus. [N] https://horde.no/blogg/jakten-pa-gjeldfriheten-er-i-gang/ (search summary)
- **[I]** The organizers planned a multi-week hunt, and the crowd solved it in 6 days.

### 3.2 Location

**Published location**
- «Tokke kommune i Telemark» / "Tokke in Telemark".
  - [N] https://www.ta.no/over-en-million-kroner-funnet-i-skogen-i-telemark/s/5-50-1754839
  - [N] kom24 659296
  - [N] https://sosialnytt.com/millionen-i-skogen-er-funnet-slik-klarte-de-a-lose-gaten/
  - [N] https://borsen.dagbladet.no/nyheter/nytt-sjokkstunt-fra-norsk-selskap/85179562
- Both finders "set course for the small municipality of Tokke, far west in Telemark". [N] Børsen 80385711

**Community framing**
- «Hordejakten 2023 (grensen Vinje/Tokke) ble funnet natt til dag 6; 2024 (sølvgruvene på Kongsberg) søndag morgen». [C] https://github.com/mkekeoooo/hordejakten-2026/issues/9 (via search summary; the issue itself was not readable)
- Magnus pin: `innhold.ts:1076`: `{ id: 'tokke', navn: '2023: Tokke (område)', pos: [59.444, 7.989], … info: 'Hordejakten 2023 ble funnet i Tokke i Telemark. Skog, bil og litt gange.' }` [C]
  - **The pin is Dalen village centre, a placeholder.** Dalen lies at Bandak lake level, which is not consistent with snow in October. It is not the find spot.
- mkekeoooo report p.3: «Tidligere Hordejakter endte i Tokke i Telemark (2023) og ved sølvgruvene i Kongsberg (2024), begge i skog med bil og kort gange.» [C] `data/raw/mkekeoooo/rapport/Hordejakten_2026_fullstendig_rapport.pdf` p.3

**Geometry computed here [I]** (`kommunevurdering.json` polygons; simplified, about 0.001° vertices)
- The Vinje/Tokke border line is about **58 km** long, spanning **59.485–59.602 N, 7.548–8.251 E**. Its centroid is about 59.562 N, 7.913 E.
- **Åmot**, the Vinje administrative centre and where Sundklakk was working (59.572 N, 7.990 E), is inside Vinje and about **1.2 km** from the nearest point of the Tokke polygon (59.563 N, 8.001 E).
- **Høydalsmo** (59.497 N, 8.197 E, on E134) is inside Tokke.
- **[I] Most likely 2023 zone:** Tokke land within roughly 0–10 km of the Vinje border near Åmot, that is, the Åmot–Dalen road (Fv38) side or the E134 side towards Høydalsmo.
  - Reasoning: the finder in Åmot saw the same snow as the stream, and the community says «grensen Vinje/Tokke».
  - This is an inference and not confirmed.

**OSRM car time from Oslo sentrum [I]** (interpolated from `drivetime.json`)

| Point | Time | Distance |
|---|---|---|
| Border near Åmot (59.56, 8.00) | 3.67 h | 216 km |
| Border east part (59.55–59.58, 8.12–8.25) | 3.18–3.31 h | 190–201 km |
| Border west part (59.585–59.60, 7.55–7.75) | 3.96–4.42 h | 232–249 km |
| Høydalsmo | 3.23 h | 196 km |
| Dalen | 3.65 h | 221 km |

Straight-line distances [I]:
- From Oslo: about 150–165 km.
- From Bergen: about 175–190 km. Road time from Bergen is about 4.5–5.5 h via Rv13/E134 over Haukeli. This is a rough estimate, not routed.

**Elevation: not published.**
- Context from the earlier file:
  - Åmot is about 465 moh and Høydalsmo about 560 moh. [N] Wikipedia via prior_years_early.md L68
  - Snow fell on the stream in mid-October in "one of few places in Norway it was snowing that week". [N] https://www.amta.no/fant-en-million-i-skogen-verdige-vinnere/s/5-3-1551361 and https://www.kvinnheringen.no/fant-en-million-i-skogen-verdige-vinnere/s/5-27-474281
- **[I] Probable band: about 450–900 moh.** This is upland forest, not the Bandak valley floor at Dalen.

**Terrain**
- Forest with bog. «Sundklakk rullet ut i en myr» from excitement and had to be pulled out; he also «kastet opp litt».
  - [N] https://borsen.dagbladet.no/nyheter/sigurd-og-hans-fant-millionen-kastet-opp/80389223
  - [N] kom24 659296
- **[I]** Tokke is a major hydropower municipality (Tokke kraftverk at Dalen), with large transmission lines. That fits the "video of power lines" hint (§3.4).
  - Source for the power station: https://en.wikipedia.org/wiki/Tokke_Hydroelectric_Power_Station (search result).
  - The mapping itself is inference.

### 3.3 Access and distance from road

- **Car horns as a proximity sensor.** "When they thought they were near the box, both began honking their car horns. Sundklakk said that when he finally heard his own honking on the livestream, he knew he was close." [N] Børsen 80385711 (search summary)
- Andersen, per the earlier file: the box was found "with the help of car honking and shouting, since the livestream from the site had sound on". About **15–20 people** were searching the same area. «I tre-tiden hørte vi folk som ropte og hoiet» (around three we heard people shouting and hollering). [N/P] rha 476728; nettavisen 1408921; ba 2418443
- **[I] What this implies:**
  - A car horn from a drivable road was audible on the box microphone.
  - In a quiet night forest a car horn carries a few hundred metres to perhaps 1–1.5 km. The box was therefore probably **within about 1 km of a drivable road, most likely a few hundred metres**.
  - It was nevertheless **not visible from the road**. Sundklakk searched for more than 16 hours, and people needed sound to home in.
- Placement was done by car, and Horde staff went back in mid-hunt to remove the cash. That points to easy access.
- Andersen later said on the Shifter podcast (Nov 2024) that during the first stunt he heard people nearby on the livestream and feared someone had seen them place the box.
  - [P via N] https://podcasts.apple.com/us/podcast/horde-gr%C3%BCnder-alf-gunnar-andersen-om-%C3%A5-bygge-selskap/id1150062749?i=1000677566928
  - https://open.spotify.com/episode/1pgCpWTv9O9VBXDunh5mDO
  - Related news: https://www.shifter.no/nyheter/horde-grnderen-da-million-stuntet-var-i-gang-holdt-pa-a-kaste-opp/362561 (via prior_years_early.md)
  - **[I]** The site was close enough to places people pass for the organizer to worry about being seen.

### 3.4 Hints (2023) and how each mapped to the real location

**Channels**
- «Hint kommer gradvis i app, nyhetsbrev og Horde.plus» [P] (Alf TikTok above)
- "continuously on livestream and app" [N] https://borsen.dagbladet.no/nyheter/ny-million-gjemt-i-norsk-skog/81303369

| Hint / signal | Type | Source | How it mapped |
|---|---|---|---|
| «2412» (released Thursday) | official number | [N] Børsen 81334871 via prior_years_early.md L50/L82. [C] issue #9: «Tallhintet fra 2023 (2412) var også en kode.» | **A code, not a place.** No elevation or coordinate reading is known. |
| «kommunevåpen med dyr» (municipal coat of arms with animals) | official pictogram / wordplay | [N] Børsen 81334871 via prior_years_early.md L82 | **Municipality-level pointer** [I]. Tokke's arms are reported as a black bear on gold ([N] snl.no search summary via prior_years_early.md L85). **Not confirmed** that the 2023 hint animal was a bear. |
| Video of power lines | official landscape media | [N] Børsen 81334871 via prior_years_early.md L82 | **Literal local feature.** It fits Tokke/Vinje hydropower lines [I]. |
| Snow falling on the stream | live natural signal | [N] amta/kvinnheringen: Sundklakk «var utplassert på jobb i Åmot i Vinje kommune da han la merke til snøen som falt på livestreamen» | **Decisive regional match.** The weather at his workplace in Åmot matched the stream, and the box was a few km away across the municipal border. |
| Air traffic (Flightradar), wind, bird sounds, power lines | crowd analysis | [N] Børsen 85179562: «Tusenvis fulgte livestreamen og analyserte vær, vind, fuglelyder, kraftlinjer og flytrafikk» | Air traffic was used by the finders (prior_years_early.md L91, from amta). The detail was not re-confirmed here. |
| Final or late clue | official | [N] https://www.dagens.no/nyheter/breaking-fant-en-million-kroner-gjemt-i-skogen: "found it using a final clue" | Content unknown. |
| Car horns and shouting heard on stream | live audio (participant-generated) | [N] Børsen 80385711; rha 476728 | **Final homing, metres to hundreds of metres.** |

**Wordplay?**
- The coat-of-arms hint is a rebus-type pointer.
- «2412» is a code.
- No anagram-type wordplay is documented for 2023. The 2026 anagrams (NORHEIMSUD → HORDE MINUS; «THILPRTE OESHF» = THE SHOPLIFTER) are new.

**Sound and light trolling in 2023**
- Viewers were "nervous at every sound, though it had only been birds so far" [N] (via prior_years_early.md L43).
- The audio at the end was demonstrably live.
- No 2023 light gimmick is documented.
- Alf's 2026 admission of earlier sound-trolling (§7) does not say which year.

### 3.5 Finders and method

- **Sigurd Sundklakk:** worked at Åmot, Vinje. He searched for **more than 16 hours** in total.
- **Hans Inge Josdal:** from Sirdal (per the earlier file).
- They did not know each other. They met in the forest and agreed to split **50/50**, which is 539 109 kr each [I, arithmetic].
- «Deres felles beslutning om å samarbeide var avgjørende» (Horde press release 2024, per search summary). [P] https://www.mynewsdesk.com/no/horde/pressreleases/11-million-skjult-i-norsk-natur-hordejakten-er-tilbake-3319716
- Andersen: "impressed over the internet: large forums worked together to solve the mystery". [N] sosialnytt
- **Outcome:** Horde became Norway's most downloaded app that week, with **about 50 000 new users**, a record for them. [N] https://www.op.no/over-en-million-kroner-funnet-i-skogen-i-telemark/s/5-36-1509193

### 3.6 Organizer actions in 2023 that reveal behaviour

- Horde placed the box themselves (Alf and colleagues).
- They **intervened mid-hunt** to remove the cash, a safety reaction to crowd size.
- The stream "crashed several times" because of traffic. [N] https://inyheter.no/18/10/2023/har-gjemt-en-million-kroner-i-norsk-skog/ (via summaries)
- They planned for weeks and it took 6 days, so **Horde underestimated the crowd**.

### 3.7 Drive times (2023)

- From Oslo: about 3.2–3.8 h (OSRM, optimistic, no stops).
- From Bergen: about 4.5–5.5 h [I].
- **[I]** The site sits roughly on the Bergen/Haugesund ↔ Oslo E134 corridor. A Bergen-based team could drive there on the main road.

### 3.8 Stream infrastructure (2023): a new find

- GitHub `danielmb/hordejakten` has one commit, dated **2023-10-19 16:30:57 +0200** ("jaja"). It contains `main.js`, which polls `https://bsstorm.horde.no/hls/stream.m3u8` every 3 s and downloads the `.ts` segments.
- **The 2023 stream was a self-hosted HLS stream on Horde's own server, not YouTube.** `bsstorm.horde.no` also appears in a public subdomain list: https://raw.githubusercontent.com/rix4uni/BugBountyData/main/data/horde.no.txt
- Clone: `/tmp/claude-0/-home-user-test/cdc3054c-9af4-5a32-8665-8227f802a011/scratchpad/danielmb_hordejakten/main.js`
- **[I]** This explains "the stream crashed several times" in 2023. In 2026 the stream is on YouTube (`EQHgfmZicc8`).

---

## 4. The 2024 hunt: "Hordejakten 2024" (29 Apr – 5 May 2024)

### 4.1 Timeline (CEST)

**Mon 29 Apr 2024, launch**
- 10:16. Alf TikTok: "Vi har gjemt 1,1 million kr i skogen. Finneren er vinneren!" [P] https://www.tiktok.com/@alf.gunnar/video/7363199855700888864 (decoded here; caption per prior_years_early.md)
- Press release «1,1 million skjult i norsk natur: Hordejakten er tilbake!», dated 29 Apr 2024 per search summary. [P] https://www.mynewsdesk.com/no/horde/pressreleases/11-million-skjult-i-norsk-natur-hordejakten-er-tilbake-3319716 Its content, per summary:
  - Horde has "over 300 000 users".
  - "Last year's winners, Sigurd Sundklakk and Hans Inge Josdal, met in the forest during Hordejakten, and their decision to work together was crucial."
  - "Horde fans requested a new hunt."
- Horde landing page title: «Hordejakten 2024 er i gang!» https://horde.no/gjeldfri/hordejakten (search result title)

**Tue 30 Apr, 10:46**
- Horde TikTok: «Jakten er i gang! Tagg oss om du er på jakt og send gjerne bilder/video til jakten@horde.no som vi kan bruke. #hordejakten» [P] https://www.tiktok.com/@horde.app/video/7363578766704037152

**Wed 1 May**
- 11:06. «Har du Horde-appen, kan du finne kassen! #hordejakten» [P] https://www.tiktok.com/@horde.app/video/7363954970053315873
- 16:36. «Du vet aldri hva du treffer på #hordejakten hint?» [P] https://www.tiktok.com/@horde.app/video/7364040181592116512

**Mid-hunt ("after several days")**
- Press release «Spenningsnivået stiger i Hordejakten: Kassen har begynt å telle ned!» [P] https://www.mynewsdesk.com/no/horde/pressreleases/spenningsnivaaet-stiger-i-hordejakten-kassen-har-begynt-aa-telle-ned-3320434
  - Horde activated a **countdown in the box**.
  - Hints came in the app, the newsletter, and Horde Plus with the AI assistant **"Jaktus"**.
  - Alf, per summary: "We wanted to create even more excitement around Hordejakten this year, and with various twists we hope to engage people even more."

**Fri 3 May**
- Økonomiamatørene ep. 175 "Hordejakten" with Andersen. [P] https://open.spotify.com/episode/178hAIH0Mcypgvvq67atBm (via prior_years_early.md)

**Sun 5 May, morning: found**
- «Noen har funnet Horde-millionen i skogen», on Sunday morning, as shown in the livestream. [N] https://borsen.dagbladet.no/studio/borsenstudio/608?post=162361
- 09:43. Horde TikTok (content unknown). https://www.tiktok.com/@horde.app/video/7365418050637663521
- 13:54. Horde TikTok «Hordejakten er ikke over!»: the box was found but not yet opened. [P] https://www.tiktok.com/@horde.app/video/7365482640843017505

**Sun 5 May, afternoon: opened and won**
- Laagendalsposten: «Tre menn fra Kongsberg ble 1 093 072 kroner rikere søndag ettermiddag» (via prior_years_early.md). [N] https://www.laagendalsposten.no/alf-gunnar-la-ut-over-n-million-i-skauen-pa-kongsberg-i-dag-ble-pengene-funnet/s/5-64-1415829
- Børsen: «Åpnet million-boksen». [N] https://borsen.dagbladet.no/nyheter/apnet-million-boksen/81357015 (title only)

### 4.2 Location

**Published location**
- «Det hemmelige stedet i år viste seg å være ved sølvgruvene på Kongsberg.» [N] https://www.ba.no/vant-million-etter-nervedrama-i-skogen/s/5-8-2615243
- Laagendalsposten headline: «Alf Gunnar la ut over én million i skauen på Kongsberg. I dag ble pengene funnet» [N] (above)
- Community: «2024 (sølvgruvene på Kongsberg) søndag morgen» [C] issue #9 (search summary).
- Magnus pin: `innhold.ts:1077`: `{ id: 'kongsberg', navn: '2024: Kongsberg-området', pos: [59.668, 9.65], … info: 'Hordejakten 2024 ble funnet i Kongsberg-området i Buskerud. Skog.' }`. **This is Kongsberg town centre, a placeholder.**

**Silver-mine field context** [N via prior_years_early.md L120–128, from norskbergverksmuseum.no]
- About 30 km² of protected cultural landscape.
- The Kongens gruve entrance is at **Saggrenda, about 8 km outside Kongsberg town**.
- The Helgevann mines are at about 550–650 moh.
- The highest pit (skjerp 17, south of Jonsknuten) is at 729 moh.
- Old mining roads and trails run between the mines.

**[I] Approximate reference area:** bbox 59.60–59.69 N, 9.49–9.60 E, centre about 59.645 N, 9.545 E. This is my approximation of the mine field west and south-west of the town, **not** a published polygon.

**OSRM from Oslo [I]:**

| Point | Time | Distance |
|---|---|---|
| Saggrenda (about 59.628, 9.556) | 1.52 h | 93 km |
| Mine-field centre | 1.53 h | 93 km |
| Kongsberg town | 1.40 h | 86 km |

- Straight line: about 68–74 km from Oslo and about 250 km from Bergen.
- By road from Bergen: about 6–7 h via E134 or Rv7 [I, rough].

**Elevation:** not published. **[I]** Plausibly about 300–750 moh.

**Terrain:** «skauen» (forest). The mining landscape has spoil heaps, shafts and old roads. The box was obviously not in dangerous shaft terrain. Horde's 2024 rules said the box is not placed where it exposes people to danger (via prior_years_early.md L162).

### 4.3 Access

- "During the morning the box was found by several people, and then it remained to see who could solve the code challenge." [N] ba.no 2615243
- **[I]** Several independent parties converging on one Sunday morning implies easy access from a road or trail network. That fits a cultural-heritage area with roads.
- No walking distance was published.

### 4.4 Hints (2024) and mapping

- «Gjennom uka ble det delt ut små hint til deltakerne, som ledet folk stadig nærmere.» [N] ba.no 2615243
- The **individual 2024 hint texts could not be recovered.** horde.no and mynewsdesk are blocked, and the search budget is exhausted.
- **Known mechanics:**
  - codes in the hints;
  - a **golden envelope with a code word** that secured the finder 1 093 072 kr [N] (Børsen 81303369 / 85179562 summaries);
  - a **countdown** in the box;
  - AI tips from **Jaktus** (Horde Plus).
- Community: the hunt was solved «først etter Hordes sene, avgjørende hint og feltsøk». [C] issue #9 (via prior_years_early.md L135)
- **Sound and light:**
  - The countdown display is a visual gimmick.
  - Alf's «trollet litt med lyden» may refer to 2024. **Not established.**

### 4.5 Finders and method

- **Joakim Kristiansen:** "a Nordmøre native living in Eastern Norway", "in his 30s".
- He was "actually the **third to arrive**". He chose to "keep calm", wait, and confer with good helpers by phone, and only tried once the code was worked out. Andersen: this "was likely the key to success".
  - [N] ba.no 2615243
  - [N] https://www.kom24.no/alf-gunnar-andersen-horde-markedsforing/ny-million-gjemt-i-skogen/713720
- Other summaries: "Three people tried and failed to crack the codes before Joakim succeeded", and he "was the fourth person to try opening the box". [N] Børsen studio 608
- Joakim: "the feeling was indescribable … never encountered such amounts of money before". [N]
- **Queue system:** finders took turns at the locks in order of arrival, and this "worked well". Via prior_years_early.md L136. The same rule was codified in 2026 (§5).

---

## 5. 2025: no hunt. The 2026 design as a reaction to 2023–2024

### No 2025 hunt

- Børsen (Sep 2026): «har tidligere arrangert pengejakten to ganger, én gang i 2023 og én gang i 2024». [N] https://borsen.dagbladet.no/nyheter/nytt-sjokkstunt-fra-norsk-selskap/85179562
- The Shifter podcast (20 Nov 2024) says Horde "has hidden one million kroner in the forest twice". [N] (Apple Podcasts summary)
- Queries for "Hordejakten 2025" returned only 2026 material. **Conclusion: no 2025 edition.**

### What changed in 2026 (context for §8)

| Item | Quote | Source |
|---|---|---|
| Person in the box | Anja, 29, from Brumunddal per Ringsaker Blad (via prior_years_early.md). "taken blindfolded and had no idea where she was" | [N] Børsen summary |
| Pickup | «OSLO, SØN KL 04.00» | [W] 21.09 18:31, `whiteboard_log.md:97` |
| Deliberate detours | «kjørt rundt i flere timer … Det var en del av opplegget»; «De tok meg med inn i skogen og bar meg» | [N] https://borsen.dagbladet.no/nyheter/anja-29-jaktes-av-hele-norge/85183299 and /anja-29-snakker-ut-absurd/85185489, via prior_years_early.md L165 |
| Office does not know the site | «Ingen på Hordekontoret vet hvor kassen befinner seg. Det er kun de som er på stedet med Anja som vet noe. De får du ikke tak i.» | [P] `innhold.ts:677` |
| Locks | Three: two 4-digit padlocks and one 5-digit electronic door lock | [C] `innhold.ts:848` |
| Queue and quarantine | «køsystem» and **5 timers karantene** after a failed attempt | [P via chat] Alf TikTok-live 25.09, `innhold.ts:335` |
| Access | «man kanskje må gå litt, men aldri noe farlig, som å krysse en elv»; «Husk at det er jaktsesong, og gå i tydelige klær.» | [P via chat] `innhold.ts:344`, `1634–1635` |
| Clothing | «Ikke kle deg ut som elg, hjort eller storfugl. Det er jaktsesong.» | [P] `innhold.ts:685` |
| Anticipating analysis | «Kjenner jeg dere riktig så vil dere overanalysere denne videoen» | [P] `innhold.ts:829`, `1620` |
| Watching the community | Whiteboard 25.09 «THILPRTE OESHF» (anagram of THE SHOPLIFTER, default.no's operator) «· NOEN SOM VET FASITEN» | [W] `innhold.ts:1038` |
| Pre-empting theories (unconfirmed) | The app word-box reportedly answers FROLAND with «Du fant et hint! Ekornet kan klatre» | [C, unconfirmed screenshot] `innhold.ts:394–399` |
| Reusing prior-year numbers | «072 er de siste sifrene i premien fra 2024 (1 093 072 kr)» | [C] `innhold.ts:718`, `1251` |
| No cabin this year | «Fellesskapet tror Horde har droppet hytte helt i år, fordi folk fant bookingene i fjor»; «Horde er mer forsiktige med hytter i år, fordi folk fant bookingene sist» | [C] `innhold.ts:820`, `515`. **No dated source.** If true it refers to 2024, since 2025 had no hunt |

---

## 6. Horde's other stunts and marketing behaviour

- **The hunt is a variant of Horde Rewards:** «'Jakten på gjeldfriheten' er en ekstrem variant av tjenesten Horde Rewards». [P] Økonomiamatørene TikTok 7293809331521342753
  - The app gamifies saving and debt reduction.
  - Hints are distributed to drive app use through the app, the newsletter, Horde Plus/Jaktus (2024), and Horde AI plus the Kodejakten games (2026: Kill the Bill, Bill Runner, Flappy-Alf, Dartskiven; `innhold.ts:668`, `709`).
  - Referral points: «Verv en venn», 500 points (`innhold.ts:718`).
  - A shop item, «Olivenoljestativ», costs 100 000 points, shipping text «Nesten Helt Hjem». [C] `data/raw/mkekeoooo/PRESISERINGER.md:30`
  - **[I]** Many "hints" are app-engagement devices that gate codes, not geographic data.
- **Budget:**
  - 2023: the whole marketing budget in the box.
  - The stated aim is to spend on customers rather than on Facebook/Instagram ads. [N] inyheter 2023 (via prior_years_early.md L157)
- **Other items found:**
  - Press release «Horde oppretter fond med 10 millioner kroner» (date and content not read). https://www.mynewsdesk.com/no/horde/pressreleases/horde-oppretter-fond-med-10-millioner-kroner-3377039
  - Alf's Medium essay «Horde — Vi er det noen banker frykter og andre banker trenger». https://medium.com/@alfgunnar/horde-vi-er-det-noen-banker-frykter-og-andre-banker-trenger-91c0d34bef6c
  - Podcasts:
    - Impressions EP. 239, «Alf Gunnar Andersen | Gjemte 1 million kr i skogen». https://open.spotify.com/episode/6astUxrzDQZ9fXVit9PXXj and https://www.youtube.com/watch?v=uzEClCHmby8
    - Shifter, 20 Nov 2024. https://open.spotify.com/episode/1pgCpWTv9O9VBXDunh5mDO
    - Lifekeys Talks. https://www.youtube.com/watch?v=qHJii5v5ZQo
  - **None of these was reachable as text.** They are the most likely place for any statement about how sites are chosen.
- **Infrastructure naming [I, trivia]:** Horde's API hosts are named after Bergen mountains (floyen, ulriken, lyderhorn .api.horde.no; rix4uni list). This is not known to relate to hints.

---

## 7. Organizer statements relevant to site choice and behaviour (verbatim where available)

| Year | Statement | Grade and source |
|---|---|---|
| 2023 | «Du må finne kassen og åpne den med riktig kode. Første til mølla vinner (dere kan jobbe i team)» | [P] TikTok 7290894903142288672 |
| 2023 | «Hint kommer gradvis i app, nyhetsbrev og Horde.plus» | [P] TikTok 7290992706124401952 |
| 2023 | Cash removed on Thursday for the safety of searchers | [N] kom24 658791; TV2 16143177 |
| 2023 | Hoped it would last until November | [N] kom24 659296 |
| 2023 (told Nov 2024) | During the first livestream he heard people nearby and feared someone had seen them place the box | [P via N] Shifter podcast summary |
| 2023 | «Dette var stas, og hvem vet hva vi finner på neste gang.» | [P] TikTok 7293120639622253856 |
| 2024 | "We wanted to create even more excitement … with various twists" | [P] mynewsdesk 3320434 (summary) |
| 2024 | Box not placed where it exposes people to danger; rule-breakers disqualified; personal attendance required; two code locks with codes in the hints | [N] Børsen 81303369 via prior_years_early.md L162 |
| 2024 | Kristiansen "was actually the third to arrive, but keeping calm and waiting for his turn was likely the key" | [N] ba.no 2615243 |
| 2026 | «Kassen står ikke i farlig terreng» | [P/C] https://horde.no/gjeldfri/hordejakten/jaktvettreglene via prior_years_early.md L164 |
| 2026 | «Det er ekte lyd på streamen. Men dere husker kanskje tidligere år, da drev vi å trollet litt med lyden.» On live versus delayed: «Ja, det må du prøve å finne ut av.» «Har reven og anda noe med hint å gjøre? Ja, kanskje.» «Kan være at noen av kodene allerede har kommet.» «Kommer en del viktige hint nå i løpet av helgen.» | [P via chat, **not checked verbatim**] `innhold.ts:344`, `1628–1635` |
| 2026 | «Ingen på Hordekontoret vet hvor kassen befinner seg …» | [P] `innhold.ts:677` |
| 2026 | «Kjenner jeg dere riktig så vil dere overanalysere denne videoen» | [P] `innhold.ts:829` |

**Not found anywhere:**
- An explicit statement on **how** Horde chooses sites: landowner permission, region choice, or distance-from-road policy.
- Why Tokke or Kongsberg was chosen.
- Any "near Bergen" versus "Østlandet" rule.

The earlier subagent reported the same gap.

---

## 8. ORGANIZER-BEHAVIOUR PRIOR (main deliverable)

**Basis:** n = 2 hunts, plus 2026 organizer statements. Every number is a judgement prior [I]. It should be combined with 2026 stream evidence (sun, sky, flights, whiteboard) as a **weak, independent** layer; reliability of about 0.5–0.6 is suggested. The machine-readable version is `prior_years_organizer_patterns_files/organizer_prior.json`.

### 8.1 Region

**Pattern**
- Both sites are inland south-central Norway, west or south-west of Oslo: Vest-Telemark and the Kongsberg silver field, about 100 km apart and in different counties.
- Both are forest. Neither is coast, island or high mountain.
- Neither is in Vestland, despite Horde's Bergen base.
- Both are on or near the **E134** corridor [I].
- In 2026 the operational start was **Oslo** («OSLO, SØN KL 04.00»), so the relevant origin is Oslo, not Bergen.
- **Rotation:** each hunt used a new area. Repeating the exact 2023/2024 municipalities (Tokke, Vinje, Kongsberg) is unlikely, about 0.03 in total [I].

**Prior regional mass** (per region, to be spread per area so large regions are not favoured for size):

| Region | Mass |
|---|---|
| Innlandet | 0.33 |
| Buskerud / Telemark / Vestfold | 0.25 |
| Akershus / Østfold | 0.10 |
| Inland Agder | 0.07 |
| Vestland / Rogaland | 0.08 |
| Trøndelag / Møre og Romsdal | 0.12 |
| North (Nordland and beyond) | 0.05 |

- This is compatible with the implemented `hordejakt/layers/organizer_prior.py` `REGION_MASS` (0.35 / 0.30 / 0.07 / 0.10 / 0.13 / 0.05).
- The only change suggested is raising **Akershus/Østfold from 0.07 to about 0.10**, since 2024 was only 1.4–1.5 h from Oslo.

### 8.2 Drive time from Oslo (OSRM car time, optimistic)

- Prior-year values: 2023 about 3.2–3.8 h; 2024 about 1.4–1.55 h.
- 2026 caveats: Anja's "about 7 h" is **not** a distance measure, because the detours were deliberate and she slept. The Monday-versus-Sunday pickup ambiguity is handled in `hordejakt/layers/travel.py`.

| OSRM time from Oslo | Probability |
|---|---|
| Under 1 h | 0.05 |
| 1–2 h | 0.22 |
| 2–3 h | 0.25 |
| 3–4 h | 0.25 |
| 4–6 h | 0.17 |
| Over 6 h | 0.06 |

**Median about 2.9 h.** From Bergen, the earlier sites were about 4.5–7 h. There is no evidence that Horde prefers short drives from Bergen.

### 8.3 Distance from the nearest drivable road (including forest and gravel roads)

**Evidence**
- 2023: car horns from the road were audible at the box, about 15–20 people searched the same small area at night, yet the finder needed more than 16 h, so the box was not visible from the road.
- 2023: the organizer team went back in mid-hunt to swap the cash.
- 2024: several parties reached the box on the same morning.
- 2026:
  - «CA 5–10 MIN Å GÅ FRA BIL»
  - «TROR DET VAR OPPOVER · SISTE 5–10 MIN»
  - «INGEN STIER»
  - «SER KUN SKOG OG KAMERA FRA BOKS»
  - «GIKK 2 MIN INN I SKOGEN» (which walk this was is ambiguous)
  - Anja was **carried** the last stretch.
  - Crew and equipment must be supplied 24/7: portable toilet, lights, camera, power and uplink.
  - Alf: «gå litt … aldri noe farlig, som å krysse en elv».
- **[I]** A 5–10 min uphill walk off-trail at about 1.5–3 km/h, carrying equipment or a person, covers about 150–500 m.

| Distance from road | Probability |
|---|---|
| Under 100 m | 0.05 (not visible from the road) |
| 100–300 m | 0.30 |
| 300–600 m | 0.35 |
| 600–1000 m | 0.18 |
| 1.0–1.5 km | 0.08 |
| Over 1.5 km | 0.04 |

- **Median about 420 m. P(≤ 1 km) ≈ 0.88.**
- Expect the box **above** the parking point (positive rise).
- Expect **no river or stream crossing and no cliffs**, off-trail but walkable.
- Expect a forest road or gravel road with room to park a car or van.

### 8.4 Terrain and elevation

**Terrain**
- Forest ≈ 0.95 (both years, plus 2026).
- Above the treeline ≈ 0.03.
- Coast or island ≈ 0.02. The 2026 whiteboard also says «INGEN FERGE · KUN BIL».
- Dangerous terrain ≈ 0.
- Bog or *myr* nearby is common (2023).

**Elevation**
- No prior-year elevation is published and **no prior-year elevation hint is known**.
- Inferred prior-year bands: 2023 about 450–900 moh; 2024 about 300–750 moh.

| Elevation (moh) | Probability |
|---|---|
| Under 200 | 0.10 |
| 200–400 | 0.22 |
| 400–600 | 0.28 |
| 600–800 | 0.25 |
| 800–1000 | 0.12 |
| Over 1000 | 0.03 |

- This is broad and **should not be used to confirm or reject the 2026 «2,7 eiffeltårn» = 810/891 moh reading**. See §9.

### 8.5 Hint style and how literal numbers were

| Hint class | Precedents | Behaviour | Prior |
|---|---|---|---|
| Official bare number | 2023 «2412»; 2024 code word; 2026 «terje» → 5008 (Horde's postcode, Lars Hilles gate 20A, 5008 Bergen); «072» = 2024 prize digits; Kodejakten code | **Lock codes or self-referential Horde numbers, not coordinates** | P(code) 0.65 · P(literal geography) 0.25 · P(other/troll) 0.10 |
| Pictogram or wordplay | 2023 «kommunevåpen med dyr»; 2026 animals (rev, kråke, ekorn, and), anagrams | Region or municipality-level pointer at best. The 2026 community tested the coat-of-arms mapping (Froland = ekorn, Vegårshei = rev) and dropped it [C] | P(meaningful at municipality level) ≈ 0.5 |
| Landscape photo or video | 2023 power-line video | Literal local feature | ≈ 0.8 literal |
| Participant's first-hand notes (2026 whiteboard) | «5–10 MIN», «OPPOVER», «INGEN STIER», «KAMERA 41 ØST / 118–120 GR ØST» | Literal but imprecise. She does not know the place | ≈ 0.9 truthful |
| Live sky, weather, sun or aircraft on video | 2023 snow match (decisive); crowd flight analysis | Truthful, unless the video is delayed or replayed | ≈ 0.85 |
| Stream audio | 2023 horns were live; Alf's admitted earlier trolling; 2026 loops 22–48 h apart (default.no) | Unreliable | P(usable for location) ≈ 0.25 |
| Explicit official text hint that is deliberately false about location | none known | – | ≈ 0.10 |
| Late decisive hint | both years, around day 5–6 | Deliberate pacing | – |

### 8.6 Trolling and countermeasures ("they fix last year's exploit")

| Previous exploit or problem | Countermeasure |
|---|---|
| 2023 cash in the box drew crowds (safety) | 2024 code word in a golden envelope. 2026 cash is back, but a person and crew are on site |
| 2023 honk-homing on the live audio | 2026 audio "real" but live or delayed is unstated; default.no finds loops. **[I] Horns or shouting will probably not confirm proximity in 2026** |
| 2024 several finders at the box at once | 2026 queue plus 5 h quarantine, 3 locks, codes gated in the app |
| Cabin or lodging bookings traced last time [C] | 2026: no cabin («INGEN HYTTE I NÆRHETEN SOM JEG VET OM ELLER SER», [W] 24.09 17:20); portable toilet |
| Leak risk from staff or the person | «Ingen på Hordekontoret vet …»; Anja blindfolded, driven on detours, carried in |
| Community over-analysis | Horde anticipates it («… overanalysere denne videoen»), plants canned answers (Horde AI; the unconfirmed FROLAND reply), and nods to default.no on the whiteboard |

**Takeaway:**
- Expect **noise channels** (sound, drive time, props) to be manipulated. P(some sensory channel manipulated) ≈ 0.5.
- **Official location statements** have so far been truthful.

### 8.7 Timing and pacing

- 2023: 5.8 days. 2024: 5.9 days to find, 6.2 days to open. Both ended at the **weekend of day 6**, after a **late decisive hint**.
- 2026 day 6 from Mon 21 Sep 06:50 is **Sat 26 Sep evening to Sun 27 Sep midday**.
- Alf promises «viktige hint … i løpet av helgen».

| 2026 outcome | Probability |
|---|---|
| Found by Sun 27 Sep 23:59 | ≈ 0.45 |
| Found by Wed 30 Sep | ≈ 0.75 |
| Later than 7 Oct | ≈ 0.10 |

- This is lower than a naive 6-day rule because 2026 adds friction: 3 locks, quarantine, and a human in the box, which supports a longer show.

### 8.8 Logistics constraints implied by organizer behaviour [I]

- **Car access for crew.** In 2023 and 2024 Horde staff drove in themselves. In 2026 there are shift changes, food, a portable toilet, and a break place "without windows and wifi" (container, camper or tent; `innhold.ts:812–821`).
- **Uplink for a 24/7 video stream.** Either mobile coverage (4G/5G) or satellite (e.g. Starlink). The 2023 stream was self-hosted HLS and crashed under load, which was a server issue.
- **Landowner tolerance.** Not documented, but cultural-heritage land (2024) and forest land (2023) were used. Expect ordinary private or commercial forest where access roads exist. Active logging near the box in 2026 (`whiteboard_log.md` WB-45) fits a forest road network.

### 8.9 Who wins

- **Locals or people nearby won both times.**
  - 2023: Sundklakk was working at Åmot, about 1–10 km from the site, and recognised the weather on the stream.
  - 2024: "Tre menn fra Kongsberg" per Laagendalsposten, although the named winner is a Nordmøre native living in Eastern Norway.
- Teams that cooperate win. In 2023 strangers teamed up; in 2024 the winner had phone helpers who solved the code while he waited.
- **[I] Implication:** a live comparison of the stream's sky and weather with people spread across the candidate regions is the proven winning technique. So is having the codes solved **before** arriving.

---

## 9. Implications for 2026 (concrete)

1. **Road filter.** Keep candidates within about 1 km of a car-drivable road or forest road, weighted to about 150–600 m, uphill from the parking point, with no stream crossing on the obvious approach.
2. **Do not let drive time or "7 h" decide the region.** The earlier sites were 1.4–3.8 h from Oslo. A 7-hour drive with detours is compatible with anything 1–5 h from Oslo, including the Hamar–Løten–Elverum–Rena and Ringsaker belts the 2026 community favours, and also Buskerud/Telemark.
3. **Treat numeric hints as codes first.** For «2,7 eiffeltårn stablet oppå hverandre», which yields 810–891:
   - P(elevation) ≈ 0.35–0.40 as a soft weight, not a hard filter.
   - P(lock code 0810/0891/0875 or a 5-digit variant) ≈ 0.30.
   - P(other) ≈ 0.30.
   - Keep a fallback band of about 400–800 moh, where the earlier sites most likely were.
   - Every earlier numeric hint whose use is known was a code, and no earlier hunt is known to have used an elevation hint.
4. **Discard audio for localisation.** This is the countermeasure pattern in §8.6. Weight sky, sun, weather and aircraft, which cracked 2023.
5. **Expect a decisive geographic hint on Sat 26 – Sun 27 Sep.** Be positioned centrally to the leading candidate areas and have the codes ready. In 2024 the winner was the one who had the code, not the first to arrive, and in 2026 a failed attempt costs 5 h of quarantine.
6. **Low weight on reusing the 2023 or 2024 municipalities** (about 0.03 total). The "118° line from Bergen passes about 20 km from Tokke" observation (`innhold.ts:527`) is not supported by the prior-year pattern.

---

## 10. Contradictions and corrections

1. **2023 find time.** Børsen says «like før klokken 02 natt til mandag». Rha and noblad say "at three o'clock at night" and «I tre-tiden hørte vi folk som ropte og hoiet».
   - **Resolution:** the @crytomade TikTok "1 million er funnet" was posted 02:16 CEST, so the find was **before 02:16**. The "three o'clock" line refers to when shouting was heard.
   - This corrects prior_years_early.md §7, which settled on "02:00–03:00". The evidence now favours **about 01:50–02:15 CEST**.
2. **2024 winner identity.** ba.no and kom24 name **Joakim Kristiansen**, a Nordmøre native living in Eastern Norway. Laagendalsposten (via the earlier file) says «Tre menn fra Kongsberg ble 1 093 072 kroner rikere». **Unresolved.** One possibility is that Joakim lives in Kongsberg and shared with two helpers.
3. **2024 order of attempts.** He was "third to arrive" (ba.no) versus "fourth person to try opening" / "three people tried and failed before Joakim" (Børsen summaries). These are consistent if he let others try first.
4. **2024 launch date.** The press release and Alf's TikTok are Mon 29 Apr 2024. Horde's "Jakten er i gang!" TikTok is Tue 30 Apr 10:46. **The launch was 29 Apr.** The 30 Apr post is a follow-up.
5. **2023 prize after removal.** "Replaced by a code word" versus "replaced with a bank transfer". **Both are true:** a code word in the box entitles the finder to a transfer.
6. **Duration of the 2023 hunt.** The earlier file reports that vervekodesiden and praktiskinfo summaries say "two weeks". This is **wrong**; primary news gives Tuesday to Monday, 6 days (rha: «søket varte i seks dager»).
7. **Summary mix-ups.** Some summaries attach Sigurd and Hans Inge or 1 078 218 kr to Kongsberg. **Wrong**: 2023 was Tokke with 1 078 218 kr; 2024 was Kongsberg with 1 093 072 kr.
8. **"Hordejakten 2025."** It does not exist. 2026 is the third hunt.
9. **"16 hours"** is Sundklakk's personal search time, not the hunt's duration of about 139 h.
10. **Magnus pins** (59.444, 7.989) and (59.668, 9.65) are **municipality or town-centre placeholders**, not find spots. Any model feature using "distance to the 2023 box" is invalid.
11. **"Both in forest with a car and a short walk"** (mkekeoooo p.3; Magnus «Skog, bil og litt gange») is a community summary. For 2023 it is supported by the horn evidence. For 2024 only by the "several finders on one morning" inference.
12. **The "cabin bookings found last time" claim** (`innhold.ts:515`, `820`) has no dated primary source. With no 2025 hunt, «i fjor» ("last year") must mean 2024 if it is true at all.

---

## 11. Open questions

- Exact coordinates, elevation, parking spot and walking distance for 2023 and 2024.
  - Possible sources: TV2, Varden/VTavisa and Laagendalsposten article bodies; the @crytomade, @jaktjegeren and horde.app TikTok videos; the 2023 HLS recordings, if `danielmb` ever published them (the repo has only code).
- The full 2024 hint list, and whether the 2024 countdown ended in a location reveal.
- Which year's sound was "trolled", and how.
- Whether the 2023 coat-of-arms animal was Tokke's bear (or Vinje's arms), and the exact «2412» code use.
- Any statement from Alf on how sites are chosen. The Shifter (Nov 2024), Impressions EP. 239 and Økonomiamatørene ep. 175 audio were not reachable.
- The content of Horde's 2026 article «– En tydelig sammenheng» (https://horde.no/artikler/hordejakten-2026) and the campaign terms (https://horde.no/gjeldfri/hordejakten/vilkaar). Both were blocked; only titles were seen.

---

## 12. Decoded post timestamps (all CEST)

| ID | Posted | Post |
|---|---|---|
| TikTok 7290788736235785505 | Tue 17 Oct 2023 07:03 | Horde, 2023 launch |
| TikTok 7290894903142288672 | Tue 17 Oct 2023 13:55 | Horde, «Du må finne kassen og åpne den med riktig kode» |
| TikTok 7290992706124401952 | Tue 17 Oct 2023 20:15 | Alf, rules and hint channels |
| TikTok 7291639715088977184 | Thu 19 Oct 2023 14:06 | TV2 |
| GitHub danielmb/hordejakten commit | Thu 19 Oct 2023 16:30:57 +0200 | HLS recorder for bsstorm.horde.no |
| TikTok 7292737938960534816 | Sun 22 Oct 2023 13:07 | Horde, "Update på Hordejakten" |
| TikTok 7292941281032981793 | **Mon 23 Oct 2023 02:16** | Viewer, "1 million er funnet" |
| TikTok 7292963813295508769 | Mon 23 Oct 2023 03:44 | Viewer |
| TikTok 7293120639622253856 | Mon 23 Oct 2023 13:52 | Horde, congratulations to Hans Inge and Sigurd |
| TikTok 7293809331521342753 | Wed 25 Oct 2023 10:25 | Økonomiamatørene |
| TikTok 7363199855700888864 | Mon 29 Apr 2024 10:16 | Alf, 2024 launch |
| TikTok 7363578766704037152 | Tue 30 Apr 2024 10:46 | Horde, «Jakten er i gang!» |
| TikTok 7363954970053315873 | Wed 1 May 2024 11:06 | Horde, «Har du Horde-appen, kan du finne kassen!» |
| TikTok 7364040181592116512 | Wed 1 May 2024 16:36 | Horde, «Du vet aldri hva du treffer på #hordejakten hint?» |
| TikTok 7365418050637663521 | Sun 5 May 2024 09:43 | Horde |
| TikTok 7365482640843017505 | Sun 5 May 2024 13:54 | Horde, «Hordejakten er ikke over!» |
| X 2102086838630453645 | Mon 21 Sep 2026 19:25 | MrMekker, 2026 launch |

**Hunt durations [I]:**
- 2023: 17 Oct 07:00 to 23 Oct about 01:50, which is 5 d 18 h 50 min = **5.78 d**.
- 2024: 29 Apr 10:16 to 5 May about 09:00 to find, **5.95 d**; to about 16:00 to open, **6.24 d**.

---

## 13. Relation to prior_years_early.md

**Re-confirmed independently in this pass (own searches):**
- 2023:
  - Tokke, Telemark.
  - 1 078 218 kr; Sundklakk and Josdal, strangers who teamed up and split.
  - Just before 02:00 on the Monday night, with 16+ h of searching.
  - Car horns: Sundklakk heard his own horn on the stream.
  - He threw up and fell into a bog.
  - Cash removed on Thursday and replaced by a code word or transfer.
  - Hoped it would last to November; about 50 000 new users.
  - About 20 searchers present, shouting around 03:00.
  - Sundklakk was working in Åmot and saw the same snow.
  - The crowd analysed weather, wind, birds, power lines and air traffic; the stream crashed.
  - The 2023 box had a code.
- 2024:
  - Press release 29 Apr; countdown; Jaktus.
  - Golden-envelope code word worth 1 093 072 kr.
  - "Near the silver mines in Kongsberg"; found on a Sunday morning by several people.
  - Joakim Kristiansen was third to arrive and waited for the code; three people failed before him.
- 2025: no hunt ("twice previously, 2023 and 2024"; Shifter: "twice").
- 2026: Anja was blindfolded and does not know where she is.

**New in this pass:**
- The 2023 HLS stream infrastructure (§3.8).
- The @crytomade 02:16 timestamp, which corrects the find time.
- The launch-day «riktig kode» TikTok, which shows 2023 already had codes.
- Vinje/Tokke border geometry and OSRM times.
- The E134 corridor observation.
- The "fix last year's exploit" pattern (§8.6).
- The locals-win pattern (§8.9).
- A revised numeric prior (§8, and the JSON file).

**Carried over unverified** (single-source, earlier subagent):
- «2412» on the Thursday.
- «kommunevåpen med dyr» and the power-line video.
- The police agreement.
- Josdal from Sirdal.
- Laagendalsposten's «Tre menn fra Kongsberg».
- Økonomiamatørene ep. 175 on 3 May.
- The silver-mine field elevations.
- Anja's quotes from Børsen 85183299 and 85185489.
- The Ringsaker Blad "Anja fra Brumunddal".
- The 2024 queue system "worked well".

---

## 14. Search log (this pass; WebSearch, 41 successful queries)

1. Horde gjemte en million i skogen funnet
2. Hordejakten 2023 1 078 218 kr funnet
3. Hordejakten 2024 vinner kasse skogen
4. Sigurd Sundklakk Hans Inge Josdal millionen Tokke (no useful results)
5. Horde millionen funnet Joakim Nordmøre koder kasse 2024
6. Hordejakten 2025 funnet vinner
7. "Hordejakten" 2025
8. Horde million Kongsberg sølvgruvene funnet kasse
9. "Utenfor boksen: arrangørlogikk" hordejakten issue tidligere år Tokke Kongsberg
10. Fant over én million i skogen Børsen Tokke Telemark Horde kasse
11. "Sigurd og Hans fant millionen" kastet opp
12. "Millionen i skogen er funnet" slik klarte de å løse gåten
13. Over en million kroner funnet i skogen i Telemark ta.no Horde
14. Horde million Vinje Tokke grensen kasse hint høyde meter over havet
15. reddit Horde million skogen hint livestream 2023
16. "Jakten på gjeldfriheten" Horde hint
17. "Vant million etter nervedrama i skogen"
18. "I tre-tiden hørte vi folk som ropte og hoiet" million skogen
19. "Millionjakta er i gang" Skutt i været Horde
20. Hordejakten 2024 hint Kongsberg gruve kasse funnet søndag morgen koder
21. Horde gjennomsiktig kasse person inni skogen 2025 jakten
22. kom24 "Hordejakten er tilbake" …
23. Alf Gunnar Andersen Horde hvordan velger vi stedet kassen skogen intervju
24. mynewsdesk Horde "Hordejakten er tilbake" 1,1 million skjult i norsk natur
25. "Horde har gjemt én million kroner i norsk natur" pengejakten
26. Joakim Kristiansen Horde million Kongsberg
27. "Spenningsnivået stiger i Hordejakten" …
28. "Slik ser en drøy million i skogen ut" Horde
29. Horde million skogen 2023 hint kraftlinje fly fuglelyd analysere livestream Tokke
30. "Horde" million skog site:reddit.com (no Reddit hits)
31. NRK Horde million skogen Tokke kasse funnet kodeord
32. "Gjemte en million kroner i skogen – nå er pengene fjernet"
33. "Har gjemt over en million i kontanter ett eller annet sted i Norge" hint
34. tv2 "Fjernet én million kroner fra skogen" Horde
35. Horde millionen Tokke Sundklakk tutet bilhorn livestream hørte
36. Horde million funnet Høydalsmo OR Dalen OR Åmot OR Rauland Telemark kasse skogen 2023
37. vtavisa Horde million Tokke Vinje kassen funnet
38. laagendalsposten Horde million Kongsberg kasse funnet skogen 2024
39. Sundklakk Åmot Vinje snø livestream Horde kassen
40. "Noen har funnet Horde-millionen i skogen" Børsen studio
41. Horde Jaktus AI hint 2024 Hordejakten gullkonvolutt kodeord

**Refused because the session budget of 200 was exhausted:**
- "Åpnet million-boksen"
- seher "Million-boksen: Her gjør de funnet"
- Kongsberg Saggrenda / Kongens gruve / Knutehytta

**GitHub searches:**
- repos "hordejakten" found fordelabs/hordejakten (empty), danielmb/hordejakten (2023 recorder), and the two 2026 repos.
- code "bsstorm.horde.no".
- code "Tokke Kongsberg horde kassen" (only the Magnus hits).

---

## 15. Source index

**Primary: Horde and Alf**
- https://www.tiktok.com/@horde.app/video/7290788736235785505
- https://www.tiktok.com/@horde.app/video/7290894903142288672
- https://www.tiktok.com/@alf.gunnar/video/7290992706124401952
- https://www.tiktok.com/@horde.app/video/7292737938960534816
- https://www.tiktok.com/@horde.app/video/7293120639622253856
- https://www.tiktok.com/@okonomiamatorene/video/7293809331521342753
- https://www.tiktok.com/@alf.gunnar/video/7363199855700888864
- https://www.tiktok.com/@horde.app/video/7363578766704037152
- https://www.tiktok.com/@horde.app/video/7363954970053315873
- https://www.tiktok.com/@horde.app/video/7364040181592116512
- https://www.tiktok.com/@horde.app/video/7365418050637663521
- https://www.tiktok.com/@horde.app/video/7365482640843017505
- https://www.mynewsdesk.com/no/horde/pressreleases/11-million-skjult-i-norsk-natur-hordejakten-er-tilbake-3319716
- https://www.mynewsdesk.com/no/horde/pressreleases/spenningsnivaaet-stiger-i-hordejakten-kassen-har-begynt-aa-telle-ned-3320434
- https://www.mynewsdesk.com/no/horde/pressreleases/horde-oppretter-fond-med-10-millioner-kroner-3377039
- https://horde.no/blogg/jakten-pa-gjeldfriheten-er-i-gang/
- https://horde.no/blogg/slik-ser-en-droy-million-i-skogen-ut/
- https://horde.no/gjeldfri/hordejakten
- https://horde.no/gjeldfri/hordejakten/vilkaar
- https://horde.no/gjeldfri/hordejakten/jaktvettreglene
- https://horde.no/artikler/hordejakten-2026
- YouTube 2023: https://www.youtube.com/watch?v=tWoD9d4eFII, https://www.youtube.com/watch?v=aN5McWdV2qI, https://www.youtube.com/watch?v=u1aJpanXt9o, https://www.youtube.com/watch?v=ThO-OsWvoL8 (not viewed)
- Podcasts:
  - https://open.spotify.com/episode/1pgCpWTv9O9VBXDunh5mDO (Shifter)
  - https://open.spotify.com/episode/6astUxrzDQZ9fXVit9PXXj and https://www.youtube.com/watch?v=uzEClCHmby8 (Impressions EP. 239)
  - https://open.spotify.com/episode/178hAIH0Mcypgvvq67atBm (Økonomiamatørene ep. 175)

**News, 2023**
- https://borsen.dagbladet.no/nyheter/har-gjemt-n-million-i-norsk-skog/80366517
- https://borsen.dagbladet.no/nyheter/fant-over-n-million-i-skogen/80385711
- https://borsen.dagbladet.no/nyheter/sigurd-og-hans-fant-millionen-kastet-opp/80389223
- https://borsen.dagbladet.no/nyheter/vill-pengejakt-tar-grep/80370921
- https://www.tv2.no/nyheter/innenriks/fjernet-en-million-kroner-fra-skogen/16143177/
- https://www.kom24.no/ellevilt-markedsforingsstunt-har-gjemt-en-million-kroner-ute-i-skogen/657713
- https://www.kom24.no/alf-gunnar-anderse-horde-markedsforing/gjemte-en-million-kroner-i-skogen-na-er-pengene-fjernet/658791
- https://www.kom24.no/alf-gunnar-og-kollegaene-gjemte-en-million-kroner-i-skogen-na-er-pengene-funnet/659296
- https://www.ta.no/over-en-million-kroner-funnet-i-skogen-i-telemark/s/5-50-1754839
- https://www.op.no/over-en-million-kroner-funnet-i-skogen-i-telemark/s/5-36-1509193
- https://www.rha.no/fant-en-million-i-skogen-i-tre-tiden-horte-vi-folk-som-ropte-og-hoiet/s/5-70-476728
- https://www.noblad.no/fant-en-million-i-skogen-i-tre-tiden-horte-vi-folk-som-ropte-og-hoiet/s/5-56-746351
- https://www.amta.no/fant-en-million-i-skogen-verdige-vinnere/s/5-3-1551361
- https://www.kvinnheringen.no/fant-en-million-i-skogen-verdige-vinnere/s/5-27-474281
- https://www.nettavisen.no/nyheter/fant-en-million-i-skogen-verdige-vinnere/s/5-95-1408921
- https://www.ba.no/fant-en-million-i-skogen-verdige-vinnere/s/5-8-2418443
- https://inyheter.no/18/10/2023/har-gjemt-en-million-kroner-i-norsk-skog/
- https://sosialnytt.com/millionen-i-skogen-er-funnet-slik-klarte-de-a-lose-gaten/
- https://sosialnytt.com/har-gjemt-over-en-million-i-kontanter-ett-eller-annet-sted-i-norge-folk-far-mann-av-huse-i-pengejakten/
- https://www.dagens.no/nyheter/breaking-fant-en-million-kroner-gjemt-i-skogen
- https://www.tiktok.com/@tv2.no/video/7291639715088977184
- https://www.tiktok.com/@crytomade/video/7292941281032981793

**News, 2024**
- https://borsen.dagbladet.no/nyheter/ny-million-gjemt-i-norsk-skog/81303369
- https://borsen.dagbladet.no/nyheter/millionjakta-er-i-gang-skutt-i-vaeret/81334871
- https://borsen.dagbladet.no/nyheter/apnet-million-boksen/81357015
- https://borsen.dagbladet.no/studio/borsenstudio/608?post=162361
- https://www.ba.no/vant-million-etter-nervedrama-i-skogen/s/5-8-2615243
- https://www.kom24.no/alf-gunnar-andersen-horde-markedsforing/ny-million-gjemt-i-skogen/713720
- https://www.dagens.no/innland/ny-vill-skattejakt-har-nok-en-gang-gjemt-en-million-i-norsk-skog
- https://www.laagendalsposten.no/alf-gunnar-la-ut-over-n-million-i-skauen-pa-kongsberg-i-dag-ble-pengene-funnet/s/5-64-1415829 (via prior_years_early.md)
- https://www.seher.no/video/her-finner-de-million-boksen/QkcCmXVr (title only)

**News, 2026**
- https://borsen.dagbladet.no/nyheter/nytt-sjokkstunt-fra-norsk-selskap/85179562
- https://borsen.dagbladet.no/nyheter/anja-29-jaktes-av-hele-norge/85183299 (via prior_years_early.md)
- https://borsen.dagbladet.no/nyheter/anja-29-snakker-ut-absurd/85185489 (via prior_years_early.md)
- https://x.com/MrMekker/status/2102086838630453645

**Community and local**
- https://github.com/mkekeoooo/hordejakten-2026/issues/9 (search summary only)
- `data/raw/magnus/src/data/innhold.ts`: L119, L150, L335, L344, L394–399, L515, L527, L668, L677, L685, L709, L718, L812–821, L829, L848, L1038, L1076–1077, L1251, L1457–1467, L1620, L1628–1635
- `data/raw/magnus/public/data/drivetime.json` and `kommunevurdering.json`
- `data/raw/mkekeoooo/rapport/Hordejakten_2026_fullstendig_rapport.pdf` p.3
- `data/raw/mkekeoooo/PRESISERINGER.md:30`
- `evidence/sources/whiteboard_log.md` L97–101, L123, L126, L134–135, L242–265
- `evidence/sources/prior_years_early.md`
- https://github.com/danielmb/hordejakten (commit feedab3, 2023-10-19)
- https://raw.githubusercontent.com/rix4uni/BugBountyData/main/data/horde.no.txt
