# Places, lock codes and news feed: MagnusPladsen community map (`innhold.ts` lines 1065–1642)

**Source file:** `/home/user/test/data/raw/magnus/src/data/innhold.ts` (1 642 lines). Mirror of GitHub `MagnusPladsen/hordejakten-2026`. HEAD commit is `68faa86`, dated 25.09.2026 21:04:38 +0200. The map site is written by a community member with AI help (commits are co-authored "Claude Opus 5.5"). It is a **community source**. It re-reports primary evidence (whiteboard, stream, Horde app, Horde/Alf statements) at second hand, and adds its own interpretations and model outputs.

**Blocks covered:** STEDER (1065–1078), TEORIER (1080–1140), SOL_I_DAG (1147–1151), TAAKE (1154–1156), DEFAULTNO (1159–1165), FLY_PUNKT (1168), DEFAULTNO_TERRENG (1170–1175), FLY_PUNKT2 (1178), SKYANALYSE (1181), SKYDEKKE (1188–1191), BOKSTAVER (1193), FAKTA (1195–1200), SJANSE/BESTE_KODER (1202–1233), KODER (1236–1255), FOLK_TROR (1258–1344), BOKSTAV_LESNINGER (1346–1441), HYTTER (1443–1453), SIKRE_FAKTA (1455–1468), SISTE_NYTT (1470–1624), TIKTOK_2509 (1626–1636), FLY_2509 (1638–1642).

**Cross-referenced from the same file:** the HINT objects the blocks point to (lines 46–878) and the whiteboard log TAVLE (881–1058).

**Verified against:**
- whiteboard and app images in `public/img/`, which I viewed myself;
- `public/data/fly_2130.json` and `hoyde891.json`;
- the raw adsb.lol `trace_full` files in `/home/user/test/data/raw/mk_bevis/bevis/claude-2026-09-25/adsb/`;
- the git history of `innhold.ts`, used for when items were added and for retractions.

**Conventions used here:**
- **Coordinates** are `[lat, lon]` in WGS84 decimal degrees, as stored in the file.
- **"Stream time"** is the clock the community reads off the YouTube stream. **"True time"** is real CEST.
- **Evidence classes:**
  - **[P]** primary: whiteboard, stream visual, app response, organizer statement.
  - **[C-obs]** community observation.
  - **[C-int]** community interpretation or theory.
  - **[M]** model output: default.no fusion, or the magnus site's own layers and computations.
  - **[V]** my own verification computation for this report.

---

## 0. Key takeaways

1. **Lock structure (primary, whiteboard):** there are 3 locks. Two are padlocks with 4 digits each, on the money box. One is a code lock on Anja's door, with 5 digits ("TROR 5", i.e. she thinks 5; "5 SIFFER · GANSKE SIKKER", i.e. 5 digits, fairly sure). I viewed and confirmed the photos `tavle-laser.jpg` and `tavle-5-siffer.jpg` (the latter is timestamped 2026-09-24 08:24:58).
2. **Code status (as of 25.09 21:04):**
   - **5008** is the only numeric code that the Horde app itself hands out: Kredittskår + «terje» gives «Du fant et hint! 5008». It is also Horde AS's postcode.
   - **Kodejakten** (horde.no/secret/kodejakten) says in its own page text that it gives the code of *one* padlock. Its server answered `not_configured` (503) as of 23.09.
   - **No 5-digit door code** has been found.
   - Everything else is interpretation, or rests on an unverified screenshot. This includes 0891/0810 from "2,7 eiffeltårn", 6788 from LD6788 → «ENKODE» (unverified), 5528, 2188, the "+5" variants and the powerbank numbers.
3. **Rule constraint (organizer, second-hand):** according to Alf on TikTok-live 25.09, if several people arrive together there is a queue, and failing to open the locks gives a **5-hour quarantine**. So the order in which codes are tried matters.
4. **Places:** the site's candidate set has converged on Innlandet. The main areas are:
   - the Hamar–Løten–Elverum–Rena corridor under the NOZ56U track;
   - Ringsakfjellet/Sjusjøen under NOZ9EG, including the new 25.09 theory "Jomfrua, Tjuven og Danseren" (three peaks named Virgin, Thief and Dancer) at 61.2279, 10.90754;
   - the 810/891 m a.s.l. band ("2,7 eiffeltårn", i.e. 2.7 Eiffel Towers). The community's own field observation (Hagina) argues against high ground near Lillehammer.
5. **Important data-quality finding [V]:** the flight file `public/data/fly_2130.json` (labelled "ekte tid 21.09, CEST") is time-shifted. Its labels are **about 45 s earlier** than the raw adsb.lol receive times for the same positions (NOZ56U and NOZ9EG, 5 of 5 samples each, offsets 44–46 s). Consequences:
   - Every magnus statement of the form "at the pointing moment 21:28:53 real time, plane X was N km away" effectively assumes **zero** stream delay.
   - The site's positions FLY_PUNKT and FLY_PUNKT2 were actually reached about 45 s later in true time than labelled.
   - Several distance claims in TEORIER, FOLK_TROR and the hints do not reproduce (see §9).
6. **Retractions in the git history:**
   - A "fake" chat claim that people were already at the box trying codes was removed on 25.09 11:16.
   - The Horde AI «grevling» ("badger") reply was removed on 25.09 14:56 because it was not repeatable in a new chat.
   - All Birkebeinervegen material was removed on 25.09 14:12, with no reason given in the commit.
   - The Terje T-shirt was re-classified as old, not new (25.09 13:01).
   - FILTER THE SHOP was downgraded (25.09 18:46).
   - The riverbank idea was dropped (25.09 20:53).
   - Froland was ruled out (23.09 15:46).
   - The pink "ingen sopp" ("no mushrooms") exclusion layer was removed (23.09 19:13).

---

## 1. SIKRE_FAKTA ("what we know for sure"), verbatim (lines 1455–1468)

The file's own heading comment (line 1455) reads: `/** Det vi vet sikkert. Holdes kort, og bare ting Anja, Horde eller bildet selv bekrefter. */` ("What we know for sure. Kept short, and only things Anja, Horde or the image itself confirms.")

| # | Verbatim (Norwegian) | My classification / notes |
|---|---|---|
| 1 | «Kassen står i Norge, ikke på en øy og ikke i farlig terreng.» | [P] Finn.no ad solution «Ikke en øy» (hint `ikkeoy`, l.643–651). Whiteboard «INGEN FERGE». Alf 25.09 said "aldri noe farlig, som å krysse en elv" (never anything dangerous, like crossing a river); this is second-hand. |
| 2 | «Anja ble hentet i Oslo kl. 04:00, med tildekkede bilvinduer. Hun sov mesteparten og vet ikke hvor lenge de kjørte.» | [P] whiteboard «OSLO, SØN KL 04.00» (TAVLE l.882) and the Børsen interview. Open conflict: the whiteboard says Sunday, but Børsen says "siden mandag morgen" (since Monday morning) (hint `reise`, l.120). |
| 3 | «Kun bil, ingen ferge. Siste bit var ca. 5–10 min å gå fra bilen, og hun tror det gikk oppover.» | [P] whiteboard «CA 5–10 MIN Å GÅ FRA BIL» (l.882). She was carried, wearing a sleep mask (hint `terreng`). |
| 4 | «Skog med furu, gran og mye bjørk, lyng og bærlyng. «Typisk fjellmark», masse sopp, mose på steiner, ikke vann (22.09: «ingen vann eller vannlyder, føler ikke det er vann i noe nærhet»). Fire store steiner. Kupert rundt.» | [P] whiteboards. On 25.09 18:13 she wrote «KANSKJE 35% BJØRK · 25% GRAN · 40% FURU · AKKURAT RUNDT MEG» (maybe 35 % birch, 25 % spruce, 40 % pine, right around me) (l.1051). |
| 5 | «Klar himmel kvelden 21.09. Sola var oppe før kl. 07.» | [P] whiteboard «INGEN SKYER NÅ» / «KLAR HIMMEL». "Sola oppe før 07" is attributed to Anja (hint `soloppgang`, l.499–506). |
| 6 | «Kassen er lydtett, så hun hører lite utenfra. Sol og vindstille kl. 17:49 den 23.09.» | [P] whiteboard 23.09 17:49 «LYDTETT · SOL · VINDSTILLE» (soundproof, sun, no wind). |
| 7 | «Horde-skiltet (nå fjernet) pekte ca. 118–120°, mot venstre i bildet. Kameraet står ca. 41° (nordøst) fra kassen.» | [P] whiteboards «ØST CA 118 · RETNING SKILT», «118–120 GR ØST» and «KAMERA 41 ØST». The sign was removed 23.09 19:12. A sign appears to be back in video from 25.09 16:20 (hint `skilt-tilbake`, status *usikker*, i.e. uncertain). |
| 8 | «3 låser: 2 hengelåser med 4 siffer på pengeboksen, og 1 kodelås på døra for Anja, med 5 eller 6 siffer (Anja er «ganske sikker» på 5). Appen ga 5008 som hint.» | [P] whiteboard photos checked (see §3.1). The 5008 response is an app response reported by the community; magnus marks it *løst* (solved). |
| 9 | «Horde har svart i kommentarfeltet at hint til hva kodene kan være, ligger i appen.» | [P, organizer] quote: «Hint til hva kodene kan være ligger i appen 💙» (hint `kodeniappen`, l.348–355, dated 24.09). |
| 10 | «Horde AI har et forhåndslaget svar på HORDEMINUS: «2,7 eiffeltårn stablet oppå hverandre». Eiffeltårnet er 300 m uten antenne og 330 m med, så 2,7 tårn er 810 eller 891 m. HORDE MINUS er de ti bokstavene fra «Verv en venn» (N O R H E I M S U D) stokket om.» | The Horde AI reply is [P, app]. "810 or 891 m" is arithmetic, and reading it as an **altitude** is [C-int]. The hint `eiffel` (l.362) notes that the AI, when asked, says it is only the phrase it was told to use for that word. When asked to summarise, it computes 891 m (330 m) or about 875 m (324 m) by itself. |
| 11 | «Kommer flere til kassen samtidig, blir det kø. Klarer du ikke å åpne låsene, får du 5 timers karantene (Alf på TikTok-live 25.09).» | [P, organizer] but second-hand: relayed in the chat. The source tag in the `regel-ko` hint is *bekreftet* (confirmed), while the `tiktok2509` hint says «ikke sjekket ordrett» (not checked word for word). Vilkår (terms) separately confirm a queue system (hint `regel-konvolutt`, l.693). |

---

## 2. FAKTA constants (lines 1195–1200) and STREAM (lines 6–11)

| Value | Label (verbatim) | Class |
|---|---|---|
| `1 116 897 kr` | «Premie» (prize) | [P] (the sign in the box reads «1 116 897 KR», visible in `tavle-laser.jpg`) |
| `20 s–1 min` | «Forsinkelse på streamen (vi tipper)» (stream delay, our guess) | [C-int] guess. Note: `STREAM.forsinkelseSek: 45` (l.10). mk_bevis README reports that default.no measured about 22 s. |
| `3 låser` | «2 på pengeboksen (4 siffer), 1 på døra (5 siffer)» (2 on the money box, 1 on the door) | [P] |
| `5–10 min` | «Fra bilen, båret oppover» (from the car, carried uphill) | [P] |

STREAM: `videoId: 'EQHgfmZicc8'`, url `https://www.youtube.com/watch?v=EQHgfmZicc8`, `forsinkelseSek: 45`.

---

## 3. Lock-code analysis (complete)

### 3.1 Primary evidence on the locks

