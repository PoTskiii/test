# Hints A: HINT array, first half (innhold.ts lines 1–479)

**Source file:** `/home/user/test/data/raw/magnus/src/data/innhold.ts` (MagnusPladsen/hordejakten-2026 community map, local mirror, read-only)
**Mirror HEAD:** `68faa86` (2026-09-25 21:04 CEST). The last commit that touched `innhold.ts` is `6c421a9` (25.09 20:53 CEST). The file has had 107 commits since `c0c849b` (23.09 14:30).
**Scope:** File header and types (L1–45), then all 44 `HINT` entries that start between L46 and L470. The last one (`lydtett`) starts on L470 and runs to L479, so it is included whole.
**Written:** 2026-09-25 (evening), for the Hordejakten 2026 evidence base.
**Method:**
1. I read every line of L1–479.
2. For each hint I traced its revision history with `git log -L` to find retractions and silent edits. I also searched the whole file history for hints that were deleted.
3. Where the repo holds the whiteboard or stream photos (`public/img/`), I looked at them to check the quoted primary text.
4. I recomputed the distance and geometry claims with pyproj (WGS84 geodesics), using `public/data/fly_2130.json`, `vind.json` and `hoyde891.json`, plus `FLY_2509` (innhold.ts L1639–1642).
5. I cross-checked against the whiteboard log `TAVLE` (L881–1054), the places lists `STEDER`/`TEORIER` (L1065–1140), `src/data/analyse.json` (default.no audio/BirdNET extract, fetched 23.09) and `src/data/defaultno_mer.json` (default.no extract, fetched 24.09 18:36).

## 0. How to read this report

Each hint in the app has two text fields. `tekst` is presented as the evidence. `betydning` is the community author's reading of it (Magnus Pladsen, with Claude as co-author per the commit trailers). **`tekst` is not always primary evidence.** Sometimes it is itself a chat relay, a satellite reading or a default.no model output. For every hint I therefore assign my own evidence class:

| Class | Meaning |
|---|---|
| **P-WB** | Primary: Anja's whiteboard ("tavla") |
| **P-SV** | Primary: stream visual (what can be seen on the livestream) |
| **P-ORG** | Primary: organizer statement (Horde / Alf) |
| **P-APP** | Primary: Horde app or Horde AI response |
| **P-MEDIA** | Primary: organizer media (Horde videos, stories, posts) |
| **NEWS** | News interview (Børsen/Dagbladet) |
| **C-OBS** | Community observation (e.g. an ADS-B track matched to a gesture, local weather report, satellite reading) |
| **C-INT** | Community interpretation / theory |
| **MODEL** | Model output (default.no analyses, BirdNET, fusion grids) |
| **RELAY** | Unverified relay (a screenshot or quote shared in chat and not checked by the author) |

The app's own status values (L17–25): `lost` = "Løst" (solved), `bekreftet` = "Bekreftet" (confirmed), `tolkning` = "Tolkning" (interpretation), `usikker` = "Usikker" (uncertain), `apen` = "Uløst" (unsolved). **The app's `bekreftet` usually means "the whiteboard or source really says this". It does not mean the interpretation is confirmed.**

**Times.** The app states that whiteboard times are *stream time*, and that the stream is "trolig 20 sek–1 min forsinket (vi tipper)" (FAKTA L1197; TAVLE doc comment). That estimate replaced an earlier "45 sek" assumption in commit `01ab80d` (25.09 11:29). `STREAM.forsinkelseSek: 45` is still hard-coded at L10. Flight (ADS-B) times are *real time, CEST*. All dates are 2026-09.

**Image timestamps.** The night-camera frames in `public/img/` carry a yellow overlay timestamp and a "TavlAI" watermark. This is a third-party frame-capture tool. The overlay clock matches the app's "stream time" labels, e.g. 2026-09-23 19:12:22 for the "19:12" board.

**Status distribution of the 44 hints:** bekreftet 18, tolkning 11, usikker 14, lost 1, apen 0.

---

## 1. File header facts (L1–45)

- L6–11 `STREAM`: videoId `EQHgfmZicc8`, url `https://www.youtube.com/watch?v=EQHgfmZicc8`, chat popout url, `forsinkelseSek: 45`. The 45 s value is stale; the prose elsewhere says "20 sek–1 min (vi tipper)".
- L13 `OSLO = [59.9139, 10.7522]`.
- L14–15 `BERGEN = [60.3896, 5.3297]`, comment "Horde AS, Lars Hilles gate 20A, 5008 Bergen".
- L17–25: status taxonomy (see above).
- L27–44 `Hint` type: `id, tittel, status, kilde, dato?, tekst, betydning, lag?` (map layers switched on by "Vis på kartet"), `fokus?` (place id in STEDER/TEORIER to zoom to), `pos?` (own map point), `lenke?`, `kompass?`, `anagram?`.
- Map layer ids used by hints in this range, with names from `src/data/lag.ts`:
  - `solidag` = "Sol 23.09 (satellitt)"
  - `teorier` = "Teorier fra fellesskapet"
  - `retning` = "Retningslinjer (118°)"
  - `skydekke` = "Skyer og tåke (utelukket)"
  - `kjoretid` = "Kjøretid fra Oslo"
  - `modell` = "Sannsynlighetskart"
  - `defaultno` = "Kandidater fra default.no"
  - `fly` = "Flyene hun så kl. 21:29"
  - `felt` = "Søkesektor fra parkering"
  - `utelukket` = "Utelukket av fellesskapet"
  - `treslag` = "Skog som ligner (bjørk, gran, furu)"
- `felt` layer definition (lag.ts L855–866): "Fra bilen ligger kassen altså mot ca. 300° (±25°, nordvest), 300–900 m unna, oppover og uten sti."

---

## 2. Hint-by-hint extraction

### 1. `solidag`: "Sol hos Anja, skyet over mesteparten av Norge" (L47–57)
- **Status:** tolkning · **Date:** 23.09 · **Source:** "Satellittbilde (fellesskapet)" · **pos:** [60.75, 11.85] · **lag:** solidag
- **Evidence class:** C-OBS (community reading of a satellite image; the image itself is not in the repo) + C-INT. The claim that Anja had sun rests on the stream visuals.
- **tekst (verbatim):** «Formiddagen 23.09 var det skyer over store deler av Norge på satellitt, mens Anja hadde sol. Klart var det fra Kongsvinger opp til Rena på siden mot Sverige, i deler av Vestfold og rundt Trondheim–Ålesund.»
- **betydning (verbatim):** «Kassen står trolig i et av de klare områdene. Det peker mot Kongsvinger–Elverum–Rena, som passer med flyet over Hamar, like ved Løten. Fredrikstad, Sarpsborg og Halden var overskyet hele dagen og er ute. Trondheim–Ålesund var blått på Windy tidligere, og det er uklart hvilke deler av Vestfold som var klare.»
- **English:** On the morning of 23.09 the satellite image showed cloud over most of Norway, while the stream showed sun. The clear areas were Kongsvinger→Rena on the Swedish side, parts of Vestfold, and Trondheim–Ålesund. The author infers the box is in one of the clear areas, most likely Kongsvinger–Elverum–Rena. Fredrikstad, Sarpsborg and Halden are ruled out (overcast all day).
- **Map polygons** (`SOL_I_DAG`, L1142–1151). The code comment says they were drawn roughly from a *description*, not from the image itself:
  - [0] Kongsvinger–Rena: (60.1,11.85),(60.5,11.6),(60.88,11.35),(61.15,11.2),(61.3,11.35),(61.3,12.1),(61.0,12.45),(60.6,12.6),(60.2,12.55),(60.0,12.2)
  - [1] Vestfold: (59.05,9.95),(59.1,10.55),(59.6,10.45),(59.65,10.0),(59.35,9.8)
  - [2] Trondheim–Ålesund: (62.3,5.9),(62.8,6.2),(63.2,8.0),(63.55,10.0),(63.5,10.7),(63.2,10.6),(62.9,9.0),(62.5,7.2),(62.2,6.3)
- **Revisions:**
  - `52c0b78` (23.09 15:02): created, with the wording "Tidligere i dag".
  - `3885ab8` (23.09 15:07): added "Fredrikstad, Sarpsborg og Halden … er ute".
  - `41304dc`: added pos.
  - `a141dae` (24.09 19:59): "flyet over Løten" corrected to "flyet over Hamar, like ved Løten" (the NOZ56U position is closer to Hamar/Løten after the Kartverket check).
  - `4a22327` (25.09 11:21): "Tidligere i dag" changed to "Formiddagen 23.09", and the layer renamed from "Sol i dag" to "Sol 23.09".
- **Caveat:** see `lysfake`. The sunlight on the stream was questioned as possibly filtered. The author concluded it was real because of the geometry check.

### 2. `benny`: «Reven heter Benny» (L58–68)
- **Status:** usikker · **Date:** 23.09 · **Source:** Tavla · **fokus:** bennyoy · **lag:** teorier, retning
- **Evidence class:** P-WB (the name) + C-INT (the place-name mapping)
- **tekst:** «Anja skrev at kosedyr-reven i boksen heter Benny.» TAVLE L904: `23.09 · REVEN HETER BENNY`. No photo is in the repo. A fox plush is visible in the box in `tavle-hogd.jpg` and `tavle-2509-5-grader.jpg`.
- **betydning (verbatim):** «Kan være et navnehint. Bare ett stedsnavn i Norge starter med «Benny»: Bennyøy, en holme i Nome (Telemark), 3,4 km fra 118°-linja fra Horde i Bergen. I Løten finnes gården Benningstad, 10 km fra flyet. Begge kan være tilfeldigheter, og Bennyøy er en øy.»
- **Places:**
  - Bennyøy, Nome: [59.2666, 9.1327] (TEORIER L1096–1101). Its info adds: «Men «Ikke en øy»-hintet taler imot.»
  - Benningstad, Løten: [60.7685, 11.3575] (TEORIER L1089–1094). Its info: «Ca. 10 km fra der flyet NOZ56U var kl. 21:28. Trolig bare en tilfeldighet.»
- **My verification:**
  - Bennyøy is **3.19 km** off a 118° geodesic from Bergen, and 247 km from Bergen at azimuth 118.7°. Off a 120° line it is 5.4 km, off 122° it is 14.1 km, and off 124° it is 22.7 km. So it only fits the *uncorrected magnetic* reading. The 118° figure was the sign's compass bearing at the box; a line from Bergen is purely a theory.
  - Benningstad is **9.8 km** from NOZ56U at 21:28:14, 7.0 km from its interpolated 21:28:53 position, and 12.8 km from `FLY_PUNKT` (21:29:50).
- **Revisions:** single commit `6d6d45c` (23.09 15:16).
- **Extra primary fact:** SIKRE_FAKTA L1457 says «Kassen står i Norge, ikke på en øy …». The origin of «Ikke en øy» is not in this range.

### 3. `tretopp`: "Tretopphyttene i Ringsaker (sjekket, ikke der)" (L69–80)
- **Status:** usikker · **Date:** 23.09 · **Source:** "Chat + default.no. Takk til default.no." · **fokus:** tretopp · **lag:** teorier · **lenke:** https://tretopphytter.no/
- **Evidence class:** C-INT (chat tip) + C-OBS (a chat user searched the site) + MODEL (default.no candidate)
- **tekst:** «Tretopphyttene (Danseråsvegen 173, Brumunddal) har et ekorn som logo, i grønt. Noen mener det er hintet bak ekornet i appen.»
- **betydning (verbatim):** «Oppdatering: én i chatten har sjekket alle Tretopphyttene og Prøysenstua, uten funn. Flere mistenkte hyttene tidligere. Det andre flyet, NOZ9EG, passerte ca. 3 km fra Tretopphyttene kl. 21:31, og default.no har en kandidat i Ringsaker. Mot: Anja var et sted uten vinduer og wifi, og Horde unngår trolig hytter i år.»
- **Places:**
  - Tretopphyttene [60.9748, 10.9167] (TEORIER L1103–1108). Its info: «NOZ56U var ca. 21 km unna (19° over horisonten) da Anja pekte opp»; «Ca. 2 t fra Oslo».
  - Prøysenstua, Rudshøgda [60.912, 10.8076] (STEDER L1074). Its info: «Én i chatten har sjekket stua, men skogen rundt er ikke sjekket.»
  - Prøysenstjerna (ca.) [60.9115, 10.806].
- **Retraction/"Oppdatering":** in `ce85e10` (23.09 15:51) the title changed from "Tips: Tretopphyttene i Ringsaker" to "(sjekket, ikke der)", and the betydning gained "Oppdatering: én i chatten har sjekket alle Tretopphyttene og Prøysenstua, uten funn". Earlier text (`3885ab8`, 23.09 15:07) said: «Men stedet lå utenfor det klare området på satellitt 23.09, og flyet var 21 km unna (19°) da Anja pekte opp.»
- **Map layer `hytter`** (lag.ts): 8 cabins; «Bjørkhytta» booked for the whole hunt; «Alle er sjekket av en i chatten, uten funn» (source: tretopphytter.no booking calendar 23.09).
- **My verification:**
  - NOZ9EG passes **2.97 km** from Tretopphyttene at 21:31:16 real time. Linear interpolation gives a minimum of 2.2 km at about 21:31:07. The claim "ca. 3 km kl. 21:31" holds.
  - The TEORIER claim "21 km / 19°" to NOZ56U matches `FLY_PUNKT` (21:29:50): I get 21.4 km and 18.7°. At 21:28:53 (the "pekte opp" time used for Digeråsen) the figures are 27.8 km and 13.0°.
