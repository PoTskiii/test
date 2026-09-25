# Hordejakten 2026: a discovery timeline rebuilt from git history

**Scope.** This is a timeline of what the two community repositories learned, added, changed and withdrew between 23.09 and 25.09.2026. It is built from their commit history.

- `/home/user/test/data/raw/magnus`: MagnusPladsen/hordejakten-2026. 150 commits, from 23.09 14:15 to 25.09 21:04 CEST. HEAD and FETCH_HEAD are the same commit, `68faa86`.
- `/home/user/test/data/raw/mkekeoooo`: mkekeoooo/hordejakten-2026, all branches. 13 commits on 25.09.
- `/home/user/test/data/raw/mk_bevis`: the branch `bevis/claude-2026-09-25` of the mkekeoooo repository.

**Method.**
- I ran `git log FETCH_HEAD` with full messages.
- I ran `git log -p --unified=0` on `src/data/innhold.ts` (107 commits touch this file), `src/data/teorier.ts` and `src/data/lag.ts`.
- I ran `git show` on data commits. I recovered removed JSON items and one deleted image with `git show <sha>^:<path>`.
- I looked at 12 whiteboard and stream images and at the deleted image.
- I extracted the text of the mkekeoooo PDF reports.

The raw extracts are saved in `/home/user/test/evidence/sources/git_history_raw/`:
- `innhold_patches.txt`, `teorier_patches.txt`, `lag_patches.txt`, `magnus_log.txt`, `mk_patches.txt`
- `removed_birkebeiner_items_e431102.json`
- `deleted_hordeai-grevling_from_996369d.jpg`

**Time conventions.**
- Commit times are shown in CEST (UTC+2). The magnus commits are all recorded in +0200. Nine mkekeoooo commits are recorded in −0700; I converted those by adding 9 h. For example, `01:40 -0700` becomes 10:40 CEST.
- A commit time is when something was added to the repository, not when it happened. For example, the 24.09 whiteboards were added in bulk between 18:26 and 18:49 after a gap of 22 hours with no commits.
- Whiteboard times in the magnus `TAVLE` log are stream time. The repository says: "Tider er streamtid (trolig 20 sek–1 min forsinket, vi tipper)" (`innhold.ts:880`).
- ADS-B times are real time.

**Evidence labels used below.**
- **[HINT]**: an organiser hint (app, Horde AI, Horde media, Alf).
- **[PRIMARY]**: something visible or audible on the stream, or on Anja's whiteboard ("tavla").
- **[COMMUNITY-OBS]**: an observation by the community, such as ADS-B matching, a field check or screenshots.
- **[INTERP]**: an interpretation or theory.
- **[MODEL]**: model output (default.no fusion, the magnus Bayes model, the mk horizon and forest tests).
- **[RETRACT]**: a retraction, correction or reversal.

---

## 0. Key findings

1. **The approach bearing flipped twice.**
   - **23.09 14:30.** The first reading was that 118° is the direction from the box to the parking. Standing at the car, the box would then be at about 298°.
   - **23.09 15:22.** The repository flipped this. The sign was placed west-north-west (WNW) of the box, pointing at it. The walk from the car would then be about 120°, and the search sector was turned to 120°.
   - **24.09 18:35.** «KOM FRA DEN VEIEN ←» flipped it back: the car is to the south-east (SE) and the walk is about 300° ±25°.
   - **24.09 19:55.** The phrase «mot kassen» (towards the box) was removed as unverified interpretation.
   - Two current hints, `retning118` (`innhold.ts:133-142`) and `skilt` (`innhold.ts:623-631`), still carry the superseded 15:22 text. The file therefore contradicts itself.
   - On 25.09 a clip from 16:20 showed a HORDE arrow sign again. It stands to the right of the box in the image and points left, towards the box and south-east.
2. **Everything about Birkebeinervegen was removed without a stated reason** (`e431102`, 25.09 14:12).
   - The removed data included default.no's highest-scoring site-finder cell: `61.44874, 10.97747`, 605 moh, score 0.995, abs 0.12638.
   - It also included four plan stops (ranks 10, 18, 20 and 38) and three field pins.
   - That site is the same point as candidate "A1" in the mkekeoooo report (61°26′55,3″N 10°58′39,0″E, within 1 m).
   - The only field note says it was blocked by a gate and "bare sett fra veien. Ikke ferdig sjekket." It is **not** documented as searched.
3. **The riverbank idea was dropped** (25.09 20:53, `6c421a9`).
   - "Riverbank" was first read as the song, then as the artist in «Goldenrod · Riverbank».
   - It was dropped after the whiteboard from 22.09 19:19:32 was added: «INGEN VANN ELLER VANNLYDER, FØLER IKKE DET ER VANN I NOE NÆRHET».
4. **The stream delay was downgraded.** It went from "45 sek (bekreftet)" to "trolig 20 sek–1 min (vi tipper)" on 25.09 at 11:29.
   - default.no measured about 22 s (mk_bevis README).
   - The code constant `STREAM.forsinkelseSek` is still 45 (`innhold.ts:10`).
5. **Several status downgrades followed on 24.09 at 19:55** (`893318a`).
   - The FROLAND → «Ekornet kan klatre» and LD6788 → «ENKODE» app replies went from Bekreftet to Usikker, because they are only known from shared screenshots.
   - The blindfold claim went from Bekreftet to Usikker.
   - The claim that Anja was "carried the last 5–10 min" was replaced by "5–10 min å gå fra bilen, og hun tror det gikk oppover".
   - The door lock became "5 eller 6 siffer".
6. **The 21.09 21:29 "plane" gesture is disputed.**
   - mk_bevis (from default.no osint_notes): she signalled a shooting star («stjerneskudd») at 21:27:42, and at 21:29:10 the chat asked her to point at it. The pointing at 21:29:38–53 may be about the shooting star.
   - mkekeoooo later retracted using the arm's angle as a measurement of the plane's elevation (`d1fbac0`).
   - magnus still says «pekte rett opp».
7. **Other items were added and then withdrawn on 25.09.**
   - The Horde AI «grevling» reply was added at 14:29 and removed at 14:56 as "not repeatable in a new chat".
   - The Terje T-shirt was announced as new at 12:43, then declared "not new" at 13:01. The app text itself says it was popular «under forrige Hordejakt».
   - «Folk skal være ved kassen og prøve koder» (23.09 15:00) was removed as fake on 25.09 at 11:16.
   - The pink «ingen sopp» exclusion layer was removed as incorrect on 23.09 at 19:13.
8. **The mkekeoooo archive demoted its own report.** At 12:31 CEST on 25.09 the numbered candidate list became "historikk, ikke gjeldende rangering".
   - The retracted items are: the B3 stump distance (17–44 m), the arm-angle inference, weather exclusions of the west and south as hard limits, and temperature as a hard filter.
   - The "bever" (beaver) reading was corrected to «grevling» (badger), with the item name «Olivenoljestativ», a price of 100 000 points, and the shipping text «Nesten Helt Hjem».

---

## 1. Master timeline (chronological)

Entries are ordered by when they entered a repository. When the event time is known it is given separately, with stream or real time stated. Magnus SHAs are 7-character short hashes.

### 1.0 Events before 23.09 14:30, as first recorded in the initial scaffold (`c0c849b`, 23.09 14:30)

These items are all present in the first version of `innhold.ts`.

**Hints**
- **[HINT]** The Horde app "Verv en venn" (refer a friend) shows letters. First recorded order: «I S N D O R U E M H» (`c0c849b`). The note says: "Trolig et anagram. «MINUS HORDE» er foreslått."
- **[HINT]** "Kredittskår" plus typing «terje» gives «Du fant et hint! 5008». 5008 is the postcode of Horde AS, Lars Hilles gate 20A, Bergen.
- **[HINT]** Sweater numbers «7 10 5 12 / 4 6 18 9» decode as GJELDFRI. Morse code on the trousers decodes as «PREMIE». Caesar +5 on the trousers: "MT→HO, WI→RD, JO→EJ, FP→AK, YJ→TE … = HORDEJAKTEN@…".
- **[HINT]** A Finn.no advert has the solution «Ikke en øy» (not an island). A Horde page «Ho Ho Hint Hint» mentions 072 and 500. There is also Kodejakten at horde.no/secret/kodejakten, first described as "fire minispill som skal gi en firesifret kode til en av låsene når det åpner".
- **[HINT]** YouTube `_KVnuWlzVsE`: a duck appears in a single frame, bottom right, at about 00:15.

**Primary stream observations**
- **[PRIMARY]** A fox, a squirrel and a crow have appeared in the box. On 23.09 a fox was put in the cage.
- **[PRIMARY]** A «Horde» sign carried by two hands, pointing left in the image.

**Whiteboards (stream time), as recorded at 14:30 on 23.09**

| Stream time | Text |
|---|---|
| 21.09 18:31 | «INGEN FLY · INGEN SKYTING · OSLO, SØN KL 04.00 · CA 5–10 MIN Å GÅ FRA BIL» |
| 21.09 18:36 | «INGEN FERGE · KUN BIL · VET IKKE ANG. TUNELLER» |
| 21.09 18:38 | «TROR DET VAR OPPOVER · SISTE 5–10 MIN» |
| 21.09 18:44 | «KUPERT TERRENG · MYE LYNG · HØRER IKKE MYE FRA BOKSEN» (mk_bevis reads «UJEVNT TERRENG»; see §5) |
| 21.09 18:48 | «LIVE 07:00 · NEI, SER KUN SKOG OG KAMERA FRA BOKS» |
| 21.09 18:57 | «PRESENNING · MER ÅPEN SKOG TIL HØYRE FOR MEG» |
| 21.09 19:00 | «INGEN SKYER NÅ · SNART SOLNEDGANG» |
| 21.09 19:32 | «IKKE MØRKT ENDA · FINT VÆR» |
| 21.09 19:35 | «CA 12 °C (DAGEN) · NÅ CA 8–11 °C» |
| 21.09 19:38 | «4 STORE STEINER, KUN STEIN DER» (mk_bevis: «4 STORE STEINER TIL VENSTRE, KUN STEIN DER») |
| 21.09 19:47 | «MØRKT NÅ» |
| 21.09 19:50 | «KLAR HIMMEL» |
| 21.09 21:30 | «FLY (pekte opp, litt mot sørøst)» |
| unknown | «ØST CA 118 · RETNING S…? (siste ord uklart)» |
| unknown | «VIL DERE SE EN BACKFLIP?» |
| 23.09 09:33 | «DET GÅR FINT · TAKK SOM SPØR ♡» |

**Interpretations at 14:30**
- **[INTERP]** «ØST CA 118»: "Fellesskapet tolker det som retningen fra kassen til parkeringen (øst-sørøst). Kameraet står ca. 73°." In other words: "Står du på parkeringen, ligger kassen mot ca. 298° (vest-nordvest)". Alternatively, 118° is the direction to Oslo, putting the box north-west of Oslo (Valdres, Sogn).
- **[INTERP]** The sign points left in the image. "Kameraet ser mot sørvest, så venstre i bildet er omtrent sørøst."
- **[COMMUNITY-OBS]** "Beste treff i flydataene er NOZ56U fra Oslo til Bodø, i stigning". Stream delay: "45 sek forsinket (bekreftet), så ekte tid er ca. 21:29."
- **[INTERP]** «Reven og kråka» (Alf Prøysen, Ringsaker). Froland has a squirrel in its coat of arms. The theories on the map were Froland, Lillehammer and Nøtterøy (the last excluded).

**Model output**
- **[MODEL]** default.no fusion model at 22.09 12:41. Top 5, with the share of probability within 10 km:

| Rank | Area | Point | Share within 10 km |
|---|---|---|---|
| 1 | Østerdalen (Elverum) | [61.45, 11.0] | 4.7 % |
| 2 | Sør for Løten og Koppang | [61.1, 11.0] | 3.1 % |
| 3 | Indre Oppland | [61.75, 8.4] | 2.2 % |
| 4 | Østre Innlandet | [61.1, 11.6] | 2.5 % |
| 5 | Valdres og Hallingdal | [60.9, 8.9] | 1.4 % |

**Facts box at 14:30:** stream delay "45 sek"; "3 låser: 2 på kassen, 1 på døra"; "5–10 min: Gange fra bilen, oppover". The terrain hint said: "Leter du i felt: 400–800 m fra en skogsbilvei".

### 1.1 Wednesday 23.09 (14:30–20:22)