| Date / time | Evidence (verbatim) | Source | Verified |
|---|---|---|---|
| 23.09 evening | «ELEKTRONISK LÅS PÅ DØRA MED 5 SIFFER» (electronic lock on the door, 5 digits) | TAVLE l.918 | no photo in mirror |
| 24.09 (no time) | «2x HENGELÅS 4 TALL · 1x KODELÅS 5–6 TALL · TROR 5» (2 padlocks with 4 numbers, 1 code lock with 5–6 numbers, think 5) | TAVLE l.990, `public/img/tavle-laser.jpg` | **Yes, I viewed it**: handwriting reads "2x HENGELÅS 4 tall / 1x KODELÅS 5-6 tall / TROR 5". The prize sign «1116 897 KR» and the toy fox are visible. |
| 24.09 08:24 (overlay "2026-09-24 08:24:58", "TavlAI") | «5 SIFFER · GANSKE SIKKER» (om dørlåsen), i.e. 5 digits, fairly sure (about the door lock) | TAVLE l.985, `public/img/tavle-5-siffer.jpg` | **Yes, I viewed it**: "5 SIFFER / GANSKE SIKKER". The overlay suggests a frame from default.no's "TavlAI" whiteboard capture. |
| 25.09 | «KAN IKKE TESTE KODER · INGEN HAR FUNNET BOKSEN (siste del litt utydelig)» (cannot test codes, no one has found the box; last part slightly unclear) | TAVLE l.1007, `tavle-2509-koder.jpg` | Viewed. The board is small and mostly illegible at mirror resolution. The magnus transcription is plausible but I cannot confirm it. |
| 21.09–23.09 | Poster «Plutselig tilbake!» ("suddenly back!"): a drawing of the box with two padlocks and "bunker" (stacks) inside, possibly card decks | hint `plakat` l.852–859 [P visual, C-int reading] | not in mirror |
| 24.09 | Horde in the YouTube comments: «Hint til hva kodene kan være ligger i appen 💙» ("hints to what the codes may be are in the app") | hint `kodeniappen` l.353 | [P organizer] second-hand |
| terms | «låse opp alle låsene med kodene fra appen» (unlock all locks with the codes from the app) and «følge instruksjonene du finner i konvolutten i kassen» (follow the instructions in the envelope in the box). «Boksen inneholder ikke fysiske kontanter» (no physical cash). There is a queue system. | hint `regel-konvolutt` l.689–695 | [P organizer, Vilkår] second-hand |
| Kodejakten client code | «Låsen er åpen: Dette er koden til den ene hengelåsen på kassen.» (The lock is open: this is the code to one of the padlocks on the box.) Four games: Kill the Bill, Bill Runner, Flappy-Alf, Dartskiven (dartboard). All four must be cleared in one session. The code is issued by the server only after verification. Help text: «Tips: Vær bedre» ("Tip: be better"). | hints `kodejakten` l.705–712, `spill-alle` l.663–671, `spill-dart` l.653–661 | [P organizer page] read from the source by magnus |
| 23.09 | Kodejakten API: all calls (start/verify) answered «not_configured» (503) | SISTE_NYTT l.1594–1598 | [C-obs] magnus's own API check. Status after 23.09 is not recorded in this file. |
| 25.09 | Alf (TikTok-live, relayed): «Kan være at noen av kodene allerede har kommet.» ("It may be that some of the codes have already come.") A queue, and 5 h quarantine if you cannot open the locks. | TIKTOK_2509 l.1631, 1633 | [P organizer] second-hand, not checked verbatim |
| 25.09 | One hand stands again in the heather in front of the box, upright with an open palm | hint `hand-tilbake` l.273–280; `public/img/stream-2509-hand.jpg` | Viewed: one upright prop hand with fingers raised, night camera |

### 3.2 App mechanisms that produced code-like responses

| Input | Where | Response | Status |
|---|---|---|---|
| «terje» | "Kredittskår": press, hold on the number and type | «Du fant et hint! 5008» ("You found a hint! 5008") | [P app] magnus status *løst/bekreftet*. The clue that leads to it is the shop item «T-skjorte i Terje-modell», 1 116 897 coins. I viewed `app-terje-tskjorte.jpg`; its text reads: «Terje-tskjorten er endelig tilbake, i limited edition grønn. H-logo på brystet, med "Terje lurer ikke meg". Denne ble svært populær under forrige Hordejakt, og vi ble utsolgt på under et døgn. Det går rykter om at de som kjøpte denne sist, økte kredittscoren sin betraktelig. Tilfeldig? Neppe.» (The Terje T-shirt is back in limited-edition green … rumour has it that those who bought it last time raised their credit score considerably. Coincidence? Hardly.) |
| «FROLAND» | same Kredittskår word box | «Du fant et hint! Ekornet kan klatre» ("the squirrel can climb"), 23.09 22:27 | **Unverified screenshot**, «kan være redigert» (may be edited) (hint `frolandekorn` l.393–401) |
| «LD6788» | "Bil & hus" (car & home), add vehicle | «Du fant et hint! ENKODE» | **Unverified screenshot** from just after midnight 24.09 (hint `enkode` l.384–391) |
| «Hordeminus» | Horde AI chat | «2,7 eiffeltårn stablet oppå hverandre» ("2.7 Eiffel Towers stacked on top of each other") | [P app] confirmed (hint `eiffel` l.357–364) |
| «Grevling» (badger) | Horde AI chat | «1 Hordeminus = 3,4 grevlinger» etc. | **RETRACTED** 25.09 14:56 (commit 337ddc2): «it was not repeatable in a new chat» |
| "Verv en venn" (refer a friend) | referral flow | letters N O R H E I M S U D, plus «Hint-hint» with a squirrel picture | [P app] |
| shaking the phone | app | black-grouse lek sound ("orrfuglleik") | [P app, community-reported] |

### 3.3 BESTE_KODER: magnus's "most likely codes", one row per lock (lines 1211–1233, verbatim)