- **Related later primary evidence:** `ingenhytte`: «INGEN HYTTE I NÆRHETEN SOM JEG VET OM ELLER SER» (24.09 17:20).

### 4. `lysfake`: "Er sollyset på streamen falskt?" (L81–89)
- **Status:** usikker · **Date:** 23.09 · **Source:** "Chat + Dagbladet-video + default.no. Takk til default.no."
- **Evidence class:** C-OBS (the stream visual as described by chat) + NEWS (Dagbladet video) + MODEL (default.no sun fit)
- **tekst (verbatim):** «Tidlig om morgenen, da nattkameraet ble skrudd av, var det skyer og grått. Neste sekund var det plutselig sol og den «AI»-looken streamen har nå. I Dagbladet-videoen fra stedet er det mindre sol, og lyset faller ikke likt som på streamen.»
- **betydning (verbatim):** «Taler imot: default.no regnet ut kameraretningen fra sola alene (219–220°), og Anja skrev senere «KAMERA 41 ØST» (filmer mot ca. 221°). To uavhengige målinger stemmer, så sollyset ser ekte ut. Bildet kan likevel være filtrert i farger. Anjas egne ord («KLAR HIMMEL») påvirkes ikke. Lyden er allerede vist å være delvis avspilt på nytt, se default.no.»
- **Retraction/reversal:** the original betydning (`52c0b78`, 23.09 15:02) was «Kan bety at bildet er filtrert eller kunstig lyssatt. Da er hint som bygger på sol i bildet usikre: «Sol i dag» og solbanen (kamera mot 220°).» It was reversed in `7983773` (23.09 15:45) after «KAMERA 41 ØST».
- **Supporting data:** `defaultno_mer.json` → `solbane`: window 2026-09-21 16:20–17:40, 40 points, best-fit heading **219.4–219.7°**, rms ≈3.30, pitch −0.3…+0.7, over trial latitudes 58.5–60.5. KAMERA 41 ØST + 180° = **221°**.
- **Note:** the 25.09 night-camera (IR) frames at 09:49 and 09:58 (`tavle-2509-ingen-take.jpg`, `tavle-2509-5-grader.jpg`) are greyscale IR images in daytime. So at least some daytime whiteboard captures come from the IR camera, not the colour feed.

### 5. `haslemoen`: "Tips fra fellesskapet: Flisa og Haslemoen" (L90–100)
- **Status:** usikker · **Date:** 23.09 · **Source:** "Chat + default.no. Takk til default.no." · **fokus:** haslemoen · **lag:** teorier, solidag
- **Evidence class:** C-INT (chat tip)
- **tekst (verbatim chat quote):** «Tror og i nærheten av Rena. Men ikke helt. Kanskje mer i området Flisa? Haslemoen har en nedlagt base.»
- **betydning (verbatim):** «Ligger i det som var klart på satellitt 23.09, i typisk furumo mot Finnskogen. Men flyet Anja pekte på var ca. 40 km unna, og default.no fant at Finnskogen ikke passer med flyet. Lagt inn som egen teori (Solør).»
- **Place:** Flisa/Haslemoen [60.66, 11.87] (TEORIER L1110–1115). Its info: «Ca. 2,5 t fra Oslo. Flyet NOZ56U var ca. 40 km unna (10° over horisonten) da Anja pekte opp.»
- **My verification:** 41.2 km / 9.8° to `FLY_PUNKT` (21:29:50); 37.3 km / 9.7° to the 21:28:53 position. "ca. 40 km (10°)" holds.
- **Later status:** Solør/Finnskogen is excluded by the community exclusion map (`utelukkingskart`).

### 6. `taake`: "Tykk tåke i Odal og på Jessheim i morges" (L101–111)
- **Status:** tolkning · **Date:** 23.09 · **Source:** "Lokal i chatten (bor i Nord-Odal)" · **pos:** [60.3, 11.45] · **lag:** skydekke
- **Evidence class:** C-OBS (local resident in chat) + P-SV (no fog at Anja, from the stream)
- **tekst (verbatim):** «Det var tykk tåke her i dag tidlig, hele veien til Sør-Odal og Jessheim», mens det ikke var tåke hos Anja.
- **betydning (verbatim):** «Nord-Odal, Sør-Odal og området rundt Jessheim er utelukket. Tegnet grovt på kartet sammen med de blå Windy-områdene. Solør og Elverum ligger utenfor.»
- **Polygon** (`TAAKE`, L1153–1156, "Grovt tegnet"): (60.1,11.05),(60.08,11.4),(60.18,11.75),(60.3,11.85),(60.48,11.75),(60.5,11.4),(60.35,11.15),(60.2,11.0).
- **Revisions:** `e94d4db` (23.09 15:18) created; `41304dc` added pos.
- **Caveat:** "no fog at Anja" on the morning of 23.09 is an inference from the stream. `lysfake` says the early morning was «skyer og grått». The only explicit «INGEN TÅKE» whiteboard is from 25.09 09:49.

### 7. `reise`: "Reisen: fra Oslo kl. 04:00, sov nesten hele veien" (L112–123)
- **Status:** bekreftet · **Date:** 22.09 · **Source:** "Tavla + Børsen-intervju" · **pos:** [59.9139, 10.7522] (Oslo) · **lag:** kjoretid, modell · **lenke:** https://borsen.dagbladet.no/nyheter/anja-29-snakker-ut-absurd/85185489
- **Evidence class:** P-WB + NEWS
- **tekst (verbatim):** «Anja ble hentet i Oslo kl. 04:00 (søndag ifølge tavla). Vinduene i bilen var dekket til. Hun sov store deler av turen og «aner ikke hvor lenge de kjørte». Hun tror selv det var ca. 7 timer. Kun bil, ingen ferge.»
- **Primary whiteboards** (TAVLE):
  - L882 `21.09 18:31`: «INGEN FLY · INGEN SKYTING · OSLO, SØN KL 04.00 · CA 5–10 MIN Å GÅ FRA BIL»
  - L883 `21.09 18:36`: «INGEN FERGE · KUN BIL · VET IKKE ANG. TUNELLER»
  - L884 `21.09 18:38`: «TROR DET VAR OPPOVER · SISTE 5–10 MIN»
- **betydning (verbatim):** «Kjøretiden er ikke et fakta: hun sov og vet ikke hvor lenge de kjørte. Den er derfor av som standard. Viktig åpent spørsmål: tavla sier søndag, men Børsen skriver at hun har sittet i buret «siden mandag morgen». Ble hun hentet mandag 04:00, var turen under ca. 3 t (streamen startet 06:50). Slå på «Hentet mandag» i Teorier-fanen for å se utslaget.»
- **Revisions (downgrading of the drive time):**
  - `c0c849b` (23.09 14:30): «Hun tror hun sov ca. 7 timer i bilen … usikker på tunneler».
  - `ecf0260`: added «Streamen startet mandag 21.09 ca. 07:00».
  - `520fd05` (23.09 14:49): rewritten with the Børsen interview, dated 22.09; model default «7 t ± 2 t».
  - `58e737c` (23.09 14:59): added the Sunday vs Monday open question.
  - `66e31ce` (23.09 15:39): «Kjøretiden er ikke et fakta … Den er derfor av som standard.» The drive-time layer is off by default.
- **STEDER L1066:** «Anja ble hentet her søndag 20.09 kl. 04:00.»
- **Numbers:** pick-up 04:00; ~7 h (her own guess, unreliable); stream start 06:50 (this hint), "ca. 07:00" (old text), "LIVE 07:00" (whiteboard L886), 06:40 (`bindfold`); a Monday pick-up would allow a drive under ~3 h.

### 8. `bokstaver`: "Bokstaver ved verving = HORDE MINUS (løst)" (L124–132)
- **Status:** lost · **Date:** none · **Source:** "Horde-appen («Verv en venn»)" · **anagram:** true
- **Evidence class:** P-APP (letters shown after referral) + C-INT (anagram) + P-APP (Horde AI reply, see `eiffel`)
- **tekst (verbatim):** «Etter å ha vervet noen får man opp bokstaver. Bekreftet sett så langt, ikke i riktig rekkefølge: N O R H E I M S U D.»
- **betydning (verbatim):** «HORDE MINUS bruker nøyaktig alle ti bokstavene, uten rest, og nå er det bekreftet: skriver man «Hordeminus» til Horde AI, svarer den «2,7 eiffeltårn stablet oppå hverandre» (ca. 891 m, se eget hint). Én idé: «HORDEJAKTEN» minus «HORDE» = «JAKTEN», og dyrene (rev, and, kråke) er jaktbare. Prøv ordene i kredittskår-boksen i appen. NORHEIMSUND (Kvam i Hardanger) passer nesten, men mangler én N, og Hardanger var blått på Windy-kartet. Test egne ord under.»
- **`BOKSTAVER` constant** (L1193): ['N','O','R','H','E','I','M','S','U','D'].
- **Retraction chain:**
  - `f99df64` (23.09 14:43): the first reading was **NORHEIMSUND**: «Alle ti bokstavene finnes i NORHEIMSUND (Kvam i Hardanger), og bare én N mangler. Det er 6,5 t å kjøre fra Oslo uten ferge, som passer med «sov ca. 7 t». Horde holder også til i Bergen, ca. 1 t unna.» It had fokus norheimsund.
  - `b671b5b` (23.09 14:59): switched to the HORDE MINUS exact anagram.
  - `7ebb743` (24.09 18:30): «nå er det bekreftet» via Horde AI.
  - `94558c2` (24.09 18:46): status tolkning changed to **lost**.
  - `63416f0` (25.09 11:07): removed `lag: ['teorier']` and `fokus: 'norheimsund'`, so Norheimsund is dropped from the map.
- **Norheimsund place** (TEORIER L1131–1136): [60.3707, 6.1453]. «6,5 t fra Oslo uten ferge, og ca. 1 t fra Horde i Bergen (5008).»
- **My verification:** Counter(HORDEMINUS) == Counter(NORHEIMSUD) is True. NORHEIMSUND minus the letters leaves {N:1}.
- **What is primary here:** the ten letters shown by the app, and the Horde AI's canned reply to «Hordeminus». "Solved" means the anagram produced a canned response. It says nothing yet about the location.

### 9. `retning118`: "Horde-skiltet pekte 118–120°" (L133–142)
- **Status:** bekreftet · **Date:** none (TAVLE L900 "Ukjent"; L905 "23.09") · **Source:** "Tavla («ØST CA 118 · RETNING SKILT») + kompasstegning" · **lag:** retning · **kompass:** true
- **Evidence class:** P-WB (the numbers) + C-INT (the sketch reading and what the sign points at)
- **Primary whiteboards:**
  - TAVLE L900 `Ukjent`: «ØST CA 118 · RETNING SKILT (skiltet peker ca. 118°)»
  - L905 `23.09`: «118–120 GR ØST (retningen skiltet peker)»
  - L909–915 `23.09`: a sketch, best reading «KAMERA» at the top, the box in the middle, «SKILT» on the right; the word on the left and at the bottom is illegible (`tavle-skisse.jpg`, `tavle-skisse-forsterket.jpg`). In the enhanced image I could not independently read the words.
  - L916 `23.09`: «KAMERA 41 ØST»
- **tekst (verbatim):** «Anja skrev at skiltet peker ca. 118° øst-sørøst, senere «118–120 gr øst». Skissen fra fellesskapet: skiltet står vest-nordvest for kassen og peker mot den, Anja skrev senere «KAMERA 41 ØST»: kameraet står ca. 41° (nordøst) fra kassen og filmer mot ca. 221°. Korrigert for misvisning (kompass viser ca. 4° for lite på Østlandet) blir sann retning ca. 122–124°.»
- **betydning (verbatim):** «Skiltet viser veien inn til kassen. Folk kommer altså fra vest-nordvest: fra bilen går du ca. 120° (øst-sørøst), 5–10 min oppover. Søkesektoren i kartet bruker dette. Andre teorier: en linje fra Oslo eller fra Horde i Bergen.»
- **Numbers:**
  - 118°, 118–120° magnetic.
  - Declination about +4° gives 122–124° true.
  - Camera at 41° from the box, looking at 221°. Left of frame ≈ 131°, right of frame ≈ 311° (my arithmetic).
