# Anja's whiteboard ("tavla"): complete log, verification and geographic constraints

Hordejakten 2026 · compiled 2026-09-25 (evening, CEST) · task `tavle-log`

---

## 0. Summary

- **Source.** The `TAVLE` array in `data/raw/magnus/src/data/innhold.ts` L881–1054 has **58 entries**. The file was last changed at commit `6c421a9` (2026-09-25 20:53:24 +0200); the repo head is `68faa86` (21:04:38). Section 2 reproduces every entry verbatim, in file order.
- **Not all entries are plain whiteboard text from the stream.** 52 are. The other 6 need care:
  - a clothing observation (`«+5» på genseren`);
  - Magnus's description of an illegible sketch;
  - a rain report (`Anja sa at det regnet`), which is not seen on a board;
  - a real board of Anja's, but seen in Horde's Facebook story rather than on the stream (`GOD HELG`);
  - a pointing gesture paired with Flightradar24 (`(ikke tavle)`);
  - one annotation-only line (`FLY (pekte opp, litt mot sørøst)`), where the board said only «FLY».
- **Photos.** I looked at all 27 whiteboard photos (`public/img/tavle-*.jpg`, covering 26 entries). They confirm the transcriptions, with the small caveats listed per entry. Eleven IR frames carry a yellow overlay clock and a «TavlAI» watermark, and their clocks match the log's minute stamps: 22.09 19:19:32 · 23.09 19:09:54 · 23.09 19:12:22 · 24.09 08:24:58 · 17:20:17 · 18:07:15 · 25.09 09:49:11 · 09:58:41 · 10:21:45 · 10:38:16 · 18:13:23.
- **The Magnus log is incomplete, and two lines are shortened.** The `mk_bevis` evidence pack (`bevis/claude-2026-09-25/README.md` L28–35) read original frames:
  - 21.09 18:44 is «STARTET 07 00 / **UJEVNT** TERRENG, MYE LYNG / HØRER IKKE MYE FRA BOKSEN». Magnus has «KUPERT TERRENG».
  - 21.09 19:38 is «4 STORE STEINER **TIL VENSTRE**, KUN STEIN DER». Magnus drops «TIL VENSTRE».
  - A 22.09 18:56–19:05 set is missing from Magnus: «JA, FØLES SOM FJELLUFT» · «GIKK IKKE PÅ STI, MEN KUPERT TERRENG» · «BLANDET SKOG, VELDIG HØYE TRÆR, KUPERT TERRENG, SOM GÅR SLAKT SLIK:» plus a drawn gentle hump.
- **The mkekeoooo report adds more boards** (full report p.3–4; short report p.3):
  - «NULL REGN», «det har ikke vært frost» and «SER VELDIG MANGE STJERNER» (22.–23.09);
  - «DET ER INGEN LYS RUNDT KASSEN» (22.09 21:36). I verified this one in `figurer/fig_lyshendelse.png`;
  - «Gule og grønne fugler» (undated);
  - a clock time of 08:46 for the 25.09 «OVERSKYET» board.
