# Earlier Horde hunts (2023, 2024; no 2025): reconstruction and prior on organizer behaviour

Compiled 2026-09-25. Research subagent: web, "prior years".

## 0. Method and reliability

- **Tooling.** WebFetch is blocked for news hosts: horde.no, mynewsdesk.com, default.no and teksta.no all returned `EGRESS_BLOCKED`. About 60 WebSearch queries in Norwegian and English supplied the result summaries used here. WebFetch worked on github.com. Both public analysis repos were `git clone`d:
  - `MagnusPladsen/hordejakten-2026`, commit `68faa86`, 2026-09-25 21:04 +0200
  - `mkekeoooo/hordejakten-2026`
- **Evidence grades.**
  - **[N]** News outlet, taken from the search-engine summary. The article body itself was not read.
  - **[P]** Primary material from Horde or Alf: TikTok, press release, podcast metadata, or a statement quoted in the news.
  - **[C]** Community analysis on GitHub or skattejakthint-style sites.
  - **[I]** My own inference or calculation.
- **Timestamps.** Post times come from decoding TikTok and X IDs. For TikTok, the ID shifted right by 32 bits gives Unix time. For X, the snowflake decode is used. See §6.
- **Caveat.** The search summaries sometimes mixed 2023 and 2024 facts. One example credits "Sigurd and Hans Inge" to Kongsberg. Where they conflict, I resolved the conflict and flagged it (§7).

---

## 1. Summary table

| | **2023 "Jakten på gjeldfriheten"** | **2024 "Hordejakten 2024"** | **2025** | **2026 (ongoing)** |
|---|---|---|---|---|
| Prize | 1 078 218 kr, in cash at first; replaced by a code word mid-hunt | 1 093 072 kr, as a code word / transfer rather than cash | **No hunt.** Børsen 2026 says it is "the third time" and that previous hunts were in 2023 and 2024 | 1 116 897 kr plus a person (Anja) in the box |
| Launch | Tue 17 Oct 2023 | Mon 29 Apr 2024 | – | Mon 21 Sep 2026 |
| Found | Mon 23 Oct 2023, just before 02:00 (night of day 6) | Sun 5 May 2024, morning. Opened and won Sunday afternoon | – | Not found as of 25 Sep (day 5) |
| Time to find | about 5.8 days (about 139 h) | about 6 days | – | – |
| Place | Tokke municipality, (Vest-)Telemark, at or near the Vinje/Tokke border | "Near the silver mines in Kongsberg" (Sølvgruvene), Buskerud | – | ? |
| Straight-line distance [I] | about 150–160 km from Oslo, about 175–190 km from Bergen | about 73 km from Oslo, about 250 km from Bergen | – | – |
| Drive from Oslo (OSRM grid, optimistic) [I] | about 3.2–3.8 h, 195–225 km | about 1.5 h, about 90 km | – | Anja's own guess is about 7 h, but the route included deliberate detours |
| Drive from Bergen [I, rough] | about 4.5–5.5 h via E134/Haukeli | about 6–7 h | – | – |
| Terrain | Forest with bog ("myr"). Snow on the stream in mid-October | Forest ("skauen") in the historic silver-mine field | – | Heather ("lyng"), rough and hilly ("kupert"), mixed forest with tall trees, "fjelluft", felling nearby, no trail |
| Winners | Sigurd Sundklakk (drove from Åmot, Vinje) and Hans Inge Josdal (drove from Sirdal). Strangers who teamed up and split 539 109 kr each | Joakim Kristiansen, a Nordmøre native living in Eastern Norway. He was the third to arrive and waited for his turn at the locks | – | – |
| How it was cracked | Snow on the stream matched Åmot's weather, plus Flightradar, plus a late hint, plus a field search. At night the finders homed in by car horns and shouting heard on the stream audio | "Late, decisive hint" plus a field search. Several finders reached the box on Sunday morning. The code locks decided the winner | – | – |

---

## 2. The 2023 hunt: "Jakten på gjeldfriheten" (17–23 Oct 2023)

### 2.1 Timeline
- **Tue 17 Oct 2023.** Launch. The TikTok "Jakten på gjeldfriheten er i gang!" was posted 05:03 UTC; ID decode `7290788736235785505`. Its text: "På et hemmelig sted i Norge har vi gjemt en drøy million kroner i kontanter. Tallet 1 078 218 tilsvarer antall nordmenn med rentebærende forbruksgjeld." [P] https://www.tiktok.com/@horde.app/video/7290788736235785505
- Horde put the box out on a Tuesday. It was found in the night leading into Monday. [N] https://borsen.dagbladet.no/nyheter/fant-over-n-million-i-skogen/80385711
- **18 Oct.** Nettavisen and inyheter covered the launch. Horde spent its **entire marketing budget** on the prize. It gave hints via livestream, app and newsletter. The box was locked with **two code locks**. Andersen said the livestream "went down multiple times". Viewers were nervous at every sound, "though it had only been birds so far".
  - [N] https://www.nettavisen.no/okonomi/selskap-med-ellevilt-stunt-har-gjemt-over-n-million-kroner-i-skogen/s/5-95-1400158
  - [N] https://inyheter.no/18/10/2023/har-gjemt-en-million-kroner-i-norsk-skog/
