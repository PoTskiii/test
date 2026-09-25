# Whiteboard and stream photos, batch A: transcription, visual audit and cross-check

Task: `whiteboards-a`. I viewed 17 images from `/home/user/test/data/raw/magnus/public/img/` one at a time with the Read tool. For each image I transcribed all visible text verbatim, translated it, described any detail that could help with geolocation, and checked the result against the community TAVLE log in `/home/user/test/data/raw/magnus/src/data/innhold.ts` (lines 881–1054), plus the related hint entries.

Written 2026-09-25, evening (CEST). All clock times are CEST (UTC+2).

Supporting files (scripts, enhanced crops, extracted tracks): `/home/user/test/evidence/sources/whiteboard_photos_a_files/`
- `fr24_georef.py`: georeferences both FR24 screenshots, then extracts the aircraft icons and track pixels.
- `fr24_distances.py`: distances and bearings to towns, time interpolation from the ADS-B track, and speeds.
- `sun_azimuth.py`: NOAA solar position.
- `*.png`: enhanced crops used for the readings below (`1909_line2.png`, `koder_text*.png`, `oversk_text.png`, `sang_text.png`, `2509_5g_text.png`, `1912_sweater.png`, `hand_*.png`, `skilt_*.png`, `godhelg_basket.png`, `bw_montage.png`).
- `fr24-2509-*_track.npy`: pixel → lat/lon samples of the track lines.

A companion file by another agent, `/home/user/test/evidence/sources/whiteboard_log.md`, covers the full TAVLE log. This file goes deeper on these 17 images only.

---

## 0. Conventions and caveats

**Evidence classes** (as the rigour rules require):
- **primary_whiteboard**: text Anja wrote on the board, as captured from the stream.
- **primary_stream_visual**: anything else visible on the stream.
- **organizer_app / organizer_media**: the Horde app, and Horde's own social media posts.
- **community_observation**: for example, FR24 screenshots chosen by the community.
- **community_interpretation**: for example, the balloon-colour rendering and the reading of the pointing gesture.
- **model_output**: my own georeferencing and derived numbers are *my* analysis, and are labelled as such.

**"TavlAI" overlay.** Nine of the images carry a yellow `YYYY-MM-DD HH:MM:SS` stamp at top left and a cyan `TavlAI` tag at bottom right. TavlAI is the whiteboard-capture tool used by the community log (default.no). The community treats these stamps as **stream time**. innhold.ts:880 says: «Tider er streamtid (trolig 20 sek–1 min forsinket, vi tipper)» ("times are stream time, probably 20 s–1 min delayed, we guess"). I have **not** independently verified which clock the overlay uses. I report the stamps exactly as printed.

**Two camera looks.** Some frames are **colour and wide**: the whole glass box, with a ladder on the left inside the box (compare the 24.09 frames). Others are **monochrome close-ups**: the TavlAI frames, which stay greyscale even at 09:49–10:38 and 18:13 in daylight. So either a second, monochrome/IR camera exists, or the main camera stays in IR mode. This matters when anyone reads "brightness" or "colour" from a frame.

**Commit times** (real time, CEST) from `git log` of the Magnus mirror give an upper bound on when each image existed:

| Image | Added in commit | Commit time |
|---|---|---|
| app-terje-tskjorte.jpg | 7e3690f | 25.09 12:43:29 |
| fr24-2509-sas364.jpg, fr24-2509-sas50j.jpg | 9a7359b | 25.09 18:02:41 |
| stream-2509-hand.jpg, tavle-2509-ballongfarger.png | 37bd161 | 25.09 17:54:47 |
| stream-2509-skilt-tilbake.jpg | ac06655 | 25.09 17:55:41 |
| tavle-1909-fly-vilt.jpg | 89d7dc0 | 23.09 19:12:47 |
| tavle-1912-skilt-borte.jpg | 405c497 | 23.09 19:15:52 |
| tavle-2209-ingen-vann.jpg | 6c421a9 | 25.09 20:53:24 (added 3 days after capture) |
| tavle-2509-{overskyet,koder,ingen-take,5-grader,sang,pad}.jpg | 01ab80d | 25.09 11:29:29 |
| tavle-2509-god-helg.jpg | 7e3690f | 25.09 12:43:29 |
| tavle-2509-shoplifter.jpg | ed45704 | 25.09 17:51:16 |

Four of the images are **not referenced anywhere in `src/`**: `app-terje-tskjorte.jpg`, `stream-2509-hand.jpg`, `stream-2509-skilt-tilbake.jpg` and `tavle-2509-ballongfarger.png`. They sit in `public/img/` alongside hints that describe them in text: `terje` L530–537, `hand-tilbake` L272–280, `skilt-tilbake` L262–271 and `shoplifter` L281–290.

---

## 1. Summary table