- **Revision history.** This is the most-edited hint; the interpretation flipped twice:
  1. `c0c849b` (23.09 14:30), titled "«ØST CA 118» på tavla", status **tolkning**: «Fellesskapet tolker det som retningen fra kassen til parkeringen (øst-sørøst). Kameraet står ca. 73°.» Betydning: «Står du på parkeringen, ligger kassen mot ca. 298° (vest-nordvest) … Hvis 118° i stedet er retningen mot Oslo, ligger kassen på linja nordvest for Oslo (Valdres og Sogn).»
  2. `58e737c` (14:59): camera "ca. 73°" changed to «nordøst for kassen og ser mot sørvest (ca. 220° ifølge solbanen)».
  3. `bdffb03` (15:15): status set to **bekreftet**; «Horde-skiltet peker 118° (øst-sørøst)»; «Retningen er bekreftet. Hva skiltet peker på er ikke det. Mest trolig: veien inn fra parkeringen. Da ligger kassen mot ca. 298° (vest-nordvest) fra bilen».
  4. `2eb6f94` (15:17): 118° changed to 118–120° per Anja.
  5. `86d52b8` (15:22): **flipped**. «Skiltet viser veien inn til kassen. Folk kommer altså fra vest-nordvest: fra bilen går du ca. 120°». The camera "filmer mot ca. 208°".
  6. `7983773` (15:45): camera changed to 41°/221° per «KAMERA 41 ØST».
  7. `893318a` (24.09 19:55): title "peker 118–120° mot kassen" changed to "pekte 118–120°" (the sign had been removed).
  - **Flip back:** `4e65b1c` (24.09 18:35) added `komfra`, which reverses the parking sector to ~300° again. **This hint's betydning was never updated**, so it still says «fra bilen går du ca. 120° … Søkesektoren i kartet bruker dette». That contradicts `komfra` and the `felt` layer (300° ±25°). See Contradictions.
- **Related:** the `retning` layer (lag.ts L203–217) draws a 298° line from Oslo with ±5° uncertainty, a dashed 118° line from Oslo, a 118° line from Horde AS Bergen, and a dashed line «korrigert for misvisning (ca. 123°)». The layer is labelled "teori".

### 10. `lyder`: "Lyder på streamen: tog, klokker, skudd? (lav sikkerhet)" (L143–151)
- **Status:** usikker · **Date:** 21.09 · **Source:** "default.no (lydanalyse) + chat. Takk til default.no."
- **Evidence class:** MODEL (default.no audio tagger) + RELAY (chat saying what Anja hears) + P-ORG (Alf quote)
- **tekst (verbatim):** «default.no sin lydanalyse fant mulige tog (08:34, 11:29, 14:07), klokker (08:35, 14:00) og skudd (14:24, 14:54) den 21.09, alle med lav sikkerhet (0,33–0,51). I chatten sies det at Anja ikke hører tog, bil eller skyting.»
- **betydning (verbatim):** «Usikkert: default.no fant identiske lydbiter 22–48 t fra hverandre, som tyder på loop. Men Alf sa på TikTok-live 25.09 at «det er ekte lyd på streamen» (tidligere år trollet de med lyden). Om den er live eller forsinket, ville han ikke si: «Ja, det må du prøve å finne ut av.» Det passer med ekte lyd som er tatt opp og spilt av på nytt. Lyder fra streamen sier derfor ingenting om stedet. Anjas eget svar (ingen tog, bil eller skyting) teller mer: kassen står trolig et stille sted, ikke nær jernbane eller trafikkert vei.»
- **Revisions (the loop claim was softened):**
  - `fe51e10` (23.09 15:55): «Trolig støy, ikke ekte lyder.»
  - `06b82f0` (23.09 16:01): «Kan ikke brukes: lyden på streamen er trolig falsk og går i loop».
  - `970c493` (25.09 10:59): changed to «Usikkert … Men Alf sa … «det er ekte lyd på streamen»».
  - `c7ed3f9` (25.09 11:08): added «Ja, det må du prøve å finne ut av.»
- **Supporting data** (`analyse.json` → `lyd`, updated 2026-09-23 12:27):
  - 52.86 h audio, 2873 files, 604 checked.
  - 227 copies at ≥0.8 correlation, 451 at ≥0.6.
  - Lag clusters: 23.9 h (290), 47.9 h (48), 24.9 h (25), 22.0 h (20), 27.3 h (20).
  - Examples at corr 0.993–0.999, e.g. 23.09 11:40:40 ≈ 21.09 11:47:10 (0.999).
  - YAMNet tag counts: wind 9173, speech 193, aircraft 49, train 20, dog 16, siren 11, gunshot 10, bell 7, music 2.
- **Primary whiteboards:** «INGEN FLY · INGEN SKYTING» (21.09 18:31); «HØRER IKKE MYE FRA BOKSEN» (21.09 18:44); «LYDTETT» (23.09 17:49); «INGEN LYD I BOKSEN OVERHODET, JEG HAR KUN DERE Å UNDERHOLDE MEG. INGENTING ANNET» (24.09, L970). The chat claim "Anja does not hear trains, cars or shooting" is not a verbatim whiteboard quote in this range.

### 11. `fugler`: "Fuglelyder: sidensvans og furukorsnebb" (L152–160)
- **Status:** usikker · **Date:** 21.09 · **Source:** "default.no (BirdNET). Takk til default.no."
- **Evidence class:** MODEL (BirdNET on stream audio, which may be looped)
- **tekst (verbatim):** «Fuglegjenkjenning fant granmeis, blåmeis, rødvingetrost, skjære og gråtrost, en flokk sidensvans kl. 07:36 og furukorsnebb.»
- **betydning (verbatim):** «Furukorsnebb passer med gammel furuskog. Sidensvans er i september mest meldt i Nord-Norge, men kan være feilgjenkjenning. Sier lite om stedet.»
- **Cross-check** (`analyse.json` → `fugler`), by detection count:
  - Kjøttmeis 966, Blåmeis 802, Granmeis 325, Bokfink 295, Rødvingetrost 240, Gråtrost 148, Skjære 125, Dompap 123, Gråsisik 109, Grankorsnebb 96, **Furukorsnebb 48**, Kjernebiter 47, …
  - **Vintererle 39, Isfugl 39**, Sidensvans 32, …, Boltit 15, Sothøne 3, Gråhegre 3.
  - `fuglerFeil` lists non-Norwegian misidentifications (e.g. "Cape White-eye", "Wood Duck").
  - The hint does not mention the water-associated species (Isfugl/kingfisher, Vintererle/grey wagtail, Gråhegre, Sothøne). They conflict with «INGEN VANN» and are probably misidentifications or looped audio.

### 12. `froland`: "Froland er utelukket: været stemmer ikke" (L161–171)
- **Status:** tolkning · **Date:** 23.09 · **Source:** "Fellesskapet (værdata)" · **fokus:** froland · **lag:** teorier
- **Evidence class:** C-OBS (weather data vs the stream) + C-INT
- **tekst (verbatim):** «Det regnet i Froland onsdag kveld 23.09, men det var ikke regn på streamen. Været i Froland samsvarer ikke med det Anja har sett og skrevet.»
- **betydning (verbatim):** «Froland og Agder-teorien trekkes kraftig ned. Ekornet i kommunevåpenet er ikke nok alene, ekorn finnes overalt.»
- **Place:** Froland [58.53, 8.63], `utelukket: true` (TEORIER L1137): «Utelukket: været i Froland samsvarer ikke med det Anja har sett.»
- **Revisions:**
  - `6cddb71` (23.09 15:46): created as the retraction of the Froland/squirrel theory (commit "Rule out Froland: the weather does not match"). Also `9ea67b3` (15:23) "Weaken the squirrel clue".
  - `01ab80d` (25.09 11:29): added the specific rain observation («Det regnet i Froland onsdag kveld 23.09»).
  - In `893318a` (24.09 19:55) the TEORIER entry changed from «Froland (lite sannsynlig)» to «Froland (utelukket)».
- **Also:** `SKYANALYSE = { senter: [58.7, 8.27], indreKm: 12, ytreKm: 45 }` (L1181), a cloud-analysis "meeting point read off the image, ±15 km" in Agder. It is presumably the earlier analysis behind the Agder/Froland theory.

### 13. `dnflyceller`: "default.no: klare celler i kveld + flyrute-filter" (L172–182)
- **Status:** tolkning · **Date:** 23.09 · **Source:** "default.no (23.09). Takk til default.no." · **pos:** [60.9, 11.2] · **lag:** defaultno, fly
- **Evidence class:** MODEL
- **tekst (verbatim):** «default.no sin nyeste analyse: klare celler i kveld er Finnskogen (8,5 °C), Koppang (8,2 °C), Trysil (6,1 °C) og halvskyet Meråker. «Sett + hørt fly»-testen deres beholder bare ca. 10 % av landet: vestsiden av Østerdalen (Elverum–Rena–Koppang under NOZ56U/NOZ9EG), Røros–Gauldal–Meråker-korridoren og Hallingdal.»
- **betydning (verbatim):** «Peker mot vestre Østerdalen (Løten–Elverum–Rena–Koppang), som passer med begge flyene, klar himmel og furumo. Deres nr. 1 er nå Løten/Elverum-skogen, nr. 2 Rena–Åsta.»
- **`DEFAULTNO` candidates** (L1158–1165; "fusjonsmodell (22.09 kl. 16:42; klare celler i kveld 23.09)"):
  1. Hamar øst mot Løten (skog) [60.9, 11.2]: "Klar himmel, under flyet"
  2. Rena og Åsta [61.3, 11.2]: "Klar himmel, under flyet"
  3. Koppang [61.5, 11.0]: "8,2 °C klart i kveld"
  4. Finnskogen (Solør) [60.6, 12.35]: "8,5 °C klart i kveld"
  5. Trysil [61.3, 12.3]: "6,1 °C klart i kveld"
- **`DEFAULTNO_TERRENG`** ("site finder", L1169–1175): Gålaveien [61.4725, 10.9677] Rena/Åmot; Madsskardveien [61.4747, 11.0966] Rena/Åmot; Tolvmilskogen [60.69, 12.35] Solør; Kirkesjøvegen [60.358, 12.507] Solør/Finnskogen. A fifth entry, Birkebeinerveien [61.4495, 10.9752], was removed in `e431102` (25.09 14:12).
- **Flight points:**
  - `FLY_PUNKT` NOZ56U [60.8705, 11.2481], 23 892 ft, «da Anja skrev «FLY» (ekte tid ca. 21:29:50)».
  - `FLY_PUNKT2` NOZ9EG [61.216, 10.896], 23 500 ft, «sørover mot Gardermoen, over Ringsakfjellet (ca. 21:29:15)».
  - My interpolation of `fly_2130.json` reproduces both: NOZ56U at 21:29:50 = (60.8705, 11.2482, 23 893 ft); NOZ9EG at 21:29:15 = (61.2167, 10.8960, 23 504 ft).
- **Revisions:** `35ba6b9` (23.09 18:16) created; `41304dc` added pos.

### 14. `komfra`: «Kom fra den veien ←» og «ingen stier» (L183–192)
- **Status:** bekreftet · **Date:** 24.09 · **Source:** Tavla · **lag:** felt
- **Evidence class:** P-WB. I verified the text and arrow direction in `public/img/tavle-kom-fra-den-veien.jpg`: the colour daytime camera shows the arrow pointing left in the frame.
- **tekst:** «Anja skrev «KOM FRA DEN VEIEN» med en pil mot venstre i bildet, og «INGEN STIER».» (TAVLE L958–962)
- **betydning (verbatim):** «Kameraet filmer mot ca. 221° (to uavhengige målinger), så venstre i bildet er ca. 130° (sørøst). Horde-skiltet pekte også mot venstre i bildet, 118–120°. Da ligger bilen og veien trolig sørøst for kassen, og man går mot nordvest (ca. 300°) og oppover fra bilen til kassen. «Ingen stier» betyr at de gikk rett gjennom skogen. Søkesektoren fra parkering på kartet er snudd til ca. 300°. Merk at dette snur den gamle tolkningen, der kassen lå mot 120° fra bilen.»
- **Explicit reversal:** «Merk at dette snur den gamle tolkningen» (commit `4e65b1c`, 24.09 18:35, "«kom fra den veien ←» flips the parking search sector to ~300°").
- **Caveat:** the "left of frame" → bearing conversion assumes the arrow is drawn in the camera's image frame and that Anja wrote it facing the camera. The board is held up facing the camera, so "left in image" = left from the camera's point of view. This is interpretation, and it is not otherwise checked.

### 15. `regn1105`: "Regn hos Anja kl. 11:05, og regn i Rena samtidig" (L193–202)
- **Status:** tolkning · **Date:** 24.09 · **Source:** "Tavla + værdata (fra fellesskapet)" · **pos:** [61.133, 11.367] (Rena centre)
- **Evidence class:** P-WB/P-SV (rain at Anja; TAVLE L999 "(kl. 11:05) Anja sa at det regnet", so the medium is unclear) + C-OBS (rain in Rena)
- **tekst (verbatim):** «Anja sa at det regnet kl. 11:05 den 24.09. Ifølge fellesskapet regnet det i Rena akkurat da.»
- **betydning (verbatim):** «Passer med Rena og Åmot. Regnbyger dekker ofte store områder, så det utelukker ikke steder i nærheten. Ikke sjekket mot radar her: da trengs regnradar for akkurat 11:05. Streamen ligger trolig 20 sek–1 min bak (vi tipper).»
- **Revisions:** `4d069c1` (24.09 18:49) created ("weak evidence for Rena"). `01ab80d` (25.09 11:29) changed "Streamen ligger 45 sek bak" to "trolig 20 sek–1 min bak (vi tipper)".
- **Note:** the default.no radar snapshot in `defaultno_mer.json` is for 2026-09-24 16:35Z, not 11:05, so it cannot confirm this. That file names a region «boksen (Rena-Evenstad)», which shows default.no's working hypothesis.

