# Hordejakten 2026: public web coverage (web-2026 sweep)

*Compiled 2026-09-25, late evening CEST (the latest source is dated 23:59:33 CEST).*

## How this sweep was done

- **WebSearch:** 36 queries succeeded, in Norwegian and English. The session's shared budget of 200 searches then ran out, and queries 37–39 were refused. The list of queries is in §12.
- **WebFetch:** worked only on `github.com`. `default.no` was tried once, because the user explicitly asked for it to be read, and it returned `EGRESS_BLOCKED`.
- **Direct `curl`:** refused with 403 for `api.github.com`, `github.com` HTML pages and `github.com/user-attachments`. `git clone` of public repos worked.

**Reliability warning.** Most of the web material below reaches us as **a search engine's summary of a page**, not the page itself. I could not open horde.no, borsen.dagbladet.no, ringsaker-blad.no, praktiskinfo.no, skattejakthint.no, vervekodesiden.no, TikTok, X, Facebook or default.no.

- Words that the summaries attribute to a page are given here as **"search-summary paraphrase"** unless the snippet itself was a verbatim title or quote.
- Treat every such item as one step removed from the source, and never as a verbatim quote.
- The search summariser also mixes years. Horde reuses `horde.no/gjeldfri/hordejakten` every year, so the index still holds 2023 and 2024 text (see §9).

**Evidence classes:**

| Tag | Meaning |
|---|---|
| **[P-org]** | Organizer, meaning Horde or Alf Gunnar Andersen |
| **[P-app]** | Horde app or Horde web page |
| **[P-wb]** | Anja's whiteboard |
| **[P-stream]** | What can be seen or heard on the stream |
| **[N]** | News outlet reporting |
| **[C-obs]** | Community observation |
| **[C-int]** | Community interpretation or theory |
| **[M]** | Model output: default.no fusion, or Claude/Codex pipelines |

"via search" means the item was seen only through a search-result summary.

Times are CEST unless marked Z. **Stream time** is the clock read off the YouTube stream. **Real time** is wall-clock time.

---

## 0. Key takeaways

1. **Status on the evening of 25.09:** no public source says the box has been found or opened.
   - mkekeoooo's README at 23:59 CEST 25.09 still says «Ingen plassering eller region er bekreftet».
   - The latest organizer statement found is second-hand: Alf on TikTok live, 25.09, said important hints are coming "i løpet av helgen", i.e. 26–27.09.
   - No news story on a find was indexed.
2. **Anja is now identified by the press.** Børsen (Dagbladet) names her as **Anja Nymoen Søberg (29)**, a *stuntkvinne* (stunt woman) from **Brumunddal** (Ringsaker, Innlandet) who trained at the **International Stunt Academy in Sør-Odal**.
   - Ringsaker Blad ran «"Hele Norge" jakter på Anja (29) fra Brumunddal».
   - Sources: [N] https://borsen.dagbladet.no/nyheter/anja-29-jaktes-av-hele-norge/85183299 and https://www.ringsaker-blad.no/hele-norge-jakter-pa-anja-29-fra-brumunddal/s/80-79-13202 (via search).
   - This supplies the source that `places_codes_news.md` §3 found missing for the community's "Anja er fra Brumunddal" tip (magnus `innhold.ts:1279-1283`).
   - It **conflicts** with the Discord-relayed gesture reading "She is Anja from Oslo" on default.no (§6). The two can be reconciled: she was picked up in Oslo and grew up in Brumunddal.
3. **What Anja can see.** Børsen, via search: her only contact with the outside world is **the team outside the glass box and an iPad that shows the comment section under the livestream** [N].
   - So her whiteboard answers are replies to chat questions she reads on the iPad.
   - This is consistent with Horde's «Anja er på publikums lag» (magnus `innhold.ts:697-703`).
4. **Hand-signal protocol reported by Børsen** (via search, «Nytt sjokkstunt fra norsk selskap»): she makes hand signals in answer to viewers. The example given is to **form a triangle with her hands if she sees mountains ("fjell"), or cross her arms behind her head if she does not.**
   - The search summary does **not** say which answer she gave. This is an open question (§11).
5. **Official rules found on horde.no** (via search; `/vilkaar`, `/jaktvettreglene` and the main page):
   - Participation is free.
   - The prize is paid by transfer to the winner's account after the campaign, "regardless of debt".
   - Until the competition is officially concluded, the prize money stays Horde's property, and **only Horde** decides and confirms the winner.
   - Horde may end or interrupt the hunt at any time.
   - The box is **video-monitored on location and streamed** at horde.no/gjeldfri/hordejakten.
   - Horde may publish the winner's **first name, age and municipality**.
   - The box is **not in dangerous terrain**.
   - Stay away from anyone who sells hints or codes.
   - Hints come via the **app, newsletter and Horde Plus**.
   - **No minimum age was found** in any snippet.
   - Queue and **5-hour quarantine**: this rule comes only from Alf's TikTok live on 25.09, relayed second-hand in chat (magnus `innhold.ts:330-335`). No web page confirming it was indexed.
6. **Newer default.no content, via the search index.** The search engine indexed a default.no version whose report body was generated **2026-09-25 03:27 Europe/Oslo**, with log updates at 02:36:14 and 03:21. The local mirror is from 24.09 18:36.
   - Best guess: «**Glomma-dalen between Rena and Evenstad (61.35–61.47 N, 10.97–11.15 E)**, where the fusion places **24 % of all probability within 25 km**, more than three times the next area.» [M]
   - The local 24.09 18:31 mirror had **28.9 %** within 25 km of 61.45/11.10 (`defaultno_mirror.md` §0).
   - Audio: «video is live (frames differ), but sound is canned». By 22.09 13:50 there were **55 replay blocks, 198 min in total**, verified by waveform.
   - TavlAI (the whiteboard reader) found **0 boards in 367 chat-cued daylight frames** at confidence 0.10.
   - A Discord-relayed gesture reading: «She is Anja from Oslo, picked up in Oslo; 7+ h by car, mostly flat, winding, no ferries; departed before 21 Sept» (flagged by default.no as "unverified but consistent").
   - Full details are in §6.
7. **mkekeoooo has two commits after the local mirror** (b067a04 at 23:23 and ea842e4 at 23:59 CEST, 25.09). The README now says:
   - **Direct sun around 17:00 CEST on 25.09** was documented by both Codex and Claude, and «Antakelsen om en helt overskyet ettermiddag er trukket tilbake» — a **retraction**.
   - A **sun star** (solstjerne) was also seen on **23.09 at 16:45 and 16:50 CEST**.
   - The satellite comparison «velger foreløpig ingen region, og Østerdalen er ikke utelukket».
   - New proposal (not a ranking): **Engerdal–southern Femund and Solør/Finnskog**.
   - Full text is in §7.
