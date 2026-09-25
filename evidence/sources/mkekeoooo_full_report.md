# mkekeoooo "Hordejakten 2026 – fullstendig forskningsrapport": full extraction with correction status

Durable record of **everything** in the 22-page full report from the mkekeoooo analysis archive, cross-referenced against the repo's own later corrections (README.md, PRESISERINGER.md). The short report and the `bevis/claude-2026-09-25` branch are used only to supplement or check it.

---

## 0. Source identification

| Item | Value |
|---|---|
| File | `/home/user/test/data/raw/mkekeoooo/rapport/Hordejakten_2026_fullstendig_rapport.pdf` (22 pages) |
| SHA-256 | `b3b1320f90d02245f83eeda999a68ea21f32a47de3a902730461ba323717b9b2` |
| PDF metadata | Title "Hordejakten 2026 – fullstendig forskningsrapport"; Author "Hordejakten 2026 – åpen analyse"; Producer ReportLab; CreationDate 2026-09-25 08:20:12 UTC (= 10:20 CEST) |
| Printed date | "25. september 2026" on every page header |
| Companion | `rapport/Hordejakten_2026_kortrapport.pdf` (12 pages, SHA-256 `bea063f6…b9bdb27ff`, created 08:20:13 UTC). Its extra details are in §30 |
| Repo | mkekeoooo/hordejakten-2026, main @ `d1fbac0` (2026-09-25 04:43 −0700 = 13:43 CEST, "Oppdater regionale avklaringer og dokumenter nytt olivin-spor") |
| Authorship | KILDER.md:3: «Rapportene er satt sammen av Claude på grunnlag av brukerens arbeid og utveksling med Codex.» ("The reports were compiled by Claude from the user's work and exchanges with Codex.") The whole report is **AI-assisted analysis (model output and interpretation)**. It is not primary evidence |
| Publication status | README.md:7: «Ingen plassering eller region er bekreftet. Den tidligere nummererte kandidatlisten er under revisjon.» ("No location or region is confirmed. The earlier numbered candidate list is under revision.") The PDF is kept unchanged as history; PRESISERINGER.md:3 says the notes "følger de to originale PDF-rapportene og endrer ikke originalfilene" (accompany the two original PDF reports and do not change the original files) |
| Extraction method | pypdf text extraction of all 22 pages, plus PyMuPDF renders of every page (110–300 dpi) to read figure labels, map coordinates and the O1–O10 legend. Full-resolution PNGs in `figurer/` were also checked |

**Time convention.** The report's whiteboard times are **stream time (strømtid)** in CEST. The report says stream time runs «ca. 22–45 sekunder etter virkeligheten» ("about 22–45 seconds behind reality", p.3; Appendix A p.22). All other times are CEST unless noted.

---

## 1. Evidence-class legend used below

- **[P-BOARD]**: primary. Anja's whiteboard text, as transcribed in the report. The report says transcriptions are «bygger på default.no, fellesskapet og egne kontroller» ("based on default.no, the community and our own checks", p.3).
- **[P-STREAM]**: primary. Something visible on the stream (pixels, gestures, light).
- **[P-ORG]**: organizer (Horde) statement, campaign page or rules.
- **[P-APP]**: Horde app or app AI-assistant response.
- **[NEWS]**: press interview (Børsen/Dagbladet).
- **[C-OBS]**: community observation, e.g. a flight track matched to a gesture.
- **[INT]**: interpretation or theory.
- **[MODEL]**: model output (terrain, forest or weather grids, default.no fusion).
- **[RETRACTED] / [CORRECTED] / [SOFTENED] / [DISPUTED]**: status after the report's own errata or the later README/PRESISERINGER.

---

## 2. Bottom line

1. **What the PDF claims.** Five "check-order" sites, all in Stor-Elvdal near Evenstad, Østerdalen: (1) Myklebysæterveien vest 61.3995, 11.0316; (2) Madsskardveien traktorvei 61.4443, 11.1234; (3) Sørlige Messelt 61.4571, 10.8362 and 61.4545, 10.8406; (4) Madsskardveien øst 61.4518, 11.1428; (5) Jernvinneveien 61.4351, 11.1435. The PDF itself says «Rekkefølgen er en kontrollrekkefølge, ikke sannsynligheter» ("the order is a check order, not probabilities") and «Ingen plassering er bekreftet» ("no location is confirmed").
2. **What the repo later says.** The ranking is **not current** (README:7, :43; PRESISERINGER:7). The **region itself is not confirmed** (README:7, :13). Several load-bearing tests have been demoted:
   - **Temperature** is no longer a hard filter (README:15).
   - The **pointing gesture** no longer selects a region (README:14).
   - **Weather exclusions** of west/south Norway were unverified model output (README:14).
   - **Morning sun** is under review (README:16, :47).
   - **Road direction ✓ for candidate 1** is unjustified, since its road bears ~94° (README:18; PRESISERINGER:12).
3. **Biggest in-report retraction.** The B3 "stump" distance of 17–44 m. It drove the earlier C07/C23 (Gålaveien/Messelt) picks and is now withdrawn (p.10, p.18). Without it the terrain test barely discriminates: 1,000–7,500 of 7,525 positions per area pass (p.12).
4. **Later contradictions of the PDF's own checkmarks.**
   - **Candidate 5 (Jernvinneveien), morning sun.** The later terrain horizon at the 5a/5b/5c markers is 8.4° / 7.3° / 6.6° toward az 98.8° (Codex reproduction, README:16; PRESISERINGER:10). All three exceed the PDF's own ~6.5° exclusion threshold (p.8), yet the PDF's checklist gives candidate 5 a ✓ for «Morgensol kl. 07.51».
   - **Candidate 1, forest test.** The bevis-branch re-run of the PDF's K0–K4 at the published marker gives candidate 1 **0/25** passing positions, with K0 canopy median 10.4 m against a <3 m requirement (`bevis/.../horisont/kkrav_resultat.txt`). This is a model output and is **not** mentioned in the README.
5. **Where the whole approach is weakest.**
   - The region choice rests on flight gestures (disputed), dryness (a model), temperature (demoted) and default.no's fusion model (shared premises).
   - Only 13 areas of 1.6 × 1.6 km were examined (p.9, p.18).
   - No field visit was made (p.18).

---

## 3. Correction and retraction register