- **About 18–19 Oct.** Horde was the most downloaded free app in the App Store on the Tuesday. The crowd was so large that Horde, **in agreement with the police, sent a team in to remove the cash**. They left a note with a **code word** in the plastic box. The reason given was safety: rival teams fighting, or a finder alone in the forest with 1 million kr.
  - [N] https://borsen.dagbladet.no/nyheter/vill-pengejakt-tar-grep/80370921
  - [N] https://www.tv2.no/nyheter/innenriks/fjernet-en-million-kroner-fra-skogen/16143177/
  - [N] https://www.kom24.no/alf-gunnar-anderse-horde-markedsforing/gjemte-en-million-kroner-i-skogen-na-er-pengene-fjernet/658791
- **Thursday (19 Oct).** A new hint was released: **"2412"**. [N] https://borsen.dagbladet.no/nyheter/millionjakta-er-i-gang-skutt-i-vaeret/81334871 (Børsen's 2024 article looks back at 2023)
- **Sun 22 Oct, 11:07 UTC.** Horde posted the TikTok "Update på Hordejakten – millionen i skogen". [P] https://www.tiktok.com/@horde.app/video/7292737938960534816
- **Mon 23 Oct, just before 02:00.** Sundklakk and Josdal found the box. Sundklakk had searched **more than 16 hours**. A viewer TikTok, "Når du innser at pengene er funnet", was posted 01:44 UTC (03:44 local). The organizer's congratulation TikTok followed at 11:52 UTC.
  - [N] https://borsen.dagbladet.no/nyheter/sigurd-og-hans-fant-millionen-kastet-opp/80389223
  - [P] https://www.tiktok.com/@jaktjegeren/video/7292963813295508769
  - [P] https://www.tiktok.com/@horde.app/video/7293120639622253856
- Horde had "hoped it would last until November". [N] https://www.kom24.no/alf-gunnar-og-kollegaene-gjemte-en-million-kroner-i-skogen-na-er-pengene-funnet/659296

### 2.2 Location
- **"Tokke kommune i Telemark"**
  - [N] https://www.kom24.no/alf-gunnar-og-kollegaene-gjemte-en-million-kroner-i-skogen-na-er-pengene-funnet/659296
  - [N] https://sosialnytt.com/millionen-i-skogen-er-funnet-slik-klarte-de-a-lose-gaten/
  - Regional press ran it as "Over en million kroner funnet i skogen i Telemark": [N] https://www.ta.no/over-en-million-kroner-funnet-i-skogen-i-telemark/s/5-50-1754839
- **Community framing:** "grensen Vinje/Tokke". [C] https://github.com/mkekeoooo/hordejakten-2026/issues/9
- **Finders' routes:** Sundklakk drove from Åmot (Vinje). Josdal drove from Sirdal (Agder). Both headed for "den lille kommunen Tokke i Vest-Telemark". [N] https://borsen.dagbladet.no/nyheter/fant-over-n-million-i-skogen/80385711 (via search summary)
- **No coordinates** appear in any source I could reach.
  - The Magnus map pin at 59.444, 7.989 is labelled "Tokke (område)" and sits on Dalen village centre. It is a placeholder, not the find spot. Its note reads: "Skog, bil og litt gange." [C] MagnusPladsen repo `src/data/innhold.ts` L1076
- **Elevation: not published.** Context for the area:
  - Åmot sits at 465 m and Høydalsmo (Tokke, on E134) at 560 m. [N] https://en.wikipedia.org/wiki/%C3%85mot,_Vinje and https://en.wikipedia.org/wiki/H%C3%B8ydalsmo
  - Snow was falling on the stream in mid-October, in one of "few places in Norway it was snowing that week". [N] https://www.amta.no/fant-en-million-i-skogen-verdige-vinnere/s/5-3-1551361 and https://www.kvinnheringen.no/fant-en-million-i-skogen-verdige-vinnere/s/5-27-474281
  - **[I] Most likely band: about 500–900 moh.** This is not confirmed.