8. **No 2026 coverage was found** from VG, NRK, E24, TV 2, Østlendingen, Hamar Arbeiderblad or GD. **No 2026 Horde TikTok, Instagram or Facebook post was indexed.** Every Horde or Alf TikTok the search returned decodes to **2023 or 2024** (§5). The only indexed 2026 social post is an X post by "Mr. Mekker" at 21.09 19:25:31 CEST.
9. **Hint aggregators exist and one is paywalled.**
   - **skattejakthint.no** sells access to "all hints" from 95 kr, with 12 hints behind a paywall.
   - **praktiskinfo.no/hordejakten-2026** and **vervekodesiden.no/blogg/hordejakten-2026** are free summaries.
   - Horde's own terms warn against anyone who *sells* hints or codes. That warning is aimed at code or hint sellers, and skattejakthint says it compiles public hints.
   - None of these could be opened.

---

## 1. Official Horde sources (horde.no), via search

| URL | Title (as indexed) | Content (search-summary paraphrase unless quoted) | Class |
|---|---|---|---|
| https://horde.no/gjeldfri/hordejakten | «Hordejakten 2026 - Horde» (an older index copy is titled «Hordejakten 2024 er i gang!») | Start 21.09.2026. Participation is free. Horde transfers the amount to the winner's account after the campaign, **regardless of debt**. Hints come via the Horde app and other channels (newsletter, Horde Plus). The box is not in dangerous terrain. If anyone offers hints or codes for payment, stay away; Horde takes no responsibility for agreements between participants. **The summariser also gave the prize as "1,093,072 kroner". That is the 2024 prize and comes from a stale index copy** (see §9). | P-app |
| https://horde.no/gjeldfri/hordejakten/vilkaar | «Kampanjevilkår for Hordejakten - Horde» | Starts 21.09.2026. Taking part means accepting the terms. Until officially concluded, the prize money remains Horde's property, and only Horde can determine and confirm the winner. Horde can end or interrupt at any time "for various reasons, including security concerns, legal violations, or unforeseen events". Horde may use images, video and other content, "including recordings from the location", for marketing during and after. Horde may process participants' personal data through recordings from the location, and may share the winner(s)' **first name, age and municipality**. "The box is video monitored on location and streamed directly on the website horde.no/gjeldfri/hordejakten." | P-app |
| https://horde.no/gjeldfri/hordejakten/hvorfor | «Hvorfor vi gjør Hordejakten – Hordejakten 2026 - Horde» | Goal: break the stigma of debt by making visible the number of people with interest-bearing debt. Economy and mental health are connected ("loneliness, shame and worries that never let go, 24/7"). **Together with Mental Helse.** "To symbolize this, they placed Anja in a transparent box with 1,116,897 kroner – the amount corresponding to the number of people with interest-bearing consumer debt." Previous hunts showed "trust, cooperation and friendship … people share hints, solve tasks, and help each other". | P-app |
| https://horde.no/gjeldfri/hordejakten/jaktvettreglene | «Jaktvettreglene 2026 - Horde» | Text not returned by search. Local mirror quotes: «Ingen på Hordekontoret vet hvor kassen befinner seg. Det er kun de som er på stedet med Anja som vet noe. De får du ikke tak i.» and «Ikke kle deg ut som elg, hjort eller storfugl. Det er jaktsesong.» (magnus `innhold.ts:673-686`). Rule 4 is about a charged phone and a powerbank (`innhold.ts:463-467`). | P-app (local) |
| https://horde.no/artikler/hordejakten-2026 | «– En tydelig sammenheng - Kampanjer - Horde» | Title only. It is probably an article about the link between economy and mental health. | P-app |
| https://horde.no/jakten/components/QuestionSection/ | «Hordejakten 2026 - Horde» | An indexed component path, suggesting an FAQ ("QuestionSection") on horde.no/jakten. No content was returned. | P-app |
| https://horde.no/secret/kodejakten | (from the local mirror) | Four mini-games. When all are cleared, the page says «Låsen er åpen: dette er koden til den ene hengelåsen på kassen». The server answered `not_configured` (503) as of 23.09 (magnus `innhold.ts:704-712`). | P-app (local) |
| https://horde.no/blogg/slik-ser-en-droy-million-i-skogen-ut/ | «Slik ser en drøy million i skogen ut - Kampanjer - Horde» | 2023 blog post. | P-app (prior year) |
| https://horde.app/vilkaar/ | «Vilkår – Horde» | General app terms. Not hunt-specific. | P-app |

**Organizer channels found:**