| # | File | Type / evidence | Time (as shown) | Verbatim text (line breaks = " / ") | innhold.ts entry | Match? |
|---|---|---|---|---|---|---|
| 1 | app-terje-tskjorte.jpg | Horde app shop screenshot (organizer_app) | phone clock 12:22, no date (≤ 25.09 12:43) | «T-skjorte i Terje-modell» / «1 116 897» / shirt: «Terje lurer ikke meg.» / description (below) | hint `terje` L530–537; code L1237 | Yes, verbatim |
| 2 | fr24-2509-sas364.jpg | Flightradar24 screenshot (community_observation) | not shown; **I derive ≈ 17:21:47 real time** | label «SAS364»; towns | TAVLE L1041–1048; hint `fly2509` L242–252 | Mostly. SAS364 was already ~22–27 km **north** of Rena |
| 3 | fr24-2509-sas50j.jpg | Flightradar24 screenshot (community_observation) | not shown; **I derive ≈ 17:21:30 real time** | label «SAS50J»; towns | same | Mostly. Alt text «mellom Hamar og Elverum» is loose: it was over eastern Stange, ~34 km S of Elverum |
| 4 | stream-2509-hand.jpg | stream, monochrome (primary_stream_visual) | none (≤ 25.09 17:54) | no text | hint `hand-tilbake` L272–280 | Yes. Adds detail: a **wooden articulated artist's hand**, open, on a black stake |
| 5 | stream-2509-skilt-tilbake.jpg | stream, colour, from the default.no cut 16:20–17:03 (primary_stream_visual) | 25.09 16:20–17:03 (per L266) | sign «HORDE»; shirt «FINN MEG»; box «1116 / 897 / KR»; board «THILPRTE / OESHF» (faint) | hint `skilt-tilbake` L262–271 | Yes. The sign looks **different** from the original script-logo sign |
| 6 | tavle-1909-fly-vilt.jpg | TavlAI (primary_whiteboard) | 2026-09-23 19:09:54 | «LITE MED FLY HER / SIKKERT MED VIL?E» | TAVLE L923–927 | Line 1 yes. Line 2's last word is **not clearly «VILT»**: an E-like final glyph is visible |
| 7 | tavle-1912-skilt-borte.jpg | TavlAI (primary_whiteboard) | 2026-09-23 19:12:22 | «SKILTET ER / BORTE, VET IKKE / HVOR» | TAVLE L928–932 | Yes |
| 8 | tavle-2209-ingen-vann.jpg | TavlAI (primary_whiteboard) | 2026-09-22 19:19:32 | «IKKE MØRKT ENDA / INGEN VANN ELLER / VANNLYDER, FØLER / IKKE DET ER VANN / I NOE NÆRHET» | TAVLE L895–899 | Yes |
| 9 | tavle-2509-5-grader.jpg | TavlAI (primary_whiteboard) | 2026-09-25 09:58:41 | «SIKKERT 5°» (short underline) / «TROR DET ER / VARMERE» | TAVLE L1015–1019 | Yes (5° glyph is soft) |
| 10 | tavle-2509-ballongfarger.png | Magnus's own rendering (community_interpretation) | n/a | «EEFHHILOPRSTT» (coloured) | hint `shoplifter` L287 | Yes, colours match L287 exactly |
| 11 | tavle-2509-god-helg.jpg | Horde Facebook story (organizer_media) showing a whiteboard | «Horde 6 min» (≤ 25.09 12:43) | «OG / GOD JAKT», «GOD HELG ♡», fruit-basket drawing; music «Goldenrod · Riverbank» | TAVLE L1030–1034; hint `god-helg` L300–310 | Yes |
| 12 | tavle-2509-ingen-take.jpg | TavlAI (primary_whiteboard) | 2026-09-25 09:49:11 | «INGEN TÅKE» | TAVLE L1010–1014 | Yes |
| 13 | tavle-2509-koder.jpg | stream colour crop (primary_whiteboard) | none (≤ 25.09 11:29, morning; long-sleeved top) | «KAN IKKE TESTE / KODER / INGEN HAR FUNNET / [illegible]» | TAVLE L1005–1009 | Lines 1–3 plausible. **Line 4 «BOKSEN» cannot be confirmed** |
| 14 | tavle-2509-overskyet.jpg | stream colour crop (primary_whiteboard) | none (mkekeoooo: 08:46) | «OVERSKYET» (fainter) / «FLYENE ER SÅ LANGT / UNNA AT DET ER UMULIG / Å SE PÅ DAGEN OG PÅ NATTA / DERSOM DET IKKE ER HELT / STJERNEKLART» | TAVLE L1000–1004 | Yes. But «OVERSKYET» is written fainter, so it may be a **separate, older answer** |
| 15 | tavle-2509-pad.jpg | TavlAI (primary_whiteboard) | 2026-09-25 10:38:16 | «IKKE TV, / MEN PAD PÅ / UTSIDEN AV GLASSET / ←» | TAVLE L1025–1029 | Yes |
| 16 | tavle-2509-sang.jpg | TavlAI (primary_whiteboard) | 2026-09-25 10:21:45 | «GJETT RIKTIG / SANG / [=?] / BACKFLIP [small word, OK?/OPP?]» | TAVLE L1020–1024 | Yes, but the log omits the small "=" mark and the trailing word |
| 17 | tavle-2509-shoplifter.jpg | phone photo of a screen showing the stream (primary_whiteboard) | none (≤ 25.09 17:51; board visible in the 16:20–17:03 cut) | «THILPRTE / OESHF» with a hand-drawn line around it | TAVLE L1036–1040; hint `shoplifter` L281–290 | Partly. **«NOEN SOM VET FASITEN» is not visible** in this photo |

---

## 2. Image-by-image

### 2.1 `app-terje-tskjorte.jpg`: Horde app shop, "T-skjorte i Terje-modell"

- **Type:** Android phone screenshot of the Horde app's shop (Horde Rewards), 600×1333 px. Evidence: **organizer_app**.
- **Status bar:** «12:22». Notification icons for Snapchat and Instagram. Bluetooth, «4G», signal bars, battery «64». No date. Committed to the repo 25.09 12:43:29, so the screenshot is probably from 25.09 12:22 (inference only).
- **Verbatim text:**
  - Printed on the shirt: a script «H» (the Horde logo), then «Terje lurer ikke meg.»
  - Product title: «T-skjorte i Terje-modell»
  - Price: a gold coin icon, then «1 116 897» (app coins, not NOK)
  - Buttons: «Legg til i handlekurv» / «Vis handlekurv»
  - Description, verbatim: «Terje-tskjorten er endelig tilbake, i limited edition grønn. H-logo på brystet, med "Terje lurer ikke meg". Denne ble svært populær under forrige Hordejakt, og vi ble utsolgt på under et døgn. Det går rykter om at de som kjøpte denne sist, økte kredittscoren sin betraktelig. Tilfeldig? Neppe.»
- **English:** "T-shirt, Terje model. 1,116,897 [coins]. Add to cart / View cart. The Terje T-shirt is finally back, in limited-edition green. H logo on the chest, with 'Terje doesn't fool me'. This was very popular during the last Hordejakt, and we sold out in under a day. Rumour has it that those who bought this last time raised their credit score considerably. Coincidence? Hardly."
- **Visual:** a studio product photo against a pale blue-grey wall. The woman has dark wavy hair and tattoos on both forearms, and wears a bottle-green T-shirt and blue jeans, hands in pockets. There are two thumbnails at top right: the same woman, and a curly-haired man in the same shirt. A back-arrow button sits at top left. The price equals the prize sum (1,116,897).
- **Geolocation value:** none. It is a **code** clue. The phrase "raised their credit score" points to the app's Kredittskår feature.
- **Cross-check:** innhold.ts:536 quotes «de som kjøpte denne sist, økte kredittscoren sin betraktelig. Tilfeldig? Neppe.», which matches the screenshot exactly. L535 describes the separate app action (Kredittskår + «terje» → «Du fant et hint! 5008»), and L1237 lists code 5008 as `bekreftet`/`hoy`. **This screenshot does not show the 5008 result.** It only shows the shop item that the community reads as the pointer. Spelling note: the app writes «kredittscoren» (with c) and «Terje-tskjorten».