| # | Claim in the full PDF (page) | Status | Where corrected |
|---|---|---|---|
| R1 | B3 «bakkant av lysningen» ("back edge of the clearing") distance 17–44 m, from a supposed 0.25–0.5 m stump 13–16 px wide (p.10, p.11) | **[RETRACTED]** in the PDF itself. The bright spot is «trolig motlyst løv» ("probably back-lit foliage"), and all positions rejected on that basis were re-admitted | PDF p.10, p.18; README:58; PRESISERINGER:28 («objektidentitet og diameter er ikke sikkert bestemt… Historiske figurer kan vise gamle ringer eller utvalg» — "object identity and diameter are not reliably determined… historical figures may show old rings or selections"); figurer/README.md:40 |
| R2 | Ray intersections at 25 cm steps (first version) | **[CORRECTED]** to 1 cm steps. Example: A2 went from 1,324 to 1,229 positions | PDF p.12, p.18. PRESISERINGER:26 adds that a 1 cm step «gir ikke terrengdata med 1 cm fysisk nøyaktighet» ("does not give terrain data with 1 cm physical accuracy") |
| R3 | Earlier claim that Gålaveien fits a low camera | **[RETRACTED]**. It was based on coarse 5 m profiles | PDF p.18 |
| R4 | Robustness merged as maximum instead of union | **[CORRECTED]** | PDF p.18 |
| R5 | Tractor roads counted as drivable | **[CORRECTED]**. Now reported separately; missing data gives «ukjent» ("unknown") | PDF p.18 |
| R6 | «alle» ("all") Gålaveien positions fail morning sun | **[CORRECTED]**. 12 pass the sun test, but none of those has access | PDF p.18; PRESISERINGER:23 |
| R7 | Community sunrise times | **[CORRECTED]**. The community's times were 3–4 min too early | PDF p.18 |
| R8 | Ranking 1–5 as the recommended check order (p.1, p.16) | **[SOFTENED / NOT CURRENT]**: «Den historiske kontrollrekkefølgen er ikke en vedtatt, gjeldende rangering» ("the historical check order is not an adopted, current ranking"). No new numbered ranking has been adopted. Birkebeinerveien, Gålaveien, Messelt and punkt 7 remain under open investigation | README:7, :31–43; PRESISERINGER:7 |
| R9 | Region = Østerdalen around Evenstad (p.1, p.9) | **[SOFTENED]**: «Regionen må holdes åpen» ("the region must be kept open"). The 21.09 flight event has uncertain object identity and delay. Codex reproduced Claude's flight table, but it «bekrefter ikke Evenstad som region» ("does not confirm Evenstad as the region") | README:7, :13; PRESISERINGER:9 (issue #5) |
| R10 | Flights used to pick the region (p.5–6) | **[SOFTENED]**: «En arm nesten loddrett i bildet er ikke en måling av flyets høydevinkel. Claude har trukket tilbake den slutningen… gesten ikke alene velger eller utelukker region» ("an arm almost vertical in the image is not a measurement of the plane's elevation angle. Claude has retracted that inference… the gesture alone neither selects nor excludes a region"). Separately, the bevis branch notes the 21:29:38–53 pointing may have been at a **shooting star**: she signalled «stjerneskudd» at 21:27:42 and chat asked her to point at 21:29:10 | README:14 (issue #9); bevis README "Tvetydighet" |
| R11 | Weather: «Dette peker mot Østlandet innenfor» ("this points to inland Eastern Norway") from rain totals; national weather test (p.7) | **[SOFTENED]**: «De tidligere værutelukkelsene av vest og sør var modellbaserte og ikke verifisert mot observasjoner; de brukes ikke som harde grenser» ("the earlier weather exclusions of west and south were model-based and not verified against observations; they are not used as hard limits") | README:14 |
| R12 | Temperature ✓/✗ column; Messelt and punkt 7 marked ✗ (p.7, p.16) | **[SOFTENED]**: «Temperatur skal ikke være et hardt filter… Messelt og andre steder skal ikke forkastes alene fordi uteluftsmodellen er kaldere enn tavleverdien» ("temperature must not be a hard filter… Messelt and other sites must not be rejected just because the outdoor-air model is colder than the board value"). Also: «dagmaks» should not automatically be read as the full-day maximum, and box-interior temperature is not the same observation as outdoor air | README:15, :48; PRESISERINGER:8, :24 (issue #3) |
| R13 | Morning-sun test (first direct sun at 07:51; horizon ≤ ~6.5°) excludes A1/A2 and passes candidates 1–5 (p.8, p.16) | **[UNDER REVIEW / PARTLY CONTRADICTED]**. The 07:51 time came from default.no. Claude later proposed crown and trunk light **earlier** than 07:51. Codex reproduced horizons of **8.4° / 7.3° / 6.6°** at Jernvinneveien 5a/5b/5c toward 98.8° from 1.5 m, with obstructions 800 / 1,050 / 1,300 m away. That is above the PDF's 6.5° line, yet candidate 5 got ✓. The A1/A2 «utelukket» ("excluded") wording is conditional | README:16, :47; PRESISERINGER:10, :23 (issue #2) |
| R14 | Candidate 1 checklist «Veiretning ca. 130°» ✓ (p.16) | **[CORRECTED]**: «Kandidat 1s vei ligger omtrent mot 94°, og får ikke ubetinget samsvar» ("candidate 1's road lies at about 94° and does not get unconditional agreement"). My own geodesic check confirms 94° from the box to the road point (§26). The PDF's p.1 text itself says «veien kommer fra øst» ("the road comes from the east") | README:18; PRESISERINGER:12 (issue #4) |
| R15 | Repeated coordinates as support. A1 Birkebeinerveien 61.4487, 10.9775 is also default.no's site-finder top | **[CAVEAT]**. 61°26′55.3″N 10°58′39.0″E matches default.no's site-finder top point at A1 to within 1 m; the same source can underlie several proposals | README:17; PRESISERINGER:11 |
| R16 | A1 in the forest model: 10 terrain+forest positions (p.16) | **[CONTRADICTED at exact point]**: at 61.4487, 10.9775, «består ingen av 25 prøveposisjoner alle skogkravene» ("none of 25 sample positions pass all the forest criteria"), whether cell-based or radial. DOM vintage is unresolved, and this «utelukker ikke hele A1-området» ("does not exclude the whole A1 area") | README:19 (issue #8) |
| R17 | App item «bever og olivenolje (ca. 100 000 poeng)» ("beaver and olive oil, c. 100,000 points", p.4) | **[CORRECTED]**. Per two third-party screenshots (praktiskinfo.no) the item shows a **badger (grevling)**, named «Olivenoljestativ», priced 100,000 points, with shipping text «Nesten Helt Hjem». «Den tidligere omtalen av en bever korrigeres» ("the earlier mention of a beaver is corrected"). Not checked in the app. A new untested lead, olive oil → **olivine**, points to Åheim/Almklovdalen. It is not ranked ahead of the others | PRESISERINGER:30; README:23 |
| R18 | «Består alle modelltestene» / «Består alt» ("passes all the model tests" / "passes everything", p.1) | **[CAVEAT]**: means only the chosen model criteria, not confirmation. Hit counts and robustness are not probabilities | PRESISERINGER:22 |
| R19 | Tests counted as agreeing lines of evidence | **[CAVEAT]**. Terrain tests and synthetic views share the same elevation data; forest tests and trunk matches share the same DOM; MET analysis and radar may be dependent | PRESISERINGER:25; README:50 |
| R20 | Access: nearest mapped road, straight lines, missing bridge ⇒ wading (p.14) | **[CAVEAT]**. The nearest road is not necessarily the one used, a straight line is not a route, and a bridge missing from OSM/DOM does not prove there is no crossing | PRESISERINGER:27 |
| R21 | Support apparatus implies a base within walking distance; the night light (p.14–15) | **[CAVEAT]**. Personnel, power and network do not prove a cabin or fixed power supply is nearby, and the light change gives no direction | PRESISERINGER:29 |
| R22 | Myklebysæterveien «flest treff» ("most hits", p.16) | **[INTERNAL INCONSISTENCY]**. The table shows E6 = 5 after all stages versus E2 Jernvinneveien = 21 | PRESISERINGER:36 |
| R23 | Madsskardveien (2) «bare to posisjoner består» ("only two positions pass", p.1, p.16) | **[INTERNAL INCONSISTENCY]**. The table has 3 for E3 after all stages | PRESISERINGER:37 |
| R24 | "13 areas" (p.9, p.16) | **[CLARIFIED]**. Includes a new P2 cut-out near old punkt 7; named table rows ≠ raster cut-outs | PRESISERINGER:38 |
| R25 | Appendix B: package with `alle_kandidatposisjoner.csv` (193 positions), `hj_modell.py`, field maps and scripts (p.22) | **[NOT PUBLISHED]**. «Den komplette pakken var ikke med i opplastingen» ("the complete package was not in the upload"). The later bevis branch «utgjør ikke en komplett reproduksjonspakke» ("is not a complete reproduction package") | PRESISERINGER:18; README:71 |
| R26 | Hint-video frames: download refused (p.18) | **[UPDATED]**. The Codex control package documents that the examined hint-video frames match zoom/crop and give no demonstrated stereo baseline for tree distances | README:25 |
| R27 | DOM (laser) vintage: «kan være fra 2016» ("may be from 2016", p.1) | **[OPEN]**. The DOM vintage is unverified, and DOM − DTM does not reliably describe trunks, species or free sight under crowns | README:49 |
| R28 | Flight comparison in the running review (issue #1) of "47° vs Messelt max 63°" | **[CORRECTED in bevis]**. It mixed a snapshot and a maximum and used 45 s. «feil sammenligningsgrunnlag» ("wrong basis for comparison") | bevis README (adsb section) |

---

## 4. Competition facts (PDF Ch. 1, p.3)

- [P-ORG] «Hordejakten 2026 er en markedsføringskampanje fra Horde AS (org.nr. 921 695 322) i Bergen.» (It is a marketing campaign by Horde AS, Bergen.)
- [P-ORG] Prize **1 116 897 kr**, «som tilsvarer antall personer i Norge med rentebærende forbruksgjeld» ("equal to the number of people in Norway with interest-bearing consumer debt").
- [P-STREAM] A woman, Anja, sits in a transparent box somewhere in Norway. Started **Monday 21 September 2026**, streamed around the clock on YouTube (EQHgfmZicc8, p.22).
- [P-ORG] To win you must physically find the box and open all code locks. «Kodene slippes som hint i Horde-appen.» ("The codes are released as hints in the Horde app.")
- Locks: «to hengelåser med fire sifre og en tallkode på døra med trolig fem sifre» ("two padlocks with four digits and a numeric door code with probably five digits").
  - Cross-check [P-BOARD, community log `magnus/src/data/innhold.ts:918, :985, :990`]: «ELEKTRONISK LÅS PÅ DØRA MED 5 SIFFER» (23.09 evening); «5 SIFFER · GANSKE SIKKER» (24.09 08:24); «2x HENGELÅS 4 TALL · 1x KODELÅS 5–6 TALL · TROR 5» (24.09).
- [P-ORG] Horde says the box is not in dangerous terrain («ikke står i farlig terreng»). Anja gets regular breaks. There are «personer i nærheten som har som oppgave å ivareta hennes ve og vel» ("people nearby whose task is to look after her wellbeing"). «Ingen på Hordekontoret vet hvor kassen står.» ("Nobody at the Horde office knows where the box is.")
- [NEWS] Anja told Børsen/Dagbladet she was picked up **at 04:00 at night** with covered windows, slept much of the trip, and was carried the last stretch wearing a sleep mask. The report concludes «Kjøretiden er derfor lite pålitelig» ("the drive time is therefore unreliable").
- [PRIOR YEARS] Earlier Hordejakter ended in **Tokke, Telemark (2023)** and at **the silver mines in Kongsberg (2024)**. Both were «i skog med bil og kort gange» ("in forest, by car and a short walk").
- Short report (kort p.3): «Anja vet ikke selv hvor hun er.» ("Anja herself does not know where she is.")

---

## 5. All hints: whiteboard table (PDF Ch. 2, p.3–4), verbatim

The report's framing: «Tavlesvarene kommer fra stedet selv og er de viktigste. Tidene er strømtid, ca. 22–45 sekunder etter virkeligheten.» ("The board answers come from the site itself and are the most important. Times are stream time, about 22–45 s behind reality.")

| Stream time (CEST) | Board text / source (verbatim from PDF) | Class | Report's use | Cross-check notes |
|---|---|---|---|---|
| 21.09 18.31 | «INGEN FLY · INGEN SKYTING · OSLO, SØN KL 04.00 · CA 5–10 MIN Å GÅ FRA BIL» | P-BOARD | Access; no firing range | Same text in community log innhold.ts:882 |
| 21.09 18.36 | «INGEN FERGE · KUN BIL · VET IKKE ANG. TUNELLER» | P-BOARD | No island/ferry | innhold.ts:883 identical |
| 21.09 18.38 | «TROR DET VAR OPPOVER · SISTE 5–10 MIN» | P-BOARD | Uphill access | innhold.ts:884 identical |
| 21.09 18.44 | «KUPERT TERRENG · MYE LYNG · HØRER IKKE MYE FRA BOKSEN» | P-BOARD | Terrain | **Wording disputed.** The bevis branch reading of board image `2109_1844_UJEVNT.png` (clip b18-44-14) is «STARTET 07 00 / UJEVNT TERRENG, MYE LYNG / HØRER IKKE MYE FRA BOKSEN»: **UJEVNT** ("uneven"), not KUPERT ("hilly") |
| 21.09 18.48 | «LIVE 07:00 · SER KUN SKOG OG KAMERA FRA BOKS» | P-BOARD | No view | innhold.ts:886 has «LIVE 07:00 · NEI, SER KUN SKOG OG KAMERA FRA BOKS» |
| 21.09 18.57 | «PRESENNING · MER ÅPEN SKOG TIL HØYRE FOR MEG» | P-BOARD | Forest (direction unclear) | — |
| 21.09 19.00 / 19.50 | «INGEN SKYER NÅ · SNART SOLNEDGANG», «KLAR HIMMEL» | P-BOARD | Cloud cover | Community log also has 19:32 «IKKE MØRKT ENDA · FINT VÆR» (innhold.ts:889; not in PDF) |
| 21.09 19.35 | «CA 12 °C (DAGEN) · NÅ CA 8–11 °C» | P-BOARD | Temperature | Temperature filter later demoted (R12) |
| 21.09 19.38 | «4 STORE STEINER, KUN STEIN DER» | P-BOARD | «Ikke brukbart i laserdata» ("not usable in laser data") | **Wording disputed.** Bevis reading of `2109_1938_4_STORE_STEINER_TIL_VENSTRE.png` (clip b19-38-13): «4 STORE STEINER TIL VENSTRE, KUN STEIN DER» ("to the left" is missing in the PDF) |
| 21.09 19.47 | «MØRKT NÅ» | P-BOARD | Dusk, does not discriminate | — |
| 21.09 21.30 | Points up, writes «FLY» | P-STREAM/P-BOARD | Flight analysis | Community log (innhold.ts:894): «FLY (pekte opp, litt mot sørøst)» ("pointed up, slightly south-east"). Bevis: the pointing may have been at a shooting star (R10) |
| 22.09 20.32–20.36 | «Reagerer på fly, peker og følger det sørover» ("reacts to plane, points and follows it south") | P-STREAM (gesture) + C-OBS (plane ID) | Flight analysis | — |
| 22.–23.09 | «NULL REGN», «det har ikke vært frost», «SER VELDIG MANGE STJERNER» | P-BOARD | Dry, dark site | — |
| 23.09 | «SOLA VAR OPPE FØR 07», «KAMERA 41 ØST», «118–120 GR ØST» (skiltet) | P-BOARD | Camera direction | Per community log, «118–120 GR ØST» is the direction the Horde **sign** pointed (innhold.ts:905, :135–138). The sign was later removed: 23.09 19:12 «SKILTET ER BORTE · VET IKKE HVOR» (innhold.ts:408) |
| 23.09 17.49 | «LYDTETT · SOL · VINDSTILLE» | P-BOARD | Weather (weak) | — |
| 23.09 evening | «TYPISK FJELLMARK», «IKKE VANN · STEIN + SOPP · MOSE PÅ STEINER», «GIKK 2 MIN INN I SKOGEN», «ISH 16°» | P-BOARD | Terrain, water, access | Fuller community text: «FÅR SE BITTELITE · MASSE SOPP · TYPISK FJELLMARK» (innhold.ts:919). Also 22.09 19:19 «INGEN VANN ELLER VANNLYDER, FØLER IKKE DET ER VANN I NOE NÆRHET» (innhold.ts:896–898) |
| 24.09 | «KOM FRA DEN VEIEN ←», «INGEN STIER», «DET HAR VÆRT HOGD TIDLIGERE DER JEG GIKK … →» | P-BOARD | «Veiretning ca. 130°» ("road direction about 130°") | **The PDF elides words.** Community log (innhold.ts:995) and board photo `magnus/public/img/tavle-hogd.jpg` give «DET HAR VÆRT HOGD TIDLIGERE DER JEG GIKK I GÅR · GIKK DEN VEIEN →» ("there has been logging earlier where I walked **yesterday** · walked that way →"). Posted 24.09, so "yesterday" = 23.09. It may describe a break walk rather than the arrival route. The companion board is «SÅ INGENTING SOM IKKE HØRER TIL I EN SKOG I GÅR» ("saw nothing yesterday that doesn't belong in a forest", innhold.ts:998). Bevis marks «…DER JEG GIKK I GÅR» [ikke verifisert] ("not verified"). The 130° value is an interpretation (see §13, §16) |
| 24.09 | «GRÅVÆR HELE DAGEN», rain c. 11.05 (gjengitt) | P-BOARD + second-hand | Weak weight | The rain claim is second-hand («gjengitt av andre, ikke sett på tavla» — "relayed by others, not seen on the board", p.7). Community log (innhold.ts:999): «(kl. 11:05) Anja sa at det regnet» ("Anja said it was raining") |
| 24.09 17.20 | «INGEN HYTTE I NÆRHETEN SOM JEG VET OM ELLER SER» | P-BOARD | No building nearby | innhold.ts: image tavle-ingen-hytte.jpg |
| 22.09 21.36 | «DET ER INGEN LYS RUNDT KASSEN» (read by the report authors from the recording) | P-BOARD | Night light | Median of 100 frames shown in Fig. 10 |
| 25.09 08.46 | «Overskyet. Flyene er så langt unna at de er umulige å se.» (gjengitt) | P-BOARD (paraphrased) | Weak weight | Fuller community transcription (innhold.ts:1002): «OVERSKYET · FLYENE ER SÅ LANGT UNNA AT DET ER UMULIG Å SE PÅ DAGEN, OG PÅ NATTA DERSOM DET IKKE ER HELT STJERNEKLART» ("impossible to see by day, and at night unless completely starry"). That qualifies it: at night under clear skies planes may be visible |
| "Nylig" (recent) | «Gule og grønne fugler» | P-BOARD | Coniferous forest, not site-specific | Short report kort p.8: fits siskin, crossbill (females/young yellow-green), great tit and goldcrest. default.no found furukorsnebb (parrot crossbill), kjøttmeis (great tit) and blåmeis (blue tit) in the day-1 audio |

Not in the PDF but in the bevis branch board readings, all from 22.09 18:56–19:05: «JA, FØLES SOM FJELLUFT» ("yes, feels like mountain air") · «GIKK IKKE PÅ STI, MEN KUPERT TERRENG» ("didn't walk on a path, but hilly terrain") · «BLANDET SKOG, VELDIG HØYE TRÆR, KUPERT TERRENG, SOM GÅR SLAKT SLIK:» ("mixed forest, very tall trees, hilly terrain, sloping gently like this:"), followed by a drawn gentle hump.

---

## 6. Hints from Horde and the app (PDF p.4)

- [P-APP] «Verv en venn» ("refer a friend") gives the letters **N O R H E I M S U D**, read as HORDE MINUS. «Hordeminus» in the app's AI assistant answers **«2,7 eiffeltårn stablet oppå hverandre»** ("2.7 Eiffel towers stacked on top of each other"), giving **810, 875 or 891 m**.
- [P-ORG] Sound hint 24.09: **black grouse (orrfugl) in autumn lek**. [C-OBS via default.no] Artsdatabanken has a registered black-grouse lek at **Evenstadlia, east of the Glomma** (no coordinates given in the PDF).
- [P-ORG] Horde's hint video 22.09 has outside shots of the box: «hevet plattform, blåbær- og tyttebærlyng, gule bjørker og høye furuer bak» ("raised platform, blueberry and lingonberry heath, yellow birches and tall pines behind").
- [P-ORG] Jaktvettreglene ("hunt etiquette rules"): «Ikke kle deg ut som elg, hjort eller storfugl. Det er jaktsesong.» ("Don't dress up as elk, deer or capercaillie. It's hunting season.")
- [P-APP, unconfirmed] «Hint-hint»-ekorn ("hint-hint squirrel"): an **unconfirmed screenshot** shows FROLAND gives «Ekornet kan klatre» ("the squirrel can climb"). A Finn advert gives «Ikke en øy» ("not an island").
- [P-APP] Code hints: «terje» gives **5008** (Horde's postcode). Sign **LD6788** is said to give «ENKODE» (unconfirmed). Kodejakten on horde.no gives one code. «Genser, bukse og chiffer gir kampanjeord, ikke steder» ("sweater, trousers and cipher give campaign words, not places").
- [P-APP] «Nytt: en appvare som kombinerer bever og olivenolje (ca. 100 000 poeng). Den er ikke tolket.» ("New: an app item combining beaver and olive oil, c. 100,000 points. Not interpreted.") **Corrected in PRESISERINGER:30:** badger, «Olivenoljestativ», 100,000 points, «Nesten Helt Hjem». See R17.

---

## 7. Data sources and method (PDF Ch. 3, p.4)

| Source | What | Used for |
|---|---|---|
| Live stream / default.no archive | Minute clips, board log, day and night stills | Camera geometry, observations, night |
| Kartverket NHM | DTM1 (ground) and DOM (surface), 1 m | Terrain, tree height, horizons |
| OpenStreetMap | Roads, tractor roads, paths, rivers, buildings | Access, river crossing |
| adsb.lol (ADS-B) | Flight tracks with time and altitude | Flight analysis |
| MET Norway | MET Nordic analysis 1 km, radar mosaic | Temperature, cloud, wind, rain |
| default.no | Fusion model, site finder, drive plan, sun spots, flight events | Region choice, morning sun |
| Community map (GitHub, MagnusPladsen) | Hint list and copies of data layers | Hint catalogue, raw data |
| Global Forest Watch (via default.no) | Logging year | Logging (uncertain hint) |

Method summary (p.4):

- **Camera:** direction and focal length from the sun's path in the image: **f = 1068 px, FOV c. 62°, heading 219.2–219.6°**.
- **Ground points** in the image become directions and elevation angles.
- **Grid:** for every possible camera spot (**10 m grid, 7,525 per area**) the model checks that rays hit the ground at the right distance in the laser terrain, and that the trees around match the image. The short report (kort p.3) adds that hits were refined at **2 m**.
- **Later tests** on the surviving positions: access, sun, temperature and trunks.
- **Numerics:** all intersections at **1 cm** steps along rays.
- **Reproducibility:** «skript og resultatfiler følger med (vedlegg B)» ("scripts and result files are included, Appendix B"). **Not published** (R25).

---

## 8. Region: the flights (PDF Ch. 4, p.5–6)

[P-STREAM] Anja reacted visibly to planes three times:
- 21.09 21.29–21.34: «peker rett opp og skriver «FLY»» ("points straight up and writes FLY").
- 22.09 20.32–20.34 and 20.34–20.36: «peker, setter seg opp og følger flyet sørover» ("points, sits up and follows the plane south").

[INT] «Et fly som står høyt på himmelen, passerer nær» ("a plane high in the sky passes close"), so ADS-B can show where on the ground a plane stood high enough.

| Event (stream time) | Candidate planes [C-OBS] | Note |
|---|---|---|
| 21.09 21.29–21.34 | **NOZ56U** (Oslo–Bodø, northbound over Hamar/Løten); **NOZ9EG** (southbound over Ringsakfjellet) | Original tracks hex **4791ac** and **47a3b0**; the exported track has a jump of c. 46 s |
| 22.09 20.32–20.34 | **SAS39A** (Bodø–Oslo) southbound down Østerdalen | **90–96 % cloud cover**; only planes below c. **28,000 ft** visible |
| 22.09 20.34–20.36 | **NOZ55J** (Bodø–Oslo) southbound, c. **21,000 ft** | She follows the plane south |

**First computation [MODEL], p.5–6, Fig. 2 (`figurer/flykart_83ruter.png`).**
- Tested **17,234 cells of c. 500 × 500 m** in the altitude band **790–911 moh**, at most **900 m from a road**, against all three planes.
- Requirement: at least **35°, 25° and 25°** above the horizon.
- **Only 83 cells passed**, all on one ridge **west of the Glomma between Mykleby and Evenstad**. «Resultatet sto seg når tidsvinduer og vinkelkrav ble endret» ("the result held when time windows and angle requirements were changed").
- Figure 2 caption: the analysis was limited to the Eiffel-hint altitude band and «er senere erstattet av en bredere vurdering» ("has since been replaced by a broader assessment").
- Figure 2 plots, read from the figure (approximate):
  - "Mine søkepunkter 1–7" ("my search points"): 1 ≈ 61.310, 10.970; 2 ≈ 61.320, 10.970; 3 ≈ 61.335, 10.950; 4 ≈ 61.310, 11.000; 5 ≈ 61.340, 10.980; 6 ≈ 61.365, 10.990 (at "Myklebysætra (ca.)" ≈ 61.364, 10.993); 7 ≈ 61.375, 10.980. **Point 7 = the later "punkt 7".**
  - Myklebysjøen (989 moh) ≈ 61.319, 10.902.
  - default.no's 40 stops (blue diamonds); "default.no stopp 1" at ≈ 61.452, 11.146.
  - The orange passing cells cluster at 61.375–61.405 N, 10.88–10.99 E and 61.30–61.38 N, 10.95–11.08 E.

**Later refinement [MODEL/INT], p.6.**
- Using original ADS-B tracks and separate delays per day, the two 22.09 planes point in opposite directions:
  - **If NOZ55J**, the north is favoured: Gålaveien, Birkebeinerveien, Messelt.
  - **If SAS39A**, the south is favoured: Myklebysætra, H2 and punkt 7.
- The split depends on reaction times, a **25° threshold** and a **15–50 s delay**, «og ingen av disse er sikkert dokumentert» ("and none of these is reliably documented").
- «Videoen viser flere armbevegelser rundt hendelsene, og armens retning kan ikke brukes, fordi dybden er usynlig.» ("The video shows several arm movements around the events, and the arm's direction cannot be used because depth is invisible.")
- Stream audio is, per default.no, a **24-hour loop recording**, so sound is not used. Anja's 25.09 remark that planes are «umulige å se» ("impossible to see") suggests some reactions may have been sound-based.
- «Flyene brukes derfor til å velge region, ikke punkt.» ("The planes are therefore used to choose a region, not a point.")

**Later status.** Region selection by flights is itself demoted (R9, R10). The bevis-branch reproduction (`adsb/fly_2109_resultat.txt`) gives these elevations at 22 s delay from stream 21:29:38:

| Site | NOZ9EG (LN-NIQ, 4791ac) | NOZ56U (LN-ENN, 47a3b0) |
|---|---|---|
| 1 Myklebysæterveien vest | 33° | 4° |
| 2 Madsskardveien | 22° | 4° |
| S-Messelt S1/S2 | 24° | 3° |
| 4 Madsskardveien øst | 20° | 4° |
| 5a Jernvinneveien | 22° | 4° |
| A1 | 26° | 4° |
| A2 C07 | 24° | 4° |
| Løten | 7° | 28° |

Bevis conclusion: «Ingen kandidat har et fly i nærheten av «rett opp» i det øyeblikket hun peker» ("no candidate has a plane anywhere near straight up at the moment she points").

---

## 9. The altitude hint (PDF Ch. 5, p.6–7)

- [P-APP] «Hordeminus» → «2,7 eiffeltårn stablet oppå hverandre».
- The Eiffel Tower is 300 m without antenna, 324 m with the old one and 330 m with the new one. 2.7 × those gives **810, 875 and 891 m**.
- [INT] Read as metres above sea level, it points to forest just below the tree line, e.g. **Messelt (870–900 moh)** and **Myklebysætra (800–900 moh)**.
- [INT] It may equally be a lock code (**0810 or 0891**). «appens AI-assistent sier selv at den ikke vet hvor kassen er» ("the app's AI assistant itself says it does not know where the box is").
- Used «som ett kriterium blant flere, ikke som et filter» ("as one criterion among several, not as a filter"). «Det er hovedgrunnen til at Messelt fortsatt står på lista.» ("That is the main reason Messelt is still on the list.")

---

## 10. Weather (PDF Ch. 6, p.7–8)

**Dry at the start.**
- [P-STREAM] The camera was dry the first days.
- [P-BOARD] «NULL REGN» on 22 and 23.09.
- [MODEL via default.no] Vestlandet, the mountains and Trøndelag got **5–15 mm** in the same period, while Østerdalen got **0–0.7 mm**. «Dette peker mot Østlandet innenfor» ("this points to inland Eastern Norway"). Later demoted (R11).

**National weather test [MODEL]: seven time-stamped statements against MET Nordic.**
- Samples: **13,348 land samples (5 km grid)** and **25,066 cells (1 km)** around Østerdalen.
- Statements tested:
  - 21.09: no clouds at 19.00, clear sky at 19.50, c. 8–11 °C at 19.35 and c. 12 °C during the day.
  - 23.09 17.49: sun and calm.
  - 24.09 c. 11:00: rain.

| Requirement (wide tolerances) | Norway | South of 64° N | Østerdalen (60.5–61.8 N, 10–12.5 E) |
|---|---|---|---|
| All seven | 2 | 0 | 0 |
| Without the rain requirement | 9 | 0 | 0 |
| Without «sol» translated to cloud cover ≤ 70 % | 427 | 409 | 146 |
| Without both sun and rain requirements | 2 191 | 2 152 | 556 |
| Only evening cloud and temperature 21.09 | 2 229 | 2 164 | 556 |

- The two cells passing everything lie at **67.4° N in Nordland**. The report calls this «ikke troverdig» ("not credible"), since the result depends on how «SOL» and «VINDSTILLE» are translated to model values.
- With those two requirements removed, **one quarter** of passing cells lie in Østerdalen (556 / 2,191 ≈ 25 %).

**Temperature [MODEL: MET Nordic 1 km]** (p.7; also Fig. 3 right, `figurer/sol_og_temp.png`)

| Site | Model «dagmaks» 21.09 | Model 19.35 | Match with «12» and «8–11» |
|---|---|---|---|
| Birkebeinerveien (A1) | 12.0 °C | 8.0 °C | ✓ |
| Gålaveien (A2) | 14.0 °C | 9.2 °C | ~ |
| Sørlige Messelt | 8.8–9.6 °C | 5.3–5.8 °C | ✗ |
| Punkt 7 / H2 | 9.5–10.4 °C | 6.4–6.7 °C | ✗ |
| Myklebysæterveien vest (1) | 11.9 °C | 8.1 °C | ✓ |
| Madsskardveien (2 and 4) | 11.5–11.6 °C | 7.5–7.6 °C | ✓ |
| Jernvinneveien (5) | 12.9 °C | 8.4 °C | ✓ |
| Rena (comparison) | 15.1 °C | 10.6 °C | ~ |

Values read from Fig. 3 for areas not in the text table (approximate):

| Area | dagmaks | 19.35 |
|---|---|---|
| E1 Madsskardveien øst | ≈ 11.5 | ≈ 7.6 |
| E2 Jernvinneveien | ≈ 12.9 | ≈ 8.4 |
| E3 Madsskardveien | ≈ 11.6 | ≈ 7.6 |
| **E4 Ole Evenstads vei** | **≈ 15.2** | ≈ 7.9 |
| E5 Madsskardveien nord | ≈ 11.8 | ≈ 7.6 |
| E6 Myklebysæterveien | ≈ 11.9 | ≈ 8.1 |
| Nordlige Messelt | ≈ 9.6 | ≈ 5.8 |

- The temperature pass criterion appears only in the short report (kort p.5): **modelled day 10–14 °C and 19.35 7–12 °C**. That explains E4 failing (day max ~15.2) while 7.5–7.6 °C at 19.35 still passes.
- Report's own caveat: «Vi vet ikke hvordan Anja målte temperaturen. «ISH 16°» om kvelden 23.09 er høyt for årstiden, og kan tyde på at noen av tallene gjelder luften i kassen. Da blir Messelt og punkt 7 mindre svekket.» ("We don't know how Anja measured the temperature. 'ISH 16°' on the evening of 23.09 is high for the season and may mean some figures refer to the air in the box. Then Messelt and punkt 7 are less weakened.")
- Later: temperature is no longer a hard filter (R12).

Fig. 1 (`figurer/oversikt_temp.png`) maps the MET Nordic modelled air temperature at 19.35 on 21.09 over 61.25–61.60 N, 10.6–11.4 E, with an 8 °C contour. The west (Messelt, 10.6–10.9 E) is cold (≈ 3–6 °C). The Glomma valley and the east side are warmer (≈ 8–11 °C).

**Rain and radar 24.09 [MODEL: MET radar mosaic]** (p.7–8). The rain at 11.05 «er gjengitt av andre, ikke sett på tavla» ("relayed by others, not seen on the board"). Radar values in mm/h:

| Site | At 11.05 | Max 10.30–11.30 | Max within 3 km |
|---|---|---|---|
| Gålaveien (A2) | 0 (blocked) | 0.001 | 0.002 |
| Birkebeinerveien (A1) | 0 | 0.003 | 0.002 |
| Sørlige Messelt | 0.006 | 0.009 | 0.039 |
| Nordlige Messelt | 0.015 | 0.022 | 0.039 |
| H2 | 0 | 0.032 | 0.019 |
| Punkt 7 | 0 | 0.042 | 0 |
| Rena | 0.115 | 0.220 | 0.254 |

- Radar is blocked in much of the Glomma valley. The only clear rain cell in the valley lay at **61.28 N, 10.92–10.96 E**.
- [P-STREAM] Stills at 11.05 and 11.08 show matte, dewy patches on the glass, but not definitely falling rain.
- «Regnhintet er derfor ikke brukt til å rangere.» ("The rain hint is therefore not used for ranking.")

---

## 11. The sun (PDF Ch. 7, p.8)

**Sunrise [MODEL, own NOAA-type calculation].**
- The community used «SOLA VAR OPPE FØR 07» to point east.
- The report computes sunrise on **23.09 at 07.01–07.04** across the area: Oslo 07.04, Evenstad 07.02, Rena 07.01.
- Only east of c. **11.6° E** (Trysil, Engerdal) does the sun rise before 07.00, «og der passer ingen fly» ("and no planes fit there"). The hint therefore does not discriminate.
- Also: community sunrise times were 3–4 min too early (R7).

**Evening sun and terrain horizon [MODEL].** 12,150 samples out to 30 km, for the first six candidates:

| Point | Shading terrain | Sun behind terrain, 1.5 m | Sun behind terrain, 20 m |
|---|---|---|---|
| Gålaveien (A2) | 50–125 m (own slope) | c. 17.34 | c. 18.03 |
| Punkt 7 | 25–350 m | c. 17.53 | c. 18.36 |
| Messelt 61.455, 10.840 | 400–450 m | c. 18.09 | c. 18.31 |
| Messelt 61.460, 10.850 | 1.3–1.6 km | c. 18.29 | c. 18.34 |
| H2 | 2.5–6 km | c. 18.48 | c. 18.51 |
| Birkebeinerveien (A1) | 7–16 km | c. 18.59 | c. 19.01 |

- [P-STREAM via report] «Siste solflekk i bildet var kl. 17.23 (sola 12,9° høy mot 246°).» ("Last sun spot in the image was at 17.23, sun 12.9° high toward 246°.")
- This does not discriminate between sites, «fordi trær kan skygge før terrenget gjør det» ("because trees can shade before the terrain does").

**Morning sun: «den mest avgjørende soltesten» ("the most decisive sun test")**
- [C-OBS: default.no] First direct sun spot in the image at **07.51 on 21.09**. The sun was strongest **08.25–09.55**.
- [P-STREAM, report's own stills] Frames at 10.15–10.45 show only diffuse light, consistent with that.
- [MODEL] At 07.51 the sun stood at **azimuth 98.8°, elevation 5.7°**. «Et sted der terrenget mot øst ligger høyere enn ca. 6,5°, kan ikke ha fått sol da.» ("A site where the terrain to the east is higher than c. 6.5° cannot have had sun then.")
- The short report says «ca. 6°» in its text (kort p.5) and «høyst ca. 6,5°» ("at most c. 6.5°") as the test.
- **Fig. 3 left** (`figurer/sol_og_temp.png`) plots the terrain horizon to the east (96–102°) for all positions passing terrain+forest (grey) and those also with access (green), with an orange line at 5.7°. Approximate readings:

| Area | Grey range | Green (with access) |
|---|---|---|
| A1 | 7 to 20.5° | ≈ 10, 10.2, 15.6° (all above) |
| A2 | −1 to 14° | ≈ 9.4, 12.7° (above) |
| Sørlige Messelt | −2.5 to 7.5° | ≈ −2.5, −1.9° |
| Nordlige Messelt | −1.5 to 3.4° | ≈ 0.3, 0.8° |
| Punkt 7 | −4 to 7.4° | ≈ −3.9, −3.6, 7.4° |
| E1 | −0.8 to 12° | ≈ −0.8, 1.2, 2, 5.3° |
| E2 | 1.1 to 22° | ≈ 3.3–11.4° (many dots, roughly half above 5.7°) |
| E3 | −3.2 to 8.9° | ≈ −3.2, −1.1, 6, 8.9° |
| E4 | 4 to 19.5° | ≈ 4–19.5° |
| E5 | 6 to 14.8° | ≈ 6–14.8° |
| E6 | −2.3 to 0.7° | ≈ −2.3 to −0.5° |

- Caveat in the PDF (p.8): «første solflekk i bildet er ikke nødvendigvis første sol på bakken. Den kan være sol på en stamme eller en refleks. Målingen er ikke kontrollert i originalopptaket, fordi nedlastingen ble nektet.» ("The first sun spot in the image is not necessarily the first sun on the ground. It may be sun on a trunk or a reflection. The measurement is not checked in the original recording because the download was refused.")

**Later evidence on morning sun** (bevis branch `sol/`; README:16, :47). Measured on default.no minute clips 07.40–08.30 on 21.09:
- The crown/sky ratio in the top-right patch rises: 0.29–0.33 until 07.44, then 0.39 (07.47), 0.53 (07.49), 0.66 (07.50), stays 0.58–0.68 until 08.00, and drops to 0.29 at 08.30.
- Sharp warm light on the trunk and spruce branches to the right appears **from 07.47**.
- «Bakken får ikke direkte sol før 08.00» ("the ground does not get direct sun before 08.00").
- The top-right patch is at azimuth 238–250°, elevation +8.5 to +18.6°.

So the "07.51 first sun" premise is refined: crowns and trunks are lit ≥ 4 min earlier and the ground later. Which surface must see the sun changes the horizon threshold. This is under review in issue #2.

---

## 12. default.no analysis (PDF Ch. 8, p.9) and region conclusion (Ch. 9)

default.no is described as «et åpent, frivillig prosjekt» ("an open, volunteer project") that logged the whole stream and used:
- flight tracks from **over 1,200 planes**;
- weather from **400 stations**;
- satellite imagery;
- forest type from NIBIO;
- logging from Global Forest Watch;
- firing ranges.

[MODEL: default.no]
- **Fusion model** best area: Glomma valley between Rena and Evenstad (**61.35–61.47 N, 10.97–11.15 E**), with **11 %** of the probability within 10 km and **29 %** within 25 km of the **top cell 61.45, 11.10**.
- **Site finder** scores each **40 m** cell on distance from road, rise, pine, relief along the camera direction, sun horizon and logging. It gave **Birkebeinerveien (61.4487, 10.9775)** as the top.
- **Drive plan of 40 stops** has **Madsskardveien east of the Glomma (61.4520, 11.1460)** as stop 1.
  - Note: the local mirror `magnus/public/data/defaultno/plan.json` (generated 2026-09-24 17:04) has `n: 36` stops, with stop 1 «Madsskardveien ost for Glomma» at 61.452, 11.146. The count differs between versions.
- The report used default.no to choose where to look and adopted its morning-sun measurement. «Deres modell bygger imidlertid på noen av de samme usikre premissene: tørrvær og hvilket fly hun så. Prosenttallene er derfor ikke brukt som bevis for enkeltpunkter.» ("Their model, however, rests on some of the same uncertain premises: dry weather and which plane she saw. The percentages are therefore not used as evidence for individual points.")

**Region conclusion (p.9) [INT].**
- «Fly, tørt vær, skogtype, temperatur og default.no sin uavhengige modell peker alle mot Østerdalen rundt Evenstad. Ingen enkeltbevis er sikkert, men de peker samme vei.» ("Planes, dry weather, forest type, temperature and default.no's independent model all point to Østerdalen around Evenstad. No single piece is certain, but they point the same way.")
- The site analysis was concentrated there: **13 areas of 1.6 × 1.6 km on both sides of the Glomma**.
- «Kassen kan likevel stå et helt annet sted; det er den største usikkerheten i hele arbeidet.» ("The box may still be somewhere completely different; that is the biggest uncertainty in the whole work.")
- Later: region demoted to "open" (R9). The "independence" of default.no is questioned by PRESISERINGER:11 and the report's own remark on shared premises.

---

## 13. Camera image (PDF Ch. 10, p.10–11)

- [P-STREAM + INT] «Kameraet står ca. 5 m nordøst for kassen og filmer mot sørvest.» ("The camera stands c. 5 m north-east of the box and films south-west.")
- [P-BOARD] «KAMERA 41 ØST» ("camera 41 east").
- [MODEL] Sun path in the image gives heading **219.6° at 59.5° N** or **219.2° at 61.5° N**, focal length **1068 px**, horizontal field **c. 188.7–250.5°** (≈ 61.8°).
- Figure 4 footnote: «Vinkelspenn dekker begge kalibreringene (219,6°/+0,2° og 219,2°/−0,9°), f = 1068 px, full bildestråle» ("the angle span covers both calibrations (219.6°/+0.2° and 219.2°/−0.9°)"). The second number is the camera pitch.
- The 1068 px refers to a 1280-wide frame. Bevis: f = 1602 px at 1920 width, with heading 219.4°.
- Short report (kort p.3–4): camera points c. 220°. The camera stands **1.1–1.9 m above ground**. Kort p.3 also says «kameraet ca. 41° øst for nord sett fra boksen → kamera mot ca. 221°» ("camera c. 41° east of north seen from the box → camera toward c. 221°").

**Measured ground points** (day image 21.09 15.01; Fig. 4, `figurer/fig_bildemaling.png`):

| Point | Pixel (x, y) | Direction | Elevation angle | Distance |
|---|---|---|---|---|
| M0 ground at the box | 617, 630 ± 5 | 218° | −15.3 to −13.7° | **4.3–5.9 m** (box width 2.0 ± 0.2 m) |
| B1 trunk foot left | 80, 490 ± 12 | 192° | −7.5 to −5.4° | not measured |
| B2 trunk foot left-centre | 400, 490 ± 12 | 207° | −8.3 to −6.0° | not measured |
| B3 back edge of clearing | 640, 402 ± 5 | 219° | −3.4 to −1.8° (Fig. 4 label reads −3.7…−2.0°) | **unknown** (previously 17–44 m, **retracted**) |
| B4 birch foot | 996, 498 ± 8 | 238° | −8.2 to −6.4° | **12–45 m** (from trunk width) |
| B5 ground line right | 1200, 505 ± 12 | 247° | −8.2 to −6.1° | not measured |

**«Stubben som ikke var en stubbe» ("the stump that wasn't a stump") [RETRACTED measurement], p.10.**
- A bright "stump" behind the box was long taken as a 0.25–0.5 m stump. Its **13–16 px** width gave **17–44 m**, «og den avstanden styrte hvilke områder som besto» ("and that distance controlled which areas passed").
- Morning images in diffuse light show no stump there. Brightness at the spot is flat in the morning but **40–52 vs 25–30** in afternoon sun: «trolig motlyst løv» ("probably back-lit foliage").
- «Avstanden er derfor trukket tilbake, og alle posisjoner som ble forkastet på grunn av den, er tatt inn igjen. Dette er den viktigste enkeltrettelsen i arbeidet.» ("The distance is therefore withdrawn and all positions rejected because of it are re-admitted. This is the single most important correction in the work.")
- Fig. 5: the same crop at 15.01, 10.15 and 10.45; the bright patch at x ≈ 950–975 (1920-px frame) exists only in afternoon sun.

**Field landmarks** (Fig. 6, morning image 21.09 10.45 full resolution; `figurer/fig_kjennetegn_1045.png`). Legend verbatim:

| ID | Legend (verbatim) | Azimuth (approx.) |
|---|---|---|
| O1 | «Skrå død stamme/stang bak boksen» (slanted dead trunk/pole behind the box) | ca. 218° |
| O2 | «Synlig bakkekant bak boksen (lyng → ung skog)» (visible ground edge behind the box, heather → young forest) | ca. 219° |
| O3 | «Tørr grein/liten gadd ved bakkekanten» (dry branch/small snag at the ground edge) | ca. 223° |
| O4 | «Her sto «stubben» kl. 15.01 – finnes ikke i diffust lys» (the "stump" at 15.01, absent in diffuse light) | ca. 220° |
| O5 | «Høy stamme rett bak boksen» (tall trunk right behind the box) | ca. 222° |
| O6 | «Bjørk med skjev nedre stamme» (birch with crooked lower trunk) | ca. 238° |
| O7 | «Stor mørk stamme høyre» (large dark trunk, right) | ca. 241° |
| O8 | «Store mørke stammer venstre» (large dark trunks, left) | ca. 190° |
| O9 | «Stor stamme venstre-midt» (large trunk left-centre) | ca. 201° |
| O10 | «Høye furuer med himmel mellom stammene» (tall pines with sky between the trunks) | ca. 219° |

[P-STREAM, model-checked]
- «Kameraet står stille: bildene fra 10.15 og 15.01 passer oppå hverandre med under 1 piksels avvik (114 av 127 SIFT-samsvar).» ("The camera is static: the 10.15 and 15.01 images overlay with under 1 px deviation, 114 of 127 SIFT matches.")
- «Nattkameraet er det samme bildet forstørret 2,45 ganger. Det finnes altså ingen parallakse å måle avstand med.» ("The night camera is the same image magnified 2.45×, so there is no parallax to measure distance with.")

---

## 14. Terrain model (PDF Ch. 11, p.11–12) [MODEL]

- For each candidate camera spot the model finds the camera height that puts M0 at 4.3–5.9 m.
- It then checks that rays through B3 and B4 first hit the ground at the right distance.
- Camera height must be **0.3–3 m**. Vegetation is not included.
- «Da B3 hadde 17–44 m avstand, skilte testen tydelig mellom områdene» ("when B3 had 17–44 m distance, the test clearly separated the areas"), but the sensitivity test shows the difference came almost entirely from that assumption.

Percentage of compatible positions within **40 m / 500 m** of the marker:

| B3 window (M0 4.3–5.9 m) | A2 | A1 | N-Messelt | S-Messelt | H2 | Punkt 7 |
|---|---|---|---|---|---|---|
| 17–44 m (stump scenario, retracted) | 22 / 33 | 3 / 50 | 0.2 / 63 | 88 / 65 | 95 / 63 | 51 / 40 |
| 7–44 m | 26 / 82 | 9 / 71 | 2 / 78 | 100 / 95 | 95 / 84 | 96 / 94 |
| 7–100 m | 46 / 85 | 27 / 82 | 34 / 85 | 100 / 99 | 98 / 89 | 96 / 95 |
| 0–250 m (no limit) | 68 / 89 | 72 / 90 | 92 / 92 | 100 / 99 | 100 / 96 | 97 / 97 |

- «Uten avstandsgrense består nesten alt.» ("Without a distance limit almost everything passes.")
- Numerics: 25 cm → 1 cm steps; A2 went 1,324 → 1,229 positions.
- After removing the B3 distance (only 8–250 m required), **1,000–7,500 of 7,525 positions per area pass**. «Terrenget alene skiller altså lite.» ("Terrain alone therefore separates little.")
- Short report (kort p.5) adds the other requirements used: B3 ground edge 8–250 m, birch foot 12–45 m.

---

## 15. Forest model (PDF Ch. 12, p.12–13) [MODEL]

Tree height per m² = DOM − DTM. Five criteria from the image, «låst før de ble kjørt» ("locked before they were run"):

| Criterion | Zone from camera | Threshold | Why |
|---|---|---|---|
| K0 box site | 212–226°, 3–7 m | median < 3 m | the box stands in an opening |
| K1 clearing | 213–226°, 8–17 m | median < 3 m | heath behind the box |
| K2 left side | 190–207°, 3–20 m | p90 ≥ 10 m | dense trunks on the left |
| K3 right side | 232–250°, 5–25 m | p90 ≥ 10 m | birch and big trunk on the right |
| K4 background | 213–226°, 25–70 m | p90 ≥ 12 m | tall pines behind the clearing |

Results:
- With the old B3 distance: **25 patches (F01–F25)**, later **24 (G01–G24)** with finer numerics. Three examined in detail:
  - **C07 at Gålaveien (61.4625, 10.9751)**: «passet best med skogbildet» ("best fit to the forest picture").
  - **C06** nearby: had a side ray that did not hit the ground within **228 m**.
  - **C23 at Messelt (61.4571, 10.8361)**: best access. This is the same point as report candidate 3 / S1.
- Robustness = share of **243 threshold combinations** that pass. «Dette er toleranse innen modellen, ikke sikkerhet.» ("This is tolerance within the model, not certainty.")

Exact coordinates (bevis branch `horisont/punkter_v6.csv`, the report's historical v6 points):
- C06: 61.46235821, 10.97495372
- C07: 61.46254284, 10.97511774
- C23: 61.45712966, 10.83614627
- G01–G24 also listed there: e.g. G02 (A2) 61.46248690, 10.97504982; G15 (P7) 61.37446824, 10.97722068; G16 (Messelt) 61.45711061, 10.83611124; G18 (Messelt) 61.45446203, 10.84063536 (= S2).

**Fig. 7, synthetic views** (`figurer/syntetisk_utsyn_kronebase40.png`). From DTM1 + DOM, «DOM-årgang ikke verifisert» ("DOM vintage not verified"). Blue sky, brown ground, green canopy; «Nederste 40 % av kronehøyden regnet som gje[nnomsiktig]» ("lowest 40 % of crown height treated as transparent"). Camera heights, calibration K1:

| Position | Camera height |
|---|---|
| C06 (A2) | 1.76 m |
| C07 (A2) | 1.58 m |
| F01 lokal beste (A2) | 1.56 m |
| C23 (sørlige Messelt) | 1.87 m |
| F17 lokal beste (sørlige Messelt) | 1.78 m |

Caption: «Dette er illustrasjoner. De bygger på samme data som testen og er ikke en uavhengig bekreftelse.» ("These are illustrations. They rest on the same data as the test and are not an independent confirmation.")

**Trunk test** (Fig. 8, `figurer/fig_stammeplassering.png`).
- Ten trunks measured in the image (cyan) against local maxima in the laser data (red: tops ≥ 8 m within 40 m), direction plus distance from trunk width. «Testen er svak i tett skog.» ("The test is weak in dense forest.")
- Results: C07 (A2) **8/10**; G02/F01-representant (A2) **6/10**; C23 (sørlige Messelt) **8/10**; G16/F17-representant (sørlige Messelt) **10/10**.
- «De anbefalte stedene har 8–10 av 10 stammer med et tre i riktig retning.» ("The recommended sites have 8–10 of 10 trunks with a tree in the right direction.")

**Later re-run (bevis `horisont/kkrav_resultat.txt`, [MODEL], not in README).** K0–K4 at the report's published markers over a 5×5, 10 m neighbourhood, camera = box + 5 m toward 39°. Cells show the value at the centre position:

| Site | pass/25 | K0 | K1 | K2 | K3 | K4 |
|---|---|---|---|---|---|---|
| 1 Myklebysæterveien vest | **0** | ✗ 10.4 | ✓ 0.2 | ✓ 15.6 | ✓ 11.5 | ✓ 17.9 |
| 2 Madsskardveien | 1 | ✓ 0.1 | ✓ 0.1 | ✓ 13.9 | ✓ 12.2 | ✓ 12.4 |
| 3a S-Messelt S1 | 2 | ✗ 8.0 | ✗ 6.9 | ✓ 17.5 | ✗ 5.9 | ✓ 13.5 |
| 3b S-Messelt S2 | 0 | ✓ 0.7 | ✗ 4.2 | ✗ 8.9 | ✗ 5.5 | ✓ 13.2 |
| 4 Madsskardveien øst | 1 | ✓ 0.5 | ✓ 2.8 | ✓ 14.7 | ✓ 16.5 | ✓ 18.0 |
| 5a Jernvinneveien | 2 | ✗ 12.4 | ✓ 3.0 | ✓ 11.0 | ✓ 12.2 | ✓ 12.8 |
| A1 | 0 | ✓ 0.9 | ✓ 0.4 | ✗ 5.6 | ✗ 2.8 | ✗ 1.8 |
| A2 C07 | **4** | ✓ 0.0 | ✓ 0.1 | ✓ 13.2 | ✓ 14.7 | ✓ 13.3 |

Also: bevis README records DOM 604.19 / DTM 593.79 at candidate 1, i.e. **c. 10.4 m of canopy at the box marker**. This conflicts with K0 (box in an opening) at the exact published point. The report says the five passing positions lie within c. 200 m (points 1 and 1b are the extremes), so the marker may be only representative.

---

## 16. Access (PDF Ch. 13, p.14)

Criteria:
- road or tractor road **100–900 m** away (5–10 min);
- at least **5 m rise** from the road («OPPOVER», "uphill");
- **no river crossing** in a straight line («ikke farlig terreng», "not dangerous terrain").

«Veiretningen omkring 130° («KOM FRA DEN VEIEN ←») er brukt mykt. Nærmeste kartlagte vei er ikke nødvendigvis der bilen sto, og traktorveier er ikke nødvendigvis kjørbare.» ("The road direction around 130° is used softly. The nearest mapped road is not necessarily where the car stood, and tractor roads are not necessarily drivable.")

[INT] How 130° is derived (short report kort p.7 and community innhold.ts:190): the ← arrow points to image-left. With the camera looking ~221° from the NE of the box, image-left is ~130° (SE). So the car/road is presumed SE of the box.
- Caveats: the HOGD board's → arrow refers to where she walked «I GÅR» (§5). The 130° mapping assumes the arrow is drawn in camera-image coordinates.

| Point | Nearest road | Direction | Rise | Note |
|---|---|---|---|---|
| C06 Gålaveien | 156 m, tractor road | 147° | +13 m | straight line crosses **Nørdre Eldåa** |
| C07 Gålaveien | 170 m, tractor road | 153° | +11 m | crosses Nørdre Eldåa; ravine c. 24 m deep |
| C23 Messelt | 507 m, tractor road | 129° | +32 m | only streams; no building within 1.4 km |

Fig. 9 (`figurer/bro_sjekk_A2.png`, 360 × 360 m crop; DTM hillshade, DOM hillshade, DOM−DTM):
- At C07, Nørdre Eldåa runs in a ravine c. **24 m below the road end** and **35 m below the point**.
- «Laserdataene viser ingen bro. Den eneste kartlagte forbindelsen uten å krysse elva er en sti fra Eldådalsveien på ca. 2,5 km.» ("The laser data show no bridge. The only mapped connection without crossing the river is a path from Eldådalsveien of c. 2.5 km.")
- Later caveat: the missing bridge alone does not prove wading is the only way (PDF p.17; PRESISERINGER:27).

---

## 17. New images and night (PDF Ch. 14, p.14–15) [P-STREAM + MODEL]

- **Morning images 21.09 10.15–10.45 (1920 × 1080):** diffuse light throughout, no direct sun. These revealed the stump error and gave the ten landmarks.
- **30 consecutive frames around 15.01:** cover only one second; no new information.
- **Night clips 21.–23.09:** «ingen bevegelige eller forbigående lys utenfor kassen» ("no moving or passing lights outside the box").
- **Flagged «billys» ("car light") 22.09 21.35:**
  - The left part of the image becomes **14 levels darker for c. 55 seconds**, while reflections in the glass are unchanged.
  - Fig. 10 title: «Lysnivå over tid: steg ned 49,8–50,3 s og gradvis opp ca. 101–105 s, nesten bare i venstre kant» ("light level over time: step down at 49.8–50.3 s and gradually up at c. 101–105 s, almost only at the left edge"). Also a ratio image «Forhold 150 s / 80 s: økning i venstre kant» ("ratio 150 s / 80 s: increase at left edge").
  - «Mest sannsynlig er det en lampe ved utstyret som slås av.» ("Most likely a lamp by the equipment being switched off.")
  - At the same time Anja holds up «DET ER INGEN LYS RUNDT KASSEN» (median of 100 frames in Fig. 10). «Ingen retning til vei eller hus.» ("No direction to road or house.")
  - The PDF's Ch. 18 says «Billys-hypotesen er lagt til side» ("the car-light hypothesis has been set aside").
- Night frame visible in Fig. 10: three bright lights on the box frame (IR/lamps) and the «1116 897 KR» sign.

---

## 18. Website, code and support apparatus (PDF Ch. 15, p.15)

- Campaign page, hunt rules, terms and **16 JavaScript files** read: «uten funn av stedsinformasjon» ("no location information found").
- An unusual **meta tag** on all campaign pages, probably a verification key.
- Not examined: the Gatsby `page-data` file returned **403**.
- Source maps: per default.no, the horde.no source maps show a code game (Kodejakten) but no place text.
- Deliberately not done: attempts against the app's API. The terms forbid «angrep mot Horde sine tekniske systemer» ("attacks on Horde's technical systems"), which may lead to disqualification.
- **Support apparatus** [INT]: personnel nearby, breaks, the bed carried in by day, IR light, and power and network for **1080p around the clock**. «Det peker mot en base utenfor synsvidde, men innen kort gange, og kjørbar adkomst for utstyr. Det gir ingen retning.» ("It points to a base out of sight but within a short walk, and drivable access for equipment. It gives no direction.") PRESISERINGER:29 caveats this.

---

## 19. Combined run and ranking (PDF Ch. 16, p.16–17) [MODEL]

The whole model was re-run without the stump distance: the six earlier areas plus seven new ones from default.no's top area (five east of the Glomma, Myklebysæterveien, and punkt 7 as P2). Number of positions (10 m grid) passing each stage:

| Area | Terrain + forest | Access | Morning sun | Access + sun | + temperature |
|---|---|---|---|---|---|
| Birkebeinerveien (A1) | 10 | 3 | 0 | 0 | 0 |
| Gålaveien (A2) | 20 | 2 | 12 | 0 | 0 |
| Sørlige Messelt | 8 | 2 | 7 | 2 | 0 |
| Nordlige Messelt | 6 | 3 | 6 | 3 | 0 |
| Punkt 7 / P2 | 3 | 3 | 2 | 2 | 0 |
| H2 | 0 | – | – | – | – |
| E1 Madsskardveien øst | 6 | 4 | 5 | 4 | **4** |
| E2 Jernvinneveien | 47 | 28 | 31 | 21 | **21** |
| E3 Madsskardveien | 25 | 4 | 22 | 3 | **3** |
| E4 Ole Evenstads vei | 40 | 26 | 8 | 7 | 0 |
| E5 Madsskardveien nord | 17 | 17 | 2 | 2 | **2** |
| E6 Myklebysæterveien | 9 | 5 | 9 | 5 | **5** |

- «Null skogtreff ved H2 er et modellresultat, ikke en fysisk utelukkelse.» ("Zero forest hits at H2 is a model result, not a physical exclusion.")
- Mapping of report candidates to areas:
  - 1 = E6
  - 2 = E3
  - 3 = Sørlige Messelt
  - 4 = E1
  - 5 = E2
- E4 Ole Evenstads vei and E5 Madsskardveien nord have **no published coordinates** in the PDF.

**Checklist for the best sites** (p.16; «ikke vektet» — "not weighted"; ✓ fits, ~ partly, ✗ fits poorly):

| Criterion | 1 Myklebysæterveien | 2 Madsskardveien | 3 Sørlige Messelt | 4 Madsskardveien øst | 5 Jernvinneveien | P2 Punkt 7 | A1 Birkebeinerveien |
|---|---|---|---|---|---|---|---|
| Morning sun 07.51 | ✓ | ✓ | ✓ | ✓ | ✓ **[contradicted: 5a horizon 8.4°, R13]** | ✓ | ✗ |
| Temperature 21.09 | ✓ | ✓ | ✗ [soft, R12] | ✓ | ✓ | ✗ [soft] | ✓ |
| Road 5–10 min uphill | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | ~ |
| Road direction c. 130° | ✓ **[corrected: road ~94°, R14]** | ✓ | ✓ | ~ | ~ | ~ | ✗ |
| No stream/river < 100 m | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ |
| No building < 300 m | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Several neighbour positions pass | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✓ |
| Trunks in right direction | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ~ |
| Altitude hint 810/875/891 moh | ✗ | ✗ | ✓ | ✗ | ✗ | ~ | ✗ |
| Black-grouse lek registered nearby | ✗ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ |
| In default.no's best area | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |

The black-grouse lek is Artsdatabanken's registration at Evenstadlia, relayed by default.no.

**Assessment (p.16–17), verbatim:**
- «Myklebysæterveien vest (1): flest treff og ingen klare motbevis.» ("most hits and no clear counter-evidence"). "Most hits" is inconsistent with the table (R22).
- «Madsskardveien (2): best veiretning, og øst-siden har ekstra støtte fra orrfuglleiken og aktiv hogst. Men bare to posisjoner består.» ("best road direction, and the east side has extra support from the black-grouse lek and active logging. But only two positions pass.") The table says 3 (R23).
- «Messelt (3): det eneste stedet som passer høydehintet, men i konflikt med temperaturen.» ("the only site fitting the altitude hint, but in conflict with temperature")
- «Madsskardveien øst (4) og Jernvinneveien (5): består modellen, men har bekk nær og vei fra sør.» ("pass the model but have a stream nearby and road from the south")
- «Birkebeinerveien: et betinget alternativ som faller bare på morgensola.» ("a conditional alternative that fails only on the morning sun")

---

## 20. How the recommendation changed (PDF Ch. 17, p.17)

| Round | Best proposal | Why it changed |
|---|---|---|
| 1 | East side at Madsskardveien (default.no stop 1, **61.452, 11.146**) | First review of default.no |
| 2 | Ridge south of Myklebysætra (**61.310, 10.970**) | Eiffel hint read as altitude + flight analysis |
| 3 | Six markers: Gålaveien, Birkebeinerveien, two in Messelt, H2, punkt 7 | Precise flight analysis split into north and south scenarios |
| 4 | C07 at Gålaveien and C23 at Messelt | Terrain and forest model with stump distance |
| 5 | Messelt (S2/S1) | C07 requires a river crossing; morning sun |
| 6 | Myklebysæterveien vest and the east side of the Glomma | Stump distance withdrawn; temperature; new laser data east of the Glomma |

«Det er verdt å merke seg at første forslag (østsiden ved Madsskardveien) og det endelige ligger nær hverandre. Den uavhengige stedstestingen har bekreftet regionen, men flyttet enkeltpunktene.» ("Note that the first proposal and the final one lie close together. The independent site testing confirmed the region but moved the individual points.")
- [INT] The later README says the region is **not** confirmed (R9).
- The "independence" is questionable: round 6 took its areas from default.no's top area.

---

## 21. Disagreements between the analysts (PDF Ch. 18, p.17)

«Arbeidet er gjort av to analytikere som har kontrollert hverandre.» ("The work was done by two analysts who checked each other.") Per KILDER.md and README these are Claude and Codex. Unresolved disagreements, as stated:

- **Birkebeinerveien:** the other analyst recommended checking this area first because temperature fits best among the old candidates. The report ranked it lower because the morning-sun test excludes it, «men testen er ikke originalkontrollert» ("but the test is not checked against the original").
- **Messelt:** he supported Messelt as a practical field round, but not as the most likely location, because of the temperature conflict.
- **Morning sun:** «han godtar ikke en endelig utelukkelse av Birkebeinerveien og Gålaveien før den belyste flaten er identifisert i originalopptaket» ("he does not accept a final exclusion of Birkebeinerveien and Gålaveien until the lit surface is identified in the original recording").
- **Missing bridge:** a bridge missing from map and laser data does not alone prove wading is the only option.
- **Agreement:** «ingen plassering er bekreftet. Stubbeavstanden er trukket tilbake. Billys-hypotesen er lagt til side. Et faktisk stedssamsvar i felt er det som mangler.» ("no location is confirmed. The stump distance is withdrawn. The car-light hypothesis is set aside. An actual site match in the field is what is missing.")

---

## 22. Quality control (PDF Ch. 19, p.17–18)

**Premises table:**

| Premise | Affects | If wrong |
|---|---|---|
| First direct sun at 07.51 | Excludes Birkebeinerveien and Gålaveien | Birkebeinerveien comes back, probably ahead of Messelt |
| Temperatures are outdoor air | Weakens Messelt and punkt 7 | Messelt and punkt 7 are strengthened |
| Altitude hint is metres above sea level | Strengthens Messelt | If it is a lock code, Messelt's special position falls |
| Laser data (DOM) is current | Forest test | Logging after the survey may have removed trees |
| Camera calibration and forest thresholds | All hits | Counts change, rarely which areas |
| «KOM FRA DEN VEIEN ←» means south-east | Road direction | Changes only the order |
| OpenStreetMap is complete | Access | Unregistered bridges or roads may change access |
| Planes and weather point to Østerdalen | The whole search | The box may be elsewhere; only 13 areas examined |

Short report adds: «flere steder har ny hogst i nærheten ifølge Global Forest Watch» ("several sites have recent logging nearby according to Global Forest Watch", kort p.8).

**Errors found and fixed** (p.18): see R1–R7 in §3.

**Not done** (p.18):
- field visit;
- original check of the morning sun 07.45–08.00;
- the full rain window 24.09 10.55–11.15;
- the hint video's original frames (download refused);
- check of DOM vintage;
- investigation outside the 13 areas.

---

## 23. Field plan and maps (PDF Ch. 20, p.18–21)

Map legend: terrain (hillshade and 5 m contours), tree height (green), roads (red; dashed = tractor road), streams (blue), camera and field of view (orange), nearest road point (red square). «Veipunktet er ikke kontrollert som lovlig parkering, og den prikkede linjen er luftlinje, ikke sti.» ("The road point is not checked as legal parking, and the dotted line is a straight line, not a path.")

**What to look for on site** (p.18): «en liten lysning med kassen, en skrå død stamme bak, en bjørk med skjev nedre stamme til høyre, tette mørke stammer til venstre og høye furuer bak (figur 6)» ("a small clearing with the box, a slanted dead trunk behind, a birch with crooked lower trunk to the right, dense dark trunks to the left and tall pines behind").

Map coordinates, read from the rendered maps (p.19–21; also `figurer/kart_*.png`):

| Map | Point | Lat | Lon | Notes |
|---|---|---|---|---|
| Kart 1 «Myklebysætervegen vest (E6)» | 1 | 61.39950 | 11.03156 | «Fem posisjoner består innenfor ca. 200 m» ("five positions pass within c. 200 m"); kort p.9: «1 og 1b markerer ytterpunktene» ("1 and 1b mark the extremes") |
| | 1b | 61.39770 | 11.03178 | |
| | vei (road point) | 61.39921 | 11.04086 | main road (red solid) running N–S; 600 m contour west of the points |
| Kart 2 «Madsskardvegen, traktorveg (E3)» | 2 | 61.44432 | 11.12340 | |
| | vei | 61.44206 | 11.13007 | end of the dashed tractor road; a stream (blue) runs N–S just east of the road point |
| Kart 3 «Feltsone Messelt» | S1 | 61.45713 | 10.83615 | «fire kontrollpunkter fra samme veiende (traktorvei OSM 632102560)» ("four check points from the same road end, tractor road OSM 632102560"); kronehøyde ("crown height") ≥ 2 m shown green |
| | S2 | 61.45448 | 10.84063 | |
| | N1 | 61.45998 | 10.84925 | label partly occluded; read from the full-res figure |
| | N2 | 61.45986 | 10.85133 | «N1 og N2 over åpen myr er svakere» ("N1 and N2, across open bog, are weaker") |
| | veipunkt | 61.45425 | 10.84350 | |
| Kart 4 «Madsskardvegen øst (E1)» | 4a | 61.45182 | 11.14283 | |
| | 4b | 61.45179 | 11.13851 | |
| | vei | 61.44828 | 11.14333 | road to the south (red solid); a large stream NE of the points |
| Kart 5 «Jernvinnevegen (E2)» | 5a | 61.43511 | 11.14349 | |
| | 5b | 61.43444 | 11.13907 | |
| | 5c | 61.43531 | 11.13483 | |
| | vei | 61.43345 | 11.14330 | road E–W south of the points; streams just north of 5a/5b and along the road |

Safety (p.21): «Ferdsel skjer på eget ansvar. Følg allemannsretten, ikke kjør forbi bommer, bruk synlige klær i jakttiden (elgjakta pågår) og ta med fulladet telefon. Ikke forstyrr mannskapet, og ikke forsøk å åpne eller flytte kassen uten koder.» ("Travel at your own risk. Follow the right to roam, don't drive past barriers, wear visible clothing in hunting season (elk hunt ongoing) and bring a charged phone. Don't disturb the crew, and don't try to open or move the box without codes.")

---

## 24. Appendices (PDF p.22)

**A – Glossary:**
- DTM = ground without trees and buildings (1 m).
- DOM = top of trees and buildings.
- CHM = DOM − DTM.
- ADS-B = aircraft position and altitude signals collected by volunteer receivers.
- MET Nordic = MET's hourly weather maps at 1 km.
- Azimuth = compass degrees from north.
- Høydevinkel ("elevation angle") = angle above or below the horizon.
- M0, B1–B5 = measured ground points.
- K0–K4 = forest criteria.
- Strømtid = clock time in the broadcast, «ca. 22–45 s etter virkeligheten» ("about 22–45 s behind reality").

**B – Files and reproducibility:**
- The zip package is said to contain `alle_kandidatposisjoner.csv` (193 positions with all test values), field maps, the camera model `hj_modell.py` with run scripts, and access, trunk and sun calculations.
- Earlier interim reports (version 1–9 of the joint status report) are kept separately.
- «Beregningene kan gjentas med Kartverkets offentlige høydedata, OpenStreetMap og METs arkiv.» ("The calculations can be repeated with Kartverket's public elevation data, OpenStreetMap and MET's archive.")
- **Package not published** (R25).

**C – Sources:**
- Horde AS campaign page, hunt rules and terms (horde.no/gjeldfri/hordejakten)
- YouTube EQHgfmZicc8
- default.no (open log, clip archive, board log, maps, working notes)
- Kartverket DTM1/DOM (NHM)
- MET Nordic analysis and Nordic radar mosaic (thredds.met.no)
- OpenStreetMap (ODbL)
- adsb.lol
- community map MagnusPladsen/hordejakten-2026
- Børsen/Dagbladet interviews with Anja and the Horde CEO
- Artsdatabanken (via default.no), black-grouse lek
- Store norske leksikon, Yr and UT.no

«Denne rapporten er uavhengig og har ingen tilknytning til Horde. Den er ment som støtte til egen vurdering, ikke som en fasit.» ("This report is independent and has no connection to Horde. It is meant as support for your own judgement, not as an answer key.")

---

## 25. Master list of every coordinate in or derived from the report

| Name | Lat | Lon | Elev (moh) | Source | Status |
|---|---|---|---|---|---|
| Cand. 1 Myklebysæterveien vest (E6), box ca. | 61.3995 | 11.0316 | 594 | PDF p.1 | historical rank 1; not current (R8); road bearing 94° (R14); bevis K0 fails at marker |
| Cand. 1 map point | 61.39950 | 11.03156 | — | PDF p.19 | |
| Cand. 1b | 61.39770 | 11.03178 | — | PDF p.19 | extreme of the 5 passing positions |
| Cand. 1 road point | 61.3992 / 61.39921 | 11.0409 / 11.04086 | — | PDF p.1, p.19 | walk c. 500 m west, 30 m up |
| Cand. 2 Madsskardveien traktorvei (E3) | 61.4443 (61.44432) | 11.1234 (11.12340) | 598 | PDF p.1, p.19 | historical rank 2 |
| Cand. 2 road point | 61.4421 (61.44206) | 11.1301 (11.13007) | — | PDF p.1, p.19 | walk c. 440 m NW, 45 m up |
| Cand. 3 Sørlige Messelt S1 (= C23) | 61.4571 (61.45713) | 10.8362 (10.83615) | 898 | PDF p.1, p.12, p.20 | historical rank 3; only site fitting altitude hint |
| Cand. 3 S2 | 61.4545 (61.45448) | 10.8406 (10.84063) | 876 | PDF p.1, p.20 | |
| Messelt road point | 61.4543 (61.45425) | 10.8435 (10.84350) | — | PDF p.1, p.20 | S1 c. 500 m, S2 c. 155 m; OSM way 632102560 |
| Messelt N1 | 61.45998 | 10.84925 | — | PDF p.20 | weaker (open bog) |
| Messelt N2 | 61.45986 | 10.85133 | — | PDF p.20 | weaker |
| Messelt horizon points | 61.455 / 61.460 | 10.840 / 10.850 | — | PDF p.8 | evening-sun table |
| Cand. 4 Madsskardveien øst (E1) 4a | 61.4518 (61.45182) | 11.1428 (11.14283) | 647 | PDF p.1, p.20 | historical rank 4; stream 41 m away |
| Cand. 4b | 61.45179 | 11.13851 | — | PDF p.20 | |
| Cand. 4 road point | 61.4483 (61.44828) | 11.1433 (11.14333) | — | PDF p.1, p.20 | walk c. 400 m north, 21 m up |
| Cand. 5 Jernvinneveien (E2) 5a | 61.4351 (61.43511) | 11.1435 (11.14349) | 556 | PDF p.1, p.21 | historical rank 5; horizon 8.4° (R13) |
| Cand. 5b | 61.43444 | 11.13907 | 542.5 (bevis) | PDF p.21 | horizon 7.3° |
| Cand. 5c | 61.43531 | 11.13483 | 528.0 (bevis) | PDF p.21 | horizon 6.6° |
| Cand. 5 road point | 61.4335 (61.43345) | 11.1433 (11.14330) | — | PDF p.1, p.21 | walk c. 190 m north, 15 m up |
| A1 Birkebeinerveien | 61.449 / 61.4487 | 10.977 / 10.9775 | ~605 (bevis terrain) | PDF p.1, p.9 | default.no site-finder top; conditional alternative; exact point weak forest (R16); = 61°26′55.3″N 10°58′39.0″E (README:17) |
| A2 Gålaveien C07 | 61.4625 (61.46254) | 10.9751 (10.97512) | ~365 (bevis) | PDF p.12 | best forest match (old B3); needs Nørdre Eldåa crossing |
| A2 C06 | 61.46236 | 10.97495 | — | bevis punkter_v6.csv | side ray no ground hit within 228 m |
| Punkt 7 / P2 | ≈ 61.374–61.375 | ≈ 10.976–10.98 | 800–900 band | Fig. 1, Fig. 2; bevis G15 61.37447, 10.97722 | not given numerically in the PDF |
| H2 | ≈ 61.355 | ≈ 10.99 | — | Fig. 1 (approx.) | zero forest hits (model) |
| Round 2 ridge south of Myklebysætra | 61.310 | 10.970 | 790–911 band | PDF p.17 | superseded |
| First-flight search points 1–7 | see §8 | | | Fig. 2 (approx.) | superseded |
| Myklebysætra (ca.) | ≈ 61.364 | ≈ 10.993 | 800–900 | Fig. 2 | |
| Myklebysjøen | ≈ 61.319 | ≈ 10.902 | 989 | Fig. 2 | |
| default.no stop 1 Madsskardveien øst for Glomma | 61.4520 (61.452) | 11.1460 (11.146) | — | PDF p.9, p.17 | round-1 proposal |
| default.no fusion top cell | 61.45 | 11.10 | — | PDF p.9 | 11 % within 10 km, 29 % within 25 km |
| default.no fusion best area | 61.35–61.47 N | 10.97–11.15 E | — | PDF p.9 | |
| Only clear radar rain cell 24.09 11.05 | 61.28 | 10.92–10.96 | — | PDF p.8 | |
| Evenstad (map label) | ≈ 61.43 | ≈ 11.08 | — | Fig. 1 | |
| E4 Ole Evenstads vei; E5 Madsskardveien nord | — | — | — | PDF p.16 | **no coordinates published** |
| Weather test region "Østerdalen" | 60.5–61.8 N | 10–12.5 E | — | PDF p.7 | |

---

## 26. My own derived checks (computation, not in the report)

WGS84 geodesic distance and bearing from each box/map point to its road point (pyproj):

| Point | Distance | Bearing box → road | Report's text |
|---|---|---|---|
| 1 | 498 m | **94°** (E) | "c. 500 m westward" from road; «veien kommer fra øst» ("the road comes from the east") → confirms PRESISERINGER:12, not 130° |
| 1b | 513 m | 71° | |
| 2 | 433–436 m | **124–125°** | "c. 440 m NW" → closest to 130° of all candidates |
| S1 | 499–507 m | **129°** | "c. 500 m" |
| S2 | 155 m | 100° | "155 m" |
| N1 | 708 m | 206° | from the same road end |
| N2 | 752 m | 214° | |
| 4a | 391–395 m | **176°** (S) | "c. 400 m north" → road from the south |
| 4b | 468 m | 147° | |
| 5a | 179–185 m | **183°** (S) | "c. 190 m north" → road from the south |
| 5b | 251 m | 116° | |
| 5c | 497 m | 115° | |

Separations: 1–1b 201 m (matches "within c. 200 m"); 4a–4b 230 m; 5a–5c 463 m; S1–S2 380 m. The "A1" DMS point in README:17 is 0.6 m from 61.4487, 10.9775 (matches "within 1 m").

---

## 27. Later cross-checks on the bevis branch that bear on the report (model outputs; details belong to the bevis-branch source note)

`/home/user/test/data/raw/mk_bevis/bevis/claude-2026-09-25/`:

**`horisont/horisont_api_resultat.txt`**: terrain horizon toward 98.8° from Kartverket's point API.

| Site | Ground | Horizon | Obstruction |
|---|---|---|---|
| 1 | 593.8 moh | 0.5° | 3,200 m, 623 moh |
| 2 | 597.6 moh | 1.8° | 2,425 m |
| S1 | 898.1 moh | −0.4° | — |
| S2 | 876.6 moh | −0.5° | — |
| 4 | 646.4 moh | 3.8° | 1,475 m |
| **5a** | 555.8 moh | **8.4°** | 800 m, 676 moh |
| **5b** | 542.5 moh | **7.3°** | 1,050 m |
| **5c** | 528.0 moh | **6.6°** | 1,300 m |

**`horisont/terrain_resultat.txt`**: 1 m DTM, from 0 m and 20 m, at az 97/99/101. Sun: 07:47 az 98.1 el 5.30; 07:50 el 5.65; 08:00 az 100.9 el 6.80.
- A1 horizon **11.0°** at 0 m (ridge 269 m away, 659 moh; site 605).
- A2 C07 2.6–2.8° (site 365).
- 5 Jernvinneveien 8.3–8.4° at 0 m and 7.0–7.1° at 20 m.

This matters because the PDF says A2 fails morning sun (only 12 positions pass, none with access). The bevis C07 horizon of 2.6° is below 5.7°: **terrain alone does not shade C07 at 07.51**. The report's A2 failure was therefore about access, not sun at C07 itself. That is consistent with R6.

**`horisont/canopy2_resultat.txt`**: share of the visible top-right patch in direct sun at 07:40–08:30. Only candidate 2 (Madsskardveien) is lit from 07:44 (55 %). A2 C07 is lit from 07:47 (4–8 %), rising to 66 % at 08:00. Candidates 1, 3, 4, 5 and A1 show 0 %. The bevis README says the crown test «ikke skiller» ("does not discriminate").

**`horisont/kkrav_resultat.txt`**: see §15. Candidate 1: 0/25; A2 C07: 4/25 (best).

**`adsb/fly_2109_resultat.txt`**: see §8.

---

## 28. Internal inconsistencies and discrepancies I found (beyond PRESISERINGER's list)

1. **B3 elevation angle.** Table p.10 gives −3.4 to −1.8°; the Fig. 4 label gives −3.7…−2.0°.
2. **Morning-sun threshold.** Stated three ways:
   - full p.8: «høyere enn ca. 6,5°» ("higher than c. 6.5°");
   - kort p.5 text: «høyere enn ca. 6°»;
   - kort p.5 test definition: «høyst ca. 6,5°» ("at most c. 6.5°");
   - Fig. 3 plots the line at 5.7° (the sun's elevation).
   The ~0.8° margin is not explained. Tree-top vs ground and refraction are not mentioned.
3. **Candidate 5 morning-sun ✓** conflicts with its own marker horizon of 8.4° (bevis/Codex). In Fig. 3, E2 green dots span ≈ 3–11°, so the 31 passing positions are not at the published 5a marker.
4. **Temperature criterion** is not stated in the full report. The black 8 °C line in Fig. 1 suggests the board's lower bound, yet 7.5–7.6 °C (candidates 2, 4) get ✓. The criterion (day 10–14 °C, 19.35 7–12 °C) is only in kort p.5.
5. **"Madsskardveien (2 and 4)" share one temperature row** (11.5–11.6 / 7.5–7.6), though they are c. 1 km apart.
6. **The «KOM FRA DEN VEIEN ←» / «…HOGD… →» row** elides «I GÅR». The → arrow refers to a walk the day before (23.09), not necessarily the arrival (§5).
7. **Whiteboard wording** differs from the bevis readings of board images: «UJEVNT» vs «KUPERT» (18.44); «TIL VENSTRE» is missing from «4 STORE STEINER…» (19.38).
8. **«118–120 GR ØST» is filed under camera direction**, but it is the Horde sign's pointing direction. The sign was later removed (community log).
9. **default.no drive plan**: "40 stops" (PDF) vs 36 stops in the 24.09 17:04 mirror (`plan.json`). Stop 1 is the same.
10. **"Punkt 7 / H2" temperature row** (9.5–10.4 / 6.4–6.7) merges two sites. Kort p.6 lists Punkt 7 alone as 9.5 °C / 6.4 °C.
11. **25.09 board paraphrase** omits «PÅ DAGEN, OG PÅ NATTA DERSOM DET IKKE ER HELT STJERNEKLART» ("by day, and at night unless completely starry"). The report uses the shortened form to argue that reactions may be sound-based.
12. **Candidate 1 is described as having "Fem naboposisjoner består"** ("five neighbour positions pass", p.1). The bevis 5×5 neighbourhood test at the marker gives 0/25. Different neighbourhoods may explain this, but it is unreconciled.

---

## 29. Open questions

- Which image surface is lit at 07:47–07:51 (crown, trunk, ground)? What horizon threshold follows for each candidate? (Issue #2; the original recording 07:45–08:00 has not been checked.)
- Are the board temperatures outdoor or box-interior air? «ISH 16°» on 23.09 evening is suspicious.
- Is "2,7 eiffeltårn" an altitude (810/875/891 moh) or a lock code (0810/0891; a 5-digit variant such as 00891/00810 for the door)?
- Which plane (if any) did she react to on 21.09 21:29 (shooting-star ambiguity) and on 22.09 20:32–20:36 (SAS39A vs NOZ55J)? The north/south split depends on this.
- Is «KOM FRA DEN VEIEN ←» drawn in camera-image coordinates? Does the → HOGD arrow («DER JEG GIKK I GÅR») describe a 23.09 break walk rather than the arrival route?
- DOM vintage per candidate: has logging since the survey changed K0–K4?
- Coordinates of E4 (Ole Evenstads vei), E5 (Madsskardveien nord), H2 and punkt 7/P2 are not published. The 193-position CSV (`alle_kandidatposisjoner.csv`) is unpublished.
- Where is Artsdatabanken's Evenstadlia black-grouse lek, numerically? The PDF gives no coordinate.
- The badger/«Olivenoljestativ» app item and the olive oil → olivine (Åheim/Almklovdalen) lead are unverified.
- The region outside Østerdalen is unexamined: only 13 areas of 1.6 × 1.6 km were tested.

---

## 30. Supplementary details found only in the short report (kortrapport, same date)

- Camera height **1.1–1.9 m** above ground (kort p.4).
- Hits refined on a **2 m** grid (kort p.3).
- Terrain requirements: ground under box 4.3–5.9 m, ground edge 8–250 m, birch foot 12–45 m (kort p.5).
- Test definitions (kort p.5):
  - access = road or tractor road 100–900 m away, ≥ 5 m rise, no river crossing;
  - morning sun = east horizon ≤ c. 6.5°;
  - temperature = modelled day 10–14 °C and 19.35 7–12 °C.
- Fig. 4 caption (kort p.6): «Ved Birkebeinerveien og Gålaveien ligger alle posisjoner med adkomst over linjen» ("at Birkebeinerveien and Gålaveien all positions with access lie above the line").
- Birds (kort p.8), «Gule og grønne fugler»: fits grønnsisik (siskin), korsnebb (crossbill; females/young yellow-green), kjøttmeis (great tit) and fuglekonge (goldcrest). default.no detected furukorsnebb (parrot crossbill), kjøttmeis and blåmeis (blue tit) in the day-1 audio. «støtter barskog, men skiller ikke mellom stedene» ("supports coniferous forest but does not separate the sites").
- Messelt is «rangeres høyt fordi høydehintet kan være et bevisst stedshint» ("ranked high because the altitude hint may be a deliberate location hint", kort p.8).
- default.no flights (kort p.7): the planes of 21.09 21.29 and 22.09 20.32–20.35 «var innflyginger sørover gjennom Østerdalen» ("were southbound approaches through Østerdalen"). default.no's best cell 61.45, 11.10 is «like ved stedene 2, 4 og 5» ("right by sites 2, 4 and 5").
- Access (kort p.7): «Anja skrev at hun gikk 5–10 minutter fra bilen, at det gikk oppover, at hun gikk 2 minutter inn i skogen, og tegnet at hun kom fra venstre i bildet, altså fra sørøst (ca. 130°).» ("Anja wrote that she walked 5–10 minutes from the car, that it went uphill, that she walked 2 minutes into the forest, and drew that she came from the left of the image, i.e. from the south-east, c. 130°.")