### 16. `graver`: «Gråvær hele dagen» (24.09) (L203–211)
- **Status:** bekreftet · **Date:** 24.09 · **Source:** Tavla
- **Evidence class:** P-WB. Verified in `tavle-graver.jpg`: the board reads «GRÅVÆR HELE DAGEN», on the colour daytime camera.
- **tekst:** «Anja skrev 24.09: «GRÅVÆR HELE DAGEN».»
- **betydning (verbatim):** «Etter klar himmel og sol 21.–23.09 var det overskyet hele 24.09 der kassen står. Kan sjekkes mot satellittbilder og værdata for 24.09: steder med sol store deler av dagen passer dårlig. Ikke lagt inn i modellen ennå.»

### 17. `hogst`: «Det har vært hogd tidligere der jeg gikk» (pil →) (L212–221)
- **Status:** bekreftet · **Date:** 24.09 · **Source:** Tavla · **lag:** felt
- **Evidence class:** P-WB. Verified in `tavle-hogd.jpg`: «DET HAR VÆRT HOGD TIDLIGERE DER JEG GIKK I GÅR, GIKK DEN VEIEN →», with the arrow at the lower right pointing right.
- **tekst (verbatim):** «Anja skrev «DET HAR VÆRT HOGD TIDLIGERE DER JEG GIKK I GÅR, GIKK DEN VEIEN» med pil mot høyre i bildet, og «Så ingenting som ikke hører til i en skog».» TAVLE L998: «SÅ INGENTING SOM IKKE HØRER TIL I EN SKOG I GÅR · PS! HÅPER PÅ PEPPERONIPIZZA».
- **betydning (verbatim):** «Høyre i bildet er ca. 310° (nordvest), siden kameraet filmer mot ca. 221°. Det passer med «KOM FRA DEN VEIEN ←» (ca. 130°): hun kom fra sørøst og gikk mot nordvest til kassen. På veien gikk hun gjennom et gammelt hogstfelt. Let etter eldre hogstflater sørøst for mulige steder, mellom veien og kassen. Ingen bygninger eller annet uvanlig langs gåturen. Det er uklart hva «i går» viser til.»
- **My logic check:** the board says she walked "that way →" (right in frame, ≈310° NW) and that the logging was where she walked. The plain reading is that the old felling lies to the **northwest** of the box, in the direction she walked «i går». A board dated 24.09 makes «i går» 23.09, which is probably not the arrival (20/21.09). The author's advice to look for felling **southeast** of the box does not follow from the arrow. See Contradictions.

### 18. `ingenhytte`: «Ingen hytte i nærheten som jeg vet om eller ser» (17:20) (L222–231)
- **Status:** bekreftet · **Date:** 24.09 · **Source:** Tavla · **fokus:** tretopp
- **Evidence class:** P-WB. Verified in `tavle-ingen-hytte.jpg`: TavlAI overlay 2026-09-24 17:20:17, IR camera, «INGEN HYTTE I NÆRHETEN SOM JEG VET OM ELLER SER».
- **tekst:** «Anja skrev kl. 17:20: «INGEN HYTTE I NÆRHETEN SOM JEG VET OM ELLER SER».»
- **betydning (verbatim):** «Taler imot teorier om at kassen står ved en hytte eller et hyttefelt, som Tretopphyttene. Det passer med skog uten stier, 5–10 min fra en vei.»

### 19. `treslag`: «35 % bjørk, 25 % gran, 40 % furu» rundt kassen (18:13) (L232–241)
- **Status:** bekreftet · **Date:** 25.09 · **Source:** Tavla · **lag:** treslag
- **Evidence class:** P-WB. Verified in `tavle-2509-treslag.jpg`: overlay 2026-09-25 18:13:23, «KANSKJE / 35% BJØRK / 25% GRAN / 40% FURU / AKKURAT RUNDT MEG». Anja's T-shirt reads «FINN MEG». A wooden hand stands upright in the heather in front of the box (see `hand-tilbake`).
- **tekst:** «Anja skrev kl. 18:13: «KANSKJE 35% BJØRK, 25% GRAN, 40% FURU. AKKURAT RUNDT MEG.»»
- **betydning (verbatim):** «Blandingsskog med mest furu og mye bjørk, og minst gran. Det passer furumo og lyngmark, ikke tett granskog. Mye bjørk tyder på høyereliggende skog eller et gammelt hogstfelt (som hun gikk gjennom). Slå på kartlaget «Skog som ligner (bjørk, gran, furu)» for å se hvor skogen har omtrent samme blanding.»
- **Data:** `public/data/treslag.json` has target {furu 0.40, gran 0.25, lauv 0.35}, a 0.02°×0.04° grid, source «NIBIO SR16 (dominerende treslag), hentet 25.09.2026». Note that it maps birch into "lauv" (all broadleaf).
- **Revisions:** `4d44d6a` (25.09 19:12) created; `ae6dc67` (19:19) added the layer.

### 20. `fly2509`: "Hun pekte mot himmelen igjen 25.09 kl. 17:22: SAS50J over Stange" (L242–252)
- **Status:** bekreftet · **Date:** 25.09 · **Source:** "Stream + ADS-B fra adsb.lol (sporet til SAS50J)" · **pos:** [60.59, 11.536] · **lag:** fly
- **Evidence class:** P-SV (the pointing gesture, stream time 17:22) + C-OBS (matching it to SAS50J). **The match to a specific aircraft is an inference.** The pointing direction is not recorded.
- **tekst (verbatim):** «Anja pekte opp mot himmelen kl. 17:22 (streamtid). Da, rundt 17:21–17:22 ekte tid, var SAS50J (Oslo → nord) over østre Stange mot Romedal og Løten, på 21 000–23 000 fot. På Flightradar24 var også SAS364 på vei nordover over Rena.»
- **betydning (verbatim):** «Andre gang hun peker på et fly, og igjen er det et fly fra Gardermoen nordover langs linja Hamar–Løten–Elverum–Rena. SAS50J var ca. 23 km øst for sporet til NOZ56U fra 21.09. Kassen ligger trolig et sted mellom eller langs disse sporene, i skogen øst og nord for Hamar. Sporet er tegnet på kartet i laget «Flyene hun så».»
- **Track** (`FLY_2509`, L1638–1642; «SAS50J (A320neo, OSL nordover) 25.09 kl. 17:17–17:27, ekte tid … Kilde: ADS-B fra adsb.lol»): 16 points from 17:17:00 (60.1448, 11.3412, 10 175 ft) to 17:26:42 (61.1689, 11.5894, 30 300 ft). Key points:
  - 17:21:03 (60.5292, 11.5304, 20 825 ft)
  - 17:21:21 (60.561, 11.5341, 21 525 ft)
  - 17:22:41 (60.7043, 11.5471, 24 100 ft)
- **My verification:**
  - pos [60.59, 11.536] corresponds to SAS50J at about **17:21:37 real time**.
  - Distance to the NOZ56U (21.09) track: 27.1 km at 17:21:00, **23.1 km at 17:21:30**, 20.0 km at 17:22:00, 18.2 km at 17:22:30. "ca. 23 km øst" holds for about 17:21:30.
  - Altitude over 17:21:00–17:22:30 is 20 700–23 700 ft.
- **Images:** `fr24-2509-sas50j.jpg` shows SAS50J north-north-east of Gardermoen, between Hamar/E6 and Elverum, heading north. `fr24-2509-sas364.jpg` shows SAS364 north of Rena, on a track roughly along lon ≈11.4–11.5. The screenshots have no timestamps.
- **Contradiction:** "Andre gang hun peker" (second pointing). `defaultno_mer.json` → `observasjoner.fly` records a 22.09 pointing: «Hun peker, setter seg opp og følger flyet sørover (NOZ55J, 21 000 fot)» at 2026-09-22T20:34:40+02:00, plus a chat «FLYY» event at 20:32:40 (SAS39A). So this may be the third event.
- **Revisions:** single commit `9a7359b` (25.09 18:02).

### 21. `musikk-cherry`: "Hordes innlegg om økonomisk stress har musikken «Cherry Blossom»" (L253–261)
- **Status:** tolkning · **Date:** 24.09 · **Source:** "Hordes Facebook-innlegg (ca. 24.09)"
- **Evidence class:** P-MEDIA (the post exists) + C-INT
- **tekst (verbatim):** «Horde la ut «Ikke stå i det alene», om gjeld og psykisk helse sammen med Mental Helse, med musikken «Cherry Blossom» av Ella Joy Meir.»
- **betydning (verbatim):** «Trolig ikke et hint: innlegget handler om økonomisk stress, og musikken er fra Facebook sitt bibliotek. Det viser at Facebook skriver musikk som «sang · artist», så i storyen med fruktkurven heter sangen «Goldenrod» (gullris) og artisten «Riverbank».»
- **Role:** a calibration example used to parse the story's music label. It is not a location hint.

### 22. `skilt-tilbake`: "Horde-skiltet ser ut til å være tilbake (video 25.09 kl. 16:20)" (L262–271)
- **Status:** usikker · **Date:** 25.09 · **Source:** "Opptak av streamen via default.no (202609251620–202609251703). Takk til default.no." · **lenke:** https://default.no/cuts/202609251620_202609251703.mp4 (blocked from this machine)
- **Evidence class:** P-SV (via a default.no recording). Verified in `stream-2509-skilt-tilbake.jpg`: a wooden arrow-shaped sign painted «HORDE» in red stands on the **right** of the frame and points **left** towards the box. The box contains balloons (green, yellow, pink, blue). Anja wears «FINN MEG». A whiteboard at the front left is faintly legible, consistent with the THILPRTE OESHF board.
- **tekst (verbatim):** «I ballongvideoen fra 25.09 kl. 16:20–17:03 står et treskilt med «HORDE» til høyre for kassen, formet som en pil som peker mot venstre, altså mot kassen. Anja skrev «SKILTET ER BORTE» 23.09 kl. 19:12. Solen skinner rett inn i kameraet rundt kl. 16:45–16:50, og hun holder opp tavla to ganger.»
- **betydning (verbatim):** «Enten er skiltet satt tilbake, eller så er det et annet skilt. Retningen er den samme som før: mot venstre i bildet, altså ca. 118–130°. At sola står rett foran kameraet rundt kl. 16:45 passer med at kameraet filmer mot sørvest (ca. 221°). Sjekk streamen for å bekrefte at skiltet står der nå.»
- **Sun check (my computation, NOAA-style approximation at 61.0°N 11.2°E):**
  - On 25.09 the sun's azimuth/elevation is 231.7°/17.9° at 16:20, **237.7°/15.4° at 16:45**, 238.8°/14.9° at 16:50 and 241.9°/13.5° at 17:03 CEST.
  - With the camera facing 221°, the sun at 16:45 is about 17° right of centre. That is inside a normal field of view, so the "sun straight into the camera" observation is roughly consistent, but it is not a precise azimuth test.
  - For comparison, default.no's 21.09 16:20–17:40 fit window spans sun azimuths of about 232°–251°.
  - For precise horizon work, see the mk_bevis horizon/sun scripts.
- **Revisions:** single commit `ac06655` (25.09 17:55).

### 23. `hand-tilbake`: "En hånd er tilbake foran kassen (25.09)" (L272–280)
- **Status:** bekreftet · **Date:** 25.09 · **Source:** "Stream (nattkamera)"
- **Evidence class:** P-SV. Verified in `stream-2509-hand.jpg` and `tavle-2509-treslag.jpg` (25.09 18:13:23): an articulated wooden hand stands upright on a stick in the heather in front of the box, fingers up and palm open.
- **tekst (verbatim):** «En hånd står igjen i lyngen foran kassen, der Horde-skiltet med hendene sto før det ble fjernet 23.09. Den står rett opp med åpen hånd.»
- **betydning (verbatim):** «Hendene under skiltet ble tidligere lest som tall (romertall eller fingre). Én åpen hånd kan bety 5, eller at hendene kommer tilbake én og én med et nytt tall eller en ny retning. Følg med på om flere dukker opp.»
- **Related history:** commit `4e26d93` (23.09 14:59) "Add Roman numeral and binary theories for the sign hands".