| Lock (`las`) | Code | Why (`hvorfor`, verbatim) | Chance | Backup (`reserve`, verbatim) |
|---|---|---|---|---|
| «Døra til Anja (5 siffer)» (Anja's door, 5 digits) | **Ukjent** (unknown) | «Anja skrev at døra har en elektronisk lås med 5 siffer. Ingen kjent kode har 5 siffer ennå.» | lav (low) | «Kandidater med 5 siffer: 00891 eller 00810 (2,7 eiffeltårn), 27000 (powerbanken), 50085, 55285 (5008/5528 + «+5»), 07250» |
| «Hengelås 1 (boksen)» (padlock 1, box) | **5008** | «Det eneste tallet appen selv kaller et hint («Du fant et hint!»), og det har 4 siffer.» | høy (high) | «0891 eller 0810 (2,7 eiffeltårn), 6788 (ikke bekreftet), eller 5528 hvis «00» skal byttes med 52 (kortstokken)» |
| «Hengelås 2 (boksen)» (padlock 2, box) | **Kodejakten** | «Horde sier selv at Kodejakten gir koden til en av låsene. Koden er ikke kjent ennå.» | høy (high) | «Prøv 0891, 0810, 6788, 2188 og 5528 til Kodejakten-koden er kjent» |

Note: the origin of the 5-digit backup **07250** is not explained anywhere in the file (grep finds no other occurrence).

### 3.4 KODER: the full candidate list (lines 1236–1255, verbatim `kilde`)

| Code | Source/explanation (verbatim, `kilde`) | Status | Chance | Linked hints | My evidence class |
|---|---|---|---|---|---|
| **5008** | «Kredittskår i appen + «terje». Også postnummeret til Horde AS i Bergen. Horde sier kodehintene ligger i appen, og T-skjorta i Terje-modell (1 116 897) i butikken er hintet til å skrive «terje».» | bekreftet | hoy | terje, koder, kodeniappen | App response [P]. That it is a *lock* code is [C-int], strongly supported by «hint til kodene ligger i appen». |
| **0891** | «HORDEMINUS i Horde AI: «2,7 eiffeltårn» = 2,7 × 330 m (med antenne) = 891. Med 0 foran blir det 4 siffer, som en hengelås. Kan også være høyden (891 moh), eller begge deler.» | tolkning | middels | eiffel, koder, kodeniappen | [C-int] from an [P app] phrase |
| **8915** | «891 med «+5» fra genseren satt bak (891 og 5). 4 siffer.» | tolkning | lav | eiffel, pluss5 | [C-int] |
| **0896** | «891 + 5 = 896, med 0 foran.» | tolkning | lav | eiffel, pluss5 | [C-int] |
| **8105** | «810 (uten antenne) med «+5» bak.» | tolkning | lav | eiffel, pluss5 | [C-int] |
| **0810** | «Samme hint, men med Eiffeltårnet uten antenne: 2,7 × 300 m = 810.» | tolkning | middels | eiffel, koder | [C-int] |
| **6788** | «Fra et skjermbilde som ikke er bekreftet: skiltnummeret LD6788 i «Bil & hus» skal gi «ENKODE». Sifrene kan være koden.» | usikker | lav | enkode, koder | [C-int] on an unverified screenshot |
| **5528** | «5008 med 52 i stedet for 00: plakaten ser ut til å vise kortstokker, og en kortstokk har 52 kort.» | tolkning | middels | plakat, koder | [C-int] |
| **2188** | «Nevnt i chatten. Ingen vet hvor den kommer fra.» | usikker | middels | koder | chat rumour, no provenance. Magnus nonetheless rates it "middels" (medium), which is not justified by any evidence in the file. |
| **7…** | «Hendene under Horde-skiltet: romertall (første hånd VII = 7) eller binært.» | tolkning | lav | skilt, koder | [C-int] on [P visual]. A single open hand re-appeared 25.09. |
| **5013** | «5008 + 5, hvis «+5» på genseren skal legges til koden.» | tolkning | lav | pluss5, terje | [C-int] |
| **0553** | «5008 med +5 på hvert siffer (5→0, 0→5, 0→5, 8→3).» | tolkning | lav | pluss5, terje | [C-int] |
| **5271** | «Powerbank Xtorm FS5271 i Horde Rewards (jaktvettregel 4 nevner powerbank). Trolig bare et modellnummer.» | usikker | lav | powerbank | [C-int]. FS5271 is a real product model number. |
| **27000** | «Samme powerbank, 27000 mAh. 5 siffer, som dørlåsen. Trolig tilfeldig.» | usikker | lav | powerbank | [C-int] |
| **072** | «Ho Ho Hint Hint»: «siste sifre i premien fra 2024 (1 093 072 kr). Bare 3 siffer.» | usikker | lav | hohoh | [C-int]. Unclear whether it applies to 2026. |
| **500** | «Ho Ho Hint Hint»: «poeng for å verve. Bare 3 siffer.» | usikker | lav | hohoh | [C-int] |
| **ord** (word) | «Kredittskår-boksen tar imot ord («terje» ga 5008, og ifølge skjermbilder som ikke er bekreftet, «FROLAND» og skiltnummeret LD6788). Verdt å prøve: LØTEN, RENA, RINGSAKER, RUDSHØGDA, JAKTEN, MINUSHORDE, HORDEMINUS, NORHEIMSUND.» | tolkning | middels | terje, frolandekorn, enkode, bokstaver, dyr | Suggestion. Note that LD6788 was reportedly entered in "Bil & hus", not the Kredittskår box, so the file is internally inconsistent here. |
| **????** | «Kodejakten gir koden til én hengelås når alle fire spill er klart (bekreftet i kildekoden). Dartskiven: blå +, gul −, rosa ×, lilla ÷. Kodejakten (horde.no/secret/kodejakten): fire minispill gir én kode.» | apen (open) | hoy | kodejakten | [P organizer page] |

Solved campaign codes that are **not** lock codes, per magnus:
- sweater numbers «7 10 5 12 / 4 6 18 9» decode with A=1 to **GJELDFRI** ("debt-free") (hint `genser`, l.540–546);
- trouser Morse decodes to **PREMIE** ("prize") (l.548–554);
- trouser Caesar +5 «MT WI JO FP YJ S@ MT …» decodes to **HORDEJAKTEN@HO…**, probably hordejakten@horde.no. This was a mini-contest (20 000 Horde points to the first solver) (l.556–563).

Applying +5 or −5 to the sweater numbers gives «LOJQIKWN» / «BEZGYAMD», which are meaningless (hint `pluss5`, l.840).

### 3.5 Assessment and suggested order of attempts

The following is interpretation (mine plus magnus). It is not evidence.

- **Padlock 1 = 5008**: best supported. It is the only numeric app "hint". Horde says code hints are in the app. The T-shirt priced exactly at the prize amount signposts the «terje» trick.
  - Caveat: 5008 is also Horde's postcode, and the same «Du fant et hint!» banner is used for non-numeric hints (ENKODE, «Ekornet kan klatre»). So "hint" ≠ "lock code" by itself.
- **Padlock 2 = the Kodejakten code**: organizer text states this explicitly. The code is unknown until the server is enabled (it was not enabled as of 23.09). Alf: «Kommer en del viktige hint nå i løpet av helgen» ("a number of important hints are coming this weekend"), i.e. 26–27.09.
- **Door (5 digits): unknown.** No evidence-based candidate exists.
  - The magnus backups (00891, 00810, 27000, 50085, 55285, 07250) are all speculative.
  - Logically, if 5008 plus the Kodejakten code fill both padlocks, then 6788 (if the screenshot is genuine) and "2,7 eiffeltårn" have no 4-digit lock left. Either one of them feeds the 5-digit door code, or one assumption is wrong. This is an **open question**.
- Because of the queue and the 5 h quarantine, a finder should try in this order: 5008, then the Kodejakten code if available, then 0891, 0810, 6788, 5528, then the rest. This matches the file's own advice «Prøv de sikreste først» ("try the safest first") (l.1633).
- **Retracted:** the chat claim «Flere som har prøvd seg på koden ved boksen nå by the way. Vi vet hvor det her er hen.» ("Several have tried the code at the box now, by the way. We know where this is.") was removed as a **fake item** on 25.09 11:16 (commit 094b3b8). It was also contradicted by Anja's 25.09 board «KAN IKKE TESTE KODER · INGEN HAR FUNNET BOKSEN».

---

## 4. Candidate places with coordinates

For each place: the class, what magnus says for and against (quoted or paraphrased from the `info`/`hvem` text), and the status.

### 4.1 STEDER (lines 1065–1078)

| id | Name (verbatim) | lat, lon | Type | `info` (verbatim) | Status |
|---|---|---|---|---|---|
| oslo | Oslo (start) | 59.9139, 10.7522 | start | «Anja ble hentet her søndag 20.09 kl. 04:00.» | reference |
| horde | Horde AS, 5008 Bergen | 60.3896, 5.3297 | hint | «Koden 5008 er postnummeret til Horde AS (Lars Hilles gate 20A).» | reference (code origin, anchor of the 118° line) |
| brauta | «Brauta», Ringebu (sør for Fåvang) | 61.43659, 10.1854 | hint | «Stedsnavn som ligner Haalands mellomnavn Braut. Dyrket mark, ca. 190 moh. Tips fra chatten.» | weak. Hint `haaland-brauta`: 37 cells at 810–891 m near a road within 5 km, most with the road to the SE. Wind was about 4 m/s there on 23.09 17:49, against «vindstille». |
| jomfrua | Jomfrua, Tjuven og Danseren (Ringsaker) | 61.2279, 10.90754 | hint | «Tre fjelltopper innen 1,3 km, ca. 1010–1026 moh, åpent område over skoggrensa. Teori: olivenolje → «ekstra jomfru» → Jomfrua, THE SHOPLIFTER → Tjuven, orrfuglleik → Danseren.» | **active** (new 25.09) |
| texas | «Texas», Våler i Solør | 60.87812, 12.21229 | hint | «Adressenavnet Texas i Våler (Innlandet), ca. 348 moh. Teori fra fellesskapet: «2,7 eiffeltårn» kan være Eiffeltårnet i Paris, Texas.» | weak, excluded on the community map |
| kompassen | «Kompassen», Våler i Solør | 60.87639, 12.31426 | hint | «Holme som heter Kompassen, ca. 302 moh, 5,5 km rett øst (92°) for Texas.» | weak. It is also a *holme* (islet), which conflicts with «Ikke en øy» (not an island). [V] 5.54 km at 91.9° from Texas: confirmed. |
| kroktjennet | Topp ca. 891 moh ved Kroktjennet, Åmot | 61.2405, 11.01 | hint | «Tips fra fellesskapet: et punkt på 891 moh nordvest for Kroktjennet (Hemmeldalen, vest for Rena). Kartverket gir ca. 887 moh her, åpent område. Ligger inne i Hemmeldalen naturreservat, der det er strenge regler for inngrep.» | weak (nature reserve, open ground, no car road within 900 m). [V] No `hoyde891` near-road cell within 1 km; the nearest is 4.7 km away. |
| bjorneparken | Bjørneparken, Flå | 60.4343, 9.4493 | hint | «Reklamefargene til Horde ligner Bjørneparken sine.» | weak (moved 1.2 km to the correct position on 24.09) |
| proysen | Prøysenstua, Rudshøgda | 60.912, 10.8076 | hint | «Alf Prøysens barndomshjem. Dyrene i boksen (rev, kråke, ekorn) er figurer fra Prøysens «Sirkus Mikkelikski». Én i chatten har sjekket stua, men skogen rundt er ikke sjekket.» | the house was searched (empty); the forest around it was not |
| proysenstjerna | Prøysenstjerna (ca.) | 60.9115, 10.806 | hint | «27 m høy stjerne i granskogen bak Prøysenstua, laget til Prøysen-jubileet i 2014 etter hans julevers om stjerna.» | weak (lowland, «fjellmark» argues against) |
| tokke | 2023: Tokke (område) | 59.444, 7.989 | tidligere (prior year) | «Hordejakten 2023 ble funnet i Tokke i Telemark. Skog, bil og litt gange.» | prior-year reference |
| kongsberg | 2024: Kongsberg-området | 59.668, 9.65 | tidligere (prior year) | «Hordejakten 2024 ble funnet i Kongsberg-området i Buskerud. Skog.» | prior-year reference |

### 4.2 TEORIER (lines 1080–1140)

| id | Name | lat, lon | `info` (verbatim) | Status |
|---|---|---|---|---|
| digeras | Tips: Digeråsen (Løten/Åmot) | 61.1788, 11.2639 | «61°10'43.8"N 11°15'50.1"E. Flere i chatten mener dette stemmer godt. Skog, 606 moh., 2 t 35 min fra Oslo, i kanten av det som var klart på satellitt 23.09. NOZ56U var rett over her kl. 21:32:50 (74°), da rumlingen var høyest. Men da Anja pekte opp (21:28:53 ekte tid) var flyet 45 km unna og bare 8° over horisonten.» | active/uncertain. [V] DMS matches the decimal value. The 45 km / 8° and 74° values reproduce **only** in the fly_2130 time base. In the raw ADS-B time base the 74° maximum occurs at 21:33:32 true time. |
| benningstad | Benningstad, Løten («Benny»?) | 60.7685, 11.3575 | «Gårdsnavn i Løten som ligner «Benny». Ca. 10 km fra der flyet NOZ56U var kl. 21:28. Trolig bare en tilfeldighet.» | weak. [V] 7.0 km from NOZ56U at the magnus 21:28:53 position; 12.8 km from FLY_PUNKT. |
| bennyoy | Bennyøy, Nome («Benny»?) | 59.2666, 9.1327 | «Eneste stedsnavn i Norge som starter med «Benny». En holme i Nome, Telemark, bare 3,4 km fra 118°-linja fra Horde i Bergen. Men «Ikke en øy»-hintet taler imot.» | rejected in practice (it is an island). [V] Great-circle 118° line from Horde: 3.2 km. Rhumb line: 10.5 km. Bearing Horde→Bennyøy = 118.7°. |
| tretopp | Tips: Tretopphyttene, Ringsaker | 60.9748, 10.9167 | «Danseråsvegen 173, Brumunddal. Logoen er et ekorn. Ringsaker er også Prøysens kommune (Sirkus Mikkelikski). Ca. 2 t fra Oslo. NOZ56U var ca. 21 km unna (19° over horisonten) da Anja pekte opp.» | searched: «én i chatten har vært innom alle hyttene og Prøysenstua, uten funn» (someone in the chat visited all the cabins and Prøysenstua, found nothing). Also «INGEN HYTTE I NÆRHETEN SOM JEG VET OM ELLER SER» (no cabin nearby that I know of or can see) (24.09 17:20). [V] Distance at the pointing moment is 28 km / 12° (fly_2130 base). 21 km matches FLY_PUNKT (21:29:50 label). |
| haslemoen | Tips: Flisa og Haslemoen | 60.66, 11.87 | «Noen tror det er nær Rena, men mer mot Flisa. Haslemoen har en nedlagt militærleir. Innenfor det som var klart på satellitt 23.09. Ca. 2,5 t fra Oslo. Flyet NOZ56U var ca. 40 km unna (10° over horisonten) da Anja pekte opp.» | weak; Solør is excluded on the community map. [V] 37 km / 9°. |
| nittedalen | Tips: Nittedalen | 60.07, 10.87 | «Nevnt i chatten. Bare 37 min fra Oslo, 58 km fra begge flyene og utenfor det som var klart i dag. Passer dårlig.» | poor fit. [V] "58 km from both planes" does not reproduce: 92 km from FLY_PUNKT and 128 km from FLY_PUNKT2; only the southern end of the NOZ9EG segment is about 58 km away. |
| gjovik | Gjøvik (vær og sol passer) | 60.795, 10.692 | «Noen i fellesskapet mener vær og solgang passer med Gjøvik. Ca. 2 t fra Oslo.» | weak (lowland; 95 % "open" on the exclusion map) |
| norheimsund | Norheimsund (bokstavene) | 60.3707, 6.1453 | «Vervebokstavene N O R H E I M S U D gir NORHEIMSUND med én N til. 6,5 t fra Oslo uten ferge, og ca. 1 t fra Horde i Bergen (5008).» | effectively rejected (the letters are solved as HORDE MINUS; Hardanger was blue on Windy) |
| froland | Froland (utelukket) | 58.53, 8.63 | «Utelukket: været i Froland samsvarer ikke med det Anja har sett. Et skjermbilde som ikke er bekreftet, viser at FROLAND gir «Ekornet kan klatre» i appen.» | **excluded** (it rained there on the evening of 23.09, with no rain on the stream) |
| lillehammer | Lillehammer (ekorn-maskot) | 61.115, 10.466 | «Lillehammer kommune lanserte i 2026 ekornet «Lille» som offisiell maskot for byens 200-årsjubileum. Kobler ekorn-hintet til Lillehammer. Mot: Lillehammer lå i det blå båndet på Windy-kartet, og Hagina så at høsten har kommet langt i høyden der.» | weak |
| notteroy | Nøtterøy (utelukket) | 59.21, 10.42 | «Ordspill på «nøtt», men «Ikke en øy» og «ingen ferge» taler mot.» | **excluded** |

### 4.3 FOLK_TROR: what people in the chat and on Discord believe (lines 1258–1344)

| # | `tekst` | pos / fokus | `hvem` (verbatim, abridged only where marked …) | Status |
|---|---|---|---|---|
| 1 | Jomfrua, Tjuven og Danseren: tre topper på Ringsakfjellet | 61.2238, 10.9001 (fokus jomfrua) | «Teori 25.09: olivenolje → «ekstra jomfru» → Jomfrua, THE SHOPLIFTER → «tjuven» → Tjuven, orrfuglleik (parringsdans) → Danseren. Alle tre er fjelltopper i Ringsaker, innen 1,3 km. For: tre hint som peker på tre navn på samme sted, 9,5 km fra flyet NOZ9EG, ikke utelukket, og 20 steder på 810–891 moh nær vei innen 3 km. Mot: selve toppene er 1010–1026 moh og åpent område over skoggrensa, mens kassen står i skog. Hagina så at høsten er langt kommet i høyden der. Kassen kan i så fall stå lavere i lia under toppene.» | active [C-int]. [V] 20 cells within 3 km: reproduced. "9.5 km from NOZ9EG" reproduces only with the raw ADS-B at about 22 s delay (10 km, 35° elevation). In the fly_2130 base NOZ9EG passes within 0.6 km (see §9). |
| 2 | THE SHOPLIFTER = hint til «Bob», altså bobbanen på Lillehammer? | 61.2185, 10.4525 | «Tips 25.09: BobTheShoplifter kan være et nikk til «Bob», og Skandinavias eneste bobbane ligger på Hunderfossen ved Lillehammer. For: vindstille der 23.09 kl. 17:49, og 148 steder på 810–891 moh nær vei innen 10 km. Mot: selve bobbanen ligger lavt (ca. 280 moh), det er 25–46 km til flyene hun så, og Hagina så at høsten har kommet langt i høyden rundt Lillehammer. Trolig bare en hilsen til BobTheShoplifter.» | weak. [V] 148 cells: reproduced. |
| 3 | Feltobservasjon: bjørka er for langt på høsten på ca. 510 moh (takk til Hagina) | 60.98, 10.72 | «Hagina på Discord (25.09), ute mellom Hamar, Lillehammer og Sjusjøen på ca. 510 moh: «Her er bjørketrærne oransje, ikke gule som på streamen» og «de er mye tynnere i bladverket her oppe enn på stream». Høsten har altså kommet lenger der enn der kassen står. Det taler for at kassen står lavere eller et mildere sted, og mot 810–891 moh i det området, der høsten kommer enda tidligere.» | [C-obs] a negative field observation. Commit 889d715 (25.09 16:06) used it to pull down high terrain around Ringsakfjellet/Sjusjøen. |
| 4 | Nær Brumunddal, der Anja kommer fra | 60.88362, 10.94489 (fokus ringsaker) | «Tips 25.09: Anja er opprinnelig fra Brumunddal, så kanskje hun er «nesten helt hjemme». For: Brumunddal ligger i Ringsaker, 9 km fra sporet til NOZ9EG, og det var vindstille der 23.09 kl. 17:49. Mot: ingen steder på 810–891 moh nær vei innen 20 km, de nærmeste er oppe mot Ringsakfjellet og Sjusjøen 20–30 km nord. Horde vil trolig ikke plassere henne der hun kan kjenne seg igjen, og det er bare ca. 1,5 t fra Oslo.» | weak. [V] 0 cells within 20 km (nearest 23.6 km): reproduced. The NOZ9EG track passes **4.5 km** from this point, not 9 km. The claim that Anja comes from Brumunddal is unsourced in the file. |
| 5 | Mange steder i Innlandet ligger ca. 890 moh | — | «Discord 25.09: Trysil, Engerdal, Sjusjøen, Ringsakfjellet, oppover Østerdalen og Gudbrandsdalen ligger ca. 890 moh med samme type skog. Svar fra Veritas XO: men bare Froland og Østerdalen passer med dagen det var skyet over hele landet sør for Mo i Rana mens Anja hadde sol, og med flyene. Høyden alene snevrer altså lite inn.» | [C-int] |
| 6 | Tommsen A: ved Tingstadbrua (Ringsaker) | 61.1139, 11.0011 | «Tommsen på Discord (25.09), punkt A. Skog, ca. 623 moh, ikke utelukket. Mot: nærmeste sted på 810–891 moh nær vei er 4,5 km unna.» | weak. [V] Nearest cell 4.58 km: reproduced. |
| 7 | Tommsen B: Stor-Elvdal, vest for Glomma | 61.4732, 10.9687 | «Tommsen på Discord (25.09), punkt B. Skog, ca. 411 moh, rett ved default.no sine letestopp ved Gålaveien. Mot: langt under 810–891 moh (nærmeste treff 2,7 km unna).» | weak. [V] Nearest cell 2.68 km: reproduced. It is 0.09 km from DEFAULTNO_TERRENG "Gålaveien" and identical to the default.no pin «PLAN 6 Galaveien-ryggen» (61.4732, 10.9687). |
| 8 | Tommsen C: Gruvelia/Vardåsen arbeidsområde (Nannestad) | 60.18519, 10.89289 | «Tommsen på Discord (25.09), punkt C. Mot: ca. 319 moh og punktet ligger i en elv. Nær Gardermoen, der det er mye lavtflygende fly, mens Anja skrev «LITE MED FLY HER». Langt fra 810–891 moh.» | effectively rejected |
| 9 | Finnskogen | 60.60349, 12.37164 | «Mange på Discord tipper Finnskogen nå (25.09). Mot: terrenget er for lavt for 810–891 moh (ingen treff i høydelaget), og Finnskogen er utelukket på fellesskapets utelukkingskart.» | rejected by magnus. [V] Nearest cell 71 km. |
| 10 | «Eiffeltårnet i Texas»: Texas og Kompassen i Våler (Solør) | fokus texas | «Noen mener «2,7 eiffeltårn» kan være Eiffeltårnet i Paris, Texas. … For: to navn fra hintene på samme sted, i Innlandet. Mot: Texas ligger ca. 348 moh og Kompassen 302 moh, langt unna 810–891 m. Tårnet i Paris, Texas er ca. 20 m, og 2,7 av dem er bare ca. 54 m. Området er utelukket på fellesskapets kart, og Solør er trukket ned. Nytt 25.09: det utstoppede dyret i Horde Rewards ligner Haalands vaskebjørn, som ble kjøpt i Dallas, Texas.» | weak |
| 11 | Topp på 891 moh ved Kroktjennet i Hemmeldalen (Åmot) | fokus kroktjennet | «HORDE MINUS → 2,7 eiffeltårn → 891 m. … Hemmeldalen er et naturreservat med skog, myr og mye dyre- og fugleliv, og verneforskriften nevner ande- og vadefugler spesielt (passer med and-hintet). Hemmeldalen-setrene ligger sørøst for toppen, som passer med «kom fra den veien ←». Mot: det er et naturreservat med strenge regler, toppen er åpent område og ikke skog, og det går ingen bilvei innen 900 m (OpenStreetMap). Da rekker man ikke å bære kassen dit på 5–10 min.» | weak |
| 12 | Innlandet | — | «De fleste, og stadig flere er sikre: «Det er null tvil, været, sola, skogen og alt.» Klar himmel på Østlandet, flyet over Hamar/Løten, furumo og tømmerdrift.» | consensus region [C-int] |
| 13 | Digeråsen mellom Løten og Åmot | fokus digeras | «Flere sier det «er så klink her». Passer med lyden av flyet, ikke med pekingen.» | uncertain |
| 14 | Hamar–Løten–Elverum | 60.87, 11.25 | «Vår modell: der flyet var da Anja pekte rett opp (over Hamar, like ved Løten).» | [M] magnus model. This point equals FLY_PUNKT, which is where NOZ56U was about 45 s *after* the labelled time (see §9). |
| 15 | Reven heter Benny | fokus bennyoy | «Bennyøy (Nome) ligger 3,4 km fra 118°-linja fra Bergen. Benningstad (Løten) er nær flyet. Trolig tilfeldig.» | weak. Primary: whiteboard, the fox toy is called Benny (hint `benny` l.58–68). |
| 16 | Rudshøgda (Prøysen) | fokus proysenstjerna | «Mange leter her nå. Rev, kråke og ekorn er alle figurer i Prøysens «Sirkus Mikkelikski», og Prøysenstjerna står bak Prøysenstua.» | weak |
| 17 | Rundt de to flysporene | 61.0, 11.05 | «Eneste stedene det er sol i Norge nå + eneste stedene det fløy fly over hodet hennes 21:29.» Løten–Elverum (NOZ56U) og Ringsaker (NOZ9EG).» | [C-int] |
| 18 | Nittedalen | fokus nittedalen | «Nevnt i chatten. 37 min fra Oslo og langt fra flyene, så passer dårlig.» | poor fit |
| 19 | Tretopphyttene i Ringsaker | fokus tretopp | «Sjekket: én i chatten har vært innom alle hyttene og Prøysenstua, uten funn. NOZ9EG gikk 3 km unna kl. 21:31.» | searched, negative |
| 20 | Flisa og Haslemoen | fokus haslemoen | «Én person: «nær Rena, men mer mot Flisa». Nedlagt leir på Haslemoen.» | weak |
| 21 | Rena–Evenstad | 61.45, 11.1 | «default.no sin toppkandidat, øst for Glomma i Stor-Elvdal.» | [M] default.no rank 1 (steder.json, 24.09 18:06: p = 0.127) |
| 22 | Gjøvik | fokus gjovik | «Én person: vær og sol passer.» | weak |
| 23 | Norheimsund | fokus norheimsund | «Bokstavene, men mangler én N. HORDE MINUS går opp uten rest, og Hardanger var blått på Windy.» | rejected |
| 24 | Froland er ute | fokus froland | «Været samsvarer ikke med det Anja har sett: det regnet i Froland onsdag kveld, men ikke på streamen. Et skjermbilde (ikke bekreftet) viser at appen svarer «Ekornet kan klatre» på FROLAND.» | excluded |
| 25 | Lillehammer: ekornet «Lille» er byens maskot | fokus lillehammer | «… Mot: Lillehammer lå i det blå båndet på Windy, og Hagina så at bjørka er langt på høsten i høyden rundt Lillehammer. Bobbane-tipset («Bob») peker også mot Lillehammer.» | weak |
| 26 | MINUS HORDE = JAKTEN | — | «HORDEJAKTEN» minus «HORDE» gir «JAKTEN». Rev, and og kråke er jaktbare dyr … Prøv ordene i kredittskår-boksen i appen, der «terje» ga 5008.» | [C-int], a code idea |
| 27 | 118° fra Bergen, gjennom Telemark | 59.5, 8.46 | «Anja sier skiltet peker 118°. Noen trekker linja fra Horde AS i Bergen (5008): Odda, Vinje, Seljord, Kragerø.» | weak (the sign stood at the box, not in Bergen) |
| 28 | Ikke Odal eller Jessheim | 60.3, 11.45 | «Lokal: tykk tåke der i morges, mens Anja ikke hadde tåke.» | exclusion [C-obs] |
| 29 | Ikke Fredrikstad, Sarpsborg eller Halden | — | «Overskyet der hele dagen, mens Anja hadde sol.» | exclusion [C-obs] |
| 30 | Tromsø (69° nord) | — | «TikTok-teori om «MINUS HORDE». Rundt 20 t fra Oslo, så lite sannsynlig.» | rejected |
| 31 | Sollyset er falskt | — | «Noen mener bildet er filtrert. Da er hint fra sol i bildet usikre.» | counter-argument (hint `lysfake`): an independent camera azimuth from the sun (219–220°) agrees with «KAMERA 41 ØST» (221°) |

### 4.4 BOKSTAV_LESNINGER: readings of the referral letters (lines 1357–1441)

BOKSTAVER (l.1193): `['N','O','R','H','E','I','M','S','U','D']`.

| Word | Strength | Explanation (verbatim) | pos |
|---|---|---|---|
| HORDE MINUS | sterk (strong) | «Bekreftet: Horde AI svarer «2,7 eiffeltårn stablet oppå hverandre» på «Hordeminus». 2,7 × 330 m = 891 m, trolig høyden over havet.» | — |
| MINUS 5 (dekod med −5) | sterk | ««+5» står på genseren, og buksa er kodet med +5 (MT WI JO = HO RD EJ). «MINUS HORDE» kan være bruksanvisningen: trekk fra 5 for å dekode. HORDE +5 blir MTWIJ, som står på buksa.» | — |
| JAKTEN | middels | ««HORDEJAKTEN» minus «HORDE». Rev, and og kråke er jaktbare dyr, og ekorn ble før jaktet for kjøtt og pels i Innlandet. Prøv i kredittskår-boksen.» | — |
| NORDHUE + MIS | middels | «Nordhue er et sted mellom Løten og Åmot, 14 km fra der NOZ56U var kl. 21:29. Bruker 7 av bokstavene, resten (M I S) er ikke et tydelig ord.» | 60.994, 11.3382 ([V] 14.6 km from FLY_PUNKT) |
| SMERUD + OHIN | svak (weak) | «Smerud er et sted i Solør, like ved Haslemoen og Flisa-tipset. Resten (O H I N) gir ikke et ord.» | 60.65, 11.7833 |
| DISEN + HUMOR | svak | «Bruker alle ti. Disen er et sted ved Hamar og Løten. «Humor» passer med tonen i Horde sine hint.» | 60.8, 11.08 |
| OSHEIM + RUND | svak | «Bruker alle ti. Osheim ligger nord-øst i Rena/Åmot-området.» | 61.4282, 11.7075 |
| NORDHEIM + SU | svak | «Nordheim er et vanlig gårdsnavn (169 steder i Norge), så det sier lite om hvor.» | — |
| NORHEIMSUND | svak | «Mangler én N. Stedet var blått på Windy-kartet.» | 60.3707, 6.1453 |
| HINDU MORSE | svak | «Bruker alle ti. «Morse» kobler til morsekoden på buksa (PREMIE). Trolig tilfeldig.» | — |
| HUNDRE + MISO / HODER MINUS | svak | «Tall-ord i bokstavene: HUNDRE (100) og MINUS. Kan være del av en kode, for eksempel minus 100.» | — |
| HUS MINE ORD / DINE HUS MOR | svak | «De vanligste ordene som bruker alle ti. Gir ingen tydelig mening, så trolig tilfeldige.» | — |
| 69° nord / Tromsø | svak | «TikTok-teori om «MINUS HORDE». Rundt 20 t fra Oslo, så lite sannsynlig.» | — |

Note: "NORDHUE + MIS" uses N,O,R,D,H,U,E,M,I,S, which is all ten letters, not 7 as the file says. NORDHUE is 7 letters, and the remainder M, I, S uses the other three.

### 4.5 HYTTER: Tretopphyttene booking status 23.–27.09 (lines 1443–1453)

The comment says: «`opptatt` gjelder 23.–27.09 ifølge bookingkalenderen» (booked status is for 23–27.09 according to the booking calendar, tretopphytter.no).

| Cabin | Place | lat, lon | Booked (verbatim) | [V] NOZ9EG closest approach (fly_2130 labels) |
|---|---|---|---|---|
| Bjørkhytta | Danseråsen | 60.9914, 10.8841 | Opptatt sammenhengende 23.09–11.10 (`helePerioden: true`) | 0.33 km at 21:30:59 |
| Granhytta | Danseråsen | 60.9902, 10.8866 | Opptatt 23.09 og 25.09–03.10 | 0.47 km |
| Utsiktsredet | Danseråsvegen | 60.9748, 10.9167 | Opptatt 24.–26.09 | 2.2 km |
| Himmelhytta | Klufttjernet | 60.9978, 10.8777 | Opptatt 24.–28.09 | 0.07 km |
| Furuhytta | Sør-Mesna | 61.0747, 10.8309 | Opptatt 23.–27.09 | 2.9 km |
| Forest View | Høgbrennvegen | 60.9811, 10.9401 | Opptatt 24., 26. og 27.09 | 3.4 km |
| Lerkhytta | Veldre (ca.) | 60.93, 10.9 | Opptatt 25.–27.09 | 1.6 km |
| Klatrehytta | Helgøya | 60.7388, 10.9798 | Opptatt 25.–27.09 | 7.9 km |

Magnus considers this «Trolig ikke relevant» (probably not relevant). Anja was at a pause place «uten vinduer og uten wifi» (without windows or wifi). She wrote «INGEN HYTTE I NÆRHETEN» (no cabin nearby). The cabins were searched with no find.

### 4.6 default.no model points mirrored in the file

**DEFAULTNO (l.1158–1165):** the comment says «Toppkandidater fra default.no sin fusjonsmodell (22.09 kl. 16:42; klare celler i kveld 23.09)» (top candidates from default.no's fusion model, 22.09 at 16:42; clear cells this evening, 23.09).

| nr | lat, lon | Name | p (verbatim) | [V] closest approach NOZ56U / NOZ9EG |
|---|---|---|---|---|
| 1 | 60.9, 11.2 | Hamar øst mot Løten (skog) | «Klar himmel, under flyet» | 2.9 km / 18 km |
| 2 | 61.3, 11.2 | Rena og Åsta | «Klar himmel, under flyet» | 7.3 km / 16 km |
| 3 | 61.5, 11.0 | Koppang | «8,2 °C klart i kveld» | 26 km / 17 km |
| 4 | 60.6, 12.35 | Finnskogen (Solør) | «8,5 °C klart i kveld» | 63 km / 84 km |
| 5 | 61.3, 12.3 | Trysil | «6,1 °C klart i kveld» | 51 km / 75 km |

**Staleness caveat:** the mirrored default.no `steder.json` (updated `2026-09-24T18:06:17`, retning 219.0) has a different ranking:

| Rank | lat, lon | p |
|---|---|---|
| 1 | 61.45, 11.1 (Rena–Evenstad) | 0.127 |
| 2 | 60.7, 11.6 | 0.056 |
| 3 | 60.95, 11.3 | 0.054 |
| 4 | 61.75, 11.1 | 0.02 |
| 5 | 58.55, 6.1 | 0.044 |
| … | | |

So the DEFAULTNO constant is out of date by at least one model iteration.

**DEFAULTNO_TERRENG (l.1169–1175):** «Sterke terrengtreff fra default.no sitt «site finder» (vei, oppoverbakke, furu, relieff og solhorisont)» (strong terrain hits from default.no's site finder: road, uphill slope, pine, relief and sun horizon).

| Name | lat, lon | Area |
|---|---|---|
| Gålaveien | 61.4725, 10.9677 | Rena/Åmot |
| Madsskardveien | 61.4747, 11.0966 | Rena/Åmot |
| Tolvmilskogen | 60.69, 12.35 | Solør |
| Kirkesjøvegen | 60.358, 12.507 | Solør/Finnskogen |

**Removed:** «Birkebeinerveien» at 61.4495, 10.9752 (Rena/Åmot) was deleted on 25.09 14:12 (commit e431102, "Remove everything about Birkebeinervegen"). The same commit removed:
- the FOLK_TROR entry «Birkebeinervegen over Ringsakfjellet (Ringsaker–Rena)» at 61.36168, 10.84625. It said «ca. 720–1040 moh. Det er 341 steder på 810–891 moh nær vei her, 233 av dem med vei mot sørøst … området er ikke utelukket» (about 720–1040 m a.s.l.; 341 places at 810–891 m near a road here, 233 of them with the road to the SE; the area is not excluded);
- default.no pins «BOM / privat vei (23.09 ca 00:30) - Birkebeinerveien-avkjoring mot 61.4495,10.9752. Ga forbi bommen til fots, 500 m» (barrier / private road, turn-off towards 61.4495,10.9752; walked past the barrier on foot, 500 m) and «privat vei - pin Birkebeinerveien-ryggen, ikke sjekket til fots» (private road, ridge pin, not checked on foot).

The commit gives **no reason**. The mk_bevis analysis still lists "A1 Birkebeinerveien" as a candidate.

**Current default.no pins in the mirror (`public/data/defaultno/pins.json`)**, for cross-reference:

| Pin | Point | Note |
|---|---|---|
| — | 61.4307, 11.0483 | «privat vei - sjaforen er her NA (23.09 00:40), serviceveg av Storelvdalsveien, 410 m gange» (private road, the driver is here now; service road off Storelvdalsveien, 410 m walk) |
| PLAN 1 | 61.376, 11.143 | Evenstad øst E1 |
| PLAN 2 | 61.382, 11.125 | Evenstad øst E2 |
| PLAN 3 | 61.387, 11.14 | Evenstad øst E4 |
| PLAN 4 | 61.372, 11.094 | Evenstad øst E3 |
| PLAN 5 | 61.3954, 11.0343 | Snipperslåtten A |
| PLAN 6 | 61.4732, 10.9687 | Gålaveien-ryggen |
| PLAN 8 | 61.4628, 10.9755 | Gålaveien sør |
| PLAN 9 | 61.4682, 11.0325 | Søstugutua |
| PLAN 10 | 61.25, 11.0 | «Elverum-stripa … bare hvis 1-9 er tomme» (only if 1–9 are empty) |

### 4.7 Aircraft reference points (not box candidates)

| Constant | lat, lon | Details (verbatim comment) | [V] |
|---|---|---|---|
| FLY_PUNKT (l.1167–1168) | 60.8705, 11.2481 | «Der NOZ56U var da Anja skrev «FLY» (ekte tid ca. 21:29:50)» (where NOZ56U was when Anja wrote "FLY", real time about 21:29:50). Callsign NOZ56U, 23 892 ft. | Matches the fly_2130 interpolation at the 21:29:50 label. The raw adsb.lol trace puts NOZ56U there at about **21:30:35 CEST**. |
| FLY_PUNKT2 (l.1177–1178) | 61.216, 10.896 | «Det andre flyet nær Anja 21:29: NOZ9EG sørover mot Gardermoen, over Ringsakfjellet (ca. 21:29:15, 23 500 fot)» (the other plane near Anja at 21:29: NOZ9EG southbound to Gardermoen, over Ringsakfjellet, about 21:29:15, 23 500 ft) | Matches the fly_2130 interpolation at 21:29:15. Raw trace: NOZ9EG there at about **21:30:00 CEST** (baro about 23 400, geom about 24 150 ft). |
| hint `fly2509` pos (l.250) | 60.59, 11.536 | SAS50J when Anja pointed on 25.09 | see §7 |
| hint `regn1105` pos (l.201) | 61.133, 11.367 | Rena (rain at 11:05 on 24.09) | — |

### 4.8 Area layers (polygons), with full coordinates

- **SOL_I_DAG (l.1142–1151):** «Klare områder på satellittbildet 23.09 (fellesskapet) … Grovt tegnet ut fra en beskrivelse, ikke fra selve bildet.» (Clear areas on the 23.09 satellite image, from the community; drawn roughly from a description, not from the image itself.) Class [C-obs], roughly drawn.
  - [0] Kongsvinger–Rena towards Sweden: `[[60.1,11.85],[60.5,11.6],[60.88,11.35],[61.15,11.2],[61.3,11.35],[61.3,12.1],[61.0,12.45],[60.6,12.6],[60.2,12.55],[60.0,12.2]]`
  - [1] parts of Vestfold: `[[59.05,9.95],[59.1,10.55],[59.6,10.45],[59.65,10.0],[59.35,9.8]]`
  - [2] Trondheim–Ålesund («var blått på Windy-kartet tidligere, så usikkert», i.e. was blue on the Windy map earlier, so uncertain): `[[62.3,5.9],[62.8,6.2],[63.2,8.0],[63.55,10.0],[63.5,10.7],[63.2,10.6],[62.9,9.0],[62.5,7.2],[62.2,6.3]]`
- **TAAKE (l.1153–1156):** «Tykk tåke morgenen 23.09 fra Nord-Odal til Sør-Odal og Jessheim (lokal melding), mens Anja ikke hadde tåke. Grovt tegnet.» (Thick fog on the morning of 23.09 from Nord-Odal to Sør-Odal and Jessheim, local report, while Anja had no fog. Roughly drawn.)
  - `[[60.1,11.05],[60.08,11.4],[60.18,11.75],[60.3,11.85],[60.48,11.75],[60.5,11.4],[60.35,11.15],[60.2,11.0]]`
- **SKYDEKKE (l.1183–1191):** «Blå områder på Windy-kartet (skyer/nedbør) samme periode som Anja så klar himmel. Tegnet for hånd ut fra skjermbildet, stedfestet med byene i bildet (feil under ca. 10 km).» (Blue areas on the Windy map, clouds/precipitation, in the same period as Anja saw clear sky. Hand-drawn from the screenshot, georeferenced with the towns in the image, error under about 10 km.)
  - [0] Vestlandet, the Sørlandet coast and Trøndelag: `[[63.685,7.743],[63.766,9.107],[63.966,10.32],[64.119,11.305],[63.953,11.835],[63.618,11.532],[63.347,10.926],[63.074,10.244],[62.833,9.789],[62.449,9.531],[62.061,9.486],[61.704,9.41],[61.379,9.183],[61.087,9.259],[60.867,9.107],[60.607,8.652],[60.533,8.046],[60.346,7.516],[60.044,7.212],[59.664,6.985],[59.279,6.864],[58.889,6.833],[58.574,7.137],[58.336,7.591],[58.177,7.819],[58.017,7.288],[58.257,6.379],[58.653,5.621],[59.356,4.863],[60.421,4.56],[61.452,4.636],[62.309,5.166],[63.074,6.227],[63.483,7.137]]`
  - [1] the band from Lillehammer towards Sweden («mest usikkert», most uncertain): `[[60.94,10.092],[61.014,10.547],[61.596,11.229],[62.168,11.835],[62.729,12.366],[63.347,12.82],[63.719,12.896],[63.739,12.563],[63.005,12.108],[62.379,11.608],[61.812,11.002],[61.233,10.32],[61.051,9.941]]`
- **SKYANALYSE (l.1180–1181):** «Skyanalyse-kartet. Møtepunktet er lest av bildet, ±15 km.» (Cloud-analysis map; the meeting point is read off the image, ±15 km.) Centre 58.7, 8.27; inner radius 12 km; outer radius 45 km.
  - Hint `skyanalyse` (l.732–741, [C-int], *usikker*) says it points to inner Agder (Birkenes/Froland). Magnus counters: «Derfra er det bare ca. 4 t å kjøre fra Oslo, som strider mot 7 t i bilen. Ikke bekreftet.» (From there it is only about a 4 h drive from Oslo, which conflicts with 7 h in the car. Not confirmed.)
  - Froland was later excluded on weather.

---

## 5. TIKTOK_2509: Alf on Horde's TikTok live, 25.09 (lines 1626–1636)

These are relayed in the chat and «ikke sjekket ordrett» (not checked verbatim). Class: [P organizer], second-hand.

| Quote (verbatim) | magnus's meaning (`betyr`, verbatim) |
|---|---|
| «Det er ekte lyd på streamen. Men dere husker kanskje tidligere år, da drev vi å trollet litt med lyden.» (The sound on the stream is real. But you may remember earlier years, when we trolled a bit with the sound.) | «Lyden er ekte, men kan være tatt opp og spilt av på nytt. default.no fant lydbiter som gjentar seg.» |
| Er lyden live eller forsinket? «Ja, det må du prøve å finne ut av.» (med et smil) (Is the sound live or delayed? "Yes, you'll have to try to find that out." With a smile.) | «Han vil ikke si det. Vær forsiktig med å bruke lyd til å finne stedet.» |
| «Har reven og anda noe med hint å gjøre? Ja, kanskje.» (Do the fox and the duck have anything to do with hints? Yes, maybe.) | «Dyrene kan være hint: ekorn, stokkand, rev, orrfugl og grevling/vaskebjørn.» |
| «Kan være at noen av kodene allerede har kommet.» (Some of the codes may already have come.) | «Noen koder kan allerede være kjent, for eksempel 5008 fra appen og 0810/0891 fra Horde AI.» |
| «Kommer en del viktige hint nå i løpet av helgen.» (A number of important hints are coming this weekend.) | «Følg med på streamen, appen og TikTok i helgen.» |
| Det blir kø hvis flere kommer samtidig, og 5 timers karantene hvis du ikke får åpnet kodene. (Queue if several arrive together; 5 hours' quarantine if you cannot open the codes.) | «Ha kodene klare før du drar. Prøv de sikreste først.» |
| Man må kanskje gå litt, men aldri noe farlig, som å krysse en elv. (You may have to walk a bit, but never anything dangerous, like crossing a river.) | «Veien til kassen er trygg. Ser den farlig ut, er det feil vei.» |
| Husk at det er jaktsesong, og gå i tydelige klær. (Remember it is hunting season; wear visible clothing.) | «Gå med synlige klær, gjerne oransje, og vis hensyn der det jaktes.» |

---

## 6. SISTE_NYTT news feed as a timeline (lines 1470–1624)

The file stores this newest first. It is rewritten here oldest first.
- **"Stated time"** is the `tid` field. It is ambiguous whether it is stream time or true time; for board events it is usually the stream clock.
- **"Added"** is the commit time (CEST) at which the entry's current wording first appeared in git (`git log -S`). Wording may have been revised, so an earlier version can exist.
- Title and text are verbatim.

| # | Stated time | Added (commit) | Title (verbatim) | Text (verbatim) | hint link | Class |
|---|---|---|---|---|---|---|
| 1 | 23.09 kl. 15:30 | 23.09 15:57 (90f20c3) | Ny Horde-video med nye tall og bokstaver på genseren | «Horde har lagt ut «Hvordan går det med Anja?». Genseren viser nå «+5» på ryggen, sammen med tallene og bokstavene. Horde skriver selv: «Kjenner jeg dere riktig så vil dere overanalysere denne videoen».» Link: https://www.youtube.com/shorts/1raIm3ANsAI | pluss5 | [P organizer media] |
| 2 | 23.09 kveld (evening) | 23.09 17:56 (aa81ebf) | Mange leter nå ved Rudshøgda (Prøysen-teorien) | «Rev, kråke og ekorn er alle med i Prøysens «Sirkus Mikkelikski», og bak Prøysenstua står den 27 m høye Prøysenstjerna. Flyet NOZ9EG gikk ca. 6–11 km unna kl. 21:31. Se «Prøysen-teorien» under Hint.» | rudshogda | [C-int]. [V] NOZ9EG's closest approach to Prøysenstua is **3.2 km**, not 6–11 km. |
| 3 | 23.09 kl. 17:49 | 23.09 18:01 (df596d3) | Ny tavle: «LYDTETT · SOL · VINDSTILLE» | «Kassen er lydtett, så hun hører lite utenfra. Det var sol og vindstille kl. 17:49. Sammenlign med værstasjoner i kandidatområdene.» | lydtett | [P whiteboard] |
| 4 | 23.09 kveld | 23.09 18:02 (c4c0aa3) | Døra har en elektronisk lås med 5 siffer | «Det er 3 låser: 2 hengelåser med 4 siffer på pengeboksen, og 1 elektronisk lås med 5 siffer på døra for å slippe ut Anja. Kodejakten gir koden til én av hengelåsene. Se «Mest sannsynlige koder» under Hint.» | koder | [P whiteboard] plus [P organizer page] |
| 5 | 23.09 | 23.09 18:17 (b7a2c7f) | Kodejakten er ikke aktiv ennå | «Vi sjekket API-et: serveren som gir koden svarer «not_configured» (503) på alle kall. Kodejakten-spillene laster, men ingen kan få en kode fra dem før Horde skrur på serveren.» | kodejakten | [C-obs] |
| 6 | 23.09 kveld | 23.09 19:01 (4a9f3ee) | Nye tavler: «Typisk fjellmark», masse sopp, ikke vann | «Anja skrev «TYPISK FJELLMARK», «MASSE SOPP», «MOSE PÅ STEINER», «IKKE VANN», ca. 16 grader og «GIKK 2 MIN INN I SKOGEN». Fjellmark peker mot høyereliggende områder, som Ringsakfjellet/Sjusjøen og åsene over Rena og Løten.» | fjellmark | [P whiteboard] plus [C-int] |
| 7 | 23.09 kl. 19:09 | 23.09 19:12 (89d7dc0) | Ny tavle: «Lite med fly her · sikkert med vilt» | «Få fly der kassen står, altså ikke under lavtflygende ruter til Gardermoen. Og trolig mye vilt, som passer med jaktskog.» | litefly | [P whiteboard]. Photo: `tavle-1909-fly-vilt.jpg` |
| 8 | 23.09 kl. 19:12 | 23.09 19:15 (405c497) | Horde-skiltet er fjernet | «Anja skrev «SKILTET ER BORTE, VET IKKE HVOR». Skiltet som pekte 118–120° er tatt bort. Retningen vi målte før gjelder fortsatt.» | skiltborte | [P whiteboard]. Photo: `tavle-1912-skilt-borte.jpg` |
| 9 | 23.09 kveld | 23.09 19:13 (b55eafc) | Utelukkingskart: Hamar–Løten–Rena–Koppang, Ringsakfjellet og Gjøvik står igjen | «Fellesskapet har utelukket områder med fjellbjørk (lyseblått). Solør, Finnskogen, Trysil og Elverum sentrum er ute. Nytt kartlag «Utelukket av fellesskapet» er på som standard.» | utelukkingskart | [C-int]. Same commit removed the pink "ingen sopp" layer as «not correct». Hint `utelukkingskart` gives "open" shares: Rudshøgda 100 %, Gjøvik 95 %, Rena 93 %, Ringsaker 83 %, Løten 77 %. |
| 10 | 23.09 kl. 22:27 | 24.09 19:55 (893318a) | Ikke bekreftet: skjermbilde viser at FROLAND gir «Ekornet kan klatre» | «Et skjermbilde delt i chatten viser dette, men vi har ikke bekreftet det selv. Froland er fortsatt utelukket på grunn av været.» | frolandekorn | unverified app screenshot |
| 11 | 24.09 kl. 00:01 | 24.09 18:26 (addc834) | Ikke bekreftet: skjermbilde viser at LD6788 gir «ENKODE» | «Legg til kjøretøy LD6788 under «Bil & hus» i appen, så kommer «Du fant et hint! ENKODE». Kan bety at 6788 er en kode til en hengelås. Lagt til som kodekandidat.» | enkode | unverified app screenshot |
| 12 | 24.09 kl. 11:05 | 24.09 18:49 (4d069c1) | Anja sa det regnet, og da regnet det i Rena | «Regn hos Anja kl. 11:05 stemmer med regn i Rena samtidig, ifølge fellesskapet. Styrker Rena og Åmot litt.» | regn1105 | [P] (Anja said it) plus [C-obs] (weather); not checked against radar |
| 13 | 24.09 kl. 17:54 | 24.09 18:30 (7ebb743) | HORDEMINUS løst: «2,7 eiffeltårn stablet oppå hverandre» = 810 eller 891 m | «Horde AI i appen svarer dette på «Hordeminus». Eiffeltårnet er 300 m uten antenne og 330 m med, så 2,7 tårn er 810 eller 891 m. Trolig høyden over havet der kassen står. Nye kartlag viser steder i den høyden nær vei, og fellesskapets 800–900 moh-kart.» | eiffel | [P app] plus [C-int] (the altitude reading) |
| 14 | 24.09 kveld | 24.09 18:32 (b03c6a9) | Horde: hint til kodene ligger i appen | «Horde svarte i kommentarfeltet: «Hint til hva kodene kan være ligger i appen». Det styrker 5008, 6788 og 0891/0810. Se Hint-fanen for alle koder.» | kodeniappen | [P organizer] |
| 15 | 24.09 | 24.09 18:33 (4bd3590) | Anja: «Hjelper veldig at jeg kan se det dere skriver <3» | «Hun kan lese det chatten skriver. Spørsmål i chatten kan altså nå henne, og svarene kommer på tavla. Tidligere tavler: «INGEN PIZZA ENDA».» | — | [P whiteboard] |
| 16 | 24.09 | 24.09 18:34 (c0b1da8) | Pizzaen kom: «Hjemmelaget pepperonipizza, dressing fra Coop, knallgodt» | «Maten er handlet på Coop. Det sier lite alene, for Coop finnes nesten overalt i Innlandet, men det passer med en Coop-butikk innen kort kjøring fra kassen. Nye tavler i dag: «Ingen pizza enda», «Hjelper veldig at jeg kan se det dere skriver», «Skal klare å holde ut til noen finner meg».» | — | [P whiteboard] plus [C-int] |
| 17 | 24.09 kveld | 24.09 18:35 (4e65b1c) | «Kom fra den veien ←» og «ingen stier»: bilen står trolig sørøst for kassen | «Pila peker mot venstre i bildet, som er ca. 130° siden kameraet filmer mot 221°. Fra bilen går man altså mot nordvest og oppover, uten sti. Søkesektoren fra parkering er snudd. Også nytt: «Ingen hytte i nærheten som jeg vet om eller ser».» | komfra | [P whiteboard] plus [C-int] (azimuth mapping). This reversed the earlier reading that the box lay towards 120° from the car. |
| 18 | 24.09 kveld | 24.09 18:38 (679260b) | Spor: topp på ca. 891 moh ved Kroktjennet i Hemmeldalen (Åmot) | «Vest for Rena, inne i det røde området på fellesskapets 800–900 moh-kart. Hemmeldalen-setrene ligger sørøst for toppen, som passer med «kom fra den veien ←». Men toppen ligger inne i Hemmeldalen naturreservat og er åpent område, ikke skog. Se markøren på kartet.» | eiffel | [C-int] |
| 19 | 24.09 kveld | 24.09 18:43 (a269415) | «Det har vært hogd der jeg gikk» med pil →: hun gikk gjennom et gammelt hogstfelt | «Pila peker mot høyre i bildet (ca. 310°, nordvest). Det passer med «kom fra den veien ←» (ca. 130°): fra bilen i sørøst, gjennom et gammelt hogstfelt, mot nordvest og oppover til kassen. Hun så ingenting uvanlig på veien.» | hogst | [P whiteboard] plus [C-int]. mk_bevis marks the «…DER JEG GIKK I GÅR» wording as [ikke verifisert] (not verified). |
| 20 | 25.09 | 25.09 10:59 (970c493) | Alf på TikTok-live: «Det er ekte lyd på streamen» og «viktige hint i helgen» | «Alf sa også at reven og anda «kanskje» har med hint å gjøre, og at «noen av kodene kan allerede ha kommet». Gjengitt i chatten, ikke sjekket ordrett. Lyden var tidligere regnet som loop, så det er nå usikkert.» | tiktok2509 | [P organizer], second-hand |
| 21 | 25.09 | 25.09 11:00 (10c2793) | Dyrehintene: ekorn, stokkand, rev, orrfugl og grevling (eller vaskebjørn) | «Nytt: orrfuglleik-lyd når man rister appen, og en utstoppet grevling i Horde Rewards. Orrfuglen leker ofte på myrer i høyden, som passer med 810–891 moh.» | dyreoversikt | [P app] plus [C-int] |
| 22 | 25.09 | 25.09 11:02 (ddf93d0); revised 14:12 | Discord: mange tipper Finnskogen, flere Ringsaker–Rena | «Finnskogen er for lav for 810–891 moh og er utelukket på fellesskapets kart. Den er lagt på kartet under «Hva folk tror».» | — | [C-int]. Originally also named Birkebeinervegen; removed 25.09 14:12. |
| 23 | 25.09 | 25.09 17:49 (f965b2f) | Streamen er fryst: tekniske problemer, sier Horde | «Streamen står stille, men ifølge Horde er det bare tekniske problemer. Anja er fortsatt i boksen, og det er ikke et hint.» | — | [P organizer], second-hand; time of the freeze not given |
| 24 | 25.09 | 25.09 17:49 (1dfb536) | ⚠️ ADVARSEL: 11 elgpåkjørsler siste timen i Elverum-området | «Meldt i chatten: 11 elgpåkjørsler på én time rundt Elverum. Elgjakta er i gang, og elgen er urolig og krysser veiene. Kjør sakte, særlig i skumringen og i mørket, og se etter elg langs veikanten. Pass på dere som leter!» | — | chat report, unverified (a safety note, not location evidence) |
| 25 | 25.09 kl. 17:22 | 25.09 18:02 (9a7359b) | Hun pekte opp mot himmelen: SAS50J over Stange mot Løten | «Ifølge ADS-B var SAS50J over østre Stange, nær Romedal og Løten, på ca. 22 000 fot da hun pekte. SAS364 var på vei nordover over Rena. Begge følger samme linje nordover fra Gardermoen som flyet 21.09. Sporet er på kartet.» | fly2509 | [P stream] (the gesture) plus [C-obs] (ADS-B match). See §7. |
| 26 | 25.09 | 25.09 18:44 (72f623a); revised 18:46 (971c9d6) | Tavla: «THILPRTE OESHF» = THE SHOPLIFTER eller FILTER THE SHOP? | «Bokstavene går nøyaktig opp i både THE SHOPLIFTER og FILTER THE SHOP. Oppdatering: butikken i Horde-appen har ikke noe filter, så THE SHOPLIFTER er trolig den riktige lesningen. På samme tavle: «NOEN SOM VET FASITEN». Enten spør hun om noen kan løse det, eller så sier hun at BobTheShoplifter (som har laget default.no) vet fasiten. Takk til ham for all dataen!» | shoplifter | [P whiteboard] plus [C-int] |

Notes on entry 26 (THILPRTE OESHF):
- I viewed `tavle-2509-shoplifter.jpg`. It shows «THILPRTE» / «OESHF» with a bracket. «NOEN SOM VET FASITEN» is **not visible in this crop**, so that part is unverified from the mirror.
- Hint `shoplifter` adds a third anagram, «HELHET FOR TIPS» (Norwegian, "wholeness for tips").
- It says the letters come from balloons in a Horde video, recorded by default.no (https://default.no/cuts/202609251620_202609251703.mp4).
- Balloon colours per the hint: green E, P, T · purple E · blue F · yellow H, H, I, R, S, T · pink L, O. These are unsolved.

---

## 7. FLY_2509: the SAS50J track on 25.09 (lines 1638–1642)

Comment (verbatim): `/** SAS50J (A320neo, OSL nordover) 25.09 kl. 17:17–17:27, ekte tid. Anja pekte opp kl. 17:22 streamtid. Kilde: ADS-B fra adsb.lol. */` (SAS50J, A320neo, Oslo northbound, 25.09 17:17–17:27 real time; Anja pointed up at 17:22 stream time; source ADS-B from adsb.lol.)

Full track `[time, lat, lon, ft]`:
```
17:17:00 60.1448 11.3412 10175 | 17:17:03 60.1476 11.3419 10275 | 17:17:20 60.1726 11.3489 10775 | 17:17:23 60.1757 11.3498 10825
17:17:42 60.2048 11.3586 11650 | 17:18:02 60.2350 11.3683 12600 | 17:18:43 60.2993 11.3875 14525 | 17:19:02 60.3301 11.4005 15350
17:19:23 60.3644 11.4239 16425 | 17:20:21 60.4597 11.4892 18975 | 17:21:03 60.5292 11.5304 20825 | 17:21:21 60.5610 11.5341 21525
17:22:41 60.7043 11.5471 24100 | 17:23:03 60.7439 11.5507 24750 | 17:25:20 61.0070 11.5747 28550 | 17:26:42 61.1689 11.5894 30300
```

Hint `fly2509` (l.242–252), status *bekreftet* (confirmed), source «Stream + ADS-B fra adsb.lol»:
- «Anja pekte opp mot himmelen kl. 17:22 (streamtid). Da, rundt 17:21–17:22 ekte tid, var SAS50J (Oslo → nord) over østre Stange mot Romedal og Løten, på 21 000–23 000 fot. På Flightradar24 var også SAS364 på vei nordover over Rena.» (Anja pointed at the sky at 17:22 stream time. Around 17:21–17:22 true time, SAS50J was over eastern Stange towards Romedal and Løten at 21 000–23 000 ft. On Flightradar24, SAS364 was also heading north over Rena.)
- Meaning: «Andre gang hun peker på et fly … SAS50J var ca. 23 km øst for sporet til NOZ56U fra 21.09. Kassen ligger trolig et sted mellom eller langs disse sporene, i skogen øst og nord for Hamar.» (The second time she points at a plane … SAS50J was about 23 km east of the 21.09 NOZ56U track. The box is probably somewhere between or along these tracks, in the forest east and north of Hamar.)

[V] SAS50J position at stream 17:22:00, depending on the delay:

| Delay | True time | Position | Altitude |
|---|---|---|---|
| 0 s | 17:22:00 | 60.6309, 11.5404 | 22 780 ft |
| 22 s | 17:21:38 | 60.5915, 11.5369 | 22 072 ft |
| 45 s | 17:21:15 | 60.5504, 11.5329 | 21 292 ft |

- The hint position (60.59, 11.536) corresponds to about a 22 s delay.
- The lateral offset from the 21.09 NOZ56U track is about **17–19 km**, not 23 km (it is 17.1 km at 60.87° N and about 18.7 km at 60.59° N).

Elevation of SAS50J at 22 s delay, seen from candidates (assumed ground heights):

| Elevation | Places |
|---|---|
| High (≥ 15°) | Smerud 23° (15 km), Flisa/Haslemoen 18° (20 km), Benningstad 16° (22 km) |
| 8–11° | DN#1 Hamar øst 9°, Hamar–Løten 10°, Disen 11° |
| 4–5° | Digeråsen 5° (67 km), Jomfrua 4° (79 km), Rena–Evenstad 3° (99 km), Kroktjennet 4° |

So a gesture at SAS50J "overhead" would favour the Stange-east / Våler / Åsnes (Solør) side. That contradicts the community exclusion of Solør. It would not favour Ringsakfjellet or Rena.

Caveats:
- (i) On 25.09 Anja wrote «OVERSKYET · FLYENE ER SÅ LANGT UNNA AT DET ER UMULIG Å SE PÅ DAGEN, OG PÅ NATTA DERSOM DET IKKE ER HELT STJERNEKLART» (overcast; the planes are so far away that it is impossible to see them by day, and at night unless it is completely starry) (l.1002; photo `tavle-2509-overskyet.jpg`). A daytime pointing gesture at 17:22 may therefore not be at a plane at all.
- (ii) FLY_2509 is labelled "ekte tid" (true time). If it was taken from the same default.no-derived pipeline as fly_2130.json, it could carry the same approximately 45 s offset (about 4–5 km along track). It cannot be checked here: the adsb.lol raw trace for SAS50J is not in any local mirror.
- (iii) The two Flightradar24 screenshots (`fr24-2509-sas50j.jpg`, `fr24-2509-sas364.jpg`, both viewed) carry **no timestamps**. In the SAS364 screenshot the aircraft is already north of Rena.

---

## 8. The two 21.09 flights and the pointing gesture (context for many place claims)

**Primary:**
- TAVLE l.894 `21.09 21:30` «FLY (pekte opp, litt mot sørøst)» ("PLANE", pointed up, slightly towards the south-east).
- Hint `fly` (l.743–752): «Anja pekte rett opp kl. 21:29:38 og skrev «FLY» kl. 21:30 (streamtid).» (Anja pointed straight up at 21:29:38 and wrote "FLY" at 21:30, stream time.)

**Community match:**
- NOZ56U (B738, LN-ENN, hex 47a3b0), northbound over Hamar near Løten.
- NOZ9EG (B738, LN-NIQ, hex 4791ac), southbound over Ringsakfjellet/Sjusjøen.

**Ambiguity (mk_bevis README, citing default.no osint_notes):** «kl. 21:27:42 signaliserte hun et stjerneskudd, og kl. 21:29:10 ba chatten henne peke dit. Pekingen 21:29:38–53 kan altså gjelde stjerneskuddet og ikke et fly.» (At 21:27:42 she signalled a shooting star, and at 21:29:10 the chat asked her to point at it. The pointing at 21:29:38–53 may therefore concern the shooting star and not a plane.)

[V] Plane geometry at stream 21:29:38, from the **raw** adsb.lol trace (geometric altitude, 4/3-earth refraction, candidate ground height assumed). Each cell gives NOZ56U, then NOZ9EG, as distance / elevation.

| Place | 0 s delay | 22 s delay | 45 s delay | Max elevation, 21:28:30–21:35 true time |
|---|---|---|---|---|
| Jomfrua (1015 m) | 53 km/6° · 4 km/56° | 57/5° · 10/35° | 61/4° · 16/24° | NOZ9EG 85° at 21:29:56 |
| Kroktjennet 891 | 53/6° · 7/46° | 57/5° · 10/34° | 61/4° · 15/25° | NOZ9EG 48° at 21:29:48 |
| Tommsen B / Gålaveien | 79/4° · 23/17° | 83/4° · 18/23° | 87/3° · 12/33° | NOZ9EG 52° at 21:28:30 |
| Rena–Evenstad | 76/5° · 23/18° | 79/4° · 18/23° | 84/4° · 14/30° | NOZ9EG ≥ 38° (edge of window) |
| DN#3 Koppang | 82/4° · 26/15° | 86/4° · 21/20° | 90/3° · 15/27° | NOZ9EG ≥ 39° |
| Madsskardveien | 78/4° · 25/16° | 82/4° · 20/20° | 86/3° · 15/26° | — |
| DN#2 Rena/Åsta | 59/6° · 16/24° | 62/5° · 16/25° | 67/5° · 17/24° | NOZ56U 53° at 21:34:39 |
| Tommsen A | 40/9° · 18/21° | 43/7° · 23/17° | 47/6° · 29/15° | — |
| Digeråsen | 45/8° · 22/18° | 49/6° · 25/16° | 53/5° · 29/15° | NOZ56U 74° at 21:33:32 |
| Hamar–Løten (60.87, 11.25) | 11/31° · 48/9° | 15/22° · 53/8° | 19/17° · 59/8° | NOZ56U 89° at 21:30:36 |
| DN#1 Hamar øst | 14/24° · 44/9° | 18/18° · 49/9° | 22/14° · 55/8° | NOZ56U 68° at 21:30:53 |
| Benningstad | 7/42° · 61/7° | 8/37° · 66/6° | 11/27° · 71/6° | NOZ56U 42° at 21:29:41 |
| Disen | 9/37° · 53/8° | 10/31° · 58/7° | 13/23° · 64/7° | — |
| Brumunddal | 20/18° · 43/10° | 22/15° · 48/9° | 25/13° · 54/8° | NOZ9EG 50° at 21:32:35 |
| Tretopphyttene | 28/12° · 33/12° | 31/10° · 38/11° | 34/9° · 44/10° | NOZ9EG 69° at 21:31:53 |
| Prøysenstua | 28/13° · 40/10° | 30/11° · 45/9° | 32/10° · 51/9° | NOZ9EG 59° at 21:32:25 |
| Flisa/Haslemoen | 37/10° · 86/5° | 36/9° · 90/5° | 36/9° · 95/5° | ≤ 10° |
| Texas / Kompassen | 55–60/6° · 83–88/5° | similar | similar | ≤ 9° |
| Finnskogen, Tolvmilskogen, Kirkesjøvegen, Trysil, Nittedalen, Tommsen C | all ≤ 6° | | | |

Plane positions at the pointing moment:

| Delay | NOZ56U | NOZ9EG |
|---|---|---|
| 0 s | 60.775, 11.229 (21 967 ft geom) | 61.267, 10.900 (25 067 ft) |
| 22 s | 60.739, 11.222 (20 655 ft) | 61.317, 10.904 (25 920 ft) |
| 45 s | 60.702, 11.214 (19 343 ft) | 61.370, 10.908 (26 846 ft) |

Reading:
- At the plausible 22 s delay, **no candidate** has either plane near the zenith. The highest are Jomfrua / Kroktjennet / Benningstad at 34–37°, and Hamar–Løten and Disen at 22–31°.
- This agrees with mk_bevis: «Ingen kandidat har et fly i nærheten av «rett opp» i det øyeblikket hun peker.» (No candidate has a plane anywhere near "straight up" at the moment she points.)
- "Litt mot sørøst" (slightly south-east) with a camera facing 221° is additional directional information. It is not used anywhere in the magnus place texts.

---

## 9. Verification of magnus's numeric place claims [V]

Scripts are in the session scratchpad:
- `verify_pc.py` (the fly_2130 base);
- `raw_elev.py` (the raw adsb.lol base);
- `sas50j.py`.

Counts of `hoyde891.json` cells use cells `[lat, lon, z, road_dist_m, road_to_SE_flag]`. The layer contains 17 234 cells with z 790–911 m and road distance 0–900 m.

| Claim (location in file) | Result |
|---|---|
| Kompassen «5,5 km rett øst (92°)» from Texas (l.1071) | **OK**: 5.54 km, 91.9° |
| Digeråsen DMS = decimal (l.1086) | **OK**: 61.17883, 11.26392 |
| Digeråsen «45 km … 8°» at pointing, «74°» at 21:32:50 (l.1086) | **OK in the fly_2130 base**: 44.8 km / 7.6°; 73° at 2.6 km. In the raw base this equals 0 s delay; the 74° maximum is at 21:33:32 true time. |
| Benningstad «ca. 10 km» from NOZ56U at 21:28 (l.1093) | roughly: 7.0 km at 21:28:53 (label base); 12.8 km from FLY_PUNKT |
| Bennyøy «3,4 km fra 118°-linja fra Horde» (l.1100) | **OK** as a great circle (3.2 km). The rhumb line gives 10.5 km. |
| Tretopp «NOZ56U ca. 21 km (19°) da Anja pekte opp» (l.1107) | **Not at the pointing time**: 27.8 km / 12° at the 21:28:53 label. 21 km corresponds to FLY_PUNKT (the 21:29:50 label, when she wrote "FLY"). |
| Haslemoen «ca. 40 km (10°)» (l.1114) | OK: 37 km / 9° |
| Nittedalen «58 km fra begge flyene» (l.1121) | **Does not reproduce**: 92 km from FLY_PUNKT, 128 km from FLY_PUNKT2 |
| Prøysen «NOZ9EG … ca. 6–11 km unna kl. 21:31» (l.1614, hint `rudshogda`) | **Does not reproduce**: closest approach 3.2 km (label 21:31:39) |
| Brumunddal «9 km fra sporet til NOZ9EG» (l.1280) | **Does not reproduce**: 4.5 km |
| Jomfrua «9,5 km fra flyet NOZ9EG» (l.1261) | Reproduces only with the raw trace at about 22 s delay (10 km). The track passes 0.6 km from Jomfrua (FLY_PUNKT2 is 1.5 km away). |
| SAS50J «ca. 23 km øst for sporet til NOZ56U» (l.249) | **Overstated**: 17–19 km |
| Jomfrua «20 steder på 810–891 moh nær vei innen 3 km» | **OK**: 20 (12 with road to SE) |
| Bobbane «148 steder … innen 10 km» | **OK**: 148 (116 to SE) |
| Brauta «37 steder … innen 5 km, de fleste med vei mot sørøst» | **OK**: 37 (35 to SE) |
| Brumunddal «ingen … innen 20 km» | **OK**: nearest 23.6 km |
| Tommsen A «nærmeste … 4,5 km» | **OK**: 4.58 km |
| Tommsen B «nærmeste treff 2,7 km» | **OK**: 2.68 km |
| NOZ9EG «ca. 3 km fra Tretopphyttene kl. 21:31» (hint `fly`) | OK for Utsiktsredet (2.2 km). Himmelhytta and Bjørkhytta are 0.1–0.3 km. |

**Time-base finding (important).** `public/data/fly_2130.json` is labelled «ADS-B fra adsb.lol, hentet ut av default.no (event_planes.json)», «ekte tid 21.09, CEST». Compared with the raw adsb.lol `trace_full` files (mk_bevis, decoded to Europe/Oslo), each fly_2130 position is reached about 45 s **later** than its label:

| Flight | fly_2130 label | Position | Raw trace time | Offset |
|---|---|---|---|---|
| NOZ56U | 21:28:14 | 60.7137 | ≈ 21:28:58 | 44 s |
| NOZ56U | 21:29:48 | 60.8671 | ≈ 21:30:34 | 46 s |
| NOZ56U | 21:32:50 | 61.1823 | ≈ 21:33:35 | 45 s |
| NOZ9EG | 21:28:14 | 61.3538 | ≈ 21:29:00 | 46 s |
| NOZ9EG | 21:31:16 | 60.9573 | ≈ 21:32:01 | 45 s |

Altitudes in fly_2130 match barometric altitude, not geometric.

Magnus computes the "pointing moment" as 21:29:38 − 45 s = 21:28:53 and looks it up in this file, so the two shifts cancel. The magnus pointing-moment geometry is therefore equivalent to **zero stream delay**. This is a [V] finding, not a primary fact. The raw trace timestamps are adsb.lol receive times, and I assume they are correct to about 1 s.

---

## 10. Retractions and corrections (git history of `innhold.ts`)

| When (CEST) | Commit | Change |
|---|---|---|
| 23.09 15:17 | 2eb6f94 | Sign direction updated to 118–120° «per Anja» |
| 23.09 15:46 | 6cddb71 | Froland ruled out: «the weather does not match» |
| 23.09 19:13 | b55eafc | Pink "no mushrooms" exclusion removed: «was not correct» |
| 23.09 20:09 | 602389f | Dart calculator removed; live Kodejakten status check added |
| 24.09 (hint `komfra`) | — | «Merk at dette snur den gamle tolkningen, der kassen lå mot 120° fra bilen» (note that this reverses the old reading, in which the box lay towards 120° from the car). The parking-sector direction was flipped to about 300°. |
| 24.09 19:59 | a141dae | Place names corrected against Kartverket. NOZ56U was «over Hamar (near the Løten border) at 21:29, not over Løten». The "Rena og Åmot" theory was renamed «Rena–Evenstad» (Stor-Elvdal). Bjørneparken moved 1.2 km. |
| 25.09 11:01 | 67eb8d0 | Horde Rewards animal changed from "badger" to «may be Haaland's stuffed raccoon from Texas» |
| 25.09 11:16 | 094b3b8 | **Fake item removed**: «Folk skal være ved kassen og prøve koder» (people are supposed to be at the box trying codes), a chat quote. The queue/quarantine rule moved into SIKRE_FAKTA. |
| 25.09 13:01 | 2f86bbf | Terje T-shirt «is not new»; the news item was dropped |
| 25.09 14:12 | e431102 | **All Birkebeinervegen content removed**: tip, news, theory, terrain pin, default.no search stops and field notes. No reason given. |
| 25.09 14:56 | 337ddc2 | Horde AI «grevling» reply removed: «not repeatable in a new chat» |
| 25.09 15:47 | bb53374 | Moose-hunting fields marked unlikely; small-game and bird hunting not excluded |
| 25.09 16:06 | 889d715 | Hagina's birch observation pulls down high terrain around Ringsakfjellet/Sjusjøen |
| 25.09 18:46 | 971c9d6 | «FILTER THE SHOP is weaker: the shop in the Horde app has no filter» |
| 25.09 20:53 | 6c421a9 | Board 22.09 19:19 added: «IKKE MØRKT ENDA · INGEN VANN ELLER VANNLYDER, FØLER IKKE DET ER VANN I NOE NÆRHET» (not dark yet; no water or water sounds, don't feel there is water anywhere near). The riverbank idea was dropped. |

---

## 11. Contradictions

1. **Pick-up day.** The whiteboard says «OSLO, SØN KL 04.00» (Sunday 20.09). Børsen says «siden mandag morgen» (since Monday morning). If she was picked up Monday at 04:00, the drive was under about 3 h, because the stream started at 06:50 (hint `reise`).
2. **Door lock digits.** 23.09: «ELEKTRONISK LÅS PÅ DØRA MED 5 SIFFER». 24.09: «1x KODELÅS 5–6 TALL · TROR 5» and «5 SIFFER · GANSKE SIKKER». These are consistent at 5, with residual doubt about 6.
3. **Too many 4-digit codes for two padlocks.** If 5008 (app), the Kodejakten code (organizer) and 6788 (ENKODE, unverified) are all padlock codes, there are three codes for two padlocks. At least one assumption is wrong, or one code feeds the door.
4. **Pointing-moment geometry.** Magnus uses the fly_2130 label base; the raw ADS-B shows about a 45 s shift. As a result:
   - the Digeråsen, Benningstad and Hamar–Løten "under the plane" claims correspond to 0 s delay;
   - the Jomfrua "9.5 km" claim corresponds to about 22 s delay on the raw base;
   - the Tretopp "21 km / 19°" claim uses the "FLY" writing time, not the pointing time.
5. **Several distance claims do not reproduce:** Prøysen 6–11 km (actual 3.2), Brumunddal 9 km (actual 4.5), Nittedalen 58 km, and SAS50J 23 km east (actual 17–19).
6. **"810–891 moh" (the altitude reading of 2,7 eiffeltårn) against field evidence.** Hagina saw orange, thin birch at about 510 m between Hamar, Lillehammer and Sjusjøen, while the stream shows yellow, full birch. Anja writes «TYPISK FJELLMARK» (typical mountain terrain). The Jomfrua peaks are 1010–1026 m and open. Kroktjennet 891 is open, in a nature reserve, and has no road within 900 m.
7. **Solør and Finnskogen.** They are excluded on the community map and are too low for 810–891 m. Yet the 25.09 SAS50J gesture, taken at face value, favours Stange-east / Solør (Smerud 23°, Haslemoen 18°). Many on Discord also tip Finnskogen.
8. **Sign.** «SKILTET ER BORTE, VET IKKE HVOR» (the sign is gone, don't know where) on 23.09 19:12. But a wooden «HORDE» arrow sign appears to the right of the box in video from 25.09 16:20–17:03 (hint `skilt-tilbake`, *usikker*).
9. **THILPRTE OESHF.** The magnus TAVLE says the same board had «NOEN SOM VET FASITEN», but the mirrored photo crop shows only the anagram.
10. **Sound.** default.no found audio snippets repeating 22–48 h apart, which suggests a loop. Alf says «Det er ekte lyd på streamen» (the sound is real) but will not say whether it is live.
11. **DEFAULTNO list staleness.** The file has the 22.09/23.09 ranking (#1 Hamar øst/Løten). The mirrored default.no `steder.json` of 24.09 18:06 has #1 Rena–Evenstad (61.45, 11.1), p = 0.127.
12. **Letter count.** BOKSTAV_LESNINGER says NORDHUE + MIS «bruker 7 av bokstavene» (uses 7 of the letters), but NORDHUE + MIS uses all ten.

## 12. Open questions

- Has the Kodejakten server been enabled since 23.09? If so, what is the padlock code? Alf promised «viktige hint i løpet av helgen» (important hints over the weekend) on 26–27.09.
- What is the 5-digit door code? Is it derived from 5008, 891/810, 6788 or "+5", or will it be released separately?
- Can the LD6788 → «ENKODE» and FROLAND → «Ekornet kan klatre» screenshots be reproduced in the app? The Horde AI "grevling" reply was retracted after it failed a fresh-chat test; the same test should be applied here.
- Where does the 5-digit backup candidate "07250" come from? It is undocumented.
- Which delay applies to the 21.09 21:29:38 gesture: 22 s (default.no) or 45 s (magnus constant)? Was the gesture at a plane or at a shooting star?
- Does FLY_2509 (SAS50J, 25.09) carry the same approximately 45 s time-base offset as fly_2130.json? Was Anja's 17:22 gesture on an overcast day at a plane at all?
- Why was all Birkebeinervegen material (61.4495, 10.9752 and 61.36168, 10.84625) removed on 25.09 14:12?
- Is the approximately 891 m altitude a location constraint, a distance, or a code? The Horde AI itself says the phrase is just the one it was told to use.
- Does the one open hand (25.09) in front of the box encode a digit (5?), with more hands to come?
- What do the balloon colours of THILPRTE OESHF mean?