- **Terrain:** forest with bog. Sundklakk rolled into a bog ("myr") from the excitement and had to be pulled out ("rescue operation"). He also threw up a little. [N] https://borsen.dagbladet.no/nyheter/sigurd-og-hans-fant-millionen-kastet-opp/80389223 and https://www.kom24.no/alf-gunnar-og-kollegaene-gjemte-en-million-kroner-i-skogen-na-er-pengene-funnet/659296
- **Road proximity (key point).** Andersen said the box was found "with the help of **car honking** and shouting, since the livestream from the site had sound on". Around 03:00, "we heard people shouting and hollering; they used their voices to locate the box". There were about **15–20 people searching in the same area**.
  - [N/P] https://www.rha.no/fant-en-million-i-skogen-i-tre-tiden-horte-vi-folk-som-ropte-og-hoiet/s/5-70-476728
  - [N/P] https://www.nettavisen.no/nyheter/fant-en-million-i-skogen-verdige-vinnere/s/5-95-1408921
  - [N/P] https://www.ba.no/fant-en-million-i-skogen-verdige-vinnere/s/5-8-2418443
  - **[I]** A car horn from a road was audible on the box microphone. That puts the box within earshot of a drivable road, probably a few hundred metres and at most about 1 km in a quiet night forest.
  - Andersen later told Shifter that during the first stunt he **heard people nearby on the livestream** and feared someone had seen them place the box ("holdt på å kaste opp"). [P via N] https://www.shifter.no/nyheter/horde-grnderen-da-million-stuntet-var-i-gang-holdt-pa-a-kaste-opp/362561
  - **[I]** This also points to a spot near places where people pass.

### 2.3 Hints (2023) and how they mapped
- **Channels:** hints were "continuously on the livestream and app". Horde's page described new hints weekly in the app, the newsletter and Horde Plus. [N] https://borsen.dagbladet.no/nyheter/ny-million-gjemt-i-norsk-skog/81303369 and https://sosialnytt.com/millionen-i-skogen-er-funnet-slik-klarte-de-a-lose-gaten/
- **Hint types reported:** "anything from codes like «2412», to **kommunevåpen med dyr** (municipal arms with animals), to a **video of power lines**". [N] https://borsen.dagbladet.no/nyheter/millionjakta-er-i-gang-skutt-i-vaeret/81334871
  - **"2412"** was a **code** (lock or code word), **not** an elevation or coordinate. [C] https://github.com/mkekeoooo/hordejakten-2026/issues/9 ("Tallhintet fra 2023 (2412) var også en kode.")
  - **Coat of arms with animal.** This is a region wordplay or pictogram.
    - **[I, unverified]** Tokke's arms show a black bear on gold. [N] https://snl.no/Tokke (search summary)
    - The mapping to Tokke is plausible, but no source confirms that the 2023 animal was a bear.
    - The 2026 community reused this "kommunevåpen" approach: ekorn gave Froland, rev gave Vegårshei. They then declared it "dead". [C] issue #9.
  - **Power-line video.** A literal landscape feature in the area.
- **What actually cracked it:**
  1. **Weather match.** Snow on the stream matched where Sundklakk was working (Åmot).
  2. **Flightradar24** aircraft matching. Both winners used it.
  3. Hints narrowed the area.
  4. A **field search of more than 16 hours** with about 15–20 others.
  5. **Horns and shouting** heard on the live audio for the final metres.

  Sources: [N] https://www.amta.no/fant-en-million-i-skogen-verdige-vinnere/s/5-3-1551361 and https://www.rha.no/fant-en-million-i-skogen-i-tre-tiden-horte-vi-folk-som-ropte-og-hoiet/s/5-70-476728. Dagens.no says the winner found it "using a final clue". [N] https://www.dagens.no/nyheter/breaking-fant-en-million-kroner-gjemt-i-skogen
- **Crowd method:** "Thousands followed the livestream and analysed weather, wind, bird sounds, power lines and air traffic". "Large forums worked together." [N] https://borsen.dagbladet.no/nyheter/nytt-sjokkstunt-fra-norsk-selskap/85179562 and https://sosialnytt.com/millionen-i-skogen-er-funnet-slik-klarte-de-a-lose-gaten/
- **Outcome:** Horde became Norway's most downloaded app that week, with about 50 000 new users. [N] https://www.rha.no/fant-en-million-i-skogen-i-tre-tiden-horte-vi-folk-som-ropte-og-hoiet/s/5-70-476728

---

## 3. The 2024 hunt: "Hordejakten 2024" (29 Apr – 5 May 2024)

### 3.1 Timeline
- **Mon 29 Apr 2024.** Launch.
  - Alf's TikTok "Vi har gjemt 1,1 million kr i skogen. Finneren er vinneren!" was posted 08:16 UTC. [P] https://www.tiktok.com/@alf.gunnar/video/7363199855700888864
  - The press release "1,1 million skjult i norsk natur: Hordejakten er tilbake!" went out 29 Apr 2024 at 12:35. [P] https://www.mynewsdesk.com/no/horde/pressreleases/11-million-skjult-i-norsk-natur-hordejakten-er-tilbake-3319716
  - The prize was **1 093 072 kr**, given as a **code word or password**, not cash, "for security reasons". [N] https://www.dagens.no/innland/ny-vill-skattejakt-har-nok-en-gang-gjemt-en-million-i-norsk-skog and https://cphpost.dk/2024-04-30/news/round-up/treasure-hunt-to-find-one-million-kroner-in-norwegian-forest-goes-viral/
  - Engagement "skutt i været" from the first video. [N] https://borsen.dagbladet.no/nyheter/millionjakta-er-i-gang-skutt-i-vaeret/81334871