### 24. `shoplifter`: "Tavla: «THILPRTE OESHF» = THE SHOPLIFTER eller FILTER THE SHOP? · «Noen som vet fasiten»" (L281–290)
- **Status:** tolkning · **Date:** 25.09 · **Source:** Tavla · **lenke:** https://default.no/cuts/202609251620_202609251703.mp4
- **Evidence class:** P-WB (letters; verified in `tavle-2509-shoplifter.jpg`: «THILPRTE / OESHF») + P-MEDIA/P-SV (the balloons) + C-INT (the anagram readings). «NOEN SOM VET FASITEN» is not visible in the cropped image; it rests on the text and TAVLE L1038.
- **tekst (verbatim):** «Anja skrev «THILPRTE OESHF» og «NOEN SOM VET FASITEN» på samme tavle. Bokstavene kommer fra ballongene i en video Horde la ut (opptak via default.no), og de 13 bokstavene går nøyaktig opp i både THE SHOPLIFTER, FILTER THE SHOP og den norske HELHET FOR TIPS. Fargene på ballongene: grønn E, P og T · lilla E · blå F · gul H, H, I, R, S og T · rosa L og O.»
- **betydning (verbatim):** «FILTER THE SHOP er en konkret oppgave: gå inn i butikken i Horde-appen (Horde Rewards) og bruk filteret, for eksempel på pris eller kategori. Butikken har allerede hint som T-skjorta i Terje-modell til 1 116 897 og det utstoppede dyret med olivenolje, så det passer godt med at kodehintene ligger i appen. Oppdatering 25.09: butikken i Horde-appen har ikke noe filter, så denne lesningen er svakere. HELHET FOR TIPS kan bety at man må se alle hintene samlet, som en helhet, i stedet for hvert for seg. Den kan fortsatt bety noe annet, som å se nøye gjennom (filtrere) varene i butikken. «Noen som vet fasiten» kan bety to ting: at hun spør chatten om noen kan løse bokstavene, eller at THE SHOPLIFTER er «noen som vet fasiten», altså at BobTheShoplifter er inne på riktig svar. Uansett trolig en hilsen til BobTheShoplifter, en av de mest aktive i Discord-gruppa og mannen bak default.no, som mye av dataen i denne appen kommer fra. Anja kan se chatten, så det er et nikk til de som leter. Det kan bety at de er på riktig spor, eller bare at de har lagt merke til ham. Fargene er ikke løst ennå. Én idé er dartskive-fargene fra Kodejakten (blå +, gul −, rosa ×, lilla ÷), men grønn finnes ikke der. Stor takk til BobTheShoplifter og default.no.»
- **My verification:**
  - THE SHOPLIFTER, FILTER THE SHOP and HELHET FOR TIPS are each exact anagrams of THILPRTE OESHF (13 letters).
  - The balloon colours total 13 and match the letter multiset.
  - `tavle-2509-ballongfarger.png` shows E(green) E(purple) F(blue) H H I(yellow) L O(pink) P(green) R S T(yellow) T(green).
- **Revision chain:**
  - `ed45704` (25.09 17:51): created as status **lost**, «nøyaktig THE SHOPLIFTER».
  - `37bd161` (17:54): added the balloon colours and the video origin.
  - `9db1159` (17:58): added «Noen som vet fasiten».
  - `72f623a` (18:44): status lost changed to **tolkning**, with FILTER THE SHOP as an equally valid reading.
  - `971c9d6` (18:46): «Oppdatering 25.09: butikken i Horde-appen har ikke noe filter, så denne lesningen er svakere».
  - `a5526bb` (19:41): added HELHET FOR TIPS.
- **Related removed hint:** `terje-tskjorte` (added `7e3690f` 25.09 12:43, folded into the «terje» hint in `2f86bbf` 13:01). Its text: «I butikken i appen selges «T-skjorte i Terje-modell» i grønt, med H-logo og «Terje lurer ikke meg», til 1 116 897 mynter, samme sum som i kassen. Teksten sier: «Det går rykter om at de som kjøpte denne sist, økte kredittscoren sin betraktelig. Tilfeldig? Neppe.»» (screenshot `public/img/app-terje-tskjorte.jpg`)
- **Provenance ambiguity:** this hint calls the balloon footage «en video Horde la ut». `skilt-tilbake` calls it «Opptak av streamen». Both cite the same default.no cut.

### 25. `ferist`: «Ingen ferist som jeg merka» (L291–299)
- **Status:** bekreftet · **Date:** 25.09 · **Source:** Tavla
- **Evidence class:** P-WB (no photo in the repo; TAVLE L1035)
- **tekst:** «Anja skrev 25.09: «INGEN FERIST SOM JEG MERKA».»
- **betydning (verbatim):** «En ferist er en rist i veien som hindrer beitedyr i å gå ut, og den dunker godt når bilen kjører over. De er vanlige på seter- og fjellveier der sau og storfe går fritt, for eksempel på Ringsakfjellet, Sjusjøen og mange setervoller i Østerdalen. Taler litt imot slike veier, men hun sov mesteparten av turen, så hun kan ha kjørt over en uten å merke det.»