### 2.2 and 2.3 `fr24-2509-sas364.jpg` and `fr24-2509-sas50j.jpg`: Flightradar24 at Anja's pointing gesture of 25.09 17:22

- **Type:** two FR24 web-map screenshots, 808×716 and 743×689 px. Evidence: **community_observation**. The link to Anja's gesture is **community_interpretation**. **Neither screenshot shows a clock, altitude or speed.** Only the callsign labels «SAS364» and «SAS50J» (red, selected aircraft) are shown.
- **Visible base-map labels:** Beitostølen, Biri, Gjøvik, Rena, Elverum, Kongsvinger, Drammen, «E6» shields, a «…sjonalpark» label at top left (Jotunheimen), and the Swedish border (black line, right).
- **Tracks as drawn:**
  - **SAS364:** leaves OSL southbound (green segment), turns left (east, then north) and climbs (cyan → blue). It then runs almost exactly **due north along ≈ 11.39–11.41° E**, passing ~9–10 km west of Elverum and ~1 km east of Rena. The track is violet near the aircraft, meaning higher altitude on FR24's colour scale.
  - **SAS50J:** leaves OSL southbound, turns left and heads NNE (≈ 5°). The track is blue near the aircraft (FR24 ≈ 20 000 ft range).

**My georeferencing (model output; scripts in `whiteboard_photos_a_files/`):**
- I fitted a north-up Web-Mercator similarity transform to the town dots. Control points: Rena 61.1348/11.3649, Elverum 60.8819/11.5623, Gjøvik 60.7957/10.6916, Biri 60.9571/10.6143, Kongsvinger 60.1905/11.9977, Drammen 59.7439/10.2045, Beitostølen 61.2466/8.9097. These are town-centre coordinates from memory, ±0.01°.
- Residuals: 1.0–1.8 px (Gjøvik 5.7 px, where the label contaminates the dot) for the SAS364 image at 622 m/px, and 2.3–2.8 px for the SAS50J image at 529 m/px. **Accuracy is about ±1 km.**
- **Validation:** the extracted SAS50J track pixel at y=461 maps to 60.436 N, 11.470 E. The community ADS-B track (innhold.ts:1641) at that latitude gives 11.473 E, a difference of 0.003°. The SAS50J icon maps to **60.5768 N, 11.5316 E**. The ADS-B track passes 60.5768 N at **17:21:29.8**, at 11.5355 E (0.2 km away) and ~21 800 ft.

| Object | sas50j screenshot | sas364 screenshot |
|---|---|---|
| **SAS50J** | red icon 60.5768 N 11.5316 E → ADS-B time **≈ 17:21:30**, ~21 800 ft; Stange municipality; 24 km SE (az 130°) of Stange centre, 29 km SSE of Løten, 34 km S of Elverum | yellow icon at 60.6085 N 11.5375 E → ADS-B time **≈ 17:21:47**, ~22 400 ft; still in Stange; 30.5 km S of Elverum |
| **SAS364** | the dim yellow icon at top is 61.3325 N 11.3645 E: 22.0 km due N of Rena, Åmot municipality | red icon 61.3732 N 11.3647 E: 26.6 km due N of Rena, Åmot |
| **Unidentified northbound jet** (not mentioned by the community) | yellow icon 60.7420 N 11.3322 E: Stange, 8.5 km S of Løten, 15.5 km ESE of Hamar | yellow icon 60.7790 N 11.3316 E: Løten municipality, 4.4 km S of Løten centre |

- The three aircraft moved 3.5 km (SAS50J, heading 5°), 4.5 km (SAS364, heading 0°) and 4.1 km (unknown, heading 0°) between the two screenshots. That fits a gap of **≈ 17 s** at 209, 267 and 243 m/s. The SAS50J screenshot was taken first and the SAS364 screenshot about 17 s later.
- The other yellow icons are clustered around OSL (approach and departure traffic) and scattered elsewhere (Valdres/Hallingdal, Sweden). They are not relevant.
- Municipality attribution uses `magnus/public/data/kommunevurdering.json`. SAS50J reached **Løten** municipality by 17:22:41 (ADS-B 60.7043/11.5471).

**Cross-check with innhold.ts:**
- L1043: «Flightradar24 rundt da: SAS50J over Stange/Løten og SAS364 over Rena». SAS50J over Stange, then Løten, is **correct**. The SAS364 *track* passes over Rena, but at the screenshot moment (≈ 17:21:30–47) the aircraft was **22–27 km north of Rena** over Åmot.
- L1045 alt text «SAS50J nordover mellom Hamar og Elverum» is **inexact**. At the screenshot moment it was SE and S of both towns (~35 km from Hamar, ~34 km from Elverum) and had not yet reached the Hamar–Elverum line.
- L248: «rundt 17:21–17:22 ekte tid … på 21 000–23 000 fot» is **consistent** with the derived 17:21:30 / 21 800 ft and 17:21:47 / 22 400 ft.
- **Missed by the community:** a **third northbound jet** was in the same corridor at that moment, about 15–25 km **closer to Hamar and Løten** than SAS50J. It was over the Stange/Løten border at ≈ 11.33 E, flying due north. If Anja's box is near Hamar/Løten, that aircraft (callsign unknown; it needs an ADS-B lookup for 25.09 17:21 around 60.76 N 11.33 E) is at least as good a match for her gesture as SAS50J.
- **Tension with primary evidence:** that same morning Anja wrote «FLYENE ER SÅ LANGT UNNA AT DET ER UMULIG Å SE PÅ DAGEN …» (§2.14). She has also written «LYDTETT» (23.09 17:49, L917) and «INGEN LYD I BOKSEN OVERHODET» (24.09, L970). A daytime "pointing at a plane" at 17:22 therefore needs caution. Possible explanations include a contrail after the afternoon clearing (the community reports sun into the camera at 16:45–16:50, L268), or a gesture that meant something else. This is a reading of the evidence, not a refutation.