| CEST | SHA | Type | What happened |
|---|---|---|---|
| 14:42 | ecf0260 | [COMMUNITY-OBS] | Plane: "Anja pekte rett opp kl. 21:29:38 og skrev «FLY» kl. 21:30 (streamtid). 49 fly var i lufta. Beste treff er NOZ56U (Oslo–Bodø), som var over Løten i ca. 24 000 fot." Plane point: [60.8705, 11.2481], "ekte tid ca. 21:29:50", 23 892 ft. |
| 14:42 | ecf0260 | [MODEL] | default.no candidates at 22.09 16:42: #1 Rena og Åmot [61.45, 11.1], 4.2 %; #2 Gjerstad og Vegårshei (Agder) [58.75, 9.3], 2.2 %; #3 Indre Oppland [61.75, 8.4], 1.4 %; #4 Nes og Eidsvoll [60.35, 11.2], 1.2 %; #5 Løten og Hamar [61.15, 10.9], 1.1 %. |
| 14:42 | ecf0260 | [HINT] | Official hint video `H_-0LbPSu5s` (22.09): "Bare 0–3 s og 10–12 s viser selve stedet … lav plattform i blåbær- og tyttebærlyng, med gule bjørker og høye furuer bak." |
| 14:42 | ecf0260 | [PRIMARY via default.no] | Timber: "Anja har kjent lukt av tømmer, hørt dunking og sett en lastet tømmerbil." |
| 14:43 | f99df64 | [INTERP] | The letters, now written in order «N O R H E I M S U D», were read as NORHEIMSUND with one N short. "6,5 t … passer med «sov ca. 7 t»". |
| 14:49 | 520fd05 | [PRIMARY/news] | Børsen interview: covered windows; «aner ikke hvor lenge de kjørte»; "sovemaske og headset og ble båret inn i skogen". Field search distance changed from 400–800 m to 300–900 m. Windy blue areas were drawn as excluded. «Plutselig tilbake!» poster (money stacks and two padlocks). |
| 14:59 | 58e737c | [INTERP]→[RETRACT] | Camera changed from "ca. 73°" to "nordøst for kassen og ser mot sørvest (ca. 220° ifølge solbanen)". Open question: the board says Sunday, but Børsen says «siden mandag morgen». A Monday pickup would mean under about 3 h of driving; the stream started at 06:50. Codes 5008, 5528 and 2188 were added. Locks: "2 hengelåser og døra 1, alle med 4 siffer". The poster stacks were reread as card decks, giving 52 and the code 5528. Digeråsen tip: 61°10′43.84″N 11°15′50.13″E, 606 moh. |
| 14:59 | b671b5b | [RETRACT] | NORHEIMSUND downgraded. "HORDE MINUS bruker nøyaktig alle ti bokstavene, uten rest." Model factor lowered from 4 to 2. |
| 14:59 | 4e26d93 | [INTERP] | Sign hands read as Roman numerals ("første viser VII = 7") or as binary. |
| 15:00 | 5b2a319 | [INTERP] | Chat: «Flere som har prøvd seg på koden ved boksen nå by the way. Vi vet hvor det her er hen.» **Removed as fake on 25.09 at 11:16 (`094b3b8`).** |
| 15:02 | 52c0b78 | [COMMUNITY-OBS] | Satellite on 23.09: clear from Kongsvinger to Rena (the side towards Sweden), parts of Vestfold, and Trondheim–Ålesund. Doubt raised about fake sunlight. Tip: Flisa/Haslemoen. |
| 15:05 | cf75140 | [PRIMARY]/[INTERP] | Whiteboard «LAST NED HORDE APPEN». A 118° line drawn from Horde AS in Bergen. "HORDEJAKTEN" minus "HORDE" gives JAKTEN. The hands seemed to change position during 23.09. |
| 15:07 | 3885ab8 | [RETRACT] | Lock count changed from 3 locks to "2 kodelåser med 4 siffer". Tretopphyttene tip (Danseråsvegen 173, squirrel logo). Fredrikstad, Sarpsborg and Halden were overcast all day. |
| 15:15 | bdffb03 | [PRIMARY] | Board reading completed as «ØST CA 118 · RETNING SKILT», meaning the sign direction, confirmed by Anja. The interpretation was still "Mest trolig: veien inn fra parkeringen. Da ligger kassen mot ca. 298° … fra bilen." |
| 15:16 | 6d6d45c | [PRIMARY] | «REVEN HETER BENNY». Bennyøy (Nome) [59.2666, 9.1327] and Benningstad (Løten) [60.7685, 11.3575] pinned. |
| 15:16 | 45200c5 | [COMMUNITY] | Chat: «Det er null tvil, været, sola, skogen og alt.» (Innlandet). |
| 15:17 | 2eb6f94 | [PRIMARY] | «118–120 GR ØST». Box stated as 298–300° from the car. |
| 15:18 | e94d4db | [COMMUNITY-OBS] | A local in Nord-Odal: «Det var tykk tåke her i dag tidlig, hele veien til Sør-Odal og Jessheim». |
| **15:22** | **86d52b8** | **[INTERP] reversal #1** | New sign geometry: "skiltet står vest-nordvest for kassen og peker mot den, og kameraet står nord-nordøst og filmer mot ca. 208°". This gives "fra bilen går du ca. 120° (øst-sørøst)". In `Kart.tsx` the search sector changed from `sektor(pos, 298, 20…)` to `sektor(pos, 120, 20…)`. Bergen line with magnetic declination: about 123°. Also added: «SOLA VAR OPPE FØR 07»; the sun due south at 13:02–13:08, giving 11–12° E; the break place has no windows or wifi. |
| 15:23 | 9ea67b3 | [RETRACT] | Squirrel clue weakened ("finnes over hele landet"), factor 1.1. |
| 15:32 | 6a33959, 015d617 | [PRIMARY]/[INTERP] | «+5» on the sweater. Candidate codes 5013 and 0553. Applying +5 or −5 to the sweater numbers gives LOJQIKWN or BEZGYAMD, which is meaningless. |
| 15:34 | a49eadd | [INTERP] | Trousers decoded: "HORDEJAKTEN@HO…, trolig hordejakten@horde.no". |
| 15:39 | 66e31ce | [HINT]/[RETRACT] | Horde video `1raIm3ANsAI` «Hvordan går det med Anja?» (news time "23.09 kl. 15:30"): «Kjenner jeg dere riktig så vil dere overanalysere denne videoen». It shows +5 on the back, mixed forest with gran, furu and many thin yellow birches, a ladder, a black screen in the box, and three lamps at night. **The 7 h drive time was switched off by default** ("ikke et fakta"). |
| 15:41 | e72a665 | [COMMUNITY-OBS] | Second plane: NOZ9EG southbound over Ringsakfjellet at 21:29 ([61.216, 10.896], about 23 500 ft), passing about 3 km from Tretopphyttene at 21:31. Tip: Nittedalen. |
| 15:43 | eb4093e | [PRIMARY] | Whiteboard sketch. Best reading: «KAMERA» at the top, the box in the middle, «SKILT» on the right. It is hard to read (I viewed the enhanced image). |
| 15:45 | 7983773 | [PRIMARY]→[RETRACT] | «KAMERA 41 ØST»: the camera is at about 41° (north-east) and films about 221°. This replaced "~208°". It agrees with default.no's sun-only estimate of 219–220°, which argues against the fake-light doubt. |
| 15:46 | 6cddb71 | [INTERP] | Froland excluded: "Været i Froland samsvarer ikke". |
| 15:51 | ce85e10 | [COMMUNITY-OBS] searched-empty | «én i chatten har sjekket alle Tretopphyttene og Prøysenstua, uten funn». |
| 15:55 | fe51e10 | [MODEL]/[COMMUNITY-OBS] | default.no audio tags on 21.09: trains at 08:34, 11:29, 14:07; bells at 08:35, 14:00; shots at 14:24, 14:54 (confidence 0.33–0.51). Birds: sidensvans at 07:36 and furukorsnebb. Dew on the roof from 07:00 to 09:40. default.no terrain site-finder hits: **Birkebeinerveien [61.4495, 10.9752]**, Gålaveien, Madsskardveien, Tolvmilskogen, Kirkesjøvegen. Added to the certain facts: "Stille sted: ingen fly på dagtid…". |
| 16:01 | 06b82f0 | [RETRACT] | Audio changed from "trolig støy" to "falsk og går i loop (… identiske lydbiter 22–48 t fra hverandre)". 13 letter readings added. |
| 17:56 | aa81ebf | [INTERP] | Prøysen/Rudshøgda theory: «Sirkus Mikkelikski» (Mikkel Rev, Frøken Kråke, ekornet Nøtteliten). Prøysenstjerna is 27 m tall. NOZ9EG passed 6–11 km away at 21:31. |
| 18:01 | df596d3 | [PRIMARY] | 17:49 (stream): «LYDTETT · SOL · VINDSTILLE». |
| 18:01 | 125f83f | [HINT] from source code | Kodejakten: the server gives one padlock code after all four games are verified. Darts: blue +, yellow −, pink ×, purple ÷. The runner "Alf" is Horde's frontman, not Alf Prøysen. |
| 18:02 | c4c0aa3 | [PRIMARY] | «ELEKTRONISK LÅS PÅ DØRA MED 5 SIFFER». |
| 18:16 | 35ba6b9 | [MODEL] | default.no "klare celler i kveld" (clear cells tonight): #1 Løten og Elverum (skog) [60.9, 11.2]; #2 Rena og Åsta [61.3, 11.2]; #3 Koppang [61.5, 11.0], 8.2 °C; #4 Finnskogen [60.6, 12.35], 8.5 °C; #5 Trysil [61.3, 12.3], 6.1 °C. The "sett + hørt fly" test keeps about 10 % of Norway. |
| 18:17 | b7a2c7f | [COMMUNITY-OBS] | Kodejakten API returns `503 not_configured` on all endpoints, so no code can be obtained yet. |
| 19:01 | 4a9f3ee | [PRIMARY] | 23.09 evening: «FÅR SE BITTELITE · MASSE SOPP · TYPISK FJELLMARK», «IKKE VANN · STEIN + SOPP · MOSE PÅ STEINER», «ISH 16°», «GIKK 2 MIN INN I SKOGEN». |
| 19:04 | 41304dc | [HINT] | Horde's rules: «Ingen på Hordekontoret vet hvor kassen befinner seg…»; «Ikke kle deg ut som elg, hjort eller storfugl. Det er jaktsesong.»; the terms say there is an envelope in the box and no cash; «Anja er på publikums lag». |
| 19:08 | 6763e06 | [COMMUNITY] | Community exclusion map with pink «ingen sopp» and light-blue mountain birch. Powerbank «Xtorm FS5271 27000mAh» gives codes 5271 and 27000. |
| 19:10 | 24c4d59 | [RETRACT] | Lock count became 3: 2 padlocks with 4 digits on the money box, and 1 electronic 5-digit lock on the door. |
| 19:12 | 89d7dc0 | [PRIMARY] | 19:09: «LITE MED FLY HER · SIKKERT MED VILT». |
| **19:13** | **b55eafc** | **[RETRACT]** | "Remove the pink 'no mushrooms' exclusion, which was not correct". Open shares changed: Gjøvik from 44 % to 95 %, Røros from 14 % to 20 %. |
| 19:15 | 405c497 | [PRIMARY] | 19:12: «SKILTET ER BORTE · VET IKKE HVOR». |
| 19:22 | 1971621 | [COMMUNITY] | Analyse tab added: default.no audio lags (23.9 h ×290, 47.9 h ×48 …); hordejakten.vercel.app's "confirmed" list, which includes «Hun reiste i minst 7 timer», «Hun får bind for øynene hver gang hun forlater boksen», «Livestreamen starter 06:40» and «Retningen på kameraet fra henne er 219 grader». The blindfold claim was first marked Bekreftet. |
| 20:03 | fc71636 | [INTERP] | Everything west of 8.4° E marked as excluded, because the exclusion image did not cover it. |
| 20:09 | 602389f | [COMMUNITY-OBS] | Live Kodejakten status check (`POST horde.no/api/spill/status`; `503 not_configured` means off). |

### 1.2 Night of 23.09 to 24.09: events logged later

These were first logged in `addc834` at 24.09 18:26.