- Horde TikTok: `@horde.app`
- Alf TikTok: `@alf.gunnar`
- Alf on X: `@AlfG86` (https://x.com/AlfG86)
- Alf on Instagram: `@alf.gunnar` (https://www.instagram.com/alf.gunnar/)
- Horde on Facebook: https://www.facebook.com/horde.no/, including the video «Tips og hint om Hordejakten» (https://www.facebook.com/horde.no/videos/tips-og-hint-om-hordejakten/415958894406552/). The year of that video is unknown, because its ID cannot be decoded to a date.
- YouTube stream: https://www.youtube.com/watch?v=EQHgfmZicc8
- Older YouTube videos: «Hordejakten - Jakten på gjeldfriheten» (https://www.youtube.com/watch?v=tWoD9d4eFII and https://www.youtube.com/watch?v=ThO-OsWvoL8), and «Trenger du et hint?» (https://www.youtube.com/watch?v=H_-0LbPSu5s), which magnus also links.

**Alf Gunnar Andersen:** CEO and founder of Horde. The app has "over 300,000 users" (search summary of his speaker page, https://www.norwayfintechfestival.no/2026/speakers/alf-gunnar-andersen.). Podcasts:

- Økonomiamatørene ep. 175 «Hordejakten» (2024): https://open.spotify.com/episode/178hAIH0Mcypgvvq67atBm
- Shifter «Horde-gründer Alf Gunnar Andersen om å bygge selskap og plassere en million kroner ute i skogen»: https://open.spotify.com/episode/1pgCpWTv9O9VBXDunh5mDO

Both are prior-year material. The search also named "Torstein Nyhammer Mellingen" and "Jan Tore Kristoffersen" alongside Alf, but the context was the 2024 prize of 1,093,072 kr, so their 2026 role is unknown.

---

## 2. News coverage of 2026 (all via search; articles not opened)

### 2.1 Børsen / Dagbladet: «Nytt sjokkstunt fra norsk selskap»

URL: https://borsen.dagbladet.no/nyheter/nytt-sjokkstunt-fra-norsk-selskap/85179562. The indexed title variant is «Hordejakten 2026: Kvinne gjemt med 1,1 millioner».

What the article reports [N]:

- A woman is locked in a transparent box at a secret location in Norway while strangers look for her and 1.1 million kroner.
- **Hand signals:** "The woman follows instructions from a livestream to help viewers by making hand signals based on terrain, such as forming a triangle with her hands if she sees mountains, or crossing her arms behind her head if she doesn't." This describes a stream exchange [P-stream as reported by N]. The answer she gave is **not** in the snippet.
- Horde works with **Mental Helse**. Horde says it takes care of her, that she had a **psychological evaluation beforehand**, and that "all her needs are met, including psychological".
- Horde has run the money hunt twice before, in 2023 and 2024. Prior-year context: "Thousands followed the livestream and analysed weather, wind, bird sounds, power lines and air traffic".
- The summariser also said "Horde placed a box with over one million kroner in the forest **on Tuesday**". That is **probably the 2023 back-story**, when the box went out on a Tuesday. 21.09.2026 is a **Monday**, and the stream started 21.09 ~06:50. Do not use this as a 2026 fact.

### 2.2 Børsen: «Aner ikke hvor hun er: – Anja (29) jaktes av «hele» Norge»

URL: https://borsen.dagbladet.no/nyheter/anja-29-jaktes-av-hele-norge/85183299

What the article reports [N]:

- The woman is **Anja Nymoen Søberg**, a stunt woman from **Brumunddal**, "selected by the company Horde".
- She trained at the **International Stunt Academy in Sør-Odal**.
- **Alf Gunnar Andersen:** she "was picked up in the middle of the night and driven around in a car with **blacked-out windows** before being placed in the box, so she doesn't know where she is."
- The local mirror quotes the same article: «kjørt rundt i flere timer uten å vite hvor hun skulle ende opp. Det var en del av opplegget» (mkekeoooo issue #9; `prior_years_early.md:165`).
- **"Anja's only contact with the outside world is the team outside the glass box and an iPad screen showing the comments section under the livestream."**
- The article calls it a PR stunt by "finance and loan company Horde". Participants must find both the glass box and the code combination.
- "The company states that **months of planning** went into the event, regarding security, location, and implementation." This came from a VG-oriented query summary that cited Børsen, so its exact article is uncertain.

### 2.3 Børsen: «Hordejakten: – Anja (29) snakker ut: – Absurd»

URL: https://borsen.dagbladet.no/nyheter/anja-29-snakker-ut-absurd/85185489. It is dated 22.09 per magnus (`innhold.ts` hint `reise`).

What the article reports [N]:

- Anja "has been sitting in a glass box **since Monday morning**".
  - Monday is 21.09, and the stream started ~06:50, so this is **consistent** with the stream start.
  - It does not by itself contradict the whiteboard «OSLO, SØN KL 04.00», which is a pickup time, not a box-entry time.
- Most absurd to her: people follow her around the clock. She woke at night and realised people were watching her sleep, with the chat still going.
- Positive comments are the majority. People show concern and encouragement, and that motivates her.
- "Picked up in the middle of the night, driven around for several hours, then placed at a secret location."
- Her own words, as quoted in community sources: «De tok meg med inn i skogen og bar meg. Jeg så ingenting og hørte ingenting.» (search summary of mkekeoooo issue #6/#9; magnus hint `terreng`).

### 2.4 Ringsaker Blad: «Brumunddal, Arbeidsliv | «Hele Norge» jakter på Anja (29) fra Brumunddal»

URL: https://www.ringsaker-blad.no/hele-norge-jakter-pa-anja-29-fra-brumunddal/s/80-79-13202

- Anja, 29, from Brumunddal, "is lying in a glass booth somewhere in Norway, and those who find her win a good sum of money" [N, local].
- The metadata said the article was "about three days old" when indexed, i.e. about 22–23.09.

### 2.5 Other outlets

- **Searched, but no 2026 story indexed:** VG, NRK, E24, TV 2, Østlendingen, Hamar Arbeiderblad, Gudbrandsdølen Dagningen. Also no *finansavisen* story, although finansavisen.no/tema/norge appeared as a generic hit.
- **Returned, but prior-year only:**
  - https://www.ba.no/vant-million-etter-nervedrama-i-skogen/s/5-8-2615243 («Vant million etter nervedrama i skogen»)
  - https://www.nettavisen.no/nyheter/fant-en-million-i-skogen-verdige-vinnere/s/5-95-1408921
  - https://www.kom24.no/alf-gunnar-anderse-horde-markedsforing/gjemte-en-million-kroner-i-skogen-na-er-pengene-fjernet/658791 (2023, cash removed mid-hunt)
  - https://gjerrigknark.com/Konkurranser/Penger-bonus-og-gavekort/Finn-og-vinn-kassen-med-over-en-million-kroner-i-skogen

---

## 3. Community and aggregator pages on the web (not openable)

| URL | What the search says | Class |
|---|---|---|
| https://praktiskinfo.no/hordejakten-2026/ | «Hordejakten 2026: hint, regler og premie». Content was not returned. mkekeoooo/`prior_years_early.md:202` notes that praktiskinfo's claim "the 2023 hunt took two weeks" is wrong (it took 6 days). | C |
| https://skattejakthint.no/ | «Hint til Hordejakten 2026: alle hint samlet på ett sted». Collects all hints with sources, solutions and notes, and is updated continuously. A free sample is available, with **12 hints behind a paywall**, **from 95 kr**. One payment covers all hints, including later ones. | C (commercial) |
| https://vervekodesiden.no/blogg/hordejakten-2026 | «Hordejakten 2026 – slik finner du kassen med 1 116 897 kr». The summary says: "Without codes from the Horde app, you cannot open the box even if you find it." | C |
| https://x.com/MrMekker/status/2102086838630453645 | Verbatim snippet: «Kom over en kul konkurranse! HORDEJAKTEN Økonomi-appen Horde har gjemt en gjennomsiktig kasse i skogen et sted i Norge. Inni sitter en ekte kvinne + premie på 1 116 897 kr. Tallet tilsvarer antall nordmenn med rentebærende forbruksgjeld. Kvinnen skal symbolisere å være «fanget…». The snowflake ID decodes to **2026-09-21 17:25:31 Z = 19:25:31 CEST**. | C |
| https://default.no/ , https://default.no/index.php , https://default.no/map.php | «Hordejakten 2026 · open-data search log» and «Hordejakten 2026 · kartet». See §6. | C-obs / M |
| https://discord.gg/ETKzsk4xU | Discord invite used by the magnus map (`src/components/Discord.tsx:5`). | C |
| https://discord.com/invite/RpzHG3yvXG | «Join the HORDE Discord Server!», about 9,077 members. **Probably unrelated** to Horde AS (it looks like a gaming "HORDE" server). | — |
| https://github.com/fordelabs/hordejakten | New repo, created 2026-09-25 15:14:26Z. **Empty**: I cloned it and it has no commits. | — |
| https://github.com/danielmb/hordejakten | JavaScript repo from 2023-10-19, from the 2023 hunt. | prior year |

---

## 4. Rules, timeline and status, consolidated from the web

| Item | Value | Source | Class / confidence |
|---|---|---|---|
| Start | 21.09.2026. The stream started ~06:50 on Monday 21.09. | horde.no/…/vilkaar (search); task background | P-app, high |
| End | "Lasts until someone wins" | skattejakthint / X / praktiskinfo summaries | C, high |
| Cost | Free | horde.no/gjeldfri/hordejakten (search) | P-app, high |
| Prize | 1 116 897 kr, equal to the number of Norwegians with interest-bearing consumer debt. Paid by transfer after the campaign, "regardless of debt". No physical cash in the box (vilkår, via magnus). | horde.no/…/hvorfor; main page; magnus `innhold.ts:689-695` | P-app, high |
| Winning | Find the box, open all locks with codes from the app, and follow the instructions in the envelope in the box. First to open all locks wins; **arriving first does not guarantee winning** (magnus interpretation of vilkår). | magnus `innhold.ts:689-695`; X/Børsen summaries | P-app via C, med-high |
| Queue and 5 h quarantine | «Det blir kø hvis flere kommer samtidig, og 5 timers karantene hvis du ikke får åpnet kodene.» | Alf, TikTok live 25.09, relayed in chat (magnus `innhold.ts:330-335, 1633`), «ikke sjekket ordrett». Not found on the web. | P-org second-hand, medium |
| Winner confirmation | Only Horde decides. Prize money stays Horde's property until officially concluded. | vilkår (search) | P-app, high |
| Early stop | Horde may end or interrupt the hunt (security, law, unforeseen events). | vilkår (search) | P-app, high |
| Publicity | Location recordings used in marketing. Winner's first name, age and municipality may be published. | vilkår (search) | P-app, high |
| Monitoring | "The box is video monitored on location and streamed directly on horde.no/gjeldfri/hordejakten" | vilkår (search) | P-app, high |
| Safety | Box not in dangerous terrain. Alf 25.09: «man kanskje må gå litt, men aldri noe farlig, som å krysse en elv» | main page (search); magnus `innhold.ts:344` | P-app high; P-org second-hand |
| Hunting season | «Ikke kle deg ut som elg, hjort eller storfugl. Det er jaktsesong.» Alf: «husk at det er jaktsesong, og gå i tydelige klær» | Jaktvettreglene (magnus `innhold.ts:681-686`); magnus `innhold.ts:1635` | P-app / P-org |
| Paid hints | "If anyone offers hints or codes for payment, stay away" | main page (search) | P-app |
| Age limit | **Not found** in any indexed snippet | — | open |
| Hint channels | App, newsletter, Horde Plus. Also the stream, whiteboard and TikTok. «Hint til hva kodene kan være ligger i appen 💙» (Horde comment, 24.09) | main page (search); magnus `innhold.ts:348-355` | P-app / P-org |
| Organizer's knowledge | «Ingen på Hordekontoret vet hvor kassen befinner seg …» | Jaktvettreglene (local) | P-app |
| Anja's communication | «Anja er på publikums lag. Hun har ikke fått noen føringer fra Horde om hva hun kan, eller ikke kan si.» She sees chat on an iPad (Børsen). | horde.no "Derfor gjør vi dette" (magnus `innhold.ts:697-703`); Børsen | P-app; N |
| Next hints | «Kommer en del viktige hint nå i løpet av helgen.» | Alf, TikTok live 25.09, second-hand (magnus `innhold.ts:344`) | P-org second-hand |
| Status 25.09 evening | Not found or not opened, as far as any indexed source says. mkekeoooo README at 23:59: no location or region confirmed. The search summary "Hordejakten dag 5": "No finds after five days is normal." | web_mk `README.md` @ ea842e4; mkekeoooo issue #9 | C, high that no public report of a find exists |

**Prior-year durations** (from mkekeoooo issue #9 via WebFetch; details in `prior_years_early.md`):

- **2023:** Vinje/Tokke border, found in the night of day 6.
- **2024:** «sølvgruvene i Kongsberg» (Kongsberg silver mines), found on a Sunday morning.

In both years the find came after Horde's late decisive hints and a field search.

---

## 5. Social posts and their decoded dates

Every Horde or Alf TikTok the web search returned is from a **prior year**. The IDs are decoded as `id >> 32` giving Unix seconds:

| TikTok ID | Account | Decoded (UTC) | Caption (snippet) |
|---|---|---|---|
| 7290894903142288672 | @horde.app | 2023-10-17 11:55:53 | «Finn og vinn pengene. Følg hintene våre, og du kan finne og vinne drøye 1 million kroner! … Første til mølla vinner (dere kan jobbe i team) Se pengene live på streamen» |
| 7290992706124401952 | @alf.gunnar | 2023-10-17 18:15:24 | «Les regler og vilkår på horde.no/jakten. Hint kommer gradvis i app, nyhetsbrev og Horde.plus» |
| 7293120639622253856 | @horde.app | 2023-10-23 11:52:52 | «Øyeblikket og følelsen når du finner millionen i skogen! Vi gratulerer til Hans Inge og Sigurd …» |
| 7363954970053315873 | @horde.app | 2024-05-01 09:06:15 | «Har du Horde-appen, kan du finne kassen! #hordejakten» |
| 7363976395694886177 | @alf.gunnar | 2024-05-01 10:29:24 | «#hordejakten» |
| 7364040181592116512 | @horde.app | 2024-05-01 14:36:55 | «Du vet aldri hva du treffer på #hordejakten hint?» / «Spennende hints for Hordejakten» |

The one 2026 social post indexed is the X post by @MrMekker, 2026-09-21 19:25:31 CEST (§3). **The 25.09 TikTok live by Alf was not indexed.** Its content is known only from the chat relay in magnus `innhold.ts:330-345, 1626-1636`.

---

## 6. default.no content recovered through the search index (version 25.09 ~03:27)

default.no is blocked from this machine, and WebFetch returned `EGRESS_BLOCKED`. However, the search engine has indexed `https://default.no/`, `https://default.no/index.php` and `https://default.no/map.php`. The summaries below come from that index.

- **Version:** «last updated on 2026-09-25 at 02:36:14 and 03:21, with the report body generated on 2026-09-25 at 03:27 Europe/Oslo».
- This is **about 9 hours newer** than the local mirror (24.09 18:36, `defaultno_mirror.md`).
- All of it is **community observation or model output**, relayed by a search summariser, so the relay loss is double.

### 6.1 Headline and fusion [M]

- «The best guess is **Glomma-dalen between Rena and Evenstad (61.35–61.47 N, 10.97–11.15 O)**, where the fusion analysis places **24 % of all probability within 25 km** — more than three times the next area.»
  - Compare the local mirror at 24.09 18:31: top cell 61.45 N 11.10 E, p = 0.127, **28.9 %** within 25 km.
  - So by 03:27 the concentration had **fallen** from about 29 % to 24 %, but the area remained first.
- **Contradiction:** mkekeoooo issue #5 (25.09, time unknown) says default.no's "Best guesses" now rank **60.70, 11.60** (south) and **60.95, 11.30** (Løten) above Evenstad. Issue #1 says default.no's best guesses "have shifted positions since initial analysis". This cannot be resolved without seeing default.no. The two statements may refer to different ranked lists: the fusion mass versus a "best guesses" list.
- Scoring: «The "abs" score equals score × fusion mass of the area, comparable across areas.»
- «Within ±60 s Østerdalen stays best». This is a robustness check of the aircraft-timing term against stream-delay uncertainty [M].

### 6.2 Map layers (map.php) [M/C-obs]

- **Terrain:** 800–900 moh (orange) and 780–920 (yellow). This is the "2,7 eiffeltårn" = 810/891 m band.
- **Berries:** cloudberry and lingonberry (red) and blueberry (blue). Red = dense; dots = individual finds when zoomed in.
- **Distance from roads:** the summariser wrote «780–920 meters from nearest drivable road (red) or public road (yellow)». This is **likely garbled**: it conflates the elevation band with the road-distance layer. Do not use it.
- **Route probability:** red = best 2 % of routes, orange = top 15 %, yellow = top 40 %.
- **Accommodation:** orange = occupied now (Inatur), dark grey = not bookable online, black = closed (DNT), green = available/rental, blue = tourist cabin.
- «Hordes hint are placed on the map as open data.» Data sources: MET, Kartverket, NIBIO, NGU, OSM, adsb.lol, GBIF, NASA (GIBS), EUMETSAT.
- Services listed: a timelapse of every minute; every minute of the stream playable; all aircraft clips with spectrograms and voting; satellite passes; raw data files; `osint_notes.md` («Hordejakten 2026 – OSINT notes», "a living file").

### 6.3 Audio [C-obs]

- «Audio was found to be partly a replay on 22.09 around 13:15, after fingerprinting all 30 hours of stream audio.»
- Sample-level check: «22.09 11:02:40 identical to 21.09 11:09:13, waveform correlation 0.999».
- Replay blocks:
  - «22.09 10:26–13:00 replayed 21.09 10:33–15:00 in pieces with various lags»
  - «22.09 08:24–08:32 and 09:43–09:48 replayed 22.09 06:30–07:00»
- «By 13:50, **55 replay blocks totaling 198 minutes** had been waveform-verified.»
- «Video is live (frames differ), but sound is canned.» «Sound-based evidence after 22 Sep 06:30 is ignored.» «The audio track is not used in any calculations.»
- The local mirror has other examples at corr 0.993–0.999 (`defaultno_mirror.md:1154`).
- Organizer counterpoint, second-hand: Alf said «Det er ekte lyd på streamen» but also «tidligere år … trollet litt med lyden». That is compatible with real sound that was recorded and is replayed.

### 6.4 Aircraft 21.09 [C-obs]

- «A "rumble detector" recorded an overflight at 21:33:12, detected as the plane she saw at 21:29»
- «seen (board FLY 21:30) and heard (rumble peak 21:33:20 stream)». Event window 21:29–21:34.
- «Østerdalen west side (Elverum–Rena–Koppang) was under the airway NOZ56U/NOZ9EG during this plane sighting event.»
- **Caveat:** the rumble at 21:33 is on the evening of 21.09. That is **before** default.no's audio cut-off (22.09 06:30), so default.no's own rule does not exclude it. It is still unproven that the 21.09 evening audio was live and not replayed.

### 6.5 Chat and gesture relay, 21.09 [C-obs, unverified]

- «According to crowd-read gestures relayed on Discord on 2026-09-21 (**unverified but consistent**): "She is Anja from Oslo, picked up in Oslo; 7+ h by car, mostly flat, winding, no ferries; departed before 21 Sept."»
- «Sigdal check» 21.09 15:30. Chat prompts:
  - «Sigdal? stand up» at 15:15
  - «Buskerud? hop 5×» at 15:18
  - «she stood up around 15:19:36»
- The outcome of the Sigdal/Buskerud test is ambiguous. Standing up four minutes after a prompt, with a second prompt in between, is weak evidence. mkekeoooo issue #1 also lists "7+ hours by car" as having a gestural and disputed origin.
- **Conflicts:**
  - "7+ h by car" vs Anja on the whiteboard: she slept and does not know how long they drove.
  - "7+ h by car" vs Alf: «kjørt rundt i flere timer … del av opplegget».
  - "from Oslo" vs Børsen: "from Brumunddal".

### 6.6 TavlAI and night camera [C-obs]

- «TavlAI … finds **0 boards in 367 chat-cued daylight frames** at confidence 0.10» ("daylight blindness"). «**120 daylight frames were queued for hand labelling** to retrain.»
- **Implication:** default.no's automatic whiteboard log is **incomplete in daylight**. This matches mkekeoooo issue #6 on missing and shortened whiteboard hints (§7.2).
- IR camera: one search summary said the page tracks «when infrared was switched off at **08:00:19** and back on at **18:30**». A second, targeted query said this was *not* found. **Low confidence.** The local `hints_a.md:121` shows some daytime whiteboard captures on 25.09 are IR greyscale frames.

### 6.7 Weather [C-obs/M]

- «Weather data from 400 stations and live MET data with 193 points showing rain and temperatures 0.9–15.5 °C». The time of that snapshot is unknown.
- Sun/camera items mention «17:23 evening sun» and «10:30 morning sun». The latter may be garbled; the local and mkekeoooo sun times are 07:44–07:51.
- The local mirror has the "dry camera glass while 796 of 831 stations got rain" item (`defaultno_mirror.md` §0 item 4).

---

## 7. GitHub web content not in the local mirrors

### 7.1 mkekeoooo/hordejakten-2026: commits after the local mirror

The local mirror is at `d1fbac0` (25.09 04:43 -0700 = 13:43 CEST). A fresh clone in scratchpad (`web_mk`) has:

- **b067a04** 2026-09-25 **23:23:21** +0200, «Dokumenter solobservasjon 25.09 og nytt landsøk» (README, +33/−28)
- **ea842e4** 2026-09-25 **23:59:33** +0200, «Dokumenter ny solobservasjon 23.09 og sammenligning av soldager» (README, +2)
- On the bevis branch: **e8178da** 2026-09-25 13:57:01 -0700, «Solkart 25.09 14:30–15:10Z: klart/sky mot klarværsbasis + MTG cloudtype/truecolour (#10)». This may already be in the local `mk_bevis`; check.

README at ea842e4, verbatim:

> **Ny originalkontroll: solstjerne også 23.09 kl. 16.45 og 16.50 CEST.** Codex har kontrollert seks bilder fra to minuttklipp. Sammenligningen med 25.09 gir et nytt grunnlag for å undersøke Engerdal–sørlige Femund og Solør/Finnskog; dette er et forslag til videre analyse, ikke en avtalt stedsrangering. [Resultater og svar til Claude · #10](https://github.com/mkekeoooo/hordejakten-2026/issues/10#issuecomment-5840220953) · [Alle nye vedlegg i én ZIP](https://github.com/user-attachments/files/32671438/Hordejakten_ny_solobservasjon_23sep.zip)
>
> **Ny avklaring 25.09: Direkte sol rundt kl. 17.00 CEST er dokumentert av både Codex og Claude.** Antakelsen om en helt overskyet ettermiddag er trukket tilbake. Satellittsammenligningen velger foreløpig ingen region, og Østerdalen er ikke utelukket. Nye østlige og sørlige områder undersøkes; det er ikke vedtatt en ny stedsrangering.
>
> [Solobservasjon og landsøk med satellittparallakse · #10](https://github.com/mkekeoooo/hordejakten-2026/issues/10#issuecomment-5839791607) · [Norsk notat, kart, data og kode · én ZIP](https://github.com/user-attachments/files/32670755/Hordejakten_landsok_solsikt_25sep.zip)

Notes:

- The sun observations are [P-stream as observed by C]: sun visible at ~17:00 on 25.09, and a sun star at 16:45 and 16:50 on 23.09.
- The regional suggestion is [C-int].
- **Retraction:** «Antakelsen om en helt overskyet ettermiddag er trukket tilbake».
- The two ZIPs could not be downloaded (403 from the proxy), and the issue #10 comments were not returned by WebFetch.
- The rest of the README is unchanged apart from whitespace. It still says «Status 25. september 2026: Ingen plassering eller region er bekreftet».

### 7.2 mkekeoooo issues (WebFetch of github.com, bodies only; comments not rendered)

**#1 «Samlesak: uavhengig revisjon 25.09 og debatt Claude ↔ ChatGPT»:**

- Confirms sun angles for 21.09: 07:51 (az 98.8°, el 5.7°) and 17:23 (246.6° / 12.8°).
- Corrections:
  - Direct sun first hit «upper crown and stems» at ~07:44–07:47, not the ground at 07:51.
  - Temperature must not be a hard filter.
  - The 130° road-direction vector mixes reference frames; ~94° was found.
  - "Most hits" is a baseline artefact.
  - Tree-crown shadows of 15–20 m reach 150–200 m at those sun angles.
- Unverified items listed:
  - original video (only default.no clips were used)
  - 22.09 aircraft data
  - the origin of "7+ hours by car"
  - "Olive oil prize inscription details"
  - "**Anja's September 25 TikTok statements**"
- Proposes southern Messelt at #2.

**#2 «Morgensol: Jernvinneveien (5) står bak en ås kl. 07.45–08.14, og kronetesten skiller ikke»:**

- Terrain horizons: 5a 8.4° at az 98.8° (sun clears ~08:14), 5b 7.3° (~08:05), 5c 6.6° (~07:58).
- Sun elevation 21.09: «07.44 4,96° · 07.47 5,30° · 07.51 5,7° (98,8°)».
- Crowns lit 07:44–07:49 (5.0–5.5°); ground not lit until ~08:00.
- «Jernvinneveien (5) er uforenlig med morgenbildet».
- Method: DTM1 with k = 0.13 refraction.

**#3 «Temperatur bør ikke være et hardt filter»:**

- Whiteboard «ISH 16°» on the evening of 23.09.
- Rena lufthavn (255 m): 14.7 °C at 15Z and 14.1 °C at 16Z on 23.09; max 15.3 °C on 21.09 (model 15.1).
- Open-Meteo at ~600 m, 21.09: max 12.0–12.3 °C, 8.3–8.5 °C at 19:00.
- Messelt (~900 m) is ~3 °C colder and is «settes til 0» by the filter.
- The thermometer may be inside the transparent box.

**#4 «Veiretning «ca. 130°»: referanseramme og kandidat 1 (94°)»:**

- Bearings box → nearest road: candidate 1 ≈ 94° (61.39921, 11.04086), 2 = 124°, S1 = 129°, S2 = 98°, 4 = 176°, 5 = 183°.
- Three readings of «KOM FRA DEN VEIEN ←»:
  - image-left, ~190–200° (camera 219°, HFOV 62°)
  - Anja's left, ~310°
  - the sign «118–120 GR ØST» (removed 23.09 19:12)
- Proposes a "~" instead of a tick for candidate 1.

**#5 «Regionpremisset: Evenstad, flydataene og kontrollruter»:**

- NOZ9EG (LN-NIQ, hex 4791ac) at **19:28:53Z**, which is stream 21:29:38 minus a 45 s delay, at **61.370 N 10.908 E, FL260**.
- Elevation angles from candidate sites: candidate 1 = 47°, Evenstad = 35°, Messelt S1 = 37° (max 63°), Sjusjøen = 20°, Rudshøgda = 9°, Løten = 7°.
- «Tatt bokstavelig («peker rett opp») taler dette mot Elverum–Løten».
- 7 of the 13 search areas come from default.no's top cell. Model premises: 790–911 m and ≤ 900 m from road.
- default.no "best guesses" now rank 60.70/11.60 and 60.95/11.30 above Evenstad.

**#6 «Manglende og forkortede tavlehint (UJEVNT, TIL VENSTRE, FJELLUFT, båret)»** [P-wb via default.no minute clips]:

| Time | Whiteboard text |
|---|---|
| 21.09 18:44 | «UJEVNT TERRENG, MYE LYNG» |
| 21.09 19:38 | «4 STORE STEINER TIL VENSTRE, KUN STEIN DER» |
| 22.09 ~18:56 | «JA, FØLES SOM FJELLUFT» |
| 22.09 ~18:58 | «GIKK IKKE PÅ STI, MEN KUPERT TERRENG» |
| 22.09 ~19:05 | «BLANDET SKOG, VELDIG HØYE TRÆR, KUPERT TERRENG, SOM GÅR SLAKT…» (with a sketch of a gentle slope) |
| 24.09 | «…DER JEG GIKK I GÅR, GIKK DEN VEIEN →» |

These are relayed through default.no minute recordings, not the original video.

**#7 «Eierbeslutning: skal stillbilder fra sendingen inn i repoet?»:** a privacy and documentation decision, with the recommendation to crop or redact Anja. No Horde rights statement.

**#8 «Skogkravene K0–K4 lar seg ikke gjenskape …»:**

- K0: 212–226°, 3–7 m, median < 3 m
- K1: 213–226°, 8–17 m, median < 3 m
- K2: 190–207°, 3–20 m, p90 ≥ 10 m
- K3: 232–250°, 5–25 m, p90 ≥ 10 m
- K4: 213–226°, 25–70 m, p90 ≥ 12 m

Results:

- A1 (61.4487, 10.9775): crown p90/p99 = «2,3 / 9,1 m», «har nesten ikke trær i kameraets synsfelt».
- Candidate 1 (61.3995, 11.0316) passes 0/25 positions.
- A2 = Gålaveien C07 (61.4625, 10.9751).

**#9 «Utenfor boksen: arrangørlogikk, og 21.29-pekingen kan ikke stedfeste kassen (østsiden gjenåpnes)»:**

- Whiteboard 21.09 18:57: «PRESENNING / MER ÅPEN SKOG TIL HØYRE FOR MEG».
- The coat-of-arms trail is dead: squirrel = Froland, fox = Vegårshei. On 23.09 Froland had rain and cloud, against «SOL · VINDSTILLE», and on 21.09 it had 45+ flights at ≥ 40° elevation, against «INGEN FLY».
- An Open-Meteo check found **dry weather 21–23.09 only in Hedmark/Østerdalen (Trysil, Engerdal, Rendalen, Finnskogen)**.
- 21:29:38–53 stream: arm 10–20° from vertical, leaning camera-left (~129°, SE). Taken literally, it points to bare mountain (900–1080 m). "**Pointing likely referenced a meteor**"; the 21:29 gesture should not select a region.
- Proposes the **eastern pine plateaus**: Osen/Trysil-west, Trysil, Engerdal, Finnskogen, 61.1–61.6 N, 11.7–12.4 E, 750–900 m, pine ~55 % (vs 7–8 % in west Østerdalen).

**#10 «Værmatching: MTG-satellitt (10 min) mot sol i sendingen – oppsett, dagens vakt og et ærlig negativt historikkresultat»:**

- EUMETSAT MTG FCI `mtg_fd:vis06_hrfi`, 1 km, 10 min, over «60,3–62,3 N / 10,2–12,9 Ø».
- 13 sites: «1, 2, Messelt, A1, Rena, Løten, Elverum S, Sjusjøen, Koppang, Osen, Trysil, Engerdal og Finnskogen».
- Baseline: «laveste verdi per sted innen ±10 min av samme klokkeslett over 21.–25.09».
- 22–24.09: «73 tidssteg der kandidatene er uenige», but the stream could not resolve thin cloud. «Direkte sol er bare tydelig ved lav sol om morgenen (07.45–08.00) og i motlys om ettermiddagen».
- Watch window ~15:00–17:30. «Ingen historisk konklusjon trekkes».
- `sun_patches.csv` returned 404.

**#11 «Olivin-sporet (Sunnmøre/Nordfjord) testet: uforenlig med morgensol og skydekke 21.09»:**

- Earliest direct sun: Åheim/Almklovdalen/Gusdalen 08:04 (median 09:12); Bjørkedalen (Volda) 08:10 (median 09:56); Onilsa/Ørsta-sør 07:50 at a single point (median > 10:00). The stream shows sun on the treetops at 07:44–07:49 CEST.
- MTG: cloud (≥ 25) over the olivine areas 14:20–15:20Z, while the stream shows the sun disc 16:20–17:27 CEST.
- «uforenlig» (incompatible). **Rejected.**

### 7.3 MagnusPladsen/hordejakten-2026

A fresh clone shows **no commits after 68faa86** (25.09 21:04:38 +0200). The local mirror is current.

---

## 8. Candidate places mentioned in web sources

Coordinates are WGS84. "approx" means a regional centroid I chose myself; it is not a published point.

| Name | Lat, Lon | Source | Status |
|---|---|---|---|
| Glomma-dalen Rena–Evenstad (default.no best guess, box 61.35–61.47 N, 10.97–11.15 E) | 61.41, 11.06 (box centre) | default.no via search index, 25.09 03:27 | active [M] |
| default.no alt "best guess" south | 60.70, 11.60 | mkekeoooo #5 | active [M], ranking disputed |
| default.no alt "best guess" Løten | 60.95, 11.30 | mkekeoooo #5 | active [M] |
| Candidate 1, Myklebysæterveien vest | 61.3995, 11.0316 | mkekeoooo README / #4 / #8 | active but weakened (0/25 forest positions; road ~94°) |
| A1, Birkebeinerveien (default.no site-finder top) | 61.4487, 10.9775 | mkekeoooo #8 | weakened (almost no trees in camera sector) |
| A2, Gålaveien C07 | 61.4625, 10.9751 | mkekeoooo #8 | active [M] |
| 2, Madsskardveien traktorvei | 61.4443, 11.1234 | mkekeoooo README | active [M] |
| 4, Madsskardveien øst | 61.4518, 11.1428 | mkekeoooo README | active [M] |
| 5, Jernvinneveien | 61.4351, 11.1435 | mkekeoooo #2 | rejected by #2 (morning-sun horizon) [C-int] |
| Eastern pine plateaus (Osen/Trysil-west, Trysil, Engerdal, Finnskogen; 61.1–61.6 N, 11.7–12.4 E) | 61.35, 12.05 (approx) | mkekeoooo #9 | proposed [C-int] |
| Engerdal–southern Femund | 61.9, 11.95 (approx) | mkekeoooo README ea842e4 | proposed for analysis, not ranked |
| Solør/Finnskog | 60.55, 12.35 (approx) | mkekeoooo README ea842e4 | proposed for analysis, not ranked |
| Brumunddal (Anja's home town per Børsen) | 60.88, 10.94 | Børsen, Ringsaker Blad; magnus FOLK_TROR | background fact. The idea that the box is near her home is [C-int] and weak. |
| Sigdal (Buskerud), chat gesture test 21.09 15:15–15:19 | 60.05, 9.63 (approx) | default.no via search | ambiguous / untested |
| Åheim / Almklovdalen (olivine wordplay) | 62.04, 5.52 (approx) | mkekeoooo #11 | rejected (sun and cloud) |
| Froland (squirrel arms) | 58.52, 8.64 (approx) | mkekeoooo #9 | rejected |
| Vegårshei (fox arms) | 58.76, 8.84 (approx) | mkekeoooo #9 | rejected |
| 2023 site, Vinje/Tokke border | 59.5, 7.9 (approx) | mkekeoooo #9 / prior_years | prior year |
| 2024 site, Kongsberg silver mines | 59.62, 9.57 (approx) | mkekeoooo #9 | prior year |

---

## 9. Contradictions and corrections

1. **Prize amount.** horde.no was summarised as "1,093,072 kroner". This comes from the **2024** copy of the same URL (an older index title reads «Hordejakten 2024 er i gang!»). The 2026 figure is **1 116 897 kr**, stated on the /hvorfor page and the sign in the box. The same stale index attaches Torstein Nyhammer Mellingen and Jan Tore Kristoffersen to "1,093,072 kr".
2. **"Box placed on Tuesday"** (Børsen summary) vs the stream starting Monday 21.09 ~06:50. This is most likely the 2023 back-story; 2023 launched on Tuesday 17.10.
3. **Anja's origin.** Discord-relayed gestures say "Anja from Oslo, picked up in Oslo" (default.no). Børsen and Ringsaker Blad say she is from **Brumunddal**. The whiteboard says «OSLO, SØN KL 04.00» (pickup). These are compatible if she was picked up in Oslo.
4. **Drive time.** Default.no's gesture relay gives "7+ h by car". Anja and the whiteboard say she slept and does not know. Alf/Børsen say «kjørt rundt i flere timer … Det var en del av opplegget». The drive time is deliberately uninformative.
5. **Pickup day.** The whiteboard says «SØN KL 04.00». Børsen says in the box «since Monday morning». These are not strictly contradictory, because pickup and box entry are different events. If "SØN 04.00" means Sunday 20.09 at 04:00, about 27 h pass before the stream started. If it means the night into Monday, it is about 3 h. Unresolved.
6. **default.no ranking.** The 03:27 index says Glomma Rena–Evenstad is best, with 24 % within 25 km. mkekeoooo #5 says default.no "best guesses" now put 60.70/11.60 and 60.95/11.30 above Evenstad. The local mirror from 24.09 18:31 had 28.9 % within 25 km.
7. **Audio.** default.no: «sound is canned», with replays verified. Alf (second-hand): «Det er ekte lyd på streamen». These are compatible if the sound is real but replayed.
8. **Afternoon sun.** mkekeoooo **retracted** «Antakelsen om en helt overskyet ettermiddag» on 25.09 (commit b067a04, 23:23). Direct sun at ~17:00 on 25.09 and a sun star at 16:45 and 16:50 on 23.09 are documented.
9. **21:29 pointing.**
   - default.no and magnus treat it as a plane: «board FLY 21:30», rumble at 21:33:20.
   - mkekeoooo #9 says it was probably a meteor and must not select a region.
   - mkekeoooo #5 gives the literal elevation angles, which argue against Elverum–Løten.
10. **Infrared times** (08:00:19 off, 18:30 on) appeared in one search summary but were not confirmed by a second query. Low confidence.
11. **Hand-signal protocol.** Børsen describes triangle = sees mountains and crossed arms behind head = no mountains. Her actual answer is unknown to me.

---

## 10. What this sweep did NOT find

- No official 2026 hint text from the Horde app, the newsletter or Horde Plus appeared in search results. Only the page-level summaries in §1 did.
- No news coverage of 2026 from VG, NRK, E24, TV 2, Østlendingen, HA or GD.
- No 2026 Horde or Alf TikTok, Instagram or Facebook posts were indexed. The TikTok live of 25.09 is known only second-hand.
- No age rule. No official written confirmation of the 5 h quarantine.
- No report of the box being found or opened as of the evening of 25.09.
- Nothing from a Hordejakten-specific Discord or Reddit beyond the magnus invite link.

---

## 11. Open questions

1. Which answer did Anja give to the "triangle = I see mountains / crossed arms = no mountains" prompt reported by Børsen, and when? Check the whiteboard and gesture logs for the day of the «Nytt sjokkstunt» article, 21–22.09.
2. What did Alf say on the 25.09 TikTok live, word for word? The quarantine, the queue and «viktige hint i helgen» are all relayed second-hand.
3. What official hints will appear on 26–27.09 (the "weekend hints")?
4. Is Kodejakten (horde.no/secret/kodejakten) still `not_configured`?
5. What is in the issue #10 comments 5839791607 and 5840220953, and in the ZIPs (`Hordejakten_landsok_solsikt_25sep.zip`, `Hordejakten_ny_solobservasjon_23sep.zip`)? They were not retrievable from here.
6. Which default.no ranking is current: Glomma Rena–Evenstad first, or 60.70/11.60 and 60.95/11.30?
7. What exactly do the praktiskinfo.no, vervekodesiden.no and paywalled skattejakthint.no hint lists contain? Are any hints there missing from magnus `innhold.ts`?
8. Does the Ringsaker Blad article add anything about Anja's background, such as her knowledge of the local terrain, that bears on where Horde would *avoid* placing her?
9. Is there an age limit in the vilkår?
10. What are "Anja's September 25 TikTok statements" (mentioned in mkekeoooo #1)?

---

## 12. Queries run (36 successful)

1. `Hordejakten 2026 hint`
2. `Hordejakten Anja kasse skogen`
3. `Horde kasse skogen 2026 million`
4. `praktiskinfo Hordejakten 2026 hint regler premie`
5. `skattejakthint.no Hordejakten alle hint samlet`
6. `horde.no gjeldfri hordejakten regler`
7. `Kampanjevilkår for Hordejakten horde.no vilkaar`
8. `Jaktvettreglene 2026 Horde hordejakten`
9. `"Hvorfor vi gjør Hordejakten" Horde`
10. `Anja 29 snakker ut Børsen Hordejakten`
11. `"Anja" jaktes av hele Norge Børsen`
12. `nytt sjokkstunt fra norsk selskap Horde kvinne kasse`
13. `Ringsaker Blad "Hele Norge" jakter på Anja Brumunddal`
14. `Anja Nymoen Søberg stuntkvinne`
15. `Hordejakten Anja håndtegn trekant fjell livestream`
16. `Hordejakten dag 5`
17. `Hordejakten nytt hint`
18. `Alf Gunnar Andersen Hordejakten 2026`
19. `Hordejakten VG kvinne glassboks million skogen`
20. `NRK Horde kvinne i kasse skogen livestream kritikk`
21. `Hordejakten Østlendingen OR "Hamar Arbeiderblad" OR "Gudbrandsdølen Dagningen"`
22. `Hordejakten funnet kassen 2026 vinner`
23. `Hordejakten default.no open-data search log`
24. `Hordejakten discord OR reddit 2026`

Queries 25–36 were restricted to default.no:

25. latest update
26. osint_notes
27. map layers fusion
28. best guess Glomma
29. audio replay
30. aircraft 21:29 / NOZ9EG
31. log entries 25 September
32. infrared 08:00:19
33. TavlAI
34. Discord relay gestures
35. Østerdalen ±60 s
36. rain stations dry glass

Refused because the budget was exhausted: evening sun 17:23, field checks searched-empty, and app hints 5008/kodejakten.

**Other retrieval:**

- WebFetch (github.com): mkekeoooo issues #1–#11.
- `git clone` into scratchpad: `web_mk` (mkekeoooo, HEAD ea842e4), `web_magnus` (HEAD 68faa86), `fordelabs` (empty).
- GitHub MCP `search_repositories`: `hordejakten` gives 4 repos.
- `search_code`: `Hordejakten` gives 19 hits, all in magnus or danielmb apart from one unrelated m3u.

## 13. URL index

- https://horde.no/gjeldfri/hordejakten
- https://horde.no/gjeldfri/hordejakten/vilkaar
- https://horde.no/gjeldfri/hordejakten/hvorfor
- https://horde.no/gjeldfri/hordejakten/jaktvettreglene
- https://horde.no/artikler/hordejakten-2026
- https://horde.no/jakten/components/QuestionSection/
- https://horde.no/secret/kodejakten
- https://borsen.dagbladet.no/nyheter/nytt-sjokkstunt-fra-norsk-selskap/85179562
- https://borsen.dagbladet.no/nyheter/anja-29-jaktes-av-hele-norge/85183299
- https://borsen.dagbladet.no/nyheter/anja-29-snakker-ut-absurd/85185489
- https://www.ringsaker-blad.no/hele-norge-jakter-pa-anja-29-fra-brumunddal/s/80-79-13202
- https://praktiskinfo.no/hordejakten-2026/
- https://skattejakthint.no/
- https://vervekodesiden.no/blogg/hordejakten-2026
- https://gjerrigknark.com/Konkurranser/Penger-bonus-og-gavekort/Finn-og-vinn-kassen-med-over-en-million-kroner-i-skogen
- https://x.com/MrMekker/status/2102086838630453645
- https://x.com/AlfG86
- https://www.instagram.com/alf.gunnar/
- https://www.norwayfintechfestival.no/2026/speakers/alf-gunnar-andersen.
- https://www.facebook.com/horde.no/videos/tips-og-hint-om-hordejakten/415958894406552/
- https://www.youtube.com/watch?v=EQHgfmZicc8
- https://www.youtube.com/watch?v=H_-0LbPSu5s
- https://www.youtube.com/watch?v=tWoD9d4eFII
- https://www.youtube.com/watch?v=ThO-OsWvoL8
- https://open.spotify.com/episode/178hAIH0Mcypgvvq67atBm
- https://open.spotify.com/episode/1pgCpWTv9O9VBXDunh5mDO
- https://default.no/ , https://default.no/index.php , https://default.no/map.php
- https://github.com/mkekeoooo/hordejakten-2026 (issues 1–11)
- https://github.com/MagnusPladsen/hordejakten-2026
- https://github.com/fordelabs/hordejakten
- https://discord.gg/ETKzsk4xU
- Prior-year news:
  - https://www.ba.no/vant-million-etter-nervedrama-i-skogen/s/5-8-2615243
  - https://www.nettavisen.no/nyheter/fant-en-million-i-skogen-verdige-vinnere/s/5-95-1408921
  - https://www.kom24.no/alf-gunnar-anderse-horde-markedsforing/gjemte-en-million-kroner-i-skogen-na-er-pengene-fjernet/658791