- **The strongest location constraints on the boards** (all primary, but each is Anja's perception):
  - access: 5–10 min walk from the car, "I think it was uphill", no paths, no ferry, only car;
  - ground: hilly or uneven, lots of heather, "typical mountain terrain", "feels like mountain air", 4 big boulders, moss on stones, lots of mushrooms;
  - no water or water sounds nearby, and no cabin nearby;
  - forest mix «35% BJØRK · 25% GRAN · 40% FURU» right around the box (birch, spruce, pine);
  - it had been logged earlier where she walked "yesterday";
  - she noticed no cattle grid on the drive;
  - weather sequence: 21.09 clear, 22.–23.09 no rain, 23.09 17:49 sun and calm, 24.09 grey all day, 25.09 overcast with no fog;
  - temperatures: 21.09 ~12 °C by day and ~8–11 °C at 19:35; 23.09 evening "ish 16°"; 25.09 09:58 "probably 5°";
  - camera at «41 ØST», and the Horde sign pointing «118–120 GR ØST»;
  - "few planes here", and planes "so far away that it is impossible to see them".
- **Arrow and left/right boards have an unresolved mirror ambiguity** (section 6). «KOM FRA DEN VEIEN ←» reads as ≈131° (SE) if the displayed arrow is taken at face value. It reads as ≈311° (NW) if she drew it from her own point of view before turning the board to the camera.

---

## 1. Sources and conventions

### 1.1 Files read

| Item | Path / reference | Notes |
|---|---|---|
| Whiteboard log | `/home/user/test/data/raw/magnus/src/data/innhold.ts` L880–1054 | Doc comment L880: «Svar Anja har skrevet på tavla, i rekkefølgen de kom (nye legges nederst). Tider er streamtid (trolig 20 sek–1 min forsinket, vi tipper).» |
| Panel note | `.../magnus/src/components/TavlePanel.tsx` L17 | «Tidene er streamtid, som trolig ligger 20 sek–1 min bak (vi tipper). Tavlene fra 24.09 er merket med dato, ikke klokkeslett, og står ikke i riktig rekkefølge innbyrdes.» |
| Stream delay constant | `innhold.ts` L10 | `forsinkelseSek: 45`. This is still the old 45 s value; it was replaced in the texts by "20 sek–1 min" in commit `01ab80d` (25.09 11:29). |
| Hints that cite «Tavla» | `innhold.ts` L58–68, 133–142, 183–241, 291–318, 402–449, 470–488, 499–506, 721–729, 742–761, 805–822 | Community interpretations of the boards. They are cited below where relevant and marked as interpretation. |
| Whiteboard photos | `.../magnus/public/img/tavle-*.jpg` (27 files; `tavle-2509-ballongfarger.png` is Magnus's own rendering), `fr24-2509-*.jpg`, `stream-2509-skilt-tilbake.jpg` | I viewed every file. |
| Git history of TAVLE | `git log -L '/export const TAVLE/,/^]$/:src/data/innhold.ts'` in the magnus mirror | Gives the commit (real time, CEST) when each entry was first logged, which is an **upper bound** on when the board was written. It also records every text change or retraction. |
| mk_bevis evidence pack | `/home/user/test/data/raw/mk_bevis/bevis/claude-2026-09-25/README.md` L28–35, L48, L62 | Full frame readings of three boards, delay of ~22 s measured by default.no, and the shooting-star ambiguity. |
| mkekeoooo reports | `.../mk_bevis/rapport/Hordejakten_2026_fullstendig_rapport.pdf` p.3–4 and 14–15; `..._kortrapport.pdf` p.3, 6–7 | Whiteboard table built on default.no's tavlelogg: extra boards and extra clock times. |
| mkekeoooo figure | `.../mkekeoooo/figurer/fig_lyshendelse.png` | Stacked board frame reading «DET ER INGEN LYS RUNDT KASSEN» (22.09 ~21:35–21:36). |
| default.no extract | `.../magnus/src/data/defaultno_mer.json` → `observasjoner` (fetched 24.09 18:36) | Timings for the "FLY" gesture, the 22.09 pointing events, and two board paraphrases used as sun constraints. |

default.no itself, including its full `tavlelogg`, was **not reachable** from this machine. Magnus's log and the mkekeoooo table are both partly derived from it.

### 1.2 Timestamps

- **TAVLE `t`** is *stream time*: what the YouTube stream showed, in CEST. The stream lags real time. Delay estimates in the sources:
  - ~22 s, measured by default.no (`mk_bevis` README L48);
  - "20 sek–1 min, vi tipper" (TAVLE L880);
  - "ca. 22–45 sekunder" (mkekeoooo full report p.3);
  - 45 s (the obsolete `STREAM.forsinkelseSek`).
- **Overlay clocks** in the IR ("nattkamera") frames are yellow `YYYY-MM-DD HH:MM:SS` stamps next to a «TavlAI» watermark. The watermark is probably a community frame-grab tool; its clock basis is not documented. Each overlay matches the TAVLE minute exactly, so I treat them as stream time with seconds.
- **Commit times** are real time, CEST (+0200), when an entry reached the repo. The board must have been written before that.
- In the tables below, "(kl. HH:MM)" inside a text is Magnus's own notation for a time on a day-only entry.

### 1.3 Flags

- **GEO** = geographic or physical constraint. The subclasses are terrain, forest, water, sound, weather, temperature, sun/light, direction, walk/access, travel, buildings/cabins, aircraft and exclusion.
- **CODE** = locks and codes.
- **META** = about the stream, the setup or the organiser.
- **CHAT** = chit-chat or social replies with no location content.
- **NOT-WB** = the entry is not whiteboard text.

---

## 2. The complete TAVLE log, verbatim, in file order (58 entries)

File order is the log's own claimed order of arrival (L880). Exceptions: the 24.09 boards are in unknown order (TavlePanel L17), and the two «Ukjent» entries have no known time. A chronological re-sort is in section 3.

Columns:
- **#** is the array index (1-based).
- **L** is the line or lines in `innhold.ts`.
- **t** is the timestamp exactly as given.
- **tekst** is exact; the parentheses inside it are Magnus's annotations.
- **English** is my translation.
- **Photo / my check** is the image file and what I could read myself.
- **Logged** is the commit that added the entry (real time CEST, upper bound on writing time).

| # | L | t (stream time) | tekst (verbatim) | English | Photo / my check | Logged (commit, real time) | Flags |
|---|---|---|---|---|---|---|---|
| 1 | 882 | 21.09 18:31 | `INGEN FLY · INGEN SKYTING · OSLO, SØN KL 04.00 · CA 5–10 MIN Å GÅ FRA BIL` | NO PLANES · NO SHOOTING · OSLO, SUN[DAY] AT 04.00 · APPROX. 5–10 MIN TO WALK FROM CAR | none | c0c849b 23.09 14:30 | GEO aircraft, sound, exclusion (shooting ranges), travel, walk |
| 2 | 883 | 21.09 18:36 | `INGEN FERGE · KUN BIL · VET IKKE ANG. TUNELLER` | NO FERRY · ONLY CAR · DON'T KNOW REGARDING TUNNELS | none | c0c849b | GEO travel, exclusion (islands) |
| 3 | 884 | 21.09 18:38 | `TROR DET VAR OPPOVER · SISTE 5–10 MIN` | THINK IT WAS UPHILL · LAST 5–10 MIN | none | c0c849b | GEO walk, terrain |
| 4 | 885 | 21.09 18:44 | `KUPERT TERRENG · MYE LYNG · HØRER IKKE MYE FRA BOKSEN` | HILLY TERRAIN · LOTS OF HEATHER · DON'T HEAR MUCH FROM THE BOX | none in Magnus. **mk_bevis frame reading** (clip b18-44-14): «STARTET 07 00 / UJEVNT TERRENG, MYE LYNG / HØRER IKKE MYE FRA BOKSEN» ("STARTED 07 00 / UNEVEN TERRAIN, LOTS OF HEATHER / …") | c0c849b | GEO terrain, ground cover, sound; META |
| 5 | 886 | 21.09 18:48 | `LIVE 07:00 · NEI, SER KUN SKOG OG KAMERA FRA BOKS` | LIVE 07:00 · NO, ONLY SEE FOREST AND CAMERA FROM BOX | none. mkekeoooo quotes it without «NEI,». | c0c849b | GEO (no view, no visible buildings/roads); META |
| 6 | 887 | 21.09 18:57 | `PRESENNING · MER ÅPEN SKOG TIL HØYRE FOR MEG` | TARPAULIN · MORE OPEN FOREST TO MY RIGHT | none. The question "PRESENNING" answered is unknown. | c0c849b | GEO forest structure, direction (ambiguous "my right") |
| 7 | 888 | 21.09 19:00 | `INGEN SKYER NÅ · SNART SOLNEDGANG` | NO CLOUDS NOW · SUNSET SOON | none. default.no paraphrases it as «sola går ned snart» at 19:00:40 (`defaultno_mer.json` observasjoner.sol[0]). | c0c849b | GEO weather (sky), sun |
| 8 | 889 | 21.09 19:32 | `IKKE MØRKT ENDA · FINT VÆR` | NOT DARK YET · NICE WEATHER | none | c0c849b | GEO sun/light, weather |
| 9 | 890 | 21.09 19:35 | `CA 12 °C (DAGEN) · NÅ CA 8–11 °C` | APPROX. 12 °C (THE DAY) · NOW APPROX. 8–11 °C | none | c0c849b | GEO temperature |
| 10 | 891 | 21.09 19:38 | `4 STORE STEINER, KUN STEIN DER` | 4 BIG ROCKS/BOULDERS, ONLY STONE THERE | none in Magnus. **mk_bevis frame reading** (clip b19-38-13): «4 STORE STEINER TIL VENSTRE, KUN STEIN DER» ("… TO THE LEFT …") | c0c849b | GEO terrain (boulders), direction (left of whom?) |
| 11 | 892 | 21.09 19:47 | `MØRKT NÅ` | DARK NOW | none. default.no: «MØRKT NÅ» (mørkt under trærne), used as a sun-elevation constraint of −4.5° ± 2.0 at 19:47:00. | c0c849b | GEO sun/light |
| 12 | 893 | 21.09 19:50 | `KLAR HIMMEL` | CLEAR SKY | none | c0c849b | GEO weather |
| 13 | 894 | 21.09 21:30 | `FLY (pekte opp, litt mot sørøst)` | PLANE (pointed up, slightly toward the south-east) | none. The board says only «FLY»; the parenthesis is Magnus's description of the gesture. default.no: «Hun peker opp 21:29:38, skriver «FLY» 21:30:12, og lyden er sterkest 21:33:20.» | c0c849b | GEO aircraft |
| 14 | 895–899 | 22.09 19:19 | `IKKE MØRKT ENDA · INGEN VANN ELLER VANNLYDER, FØLER IKKE DET ER VANN I NOE NÆRHET` | NOT DARK YET · NO WATER OR WATER SOUNDS, DON'T FEEL THERE IS WATER ANYWHERE NEAR | `tavle-2209-ingen-vann.jpg`: IR frame, overlay **2026-09-22 19:19:32**. Board reads «IKKE MØRKT ENDA / INGEN VANN ELLER / VANNLYDER, FØLER / IKKE DET ER VANN / I NOE NÆRHET» with trailing marks (probably «!!»). Confirmed. | 6c421a9 **25.09 20:53** (logged three days late) | GEO water, sound, sun/light |
| 15 | 900 | Ukjent | `ØST CA 118 · RETNING SKILT (skiltet peker ca. 118°)` | EAST APPROX. 118 · DIRECTION SIGN (the sign points approx. 118°) | none. First logged as «ØST CA 118 · RETNING S…? (siste ord uklart)» (c0c849b). "SKILT" was filled in at bdffb03 (23.09 15:15) after #20. | c0c849b 23.09 14:30 | GEO direction |
| 16 | 901 | Ukjent | `VIL DERE SE EN BACKFLIP?` | DO YOU WANT TO SEE A BACKFLIP? | none | c0c849b | CHAT |
| 17 | 902 | 23.09 09:33 | `DET GÅR FINT · TAKK SOM SPØR ♡` | IT'S GOING FINE · THANKS FOR ASKING ♡ | none | c0c849b | CHAT |
| 18 | 903 | 23.09 | `LAST NED HORDE APPEN` | DOWNLOAD THE HORDE APP | none | cf75140 23.09 15:05 | META (promo) |
| 19 | 904 | 23.09 | `REVEN HETER BENNY` | THE FOX IS CALLED BENNY | none. Refers to the plush fox in the box, visible in several frames. | 6d6d45c 23.09 15:16 | META / possible name hint (interpretation only) |
| 20 | 905 | 23.09 | `118–120 GR ØST (retningen skiltet peker)` | 118–120 DEG EAST (the direction the sign points) | none | 2eb6f94 23.09 15:17 | GEO direction |
| 21 | 906 | 23.09 | `SOLA VAR OPPE FØR 07` | THE SUN WAS UP BEFORE 07 | none. Which morning it refers to is unknown. The `soloppgang` hint (L499–506) gives the source as «Anja». | 86d52b8 23.09 15:22 | GEO sun |
| 22 | 907 | 23.09 | `«+5» på genseren` | "+5" on the sweater | none. **NOT-WB**: a stream-visual note about clothing (confirmed in the Horde video 1raIm3ANsAI per L829). | 6a33959 23.09 15:32 | NOT-WB; CODE? |
| 23 | 908–915 | 23.09 | `SKISSE av stedet. Beste lesning: «KAMERA» øverst, kassen i midten, «SKILT» til høyre. Ordet til venstre og nederst er ikke lesbart.` | SKETCH of the site. Best reading: "CAMERA" at the top, the box in the middle, "SIGN" on the right. The word on the left and at the bottom is not legible. | `tavle-skisse.jpg` and `tavle-skisse-forsterket.jpg`: a rectangle in the middle with words around it and a scribble at left. I could **not** independently read «KAMERA» or «SKILT». The text is Magnus's reading, not Anja's words. Earlier reading (66e31ce): «SKISSE: et rektangel i midten (kassen?) med ord rundt. Ikke lesbart på bildet.» | 66e31ce 23.09 15:39; revised eb4093e 15:43 | GEO direction (weak); interpretation |
| 24 | 916 | 23.09 | `KAMERA 41 ØST` | CAMERA 41 EAST | none | 7983773 23.09 15:45 | GEO direction (camera bearing) |
| 25 | 917 | 23.09 17:49 | `LYDTETT · SOL · VINDSTILLE` | SOUNDPROOF · SUN · NO WIND (CALM) | none | df596d3 23.09 18:01 | GEO sound, weather, sun |
| 26 | 918 | 23.09 kveld | `ELEKTRONISK LÅS PÅ DØRA MED 5 SIFFER` | ELECTRONIC LOCK ON THE DOOR WITH 5 DIGITS | none | c4c0aa3 23.09 18:02 | CODE |
| 27 | 919 | 23.09 kveld | `FÅR SE BITTELITE · MASSE SOPP · TYPISK FJELLMARK` | GET TO SEE A TINY BIT · LOTS OF MUSHROOMS · TYPICAL MOUNTAIN TERRAIN (*fjellmark*) | none | 4a9f3ee 23.09 19:01 | GEO terrain, ground cover |
| 28 | 920 | 23.09 kveld | `IKKE VANN · STEIN + SOPP · MOSE PÅ STEINER` | NOT WATER · STONE + MUSHROOMS · MOSS ON ROCKS | none | 4a9f3ee | GEO water, ground cover |
| 29 | 921 | 23.09 kveld | `ISH 16° (ca. 16 grader)` | ISH 16° (approx. 16 degrees) | none | 4a9f3ee | GEO temperature |
| 30 | 922 | 23.09 kveld | `GIKK 2 MIN INN I SKOGEN` | WALKED 2 MIN INTO THE FOREST | none | 4a9f3ee | GEO walk |
| 31 | 923–927 | 23.09 19:09 | `LITE MED FLY HER · SIKKERT MED VILT (siste ord litt utydelig)` | FEW PLANES HERE · PROBABLY [PLENTY OF] GAME (last word slightly unclear) | `tavle-1909-fly-vilt.jpg`: IR, overlay **2026-09-23 19:09:54**. «LITE MED FLY HER» is clear. Line 2 reads «SIKKERT MED VIL?E»; the last word could be VILT (game) or something else. | 89d7dc0 23.09 19:12 | GEO aircraft, wildlife |
| 32 | 928–932 | 23.09 19:12 | `SKILTET ER BORTE · VET IKKE HVOR` | THE SIGN IS GONE · DON'T KNOW WHERE | `tavle-1912-skilt-borte.jpg`: IR, overlay **2026-09-23 19:12:22**. Reads «SKILTET ER / BORTE, VET IKKE / HVOR». Confirmed. | 405c497 23.09 19:15 | META (sign removed) |
| 33 | 933–937 | 24.09 | `INGEN PIZZA ENDA` | NO PIZZA YET | `tavle-ingen-pizza.jpg`: daytime colour camera. The board is readable. Drops or wet specks are visible on the box roof. | b03c6a9 24.09 18:32 | CHAT |
| 34 | 938–942 | 24.09 | `HJELPER VELDIG AT JEG KAN SE DET DERE SKRIVER <3` | IT HELPS A LOT THAT I CAN SEE WHAT YOU WRITE <3 | `tavle-ser-chatten.jpg`: colour, low resolution, consistent. | 4bd3590 24.09 18:33 | META (she reads chat) |
| 35 | 943–947 | 24.09 | `SKAL KLARE Å HOLDE UT TIL NOEN FINNER MEG` | I'LL MANAGE TO HOLD OUT UNTIL SOMEONE FINDS ME | `tavle-holde-ut.jpg`: colour; reads «SKAL KLARE Å HOLDE UT TIL NOEN FINNER MEG». | 91c7e7d 24.09 18:33 | CHAT |
| 36 | 948–952 | 24.09 | `HJEMMELAGET PEPPERONIPIZZA · DRESSING FRA COOP · KNALLGODT` | HOMEMADE PEPPERONI PIZZA · DRESSING FROM COOP · REALLY GOOD | `tavle-pizza-coop.jpg`: crop reading «HJEMMELAGET / PEPPERONIPIZZA / DRESSING FRA COOP / KNALLGODT». Confirmed. | c0b1da8 24.09 18:34 | GEO (very weak: Coop supply); CHAT |
| 37 | 953–957 | 24.09 | `JEG HAR TROA PÅ DERE` | I BELIEVE IN YOU | `tavle-troa-pa-dere.jpg`: colour, consistent. | 4e65b1c 24.09 18:35 | CHAT |
| 38 | 958–962 | 24.09 | `KOM FRA DEN VEIEN ← (pil mot venstre i bildet) · INGEN STIER` | CAME FROM THAT WAY ← (arrow pointing left in the image) · NO PATHS | `tavle-kom-fra-den-veien.jpg`: colour. «KOM FRA DEN VEIEN», an arrow pointing **left in the frame**, and «INGEN STIER». Confirmed. | 4e65b1c | GEO direction, walk |
| 39 | 963–967 | 24.09 | `(kl. 17:20) INGEN HYTTE I NÆRHETEN SOM JEG VET OM ELLER SER` | (at 17:20) NO CABIN NEARBY THAT I KNOW OF OR SEE | `tavle-ingen-hytte.jpg`: IR, overlay **2026-09-24 17:20:17**. Reads «INGEN HYTTE I / NÆRHETEN SOM JEG / VET OM ELLER SER». Confirmed. First logged with t '24.09 17:20' and moved into the text at a9eacd9. | 4e65b1c | GEO buildings/cabins |
| 40 | 968–972 | 24.09 | `INGEN LYD I BOKSEN OVERHODET, JEG HAR KUN DERE Å UNDERHOLDE MEG. INGENTING ANNET` | NO SOUND IN THE BOX AT ALL, I ONLY HAVE YOU TO ENTERTAIN ME. NOTHING ELSE | `tavle-ingen-lyd.jpg`: colour, low resolution, consistent with about five lines of text. | 4e65b1c | GEO sound (ambiguous, see §5); CHAT |
| 41 | 973–977 | 24.09 | `(kl. 18:07) MAMMA <3 (svar til chatten, som savner mamma og stemte på at Anja skal ringe mamma)` | (at 18:07) MUM <3 (reply to the chat, which misses mum and voted for Anja to call mum) | `tavle-mamma.jpg`: IR, overlay **2026-09-24 18:07:15**. «MAMMA ♡», and she blows a kiss. | 4e65b1c / caf7bcb | CHAT |
| 42 | 978–982 | 24.09 | `GRÅVÆR HELE DAGEN` | GREY / OVERCAST WEATHER ALL DAY | `tavle-graver.jpg`: colour; «GRÅVÆR / HELE DAGEN». Confirmed. | caf7bcb 24.09 18:36 | GEO weather |
| 43 | 983–987 | 24.09 | `(kl. 08:24) 5 SIFFER · GANSKE SIKKER (om dørlåsen)` | (at 08:24) 5 DIGITS · QUITE SURE (about the door lock) | `tavle-5-siffer.jpg`: IR, overlay **2026-09-24 08:24:58**. «5 SIFFER / GANSKE SIKKER». Confirmed. | 1aab84b 24.09 18:42 | CODE |
| 44 | 988–992 | 24.09 | `2x HENGELÅS 4 TALL · 1x KODELÅS 5–6 TALL · TROR 5` | 2x PADLOCK 4 NUMBERS · 1x CODE LOCK 5–6 NUMBERS · THINK 5 | `tavle-laser.jpg`: a phone photo of a screen, colour. «2x HENGELÅS 4 tall / 1x KODELÅS 5-6 tall / TROR 5». Confirmed. **Date changed**: first logged as `23.09` (a269415) and re-dated `24.09` (a9eacd9). | a269415 24.09 18:43 | CODE |
| 45 | 993–997 | 24.09 | `DET HAR VÆRT HOGD TIDLIGERE DER JEG GIKK I GÅR · GIKK DEN VEIEN → (pil mot høyre i bildet)` | THERE HAS BEEN LOGGING PREVIOUSLY WHERE I WALKED YESTERDAY · WALKED THAT WAY → (arrow pointing right in the image) | `tavle-hogd.jpg`: a phone photo of a screen. «DET HAR VÆRT / HOGD TIDLIGERE / DER JEG GIKK I GÅR / GIKK DEN VEIEN →». The arrow points **right in the frame**. Confirmed. | a269415 | GEO forest (logging), direction, walk |
| 46 | 998 | 24.09 | `SÅ INGENTING SOM IKKE HØRER TIL I EN SKOG I GÅR · PS! HÅPER PÅ PEPPERONIPIZZA` | SAW NOTHING THAT DOESN'T BELONG IN A FOREST YESTERDAY · PS! HOPING FOR PEPPERONI PIZZA | none | a269415 | GEO (nothing man-made seen on the walk); CHAT |
| 47 | 999 | 24.09 | `(kl. 11:05) Anja sa at det regnet` | (at 11:05) Anja said that it was raining | none. **NOT-WB as far as documented.** mkekeoooo: «Regnet kl. 11.05 er gjengitt av andre, ikke sett på tavla.» | 4d069c1 24.09 18:49 | GEO weather (secondary) |
| 48 | 1000–1004 | 25.09 | `OVERSKYET · FLYENE ER SÅ LANGT UNNA AT DET ER UMULIG Å SE PÅ DAGEN, OG PÅ NATTA DERSOM DET IKKE ER HELT STJERNEKLART` | OVERCAST · THE PLANES ARE SO FAR AWAY THAT IT IS IMPOSSIBLE TO SEE [THEM] BY DAY, AND AT NIGHT UNLESS IT IS COMPLETELY STARRY-CLEAR | `tavle-2509-overskyet.jpg`: colour; «OVERSKYET / FLYENE ER SÅ LANGT / UNNA AT DET ER UMULIG / Å SE PÅ DAGEN OG PÅ NATTA / DERSOM DET IKKE ER HELT / STJERNEKLART». Confirmed. mkekeoooo gives **08:46**, with the paraphrase «Flyene er så langt unna at de er umulige å se.» | 01ab80d 25.09 11:29 | GEO weather, aircraft |
| 49 | 1005–1009 | 25.09 | `KAN IKKE TESTE KODER · INGEN HAR FUNNET BOKSEN (siste del litt utydelig)` | CAN'T TEST CODES · NOBODY HAS FOUND THE BOX (last part slightly unclear) | `tavle-2509-koder.jpg`: colour, low resolution. The first line fits «KAN IKKE TESTE / KODER»; lines 3–4 are **not legible to me**. | 01ab80d | CODE / META |
| 50 | 1010–1014 | 25.09 | `(kl. 09:49) INGEN TÅKE` | (at 09:49) NO FOG | `tavle-2509-ingen-take.jpg`: IR, overlay **2026-09-25 09:49:11**. «INGEN TÅKE». Confirmed. | 01ab80d | GEO weather |
| 51 | 1015–1019 | 25.09 | `(kl. 09:58) SIKKERT 5° · TROR DET ER VARMERE` | (at 09:58) PROBABLY 5° · THINK IT IS WARMER | `tavle-2509-5-grader.jpg`: IR, overlay **2026-09-25 09:58:41**. «SIKKERT 5°» (underlined) / «TROR DET ER / VARMERE». Confirmed. | 01ab80d | GEO temperature |
| 52 | 1020–1024 | 25.09 | `(kl. 10:21) GJETT RIKTIG SANG · BACKFLIP` | (at 10:21) GUESS THE RIGHT SONG · BACKFLIP | `tavle-2509-sang.jpg`: IR, overlay **2026-09-25 10:21:45**. «GJETT RIKTIG / SANG / BACKFLIP» plus a small unread word after BACKFLIP (looks like «OPP?» or «OFF?»). | 01ab80d | CHAT / META (a song game) |
| 53 | 1025–1029 | 25.09 | `(kl. 10:38) IKKE TV, MEN PAD PÅ UTSIDEN AV GLASSET ←` | (at 10:38) NOT A TV, BUT A PAD [TABLET] ON THE OUTSIDE OF THE GLASS ← | `tavle-2509-pad.jpg`: IR, overlay **2026-09-25 10:38:16**. «IKKE TV, / MEN PAD PÅ / UTSIDEN AV GLASSET» plus an arrow pointing left in the frame. Confirmed. | 01ab80d | META (how she sees the chat) |
| 54 | 1030–1034 | 25.09 | `GOD HELG ♥ · OG GOD JAKT (tegning av en fruktkurv, fra Hordes story på Facebook. Musikken i storyen: «Goldenrod · Riverbank»)` | HAVE A GOOD WEEKEND ♥ · AND GOOD HUNTING (drawing of a fruit basket, from Horde's story on Facebook. The music in the story: "Goldenrod · Riverbank") | `tavle-2509-god-helg.jpg`: a Facebook story screenshot. Header «Horde 6 min» and «Goldenrod · Riverbank». Board has a fruit basket, «OG GOD JAKT» and «GOD HELG ♡». Anja wears a «FINN MEG» T-shirt. **Organizer media, not a stream frame.** | 7e3690f 25.09 12:43; text edited 67c7124 14:59 | CHAT; organizer media |
| 55 | 1035 | 25.09 | `INGEN FERIST SOM JEG MERKA` | NO CATTLE GRID THAT I NOTICED | none | 0cc7e96 25.09 15:19 | GEO travel/road |
| 56 | 1036–1040 | 25.09 | `THILPRTE OESHF (anagram av THE SHOPLIFTER) · NOEN SOM VET FASITEN` | THILPRTE OESHF (anagram of THE SHOPLIFTER) · ANYONE WHO KNOWS THE ANSWER? / SOMEONE WHO KNOWS THE ANSWER | `tavle-2509-shoplifter.jpg` (photo of a screen) shows **only** «THILPRTE / OESHF». «NOEN SOM VET FASITEN» is **not visible** in the archived crop; it was added from "the same whiteboard" in 9db1159 (17:58). The board is also visible in `stream-2509-skilt-tilbake.jpg` (the 25.09 16:20–17:03 balloon video via default.no). | ed45704 25.09 17:51; extended 9db1159 17:58 | META / puzzle (letters from balloons) |
| 57 | 1041–1048 | 25.09 17:22 | `(ikke tavle) Anja pekte opp mot himmelen. Flightradar24 rundt da: SAS50J over Stange/Løten og SAS364 over Rena` | (not whiteboard) Anja pointed up at the sky. Flightradar24 around then: SAS50J over Stange/Løten and SAS364 over Rena | `fr24-2509-sas50j.jpg` and `fr24-2509-sas364.jpg` are FR24 screenshots **without timestamps**. The SAS364 screenshot shows the aircraft already north of Rena. | 9a7359b 25.09 18:02 | NOT-WB; GEO aircraft (community observation) |
| 58 | 1049–1053 | 25.09 | `(kl. 18:13) KANSKJE 35% BJØRK · 25% GRAN · 40% FURU · AKKURAT RUNDT MEG` | (at 18:13) MAYBE 35% BIRCH · 25% SPRUCE · 40% PINE · RIGHT AROUND ME | `tavle-2509-treslag.jpg`: IR, overlay **2026-09-25 18:13:23**. «KANSKJE / 35% BJØRK / 25% GRAN / 40% FURU / AKKURAT RUNDT MEG». Confirmed. A wooden hand stands upright in the heather in front of the box. | 4d44d6a 25.09 19:12 | GEO forest |

Tally: 58 entries. 27 whiteboard photos cover 26 entries; the sketch entry (#23) has two photos. Two further photos are Flightradar24 screenshots attached to #57.

---

## 3. Best-estimate chronological timeline, merged with other sources

Stream time, CEST. "≤ hh:mm" is an upper bound taken from the commit time (real time). Entries marked **[S]** are supplementary boards or events that are *not* in Magnus's TAVLE; their source is given.

**Sunday 20.09**
- 04:00: picked up in Oslo (#1). The Magnus `reise` hint (L112–123) notes a conflict with Børsen's «siden mandag morgen».

**Monday 21.09** (stream start ~06:50 per the `reise` hint L120 / «LIVE 07:00» #5 / «STARTET 07 00» [S mk_bevis])
- 18:31 #1 · 18:36 #2 · 18:38 #3
- 18:44 #4. [S] Frame reading: «STARTET 07 00 / UJEVNT TERRENG, MYE LYNG / HØRER IKKE MYE FRA BOKSEN» (mk_bevis README L31).
- 18:48 #5 · 18:57 #6 · 19:00 #7 · 19:32 #8 · 19:35 #9
- 19:38 #10. [S] Frame reading: «4 STORE STEINER TIL VENSTRE, KUN STEIN DER» (mk_bevis L32).
- 19:47 #11 · 19:50 #12
- [S] 21:27:42: she "signalled a shooting star"; 21:29:10: the chat asked her to point at it (mk_bevis L62, "[verifisert i default.no osint_notes]").
- 21:29:38–53: points up. 21:30 (default.no: 21:30:12): writes «FLY» (#13). Sound loudest at 21:33:20 (default.no).

**Tuesday 22.09**
- [S] Anja reported clouds at ~12:00, 15–17 and 19–20 (community "Skyanalyse" map, `innhold.ts` L732–741; exact words not given).
- [S] 18:56–19:05: «JA, FØLES SOM FJELLUFT» · «GIKK IKKE PÅ STI, MEN KUPERT TERRENG» · «BLANDET SKOG, VELDIG HØYE TRÆR, KUPERT TERRENG, SOM GÅR SLAKT SLIK:» with a drawn gentle hump (mk_bevis L33, file `2209_1856-1905_FJELLUFT_STI_BLANDET_SKOG.png`, withheld).
- 19:19:32 #14 (IR).
- [S] 20:32–20:34: reacts to a plane; the chat writes «FLYY» (default.no candidate SAS39A; 90–96 % cloud).
- [S] 20:34–20:36: «Hun peker, setter seg opp og følger flyet sørover» (candidate NOZ55J, 21 000 ft; chat: «Fly blinker med farger») (`defaultno_mer.json` observasjoner.fly[1–2]).
- [S] ~21:35–21:36: «DET ER INGEN LYS RUNDT KASSEN», held up during a ~55 s dimming of the left frame edge (mkekeoooo full report p.14–15; `fig_lyshendelse.png`, verified by me).
- [S] 22.–23.09: «NULL REGN», «det har ikke vært frost», «SER VELDIG MANGE STJERNER» (mkekeoooo full report p.3). Exact times not given.

**Unknown, but written before 23.09 14:30** (commit c0c849b): #15 «ØST CA 118 · RETNING S…», #16 «VIL DERE SE EN BACKFLIP?»

**Wednesday 23.09**
- 09:33 #17
- ≤ 15:05 #18 · ≤ 15:16 #19 · ≤ 15:17 #20 · ≤ 15:22 #21 · ≤ 15:32 #22 (sweater) · ≤ 15:39 #23 (sketch) · ≤ 15:45 #24 «KAMERA 41 ØST»
- 17:49 #25
- "kveld", ≤ 18:02 #26 · "kveld", ≤ 19:01 #27–#30. So "kveld" here means roughly 17:50–19:00.
- 19:09:54 #31 · 19:12:22 #32
- (Interpretation.) The walk "i går" in #45 and #46, written 24.09, would have happened on 23.09. That matches #30 «GIKK 2 MIN INN I SKOGEN».

**Thursday 24.09** (order unknown except where a clock time is given; all logged 18:32–18:49 real time)
- 08:24:58 #43
- 11:05 #47 (rain, reported)
- undated before ~18:43: #33, #34, #35, #36, #37, #38, #40, #42, #44, #45, #46
- 17:20:17 #39 · 18:07:15 #41
- Plausible pizza order (interpretation): #46 «PS! HÅPER PÅ PEPPERONIPIZZA», then #33 «INGEN PIZZA ENDA», then #36 «HJEMMELAGET PEPPERONIPIZZA … KNALLGODT».
- [S] Horde sound hint of black grouse lek (mkekeoooo); not a whiteboard.

**Friday 25.09**
- 08:46 #48 (time from mkekeoooo, «gjengitt»)
- 09:49:11 #50 · 09:58:41 #51 · 10:21:45 #52 · 10:38:16 #53
- ≤ 11:29 #49
- ≤ 12:43 #54 (Facebook story)
- ≤ 15:19 #55
- ~16:20–17:03 #56 (visible in the balloon video 202609251620–202609251703), logged 17:51
- 17:22 #57 (pointing; not a board)
- 18:13:23 #58

**Undated [S]:** «Gule og grønne fugler» (mkekeoooo full report p.4, "Nylig"; short report p.3: «Anja har også nevnt «gule og grønne fugler»»).

---

## 4. Supplementary Anja statements referenced in the Magnus hints (medium unclear; not in TAVLE)

| Statement (verbatim from the hint) | Where | Medium | Notes |
|---|---|---|---|
| «Anja har sagt at hun var et sted uten vinduer og uten wifi.» | `innhold.ts` L805–813 (`vinduslos`, bekreftet) | unknown (board or spoken) | Refers to the pause or rest place. |
| «Anja har bekreftet at doen er portabel.» | L814–822 (`hytte`, tolkning) | unknown | The toilet is portable. |
| «Anja sier hun liker å se stjernene om natta.» | L780 | unknown | Compare [S] «SER VELDIG MANGE STJERNER». |
| «Anja har kjent lukt av tømmer, hørt dunking og sett en lastet tømmerbil.» | L870–877 (`tommer`, usikker; «Stream (via default.no)») | unknown | Timber smell, thumping, and a loaded timber truck seen. Unverified. |
| «På siste etappe hadde hun sovemaske og headset og ble båret inn i skogen.» | L754–761 (`terreng`, source "Tavla + Børsen-intervju") | news interview | She was carried with a sleep mask and headset on the last stretch. |
| «Anja får bind for øynene hver gang hun forlater boksen.» | L433–440 (`bindfold`, usikker; «hordejakten.vercel.app (ikke sjekket selv)») | third-party site | Conflicts with #45 and #46 if those describe a sighted walk (see §7). |
| «det var dugg på taket av kassen 07:00–09:40» | L760 | stream visual (community) | Dew on the roof, 21.09. |

---

## 5. Entry-by-entry fact extraction and geo classification

IDs are `WB-nn` for TAVLE entries (nn = array index) and `WBS-x` for supplementary boards. The **fact** is always "Anja wrote X". The **content** (what X says about the world) is her perception. Confidence refers to the wording being correct as quoted.

### 5.1 Geographic constraints (GEO)

| ID | Board (verbatim) | Category | What it constrains | Suggested map layer / test | Confidence (wording) |
|---|---|---|---|---|---|
| WB-01a | «INGEN FLY» (21.09 18:31) | aircraft, sound | At 18:31 she noticed no planes. Later boards (#31, #48) refine this to "few, and far away". | Weak. Penalise cells under low-level approach or departure paths to OSL/Gardermoen and regional airports. | 0.8 |
| WB-01b | «INGEN SKYTING» | sound, exclusion | She hears no shooting. The box is soundproof (#25), so this is weak. | Down-weight active shooting ranges and military fields (e.g. Regionfelt Østlandet, Rena). | 0.8 |
| WB-01c | «OSLO, SØN KL 04.00» | travel | Pick-up in Oslo on Sunday 20.09 at 04:00. | Start point for drive-time. Drive duration unknown, since she slept. | 0.8 |
| WB-01d | «CA 5–10 MIN Å GÅ FRA BIL» | walk | Walk from the car to the box: 5–10 min. She was carried, with sleep mask and headset (Børsen via L759). | Distance from car-accessible road (including forest roads): ~150–700 m at 1.5–4 km/h. The Magnus field advice is 300–900 m. | 0.8 |
| WB-02 | «INGEN FERGE · KUN BIL · VET IKKE ANG. TUNELLER» | travel, exclusion | Road-connected mainland; no ferry. Tunnels unknown. | Exclude islands without a fixed link (supported by the Finn.no «Ikke en øy», L642–651). | 0.8 |
| WB-03 | «TROR DET VAR OPPOVER · SISTE 5–10 MIN» | walk, terrain | She thinks the last 5–10 min went uphill. | The box is higher than the parking spot. Require positive rise from the nearest road (default.no's plan uses rise_m). | 0.8 |
| WB-04 | «KUPERT TERRENG · MYE LYNG» (Magnus) / «UJEVNT TERRENG, MYE LYNG» (frame, mk_bevis) | terrain, ground cover | Uneven or hilly ground with lots of heather (*lyng*). | Relief or roughness within 50–150 m; heather-dominated forest floor (poor pine heath). | 0.85 (exact word disputed) |
| WB-04b | «HØRER IKKE MYE FRA BOKSEN» | sound | She hears little from inside the box. | Sound-based inferences are weak. | 0.85 |
| WB-05 | «SER KUN SKOG OG KAMERA FRA BOKS» | buildings, view | From the box she sees only forest and the camera: no buildings, roads, lakes or view. | Exclude sites with a line of sight to roads, buildings or open water within ~50–100 m. | 0.8 |
| WB-06 | «PRESENNING · MER ÅPEN SKOG TIL HØYRE FOR MEG» | forest, direction | A tarpaulin (context unknown), and more open forest to her right. | Her right is ≈131° (SE) if she faces the camera, or ≈311° if she faces away (§6). Weak. | 0.75 |
| WB-07 | «INGEN SKYER NÅ · SNART SOLNEDGANG» (19:00) | weather, sun | Cloud-free at 19:00. Sunset "soon". | Cloud-free at 19:00 on 21.09 in satellite and model data. At 19:00 the sun elevation is ≈+1.5° at Hamar/Rena and ≈+4.3° at Bergen (§8), so "soon" fits eastern Norway best. default.no uses +1° ± 2.5°. | 0.8 |
| WB-08 | «IKKE MØRKT ENDA · FINT VÆR» (19:32) | sun, weather | Not dark yet at 19:32; nice weather. | Sun ≈ −2.5° in the east (civil twilight). Does not separate places. | 0.8 |
| WB-09 | «CA 12 °C (DAGEN) · NÅ CA 8–11 °C» (19:35) | temperature | Daytime ~12 °C; ~8–11 °C at 19:35. | Test against MET Nordic. Where she measured is unknown; it may be inside the box. mkekeoooo #3 says not to use it as a hard filter. | 0.8 |
| WB-10 | «4 STORE STEINER(, TIL VENSTRE), KUN STEIN DER» | terrain | Four large boulders (to the left of someone), with only stone there. | A field-recognition cue. mkekeoooo says it is not visible in the lidar ("Ikke brukbart i laserdata"). | 0.8 |
| WB-11 | «MØRKT NÅ» (19:47) | sun | Dark at 19:47 (under trees). | Sun ≈ −4.2° (Hamar). default.no uses −4.5° ± 2.0°. Weak. | 0.8 |
| WB-12 | «KLAR HIMMEL» (19:50) | weather | Clear sky at 19:50 on 21.09. | Cloud mask at ~19:50 on 21.09 (the Windy exclusion in `skyer` L721–729). | 0.8 |
| WB-13 | «FLY» + pointing (21:29:38–21:30:12) | aircraft | She pointed up and wrote PLANE. The pointing may relate to a shooting star (mk_bevis L62). | ADS-B overpass test with a delay of 15–50 s. Candidates in `fly_2130.json`: NOZ56U northbound over Hamar/Løten (60.8671 N, 11.2475 E at 21:29:48, 23 825 ft) and NOZ9EG southbound over Ringsakfjellet (61.1425 N, 10.8901 E at 21:29:48, 22 275 ft). The arm angle is not an elevation measurement (mkekeoooo README, retraction). | 0.85 that she wrote «FLY»; 0.5 on which object she meant |
| WB-14 | «INGEN VANN ELLER VANNLYDER, FØLER IKKE DET ER VANN I NOE NÆRHET» (22.09 19:19) | water, sound | No water or water sounds; she doesn't feel water is anywhere near. | Down-weight cells within ~100–300 m of lakes, rivers and noisy streams. The box is soundproof, so absence of water sound is weak; absence in view is stronger. | 0.95 (photo) |
| WB-14b | «IKKE MØRKT ENDA» (22.09 19:19) | sun | Not dark yet at 19:19:32 on 22.09. | Sun ≈ −1.2° in the east and ≈ +1.6° at Bergen. Non-discriminating. | 0.95 |
| WB-15 / WB-20 | «ØST CA 118 · RETNING S[KILT]» · «118–120 GR ØST (retningen skiltet peker)» | direction | The Horde sign pointed 118–120° (compass, probably magnetic; device unknown). The sign was removed 23.09 19:12 (#32). | See §6. Magnus adds +4° declination to get 122–124° true (L138). What the sign points *at* (box, road, nothing) is interpretation. | 0.8 (numbers); the "SKILT" word was inferred |
| WB-21 | «SOLA VAR OPPE FØR 07» | sun | The sun was up before 07:00 on an unspecified morning (21, 22 or 23.09). | Sea-level-horizon sunrise (§8): on 21.09 Oslo 06:59, Hamar 06:57, Rena 06:56, but Kristiansand/Tokke 07:10 and Bergen 07:20. On 23.09 only the far east (Kongsvinger 06:58, Trysil 06:57) is before 07:00. Supports eastern Norway only loosely, since "sun up" may mean daylight. default.no: first direct sunlight in the frame at 07:51 on 21.09. | 0.75 |
| WB-24 | «KAMERA 41 ØST» | direction, camera geometry | The camera stands at bearing ~41° from the box (NE) and so looks toward ~221°. | Matches default.no's sun-track camera heading of 219.2–219.6° (`defaultno_mer.json` solbane best heading 219.6°; mkekeoooo report). If 41° is magnetic, true is ~45° and the view ~225°; the raw 221° fits the sun solution better (interpretation). | 0.8 |
| WB-25 | «LYDTETT · SOL · VINDSTILLE» (23.09 17:49) | sound, weather, sun | The box is soundproof. Sun and calm at 17:49 on 23.09. | At 17:49 the sun is ≈9° high at az ≈252° in Hedmark (§8), which is ~31° right of the camera axis. "SOL" implies a clear sky and a local horizon lower than ~9° toward WSW, if she meant direct sun. Calm: MET wind at 17–18. The mkekeoooo national test found that SOL and VINDSTILLE cannot be translated into model values. | 0.8 |
| WB-27 | «FÅR SE BITTELITE · MASSE SOPP · TYPISK FJELLMARK» | terrain, ground cover | She sees only a tiny bit. Lots of mushrooms. "Typical *fjellmark*" (mountain or upland terrain). | Upland forest, poor soils, rocky heath. Magnus reads this as 500–900 m a.s.l. (interpretation, L429). | 0.8 |
| WB-28 | «IKKE VANN · STEIN + SOPP · MOSE PÅ STEINER» | water, ground cover | No water; stones and mushrooms; moss on rocks. | Same as WB-14 plus a bouldery, mossy forest floor. | 0.8 |
| WB-29 | «ISH 16°» (23.09 evening) | temperature | About 16° on the evening of 23.09. | High for the season. It may be the temperature inside the box (mkekeoooo caveat). Test with caution. | 0.8 |
| WB-30 | «GIKK 2 MIN INN I SKOGEN» | walk | She walked 2 min into the forest. Which walk is unknown: the approach on 21.09, or a walk on 23.09 (§7). | If it was the approach: road within ~100–200 m. If it was a 23.09 walk: some feature, possibly the old clear-cut (#45), lies ~2 min from the box. | 0.8 |
| WB-31 | «LITE MED FLY HER · SIKKERT MED VILT(?)» (23.09 19:09) | aircraft, wildlife | Few planes here; probably game. | Penalise busy low-level traffic areas. Game says little (hunting season everywhere). | 0.95 line 1; 0.6 line 2 |
| WB-36 | «DRESSING FRA COOP» | other | Food was bought at Coop. | Coop is everywhere in Innlandet. Very weak. | 0.95 |
| WB-38 | «KOM FRA DEN VEIEN ← · INGEN STIER» | direction, walk | She came from the direction of the arrow, which points left in the frame. No paths. | Image-left ≈ 131° (SE) with the camera looking 221°; ≈311° under the mirror reading (§6). No trail between car and box: cross-country walk. | 0.95 |
| WB-39 | «INGEN HYTTE I NÆRHETEN SOM JEG VET OM ELLER SER» (24.09 17:20) | buildings | No cabin nearby that she knows of or sees. | Down-weight sites with buildings within view (~100–200 m). The `plan.json` field nearest_building_m can be used. | 0.95 |
| WB-40 | «INGEN LYD I BOKSEN OVERHODET, JEG HAR KUN DERE Å UNDERHOLDE MEG» | sound | Either (a) no ambient sound reaches the box, or (b) there is no audio or music in the box. Reading (b) fits "I only have you to entertain me". | If (a), ambient-sound clues from Anja are void. The stream audio is a separate question (default.no found loops). | 0.9 |
| WB-42 | «GRÅVÆR HELE DAGEN» (24.09) | weather | Overcast "all day" (up to the unknown writing time, before ~18:36). | Cloud cover over 24.09 daytime; exclude places with long sunny spells. | 0.95 |
| WB-45 | «DET HAR VÆRT HOGD TIDLIGERE DER JEG GIKK I GÅR · GIKK DEN VEIEN →» | forest (logging), direction, walk | Where she walked "yesterday" (probably 23.09) there had been logging earlier. The arrow points right in the frame. | An older clear-cut or thinning near the box. Image-right ≈311° (NW), or ≈131° under the mirror reading. default.no's tømmer layer uses clear-cuts of 2022+ within 800 m, or 2024–25 within 400 m (L876). "Tidligere" (previously) suggests older cutting, not fresh. | 0.95 |
| WB-46 | «SÅ INGENTING SOM IKKE HØRER TIL I EN SKOG I GÅR» | buildings, other | On yesterday's walk she saw nothing that doesn't belong in a forest: no buildings, vehicles or structures. | Supports remoteness. It also implies she could **see** on that walk (§7). | 0.8 |
| WB-47 | «(kl. 11:05) Anja sa at det regnet» (24.09) | weather | Rain at about 11:05 on 24.09, as reported. | Radar at 11:05 (mkekeoooo: MET radar blocked over much of Glommadalen; not used). Magnus: rain in Rena at the same time (community). | 0.5 |
| WB-48 | «OVERSKYET · FLYENE ER SÅ LANGT UNNA AT DET ER UMULIG Å SE …» (25.09 ~08:46) | weather, aircraft | Overcast on the morning of 25.09. Planes are too far away to be seen by day, or at night unless it is fully starry. | Aircraft are high cruise traffic, not low approaches. It also warns that earlier "sightings" may be based on sound. | 0.95 |
| WB-50 | «INGEN TÅKE» (25.09 09:49) | weather | No fog at 09:49 on 25.09. | Exclude cells with fog or low stratus at ~09:30–10:00 on 25.09 (for example webcams, `vegkamera.json`). | 0.95 |
| WB-51 | «SIKKERT 5° · TROR DET ER VARMERE» (25.09 09:58) | temperature | "Probably 5°", then "I think it is warmer". The question may have been "is it warmer today?" | The 5 °C value is uncertain. Measurement location unknown. | 0.95 (wording); 0.5 (meaning) |
| WB-55 | «INGEN FERIST SOM JEG MERKA» (25.09) | travel/road | She noticed no cattle grid on the drive. She slept or was masked for much of it. | Weakly down-weight final access roads with cattle grids (mountain and summer-farm roads, e.g. Ringsakfjellet or Sjusjøen). | 0.8 |
| WB-58 | «KANSKJE 35% BJØRK · 25% GRAN · 40% FURU · AKKURAT RUNDT MEG» (25.09 18:13) | forest | "Maybe" 35 % birch, 25 % spruce and 40 % pine right around her. | SR16 or Kilden species-share raster within ~50 m. Pine-dominated mixed forest with a lot of birch. The Magnus `treslag` layer implements this (commit ae6dc67). | 0.95 |
| WBS-a | «JA, FØLES SOM FJELLUFT» (22.09 ~18:56–19:05) | terrain, weather | "Yes, feels like mountain air." | Supports higher elevation. Subjective. | 0.8 (mk_bevis frame) |
| WBS-b | «GIKK IKKE PÅ STI, MEN KUPERT TERRENG» (22.09) | walk, terrain | "Didn't walk on a path, but hilly terrain." | No trail between car and box; hilly. | 0.8 |
| WBS-c | «BLANDET SKOG, VELDIG HØYE TRÆR, KUPERT TERRENG, SOM GÅR SLAKT SLIK:» + a drawn gentle hump (22.09) | forest, terrain | Mixed forest, very tall trees, hilly terrain that rises gently, as drawn. | Tall mature canopy (DOM − DTM heights), gentle slopes, and a rounded knoll or ridge profile. | 0.8 |
| WBS-d | «DET ER INGEN LYS RUNDT KASSEN» (22.09 ~21:36) | buildings, light | No lights around the box. | No visible artificial lights at night: remote from houses, roads and cabins. | 0.9 (verified figure) |
| WBS-e | «NULL REGN» (22.–23.09) | weather | No rain on 22–23.09. | Exclude areas with rain on 22–23.09. mkekeoooo: Vestlandet, the mountains and Trøndelag got 5–15 mm, Østerdalen 0–0.7 mm. | 0.7 (read through the mkekeoooo table) |
| WBS-f | «det har ikke vært frost» (22.–23.09) | temperature | No frost so far. | Exclude cells with Tmin < 0 °C on the nights of 20–23.09. It may be felt inside the box. | 0.6 (lower case in the source suggests a paraphrase) |
| WBS-g | «SER VELDIG MANGE STJERNER» (22.–23.09) | weather, light | She sees very many stars: clear, dark sky. | A clear night and little light pollution. | 0.7 |
| WBS-h | «Gule og grønne fugler» (undated) | wildlife | Yellow and green birds. | Possibly siskin, greenfinch or crossbill; says little about location (mkekeoooo: «Barskog, ikke stedsspesifikt»). | 0.6 |

### 5.2 Codes and locks (CODE)

| ID | Board | Meaning |
|---|---|---|
| WB-26 | «ELEKTRONISK LÅS PÅ DØRA MED 5 SIFFER» (23.09 evening) | The door has an electronic lock with 5 digits. |
| WB-43 | «5 SIFFER · GANSKE SIKKER» (24.09 08:24:58) | 5 digits, and she is quite sure (door lock). |
| WB-44 | «2x HENGELÅS 4 TALL · 1x KODELÅS 5–6 TALL · TROR 5» (24.09; first logged 23.09) | Two 4-digit padlocks, plus one code lock of 5–6 digits, which she thinks is 5. |
| WB-49 | «KAN IKKE TESTE KODER · INGEN HAR FUNNET BOKSEN(?)» (25.09 ≤ 11:29) | She cannot test codes from inside. The second line is uncertain. |
| WB-22 | «+5» on the sweater (NOT-WB) | Unsolved; possibly a code modifier. Stream visual only. |

### 5.3 Meta, organizer and puzzle

| ID | Board | Note |
|---|---|---|
| WB-05 (part) | «LIVE 07:00» / «STARTET 07 00» | The stream went live about 07:00 on 21.09. |
| WB-18 | «LAST NED HORDE APPEN» | Promotion. |
| WB-19 | «REVEN HETER BENNY» | The plush fox's name. The name-hint theory (Bennyøy, Benningstad) is interpretation (L58–68). |
| WB-23 | Sketch | Existence is primary; the reading is Magnus's interpretation. |
| WB-32 | «SKILTET ER BORTE · VET IKKE HVOR» (23.09 19:12:22) | The Horde sign was removed. The 25.09 balloon video shows a **different-looking** sign: a painted wooden arrow reading «HORDE», on the right of the frame, pointing left. The original was the «Horde» script logo carried by two hands in front of the box (seen at night in `fig_lyshendelse.png`). |
| WB-34 | «HJELPER VELDIG AT JEG KAN SE DET DERE SKRIVER <3» | She reads the chat. |
| WB-52 | «GJETT RIKTIG SANG · BACKFLIP» (25.09 10:21:45) | A game with the chat. |
| WB-53 | «IKKE TV, MEN PAD PÅ UTSIDEN AV GLASSET ←» (25.09 10:38:16) | The chat is shown on a tablet outside the glass, to the left in the frame. |
| WB-54 | «GOD HELG ♥ · OG GOD JAKT» + fruit-basket drawing | From Horde's Facebook story, with music «Goldenrod · Riverbank» (organizer media). |
| WB-56 | «THILPRTE OESHF» · «NOEN SOM VET FASITEN» | The 13 letters are an exact anagram of THE SHOPLIFTER (and of FILTER THE SHOP and HELHET FOR TIPS). Magnus says the letters come from balloons in a Horde video; the balloon colours are unsolved. "NOEN SOM VET FASITEN" is not visible in the archived photo. |

### 5.4 Chit-chat (CHAT)

- #16 «VIL DERE SE EN BACKFLIP?»
- #17 «DET GÅR FINT · TAKK SOM SPØR ♡» (23.09 09:33)
- #33 «INGEN PIZZA ENDA»
- #35 «SKAL KLARE Å HOLDE UT TIL NOEN FINNER MEG»
- #36 «HJEMMELAGET PEPPERONIPIZZA · DRESSING FRA COOP · KNALLGODT» (the Coop part is weakly geographic)
- #37 «JEG HAR TROA PÅ DERE»
- #41 «MAMMA <3» (24.09 18:07:15)
- #46 second half «PS! HÅPER PÅ PEPPERONIPIZZA»
- #52 «GJETT RIKTIG SANG · BACKFLIP»
- #54 «GOD HELG ♥ · OG GOD JAKT»

### 5.5 Not whiteboard (NOT-WB)

- #22 «+5» on the sweater: a stream visual.
- #23 the sketch description: Magnus's text.
- #47 rain at 11:05: reported by others.
- #54: an organizer media frame (the board is real, but it is not from the stream).
- #57 pointing at 17:22 plus Flightradar24: community observation.
  - ADS-B extract in `innhold.ts` L1639–1642: SAS50J at 17:21:21 at 60.561 N, 11.5341 E, 21 525 ft; at 17:22:41 at 60.7043 N, 11.5471 E, 24 100 ft (real time).
  - Magnus: "over østre Stange mot Romedal og Løten, på 21 000–23 000 fot".
- #13's parenthesis «pekte opp, litt mot sørøst»: Magnus's description of the gesture.

---

## 6. Direction geometry (interpretation; primary numbers only in quotes)

**Primary inputs.** These are Anja's words and the stream image:
- «KAMERA 41 ØST»;
- «ØST CA 118 · RETNING S…» and «118–120 GR ØST»;
- «KOM FRA DEN VEIEN ←», where the arrow points left in the image;
- «GIKK DEN VEIEN →», where the arrow points right in the image;
- «MER ÅPEN SKOG TIL HØYRE FOR MEG»;
- «4 STORE STEINER TIL VENSTRE» (mk_bevis frame);
- «PAD PÅ UTSIDEN AV GLASSET ←».

**Independent check.** default.no fitted the camera heading from the sun track alone: 219.2–219.6°, with f = 1068 px at 1280 px width, giving a horizontal field of view of about 62° (`defaultno_mer.json` solbane; mkekeoooo report p.4). If the camera stands at 41° from the box, it looks at 221°. The two agree within about 1.5°. Declination in Innlandet is about +4° E. If the phone compass was magnetic, the true camera bearing is about 45° and the view about 225°, which is about 5° off the sun solution. The raw value fits slightly better. The compass mode (true or magnetic) is unknown.

**Mapping from the frame to the world** (camera looking at about 221°):
- image-left is 221 − 90 = **131° (SE)**;
- image-right is 221 + 90 = **311° (NW)**;
- the left and right frame edges are at about 190° and 252°.

**Mirror ambiguity for arrows drawn on the board.** Anja faces the camera (bearing ~41°) when she holds up the board.
- (a) *Viewer reading.* She drew the arrow to be correct as displayed. Then ← means 131° (SE) and → means 311° (NW).
- (b) *Writer reading.* She drew the arrow toward her own left or right while the board faced her, then turned it round (a 180° turn about the vertical axis). An arrow toward her own left (311° while she faces 41°) then appears pointing to image-left. So a displayed ← means **311° (NW)** and a displayed → means **131° (SE)**.
- In both readings #38 and #45 point in opposite directions, so the pair does not settle which reading is right.
  - Reading (a): she came from the SE and walked NW "yesterday".
  - Reading (b): she came from the NW and walked SE.

**The Horde sign.**
- Magnus hints say the sign "points left in the image" (L629). Anja gives 118–120°. Image-left is 131°, so the two agree to within about 11–13°. The sign need not be perpendicular to the camera axis.
- If the sign marks the approach *to* the box from the WNW, people come from about 300°. This matches reading (b) of #38 and contradicts reading (a).
- The Magnus `komfra` hint (L183–192) adopts reading (a): "bilen og veien trolig sørøst for kassen, og man går mot nordvest (ca. 300°)". It explicitly reverses the earlier sign-based sector.
- The `retning118` hint (L133–142) was never updated and still says «fra bilen går du ca. 120°». That is an internal contradiction in the Magnus app.
- mkekeoooo uses about 130° as a soft criterion and flags that its candidate 1's road runs toward about 94° (README L18, issue #4).

**«TIL HØYRE FOR MEG» and «TIL VENSTRE».** These are relative to Anja's body. If she faces the camera (41°), her right is 131° and her left is 311°. If she was describing what she sees looking out the other way, they swap. The data cannot resolve this.

**Recommendation.** Treat the approach bearing as bimodal, about 130° or about 310° ± 30°, rather than as one sector. Treat the "sign points at the box" reading as an unconfirmed interpretation.

---

## 7. Cross-entry inferences (clearly interpretation)

1. **The "i går" walk was probably on 23.09 and was sighted.**
   - #45 and #46 were logged on 24.09, so "i går" means 23.09. On the evening of 23.09 she wrote «GIKK 2 MIN INN I SKOGEN» (#30).
   - #46 «SÅ INGENTING SOM IKKE HØRER TIL I EN SKOG» and #45 «DET HAR VÆRT HOGD TIDLIGERE» both require that she could see on that walk.
   - That conflicts with the unverified claim that she is blindfolded whenever she leaves the box (L433–440).
   - If the link holds, an older cutting lies about 2 min' walk (~100–150 m) from the box, in the → direction (311° or 131°, §6).
   - Caveat: the 24.09 boards are undated. "I går" could also refer to an earlier walk, and #30 could mean the approach walk.
2. **Temperatures may be inside the box.** «ISH 16°» on the evening of 23.09 is high for Innlandet in late September. mkekeoooo #3 states that the measurement location is unknown and that temperature should not be a hard filter.
3. **"Sightings" of planes may be auditory.** #48 says planes are "so far away that it is impossible to see them" by day, and at night unless the sky is fully starry. The 21.09 pointing may also refer to a shooting star (mk_bevis L62). So every pointing-to-ADS-B match (21.09 21:29, 22.09 20:32–20:36, 25.09 17:22) is object-uncertain. mkekeoooo README states: «Flyhendelsen 21.09 har usikker objektidentitet og tidsforsinkelse.»
4. **Late-evening direct sun on 23.09 17:49 («SOL»).** If she meant direct sun at the box, the terrain and canopy horizon toward about 250–255° must be below about 9°. This is a possible horizon test; it has not been computed here.
5. **The weather sequence as one fingerprint.** The boards form a joint weather test:
   - 21.09: clear from 19:00 to 19:50, 12 °C by day and 8–11 °C at 19:35;
   - 22–23.09: no rain;
   - 23.09 17:49: sun and calm;
   - 24.09: grey all day, rain around 11:05 (reported);
   - 25.09 ~08:46: overcast, no fog at 09:49, about 5 °C.
   mkekeoooo found that a strict joint test of seven statements left only 2 national hits (both in Nordland) because «SOL» and «VINDSTILLE» are hard to encode. Soft scoring is therefore needed.

---

## 8. Reference sun table (model output; NOAA formulas, sea-level horizon, −0.833° for rise and set)

Script: `/tmp/claude-0/-home-user-test/cdc3054c-9af4-5a32-8665-8227f802a011/scratchpad/sun_ref.py` and `sun2.py` (scratch). Accuracy is about ±1 min and ±0.2°. Terrain and trees delay the sunrise actually seen, so sea-level times are *earliest possible*.

| Place | Sunrise 21 / 22 / 23 / 24 / 25.09 | Sunset 21.09 | Sun elevation 21.09 19:00 («SNART SOLNEDGANG») | 21.09 19:32 («IKKE MØRKT ENDA») | 21.09 19:47 («MØRKT NÅ») | 22.09 19:19 («IKKE MØRKT ENDA») | 23.09 17:49 el / az («SOL») | 25.09 17:22 el / az |
|---|---|---|---|---|---|---|---|---|
| Oslo | 06:59 / 07:01 / 07:03 / 07:06 / 07:08 | 19:20 | +1.7° | −2.3° | −4.2° | −1.1° | 9.7° / 252° | 12.1° / 246° |
| Hamar | 06:57 / 07:00 / 07:02 / 07:04 / 07:07 | 19:19 | +1.5° | −2.4° | −4.2° | −1.2° | 9.3° / 252° | 11.6° / 246° |
| Rena | 06:56 / 06:58 / 07:01 / 07:03 / 07:06 | 19:18 | +1.4° | −2.5° | −4.3° | −1.3° | 9.0° / 253° | 11.3° / 246° |
| Evenstad | 06:57 / 06:59 / 07:02 / 07:04 / 07:07 | 19:19 | +1.5° | −2.4° | −4.1° | −1.2° | 9.1° / 252° | 11.3° / 246° |
| Lillehammer | 06:59 / 07:02 / 07:04 / 07:07 / 07:09 | 19:22 | +1.8° | −2.1° | −3.9° | −0.9° | 9.5° / 252° | 11.7° / 246° |
| Kongsvinger | 06:54 / 06:56 / 06:58 / 07:01 / 07:03 | 19:15 | +1.1° | −2.9° | −4.8° | −1.7° | 9.0° / 253° | 11.4° / 247° |
| Trysil | 06:52 / 06:55 / 06:57 / 07:00 / 07:02 | 19:15 | +0.9° | −2.9° | −4.7° | −1.7° | 8.6° / 253° | 10.9° / 247° |
| Trondheim | 06:59 / 07:01 / 07:04 / 07:07 / 07:10 | 19:23 | +1.7° | −1.9° | −3.5° | −0.8° | 8.8° / 251° | 10.8° / 245° |
| Tokke (Dalen) | 07:10 / 07:12 / 07:15 / 07:17 / 07:19 | 19:31 | +3.1° | −1.0° | −2.9° | +0.3° | 11.2° / 250° | 13.6° / 244° |
| Kristiansand | 07:10 / 07:13 / 07:15 / 07:17 / 07:19 | 19:31 | +3.2° | −1.0° | −3.0° | +0.3° | 11.6° / 250° | 14.1° / 244° |
| Bergen | 07:20 / 07:23 / 07:25 / 07:27 / 07:30 | 19:42 | +4.3° | +0.4° | −1.5° | +1.6° | 12.1° / 247° | 14.3° / 241° |

**Reading.**
- «SOLA VAR OPPE FØR 07» excludes the south and west (Agder, Telemark, Vestland), where sunrise is after 07:10 even at sea-level horizon on any of the days.
- If it refers to 23.09, it also excludes Oslo, Hamar, Rena and Lillehammer, leaving only the far east (Kongsvinger, Trysil).
- The day is unknown, and "oppe" may be loose. Low weight.
- «MØRKT NÅ» at 19:47 and «SNART SOLNEDGANG» at 19:00 fit the east better than Bergen, where the sun is still +4.3° at 19:00.

---

## 9. Contradictions, corrections and retractions (recorded explicitly)

1. **21.09 18:44 wording.** Magnus has «KUPERT TERRENG» (L885). The frame reading has «UJEVNT TERRENG» and a first line «STARTET 07 00» (mk_bevis L31). Magnus also has «LIVE 07:00» as a separate entry at 18:48.
2. **21.09 19:38.** Magnus has «4 STORE STEINER, KUN STEIN DER» (L891). The frame reading has «4 STORE STEINER TIL VENSTRE, KUN STEIN DER» (mk_bevis L32). Magnus omits the direction.
3. **21.09 18:48.** Magnus includes «NEI,»; mkekeoooo (p.3) quotes «LIVE 07:00 · SER KUN SKOG OG KAMERA FRA BOKS» without it.
4. **21.09 19:00.** Magnus has «SNART SOLNEDGANG»; default.no has «sola går ned snart» at 19:00:40. One of them is a paraphrase.
5. **25.09 «OVERSKYET» board.** Magnus: undated, full text. mkekeoooo: 08:46, paraphrased as «de er umulige å se». The photo supports the Magnus wording.
6. **Rain 24.09 11:05.** Magnus (L193–202, L999) treats it as a hint and weak evidence for Rena. mkekeoooo says it was reported by others, not seen on a board, radar was blocked, and the hint is not used. Separately, [S] «NULL REGN» was on the board 22–23.09.
7. **Approach direction.**
   - `retning118` (L138–139): «fra bilen går du ca. 120°».
   - `komfra` (L190): «man går mot nordvest (ca. 300°) … Merk at dette snur den gamle tolkningen».
   - The two hints in the same file conflict. The mirror ambiguity (§6) means neither is established.
8. **Revision history of the «ØST CA 118» interpretation** (git):
   - c0c849b (23.09 14:30) read it as the direction box→parking, with the camera "ca. 73°".
   - bdffb03 (15:15) made the 118° reading "bekreftet" and supplied the word «SKILT».
   - 86d52b8 (15:22) flipped the meaning to "the sign shows the way in; walk 120° from the car".
   - 7983773 (15:45) set the camera to 41°/221°.
   - 4e65b1c (24.09 18:35) flipped the parking sector back to about 300°.
9. **Sketch reading changed.** «Ikke lesbart på bildet» (66e31ce) became «Beste lesning: «KAMERA» øverst … «SKILT» til høyre» (eb4093e) three minutes later. I cannot confirm the new reading from the enhanced image.
10. **Lock board re-dated** from 23.09 to 24.09 (a9eacd9). The 24.09 board times were moved into the text, and their mutual order was declared unknown.
11. **"The sign is back".** #32 (23.09 19:12) says the sign is gone. The Magnus `skilt-tilbake` hint (L262–271) says it "appears to be back" on 25.09. The 25.09 object is a painted wooden arrow «HORDE», which is visually different from the original script-logo sign with hands, so it may be a new sign.
12. **Stream delay values are inconsistent:** 45 s (L10), 20 s–1 min (L880), about 22 s (default.no via mk_bevis L48), 22–45 s (mkekeoooo).
13. **The 21.09 21:29 pointing target.**
    - Magnus treats it as a plane (NOZ56U or NOZ9EG).
    - mk_bevis L62: she had signalled a shooting star at 21:27:42, and the chat asked her to point at 21:29:10, so the pointing may be at the shooting star.
    - The mkekeoooo README says Claude retracted the use of the arm angle as an elevation measurement.
    - The mkekeoooo short report calls the 21.09 and 22.09 aircraft «innflyginger sørover», while its own table lists NOZ56U as northbound. The report is internally inconsistent.
14. **Pick-up day.** The board says «SØN KL 04.00». Børsen says she has been in the cage «siden mandag morgen» (Magnus L120). This is unresolved.
15. **Walk time.** «CA 5–10 MIN Å GÅ FRA BIL» (#1) versus «GIKK 2 MIN INN I SKOGEN» (#30). They may be different walks.
16. **Blindfold claim versus a sighted walk:** see §7.1.
17. **The #13 annotation «pekte opp, litt mot sørøst»** is Magnus's description, not board text. mkekeoooo: «armens retning kan ikke brukes, fordi dybden er usynlig».
18. **«NOEN SOM VET FASITEN»** is attributed to the same board as «THILPRTE OESHF» but is not visible in the archived photo.
19. **Late logging.** #14 (22.09 19:19) was logged only on 25.09 20:53. Earlier analyses built on the Magnus log (for example the `god-helg` "Riverbank" discussion, later noted with «Kassen står neppe ved en elv») did not have it, and the riverbank idea was dropped at 6c421a9.

---

## 10. Open questions

1. What chat question did each short board answer? This matters for «PRESENNING», «IKKE VANN», «SIKKERT 5° · TROR DET ER VARMERE», «4 STORE STEINER (TIL VENSTRE)» and «ØST CA 118». default.no's tavlelogg and the chat replay are needed, and they are blocked here.
2. Is Anja's compass reading magnetic or true, and on what device? This affects 41° and 118–120° by about 4°.
3. Were the arrows (#38, #45, #53) drawn for the viewer or from her own point of view (§6)?
4. What are the exact stream-time clocks for the undated 23.09 boards (#18–#24) and the 24.09 boards? Original frames are needed.
5. What does «GIKK 2 MIN INN I SKOGEN» refer to: the arrival walk, or the walk on 23.09 that passed old logging?
6. Are the temperatures (12, 8–11, 16, 5 °C) inside or outside the box?
7. What is the last word of #31 («SIKKERT MED VIL?E»)?
8. What are lines 3–4 of #49?
9. What is the small word after «BACKFLIP» in #52?
10. What is the full text of the sketch (#23)? Which way is it oriented: camera at the top, as seen from the box?
11. What exactly were «NULL REGN», «det har ikke vært frost», «SER VELDIG MANGE STJERNER» and «Gule og grønne fugler», with times? They come only through the mkekeoooo table.
12. Is the 25.09 wooden «HORDE» arrow sign the original sign or a new one, and does it point the same way?
13. Does the default.no tavlelogg contain boards that neither mirror has? This is likely, given the 22.09 FJELLUFT set.
14. What was the pick-up day: Sunday (board) or Monday (Børsen)?