- **[COMMUNITY-OBS, unverified]** 23.09 22:27: a screenshot shows FROLAND typed in the Kredittskår word box, and the reply «Du fant et hint! Ekornet kan klatre».
- **[COMMUNITY-OBS, unverified]** 24.09 00:01: a screenshot shows the number plate LD6788 under «Bil & hus», and the reply «Du fant et hint! ENKODE».
- **[COMMUNITY-OBS]** default.no field notes, in the mirrored `pins.json` and `rejected.json`, dated 23.09:
  - 00:30, «BOM / privat vei … Birkebeinerveien-avkjoring mot 61.4495,10.9752. Ga forbi bommen til fots, 500 m». Removed from magnus on 25.09.
  - 00:40, `61.4307, 11.0483`: «privat vei - sjaforen er her NA (23.09 00:40)»; the rejected note says «Sjekket på bakken natt til 23.09: bolighus 7 m unna, ikke boksen» (**searched, empty**).
  - `61.4495, 10.9763`: «Bom på veien 23.09, bare sett fra veien. Ikke ferdig sjekket». This entry still exists in `rejected.json`.

### 1.3 Thursday 24.09 (18:26–19:59); nothing was committed between 23.09 20:22 and 24.09 18:26

| CEST | SHA | Type | What happened |
|---|---|---|---|
| 18:26 | addc834 | [HINT?]/[INTERP] | FROLAND and ENKODE added as **Bekreftet**. Froland changed from excluded to "lite sannsynlig". Code 6788 rated middels. **Downgraded at 19:55.** |
| 18:30 | 7ebb743 | [HINT] | **Horde AI replies «2,7 eiffeltårn stablet oppå hverandre» to "Hordeminus"** (news time "24.09 kl. 17:54"). Asked what it means, the AI says it is only the phrase it was told to use. First computed as 891 m (2.7 × 330). Code 0891. A frame from the Facebook video shows a globe with «Bandar Seri Begawan», «BRUNEI», «MALAYSIA». |
| 18:31 | 2995786 | [RETRACT] | Changed to "300 m uten antenne og 330 m med, så 810 eller 891 m". Code 0810. |
| 18:32 | b03c6a9 | [HINT] | Horde in a comment thread: «Hint til hva kodene kan være ligger i appen 💙». Whiteboard «INGEN PIZZA ENDA». Community 800–900 moh map added. Codes 8915, 0896, 8105. |
| 18:33–18:36 | 4bd3590…caf7bcb | [PRIMARY] | 24.09 boards (order unknown, see `a9eacd9`): «HJELPER VELDIG AT JEG KAN SE DET DERE SKRIVER <3»; «SKAL KLARE Å HOLDE UT TIL NOEN FINNER MEG»; «HJEMMELAGET PEPPERONIPIZZA · DRESSING FRA COOP · KNALLGODT»; «JEG HAR TROA PÅ DERE»; **«KOM FRA DEN VEIEN ← · INGEN STIER»**; «(17:20) INGEN HYTTE I NÆRHETEN SOM JEG VET OM ELLER SER»; «INGEN LYD I BOKSEN OVERHODET, JEG HAR KUN DERE Å UNDERHOLDE MEG. INGENTING ANNET»; «(18:07) MAMMA <3»; «GRÅVÆR HELE DAGEN». |
| **18:35** | **4e65b1c** | **[INTERP] reversal #2** | The «KOM FRA DEN VEIEN ←» arrow points left, which is about 130° with the camera at 221°. The car is SE and the walk goes NW, about 300°. The search sector changed from `sektor(pos, 120, 20…)` to `sektor(pos, 300, 25…)`. The hint text says explicitly: «Merk at dette snur den gamle tolkningen, der kassen lå mot 120° fra bilen.» (`innhold.ts:190`). |
| 18:38 | 679260b | [INTERP] | Kroktjennet/Hemmeldalen lead: a top at about 891 moh [61.2405, 11.01]. Kartverket gives about 887 moh. It lies inside a nature reserve. |
| 18:38 | 9264140 | [RETRACT] | Horde AI summary figures (891 m, 875 m from a 324 m tower, "høyden 2000–2022") are "bare chatboten som regner, ikke et nytt hint". |
| 18:39 | 39e2789 | [HINT] | YouTube «Ingen har funnet Anja enda..»: soldiers and a drone in fog; «men i år har de også plassert en kvinne i en boks med en livestream». |
| 18:42 | 1aab84b | [PRIMARY] | 08:24: «5 SIFFER · GANSKE SIKKER». |
| 18:43 | a269415 | [PRIMARY]/[INTERP] | «2x HENGELÅS 4 TALL · 1x KODELÅS 5–6 TALL · TROR 5». «DET HAR VÆRT HOGD TIDLIGERE DER JEG GIKK I GÅR · GIKK DEN VEIEN →». «SÅ INGENTING SOM IKKE HØRER TIL I EN SKOG I GÅR · PS! HÅPER PÅ PEPPERONIPIZZA». Interpretation: the → arrow (about 310°) and ← (about 130°) are "the same walk". See §2.O for the «I GÅR» ambiguity. |
| 18:44 | 7d0554e | [MODEL] | default.no layers added, fetched 24.09 18:36. plan.json (generated 24.09 17:04) had 40 stops; stop 1 was Madsskardveien øst for Glomma [61.452, 11.146]. |
| 18:44 | a9eacd9 | [RETRACT] | All 24.09 boards were marked by date only: "their order is unknown". The locks board was re-dated from 23.09 to 24.09. |
| 18:46 | 38e9f02, 94558c2 | [HINT] | The letters hint was marked **Løst: HORDE MINUS**. |
| 18:49 | 4d069c1 | [PRIMARY]/[COMMUNITY-OBS] | 11:05: Anja said it was raining. The community says it rained in Rena at the same time. |
| 19:02–19:07 | 71778ff…e4f04b5 | [MODEL] | All default.no layers mirrored: nine fusion variants, flight events (21.09 21:30, 22.09 20:33, 20:35), and "regn siden søndag … glasset foran kameraet har vært tørt" (rain since Sunday, but the glass in front of the camera has stayed dry). |
| 19:49 | e537086 | [MODEL] | 810–891 moh layer: "17 234 spots at 790–911 moh within 900 m of a drivable road (OSM), 12 041 of them with a road to the SE". |
| 19:49 | 4654dfd | [RETRACT] | Kroktjennet: "det går ingen bilvei innen 900 m" (weakened). |
| 19:51 | 197e40e | [INTERP] | "Eiffel Tower in Texas" theory: Texas [60.87812, 12.21229], about 348 moh; Kompassen [60.87639, 12.31426], 302 moh. |
| **19:55** | **893318a** | **[RETRACT]** | "Stop marking unverified things as confirmed". FROLAND and ENKODE went to Usikker (screenshots only). Froland went back to "utelukket". Blindfold went to Usikker. «mot kassen» (towards the box) was removed from the sign hint, which now reads «Horde-skiltet pekte 118–120°». The certain facts changed: "De siste 5–10 min ble hun båret oppover med sovemaske og headset" became "Siste bit var ca. 5–10 min å gå fra bilen, og hun tror det gikk oppover". The door lock became "5 eller 6 siffer (Anja er «ganske sikker» på 5)". Code 6788 went from middels to lav. |
| 19:59 | a141dae | [RETRACT] | Place names checked against Kartverket: NOZ56U was over **Hamar** (near the Løten border), not Løten. "Rena og Åmot" renamed "Rena–Evenstad" (Stor-Elvdal). Bjørneparken moved 1.2 km. |

### 1.4 Friday 25.09