### 2.4 `stream-2509-hand.jpg`: the hand in the heather

- **Type:** monochrome (IR-look) stream crop, 543×483 px. No overlay and no clock. Committed 25.09 17:54:47. Evidence: **primary_stream_visual**.
- **Text:** none.
- **What it shows:** a **wooden articulated hand**, like the jointed artist's/mannequin hands sold for drawing practice. Joint dots are visible on the fingers in the enhanced crop (`hand_stream.png`, `hand_treslag.png`). It is mounted upright on a **black stake** pushed into the ground. It stands in the heather/bilberry in front of the box platform. All four fingers point straight up, and the thumb angles out to the image right: an **open hand (five digits extended)**.
- **Behind it:** the whiteboard, seen as a white panel with a dark frame. Its black eraser block is at the board's top-left in this frame; at 18:13 it is at top-right, so this is a different moment from `tavle-2509-treslag.jpg`. Below the board is the platform edge with bright specular dots (lamp reflections on the frame). To the right is a small leafless woody stem (young shrub or sapling) with bright IR speckles.
- **Ground:** dense low shrubs (bilberry/heather), grass blades, and fallen dead leaves on the ground (autumn leaf fall).
- **Same object in other frames:** the hand appears in `tavle-2509-treslag.jpg` (25.09 18:13:23) in the same pose, and a dark stake-mounted silhouette stands in the same place in the colour frame from 16:20–17:03 (§2.5). It is **not visible** in the 25.09 09:49–10:38 TavlAI crops (`bw_montage.png`). Those crops are framed differently, though, so this does **not** prove the hand was absent in the morning.
- **Cross-check:** hint `hand-tilbake` (L272–280) says «En hånd står igjen i lyngen foran kassen … Den står rett opp med åpen hånd.» That is **consistent**. The log does not mention that it is a wooden articulated model hand, which matters: its finger positions can be set by hand, so it can be re-posed to show numbers. The earlier sign had hands under the «Horde» logo (L625–630, and `mkekeoooo/figurer/fig_lyshendelse.png`, night crop). That the 25.09 hand is one of those hands is plausible but **unverified**.

### 2.5 `stream-2509-skilt-tilbake.jpg`: wide colour frame from the 25.09 "balloon video"

- **Type:** colour stream frame, 900×467 px. Per innhold.ts:266 it comes from the default.no recording `202609251620_202609251703`. Committed 25.09 17:55:41. Evidence: **primary_stream_visual**.
- **Verbatim text:**
  - Wooden sign: «HORDE» (dark red capitals). The final E is cut by the image edge.
  - Anja's T-shirt: «FINN MEG»
  - Money box: «1116 / 897 / KR»
  - Whiteboard, faint: «THILPRTE / OESHF» (first letters barely resolved; enhanced in `skilt_*.png`)
- **English:** "HORDE"; "FIND ME"; "1,116,897 NOK".
- **The sign:** made of 2–3 horizontal planks, cut to an **arrow shape pointing to image-left**, towards the box. The letters are painted in red-brown block capitals. It is mounted on a wooden post, with a **white-barked birch trunk** directly behind it. It stands to the right of the box, some way out. This is **visually different** from the sign in the 21.09–23.09 night crops (`fig_lyshendelse.png`), which was the cursive «Horde» logo carried by hands in front of the box. The 25.09 sign may therefore be a **new or different sign**, not the original put back. innhold.ts L269 allows for this («Enten er skiltet satt tilbake, eller så er det et annet skilt»).
- **In the box:**
  - Anja sits on the left in a short-sleeved grey/white «FINN MEG» T-shirt, handling something at her lap. Her hair is tied up.
  - Grey pillows/sleeping bag on the left; an olive sleeping bag behind the balloons.
  - A white container with a dark round face (see §2.9), and the fox plush («Benny», L904).
  - **Balloons:** 3 green, ~7 yellow, 1 pale pink, 1 bright blue, 1 lilac/purple (right edge), plus orange and white/cream balloons at the left behind the board.
  - The floor is **covered in multicoloured confetti or balloon fragments**, so balloons have been popped.
  - A black thermos stands on the money box.
- **Balloons vs the letter list:** the balloon colours visible here do **not** map one-to-one onto the 13-letter colour list in L287. Orange and white balloons appear here but are absent from the list, and only one pink balloon is visible where the list has two. No letters on the balloons can be read at this resolution.
- **Vegetation and terrain:**
  - Tall mixed forest with dark conifers (spruce/pine) and several birches with **yellow autumn leaves** in the upper canopy (upper left and upper right).
  - A thin **leaning or fallen pole-tree** runs diagonally behind Anja's head. It may be the same leaning stem seen behind her in the 22.09 monochrome frame (§2.8).
  - Field layer: heather/bilberry, moss and grasses, with scattered yellow leaves.
  - A **dark hollow or depression** in the ground to the right of the box (below the sign), possibly an uprooted-stump pit or a ditch.
  - The box stands on a low platform with a visible grid-like base.
  - No sky is visible.