- **Mid-hunt twist.** Horde activated a **countdown in the box** after "several days of intense searching". Hints came via the app, the newsletter, and the Horde Plus AI assistant **"Jaktus"**. [P] https://www.mynewsdesk.com/no/horde/pressreleases/spenningsnivaaet-stiger-i-hordejakten-kassen-har-begynt-aa-telle-ned-3320434
- **Fri 3 May.** Økonomiamatørene episode 175, "Hordejakten", with Alf Gunnar Andersen. [P] https://open.spotify.com/episode/178hAIH0Mcypgvvq67atBm
- **Sun 5 May, morning.** "Noen har funnet Horde-millionen i skogen". The finders had to solve the locks, and Andersen said they had not opened it yet. [N] https://borsen.dagbladet.no/studio/borsenstudio/608?post=162361
  - Horde posted "Hordejakten er ikke over!" at 11:54 UTC. The box had been found but not yet opened. [P] https://www.tiktok.com/@horde.app/video/7365482640843017505
- **Sun 5 May, afternoon.** "Tre menn fra Kongsberg ble 1 093 072 kroner rikere søndag ettermiddag." [N] https://www.laagendalsposten.no/alf-gunnar-la-ut-over-n-million-i-skauen-pa-kongsberg-i-dag-ble-pengene-funnet/s/5-64-1415829

### 3.2 Location
- **"Det hemmelige stedet i år viste seg å være ved sølvgruvene på Kongsberg."** [N] https://www.ba.no/vant-million-etter-nervedrama-i-skogen/s/5-8-2615243
- Laagendalsposten's headline: "Alf Gunnar la ut over én million i **skauen på Kongsberg**". [N] https://www.laagendalsposten.no/alf-gunnar-la-ut-over-n-million-i-skauen-pa-kongsberg-i-dag-ble-pengene-funnet/s/5-64-1415829
- **No coordinates or exact site published.** The Magnus pin at 59.668, 9.65 sits on Kongsberg town and is a placeholder. [C] `innhold.ts` L1077
- **Context for the Kongsberg silver-mine field:**
  - The field is about 30 km² of protected cultural landscape.
  - The mine entrance is at Saggrenda, 8 km outside Kongsberg town.
  - The Helgevann mines lie at about 550–650 moh.
  - The highest pit (skjerp nr. 17), south of Jonsknuten, is at 729 moh.
  - Old mining roads and trails run between the mines.
  - [N] https://norskbergverksmuseum.no/solvgruvene
  - [N] https://norskbergverksmuseum.no/helgevannsgruvene-pukkverk-og-dam
  - [N] https://norskbergverksmuseum.no/knutehavet-og-jonsknutskjerpene
  - **[I]** The exact elevation of the 2024 box is unknown. Plausible range is about 300–750 moh.
- **Access [I].** This is a tourist and cultural-heritage area with a road network and signed trails. Several finders reached the box on one Sunday morning, which fits easy access.

### 3.3 Hints and solution (2024)
- "Gjennom uka ble det delt ut små hint til deltakerne, som ledet folk stadig nærmere." [N] https://www.ba.no/vant-million-etter-nervedrama-i-skogen/s/5-8-2615243
- **The individual 2024 hint texts could not be recovered** through search summaries.
- Community summary: the hunt was solved "først etter Hordes sene, avgjørende hint og feltsøk". [C] https://github.com/mkekeoooo/hordejakten-2026/issues/9
- **Mechanics.** Finding the box was not enough; participants had to crack codes. There was a **queue system**: finders took turns at the code locks in order of arrival, and this "worked well".
  - Joakim Kristiansen "was actually the **third to arrive**". He waited and conferred with helpers by phone, and used his turn only once the code was worked out.
  - [N] https://www.ba.no/vant-million-etter-nervedrama-i-skogen/s/5-8-2615243
  - [N] https://www.kom24.no/alf-gunnar-andersen-horde-markedsforing/ny-million-gjemt-i-skogen/713720
  - [P] Horde "Jaktvettreglene 2026", per search summary: https://horde.no/gjeldfri/hordejakten/jaktvettreglene
- **Organizer reuse of 2024 numbers in 2026.** The 2026 hint "Ho Ho Hint Hint" gives **072**, the last digits of the 2024 prize, as a code fragment. [C] MagnusPladsen `innhold.ts` "hohoh"

---

## 4. 2025: no hunt
- Børsen (Sep 2026) says Horde "har tidligere arrangert pengejakten to ganger, én gang i 2023 og én gang i 2024". [N] https://borsen.dagbladet.no/nyheter/nytt-sjokkstunt-fra-norsk-selskap/85179562
- It also calls 2026 "the third time". [N] https://borsen.dagbladet.no/nyheter/anja-29-jaktes-av-hele-norge/85183299
- A "Hordejakten 2025" query returned only 2026 material.
- A community note says "people found the bookings last time", so Horde avoids cabins this year. [C] `innhold.ts` "hytte". It has no dated source. If true, it refers to 2024, when crew lodging near the site was apparently traced. That would show the crew stays close to the box.