| CEST | SHA | Type | What happened |
|---|---|---|---|
| 08:23 | e96bf5c | [MODEL] | Protected areas where hunting is banned, from Lovdata. |
| 10:40–10:48 | mk e960f5f, deb358a, 30edfa8 | [MODEL] | mkekeoooo publishes a 22-page report, a 12-page summary and 15 figures. The candidate order around Evenstad: 1 Myklebysæterveien vest (61.3995, 11.0316); 2 Madsskardveien traktorvei (61.4443, 11.1234); 3 Sørlige Messelt (61.4571, 10.8362 and 61.4545, 10.8406); 4 Madsskardveien øst (61.4518, 11.1428); 5 Jernvinneveien (61.4351, 11.1435). "Birkebeinerveien, Gålaveien og punkt 7 er fortsatt relevante betingede alternativer." |
| 10:59 | 970c493 | [HINT] (relayed) | Alf on TikTok live, as relayed in chat: «Det er ekte lyd på streamen. Men dere husker kanskje tidligere år, da drev vi å trollet litt med lyden.» «Har reven og anda noe med hint å gjøre? Ja, kanskje.» «Kan være at noen av kodene allerede har kommet.» «Kommer en del viktige hint nå i løpet av helgen.» Audio changed from "falsk/loop" to "Usikkert". |
| 11:00 | 10c2793 | [HINT] (reported) | Shaking the app plays the sound of black grouse lekking («orrfuglleik»). Horde Rewards shows a stuffed animal holding up olive oil, first called a badger («grevling»). |
| 11:01 | 67eb8d0 | [INTERP] | The animal may be Haaland's stuffed raccoon from Texas. |
| 11:02 | ddf93d0 | [INTERP] | Discord tips: **Birkebeinervegen over Ringsakfjellet** [61.36168, 10.84625], 720–1040 moh, "341 steder på 810–891 moh nær vei her, 233 av dem med vei mot sørøst". Finnskogen was judged too low and excluded. **All removed at 14:12.** |
| 11:02 | mk 94a45c1 | — | README style change only. |
| 11:03–11:10 | a1a9e1c, dc35cc6, c7ed3f9, 46b320f | [HINT] (relayed) | Alf: there will be a queue, and «5 timers karantene» if you fail to open the locks. «aldri noe farlig, som å krysse en elv»; wear visible clothes. Asked whether the sound is live or delayed: «Ja, det må du prøve å finne ut av.» |
| 11:07 | 63416f0 | — | The default map now shows only confirmed items. The letters and 5008 no longer pin Norheimsund or Bergen. |
| 11:16 | 094b3b8 | **[RETRACT]** | «Folk skal være ved kassen og prøve koder» removed as fake. The queue and quarantine hint was **upgraded from Usikker to Bekreftet** and its source changed to "Alf på Hordes TikTok-live 25.09" (the "gjengitt i chatten (ikke sjekket ordrett)" qualifier was dropped). Tommsen's A/B/C spots added. |
| 11:21 | 4a22327 | [RETRACT] | "Sol i dag" renamed "Sol 23.09": the satellite image is from the daytime on 23.09. |
| 11:29 | 01ab80d | [PRIMARY] / **[RETRACT]** | 25.09 boards: «OVERSKYET · FLYENE ER SÅ LANGT UNNA AT DET ER UMULIG Å SE PÅ DAGEN, OG PÅ NATTA DERSOM DET IKKE ER HELT STJERNEKLART»; «KAN IKKE TESTE KODER · INGEN HAR FUNNET BOKSEN (siste del litt utydelig)»; 09:49 «INGEN TÅKE»; 09:58 «SIKKERT 5° · TROR DET ER VARMERE»; 10:21 «GJETT RIKTIG SANG · BACKFLIP»; 10:38 «IKKE TV, MEN PAD PÅ UTSIDEN AV GLASSET ←». **Stream delay changed from "45 sek" to "trolig 20 sek–1 min (vi tipper)".** Froland: rain on Wednesday evening, none on the stream. Haaland/Brauta lead [61.43659, 10.1854], about 190 moh. Wind layer: 23.09 17:49 (open-meteo). |
| 12:11 | mk_bevis b370c19 | [PRIMARY re-read]/[MODEL] | Evidence pack, see §2.R. It includes the full wording of three boards, a sun-onset measurement (direct sun on crowns top right from 07:47, possibly earlier; ground from 08:00), and the plane elevation table. "Tvetydighet": the 21:29:38 pointing may refer to a shooting star. |
| 12:19 | mk_bevis 547239f | [MODEL] | Forest tests K0–K4: **A1 Birkebeinerveien passes 0 of 25 positions; view p90/p99 tree height is 2.3 / 9.1 m**. A2 Gålaveien C07 passes 4 of 25. |
| 12:31 | mk 77fe435 | **[RETRACT]** | The candidate list becomes "historikk, ikke gjeldende rangering". "Regionen må holdes åpen." Temperature is not a hard filter. Candidate 1's road bearing is about 94°, not 130°. Point A1 = 61°26′55,3″N 10°58′39,0″E, which matches the default.no site-finder top within 1 m. |
| 12:43 | 7e3690f | [HINT] | App shop: «T-skjorte i Terje-modell», 1 116 897 coins (screenshot at 12:22). The «God helg og god jakt» board with a fruit basket, and the story music presented as "«Riverbank» av Goldenrod". The interpretation said: "«Riverbank» betyr elvebredd … kassen kan stå nær en" (near a riverbank). |
| 12:47 | mk 25c3768 | [MODEL] | "Det eksakte A1-punktet har svak skogstøtte … 61.4487, 10.9775 … ingen av 25 prøveposisjoner [består] alle skogkravene". |
| 13:01 | 2f86bbf | **[RETRACT]** | "The Terje T-shirt is not new." It was folded into the terje hint and the news item dropped. The app text reads: «Denne ble svært populær under forrige Hordejakt, og vi ble utsolgt på under et døgn. Det går rykter om at de som kjøpte denne sist, økte kredittscoren sin betraktelig. Tilfeldig? Neppe.» |
| 13:03 | mk_bevis 57cd0b2 | [MODEL] | Sun limit independent of which surface is lit; tilt table for the 21:29 gesture. |
| 13:09 | mk_bevis 4baabc5 | [MODEL] | Morning-sun limit at the v6 camera positions (A1: 5.8–54.0 m needed, A2: mostly 0 m). |
| 13:43 | mk d1fbac0 | **[RETRACT]**/[HINT relayed] | "En arm nesten loddrett i bildet er ikke en måling av flyets høydevinkel. Claude har trukket tilbake den slutningen". Weather exclusions of the west and south withdrawn as hard limits. Olive-oil item per praktiskinfo.no screenshots: **grevling**, «Olivenoljestativ», 100 000 points, shipping text **«Nesten Helt Hjem»**; the earlier "bever" (beaver) corrected. New untested lead: "olivenolje → olivin", giving Åheim/Almklovdalen. |
| **14:12** | **e431102** | **[RETRACT/REMOVAL]** | **"Remove everything about Birkebeinervegen."** See §2.H. No reason given. |
| 14:29 | 996369d | [HINT?] | Horde AI reply to «Grevling»: «1 Hordeminus = 3,4 grevlinger». Screenshot recovered, see §2.N. |
| 14:56 | 337ddc2 | **[RETRACT]** | The grevling reply was removed: "it was not repeatable in a new chat". |
| 14:56–14:59 | dd51345, 67c7124 | [RETRACT] | "Stop calling it a known song." The music label comes from Horde's Facebook story. |
| 15:19 | 0cc7e96 | [PRIMARY] | «INGEN FERIST SOM JEG MERKA» (no cattle grid that I noticed). |
| 15:20 | 4dd298c | [INTERP] | "Nesten hjemme" tip: Anja is from Brumunddal [60.88362, 10.94489]. The source of the phrase is the shipping text «Nesten Helt Hjem» noted in the mk repo. |
| 15:44–15:47 | e4bd434, bb53374 | [INTERP] | Moose-hunting fields on state land (Statskog; 192 fields) are marked unlikely, because moose hunting is with rifles. Small-game and bird hunting are not excluded. The moose hunt started on 25.09. |
| 16:05–16:06 | c02748f, 889d715 | [COMMUNITY-OBS] | Hagina, about 510 moh between Hamar, Lillehammer and Sjusjøen: «Her er bjørketrærne oransje, ikke gule som på streamen», «de er mye tynnere i bladverket her oppe enn på stream». The model factor for Ringsaker became 0.6. |
| 16:20–17:03 (event) | — | [PRIMARY via default.no cut] | Balloon video `default.no/cuts/202609251620_202609251703.mp4`: balloon letters; **a HORDE arrow sign to the right of the box, pointing left**; the sun straight into the camera at about 16:45–16:50. |
| 17:22 (stream) | — | [PRIMARY] | Anja pointed up at the sky. |
| 17:49 | 1dfb536, f965b2f | [COMMUNITY]/[HINT] | Chat reports 11 moose collisions in an hour near Elverum. **The stream froze**; Horde said it was technical problems. |
| 17:51 | ed45704 | [PRIMARY] | Whiteboard «THILPRTE OESHF». Read as THE SHOPLIFTER (status Løst), a nod to BobTheShoplifter of default.no. |
| 17:54 | 37bd161 | [PRIMARY]/[INTERP] | Balloon colours: green E, P, T; purple E; blue F; yellow H, H, I, R, S, T; pink L, O. Also **one open hand standing in the heather in front of the box** (night camera). Tip: "Bob" means the bobsleigh track at Hunderfossen [61.2185, 10.4525]. |
| 17:55 | ac06655 | [PRIMARY via default.no] | "The Horde sign appears to be back in the 25.09 16:20 balloon video." Status Usikker. |
| 17:56 | e0365b0 | [INTERP] | Horde post «Ikke stå i det alene» uses «Cherry Blossom · Ella Joy Meir». Facebook's label format is "sang · artist", so the story music is the song «Goldenrod» by the artist «Riverbank». |
| 17:58 | 9db1159 | [PRIMARY] | «NOEN SOM VET FASITEN» on the same board. |
| 18:02 | 9a7359b | [COMMUNITY-OBS] | The 17:22 pointing matched to **SAS50J** (A320neo, Oslo northbound) over eastern Stange towards Romedal/Løten at 21 000–23 000 ft, real time about 17:21–17:22. The ADS-B track is at `innhold.ts:1638-1642`. Flightradar24 also showed SAS364 over Rena. |
| 18:40 | 29a1073 | [INTERP] | Lillehammer: the squirrel «Lille» is the official mascot for the 2026 200th anniversary. |
| 18:44 | 72f623a | [RETRACT] | THE SHOPLIFTER downgraded from Løst to Tolkning. FILTER THE SHOP added as "equally valid". |
| 18:46 | 971c9d6 | [RETRACT] | "FILTER THE SHOP is weaker: the shop in the Horde app has no filter." |
| 19:12 | 4d44d6a | [PRIMARY] | 18:13: «KANSKJE 35% BJØRK · 25% GRAN · 40% FURU · AKKURAT RUNDT MEG». Theory: Jomfrua, Tjuven and Danseren [61.2279, 10.90754], tops at 1010–1026 moh. |
| 19:19 | ae6dc67 | [MODEL] | Forest-mix similarity layer from NIBIO SR16, cells about 2 × 2 km. |
| 19:41 | a5526bb | [INTERP] | HELHET FOR TIPS added as a Norwegian reading of THILPRTE OESHF. |
| **20:53** | **6c421a9** | **[PRIMARY] + [RETRACT]** | New board **22.09 19:19:32**: «IKKE MØRKT ENDA · INGEN VANN ELLER VANNLYDER, FØLER IKKE DET ER VANN I NOE NÆRHET». The frame has an overlay timestamp and a "TavlAI" watermark. The riverbank idea was dropped: "Kassen står neppe ved en elv". |
| 21:04 | 68faa86 | — | Height lookup on map tap added (Kartverket DTM 1 m). |

---

## 2. Reversal threads in detail

### 2.A The sign bearing and the approach direction (118° / 120° / 130° / 298° / 300°)

| Stage | Time (CEST) | SHA | Text (verbatim) | Walk from the car |
|---|---|---|---|---|
| 0 | 23.09 14:30 | c0c849b | "Anja skrev «ØST CA 118» og tegnet et kompass på tavla. Fellesskapet tolker det som retningen fra kassen til parkeringen (øst-sørøst). Kameraet står ca. 73°." / "Står du på parkeringen, ligger kassen mot ca. 298° (vest-nordvest)" | 298° |
| 1 | 23.09 14:59 | 58e737c | "Kameraet står nordøst for kassen og ser mot sørvest (ca. 220° ifølge solbanen)." / "Horde-skiltet peker mot venstre i bildet (sørøst), og «mer åpen skog til høyre for meg» er også sørøst." (If Anja faces the camera, which looks SW, her right is SE, so this is consistent.) | 298° |
| 2 | 23.09 15:15 | bdffb03 | «ØST CA 118 · RETNING SKILT» confirmed. "Mest trolig: veien inn fra parkeringen. Da ligger kassen mot ca. 298°" | 298° |
| 3 | 23.09 15:17 | 2eb6f94 | «118–120 GR ØST» | 298–300° |
| **4 (flip)** | **23.09 15:22** | **86d52b8** | "Skissen fra fellesskapet: skiltet står vest-nordvest for kassen og peker mot den, og kameraet står nord-nordøst og filmer mot ca. 208°." / "Skiltet viser veien inn til kassen. Folk kommer altså fra vest-nordvest: fra bilen går du ca. 120° (øst-sørøst)". Code: `sektor(pos, 298, 20…)` became `sektor(pos, 120, 20…)`. | **120°** |
| 5 | 23.09 15:45 | 7983773 | «KAMERA 41 ØST»: the camera is at 41° and films about 221°. | 120° |
| 6 | 23.09 19:12 (stream) | 405c497 | «SKILTET ER BORTE · VET IKKE HVOR» | — |
| **7 (flip back)** | **24.09 18:35** | **4e65b1c** | «KOM FRA DEN VEIEN ←»: "venstre i bildet er ca. 130° (sørøst) … man går mot nordvest (ca. 300°) … Merk at dette snur den gamle tolkningen". Code: `sektor(pos, 300, 25…)`. | **300° ±25°** |
| 8 | 24.09 18:43 | a269415 | «GIKK DEN VEIEN →» read as about 310°, "the same walk". | 300° |
| 9 | 24.09 19:55 | 893318a | The title changed from «…peker 118–120° mot kassen» to «Horde-skiltet pekte 118–120°». "«mot kassen» was an interpretation and is removed". | 300° |
| 10 | 25.09 17:55 | ac06655 | A 16:20 clip shows a HORDE arrow sign "til høyre for kassen, formet som en pil som peker mot venstre, altså mot kassen". Status Usikker. | — |

**Assessment.**
- The final reading (car to the SE, box about 300° from the car) is the same as stage 0.
- The 15:22 flip was based on a community sketch of where the sign stood. That sketch was withdrawn as interpretation at 19:55 on 24.09.
- The 25.09 frame I viewed (`public/img/stream-2509-skilt-tilbake.jpg`) shows the sign at the far right, pointing left.
  - With the camera at about 221°, image-left is roughly SE.
  - So the sign points roughly SE, which agrees with «KOM FRA DEN VEIEN ←». It is not pointing at a car to the WNW.
  - Its position right of the box is consistent with "sign NW of the box, pointing back towards the road".
  - The two readings of 23.09 differ only in whether the sign points *towards* the box or *from the box towards the road*.
  - This is interpretation. Whether the sign in the 25.09 clip is the same sign in the same place is not verified.
- **Stale text in the current file:**
  - `retning118` (`innhold.ts:138-139`) still says «Skissen fra fellesskapet: skiltet står vest-nordvest for kassen og peker mot den … fra bilen går du ca. 120° (øst-sørøst)…».
  - `skilt` (`innhold.ts:630`) still says «Skiltet står vest-nordvest for kassen og peker mot den, så det viser veien inn».
  - These contradict `komfra` (`innhold.ts:183-192`) and the `felt` layer (`lag.ts:855-859`, 300° ±25°).
- mkekeoooo note (77fe435): "Kandidat 1s veipeiling er omtrent 94°. Et ubetinget samsvarsmerke mot et tolket 130°-hint er ikke begrunnet."

### 2.B Camera heading