- **Light:** dim and diffuse in this particular frame, with no direct sun, flare or hard shadows. Sun geometry (model output, `sun_azimuth.py`), at 60.9 N 11.4 E on 25.09: 16:20 alt 17.9° az 231.9°; 16:45 alt 15.4° az 237.9°; 16:50 alt 14.9° az 239.0°; 17:03 alt 13.5° az 242.1°. The sun is at az 221° (the community's camera heading, L138) at about **15:37–15:43 CEST**. At 16:45–16:50, when the community saw sun "straight into the camera" (L268), it would be ~17° right of a 221° optical axis at ~15° altitude. That is compatible with a wide-angle lens, but it is not an exact alignment.
- **Cross-check:** hint `skilt-tilbake` L262–271. Its description («treskilt med «HORDE» til høyre for kassen, formet som en pil som peker mot venstre») is **consistent**. The status «usikker» is appropriate.

### 2.6 `tavle-1909-fly-vilt.jpg`: «LITE MED FLY HER …»

- **Type:** TavlAI monochrome, 1134×660 px. Overlay **«2026-09-23 19:09:54»**. Evidence: **primary_whiteboard**.
- **Verbatim, with enhancement (`1909_line2.png`):**
  - Line 1: «LITE MED FLY HER» (clear; «HER» partly faded).
  - Line 2: «SIKKERT MED VIL?E». «SIKKERT» is readable and the second word reads best as «MED». The last word shows V-I-L, then an unclear glyph (D or T?), then a clear **E-shaped final glyph**.
- **English:** "Not much in the way of planes here." Line 2 is best read as "probably [plenty] of game", or, since «sikkert» also means "safe", "safe with respect to wildlife". The last word may be «VILT» with a stray mark, «VILDE» (the girl's name, or a misspelling), or something else.
- **Visual:**
  - Anja is lying down at left in a white sleeping bag or duvet.
  - A steel bottle/thermos sits next to the money box «1116 / 897 / KR».
  - The board has a black rectangular eraser at top-left and a round black magnet at top-right.
  - The platform's front edge carries a row of bright round dots, and there are bright specular reflections on the glass base (the lamps).
  - Foreground outside the glass: bilberry/heather shrubs.
  - Sun altitude at 19:09 on 23.09: −0.5° at 60.9 N 11.4 E and +0.4° at 59.7 N 9.6 E (civil dusk), consistent with IR mode.
- **Cross-check:** TAVLE L923–927 gives «LITE MED FLY HER · SIKKERT MED VILT (siste ord litt utydelig)». Line 1 matches. **Discrepancy:** «VILT» is not a clean match, because there is a visible extra final glyph «E». The log's own caveat («siste ord litt utydelig») is warranted. The other agent also reads «VIL?E» (whiteboard_log.md, line 127).

### 2.7 `tavle-1912-skilt-borte.jpg`: «SKILTET ER BORTE»

- **Type:** TavlAI monochrome, 1082×714 px. Overlay **«2026-09-23 19:12:22»**. Evidence: **primary_whiteboard**.
- **Verbatim:** «SKILTET ER / BORTE, VET IKKE / HVOR»
- **English:** "The sign is gone, I don't know where."
- **Visual:**
  - Anja sits behind the board in a light sweater printed with numbers. Visible: «7», «10», a partly hidden digit, «12» on one row, and «(1?)6» (or a partly hidden digit plus 6), «18», «9» below. There is also a white **oval patch** with «J.» and «S…» (`1912_sweater.png`).
  - These numbers are consistent with the community's GJELDFRI decode, 7 10 5 12 / 4 6 18 9 (hint `genser`, L540–545). The 5 and 4 are hidden here.
  - The eraser block has moved to the board's bottom-left; the round magnet is still at top-right.
  - Also visible: a steel bottle, a dark cylindrical object (torch or bottle), the money box, and the white sleeping bag at left.
  - The same heather foreground and platform-edge reflections as in 2.6.
- **Cross-check:** TAVLE L928–932, «SKILTET ER BORTE · VET IKKE HVOR». **Matches.** Hint L408–409 notes that the sign was removed on the evening the community began using its bearing.

### 2.8 `tavle-2209-ingen-vann.jpg`: «IKKE MØRKT ENDA / INGEN VANN …»

- **Type:** TavlAI monochrome, 900×688 px. Overlay **«2026-09-22 19:19:32»**. Evidence: **primary_whiteboard**. Only added to the repo on 25.09 20:53 (6c421a9), three days after capture.
- **Verbatim:** «IKKE MØRKT ENDA / INGEN VANN ELLER / VANNLYDER, FØLER / IKKE DET ER VANN / I NOE NÆRHET». The bright spots after «NÆRHET» are **lamp reflections** on the board, not punctuation.
- **English:** "Not dark yet. No water or water sounds, I don't feel there is water anywhere nearby."
- **Visual:**
  - Anja sits on the box floor in front of an **olive folding camp bed with black legs**, holding the board with both hands and a white marker in her right hand. She wears a light top, light trousers and socks, with her hair in a ponytail.
  - A **padlock** hangs on the money box (right edge; the sticker digits «11…/89…» are partly visible).
  - Black eraser block at the board's bottom-right.
- **Background (`2209_bg` crop):**
  - A small **young spruce** (conical) at upper left.
  - A **thin trunk leaning diagonally** across the upper centre.
  - Several tall straight trunks at the right (pine or spruce).
  - Dense, bushy broad-leaved undergrowth (birch/rowan/willow-type saplings).
  - No open water, sky or buildings.
- **Light:** sun altitude at 19:19 on 22.09 was −1.4° at 60.9 N 11.4 E and −0.5° at 59.7 N 9.6 E, just after sunset. That is consistent with «IKKE MØRKT ENDA» and with the camera being in IR mode.
- **Cross-check:** TAVLE L895–899, «IKKE MØRKT ENDA · INGEN VANN ELLER VANNLYDER, FØLER IKKE DET ER VANN I NOE NÆRHET». **Matches.** The commit message for 6c421a9 says it was used to «drop the riverbank idea» (the «Riverbank» artist name in the god-helg story).

### 2.9 `tavle-2509-5-grader.jpg`: «SIKKERT 5°»

- **Type:** TavlAI monochrome, 846×582 px. Overlay **«2026-09-25 09:58:41»**. Evidence: **primary_whiteboard**.
- **Verbatim (`2509_5g_text.png`):** «SIKKERT 5°», with a short stroke under «SI…», which may be an underline or an erase remnant. Then «TROR DET ER / VARMERE». The «5°» is soft; «5C» is less likely.
- **English:** "Probably 5°. I think it's warmer." It is unclear whether this means "warmer than 5°", "warmer than yesterday" or "warmer than the forecast". The question that prompted it is unknown.
- **Visual:**
  - Anja in a **long-sleeved** «FINN MEG» sweatshirt.
  - The **fox plush** (Benny) at left.
  - A **white cylindrical device or container with a round black face** on its side (unidentified: possibly a heater, fan, speaker, bin or camping toilet). It appears in several frames (`white_device.png`).
  - A dark mug, the olive sleeping bag at right, and the board standing on the floor.
  - Heather and bilberry in the foreground.
  - Greyscale in daylight: the sun was at alt ~20° and az ~130° at 60.9 N 11.4 E. The dull image suggests overcast, which matches the «OVERSKYET» board that morning.
- **Cross-check:** TAVLE L1015–1019, «(kl. 09:58) SIKKERT 5° · TROR DET ER VARMERE». **Matches.**

### 2.10 `tavle-2509-ballongfarger.png`: community rendering of the balloon letters

- **Type:** a graphic made by the map author (Magnus): coloured monospace letters on a dark background, 1292×262 px. **Not a stream frame.** Evidence: **community_interpretation**.
- **Text:** «EEFHHILOPRSTT» (the 13 letters of THILPRTE OESHF, sorted alphabetically).
- **Colours, sampled median RGB:**
  - E #4c8c49 green
  - E #b197ff lilac
  - F #6798da blue
  - H #a58946 ochre/"yellow"
  - H #a58946
  - I #a58946
  - L #f98caf pink
  - O #f98caf pink
  - P #4c8c49 green
  - R #a58946
  - S #a58946
  - T #a58946
  - T #4c8c49 green
- **Cross-check:** hint `shoplifter` L287, «grønn E, P og T · lilla E · blå F · gul H, H, I, R, S og T · rosa L og O». **Exact match** (green 3, lilac 1, blue 1, yellow 6, pink 2).
- **Caveat:** this is Magnus's transcription of a video I cannot see here. The balloon counts in §2.5 do not verify it.
- **Anagram check (my arithmetic):** T×2, H×2, E×2, I, L, P, R, O, S, F = 13 letters. These are identical multisets to THE SHOPLIFTER, FILTER THE SHOP and HELHET FOR TIPS. `magnus/public/data/shoplifter.json` lists many more English anagrams, so one exact anagram proves little on its own.

### 2.11 `tavle-2509-god-helg.jpg`: Horde's Facebook story, «GOD HELG ♡ / OG GOD JAKT»

- **Type:** a phone screenshot of a **Horde story**. Header: Horde's «H» avatar, «Horde 6 min», music line «Goldenrod · Riverbank», a mute icon, and the ⌄ ⋯ ✕ controls. 600×1066 px. Evidence: **organizer_media** (the board content is Anja's). Committed 25.09 12:43:29, so the story was posted ≤ ~12:37.
- **Verbatim, board:**
  - Drawing of a **wicker fruit basket** with a bow on the handle. It holds an apple (with stem and leaf), an orange (dotted peel), a strawberry, a pear, a banana lying along the rim, and a bunch of grapes.
  - To the right, written at an angle: «OG / GOD JAKT».
  - Bottom: «GOD HELG ♡».
- **English:** "Have a good weekend ♡ … and good hunting." 25.09.2026 is a **Friday**.
- **Visual:**
  - Anja is smiling, in a **short-sleeved** light grey «FINN MEG» T-shirt, with her hair wet or slicked back and white socks. The board rests on a greenish/olive surface.
  - The photo is taken from **outside the glass at low height**: bilberry sprigs in the foreground, glass edge at the bottom. It is a different vantage from the stream cameras.
  - Background (`godhelg_bg` crop): dense **bilberry-dominated field layer** with yellow-green and some reddish-brown autumn leaves, and tall straw-coloured grass (wavy hair-grass type).
  - A **young spruce** at right.
  - Two tree trunks: a grey, lichen-spotted one at left (birch or aspen with dark patches) and a dark rough one at right (pine or spruce).
  - The vegetation fills the frame up to the top behind her, so the ground **appears to rise** behind the box. A low, zoomed camera angle could produce the same look, so this is an interpretation only.
  - Soft, diffuse light with no shadows: overcast.
- **Clothing timeline (inference):** at 09:49–10:38 on 25.09 she wore a long-sleeved sweatshirt, and from 16:20 and at 18:13 a short-sleeved T-shirt. On 24.09 she wore the same T-shirt at times (`tavle-troa-pa-dere.jpg`, `tavle-kom-fra-den-veien.jpg`). So the photo was taken either on 25.09 between ~10:40 and ~12:37, or on an earlier day. **The capture date is not established.**
- **Cross-check:** TAVLE L1030–1034 and hint `god-helg` L300–310. The fruit list in L306 («eple, appelsin, banan, pære, jordbær og druer») **matches** my reading. «Goldenrod · Riverbank» **matches**. L306 says the music «var ikke på streamen» ("was not on the stream"); that is consistent with this being a Facebook story.

### 2.12 `tavle-2509-ingen-take.jpg`: «INGEN TÅKE»

- **Type:** TavlAI monochrome, 714×582 px. Overlay **«2026-09-25 09:49:11»**. Evidence: **primary_whiteboard**.
- **Verbatim:** «INGEN TÅKE». The initial I is faint; the ring on Å is visible.
- **English:** "No fog."
- **Visual:**
  - Anja sits cross-legged holding the board, in the long-sleeved «F…» (FINN MEG) sweatshirt and light trousers.
  - A black object (phone or power bank) lies on the floor at left, with the olive sleeping bag at right.
  - Background: dark forest undergrowth and trunks, and a diagonal branch at upper right.
  - Dull greyscale in daylight (sun alt ~17.7°, az ~127° at 60.9 N 11.4 E).
- **Cross-check:** TAVLE L1010–1014, «(kl. 09:49) INGEN TÅKE». **Matches.**

### 2.13 `tavle-2509-koder.jpg`: «KAN IKKE TESTE KODER …»

- **Type:** colour wide-camera crop, 551×507 px. No overlay. Evidence: **primary_whiteboard**. Committed 25.09 11:29. She is wearing the long-sleeved sweatshirt, so this is the morning.
- **Verbatim, best effort (low resolution; `koder_text.png` and `koder_text2.png`):**
  - Line 1: «KAN IKKE TESTE» (plausible)
  - Line 2: «KODER» (plausible)
  - Line 3: «INGEN HAR FUNNET» (plausible)
  - Line 4: **illegible**, about 7–9 characters. «BOKSEN» (6) is possible, but so are «MEG ENDA» and others.
  - Stalks of vegetation in front of the glass cross the lower board.
- **English:** "Can't test codes. Nobody has found [the box / me yet?]."
- **Visual:**
  - Wide colour view of the glass box, with Anja seated facing left in the long-sleeved «FINN MEG» sweatshirt.
  - The dark vertical element with short pegs at left is the **box's internal ladder**, as in the 24.09 wide frames («en stige», L829), **not** a spruce trunk.
  - Also visible: the fox plush, the white cylindrical device, a navy bag, and the olive sleeping bag.
  - On the money box: a white bottle, a dark jar or can, and a **plate with food (orange-yellow, probably pizza slices)**. The money box shows «1116 / 897 / KR».
  - Forest: tall trunks, **yellow birch foliage** in the canopy, and a dark conifer understorey.
  - Ground: heather, bilberry and moss with yellow leaves. A dark area at the right foreground.
- **Cross-check:** TAVLE L1005–1009, «KAN IKKE TESTE KODER · INGEN HAR FUNNET BOKSEN (siste del litt utydelig)». Lines 1–3 are plausible. **«BOKSEN» cannot be confirmed from this image.** The log's caveat is warranted. The other agent reached the same conclusion (whiteboard_log.md, line 145).

### 2.14 `tavle-2509-overskyet.jpg`: «OVERSKYET / FLYENE ER SÅ LANGT UNNA …»

- **Type:** colour crop, 728×526 px. No overlay. Evidence: **primary_whiteboard**. mkekeoooo's report gives **25.09 08.46**, paraphrased as «Overskyet. Flyene er så langt unna at de er umulige å se.» (`mkekeoooo/rapport/Hordejakten_2026_fullstendig_rapport.pdf` p.3 and `…_kortrapport.pdf` p.3). Committed 25.09 11:29.
- **Verbatim (`oversk_text.png`):**
  - «OVERSKYET», written **noticeably fainter** than the rest, with a faint horizontal stroke above it.
  - «FLYENE ER SÅ LANGT»
  - «UNNA AT DET ER UMULIG»
  - «Å SE PÅ DAGEN OG PÅ NATTA»
  - «DERSOM DET IKKE ER HELT»
  - «STJERNEKLART»
- **English:** "Overcast. The planes are so far away that it is impossible to see [them] in the daytime, and at night unless it is completely clear and starry."
- **Visual:**
  - Anja in the long-sleeved «FINN MEG» sweatshirt behind the board.
  - A can and a glass jar with a stick or straw; a yellow item behind.
  - The **olive camp bed** (black legs) with the olive sleeping bag.
  - The black eraser block at the board's right edge.
  - Heather and bilberry in the foreground.
  - Muted, low-contrast colour, consistent with overcast.
- **Cross-check:** TAVLE L1000–1004. The wording **matches** (the log adds a comma after DAGEN). **Flag:** the fainter «OVERSKYET» suggests it may be the remains of an earlier, partly erased answer (for example, to "what is the weather?") rather than part of the plane statement. The log merges the two into one entry. The plane statement is the more important one, and it bears on §2.2–2.3.

### 2.15 `tavle-2509-pad.jpg`: «IKKE TV, MEN PAD …»

- **Type:** TavlAI monochrome, 714×528 px. Overlay **«2026-09-25 10:38:16»**. Evidence: **primary_whiteboard**.
- **Verbatim:** «IKKE TV, / MEN PAD PÅ / UTSIDEN AV GLASSET / ←» (a hand-drawn arrow pointing image-left).
- **English:** "Not a TV, but a pad [tablet] on the outside of the glass ←."
- **Visual:**
  - Anja sits cross-legged with a marker in her mouth, in the long-sleeved top.
  - At the far left there is a **tall dark rectangular object** (the arrow points towards it), and next to it the white cylindrical device.
  - Olive sleeping bag at left; black eraser at the board's right edge.
  - Background: dark undergrowth and a diagonal branch.
- **Cross-check:** TAVLE L1025–1029. **Matches.** This corrects L829 («en svart skjerm inne i kassen», "a black screen inside the box"): per Anja, the screen is a pad *outside* the glass. It is how she reads the chat (see L940, «HJELPER VELDIG AT JEG KAN SE DET DERE SKRIVER»).

### 2.16 `tavle-2509-sang.jpg`: «GJETT RIKTIG SANG … BACKFLIP»

- **Type:** TavlAI monochrome, 818×554 px. Overlay **«2026-09-25 10:21:45»**. Evidence: **primary_whiteboard**.
- **Verbatim (`sang_text.png`):**
  - «GJETT RIKTIG»
  - «SANG»
  - a small mark, probably «=»
  - «BACKFLIP», followed by a **small, lower word** that is only partly legible («OK?» / «OPP?» / «OFF?»)
- **English:** "Guess the right song = backflip [OK?]". Presumably, if the chat guesses the song she is thinking of, she does a backflip. Compare «VIL DERE SE EN BACKFLIP?» (L901).
- **Visual:**
  - Anja kneels in the long-sleeved top, looking to her right.
  - The tall dark object at left, the white device, a dark pen or knife on the floor, the olive sleeping bag at right.
  - The platform edge with bright dots, and heather in front.
- **Cross-check:** TAVLE L1020–1024, «(kl. 10:21) GJETT RIKTIG SANG · BACKFLIP». It matches, but the log **omits** the «=» mark and the trailing small word. The hint `god-helg` L307 links this board to the «Goldenrod» music in Horde's story. That link is an interpretation.

### 2.17 `tavle-2509-shoplifter.jpg`: «THILPRTE / OESHF»

- **Type:** a phone photo of a monitor showing the stream (moiré pattern visible), 700×568 px, colour. No overlay. Committed 25.09 17:51:16. The same board is faintly visible in the 16:20–17:03 colour frame (§2.5), so it was written **≤ 16:20–17:03 on 25.09**. Evidence: **primary_whiteboard**.
- **Verbatim:** «THILPRTE / OESHF». A **hand-drawn line** runs from the right of the final «E» of line 1 down and leftwards under line 1 to the right of «F», then down as a slash («/») past «OESHF». It encloses or brackets the two lines as a group.
- **English:** the letters are a scramble (13 letters; see §2.10). There is no Norwegian or English meaning as written.
- **Visual:**
  - Behind the board: balloons (yellow, orange), a navy fabric (sleeping bag or jacket), and an orange/white item.
  - The black eraser block at the lower-right of the board, and thin plant stalks in front.
  - The lower half of the board is **blank** in this photo.
- **Cross-check:** TAVLE L1036–1040, «THILPRTE OESHF (anagram av THE SHOPLIFTER) · NOEN SOM VET FASITEN», and hint L281–290. **Discrepancy:** «NOEN SOM VET FASITEN» (roughly "anyone who knows the answer") is **not visible** anywhere on the board in this photo, whose lower half is empty. It may have been written at another moment. The claim «på samme tavle» (L287) is not supported by this image. The bracketing line is not mentioned in the log.

---

## 3. Consolidated discrepancies and things the community missed

1. **A third northbound jet at 17:21 on 25.09 (my finding, from the community's own screenshots).** An unidentified aircraft was at 60.742 N 11.332 E (≈17:21:30), then 60.779 N 11.332 E (≈17:21:47), flying due north at ~243 m/s over the Stange→Løten border. It was 4–9 km south of Løten centre and ~15 km E of Hamar. The community attributes Anja's 17:22 gesture to SAS50J (innhold.ts:244–250, 1473–1475), but this aircraft is an equally valid candidate, and a closer one for any box near Hamar/Løten. It needs an ADS-B lookup: 25.09 ~17:21 CEST, ~60.76 N 11.33 E, northbound.
2. **The FR24 screenshot times can be derived.** SAS50J ≈ **17:21:30** and SAS364 ≈ **17:21:47** real time CEST, via the SAS50J ADS-B track at innhold.ts:1641 (±~5–10 s). They were taken 17 s apart.
3. **"SAS364 over Rena" (L1043, L1475) is imprecise.** At the screenshot moment it was 22–27 km **north** of Rena over Åmot. Its *track* passes ~1 km east of Rena along ≈ 11.38–11.41 E, and ~9–10 km west of Elverum.
4. **The alt text "SAS50J … mellom Hamar og Elverum" (L1045) is imprecise.** It was ~34 km S of Elverum and ~35 km SE of Hamar, over eastern Stange (24 km SE of Stange centre).
5. **The 23.09 19:09 board ends in «VIL?E», not a clean «VILT»** (L925). The final E-shaped glyph is visible.
6. **The 25.09 «koder» board's last line is illegible.** «BOKSEN» (L1007) is a guess.
7. **«OVERSKYET» is written fainter** than the plane statement and may be a remnant of a different answer (L1002 merges them).
8. **The «sang» board has an «=» and a small trailing word** (OK?/OPP?) that the log omits (L1022).
9. **«NOEN SOM VET FASITEN» is not visible** on the THILPRTE board photo (L1038, L287). The board also has a bracket/outline line, not previously described.
10. **The 25.09 "HORDE" sign is a different object** (a painted plank arrow with block capitals on a post by a birch) from the original cursive «Horde» logo held by hands. L264's «ser ut til å være tilbake» ("appears to be back") should read "a sign is present"; whether it points the same way needs checking in the stream.
11. **The "hand" is a wooden articulated artist's hand** on a black stake, set open (5). Because it is posable, its finger configuration can be changed deliberately. It stood in front of the box by 16:20–17:03 (dark silhouette) and at 18:13 on 25.09.
12. **The dark vertical object with pegs** on the left of the colour wide frames is the internal **ladder**, not a tree.
13. **Tension:** «FLYENE ER SÅ LANGT UNNA AT DET ER UMULIG Å SE PÅ DAGEN» (25.09 morning) and «LYDTETT» / «INGEN LYD I BOKSEN OVERHODET», against the community's daytime "she pointed at a plane" at 17:22. The weather clearing in the afternoon (sun at 16:45–16:50 per L268) could reconcile these, but the gesture's meaning is uncertain. mkekeoooo notes that the stream audio is, per default.no, a looped 24-hour recording («døgnopptak i sløyfe», fullstendig_rapport p.6), so stream audio cannot be used to confirm aircraft either.
14. **Background shows no water, no sky, no buildings, no roads and no signage** in any of these 17 images. Nothing in them names a place.

## 4. Geolocation-relevant observations (all images)

- **Forest type:**
  - Mixed coniferous–birch forest: tall pines/spruces with dark crowns.
  - Many birches with **yellow autumn foliage** on 25.09, and white birch trunks next to the sign.
  - Young spruces in the understorey.
  - Field layer dominated by **bilberry/heather with grasses** (wavy hair-grass type) and moss. Fallen yellow/brown leaves on the ground.
  - This matches Anja's own 25.09 18:13 estimate «KANSKJE 35% BJØRK / 25% GRAN / 40% FURU / AKKURAT RUNDT MEG» (L1049–1053), which is not part of this batch but was viewed for context.
- **Terrain:**
  - A dark hollow or depression right of the box, towards the sign.
  - A leaning thin tree behind the box.
  - The ground behind the box appears to rise in the Horde story photo (interpretation).
  - The box sits on a low platform with a gridded base.
- **Weather and light (primary):**
  - 22.09 19:19: «IKKE MØRKT ENDA», with the sun at −1.4°.
  - 25.09 morning: «OVERSKYET», «INGEN TÅKE» (09:49), «SIKKERT 5° · TROR DET ER VARMERE» (09:58). Dull daylight in the frames.
  - 25.09 afternoon: brighter. The Horde story photo has diffuse overcast light.
- **Aircraft (community / model):** FR24 at ≈ 17:21:30–47 shows three northbound jets in the OSL→north corridor: SAS50J at ≈ 11.53 E, an unknown jet at ≈ 11.33 E, and SAS364 at ≈ 11.36–11.41 E (already north of Rena).
- **Sign bearing (primary + community):** the 25.09 arrow points to image-left, i.e. towards the box. Given the community's camera heading of 221° (L138), image-left is roughly SE. This is an interpretation that depends on the camera azimuth.

## 5. Open questions

1. What is the callsign of the unidentified northbound jet at ~60.76 N 11.33 E, 25.09 ~17:21:30–47 CEST, and at what altitude? This needs an ADS-B archive (adsb.lol, OpenSky, FR24 playback), which is not reachable from this machine.
2. When exactly did Anja point at 17:22 (stream time), in what direction, and at what elevation? This needs the stream recording (default.no cuts, blocked here).
3. What is the last word of the 23.09 19:09 board (VILT / VILDE / other)? It needs a higher-resolution frame.
4. What is the last line of the 25.09 «koder» board? It needs a higher-resolution frame or the default.no TavlAI log.
5. Was «NOEN SOM VET FASITEN» written on the same board as THILPRTE OESHF, and when?
6. Is the 25.09 wooden «HORDE» arrow the same object as the sign Anja measured at 118–120° (L900, L905), or a new sign? Does it point the same way?
7. Does the wooden hand's finger configuration change over time? Tracking it frame by frame on the stream would test whether it encodes digits.
8. When was the Horde story photo (god helg) taken, and by whom? An organizer at the box, or a separate camera?