---

## 5. Organizer statements relevant to site selection and behaviour

| Statement | Year | Source |
|---|---|---|
| Entire marketing budget in the box; aim is to spend on customers rather than Facebook/Instagram | 2023 | [N] https://inyheter.no/18/10/2023/har-gjemt-en-million-kroner-i-norsk-skog/ |
| Cash removed mid-hunt with police agreement, for participant safety | 2023 | [N] https://borsen.dagbladet.no/nyheter/vill-pengejakt-tar-grep/80370921 |
| "Hoped it would last until November" (it lasted 6 days) | 2023 | [N] https://www.kom24.no/alf-gunnar-og-kollegaene-gjemte-en-million-kroner-i-skogen-na-er-pengene-funnet/659296 |
| Feared passers-by had seen the placement | 2023 | [P via N] https://www.shifter.no/nyheter/horde-grnderen-da-million-stuntet-var-i-gang-holdt-pa-a-kaste-opp/362561 |
| Many had phoned asking for a new round, saying it was "a fun way to get out in nature", nostalgic treasure-hunt feeling | 2024 | [N] https://www.dagens.no/innland/ny-vill-skattejakt-har-nok-en-gang-gjemt-en-million-i-norsk-skog |
| Box not placed where it exposes people to danger; rule-breakers disqualified; no violence; personal attendance required; two code locks with codes in the hints | 2024 | [N] https://borsen.dagbladet.no/nyheter/ny-million-gjemt-i-norsk-skog/81303369 |
| "Hordejakten … an opportunity to get out in nature, collaborate…" | 2024 | [P] https://www.mynewsdesk.com/no/horde/pressreleases/spenningsnivaaet-stiger-i-hordejakten-kassen-har-begynt-aa-telle-ned-3320434 |
| **"Kassen står ikke i farlig terreng"**; respect private property (jaktvett rule 6) | 2026 | [P/C] https://horde.no/gjeldfri/hordejakten/jaktvettreglene; https://github.com/mkekeoooo/hordejakten-2026/issues/1 |
| Anja picked up at night (04:00, Oslo per the whiteboard) and "kjørt rundt i flere timer uten å vite hvor hun skulle ende opp. **Det var en del av opplegget**"; blacked-out windows; sleep mask and headset on the final leg; "**De tok meg med inn i skogen og bar meg**" | 2026 | [N] https://borsen.dagbladet.no/nyheter/anja-29-jaktes-av-hele-norge/85183299; https://borsen.dagbladet.no/nyheter/anja-29-snakker-ut-absurd/85185489; [C] issue #9 |
| Alf on TikTok live, 25.09: "man kanskje må **gå litt**, men **aldri noe farlig, som å krysse en elv**"; "Det er ekte lyd på streamen. Men dere husker kanskje tidligere år, da drev vi å **trollet litt med lyden**"; "Kommer en del **viktige hint** nå i løpet av **helgen**"; "Kan være at noen av kodene allerede har kommet" | 2026 | [C] MagnusPladsen `innhold.ts` L340–345; https://github.com/mkekeoooo/hordejakten-2026/issues/9 |

**Not found in any source:**
- Explicit statements about landowner permission.
- Why Tokke or Kongsberg was chosen.
- Any "near Bergen versus Østlandet" policy.