### 26. `god-helg`: «God helg og god jakt» med fruktkurv, og musikk i Hordes story («Goldenrod · Riverbank») (L300–308)
- **Status:** tolkning · **Date:** 25.09 · **Source:** "Hordes story 25.09 (skjermbilde)"
- **Evidence class:** P-MEDIA (Horde's Facebook story) + P-WB (the board in it). Verified in `tavle-2509-god-helg.jpg`: the story header reads "Horde 6 min" and "Goldenrod · Riverbank"; the board shows a drawn fruit basket, «OG GOD JAKT» and «GOD HELG ♥». This is a close-up handheld photo, not the stream camera.
- **tekst (verbatim):** «Anja holdt opp en tavle med en tegnet fruktkurv (eple, appelsin, banan, pære, jordbær og druer) og «GOD HELG ♥ OG GOD JAKT». Musikken kommer fra Hordes story på Facebook: øverst i storyen står «Goldenrod · Riverbank», som er musikken Horde la på. Facebook skriver musikk som «sang · artist» (se Horde-innlegget med «Cherry Blossom · Ella Joy Meir»), så sangen heter «Goldenrod» og artisten «Riverbank». Den var ikke på streamen, og Anja hører den ikke i boksen. Det er uklart hva som er artist og hva som er sangtittel, og vi fant ikke noen kjent sang med det navnet, så det er trolig et spor fra Facebook sitt eget musikkbibliotek.»
- **betydning (verbatim):** «Trolig bare en hilsen før helgen. Men tavla kl. 10:21 samme dag sa «GJETT RIKTIG SANG», så sangvalget kan være et hint. Sangen heter «Goldenrod», som er planten gullris. «Riverbank» (elvebredd) er bare artistnavnet, så det teller mindre. Kassen står neppe ved en elv: Anja skrev 22.09 «ingen vann eller vannlyder, føler ikke det er vann i noe nærhet». Fruktkurven kan også være et ordspill. Ren tolkning.»
- **Related primary evidence:**
  - «GJETT RIKTIG SANG · BACKFLIP» (25.09 10:21:45, verified in `tavle-2509-sang.jpg`).
  - «IKKE MØRKT ENDA · INGEN VANN ELLER VANNLYDER, FØLER IKKE DET ER VANN I NOE NÆRHET» (22.09 19:19:32, verified in `tavle-2209-ingen-vann.jpg`).
- **Retraction chain:**
  - `7e3690f` (25.09 12:43): «sangen «Riverbank» av Goldenrod»; «Riverbank» betyr elvebredd; «kassen kan stå nær en [elv]».
  - `dd51345` (14:56): "stop calling it a known song".
  - `67c7124` (14:59).
  - `e0365b0` (17:56): the song/artist order was inverted using the «Cherry Blossom» post.
  - `6c421a9` (20:53): **"drop the riverbank idea"**, replacing «Alf har sagt at man aldri må krysse en elv, men kassen kan stå nær en» with «Kassen står neppe ved en elv: Anja skrev 22.09 «ingen vann …»».

### 27. `flylangtunna`: «Flyene er så langt unna at det er umulig å se» (25.09) (L309–318)
- **Status:** bekreftet · **Date:** 25.09 · **Source:** Tavla · **lag:** fly
- **Evidence class:** P-WB. Verified in:
  - `tavle-2509-overskyet.jpg`: «OVERSKYET / FLYENE ER SÅ LANGT UNNA AT DET ER UMULIG Å SE PÅ DAGEN, OG PÅ NATTA DERSOM DET IKKE ER HELT STJERNEKLART»
  - `tavle-2509-ingen-take.jpg` (09:49:11): «INGEN TÅKE»
  - `tavle-2509-5-grader.jpg` (09:58:41): «SIKKERT 5° / TROR DET ER VARMERE»
- **tekst (verbatim):** «Anja skrev 25.09: «OVERSKYET. FLYENE ER SÅ LANGT UNNA AT DET ER UMULIG Å SE PÅ DAGEN, OG PÅ NATTA DERSOM DET IKKE ER HELT STJERNEKLART.» Samme dag: «INGEN TÅKE» (09:49) og «SIKKERT 5°, TROR DET ER VARMERE» (09:58).»
- **betydning (verbatim):** «Flyene går høyt over henne, i marsjhøyde, ikke lavt inn mot en flyplass. Det passer med «LITE MED FLY HER» og med NOZ56U/NOZ9EG på 20 000–27 000 fot. Overskyet uten tåke og ca. 5 °C morgenen 25.09 kan sjekkes mot værdata.»
- **Revisions:** single commit `01ab80d` (25.09 11:29).

### 28. `haaland-brauta`: "Grevlingstativet: Haaland, og stedet Brauta?" (L319–328)
- **Status:** tolkning · **Date:** 25.09 · **Source:** "Tips fra chatten (Codex)" · **pos:** [61.43659, 10.1854]
- **Evidence class:** C-INT (chat; "Codex" suggests an AI-generated tip)
- **tekst (verbatim):** «Dyret i Horde Rewards ligner flaskestativet Erling Braut Haaland tok med hjem fra Texas (en utstoppet vaskebjørn med en flaske). Teorien er at hintet ikke handler om dyret, men om navnet Haaland, eller mellomnavnet Braut. Det finnes et sted som heter Brauta i Ringebu, like sør for Fåvang.»
- **betydning (verbatim):** «Brauta i Ringebu er dyrket mark på ca. 190 moh, altså ikke 810–891 moh. Men det er 37 steder på 810–891 moh nær vei innen 5 km, de fleste med vei mot sørøst. Vinden var ca. 4 m/s der 23.09 kl. 17:49, mens Anja skrev «vindstille». Ren tolkning.»
- **Place:** STEDER L1068 «Brauta», Ringebu (sør for Fåvang) [61.43659, 10.1854]: «Dyrket mark, ca. 190 moh.»
- **My verification:**
  - `hoyde891.json` has **37** grid points within 5 km of Brauta; 35 of them have flag = 1 (road to the SE per the layer); elevations 797–910 m.
  - `vind.json` (open-meteo historic forecast at 10 m, 2026-09-23 17:49): the nearest cell (61.4, 10.0) gives 4.4 m/s (second value 7.7, probably gust); cell (61.4, 10.4) gives 2.8 m/s. "ca. 4 m/s" is a *model* value, not an observation.
- **Related history:** `67eb8d0` (25.09 11:01): "The Horde Rewards animal may be Haaland's stuffed raccoon from Texas, not a badger". `10c2793`: badger hint. `337ddc2` (25.09 14:56) **removed** the Horde AI «grevling» reply: «1 Hordeminus = 3,4 grevlinger»; the commit message says "it was not repeatable in a new chat".

### 29. `regel-ko`: "Kø ved kassen, og 5 timers karantene hvis du ikke får opp låsene" (L329–337)
- **Status:** bekreftet · **Date:** 25.09 · **Source:** "Alf på Hordes TikTok-live 25.09"
- **Evidence class:** P-ORG (relayed; see the note on status)
- **tekst (verbatim):** «Alf sa på TikTok-live at det blir et køsystem hvis flere kommer til kassen samtidig, og at man får 5 timers karantene hvis man ikke klarer å åpne låsene. Det er for at alle skal få prøve, og ingen skal sitte lenge og prøve koder.»
- **betydning (verbatim):** «Ha kodene klare før du drar ut. Du får trolig bare en kort runde med forsøk før du må vente 5 timer. Prøv de sikreste kodene først (se «Mest sannsynlige koder»).»
- **Status inconsistency:** created in `a1a9e1c` (25.09 11:03) as **usikker**, «gjengitt i chatten (ikke sjekket ordrett)». Upgraded to **bekreftet** in `094b3b8` (11:16) with no stated verification. The sibling hint `tiktok2509`, from the same live stream, remains usikker/«ikke sjekket ordrett».
- **Lock facts nearby** (not hints in this range): TAVLE L985 «(kl. 08:24) 5 SIFFER · GANSKE SIKKER (om dørlåsen)»; L990 «2x HENGELÅS 4 TALL · 1x KODELÅS 5–6 TALL · TROR 5»; L918 «ELEKTRONISK LÅS PÅ DØRA MED 5 SIFFER»; L1007 «KAN IKKE TESTE KODER · INGEN HAR FUNNET BOKSEN».

### 30. `tiktok2509`: "Alf på TikTok-live 25.09: ekte lyd, dyrene kan være hint, koder kan ha kommet, ingen farlig vei" (L338–346)
- **Status:** usikker · **Date:** 25.09 · **Source:** "Alf på Hordes TikTok-live 25.09, gjengitt i chatten (ikke sjekket ordrett)"
- **Evidence class:** P-ORG via RELAY (quotes as relayed in chat, not checked verbatim)
- **tekst (verbatim):** «Alf sa på TikTok-live: «Det er ekte lyd på streamen. Men dere husker kanskje tidligere år, da drev vi å trollet litt med lyden.» «Har reven og anda noe med hint å gjøre? Ja, kanskje.» «Kan være at noen av kodene allerede har kommet.» «Kommer en del viktige hint nå i løpet av helgen.» På spørsmål om lyden er live eller forsinket, svarte han med et smil: «Ja, det må du prøve å finne ut av.» Han sa også at man kanskje må gå litt, men aldri noe farlig, som å krysse en elv, og ba alle huske at det er jaktsesong og gå i tydelige klær.»
- **betydning (verbatim):** «Lyden: Alf sier den er ekte, men ville ikke si om den er live eller forsinket («det må du prøve å finne ut av»). default.no fant lydbiter som gjentar seg 22–48 t senere, så lyden kan være ekte, men spilt av på nytt. Begge deler kan stemme hvis noe av lyden er ekte og noe er lagt på, eller hvis Alf troller igjen. Vær forsiktig med å bruke lyd. Dyrene: reven og anda kan være hint. Kodene: noen kan allerede være kjent, for eksempel 5008 fra appen og 0810/0891 fra Horde AI. Flere viktige hint kommer i helgen. Veien til kassen krever ikke noe farlig, som å krysse en elv: du skal kunne gå dit uten å vade eller klatre.»
- **`TIKTOK_2509`** (L1626–1636) restates the same eight items. Its reading of the animals: «ekorn, stokkand, rev, orrfugl og grevling/vaskebjørn».
- **Revisions:** `970c493` (25.09 10:59) created; `c7ed3f9` and `dc35cc6` (11:08) added the live/delayed answer and the no-dangerous-crossing and visible-clothes remarks.

### 31. `kodeniappen`: Horde: «Hint til hva kodene kan være ligger i appen» (L347–355)
- **Status:** bekreftet · **Date:** 24.09 · **Source:** "Horde i kommentarfeltet" (the platform is not named)
- **Evidence class:** P-ORG
- **tekst (verbatim):** «En bruker spurte hvordan man finner koden på låsene. Horde svarte: «Hint til hva kodene kan være ligger i appen 💙».»
- **betydning (verbatim):** «Bekrefter at kodene skal finnes i appen. Det styrker kodene som kommer fra appen: 5008 (kredittskår + «terje»), 6788 (skiltnummeret LD6788 ga «ENKODE») og 0891/0810 (HORDEMINUS i Horde AI). Kodejakten ligger også i appens univers. Tall fra chatten eller plakaten teller mindre.»
- **Stale text:** it still states «6788 (skiltnummeret LD6788 ga «ENKODE»)» as fact, although `enkode` was downgraded to unconfirmed in `893318a` (24.09 19:55).

### 32. `eiffel`: "HORDEMINUS i Horde AI = «2,7 eiffeltårn stablet oppå hverandre»" (L356–364)
- **Status:** bekreftet · **Date:** 24.09 · **Source:** "Horde AI i appen"
- **Evidence class:** P-APP (the canned reply) + C-INT (the 810/891 m reading) + MODEL (the chatbot's own arithmetic, explicitly flagged as not a hint)
- **tekst (verbatim):** «Skriv «Hordeminus» til Horde AI i appen. Svaret er «2,7 eiffeltårn stablet oppå hverandre». Spør man hva det betyr, svarer den at det bare er frasen den har fått beskjed om å bruke for akkurat det ordet. Ber man den oppsummere, regner den selv ut 891 m (330 m) eller ca. 875 m (324 m, høyden 2000–2022) og sier at den ikke vet noe om hvor boksen er. Det er altså bare chatboten som regner, ikke et nytt hint.»
- **betydning (verbatim):** «Bekrefter at bokstavene N O R H E I M S U D skal bli HORDE MINUS. Eiffeltårnet er 300 m uten antenne og 330 m med. 2,7 × 300 = 810 m og 2,7 × 330 = 891 m, så begge er like aktuelle. Mest trolig står kassen ca. 810 eller 891 moh. Det kan også være en avstand, for eksempel fra bilveien, eller en kode: 0810 og 0891 har 4 siffer som hengelåsene. Slå på «810–891 moh nær vei» på kartet for å se steder i den høyden som er høyst 900 m fra vei.»
- **Numbers:** 2.7 × 300 = 810 m; 2.7 × 324 = 874.8 m; 2.7 × 330 = 891 m. Candidate codes 0810 and 0891.
- **Revisions:**
  - `7ebb743` (24.09 18:30): «Mest trolig betyr det at kassen står ca. 891 moh».
  - `2995786` (18:31): both 810 and 891 equal.
  - `9264140` (18:38): the chatbot summary (875 m) is its own reasoning, not a hint.
- **Also:** SIKRE_FAKTA L1465 records «Horde AI har et forhåndslaget svar på HORDEMINUS».

### 33. `soldater`: Video «Ingen har funnet Anja enda..»: soldater, drone og tåke (L365–373)
- **Status:** usikker · **Date:** 24.09 · **Source:** "HordeApp på YouTube"
- **Evidence class:** P-MEDIA + C-INT
- **tekst (verbatim):** «Videoen viser soldater i kamputstyr og en drone i tåke. Teksten sier: «men i år har de også plassert en kvinne i en boks med en livestream».»
- **betydning (verbatim):** «Trolig bare stemning, der «jakten» vises som en militær leteaksjon. Noen vil koble det til Rena leir og Regionfelt Østlandet i Åmot, men Anja skrev «INGEN SKYTING», og skytefeltene er utelukket på fellesskapets kart. Sannsynligvis samme video som globus-bildet fra Facebook. Teller ikke i modellen.»
- **Places:** Rena leir and Regionfelt Østlandet (Åmot); no coordinates in the hint. The shooting ranges are in `public/data/defaultno/skytefelt.json`.

### 34. `globus`: "Facebook-video: globus med Brunei og Malaysia" (L374–382)
- **Status:** usikker · **Date:** 24.09 · **Source:** "Hordes Facebook-video («Ingen har funnet Anja enda, men det kan endre seg kjapt»)"
- **Evidence class:** P-MEDIA + C-INT
- **tekst (verbatim):** «Fryser man videoen Horde la ut på Facebook, viser ett bilde en globus med «SOUTH …», «Bandar Seri Begawan», «BRUNEI» og «MALAYSIA», med glød og røyk over.»
- **betydning (verbatim):** «Trolig bare en globus som snurrer i videoen, altså stemning og ikke et sted. Det er ingen kjent kobling til Norge. Mulige ordlekker, som «BRUN» i BRUNEI, er rene gjetninger. Teller ikke i modellen.»

### 35. `enkode`: "Skiltnummer LD6788 i appen = «ENKODE»? (ikke bekreftet)" (L383–391)
- **Status:** usikker · **Date:** 24.09 · **Source:** "Skjermbilde delt i chatten (ikke sjekket selv)"
- **Evidence class:** RELAY (a claimed P-APP response, unverified)
- **tekst (verbatim):** «Et skjermbilde som er delt i chatten, viser skiltnummer LD6788 lagt inn under «Bil & hus» i appen og svaret «Du fant et hint! ENKODE» (rett etter midnatt 24.09). Vi har ikke klart å bekrefte det selv.»
- **betydning (verbatim):** «Appen har lagt inn et eget svar for akkurat dette skiltnummeret, så LD6788 er med vilje. «ENKODE» (encode, eller «én kode») kan bety at skiltnummeret skal gjøres om til en kode. Den enkleste lesningen er at 6788 er koden til en hengelås (4 siffer). Det er ikke kjent hvor skiltnummeret kommer fra, eller om det er bilen som kjørte Anja. Tolkningen er usikker.»
- **Retraction/downgrade:** created in `addc834` (24.09 18:26) as **bekreftet**, source "Horde-appen", with the instruction «Gå til «Bil & hus» … legg til kjøretøy med registreringsnummer LD6788». Downgraded to **usikker** in `893318a` (24.09 19:55, "Stop marking unverified things as confirmed"). The code entry was cut from sjanse middels to lav. **The betydning still asserts «Appen har lagt inn et eget svar … så LD6788 er med vilje»**, which is stronger than the evidence.

### 36. `frolandekorn`: «FROLAND» i ord-boksen = «Ekornet kan klatre»? (ikke bekreftet) (L392–401)
- **Status:** usikker · **Date:** 23.09 · **Source:** "Skjermbilde delt i chatten (ikke sjekket selv)" · **fokus:** froland
- **Evidence class:** RELAY (a claimed P-APP response, unverified)
- **tekst (verbatim):** «Et skjermbilde som er delt i chatten, viser FROLAND skrevet i ord-boksen under «Kredittskår» og svaret «Du fant et hint! Ekornet kan klatre» (kl. 22:27). Vi har ikke klart å bekrefte det selv, og skjermbildet kan være redigert.»
- **betydning (verbatim):** «Horde har forutsett Froland-teorien (ekornet i kommunevåpenet) og lagt inn et eget svar. «Ekornet kan klatre» kan være et nikk om at ekornet (og kassen) er høyere opp, i skog eller i fjellet, eller at det skal videre. Det kan også bare være en fleip. Froland er fortsatt utelukket fordi været ikke stemmer. Svaret viser også at ord-boksen tar imot stedsnavn, så det er verdt å prøve navn som LØTEN, RENA, RINGSAKER og RUDSHØGDA.»
- **Retraction/downgrade:** created in `addc834` as **bekreftet** («Skriv FROLAND i ord-boksen … Funnet kl. 22:27»), downgraded to **usikker** in `893318a`. The betydning still asserts «Horde har forutsett … og lagt inn et eget svar» as if confirmed.

### 37. `skiltborte`: «Skiltet er borte, vet ikke hvor» (19:12) (L402–410)
- **Status:** bekreftet · **Date:** 23.09 · **Source:** Tavla
- **Evidence class:** P-WB. Verified in `tavle-1912-skilt-borte.jpg`: overlay 2026-09-23 19:12:22, IR, «SKILTET ER BORTE, VET IKKE HVOR». Anja's sweater shows numbers «7 10 12 / 6 18 9» and «J. ST…», partly visible; that is a separate clue.
- **tekst (verbatim):** «Anja skrev kl. 19:12: «SKILTET ER BORTE · VET IKKE HVOR». Horde-skiltet som sto foran kassen og pekte 118–120°, er fjernet.»
- **betydning (verbatim):** «Horde fjernet skiltet samme kveld som fellesskapet begynte å bruke retningen det pekte i. Det kan tyde på at skiltet ga for mye bort. Retningen vi har registrert (118–120°) gjelder fortsatt: den er målt før skiltet ble tatt.»
- **Later:** a HORDE sign is visible again on 25.09 16:20–17:03 (`skilt-tilbake`).

### 38. `litefly`: «Lite med fly her · sikkert med vilt» (19:09) (L411–420)
- **Status:** bekreftet · **Date:** 23.09 · **Source:** Tavla · **lag:** fly
- **Evidence class:** P-WB. Verified in `tavle-1909-fly-vilt.jpg`: overlay 2026-09-23 19:09:54, «LITE MED FLY HER / SIKKERT MED VILT». The last word is plausibly «VILT» but unclear.
- **tekst:** «Anja skrev kl. 19:09: «LITE MED FLY HER» og «SIKKERT MED VILT» (siste ord er litt utydelig).»
- **betydning (verbatim):** «Få fly bekrefter det hun sa første dag («INGEN FLY»): kassen står ikke under en inn- eller utflygningsrute til Gardermoen, der fly går lavt og ofte. Fly i marsjhøyde, som NOZ56U over Hamar, høres lite. «Sikkert med vilt» passer med skog der det jaktes (elg, rådyr, skogsfugl).»
- **Revisions:** `89d7dc0` (23.09 19:12) created; `a141dae` (24.09 19:59) changed "NOZ56U over Løten" to "over Hamar".

### 39. `fjellmark`: «Typisk fjellmark», masse sopp, mose på steiner, ikke vann (L421–431)
- **Status:** bekreftet · **Date:** 23.09 · **Source:** Tavla · **pos:** [61.1, 10.75] · **lag:** teorier
- **Evidence class:** P-WB (TAVLE L919–920 «23.09 kveld», no photo) + C-INT
- **tekst (verbatim):** «Anja skrev: «FÅR SE BITTELITE · MASSE SOPP · TYPISK FJELLMARK» og «IKKE VANN · STEIN + SOPP · MOSE PÅ STEINER». Hun ser bare litt av omgivelsene.»
- **betydning (verbatim):** «Fjellmark betyr høyereliggende, skrinn skog og lyng, typisk 500–900 moh. Det passer Ringsakfjellet og Sjusjøen (under flyet NOZ9EG), og åsene over Rena, Løten og Åmot (Digeråsen 606 moh.). Det passer dårlig med lavlandet ved Rudshøgda, Gjøvik og Toten. Ingen vann i nærheten: ikke ved et vann eller en elv.»
- **Places:** Ringsakfjellet, Sjusjøen, Rena, Løten, Åmot, Digeråsen (606 moh; TEORIER [61.1788, 11.2639], «61°10'43.8"N 11°15'50.1"E»), Rudshøgda, Gjøvik, Toten.
- **Retraction:** in `e431102` (25.09 14:12, "Remove everything about Birkebeinervegen") the mention «Birkebeinerveien ca. 590 moh.» was deleted from this betydning. The same commit deleted the Birkebeinervegen tip: «Flere på Discord (25.09) … ca. 720–1040 moh. Det er 341 steder på 810–891 moh nær vei her, 233 av dem med vei mot sørøst», pos [61.36168, 10.84625]. It also deleted the default.no terrain pin Birkebeinerveien [61.4495, 10.9752] and default.no field notes such as «BOM / privat vei (23.09 ca 00:30) - Birkebeinerveien-avkjoring … Ga forbi bommen til fots, 500 m». **No reason is given.** It is unclear whether the area was searched or the removal was editorial.
- **Interpretation caveat:** "typisk fjellmark" is colloquial Norwegian and may simply mean rugged, rocky, heathery terrain. Equating it with 500–900 moh is the author's reading.

### 40. `bindfold`: "Bind for øynene hver gang hun forlater kassen" (L432–440)
- **Status:** usikker · **Date:** 21.09 · **Source:** "hordejakten.vercel.app (ikke sjekket selv)"
- **Evidence class:** RELAY (a third-party fan site)
- **tekst (verbatim):** «Anja får bind for øynene hver gang hun forlater boksen. Livestreamen starter 06:40.»
- **betydning (verbatim):** «Hun ser aldri omgivelsene utenfor kassen, så det hun forteller gjelder bare utsikten fra kassen. Det forklarer også «Gikk 2 min inn i skogen»: pausestedet er rundt 2 minutter unna, og hun blir ført dit med bind for øynene.»
- **Downgrade:** created in `1971621` (23.09 19:22) as **bekreftet**, source "hordejakten.vercel.app (bekreftet-lista)". Downgraded to **usikker** in `893318a` (24.09 19:55).
- **Conflicts with primary evidence:** «SÅ INGENTING SOM IKKE HØRER TIL I EN SKOG I GÅR» and «DET HAR VÆRT HOGD TIDLIGERE DER JEG GIKK I GÅR» (24.09) show she perceived her surroundings on a walk. Stream start "06:40" conflicts with 06:50 (`reise`) and «LIVE 07:00» (whiteboard 21.09 18:48).

### 41. `gikk2min`: «Gikk 2 min inn i skogen» (L441–449)
- **Status:** tolkning · **Date:** 23.09 · **Source:** Tavla
- **Evidence class:** P-WB (TAVLE L922 «23.09 kveld», no photo) + C-INT
- **tekst:** «Anja skrev: «GIKK 2 MIN INN I SKOGEN».»
- **betydning (verbatim):** «Trolig turen til pausestedet: hun får bind for øynene hver gang hun går ut av kassen (hordejakten.vercel.app). Ellers kan det være hvor langt hun går på pause (til stedet uten vinduer og wifi), eller et nytt anslag for turen inn, kortere enn de 5–10 min hun sa før (hun ble båret med sovemaske). Er det turen inn, står kassen bare 100–200 m fra bilveien.»
- **Revisions:** `4a9f3ee` (23.09 19:01): «Uklart hva det svarer på». `1971621` (19:22) prefixed it with the bindfold explanation, which rests on the later-downgraded `bindfold` relay.
- **Stale claim:** «hun ble båret med sovemaske». SIKRE_FAKTA was corrected in `893318a` from «De siste 5–10 min ble hun båret oppover med sovemaske og headset» to «Siste bit var ca. 5–10 min å gå fra bilen, og hun tror det gikk oppover». FAKTA L1199 still says «Fra bilen, båret oppover». The primary whiteboard (21.09 18:31) says «CA 5–10 MIN Å GÅ FRA BIL».
- **Numbers:** 2 min; 5–10 min; 100–200 m (the author's estimate if 2 min is the walk in).

### 42. `utelukkingskart`: "Utelukkingskart: fjellbjørk" (L450–460)
- **Status:** tolkning · **Date:** 23.09 · **Source:** "Fellesskapet (kart i chatten)" · **pos:** [61.1, 11.1] · **lag:** utelukket
- **Evidence class:** C-INT / MODEL (a community-drawn exclusion map, georeferenced from an image)
- **tekst (verbatim):** «Fellesskapet har laget et kart over hva som er utelukket: rødt, og lyseblått der det vokser fjellbjørk. Det som står igjen er stripa Hamar–Løten–Rena–Koppang, Ringsakfjellet/Rudshøgda og Gjøvik/Toten. (Det rosa «ingen sopp»-laget er tatt ut, det var ikke korrekt.)»
- **betydning (verbatim):** «Utelukker Solør/Finnskogen, Trysil og Elverum sentrum. Åpent: Rudshøgda 100 %, Gjøvik 95 %, Rena 93 %, Ringsaker 83 %, Løten 77 %. Vises som eget kartlag og teller i Teorier-fanen.»
- **Retraction:** created in `6763e06` (23.09 19:08) as «ingen sopp og fjellbjørk», which excluded «Solør/Finnskogen, Trysil, Elverum sentrum, Gudbrandsdalen og Rendalen» with «Rudshøgda og Rena nesten helt, Ringsaker 83 %, Løten 77 %» open. **The pink "no mushrooms" layer was removed as incorrect** in `b55eafc` (23.09 19:13). Gudbrandsdalen and Rendalen were then no longer listed as excluded, and Gjøvik/Toten became open.
- **Data:** `public/data/utelukket.json`: «Fellesskapets utelukkingskart 23.09: rødt = utelukket, lyseblått = fjellbjørk. Stedfestet fra bilde, ca. ±10 km. Vest for bildet (vest for 8,4° Ø) er fylt inn som utelukket.» Grid 0.05°×0.1°.
- **Tension:** `fjellmark` betydning says lowland Rudshøgda/Gjøvik/Toten fits poorly, yet this map leaves Rudshøgda 100 % and Gjøvik 95 % open.

### 43. `powerbank`: "Powerbank-hint? (Jaktvettregel 4 + Horde Rewards)" (L461–469)
- **Status:** usikker · **Date:** 23.09 · **Source:** "Jaktvettreglene + Horde Rewards"
- **Evidence class:** P-APP (a shop listing) + C-INT
- **tekst (verbatim):** «Jaktvettregel 4: «Ta med deg fulladet mobiltelefon … En powerbank i lommen kan være smart.» I Horde Rewards koster «Powerbank Xtorm FS5271 27000mAh» 10 000 poeng. Displayet på bildet viser 68 %.»
- **betydning (verbatim):** «Noen tror tallene er koder: 5271 har 4 siffer (hengelås) og 27000 har 5 siffer (dørlåsen). Trolig tilfeldig: FS5271 er bare modellnummeret til en ekte powerbank. Verdt å prøve hvis du står ved kassen.»
- **Numbers:** 5271, 27000, 10 000 points, 68 %. The candidate codes are 5271 (4-digit) and 27000 (5-digit).

### 44. `lydtett`: «LYDTETT · SOL · VINDSTILLE» (17:49) (L470–479; starts in range)
- **Status:** bekreftet · **Date:** 23.09 · **Source:** Tavla · **lag:** solidag
- **Evidence class:** P-WB (TAVLE L917 `23.09 17:49`, no photo)
- **tekst:** «Anja skrev kl. 17:49: «LYDTETT», «SOL» og «VINDSTILLE».»
- **betydning (verbatim):** «Lydtett forklarer hvorfor hun ikke hører tog, bil eller skyting, og at lyden på streamen ikke kan brukes. Sol kl. 17:49 23.09 betyr at stedet ikke var overskyet på ettermiddagen, som passer med de klare områdene på satellitt (Kongsvinger–Rena). Vindstille gir et nytt værhint: sjekk vind fra værstasjoner kl. 17–18 i kandidatområdene.»
- **Data:** `public/data/vind.json` holds an open-meteo 10 m wind grid for 2026-09-23 17:49 (0.2°×0.4° cells), used to test «VINDSTILLE», e.g. against Brauta.
- **Caveat:** "lydtett" (the box is soundproof) is about what *Anja* hears. It does not imply the stream microphone (outside the box) is unusable; the author's leap to «lyden på streamen ikke kan brukes» is an interpretation.

---

## 3. Deleted hints (from git history) that belonged to this array

| id | Added | Removed | Reason / content |
|---|---|---|---|
| `vedkassen` | early 23.09 (among the first hints) | `094b3b8` 25.09 11:16 ("remove a fake item") | Chat: «Flere som har prøvd seg på koden ved boksen nå by the way. Vi vet hvor det her er hen.» The betydning then said people would come «fra parkeringen mot sørøst (118°)». **Retracted as fake.** The FOLK_TROR entry «Noen er alt ved kassen» was removed in the same commit. Whiteboard 25.09 (L1007): «KAN IKKE TESTE KODER · INGEN HAR FUNNET BOKSEN». |
| `hordeai-grevling` | `996369d` 25.09 14:29 | `337ddc2` 25.09 14:56 | Horde AI reply to «Grevling»: «1 Hordeminus = 3,4 grevlinger», «Dette prosjektet er to grevlinger unna å være ferdig», «Det gir ikke mer mening, men kanskje litt bedre stemning.» **Removed because it was not repeatable in a new chat.** The derived figure «1 grevling er ca. 238 eller 262 m» is void. |
| `terje-tskjorte` | `7e3690f` 25.09 12:43 | `2f86bbf` 25.09 13:01 | Shop item «T-skjorte i Terje-modell» for 1 116 897 coins, «Terje lurer ikke meg», «Det går rykter om at de som kjøpte denne sist, økte kredittscoren sin betraktelig. Tilfeldig? Neppe.» Folded into the «terje» hint (5008). |

Other notable edits made in this period:
- `e431102` (25.09 14:12): Birkebeinervegen removed everywhere, with no reason given (see #39).
- `b55eafc` (23.09 19:13): «ingen sopp» exclusion removed as incorrect (see #42).
- `893318a` (24.09 19:55): **"Stop marking unverified things as confirmed"**. It downgraded `enkode`, `frolandekorn` and `bindfold` from bekreftet to usikker. It changed SIKRE_FAKTA from «båret oppover med sovemaske og headset» to «ca. 5–10 min å gå fra bilen». It changed the sign fact to «(nå fjernet) pekte».
- `66e31ce` (23.09 15:39): "Separate confirmed facts from guesses".
- `01ab80d` (25.09 11:29): stream delay 45 s changed to «trolig 20 sek–1 min (vi tipper)» throughout, except that `STREAM.forsinkelseSek = 45` (L10) remains.

---

## 4. Contradictions and inconsistencies found

1. **Sign/approach direction (internal contradiction).**
   - `retning118` betydning (L139): «Skiltet viser veien inn til kassen. Folk kommer altså fra vest-nordvest: fra bilen går du ca. 120° … Søkesektoren i kartet bruker dette».
   - `komfra` (L190): «bilen og veien trolig sørøst for kassen … man går mot nordvest (ca. 300°) … Søkesektoren … er snudd til ca. 300°». The `felt` layer (lag.ts L855–866) uses 300° ±25°, 300–900 m.
   - `retning118` was not updated after `4e65b1c`.
   - Physically, the sign in the 25.09 footage stands on the frame's **right** (NW side, ≈311°) and points **left** (≈130°) toward the box. If a sign guides visitors to the box, they come from the NW. If Anja "came from" the left (SE), the car is SE. Both cannot be read as "the approach route" unless the sign's purpose is different, for example pointing to the exit or just decorative.
2. **Felling direction.** `hogst`'s arrow «GIKK DEN VEIEN →» is right in the frame ≈310° (NW). Its betydning advises looking for old felling **SE** of candidate sites. On the plain reading the logged area is where she walked, which is to the NW. «I går» on a 24.09 board is 23.09, not the arrival day.
3. **Bindfold vs what she saw.** `bindfold` (unverified fan-site claim): blindfold whenever she leaves. Primary whiteboards: «SÅ INGENTING SOM IKKE HØRER TIL I EN SKOG I GÅR», «DET HAR VÆRT HOGD TIDLIGERE DER JEG GIKK».
4. **Carried vs walked.**
   - Whiteboard 21.09 18:31: «CA 5–10 MIN Å GÅ FRA BIL».
   - 18:38: «TROR DET VAR OPPOVER · SISTE 5–10 MIN».
   - Yet `gikk2min` (L448) says «hun ble båret med sovemaske», and FAKTA L1199 says «Fra bilen, båret oppover». SIKRE_FAKTA was corrected to walking.
5. **Stream start time:** 06:50 (`reise` L120), 06:40 (`bindfold` L438, fan site), «LIVE 07:00» (whiteboard 21.09 18:48, L886), "ca. 07:00" (early `reise` version).
6. **Pick-up day:** whiteboard «OSLO, SØN KL 04.00» vs Børsen «siden mandag morgen». This is unresolved, and it swings the drive time between ~7 h (as she believes) and under 3 h.
7. **21.09 pointing time.** The app uses different reference instants:
   - «da Anja pekte opp (21:28:53 ekte tid)» (TEORIER digeras L1086).
   - «da Anja skrev «FLY» (ekte tid ca. 21:29:50)» (FLY_PUNKT L1167).
   - default.no: «Hun peker opp 21:29:38, skriver «FLY» 21:30:12, og lyden er sterkest 21:33:20».
   - TAVLE «21.09 21:30 FLY (pekte opp, litt mot sørøst)».
   - 21:29:38 − 45 s = 21:28:53, so the "real time" was derived with the now-abandoned 45 s delay.
   - Distances in TEORIER mix the references: Tretopphyttene 21 km/19° and Haslemoen 40 km/10° match 21:29:50; Digeråsen 45 km/8° uses 21:28:53.
8. **"Second pointing" claim** (`fly2509`) vs default.no's record of a 22.09 20:34:40 pointing that followed NOZ55J southward.
9. **Same source, different status:** `regel-ko` is bekreftet and `tiktok2509` is usikker; both come from Alf's TikTok live on 25.09 as relayed via chat.
10. **Audio:** default.no loop evidence (227 of 604 checked segments with corr ≥0.8; lags ~24 h and ~48 h) vs Alf: «Det er ekte lyd på streamen». This can be reconciled if the sound is real but replayed.
11. **Balloon-footage provenance:** `shoplifter` says «en video Horde la ut (opptak via default.no)»; `skilt-tilbake` says «Opptak av streamen via default.no». Same cut URL.
12. **Sign removed vs present:** «SKILTET ER BORTE · VET IKKE HVOR» (23.09 19:12) vs HORDE sign visible 25.09 16:20–17:03.
13. **Birds vs water:** BirdNET detections of Isfugl (39) and Vintererle (39), with Gråhegre and Sothøne at 3 each, vs «INGEN VANN ELLER VANNLYDER» (22.09) and «IKKE VANN» (23.09). This probably says more about BirdNET or the audio loop than about the site.
14. **Stale assertions after downgrades:** `kodeniappen` still says «6788 (skiltnummeret LD6788 ga «ENKODE»)» as fact. `enkode` and `frolandekorn` betydning still say «Appen har lagt inn et eget svar» / «Horde har forutsett …» although the tekst is unverified.
15. **Terrain vs exclusion map:** `fjellmark` says Rudshøgda/Gjøvik/Toten lowland «passer dårlig», while `utelukkingskart` keeps Rudshøgda 100 % and Gjøvik 95 % open.
16. **Bennyøy distance:** the hint says 3.4 km from the 118° Bergen line; I compute 3.19 km on a geodesic. It is off by 14–23 km at the declination-corrected 122–124°, and it is an island, which contradicts «ikke på en øy» (SIKRE_FAKTA).
17. **Stream delay constant:** `STREAM.forsinkelseSek: 45` (L10) vs the prose «20 sek–1 min (vi tipper)».

---

## 5. Places and coordinates mentioned (hints L46–479 plus the referenced STEDER/TEORIER)

| Place | lat, lon | Where | Role / status |
|---|---|---|---|
| Oslo (pick-up) | 59.9139, 10.7522 | L13, `reise` pos | start (04:00, Sunday per the whiteboard) |
| Horde AS, Lars Hilles gate 20A, 5008 Bergen | 60.3896, 5.3297 | L15 | origin of the "118° from Bergen" theory line; 5008 = postcode |
| Sol 23.09 clear area (hint pin) | 60.75, 11.85 | `solidag` | community satellite reading |
| Bennyøy, Nome | 59.2666, 9.1327 | TEORIER L1098 | «Benny» name match; island; weak |
| Benningstad, Løten | 60.7685, 11.3575 | TEORIER L1091 | «Benny»-like farm; ~10 km from NOZ56U at 21:28:14; weak |
| Tretopphyttene, Danseråsvegen 173, Brumunddal | 60.9748, 10.9167 | TEORIER L1105 | squirrel logo; searched by chat, nothing found |
| Prøysenstua, Rudshøgda | 60.912, 10.8076 | STEDER L1074 | house searched; forest not searched |
| Prøysenstjerna (ca.) | 60.9115, 10.806 | STEDER L1075 | 27 m star, context |
| Flisa / Haslemoen | 60.66, 11.87 | TEORIER L1112 | chat tip; Solør excluded by the community map |
| Odal–Jessheim fog area (pin) | 60.3, 11.45 | `taake` | excluded (thick fog morning 23.09) |
| Norheimsund | 60.3707, 6.1453 | TEORIER L1133 | letters theory; superseded by HORDE MINUS |
| Froland | 58.53, 8.63 | TEORIER L1137 | excluded (weather) |
| Agder cloud-analysis centre | 58.7, 8.27 (r 12/45 km, ±15 km) | L1181 | earlier cloud analysis |
| default.no #1 Hamar øst mot Løten | 60.9, 11.2 | L1160, `dnflyceller` pos | model top candidate |
| default.no #2 Rena og Åsta | 61.3, 11.2 | L1161 | model candidate |
| default.no #3 Koppang | 61.5, 11.0 | L1162 | clear-cell candidate |
| default.no #4 Finnskogen (Solør) | 60.6, 12.35 | L1163 | clear-cell; excluded by the community map |
| default.no #5 Trysil | 61.3, 12.3 | L1164 | clear-cell; excluded by the community map |
| Gålaveien (default.no site finder) | 61.4725, 10.9677 | L1171 | terrain match |
| Madsskardveien | 61.4747, 11.0966 | L1172 | terrain match |
| Tolvmilskogen | 60.69, 12.35 | L1173 | terrain match (Solør) |
| Kirkesjøvegen | 60.358, 12.507 | L1174 | terrain match (Solør/Finnskogen) |
| Birkebeinerveien (removed) | 61.4495, 10.9752 | removed in `e431102` | removed without reason |
| Birkebeinervegen tip (removed) | 61.36168, 10.84625 | removed in `e431102` | removed without reason |
| NOZ56U at «FLY» (21:29:50 real) | 60.8705, 11.2481 (23 892 ft) | L1168 | flight reference |
| NOZ9EG (21:29:15 real) | 61.216, 10.896 (23 500 ft) | L1178 | flight reference |
| Rena (rain 24.09 11:05) | 61.133, 11.367 | `regn1105` pos | weak support |
| SAS50J when Anja pointed 25.09 | 60.59, 11.536 (≈17:21:37 real) | `fly2509` pos | flight reference, east Stange |
| Brauta, Ringebu | 61.43659, 10.1854 | STEDER L1068, `haaland-brauta` | ~190 moh farmland; wind ≈4.4 m/s (model) vs «VINDSTILLE» |
| Fjellmark pin (Ringsakfjellet) | 61.1, 10.75 | `fjellmark` pos | interpretation |
| Digeråsen (Løten/Åmot), 606 moh | 61.1788, 11.2639 | TEORIER L1084 | chat tip |
| Exclusion-map remaining strip (pin) | 61.1, 11.1 | `utelukkingskart` pos | community map |
| Rena leir / Regionfelt Østlandet (Åmot) | not given | `soldater` | excluded (shooting ranges; «INGEN SKYTING») |
| Bandar Seri Begawan / Brunei / Malaysia | n/a | `globus` | mood, not a place clue |
| Tokke 2023 | 59.444, 7.989 | STEDER L1076 | prior-year find |
| Kongsberg area 2024 | 59.668, 9.65 | STEDER L1077 | prior-year find |

Names without coordinates in these hints: Kongsvinger, Elverum, Hamar, Løten, Rena, Vestfold, Trondheim, Ålesund, Fredrikstad, Sarpsborg, Halden (solidag); Nord-Odal, Sør-Odal, Jessheim (taake); Kvam/Hardanger (bokstaver); Meråker, Røros, Gauldal, Hallingdal, Østerdalen (dnflyceller); Stange, Romedal (fly2509); Ringsakfjellet, Sjusjøen, setervoller i Østerdalen (ferist); Fåvang (haaland-brauta); Rudshøgda, Gjøvik, Toten (fjellmark / utelukkingskart); Gardermoen (litefly, fly2509). Words the app suggests typing into the credit-score word box: LØTEN, RENA, RINGSAKER, RUDSHØGDA.

---

## 6. Numeric verification summary (my computations)

| Claim (file:line) | Stated | Computed | Verdict |
|---|---|---|---|
| Bennyøy to 118° line from Bergen (L65) | 3.4 km | 3.19 km (geodesic); 5.4 km at 120°, 14.1 km at 122°, 22.7 km at 124° | ≈ok for the magnetic reading only |
| Benningstad to plane (L65) | 10 km | 9.8 km (21:28:14), 7.0 km (21:28:53), 12.8 km (21:29:50) | ok for 21:28:14 |
| NOZ9EG to Tretopphyttene at 21:31 (L76) | ca. 3 km | 2.97 km at 21:31:16; minimum ≈2.2 km at ~21:31:07 | ok |
| NOZ56U to Tretopphyttene (TEORIER L1107) | 21 km, 19° | 21.4 km, 18.7° at 21:29:50; 27.8 km, 13.0° at 21:28:53 | ok only for 21:29:50 |
| NOZ56U to Haslemoen (L97, L1114) | ca. 40 km, 10° | 41.2 km, 9.8° (21:29:50); 37.3 km, 9.7° (21:28:53) | ok |
| FLY_PUNKT / FLY_PUNKT2 (L1168, L1178) | positions | reproduced from `fly_2130.json` by linear interpolation | ok |
| SAS50J east of NOZ56U track (L249) | ca. 23 km | 27.1 → 23.1 → 20.0 → 18.2 km over 17:21:00–17:22:30 | ok at ~17:21:30 |
| SAS50J altitude (L248) | 21 000–23 000 ft | 20 700–23 700 ft over 17:21:00–17:22:30 | ok |
| Eiffel arithmetic (L362–363) | 810/875/891 m | 810.0 / 874.8 / 891.0 | ok |
| Anagrams (L130, L287) | exact | all exact (HORDEMINUS; THE SHOPLIFTER / FILTER THE SHOP / HELHET FOR TIPS; balloon colours sum to 13) | ok |
| Camera geometry (L138, L190, L219) | 221° view; left ≈130°, right ≈310° | 41+180 = 221; 221−90 = 131; 221+90 = 311 | ok |
| Brauta: 37 points at 810–891 m within 5 km, most with road SE (L326) | 37 | 37 (35 flagged), elevations 797–910 | ok |
| Brauta wind 23.09 17:49 (L326) | ca. 4 m/s | 4.4 m/s at cell (61.4, 10.0), open-meteo model | ok (model value) |

---

## 7. Open questions arising from this half

1. Was Anja picked up on Sunday 20.09 (whiteboard) or on Monday (Børsen «siden mandag morgen»)? The drive time is ~7 h (as she believes) or under 3 h.
2. What does the HORDE sign point at: the way in or the way out? The sign stands NW of the box and points SE, while Anja «KOM FRA DEN VEIEN ←» (SE).
3. Which walk does «DET HAR VÆRT HOGD TIDLIGERE DER JEG GIKK I GÅR, GIKK DEN VEIEN →» describe: the arrival or a 23.09 pause walk? Is the old felling NW or SE of the box?
4. Is the returned sign on 25.09 the original? Do the returning wooden hands encode numbers or directions?
5. Is «2,7 eiffeltårn» an elevation (810/891 moh), a distance, or a code (0810/0891)?
6. Are the LD6788 → «ENKODE» and FROLAND → «Ekornet kan klatre» app responses real? Both are unverified screenshots.
7. Exact real-time instant of the 21.09 pointing, given the unknown stream delay (20 s–1 min estimated; 45 s previously assumed).
8. Why was all Birkebeinervegen content removed on 25.09 14:12 without a stated reason?
9. Is the daytime colour stream filtered or processed? The IR camera is used for some daytime whiteboard frames.
10. Is the audio live, delayed or replayed? Alf: «det må du prøve å finne ut av».
11. Does THILPRTE OESHF mean THE SHOPLIFTER (a nod to default.no), FILTER THE SHOP (weakened, since the shop has no filter) or HELHET FOR TIPS? And what do the balloon colours encode?
12. Rain at 11:05 on 24.09: which radar cells had rain at exactly that time? Not checked.

---

## 8. Datasets used

- `/home/user/test/data/raw/magnus/src/data/innhold.ts`: the HINT array (L46–879), TAVLE (L881–1054), STEDER/TEORIER (L1065–1140), polygons and constants (L1142–1200), SIKRE_FAKTA (L1456–1469), TIKTOK_2509 (L1626–1636), FLY_2509 (L1638–1642).
- `/home/user/test/data/raw/magnus/src/data/lag.ts`: map-layer definitions (retning L203–217, felt L855–866, hytter).
- `/home/user/test/data/raw/magnus/src/data/analyse.json`: default.no audio-loop stats, YAMNet tags, plane-sound events and BirdNET species counts (fetched 23.09).
- `/home/user/test/data/raw/magnus/src/data/defaultno_mer.json`: default.no extract fetched 24.09 18:36. Contains the plane-pointing observations (21.09, 22.09), the sun-path camera heading fit (219.4–219.7°), HLS cloud dates, the radar snapshot, flight-sound events and gas zones.
- `/home/user/test/data/raw/magnus/public/data/fly_2130.json`: ADS-B snapshots 21.09 21:28:14–21:34:17 real time (CEST) for ~50 aircraft (from default.no event_planes.json / adsb.lol).
- `/home/user/test/data/raw/magnus/public/data/vind.json`: open-meteo 10 m wind grid, 2026-09-23 17:49.
- `/home/user/test/data/raw/magnus/public/data/hoyde891.json`: 17 234 grid points at ~800–910 m, with distance to road and an SE-road flag.
- `/home/user/test/data/raw/magnus/public/data/treslag.json`: NIBIO SR16 tree-species similarity to 40/25/35.
- `/home/user/test/data/raw/magnus/public/data/utelukket.json`: the community exclusion map, georeferenced ±10 km.
- `/home/user/test/data/raw/magnus/public/img/*.jpg|png`: whiteboard and stream frames (TavlAI overlays), FR24 screenshots and the Horde story screenshot.
- Git history of the magnus repo (`git log -L` per hint id): retraction and edit chronology.