| Time | Reading |
|---|---|
| 23.09 14:30 | "Kameraet står ca. 73°" |
| 14:59 | Camera NE of the box looking SW (about 220°, from the sun's path) |
| 15:22 | NNE of the box, filming about 208° |
| 15:45 | «KAMERA 41 ØST»: stands at about 41°, films about 221° |

- default.no's sun fit (`defaultno_mer.json`, "solbane"): heading 219.4–219.7°, f = 1068 px, window 21.09 16:20–17:40.
- mk_bevis: heading 219.4°, f = 1602 px at 1920 wide.

### 2.C Stream delay

| Time | Value |
|---|---|
| 23.09 14:30 | «45 sek» (facts box); "Streamen er 45 sek forsinket (bekreftet)" (fly hint) |
| 25.09 11:29 (`01ab80d`) | «trolig 20 sek–1 min (vi tipper)» in all texts and in FAKTA (`innhold.ts:1197`) |

- `STREAM.forsinkelseSek: 45` remains in code (`innhold.ts:10`).
- default.no measured about 22 s (mk_bevis README: "default.no målte ca. 22 s").
- The Digeråsen text (`innhold.ts:1086`) still uses 21:28:53 real time for the pointing, which implies the 45 s delay.

### 2.D Locks and codes

| Time | Lock count |
|---|---|
| 23.09 14:30 | "3 låser: 2 på kassen, 1 på døra" |
| 14:59 | "2 hengelåser og døra 1, alle med 4 siffer" |
| 15:07 | "2 kodelåser med 4 siffer" |
| 18:02 | Door lock: electronic, 5 digits |
| 19:10 | 3 locks |
| 24.09 19:55 | Door has 5 or 6 digits («TROR 5», «GANSKE SIKKER») |

Code candidates, added and adjusted:
- 5008 (high)
- Kodejakten (high; server not live on 23.09)
- 0891 and 0810 (middels)
- 5528 (middels)
- 2188 (middels, unknown source)
- 6788 (middels, then lav on 24.09 19:55)
- 5013, 0553, 8915, 0896, 8105, 5271 and 27000 (all lav)
- 072 and 500 (3 digits)
- 5-digit guesses: 00891, 00810, 27000, 50085, 55285, 07250

Also recorded:
- Board «KAN IKKE TESTE KODER» (25.09).
- Alf (relayed): «Kan være at noen av kodene allerede har kommet».
- The Kodejakten lock animation angles (5°, −41°, −30°, −34°) are "bare animasjonen av bøylen" (`SpillPanel.tsx`).

### 2.E Letters → HORDE MINUS → height

| Time | Reading |
|---|---|
| 23.09 14:30 | «I S N D O R U E M H»; "MINUS HORDE" suggested |
| 14:43 | NORHEIMSUND, one N short; 6.5 h from Oslo; model factor 4 |
| 14:59 | HORDE MINUS is an exact anagram; NORHEIMSUND factor lowered to 2 |
| 24.09 18:30 | Horde AI reply: «2,7 eiffeltårn stablet oppå hverandre»; read as 891 m |
| 24.09 18:31 | Read as 810 or 891 m |
| 24.09 18:38 | 875 m is the chatbot's own reasoning |
| 24.09 18:46 | Status Løst |

Conflicts:
- Hagina's field observation (25.09 16:05) argues against 810–891 moh around Sjusjøen and Ringsakfjellet.
- None of the mk top candidates except Messelt (876–898 moh) are at that height. Myklebysæterveien is 593.8 moh, Madsskardveien 597.6, Jernvinneveien 528–556 (mk_bevis `horisont_api_resultat.txt`).
- mk's report treats «Høydehintet er høyde over havet» as a premise and adds «Er det en låskode, faller Messelts særstilling».

### 2.F Froland

| Time | Status |
|---|---|
| 23.09 14:30 | Theory (squirrel in the coat of arms) |
| 14:59 | "sølvfarget ekorn på grønn bunn (bekreftet)", about 3.5 h drive |
| 15:46 | Excluded on weather |
| 24.09 18:26 | "lite sannsynlig" after the FROLAND app reply |
| 24.09 19:55 | Back to excluded; the screenshot is unverified |
| 25.09 11:29 | Reason added: "Det regnet i Froland onsdag kveld 23.09, men det var ikke regn på streamen" |

default.no's rejected list gives a different reason: «Ingen av de tre flyene hun så var over 10° over horisonten. Feil landsdel for innflygingen til OSL.»

### 2.G Stream audio

| Time | Reading |
|---|---|
| 23.09 15:55 | "Trolig støy" (probably noise) |
| 16:01 | "falsk og går i loop" |
| 25.09 10:59 | "Usikkert" after Alf said «Det er ekte lyd på streamen» |

default.no's data (`analyse.json`, updated 2026-09-23 12:27): 52.86 h of audio, 2 873 files, 604 checked. Lags found: 23.9 h ×290, 47.9 h ×48, 24.9 h ×25, 22.0 h ×20, 27.3 h ×20. Example matches: 2026-09-23 11:40:40 matches 2026-09-21 11:47:10 with correlation 0.999.

### 2.H The Birkebeinervegen removal (`e431102`, 25.09 14:12:35)

The commit message is: "Remove everything about Birkebeinervegen — Our tip, news item and theory evidence, the terrain pin and the fjellmark mention — Birkebeinerveien search stops, places and field notes from our copy of default.no data." **No reason is given.** The full list of removed items is in `git_history_raw/removed_birkebeiner_items_e431102.json`.

Two different places called "Birkebeinervegen" were removed.

**1. The default.no "Birkebeinerveien" near 61.45 N, 10.97 E**, west of Glomma, Stor-Elvdal/Åmot, about 575–606 moh.
- **Terrain pin** in `DEFAULTNO_TERRENG`, added 23.09 15:55: `Birkebeinerveien [61.4495, 10.9752]`, area "Rena/Åmot".
- **The fjellmark text** (23.09 19:01): "Birkebeinerveien ca. 590 moh".
- **Removed from `pins.json`:**
  - `61.4452, 10.9756`: «BOM / privat vei (23.09 ca 00:30) - Birkebeinerveien-avkjoring mot 61.4495,10.9752. Ga forbi bommen til fots, 500 m»
  - `61.4495, 10.9752`: «privat vei - pin Birkebeinerveien-ryggen, ikke sjekket til fots»
  - `61.4495, 10.9763`: «PLAN 7 Birkebeinerveien pin: bom 61.4452,10.9756, ga 500 m NNO forbi bommen (sjekket bare fra veien)»
- **Removed from `plan.json`**, generated 2026-09-24 17:04; stops went from 40 to 36. All four are named "Birkebeinerveien vest/nord":

| Rank | Point | site_score | fusion | Walk | Canopy median | Other |
|---|---|---|---|---|---|---|
| 10 | 61.447, 10.965 | 0.77 | 1.15 | 82 m towards 45°, +28.7 m | 12.1 m | building 290 m away |
| 18 | 61.453, 10.952 | 0.72 | 1.15 | 636 m towards 87° | 9.5 m | from Eldådalsveien |
| 20 | 61.429, 10.95 | 0.65 | 1.79 | 537 m towards 99°, +74.1 m | 12.2 m | 17 dayplanes; parking on Birkebeinerveien 61.42973, 10.94 |
| 38 | 61.44, 10.951 | 0.66 | 1.15 | 327 m towards 140° | 1.0 m | open 0.62 |

- **Removed from `steder.json`** (site finder, 2026-09-24T18:06:17, heading 219.0; sites went from 126 to 117). Nine points, all on "Birkebeinerveien":

| Point | score | abs | moh | Distance to road | opp | hogst_m | omr |
|---|---|---|---|---|---|---|---|
| 61.44874, 10.97747 | 0.995 | **0.12638** | 605 | 556 m | 75.3 | 215 | 1 |
| 61.45306, 10.97747 | 0.786 | 0.0998 | 574 | | | | |
| 61.4473, 10.96541 | 0.748 | 0.09501 | 579 | | | | |
| 61.44874, 10.97776 | 0.981 | | | | | | |
| 61.45162, 10.97926 | 0.887 | | | | | | |
| 61.45018, 10.977 | 0.978 | | | | | | |
| 61.44955, 10.97616 | 0.844 | | | | | | |
| 61.44865, 10.97736 | 0.995 | | | | | | |
| 61.44892, 10.977 | 0.976 | | | | | | |

- **Still present** in `rejected.json`: «61.4495, 10.9763 (bom) — Bom på veien 23.09, bare sett fra veien. Ikke ferdig sjekket.»

This default.no top point is candidate **A1** in the mkekeoooo work:
- mk full report: «Stedsfinneren deres … Den ga Birkebeinerveien (61.4487, 10.9775) øverst.»
- mk README (77fe435): the point 61°26′55,3″N 10°58′39,0″E matches it within 1 m.
- The report "utelukket eller svekket" it: «Terrenget der ville skygget for morgensola kl. 07.51». It also says «Hvis 07.51-målingen er feil, kommer Birkebeinerveien (61.449, 10.977) tilbake som et godt alternativ; der passer temperaturen best av de gamle kandidatene.»
- In the report's §18 the second analyst «anbefalte å sjekke dette området først» and «godtar ikke en endelig utelukkelse av Birkebeinerveien og Gålaveien før den belyste flaten er identifisert».

mk_bevis model results for A1:
- Forest tests K0–K4: 0 of 25 pass (K2 5.6 ✗, K3 2.8 ✗, K4 1.8 ✗); view p90/p99 tree height 2.3 / 9.1 m.
- Opening: view SW 188–250° is 98 % open at 10–50 m.
- Terrain horizon towards the morning sun: 11.0–11.1° at the ground, 6.7–7.2° at 20 m, from a ridge 269 m away at 659 moh (site at 605 moh).
- Sun limit at 07:50: needs 32.3 m above the ground (`grense_2`); the v6 positions need 5.8–54.0 m.
- Plane elevation for NOZ9EG at 22 s delay: 26°.
- **In short:** the model says the exact point is open or clear-cut and shaded from the morning sun. That argues against it, but it is not a field search.

**2. The Discord tip "Birkebeinervegen over Ringsakfjellet (Ringsaker–Rena)"** `[61.36168, 10.84625]`, added 25.09 11:02:
- «går over fjellet mellom Ringsaker, Stor-Elvdal og Øyer, ca. 720–1040 moh. Det er 341 steder på 810–891 moh nær vei her, 233 av dem med vei mot sørøst. Passer godt med 2,7 eiffeltårn, og området er ikke utelukket.»
- The news item and the theory evidence `discord2509` (factors ringsaker 1.3, rena 1.15, solor 1.1) were rewritten without it.

**Status:** removed from magnus without a reason. It is **not** documented as searched-empty. The only field record says the gate stopped a full check. Possible reasons, none of them evidenced: privacy or private-road concerns, a request from default.no or the landowner, or an unlogged field search. Treat it as an open question.

### 2.I Riverbank / Goldenrod

| Time | SHA | Reading |
|---|---|---|
| 25.09 12:43 | 7e3690f | «Storyen hadde musikken «Riverbank» av Goldenrod.» / ««Riverbank» betyr elvebredd. Alf har sagt at man aldri må krysse en elv, men kassen kan stå nær en.» |
| 14:56 | dd51345 | «Det er uklart hva som er artist og hva som er sangtittel … trolig et spor fra Facebook sitt eget musikkbibliotek.» "Goldenrod" noted as the plant gullris. |
| 14:59 | 67c7124 | The music is on Horde's Facebook story. «Den var ikke på streamen, og Anja hører den ikke i boksen.» |
| 17:56 | e0365b0 | Label format "sang · artist" (from «Cherry Blossom · Ella Joy Meir»), so the song is «Goldenrod» and the artist «Riverbank». «Riverbank … er bare artistnavnet, så det teller mindre.» |
| **20:53** | **6c421a9** | «Kassen står neppe ved en elv: Anja skrev 22.09 «ingen vann eller vannlyder, føler ikke det er vann i noe nærhet».» |

Other primary no-water evidence:
- 23.09 evening: «IKKE VANN · STEIN + SOPP · MOSE PÅ STEINER».
- The organiser (Alf, relayed): «aldri noe farlig, som å krysse en elv».

### 2.J THILPRTE OESHF

| Time | Reading |
|---|---|
| 25.09 17:51 | THE SHOPLIFTER (Løst) |
| 17:54 | The letters come from balloons in a Horde video recorded by default.no, with the colours listed |
| 17:58 | «NOEN SOM VET FASITEN» on the same board |
| 18:44 | FILTER THE SHOP; status changed from Løst to Tolkning |
| 18:46 | "the shop in the Horde app has no filter" |
| 19:41 | HELHET FOR TIPS |

- Offshoots: Bob → the bobsleigh track at Hunderfossen [61.2185, 10.4525]. "Tjuven" (the thief), as part of the Jomfrua/Tjuven/Danseren theory.
- I viewed the photo `public/img/tavle-2509-shoplifter.jpg`: the board reads «THILPRTE / OESHF».

### 2.K App replies known only from screenshots

FROLAND → «Ekornet kan klatre» (23.09 22:27) and LD6788 → «ENKODE» (24.09 00:01):
- First logged as Bekreftet with source "Horde-appen" (addc834, 24.09 18:26).
- Downgraded to Usikker, "Skjermbilde delt i chatten (ikke sjekket selv) … skjermbildet kan være redigert" (893318a, 19:55).

### 2.L The animals and the olive-oil stand

- The magnus list: squirrel (the "Hint-hint" app screen), mallard (promo video), fox (plush), black grouse (shake the app), and the stuffed animal in Horde Rewards. The last was read as a badger (11:00), then possibly Haaland's raccoon from Texas (11:01).
- mk (d1fbac0, 13:43): third-party screenshots on praktiskinfo.no show a **grevling** (badger). The item is called «Olivenoljestativ», costs 100 000 points, and has the shipping text «Nesten Helt Hjem». The mk repo corrects its earlier "bever".
- magnus's "nesten hjemme / Brumunddal" tip (15:20) does not cite this shipping text. It is probably the origin.

### 2.M The Terje T-shirt

- 12:43: presented as new, with the news time "25.09 kl. 12:22" (the phone clock in the screenshot).
- 13:01: "not new".
- The app text says it was sold out «under forrige Hordejakt». This organiser app text links «Terje» to the credit score.

### 2.N The Horde AI «grevling» reply (recovered from `996369d`)

Screenshot text, verbatim:
> «Grevling er faktisk et ganske sterkt forslag. Hvis du vil, kan vi bruke det på tre måter: som kodenavn · som et internt mål på noe litt absurd · som en helt useriøs måleenhet. For eksempel: 1 Hordeminus = 3,4 grevlinger · «Dette prosjektet er to grevlinger unna å være ferdig». Kort sagt: Det gir ikke mer mening, men kanskje litt bedre stemning.»

The magnus interpretation at 14:29 took it at its word: 1 grevling ≈ 238 or 262 m. It was removed at 14:56 because it was "not repeatable in a new chat". Status: retracted, probably chatbot improvisation within the context of that chat.

### 2.O The «I GÅR» ambiguity in the logging board

- The board: «DET HAR VÆRT HOGD TIDLIGERE DER JEG GIKK I GÅR · GIKK DEN VEIEN →». I viewed `public/img/tavle-hogd.jpg`; the arrow points right.
- The repo's interpretation: this is the same walk as «KOM FRA DEN VEIEN ←», i.e. arriving from the car in the SE through an old clear-cut, going NW to the box. The hint itself admits: «Det er uklart hva «i går» viser til.» (`innhold.ts:219`).
- The arrival happened on 20–21.09, not "yesterday" relative to 24.09.
- An alternative consistent with the text: the → arrow is the direction of the walk on 23.09 to the break place («GIKK 2 MIN INN I SKOGEN», 23.09 evening). That would be a different walk from the arrival.
- The companion board «SÅ INGENTING SOM IKKE HØRER TIL I EN SKOG I GÅR» points the same way. If the blindfold claim is true, how she saw anything on that walk is itself unclear (the blindfold claim is Usikker).

### 2.P Transport and the last leg: carried or walked; Sunday or Monday; drive length

- Whiteboard 21.09 18:31: «OSLO, SØN KL 04.00 · CA 5–10 MIN Å GÅ FRA BIL». 18:38: «TROR DET VAR OPPOVER · SISTE 5–10 MIN».
- Børsen (added 23.09 14:49): covered windows; «aner ikke hvor lenge de kjørte»; «sovemaske og headset og ble båret inn i skogen»; in the cage «siden mandag morgen».
- hordejakten.vercel.app: «Hun reiste i minst 7 timer etter at hun ble hentet i Oslo.»
- Stream start: first recorded as "ca. 07:00", then 06:50. The vercel site says «Livestreamen starter 06:40»; the board says «LIVE 07:00»; mk_bevis reads «STARTET 07 00».
- **Reversal:** SIKRE_FAKTA changed from "båret oppover" to "å gå fra bilen" (24.09 19:55). The `terreng` hint (`innhold.ts:759`) still says «ble båret inn i skogen».

### 2.Q The default.no candidate list as mirrored in magnus (model outputs)

| Snapshot | Rank 1 | Rank 2 | Rank 3 | Rank 4 | Rank 5 |
|---|---|---|---|---|---|
| 22.09 12:41 | Østerdalen (Elverum) [61.45, 11.0], 4.7 % | Sør for Løten og Koppang, 3.1 % | Indre Oppland, 2.2 % | Østre Innlandet, 2.5 % | Valdres/Hallingdal, 1.4 % |
| 22.09 16:42 | Rena og Åmot [61.45, 11.1], 4.2 % | Gjerstad/Vegårshei, later "Risør og Gjerstad" [58.75, 9.3], 2.2 % | Indre Oppland, later "Lom og Jotunheimen (i det blå)", 1.4 % | Nes og Eidsvoll, 1.2 % | Løten og Hamar, later "Ringsaker (Brøttum)", 1.1 % |
| 23.09 evening (clear cells) | Løten og Elverum, later "Hamar øst mot Løten" [60.9, 11.2] | Rena og Åsta [61.3, 11.2] | Koppang, 8.2 °C | Finnskogen, 8.5 °C | Trysil, 6.1 °C |

- `steder.json` areas (2026-09-24T18:06): rank 1 at 61.45, 11.1, p = 0.127; rank 2 at 60.7, 11.6, p = 0.056; rank 3 at 60.95, 11.3, p = 0.054; rank 4 at 61.75, 11.1, p = 0.02; rank 5 at 58.55, 6.1, p = 0.044 …
- mk report: the fusion model's best area is Glommadalen between Rena and Evenstad (61.35–61.47 N, 10.97–11.15 E), with 11 % of the probability within 10 km and 29 % within 25 km of the top cell 61.45, 11.10.
- The default.no rejected list (mirrored) includes Lesja/Dovre 61.75/8.40: «Lå som nr. 1 i en utdatert fusjonsvariant (22.09, uten fly).»

### 2.R mkekeoooo: how the recommendation changed and what was retracted

The report's §17, «Hvordan vurderingen endret seg», lists the rounds:

| Round | Best proposal | Why it changed |
|---|---|---|
| 1 | Madsskardveien east side (default.no stop 1, 61.452, 11.146) | First pass through default.no |
| 2 | The ridge south of Myklebysætra (61.310, 10.970) | Eiffel hint read as height, plus the plane analysis ("83 ruter") |
| 3 | Six markers: Gålaveien, Birkebeinerveien, two in Messelt, H2, point 7 | Precise plane analysis split into a north and a south scenario |
| 4 | C07 at Gålaveien and C23 at Messelt | Terrain and forest model with the stump distance |
| 5 | Messelt (S2/S1) | C07 needs a river crossing; morning sun |
| 6 | Myklebysæterveien vest and the east side of Glomma | Stump distance retracted; temperature; new laser data |

**Retractions and corrections** (README 77fe435, 25c3768, d1fbac0; PRESISERINGER):
- «Den gamle avstanden på 17–44 m [B3 stubbeobjekt] er trukket tilbake … alle posisjoner som ble forkastet på grunn av den, er tatt inn igjen».
- «Den historiske kontrollrekkefølgen er ikke en vedtatt, gjeldende rangering».
- «Temperatur skal ikke være et hardt filter».
- «En arm nesten loddrett i bildet er ikke en måling av flyets høydevinkel. Claude har trukket tilbake den slutningen».
- «De tidligere værutelukkelsene av vest og sør var modellbaserte og ikke verifisert mot observasjoner».
- «Tallene i #1 (47° mot Messelts maks på 63°) blandet et øyeblikksbilde og et maksimum, og brukte 45 s … feil sammenligningsgrunnlag» (mk_bevis).
- «Appvaren med bever/olivenolje» was corrected to grevling, «Olivenoljestativ».
- 22.09 plane scenario: «Er det NOZ55J hun så, favoriseres områdene nord (Gålaveien, Birkebeinerveien, Messelt). Er det SAS39A, favoriseres sør (Myklebysætra, H2 og punkt 7).»
- New untested lead: olive oil → olivine, giving Åheim/Almklovdalen.

**mk_bevis plane table** (NOZ9EG elevation at 22 s delay from stream time 21:29:38):
- Candidate 1: 33°. Messelt: 24°. Other candidates: 20–26°. Løten: 7° (NOZ56U 28°).
- «Ingen kandidat har et fly i nærheten av «rett opp» i det øyeblikket hun peker.»
- NOZ9EG position at 22 s: 61.317 N, 10.904 E, 25 920 ft (GNSS). NOZ56U: 60.739 N, 11.222 E, 20 655 ft.

**mk_bevis sun measurements** (default.no minute clips, not the original; crown-to-sky ratio):

| Time | Ratio |
|---|---|
| 07:20 | 0.29 |
| 07:30–07:44 | 0.32–0.33 |
| 07:47 | 0.39 |
| 07:49 | 0.53 |
| 07:50 | 0.66 |
| 07:53 | 0.68 |
| 08:00 | 0.61 |
| 08:30 | 0.29 |

- Direct sun on crowns and trunks at top right (azimuth 238–250°, elevation +8.5° to +18.6°) from 07:47. There are faint warm patches from 07:40–07:44.
- The ground gets direct sun from 08:00.
- Sun at 07:47: azimuth 98.1°, elevation 5.30°; 07:50: 5.65°; 08:00: azimuth 100.9°, elevation 6.80°.

---

## 3. Whiteboard wording that differs between sources, or is missing from magnus

The mk_bevis README (b370c19) gives Claude's reading of three clips, identified by SHA-256. The images themselves were withheld.

| Clip | mk_bevis reading (verbatim) | magnus TAVLE |
|---|---|---|
| b18-44-14 (21.09 18:44) | «STARTET 07 00 / UJEVNT TERRENG, MYE LYNG / HØRER IKKE MYE FRA BOKSEN» | «KUPERT TERRENG · MYE LYNG · HØRER IKKE MYE FRA BOKSEN» (18:44) and «LIVE 07:00» (18:48) |
| b19-38-13 (21.09 19:38) | «4 STORE STEINER TIL VENSTRE, KUN STEIN DER» | «4 STORE STEINER, KUN STEIN DER» (missing «TIL VENSTRE») |
| s22_18-56-41, 18-57-41, 19-05-42 (22.09 18:56–19:05) | «JA, FØLES SOM FJELLUFT» · «GIKK IKKE PÅ STI, MEN KUPERT TERRENG» · «BLANDET SKOG, VELDIG HØYE TRÆR, KUPERT TERRENG, SOM GÅR SLAKT SLIK:» with a drawn gentle hump | **Not in magnus** |
| 22.09 19:19:32 | — | Added only on 25.09 at 20:53: «IKKE MØRKT ENDA · INGEN VANN ELLER VANNLYDER, FØLER IKKE DET ER VANN I NOE NÆRHET» (I viewed the image; it has the overlay timestamp "2026-09-22 19:19:32") |

Plane events from `defaultno_mer.json` (fetched 24.09 18:36) that have no magnus hint card:
- **22.09 20:32:40**: «Første av to fly inn mot Gardermoen ned Østerdalen (SAS39A). Chatten skrev «FLYY». Svakere enn 20:35. 90–96 % skyer, så bare fly under 28 000 fot teller.»
- **22.09 20:34:40**: «Hun peker, setter seg opp og følger flyet sørover (NOZ55J, 21 000 fot). Chatten: «Fly blinker med farger». Overskyet, så ikke en satellitt.»
- 21.09: «Hun peker opp 21:29:38, skriver «FLY» 21:30:12, og lyden er sterkest 21:33:20.»

---

## 4. Contradictions and stale text in the current `innhold.ts` (HEAD `68faa86`)

1. `retning118` (lines 133-142) and `skilt` (lines 623-631) still say the sign stands WNW, points at the box, and the walk from the car is about 120°. This contradicts `komfra` (lines 183-192), the `felt` layer and SIKRE_FAKTA (line 1463).
2. `STREAM.forsinkelseSek: 45` (line 10) contradicts FAKTA «20 s–1 min» (line 1197). Digeråsen still uses 21:28:53 real time (line 1086).
3. `terreng` (line 759) says «ble båret inn i skogen», but SIKRE_FAKTA (line 1459) says «5–10 min å gå fra bilen».
4. `regel-ko` (lines 329-337) is Bekreftet with source "Alf på Hordes TikTok-live 25.09". The same material in `tiktok2509` (lines 338-346) is Usikker, "gjengitt i chatten (ikke sjekket ordrett)". The upgrade was made in `094b3b8` without a documented new source. The queue itself was already in the terms (`regel-konvolutt`, lines 689-695); the 5-hour quarantine was not.
5. `fly` (lines 742-752): «Anja pekte rett opp». The TAVLE entry says «pekte opp, litt mot sørøst» (line 894). mk has retracted the arm-angle inference, and the gesture may refer to a shooting star (mk_bevis).
6. `bindfold` is Usikker (line 434), yet `gikk2min` (line 448) uses it as the leading explanation («Trolig turen til pausestedet»).
7. The `DEFAULTNO` array comment (line 1158) mixes a 22.09 16:42 fusion snapshot and a 23.09 clear-cells list under one header.

---

## 5. Candidate places whose status changed in git history

| Place | Point | Status (by the end of 25.09) | Source |
|---|---|---|---|
| Birkebeinerveien A1 (default.no site-finder top) | 61.44874, 10.97747 | Removed from magnus without a reason. Gate: "ikke ferdig sjekket". The mk model says the forest does not fit and there is terrain shade. | e431102; rejected.json; mk_bevis |
| Birkebeinervegen over Ringsakfjellet | 61.36168, 10.84625 | Removed from magnus without a reason | ddf93d0 → e431102 |
| Private road with a house | 61.4307, 11.0483 | Searched, empty ("bolighus 7 m unna, ikke boksen") | rejected.json |
| Tretopphyttene | 60.9748, 10.9167 | Searched, empty (a chatter checked all cabins) | ce85e10 |
| Prøysenstua | 60.912, 10.8076 | The house was checked; the forest around the star was not | ce85e10, aa81ebf |
| Kroktjennet top, about 891 moh | 61.2405, 11.01 | Weakened: nature reserve, open ground, no road within 900 m | 679260b, 4654dfd |
| Froland | 58.53, 8.63 | Rejected (weather, planes) | 6cddb71, 893318a |
| Norheimsund | 60.3707, 6.1453 | Rejected (the anagram is short one N; Windy blue) | b671b5b |
| Nøtterøy | 59.21, 10.42 | Rejected («Ikke en øy») | c0c849b |
| Bennyøy | 59.2666, 9.1327 | Weak; it is an island | 6d6d45c |
| Texas / Kompassen (Våler) | 60.87812, 12.21229 / 60.87639, 12.31426 | Weak; height does not fit; excluded area | 197e40e |
| Brauta (Ringebu) | 61.43659, 10.1854 | Interpretation; about 190 moh; about 4 m/s of wind at 17:49 on 23.09 | 01ab80d |
| Jomfrua / Tjuven / Danseren | 61.2279, 10.90754 | Theory; the tops are above the tree line | 4d44d6a |
| Digeråsen | 61.1788, 11.2639 | Tip | 58e737c |
| Brumunddal ("nesten hjemme") | 60.88362, 10.94489 | Theory, weak | 4dd298c |
| Bobsleigh track, Hunderfossen | 61.2185, 10.4525 | Tip, weak | 37bd161 |
| Tommsen A (Tingstadbrua) | 61.1139, 11.0011 | Tip; about 623 moh | 094b3b8 |
| Tommsen B (Stor-Elvdal) | 61.4732, 10.9687 | Tip; about 411 moh | 094b3b8 |
| Tommsen C (Gruvelia) | 60.18519, 10.89289 | Tip; the point is in a river | 094b3b8 |
| mk 1: Myklebysæterveien vest | 61.3995, 11.0316 | Historic list, under revision | mk README |
| mk 2: Madsskardveien traktorvei | 61.4443, 11.1234 | Historic list | mk README |
| mk 3: Sørlige Messelt | 61.4571, 10.8362 / 61.4545, 10.8406 | Historic list | mk README |
| mk 4: Madsskardveien øst | 61.4518, 11.1428 | Historic list | mk README |
| mk 5: Jernvinneveien | 61.4351, 11.1435 | Historic list | mk README |
| A2 Gålaveien C07 | 61.46254, 10.97512 | Conditional; "C07 krever elvekryssing" | mk_bevis punkter_v6, report |
| default.no plan stop 1: Madsskardveien øst for Glomma | 61.452, 11.146 | Model output | plan.json |
| Åheim / Almklovdalen (olivine lead) | about 62.05, 5.55 (my approximation; the source gives no coordinates) | New and untested | mk d1fbac0 |

---

## 6. Open questions raised by the history

1. Why was Birkebeinervegen removed (14:12 on 25.09)? Was A1 ever searched past the gate?
2. Does the gesture at 21:29:38 on 21.09 refer to a plane or to the shooting star signalled at 21:27:42?
3. What is the true stream delay for each event (default.no about 22 s; magnus "20 s–1 min")?
4. Does «I GÅR» on the logging board mean the arrival walk or the walk on 23.09 to the break place?
5. Is the sign in the 25.09 16:20 clip the original, in the same place? Is its bearing still 118–120°?
6. What does the single open hand in the heather (25.09 night) mean?
7. Does the door lock have 5 or 6 digits? Is the Kodejakten server live yet (it returned 503 on 23.09)?
8. Is «2,7 eiffeltårn» a height above sea level, a distance or a code? The mk candidates at about 530–650 moh do not fit a height reading. Messelt (876–898 moh) does, but conflicts on temperature.
9. Can the FROLAND and ENKODE screenshots and the «Olivenoljestativ / Nesten Helt Hjem» product text be verified directly in the app?
10. Was the 5-hour quarantine really said on TikTok? The regel-ko upgrade has no documented source.
11. Which of the 22.09 planes did she follow: NOZ55J (north scenario) or SAS39A (south scenario)?
12. Should the missing 22.09 18:56–19:05 boards («FØLES SOM FJELLUFT», «VELDIG HØYE TRÆR», «GÅR SLAKT») and «4 STORE STEINER TIL VENSTRE» be added to the whiteboard record? They are consistent with, but more specific than, «TYPISK FJELLMARK».

---

## Appendix A: all 150 magnus commits (CEST, oldest first)

| SHA | Time | Subject |
|---|---|---|
| e1b59cf | 23.09 14:15 | Initial commit |
| c0c849b | 23.09 14:30 | Scaffold Hordejakten map app with drive-time data |
| ecf0260 | 23.09 14:42 | Build map UI with panels, model controls and flight tracks |
| f99df64 | 23.09 14:43 | Add Norheimsund letters theory and README |
| 520fd05 | 23.09 14:49 | Add theory ranking with percentages, Innlandet and Windy exclusions |
| 4db364e | 23.09 14:50 | Keep excluded cells out of the probability classes |
| 58e737c | 23.09 14:59 | Fix review findings in map, model and theory estimates |
| b671b5b | 23.09 14:59 | Note HORDE MINUS as exact anagram of the referral letters |
| 4e26d93 | 23.09 14:59 | Add Roman numeral and binary theories for the sign hands |
| 5b2a319 | 23.09 15:00 | Add note that people are reportedly at the box |
| 52c0b78 | 23.09 15:02 | Add sunny-today areas, Solør theory and fake-light doubt |
| cf75140 | 23.09 15:05 | Add codes and beliefs summary with links, and Bergen 118° line |
| 3885ab8 | 23.09 15:07 | Add most likely codes, Tretopphyttene tip and Østfold note |
| e1ca795 | 23.09 15:08 | Filter hints by confirmed and not confirmed |
| f3eb2bb | 23.09 15:13 | Make the panels easier to understand |
| bdffb03 | 23.09 15:15 | Mark 118° as the sign direction, confirmed by Anja |
| 6d6d45c | 23.09 15:16 | Add "Reven heter Benny" with matching place names |
| 45200c5 | 23.09 15:16 | Add chat quote backing Innlandet |
| 2eb6f94 | 23.09 15:17 | Update sign direction to 118–120° per Anja |
| 85d9ded | 23.09 15:17 | Link the squirrel to hunting in Innlandet |
| e94d4db | 23.09 15:18 | Exclude the Odal–Jessheim morning fog area |
| 86d52b8 | 23.09 15:22 | Add "Alt vi har" mode, sun clues, new sign geometry and cabins |
| 9ea67b3 | 23.09 15:23 | Weaken the squirrel clue |
| 0d70d0c | 23.09 15:31 | Calibrate estimates and apply UX checklist |
| 6a33959 | 23.09 15:32 | Add "+5" on the sweater with code readings |
| 015d617 | 23.09 15:32 | Note that +5 on the sweater numbers gives nothing |
| a49eadd | 23.09 15:34 | Decode more of the trouser letters |
| 66e31ce | 23.09 15:39 | Separate confirmed facts from guesses and fix review findings |
| e72a665 | 23.09 15:41 | Add second plane NOZ9EG and the Ringsaker track |
| eb4093e | 23.09 15:43 | Show the whiteboard sketch with best reading |
| 5d966c0 | 23.09 15:43 | Anchor whiteboard thumbnails to the board |
| 7983773 | 23.09 15:45 | Add "KAMERA 41 ØST" and use it to check the sunlight |
| 5178ea0 | 23.09 15:45 | Note in the solar-noon clue that the sunlight checks out |
| 6cddb71 | 23.09 15:46 | Rule out Froland: the weather does not match |
| 0a6597f | 23.09 15:50 | Sort the whiteboard log newest first, with a toggle |
| ce85e10 | 23.09 15:51 | Mark Tretopphyttene and Prøysenstua as checked |
| fe51e10 | 23.09 15:55 | Add clues from default.no we were missing |
| 90f20c3 | 23.09 15:57 | Show "Siste nytt" prominently at the top |
| 06b82f0 | 23.09 16:01 | List every Norwegian word and place the referral letters can spell |
| aa81ebf | 23.09 17:56 | Add Rudshøgda/Prøysen theory and a letter word generator |
| df596d3 | 23.09 18:01 | Add "LYDTETT · SOL · VINDSTILLE" whiteboard (17:49) |
| 125f83f | 23.09 18:01 | Add Kodejakten findings from the game's source code |
| c4c0aa3 | 23.09 18:02 | Add the 5-digit electronic door lock |
| 35ba6b9 | 23.09 18:16 | Refresh default.no candidates and add flight-route filter hint |
| b7a2c7f | 23.09 18:17 | Note Kodejakten backend is not live yet |
| 4a9f3ee | 23.09 19:01 | Add fjellmark, mushroom and 2-min whiteboards |
| 41304dc | 23.09 19:04 | Show every place-linked hint on the map, and add Kodejakten game hints |
| 6763e06 | 23.09 19:08 | Add community exclusion map (no mushrooms, mountain birch) and powerbank codes |
| 24c4d59 | 23.09 19:10 | Add "Spill" tab with Kodejakten guide and dartboard calculator, and fix lock count |
| 89d7dc0 | 23.09 19:12 | Add "Lite med fly her · sikkert med vilt" whiteboard (19:09) |
| b55eafc | 23.09 19:13 | Remove the pink "no mushrooms" exclusion, which was not correct |
| 405c497 | 23.09 19:15 | Switch pink to red, and add "Skiltet er borte" whiteboard (19:12) |
| 05d8624 | 23.09 19:16 | Make the excluded area read as red rather than pale pink |
| 1971621 | 23.09 19:22 | Add Analyse tab with audio, birds, plane sounds and municipality ratings |
| d9e3376 | 23.09 19:37 | Add linkable sections via URL params and a wide desktop panel |
| 6f8b1b5 | 23.09 19:40 | Lay out the wide panel as newspaper columns, and put the Kodejakten result first |
| fb2ac52 | 23.09 19:45 | Tidy the wide layout, mark the edge of the exclusion map, and stop Analyse hanging |
| bfa356f | 23.09 19:51 | Add practice versions of the four Kodejakten games |
| fc71636 | 23.09 20:03 | Mark everything west of the community exclusion map as excluded |
| 602389f | 23.09 20:09 | Add a live Kodejakten status check and remove the dart calculator |
| 1e342f9 | 23.09 20:22 | Use Horde's real Alf sprites in the practice games and explain Dartskiven better |
| addc834 | 24.09 18:26 | Add app hints ENKODE (LD6788) and «Ekornet kan klatre» (FROLAND) |
| 7ebb743 | 24.09 18:30 | Add HORDEMINUS «2,7 eiffeltårn» hint, 0891 as a code and the Facebook globe frame |
| 2995786 | 24.09 18:31 | Eiffel hint: 300 m without antenna and 330 m with it, so 810 or 891 m; add 0810 |
| b03c6a9 | 24.09 18:32 | Add Horde's «codes are in the app» reply, +5 code variants, the «Ingen pizza enda» whiteboard and the community 800–900 moh map layer |
| 4bd3590 | 24.09 18:33 | Add whiteboard «Hjelper veldig at jeg kan se det dere skriver <3» |
| dcec931 | 24.09 18:33 | Add photo for the «kan se det dere skriver» whiteboard |
| 91c7e7d | 24.09 18:33 | Add whiteboard «Skal klare å holde ut til noen finner meg» |
| c0b1da8 | 24.09 18:34 | Add whiteboard «Hjemmelaget pepperonipizza, dressing fra Coop, knallgodt» |
| 4e65b1c | 24.09 18:35 | Add 5 whiteboards; «kom fra den veien ←» flips the parking search sector to ~300° |
| caf7bcb | 24.09 18:36 | Add whiteboards «Mamma <3» (photo) and «Gråvær hele dagen» |
| 679260b | 24.09 18:38 | Add Kroktjennet/Hemmeldalen 891 moh lead and the SE-road flag in the height layer |
| 9264140 | 24.09 18:38 | Note that the Horde AI summary is the chatbot's own reasoning, with 875 m |
| 39e2789 | 24.09 18:39 | Add the soldiers-and-drone frame from the «Ingen har funnet Anja enda» video |
| 1aab84b | 24.09 18:42 | Add whiteboard «5 siffer, ganske sikker» (08:24) |
| a269415 | 24.09 18:43 | Add whiteboards on the locks and «det har vært hogd der jeg gikk →» |
| 7d0554e | 24.09 18:44 | Add default.no layers: 800–900 moh band, 800–900 m from road, search stops, rejected areas, field notes and Coop shops (with credit) |
| a9eacd9 | 24.09 18:44 | Mark all whiteboards from 24.09 by date only, since their order is unknown |
| 38e9f02 | 24.09 18:46 | Add the confirmed Horde AI «2,7 eiffeltårn» reply to «Dette vet vi sikkert» |
| 94558c2 | 24.09 18:46 | Mark the letters hint as solved: HORDE MINUS |
| 4d069c1 | 24.09 18:49 | Add rain at 11:05 (Anja) matching rain in Rena as a hint and weak evidence for Rena |
| 1125b60 | 24.09 18:52 | Bundle the analysis data into the app so the Analyse tab never has to fetch |
| 2c6783e | 24.09 19:00 | Make the Kart tab easier: ready-made views, search, filters and ⓘ explanations |
| 71778ff | 24.09 19:02 | Add all remaining default.no map layers, loaded only when switched on |
| 1ce4c01 | 24.09 19:04 | Add «Mer fra default.no» to the Analyse tab, and draw search areas as outlines |
| d091bcf | 24.09 19:05 | Add default.no layers to the Kart views and a «Hogst, stier og skytefelt» view |
| 8c4769a | 24.09 19:05 | Shorten the default.no layer texts for the new Kart tab rows |
| 764b796 | 24.09 19:06 | Guard layer zoom against tile layers; add hogst, trails and quiet sky to views |
| e4f04b5 | 24.09 19:07 | Credit default.no everywhere their data is used |
| 89478ba | 24.09 19:08 | Add a remove (×) button per layer in «Hva ser jeg?»: on hover on desktop, always on touch |
| 14d06ce | 24.09 19:34 | Credit Kartverket and OpenStreetMap contributors on the 810–891 moh layer |
| 7679cfe | 24.09 19:41 | Add big credit to the «Hordejakten 2026» Discord and invite people to join |
| e537086 | 24.09 19:49 | Publish the 810–891 moh near-road layer and give the red map distinct colours |
| 4654dfd | 24.09 19:49 | Note that no road lies within 900 m of the Kroktjennet top |
| 197e40e | 24.09 19:51 | Add the «Eiffel Tower in Texas» theory: Texas and Kompassen in Våler (Solør) |
| c5fa5a8 | 24.09 19:53 | Add a drone law and safe-searching warning to the Kart and Stream tabs |
| 893318a | 24.09 19:55 | Stop marking unverified things as confirmed |
| 15cba55 | 24.09 19:56 | Add a bold, easy-to-spot favicon and home-screen icons |
| 42d485d | 24.09 19:59 | Check the drone and search rules against official sources and cite them |
| a141dae | 24.09 19:59 | Correct place names on map markers after checking against Kartverket |
| e96bf5c | 25.09 08:23 | Add a map layer for protected areas where hunting is banned |
| 0e60e4c | 25.09 08:24 | Move the hunting-ban layers to their own group and add a «Der jakt er forbudt» view |
| cfccae5 | 25.09 10:58 | Replace Horde's Alf photo sprites with our own drawn figure |
| 970c493 | 25.09 10:59 | Add Alf's TikTok-live quotes from 25.09 (real sound, animals may be hints, codes may be out, important hints this weekend) and mark the sound analysis as disputed |
| 10c2793 | 25.09 11:00 | Add animal hints: black grouse (shake the app) and badger (Horde Rewards), plus an overview |
| 67eb8d0 | 25.09 11:01 | The Horde Rewards animal may be Haaland's stuffed raccoon from Texas, not a badger |
| ddf93d0 | 25.09 11:02 | Add Discord tips from 25.09: Birkebeinervegen/Ringsaker–Rena (fits 810–891 moh) and Finnskogen (too low, excluded) |
| a1a9e1c | 25.09 11:03 | Add the queue and 5-hour quarantine rule from Alf's TikTok live |
| 63416f0 | 25.09 11:07 | Show only confirmed things on the map by default |
| dc35cc6 | 25.09 11:08 | Add Alf's TikTok note: no dangerous crossings like rivers, and wear visible clothes in hunting season |
| c7ed3f9 | 25.09 11:08 | Add Alf's answer on live vs delayed sound: «det må du prøve å finne ut av» |
| 46b320f | 25.09 11:10 | Add a «TikTok-live i dag» section on the front tab with all of Alf's quotes from 25.09 |
| 094b3b8 | 25.09 11:16 | Update news order and layout, remove a fake item, and add Tommsen's three spots |
| 117ac73 | 25.09 11:18 | Default map: the two planes she saw, and areas ruled out by weather, sun and vegetation |
| 4a22327 | 25.09 11:21 | Rename «Sol i dag» to «Sol 23.09»: the satellite image is from the daytime on 23.09 |
| 3c5c314 | 25.09 11:22 | Fix Discord banner spacing on the Hint tab: move it out of the header block |
| 01ab80d | 25.09 11:29 | Add 25.09 whiteboards, Haaland/Brauta lead, Discord talk, Froland rain, delay change |
| 7b64e2b | 25.09 11:32 | Fix layers that are on at startup never drawing; show wind on the default map |
| dc68a8e | 25.09 11:35 | Show a «Live på TikTok» link while Horde is live on TikTok |
| f38dd45 | 25.09 11:37 | Improve SEO for «Hordejakten», «Horde» and «Hordejakten 2026» |
| 7e3690f | 25.09 12:43 | Add Terje T-shirt hint (1 116 897, points to Kredittskår + «terje») and the «God helg og god jakt» whiteboard with the song «Riverbank» |
| 2f86bbf | 25.09 13:01 | The Terje T-shirt is not new: fold it into the «terje» hint as the clue that unlocks it, and drop the news item |
| e431102 | 25.09 14:12 | Remove everything about Birkebeinervegen |
| 996369d | 25.09 14:29 | Add Horde AI's odd «grevling» reply («1 Hordeminus = 3,4 grevlinger») as unconfirmed |
| dd51345 | 25.09 14:56 | Explain where «Goldenrod · Riverbank» comes from (music label on Horde's story) and stop calling it a known song |
| 337ddc2 | 25.09 14:56 | Remove the Horde AI «grevling» reply: it was not repeatable in a new chat |
| 67c7124 | 25.09 14:59 | Say clearly that «Goldenrod · Riverbank» is the music on Horde's Facebook story |
| 0cc7e96 | 25.09 15:19 | Add whiteboard and hint «Ingen ferist som jeg merka» |
| 4dd298c | 25.09 15:20 | Add the «nesten hjemme» tip: Anja is from Brumunddal, with checks for and against |
| e4bd434 | 25.09 15:44 | Turn on the hunting-ban layer by default and explain that almost all forest has active hunting now |
| bb53374 | 25.09 15:47 | Mark moose-hunting fields as unlikely; small-game and bird hunting are not excluded |
| c02748f | 25.09 16:05 | Add Hagina's field observation: birch is orange and thin at ~510 moh near Sjusjøen, further into autumn than on the stream |
| 889d715 | 25.09 16:06 | Count Hagina's birch observation: pull down high terrain around Ringsakfjellet/Sjusjøen |
| 1dfb536 | 25.09 17:49 | Add warning: 11 moose collisions in the last hour around Elverum |
| f965b2f | 25.09 17:49 | Add news: the stream is frozen due to technical problems, says Horde |
| ed45704 | 25.09 17:51 | Add whiteboard «THILPRTE OESHF» = THE SHOPLIFTER, a nod to BobTheShoplifter (default.no), and credit him |
| 37bd161 | 25.09 17:54 | Add THILPRTE OESHF generator, balloon colours, the returning hand and the bobsleigh-track tip |
| ac06655 | 25.09 17:55 | Add: the Horde sign appears to be back in the 25.09 16:20 balloon video (via default.no) |
| e0365b0 | 25.09 17:56 | Add Horde's «Cherry Blossom» post and use it to read the story music as song «Goldenrod» by «Riverbank» |
| 9db1159 | 25.09 17:58 | Add «Noen som vet fasiten» from the same THE SHOPLIFTER whiteboard |
| 9a7359b | 25.09 18:02 | Add the 17:22 sighting: she pointed up while SAS50J was over east Stange (ADS-B), track on the map |
| 29a1073 | 25.09 18:40 | Lillehammer: the squirrel «Lille» is the official mascot for the town's 200th anniversary (2026) |
| 72f623a | 25.09 18:44 | Add FILTER THE SHOP as an equally valid reading of THILPRTE OESHF (filter the shop in the Horde app) |
| 971c9d6 | 25.09 18:46 | FILTER THE SHOP is weaker: the shop in the Horde app has no filter |
| 4d44d6a | 25.09 19:12 | Add whiteboard «35% bjørk, 25% gran, 40% furu» and the Jomfrua/Tjuven/Danseren theory |
| ae6dc67 | 25.09 19:19 | Add a map layer for forest that matches «35% bjørk, 25% gran, 40% furu» |
| a5526bb | 25.09 19:41 | Add HELHET FOR TIPS as a Norwegian reading of THILPRTE OESHF |
| 91da5a7 | 25.09 19:44 | Fix accordions that cut off content (e.g. the THILPRTE OESHF generator) |
| 6c421a9 | 25.09 20:53 | Add whiteboard 22.09 19:19 «ingen vann eller vannlyder» and drop the riverbank idea |
| 68faa86 | 25.09 21:04 | Show height above sea level when tapping the map and in every point's popup |

## Appendix B: mkekeoooo commits, all branches (converted to CEST)

| SHA | Recorded | CEST | Subject |
|---|---|---|---|
| e960f5f | 25.09 01:40:38 −0700 | 10:40:38 | Legg til norsk forside, kilder og presiseringer |
| b296fa4 | 25.09 10:43:37 +0200 | 10:43:37 | Opprett rapportmappe med leseveiledning |
| deb358a | 25.09 01:45:36 −0700 | 10:45:36 | Publiser fullrapport og kortversjon fra 25. september |
| 5f7eda8 | 25.09 10:46:47 +0200 | 10:46:47 | Opprett figurmappe |
| 30edfa8 | 25.09 01:48:46 −0700 | 10:48:46 | Publiser 15 figurer og norsk figurgalleri |
| 94a45c1 | 25.09 02:02:05 −0700 | 11:02:05 | Ansett Inspektør Pus og innfør katteskikken |
| b370c19 | 25.09 03:11:08 −0700 | 12:11:08 | Bevispakke (skript, data, målinger) fra Claude for #1, #2 og #5 – stillbilder holdt tilbake (branch bevis) |
| 547239f | 25.09 03:19:36 −0700 | 12:19:36 | K0-K4-reproduksjon og åpningstest ved publiserte koordinater (#8) (bevis) |
| 77fe435 | 25.09 03:31:03 −0700 | 12:31:03 | Oppdater forsiden med avklaringer fra revisjonen |
| 25c3768 | 25.09 03:47:27 −0700 | 12:47:27 | Dokumenter A1-kontrollen og lenk til samlet bevispakke |
| 57cd0b2 | 25.09 04:02:55 −0700 | 13:02:55 | Sol-grense uavhengig av belyst flate (#2) og tilt-tabell for 21.29-gesten (#9) (bevis) |
| 4baabc5 | 25.09 04:09:28 −0700 | 13:09:28 | Morgensolgrense på v6-kameraposisjoner (#8) (bevis) |
| d1fbac0 | 25.09 04:43:20 −0700 | 13:43:20 | Oppdater regionale avklaringer og dokumenter nytt olivin-spor (main HEAD) |