The Shifter podcast from November 2024 (https://open.spotify.com/episode/1pgCpWTv9O9VBXDunh5mDO) and the Impressions episode 239 (https://www.youtube.com/watch?v=uzEClCHmby8) may cover this, but audio and transcripts were not reachable.

---

## 6. Derived timestamps [I]

Decoded from post IDs:

| ID | Posted (UTC) | Post |
|---|---|---|
| TikTok 7290788736235785505 | 2023-10-17 05:03 | 2023 launch |
| TikTok 7292737938960534816 | 2023-10-22 11:07 | 2023 update |
| TikTok 7292963813295508769 | 2023-10-23 01:44 | Viewer "pengene er funnet" |
| TikTok 7293120639622253856 | 2023-10-23 11:52 | Horde congratulations |
| TikTok 7363199855700888864 | 2024-04-29 08:16 | Alf, 2024 launch |
| TikTok 7363578766704037152 | 2024-04-30 08:46 | "Jakten er i gang!" |
| TikTok 7364040181592116512 | 2024-05-01 14:36 | "Du vet aldri hva du treffer på #hordejakten hint?" |
| TikTok 7365418050637663521 | 2024-05-05 07:43 | – |
| TikTok 7365482640843017505 | 2024-05-05 11:54 | "Hordejakten er ikke over!" |
| X 2102086838630453645 | 2026-09-21 17:25 | MrMekker post on the 2026 launch |

**Time to find:**
- 2023: about 5.8 days, from 17 Oct about 07:00 local to 23 Oct about 01:50 local.
- 2024: about 5.9–6.0 days, from 29 Apr morning to 5 May morning.
- **Both were found in the small hours or morning of the day-6 weekend (Sunday/Monday), after a late hint.**

---

## 7. Conflicts resolved
- **"The 2023 hunt took two weeks"**, from vervekodesiden and praktiskinfo summaries, is wrong. Primary news gives Tuesday to Monday, 6 days. [N] https://www.rha.no/fant-en-million-i-skogen-i-tre-tiden-horte-vi-folk-som-ropte-og-hoiet/s/5-70-476728 ("søket varte i seks dager")
- **The 2024 prize** was 1 093 072 kr, per Laagendalsposten, Økonomiamatørene, dagens.no and cphpost. Summaries quoting 1 078 218 for Kongsberg mixed it up with 2023.
- **"Found Sunday morning" versus "richer Sunday afternoon" (2024).** The box was found in the morning, and the locks were opened and the prize won in the afternoon.
- **The 2023 "3 AM" versus "just before 02:00" timing.** The 03:00 figure refers to when shouting was heard on the stream, per rha. Børsen gives "just before 02:00" for the find. The viewer TikTok at 01:44 UTC (03:44 local) suggests the celebration was around 03:00–04:00 local. **Take roughly 02:00–03:00 local as the find time.**

---

## 8. Organizer-behaviour prior (quantitative)

Only n = 2 hunts exist, so every number below is a judgement prior. The 2026 livestream evidence (flights, sun, whiteboard) should update it separately.

### 8.1 Region (where Horde hides things)
Pattern: both sites are **inland south-eastern and south-central Norway, west or south-west of Oslo**: Vest-Telemark and Kongsberg in Buskerud. Both are **forest, not coast or high mountain**. Both are **1.5–4 h by car from Oslo (OSRM)** and **5–7 h from Bergen**. Horde is based in Bergen (5008), but **neither hunt was in Vestland.**

Prior for 2026 before the stream evidence [I]:

| Region | Probability |
|---|---|
| Innlandet (Hedmark and Oppland forest and "fjellskog") | 0.35 |
| Buskerud / Telemark / Vestfold / inland Agder | 0.30 |
| Akershus / Østfold | 0.07 |
| Vestland / Rogaland | 0.10 |
| Trøndelag / Møre og Romsdal | 0.13 |
| Nordland and further north | 0.05 |

- Innlandet gets a slight upweight. Horde tends to rotate to a new region, and the 2026 whiteboard says "fjelluft" and "lyng".
- Buskerud/Telemark/Vestfold/inland Agder still gets 0.30 because the organizers know this belt and it is close to Oslo.
- In short: **P(Østlandet + Innlandet + Telemark/Agder-inland) ≈ 0.72.**

**Drive time.** "7 hours" is not a distance statement. Alf said the detours were deliberate. Prior on OSRM drive time from Oslo:

| Drive time from Oslo | Probability |
|---|---|
| Under 2 h | 0.20 |
| 2–4 h | 0.45 |
| 4–6 h | 0.25 |
| Over 6 h | 0.10 |

### 8.2 Distance from road and walking time
- **Evidence:**
  - 2023: car horns were audible on the box microphone, 15–20 people searched at night, and the organizers themselves went in mid-hunt to swap the cash.
  - 2024: several finders reached the box on one Sunday morning.
  - 2026: Anja was carried in. The team also had to bring in the transparent box, a portable toilet, a camera, power and network. Alf says you "may have to walk a bit", but it is never dangerous and there are no river crossings. Anja writes "gikk ikke på sti, men kupert terreng".
- **Prior on walking distance from the nearest drivable road, including gravel forest roads:**

| Distance | Walking time | Probability |
|---|---|---|
| 0–300 m | – | 0.35 |
| 300–800 m | about 5–15 min | 0.40 |
| 0.8–1.5 km | – | 0.18 |
| Over 1.5 km | – | 0.07 |

- **Median about 400–500 m. P(≤ 1 km) ≈ 0.85.**
- Expect **no river or stream crossing, no cliffs, and off-trail but walkable terrain.** Access is likely via a skogsbilvei (forest road) with space to park a van or car.

### 8.3 Elevation
- **2023:** Vest-Telemark with snow in mid-October. Probably about 500–900 moh (not confirmed).
- **2024:** Kongsberg mine field, about 300–750 moh (not confirmed).
- **Neither hunt had a published elevation hint, and neither elevation is published.**
- **[I] Prior-year band, weighted: about 400–850 moh.** Horde likes "upland forest" rather than valley-floor farmland. That fits the 2026 whiteboard: "fjelluft", "lyng", "kupert", "blandet skog, høye trær".

### 8.4 Hint literalness (from what is known)

| Hint type | Known examples | Behaviour | Prior |
|---|---|---|---|
| Bare number | 2023 "2412"; 2026 "terje" → 5008 (Horde's postal code); 2026 "072" = 2024 prize digits; Kodejakten games | **Lock codes, not places** | P(code) ≈ 0.65, P(literal geography) ≈ 0.25, P(other/troll) ≈ 0.10 |
| Pictogram or wordplay | 2023 municipal arms with animal (probably Tokke's bear, unverified) | Region-level pointer | P(region-level, municipality-scale) ≈ 0.6 |
| Landscape video or photo | 2023 power-line video | Literal local feature | P(literal) ≈ 0.8 |
| Live natural signals: weather, snow, sky, aircraft | 2023 snow and Flightradar | **Were truthful and decisive in 2023** | P(truthful) ≈ 0.8 |
| Stream audio | 2023 horns and shouting were live at the end; Alf admits "trollet litt med lyden" in earlier years; 2026 audio loops 22–48 h later (default.no) | **Unreliable** | P(usable for location) ≈ 0.25 |
| Late organizer hints | Both years solved only after a late decisive hint around day 5–6 | Deliberate pacing | – |

### 8.5 Time to find
- Both earlier hunts ended on **day 6, over the weekend**, after a **late decisive hint**.
- 2026 started Mon 21 Sep, and Alf promises "viktige hint i løpet av helgen".
- **[I] Prior before the stream evidence:**

| Found by | Probability |
|---|---|
| Sun 27 Sep 23:59 | 0.55 |
| Wed 30 Sep | 0.80 |
| Later than 7 Oct | 0.10 |

- Counterweight: the 2026 design (a person in the box, three locks including one electronic 5-digit lock, and staged games) is aimed at a longer show.
- Horde underestimated the crowd in 2023 ("hoped until November").

### 8.6 Trolling
- **Confirmed:**
  - Alf admits audio trolling in earlier years.
  - The drive is deliberately obfuscated in 2026.
  - Codes are hidden in app easter eggs (terje → 5008).
- **Not seen:** false geographic hints. No source says an official hint pointed to a wrong region. Misdirection so far has been **noise** (audio, drive time), not **false statements**.
- **[I] Prior:**
  - P(an explicit official text hint is deliberately false about location) ≈ 0.1.
  - P(a sensory channel is manipulated) ≈ 0.5.

---

## 9. Implications for 2026

1. **"2,7 eiffeltårn stablet oppå hverandre"** (Horde AI's reply to "Hordeminus", which is the NORHEIMSUD → HORDE MINUS anagram).
   - **Against a literal reading:**
     - Every earlier numeric hint whose use is known turned out to be a **code** (2412; 5008; 072).
     - No earlier hunt used an elevation hint.
     - The 810/875/891 m arithmetic is the chatbot's own, not Horde's text.
   - **For a height reading:**
     - "Stacked on top of each other" describes **vertical height**, not a 4-digit string.
     - 810–891 moh matches the 2026 whiteboard ("fjelluft", "lyng") and the upland-forest pattern of earlier years.
   - **Recommendation:** use it as a **soft weight, not a hard filter**. Set P(elevation ≈ 790–910 moh) ≈ 0.40, P(lock code 0810/0891/0875 or 5-digit variant) ≈ 0.30, P(distance or other) ≈ 0.30.
   - Keep a fallback band of **about 500–800 moh**, which is where the earlier sites most likely were.
   - Test 0810, 0891, 0875 and 00810/00891 on the locks. That is cheap and settles the code branch.
2. **Road proximity is the strongest prior-year constraint.** Filter candidates to within about 1 km of a drivable road or forest road, weighted toward about 500 m or less. Also require no river crossing on the likeliest approach.
3. **Region:** do not trust the "7 h from Oslo" framing. Earlier sites were 1.5–4 h from Oslo. A 7 h drive with deliberate detours is compatible with any site 2–5 h from Oslo, which includes the Hamar–Løten–Elverum–Rena belt the 2026 community favours.
4. **Discard audio evidence.** Weight sky, weather and flights instead; these cracked 2023. Expect a decisive hint on **Sat 26 – Sun 27 Sep**.
5. **Codes:** expect codes to be spread across app easter eggs and games, some reusing earlier-year numbers. In 2024 the win went to whoever cracked the locks, not the first to arrive. Knowing the codes before arriving is decisive.

---

## 10. Known gaps
- No coordinates, elevation, parking spot or walking distance was published for 2023 or 2024. Both are known only to municipality or "near the Kongsberg silver mines" level.
- The 2024 hint list was not recoverable. horde.no and mynewsdesk are blocked, and search summaries do not quote the hints.
- There is no source on landowner arrangements or on why these regions were chosen. The podcasts (Shifter, Nov 2024; Impressions ep. 239; Økonomiamatørene ep. 148 and 175) were not reachable as text.

## 11. Source index

**Primary: Horde and Alf**
- https://www.tiktok.com/@horde.app/video/7290788736235785505
- https://www.tiktok.com/@horde.app/video/7293120639622253856
- https://www.tiktok.com/@alf.gunnar/video/7363199855700888864
- https://www.tiktok.com/@horde.app/video/7365482640843017505
- https://www.mynewsdesk.com/no/horde/pressreleases/11-million-skjult-i-norsk-natur-hordejakten-er-tilbake-3319716
- https://www.mynewsdesk.com/no/horde/pressreleases/spenningsnivaaet-stiger-i-hordejakten-kassen-har-begynt-aa-telle-ned-3320434
- https://open.spotify.com/episode/178hAIH0Mcypgvvq67atBm
- https://horde.no/gjeldfri/hordejakten/jaktvettreglene

**News, 2023**
- https://borsen.dagbladet.no/nyheter/fant-over-n-million-i-skogen/80385711
- https://borsen.dagbladet.no/nyheter/sigurd-og-hans-fant-millionen-kastet-opp/80389223
- https://borsen.dagbladet.no/nyheter/vill-pengejakt-tar-grep/80370921
- https://www.tv2.no/nyheter/innenriks/fjernet-en-million-kroner-fra-skogen/16143177/
- https://www.kom24.no/alf-gunnar-anderse-horde-markedsforing/gjemte-en-million-kroner-i-skogen-na-er-pengene-fjernet/658791
- https://www.kom24.no/alf-gunnar-og-kollegaene-gjemte-en-million-kroner-i-skogen-na-er-pengene-funnet/659296
- https://www.rha.no/fant-en-million-i-skogen-i-tre-tiden-horte-vi-folk-som-ropte-og-hoiet/s/5-70-476728
- https://www.nettavisen.no/nyheter/fant-en-million-i-skogen-verdige-vinnere/s/5-95-1408921
- https://www.ba.no/fant-en-million-i-skogen-verdige-vinnere/s/5-8-2418443
- https://www.amta.no/fant-en-million-i-skogen-verdige-vinnere/s/5-3-1551361
- https://www.ta.no/over-en-million-kroner-funnet-i-skogen-i-telemark/s/5-50-1754839
- https://www.nettavisen.no/okonomi/selskap-med-ellevilt-stunt-har-gjemt-over-n-million-kroner-i-skogen/s/5-95-1400158
- https://inyheter.no/18/10/2023/har-gjemt-en-million-kroner-i-norsk-skog/
- https://sosialnytt.com/millionen-i-skogen-er-funnet-slik-klarte-de-a-lose-gaten/
- https://www.dagens.no/nyheter/breaking-fant-en-million-kroner-gjemt-i-skogen
- https://www.shifter.no/nyheter/horde-grnderen-da-million-stuntet-var-i-gang-holdt-pa-a-kaste-opp/362561

**News, 2024**
- https://www.ba.no/vant-million-etter-nervedrama-i-skogen/s/5-8-2615243
- https://www.laagendalsposten.no/alf-gunnar-la-ut-over-n-million-i-skauen-pa-kongsberg-i-dag-ble-pengene-funnet/s/5-64-1415829
- https://borsen.dagbladet.no/studio/borsenstudio/608?post=162361
- https://borsen.dagbladet.no/nyheter/ny-million-gjemt-i-norsk-skog/81303369
- https://borsen.dagbladet.no/nyheter/millionjakta-er-i-gang-skutt-i-vaeret/81334871
- https://www.kom24.no/alf-gunnar-andersen-horde-markedsforing/ny-million-gjemt-i-skogen/713720
- https://www.dagens.no/innland/ny-vill-skattejakt-har-nok-en-gang-gjemt-en-million-i-norsk-skog
- https://cphpost.dk/2024-04-30/news/round-up/treasure-hunt-to-find-one-million-kroner-in-norwegian-forest-goes-viral/

**News, 2026**
- https://borsen.dagbladet.no/nyheter/nytt-sjokkstunt-fra-norsk-selskap/85179562
- https://borsen.dagbladet.no/nyheter/anja-29-jaktes-av-hele-norge/85183299
- https://borsen.dagbladet.no/nyheter/anja-29-snakker-ut-absurd/85185489
- https://www.ringsaker-blad.no/hele-norge-jakter-pa-anja-29-fra-brumunddal/s/80-79-13202

**Community**
- https://github.com/mkekeoooo/hordejakten-2026/issues/9
- https://github.com/mkekeoooo/hordejakten-2026/issues/1
- https://github.com/mkekeoooo/hordejakten-2026/issues/6
- https://github.com/MagnusPladsen/hordejakten-2026, `src/data/innhold.ts` @ 68faa86 (TikTok-live quote at L340–345; pins at L1076–1077); OSRM grid in `public/data/drivetime.json`

**Geography context**
- https://en.wikipedia.org/wiki/%C3%85mot,_Vinje
- https://en.wikipedia.org/wiki/H%C3%B8ydalsmo
- https://snl.no/Tokke
- https://norskbergverksmuseum.no/solvgruvene
- https://norskbergverksmuseum.no/helgevannsgruvene-pukkverk-og-dam
- https://norskbergverksmuseum.no/knutehavet-og-jonsknutskjerpene
