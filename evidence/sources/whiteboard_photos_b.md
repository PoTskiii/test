# Whiteboard photos, batch B: transcriptions, visual forensics, cross-check against the community TAVLE log

Task id: whiteboards-b. Written 2026-09-25, evening (CEST). Analyst: Claude, working only from the local mirrors listed below. No network fetches were made.

## 0. Scope, sources and conventions

**Images examined.** Each one was viewed at full size, then as crops enlarged 3–8x with contrast stretching or high-pass filtering. All are in `/home/user/test/data/raw/magnus/public/img/`:

| # | File | px | Camera / capture type | Git commit that added it (CEST, real time) |
|---|---|---|---|---|
| 1 | tavle-2509-treslag.jpg | 1002×714 | Close, low camera, B/W. TavlAI overlay 2026-09-25 18:13:23 | 4d44d6a, 2026-09-25 19:12:20 |
| 2 | tavle-5-siffer.jpg | 738×582 | Close camera, B/W. TavlAI overlay 2026-09-24 08:24:58 | 1aab84b, 2026-09-24 18:42:43 |
| 3 | tavle-graver.jpg | 485×592 | Main camera, colour, cropped | caf7bcb, 2026-09-24 18:36:00 |
| 4 | tavle-hogd.jpg | 900×1200 | Main camera, **phone photo of a screen** (moiré, scan lines) | a269415, 2026-09-24 18:43:35 |
| 5 | tavle-holde-ut.jpg | 559×685 | Main camera, colour, cropped | 91c7e7d, 2026-09-24 18:33:50 |
| 6 | tavle-ingen-hytte.jpg | 738×606 | Close camera, B/W. TavlAI overlay 2026-09-24 17:20:17 | 4e65b1c, 2026-09-24 18:35:42 |
| 7 | tavle-ingen-lyd.jpg | 513×568 | Main camera, colour, cropped | 4e65b1c, 2026-09-24 18:35:42 |
| 8 | tavle-ingen-pizza.jpg | 685×756 | Main camera, colour, wider crop that shows the canopy | b03c6a9, 2026-09-24 18:32:59 |
| 9 | tavle-kom-fra-den-veien.jpg | 1000×1098 | Main camera, colour | 4e65b1c, 2026-09-24 18:35:42 |
| 10 | tavle-laser.jpg | 900×1200 | Main camera, **phone photo of a screen** | a269415, 2026-09-24 18:43:35 |
| 11 | tavle-mamma.jpg | 686×528 | Close camera, B/W. TavlAI overlay 2026-09-24 18:07:15 | caf7bcb, 2026-09-24 18:36:00 |
| 12 | tavle-pizza-coop.jpg | 358×230 | Main camera, small crop | c0b1da8, 2026-09-24 18:34:08 |
| 13 | tavle-ser-chatten.jpg | 487×581 | Main camera, colour, cropped | dcec931, 2026-09-24 18:33:34 |
| 14 | tavle-skisse-forsterket.jpg | 1020×638 (grey) | 2x upscale plus contrast boost of the board area in #15, made by the community. Not an independent frame | eb4093e, 2026-09-23 15:43:01 |
| 15 | tavle-skisse.jpg | 510×886 | Probably the close camera in colour (daylight) mode; see §5.1 | eb4093e, 2026-09-23 15:43:01 |
| 16 | tavle-troa-pa-dere.jpg | 497×575 | Main camera, colour, cropped | 4e65b1c, 2026-09-24 18:35:42 |

None of the files carries EXIF data; each has only a JFIF header. SHA-256 hashes are in §10.

**Cross-check sources**
- TAVLE log: `/home/user/test/data/raw/magnus/src/data/innhold.ts:880-1054`. Related HINT entries: lines 134-142 (retning118), 184-192 (komfra), 204-211 (graver), 213-221 (hogst), 223-231 (ingenhytte), 233-241 (treslag), 263-280 (skilt-tilbake, hand-tilbake), 433-449 (bindfold, gikk2min), 480-488 (kamera41), 540-546 (genser), 624-631 (skilt), 824-841 (video2309, pluss5), 843-850 (koder).
- Community compass drawing: `/home/user/test/data/raw/magnus/src/components/HintPanel.tsx:171-220`.
- Git history of the magnus repo (`git log`), used for commit-time upper bounds.
- mkekeoooo report: `/home/user/test/data/raw/mkekeoooo/rapport/Hordejakten_2026_fullstendig_rapport.pdf`, p.3 (hint table), p.10 (camera calibration), p.14.
- mkekeoooo figures: `figurer/fig_bildemaling.png` (21.09 main-camera frame, calibration) and `figurer/fig_kjennetegn_1045.png` (21.09 10:45 landmarks).
- Additional magnus frames, for context only: `stream-2509-skilt-tilbake.jpg`, `stream-2509-hand.jpg`, `tavle-1912-skilt-borte.jpg`, `tavle-2509-koder.jpg`.

**Conventions**
- *Board text* is transcribed verbatim, in capitals as written, with the line breaks on the board. `[?]` marks an illegible glyph and `{…}` marks my uncertainty.
- *Times*: "overlay" is the yellow-on-black timestamp burned in by the **TavlAI** capture tool, which is not part of the YouTube stream. Whether it records real time or stream time is **not documented** (open question Q3). The magnus log treats its times as stream time, "trolig 20 sek–1 min forsinket" (innhold.ts:880). mkekeoooo gives "ca. 22–45 sekunder etter virkeligheten" (report p.3). Git commit times are real time, CEST (+0200), and are **upper bounds** on when a board was shown.
- *Evidence grades*: **[P]** primary (board text, stream pixels); **[C]** community observation or interpretation; **[I]** my own interpretation; **[M]** model output.
- *Directions*: "image-left" and "image-right" are as seen on the stream. Converting them to compass bearings needs a camera heading, which is [C] or [M]. mkekeoooo p.10 gives 219.6° (at 59.5°N) or 219.2° (at 61.5°N), f = 1068 px at 1280 px width, and a horizontal field of view of about 188.7–250.5°, from the sun track. The magnus log uses about 221°, and at 23.09 15:22 used 208° before correcting it (git 86d52b8). An arrow drawn on a board held parallel to the image plane therefore points roughly heading − 90° ≈ **129–131°** (image-left) or heading + 90° ≈ **309–311°** (image-right).

---

## 1. Key findings

1. **The "hogd" board is about the walk on 23.09, not the walk in.** The board reads «DET HAR VÆRT / HOGD TIDLIGERE / DER JEG GIKK I GÅR / GIKK DEN VEIEN →».
   - On 24.09, «I GÅR» (yesterday) is 23.09. That matches the 23.09 board «GIKK 2 MIN INN I SKOGEN», which was committed 23.09 19:01 (innhold.ts:922, 443-449).
   - Read literally, the earlier felling lies **about 2 minutes' walk from the box, toward image-right**. With the ~220° heading that is about **310° (NW)**.
   - The magnus hint (innhold.ts:219) instead reads it as the arrival route and advises "Let etter eldre hogstflater **sørøst** … mellom veien og kassen". mkekeoooo (p.3) lists the same board under "Veiretning ca. 130°" and replaces «I GÅR» with "…".
   - These are **opposite sides of the box**. Neither reading is proven [I], but the literal text favours NW and within about 100–200 m.
2. **Anja's gaze supports reading «KOM FRA DEN VEIEN ←» as image-left.** In tavle-kom-fra-den-veien.jpg her head is turned to her right, which is image-left, the way the arrow points [P]. So the arrow was probably not drawn mirror-reversed. Its image-left direction is about 130° under the ~220° heading [I].
3. **The "stige" (ladder) is probably the camp cot stood on end.** The black column with C-shaped steps at the left of the box appears only in frames where the cot is *not* lying flat, and never in frames where it is. In tavle-troa-pa-dere.jpg it leans diagonally, so it is movable. Its height, about the height of the box, fits a cot of about 2 m. See §6.3 and the contact sheet `whiteboard_photos_b_assets/column_vs_cot_contact_sheet.jpg` [I].
   - The magnus hint "video2309" (innhold.ts:829) lists "en stige" as a feature of the box. It is most likely not a clue.
4. **The sketch (tavle-skisse.jpg) contains more than the log records.**
   - It has a dot inside the box rectangle.
   - A horizontal stroke runs from the box's upper-left corner to the left and ends in a group of diagonal strokes (possibly an arrow or path).
   - There is a separate slanted word of 4–5 glyphs at the lower left, and a 3–4-glyph item under the box.
   - No compass rose, north arrow or legible numbers can be seen.
   - **Orientation problem:** with «KAMERA» at the top, a true plan view would put the sign on the camera's *left*. On 21.09 the sign (a cursive "Horde" logo on two supports) actually stood *in front of* the box, between camera and box. The only frame with a sign to the right of the box is from 25.09, and it shows a different sign. So either the sketch is drawn from the viewer's side (mirror-reversed), or «SKILT» is misread, or the sign had moved by 23.09 [I]. See §5.
5. **The 25.09 "returned" sign is a different object.**
   - 21.09: a cursive brass/wood "Horde" logo held up by two supports ("hender") in front of the left half of the box (mkekeoooo fig_bildemaling.png) [P via C].
   - 25.09: a painted wooden arrow board "HORDE" on a post, right of the box, pointing left (stream-2509-skilt-tilbake.jpg) [P].
   - innhold.ts:263-269 leaves open whether it was put back or is a new sign. Visually it is **a new sign with a different design**.
6. **The "nattkamera" is not only a night camera.** The close, low camera delivered B/W frames at 08:24, 17:20 and 18:07 on 24.09 and 18:13 on 25.09, all in daylight hours on overcast days. The 23.09 sketch frame from what appears to be the same camera is in colour.
   - This is consistent with a day/night camera that switches to B/W in dim light.
   - The B/W frames therefore agree with «GRÅVÆR HELE DAGEN» (24.09) and «OVERSKYET» (25.09) [I].
   - The close camera also sees the leaning dead stem behind the box, so it looks along roughly the same axis as the main camera [P/I].
7. **The TAVLE log is not in chronological order.** Its header says "i rekkefølgen de kom (nye legges nederst)" (innhold.ts:880), but the 24.09 entries run 17:20 → 18:07 → 08:24 → 11:05. List order cannot be used to date the untimed 24.09 boards.
8. **A tension with the blindfold claim.** innhold.ts:433-439 says, citing hordejakten.vercel.app and unchecked, that Anja is blindfolded whenever she leaves the box. The 24.09 board «SÅ INGENTING SOM IKKE HØRER TIL I EN SKOG I GÅR» (innhold.ts:998, no photo in this batch) and «HOGD … DER JEG GIKK I GÅR» both suggest she could *see* on the 23.09 walk [I].
9. **Several visual facts are confirmed on the stream [P].**
   - The money box has **two black padlocks** on its lid corners.
   - The **door is in the right-hand side wall**, with hardware at mid-height. Under the ~220° heading that wall faces about 310° (NW) [I].
   - Every 24.09 main-camera frame has flat, overcast light with no cast shadows.
   - Tall, straight **pines** with sky between the trunks stand behind the box, with yellow birches to the left and dark spruce to the right.
   - The ground is dwarf-shrub heath (lyng) with fallen yellow leaves.

---

## 2. Per-image transcriptions and descriptions

### 2.1 tavle-2509-treslag.jpg (overlay 2026-09-25 18:13:23; log innhold.ts:1049-1053)

**Board, verbatim**
```
KANSKJE
35% BJØRK
25%GRAN
40% FURU
AKKURAT RUNDT MEG
```
(«25%GRAN» has no space. «RUNDT» has a slightly malformed D.)

**English:** "MAYBE / 35% BIRCH / 25% SPRUCE / 40% PINE / RIGHT AROUND ME".

**Scene [P]**
- B/W close camera, just outside the front glass at heather height.
- Overlay text: "2026-09-25 18:13:23" (top-left) and "TavlAI" (bottom-right).
- Anja, head out of frame, wears a white T-shirt printed «FINN MEG» ("find me"; the F is cut off).
- **Foreground:** dwarf shrubs, dead grass stalks, and a leafless twiggy sapling in front of the board. A **wooden articulated artist's hand** stands upright on a dark stick in the heather, left of centre. It is the same object as in stream-2509-hand.jpg.
- **Inside the box:** a camp cot lying flat on its legs, with duvet and pillows (centre-right). At the left, a white cylinder with a black circular face lies on the floor near the glass, with a coiled cord under it; it could be a heater, fan, speaker or bucket. At the right, a heap of crumpled white paper, wrappers or leaves, and a glass jar at the right edge.
- **Beyond the glass:** heather and shrubs, and tree trunks at top right.
- No shadows. This is 25.09, logged as «OVERSKYET» (innhold.ts:1002).

**Geolocation relevance:** Anja's own estimate of the tree mix, «right around me», is the only quantitative stand description in this batch [P]. It agrees with the visible stand behind the box (pine, birch, spruce; see §7).

### 2.2 tavle-5-siffer.jpg (overlay 2026-09-24 08:24:58; log innhold.ts:984-987)

**Board**
```
5 SIFFER
GANSKE SIKKER
```

**English:** "5 DIGITS / QUITE SURE".

**Scene [P]**
- B/W close camera.
- Anja wears a **light knit beanie**, is wrapped to the waist in a grey sleeping bag and looks toward image-left.
- On the right, a flat surface on a leg at mid-height: the **cot lying flat**.
- At the left, a jacket or sleeping-bag heap. Bottom-left, a bottle or thermos. Far right, a jar.
- Background: dense dark vegetation and a **diagonal thin dead stem** across the upper centre.
- The board is rotated: its black marker holder is at top-right and a black magnet is at bottom-left.

**Log comparison:** the log adds "(om dørlåsen)" ("about the door lock"). **That is not on the board.** It is context taken from the 23.09 board «ELEKTRONISK LÅS PÅ DØRA MED 5 SIFFER» (innhold.ts:918).

### 2.3 tavle-graver.jpg (24.09, time unknown, ≤ 18:36:00 CEST; log innhold.ts:979-982)

**Board**
```
GRÅVÆR
HELE DAG{EN}
```
«HELE DAG» is legible; the final «EN» is faint.

**English:** "GREY/OVERCAST WEATHER / ALL DAY".

**Scene [P]**
- Main camera, colour.
- The whole glass box is in frame. The **glass roof is speckled with dark spots**, probably drops, leaves or needles.
- **Left rear:** a dark vertical column with 5 C-shaped metal steps, running from the floor to about roof height (see §6.3).
- **Right side wall:** a vertical door frame with **handle/lock hardware at mid-height**.
- Anja wears white, sits cross-legged with her hair up, and looks down.
- **Floor:** a yellow-orange sleeping bag and a khaki bag at the left, small orange items at the far left, and the money box at the right, marked «1 116 / 897 / KR».
- **Background:** yellow-leaved birches at upper left, dark spruce at centre-right, straight dark trunks, and a **dead stem leaning** from upper-left to lower-right behind the box. mkekeoooo calls it O1, "Skrå død stamme/stang bak boksen (asimut ca. 218°)".
- Heather with fallen yellow leaves both in front of and behind the box.
- **Light is diffuse; there are no shadows.** This is a primary visual match for the board's text.

### 2.4 tavle-hogd.jpg (24.09, ≤ 18:43:35 CEST; log innhold.ts:994-997)

**Board** (read from a moiré-affected phone photo; readable after contrast enhancement)
```
DET HAR VÆRT
HOGD TIDLIGERE
DER JEG GIKK I GÅR
GIKK DEN VEIEN ——>
```
The arrow is at the lower right, drawn along and after line 4, and points to **image-right**.

**English:** "THERE HAS BEEN / LOGGING [trees felled] EARLIER / WHERE I WALKED YESTERDAY / [I] WALKED THAT WAY →".

**Scene [P]**
- Main camera, photographed off a monitor. There are scan lines, a colour cast, and a black bar at the bottom of the matching tavle-laser.jpg.
- **Left:** the dark column with C-shaped steps; its top looks folded or tapered, like fabric.
- Anja in white sweats sits cross-legged and holds the board up at face height by its top edge.
- **Front-left on the floor:** the fox plush ("Benny", innhold.ts:904), a white thermos and a small red object.
- **Money box** «1 116 / 897 / KR» with **two black padlocks** on its top corners. An orange elongated item and a dark round item, possibly food and a bowl, sit on top of it. There is a grey bag on the right.
- **Background:** yellow birches at the top, dark spruce on the right, the leaning dead stem, and dwarf-shrub heath.

**Meaning:** see §4.1 for the full argument.

### 2.5 tavle-holde-ut.jpg (24.09; ≤ 18:33:50 CEST; log innhold.ts:944-947)

**Board**
```
SKAL KLARE
Å HOLDE UT TIL
NOEN FINNER
MEG
```

**English:** "[I] WILL MANAGE / TO HOLD OUT UNTIL / SOMEONE FINDS / ME".

**Scene [P]**
- Main camera. Anja wears the **beanie**. The **cot is flat** on its legs, with a grey sleeping bag and pillows at the left and yellow-orange and khaki sleeping bags at the right.
- An **amber bottle** stands on the money box, with a white thermos in front of it and the fox at the left edge.
- The upper crop shows yellow birches at the left, dark conifers in the centre and at the right, and a speckled roof.
- Diffuse light.

**Geolocation value:** none (morale message).

### 2.6 tavle-ingen-hytte.jpg (overlay 2026-09-24 17:20:17; log innhold.ts:964-967)

**Board** (tilted)
```
INGEN HYTTE I
NÆRHETEN SOM JEG
VET OM ELLER SER
```

**English:** "NO CABIN IN / THE VICINITY THAT I / KNOW OF OR SEE".

**Scene [P]**
- B/W close camera at 17:20, before sunset, on the "gråvær" day.
- Anja sits cross-legged with no beanie and her hair tied back, holding the board up.
- **Left edge:** two C-shaped steps of the column, and a bag.
- **Right:** a **padlock** hanging on the money box.
- **Background:** dense vegetation and the diagonal dead stem, upper centre.

**Log comparison:** transcription matches the log.

### 2.7 tavle-ingen-lyd.jpg (24.09; ≤ 18:35:42 CEST; log innhold.ts:969-972)

**Board**
```
INGEN LYD I
BOKSEN OVERHODET,
JEG HAR KUN DERE
[?] Å UNDERHOLDE MEG.
INGENTING ANNET
```
There may be one or two faint glyphs before «Å» on line 4.

**English:** "NO SOUND IN / THE BOX AT ALL, / I ONLY HAVE YOU [the chat] / TO ENTERTAIN ME. / NOTHING ELSE".

**Scene [P]**
- Main camera. Anja wears a white T-shirt with a dark print and a ponytail, and looks down.
- The **column with steps is on the left**. A grey sleeping bag lies on the floor. **The cot is not flat.**
- Money box and bottle on the right.

**Meaning [I]:**
- This agrees with «LYDTETT» (23.09 17:49, innhold.ts:917) and «HØRER IKKE MYE FRA BOKSEN» (21.09, innhold.ts:885).
- Sounds she reports, such as the timber "dunking" in innhold.ts:875, were probably heard outside the box, for example during breaks or transport. They were not heard from inside it.

### 2.8 tavle-ingen-pizza.jpg (24.09; ≤ 18:32:59 CEST; log innhold.ts:934-937)

**Board**
```
INGEN
PIZZA
ENDA  ⌒
```
A small arc after «ENDA» looks like a sad-mouth doodle.

**English:** "NO / PIZZA / YET".

**Scene [P]**
- Main camera, wider crop. Anja is smiling and wears the **beanie**. The **cot is flat.**
- **Canopy at the top of the crop:** tall, straight **orange-brown trunks, typical of Scots pine**, with bright overcast sky between them, behind the box. This matches mkekeoooo O10 "Høye furuer med himmel mellom stammene (asimut ca. 219°)". Yellow birch crowns are on the left and dark spruce on the right.
- **Box base:** the floor slab sits on a platform about 0.3–0.5 m above the heather, with a transparent skirt or frame under it.
- **Foreground:** blueberry/lingonberry-type dwarf shrubs, yellow fallen leaves and a few mushrooms or leaves.
- The fox is on the floor at the front-left corner. An amber bottle and a thermos stand on the money box.

### 2.9 tavle-kom-fra-den-veien.jpg (24.09; ≤ 18:35:42 CEST; log innhold.ts:959-962)

**Board**
```
KOM FRA DEN VEIEN
←——————
INGEN STIER
```
A black marker or eraser lies diagonally across the lower left of the board.

**English:** "[I] CAME FROM THAT WAY / ← / NO PATHS".

**Scene [P]**
- Main camera. Anja wears a white T-shirt printed «1 116 897» and a ponytail.
- **Her head is turned to her right, which is image-left, the direction the arrow points.**
- **Left:** the column with 5 C-steps.
- **Right side wall:** the door frame and handle hardware at mid-height, on the side wall between the rear-right corner (about x 800) and the front-right corner (about x 890). It is not on the front face.
- Heavily speckled roof. Money box with padlocks. A red smear or object on the floor right of centre. White thermos, fox and bags at the left.

**Meaning [I]:**
- Her gaze shows that image-left is the intended physical direction; the arrow is not mirror-reversed.
- Under the ~220° heading, image-left is about 130° (SE). So the arrival route came from the SE, as innhold.ts:190 also concludes.
- «INGEN STIER»: there was no footpath on the approach.

### 2.10 tavle-laser.jpg (24.09; ≤ 18:43:35 CEST; log innhold.ts:989-992)

**Board** (phone photo of a screen)
```
2x HENGELÅS 4 tall
1x KODELÅS 5-6 tall
TROR 5
```
«tall» is written in lower case. The hyphen in «5-6» is faint and could be read «56».

**English:** "2× PADLOCK 4 digits / 1× CODE LOCK 5–6 digits / [I] THINK 5".

**Scene [P]:** same session as hogd. Anja sits cross-legged with the board in her lap. The fox and thermos are at the left. The money box has **two black padlocks, one on each top corner**, and an orange item on top. Inside it is a crumpled white or silver item, possibly the "konvolutt" named in the terms (innhold.ts:693) [I]. The column is on the left.

**Log comparison:** matches. The board says «KODELÅS» (code lock). The 23.09 board said «ELEKTRONISK LÅS PÅ DØRA» (innhold.ts:918). These are not contradictory.

### 2.11 tavle-mamma.jpg (overlay 2026-09-24 18:07:15; log innhold.ts:974-977)

**Board:** `MAMMA ♡`

**English:** "MUM <3".

**Scene [P]:** B/W close camera. Anja, with no beanie and a ponytail, blows a kiss. At the right edge is the money box with the digits «1…» / «89…» and a padlock on its lid, and a glass jar at the top right. No location content.

### 2.12 tavle-pizza-coop.jpg (24.09; ≤ 18:34:08 CEST; log innhold.ts:949-952)

**Board**
```
HJEMMELAGET
PEPPERONIPIZZA
DRESSING FRA COOP
KNALLGODT
```

**English:** "HOMEMADE / PEPPERONI PIZZA / DRESSING FROM COOP / REALLY GOOD".

**Scene [P]:** a small main-camera crop. It shows Anja's white clothes, an orange sleeping bag at the right, a grey sleeping bag at the left, and grass or heather stalks in front of the glass.

**Meaning [I]:**
- «HJEMMELAGET» suggests the crew has cooking facilities (an oven) close enough to deliver the pizza.
- «COOP» means the crew shopped at a Coop store. Coop is almost everywhere in rural Innlandet, so this is **weak** as a location clue.
- default.no turned this into points-of-interest layers: `public/data/defaultno/pizza.json` (65 pizza places) and `coop.json` (60 Coop stores in an Innlandet box) [M].

### 2.13 tavle-ser-chatten.jpg (24.09; ≤ 18:33:34 CEST; log innhold.ts:939-942)

**Board**
```
HJELPER
VELDIG AT JEG
KAN SE DET DERE
SKRIVER <3
```

**English:** "IT HELPS / A LOT THAT I / CAN SEE WHAT YOU / WRITE <3".

**Scene [P]:** main camera. Anja wears the **beanie**. The **cot is flat**, with grey and yellow sleeping bags. An amber bottle and thermos are on the money box, and the fox is at the lower left.

**Meaning:** Anja reads the chat, so her boards answer chat questions. It helps to know which question each board answers; this is often missing from the log.

### 2.14 tavle-troa-pa-dere.jpg (24.09; ≤ 18:35:42 CEST; log innhold.ts:954-957)

**Board**
```
JEG HAR TROA
PÅ DERE
```

**English:** "I BELIEVE / IN YOU".

**Scene [P]**
- Main camera. Anja wears a white sweatshirt printed «1 116 89[7]» and a ponytail, leans on her right hand and looks toward image-left.
- **The dark column with C-shaped steps leans diagonally.** Its foot is near the board's left edge and its top is toward the upper-left corner of the glass. So it is a loose, movable object.
- The fox is at the lower left, a green sleeping bag is behind at the right, and the money box and bottle are at the right.

### 2.15 and 2.16 tavle-skisse.jpg and tavle-skisse-forsterket.jpg (23.09, ≤ 15:43:01 CEST; log innhold.ts:908-915)

See §5 for the full analysis.

**Upper half of tavle-skisse.jpg [P]**
- Anja, with her hair tied back and loose strands, looks up toward image-right.
- Her white sweatshirt shows black numerals «10 5 12». Her crossed arms hide the rest, but a fragment of a second line («…8…/…9») is visible at the lower right.
- These are the «7 10 5 12 / 4 6 18 9» GJELDFRI numbers (innhold.ts:540-546). The 23.09 19:12 frame tavle-1912-skilt-borte.jpg shows «7 10 {5} 12 / 4 6 18 9» on the same sweater. The numbers are consistent and add no new information.
- **Background:** olive and brown dwarf-shrub heath and a diagonal dead stem across the upper right. An orange sleeping bag is at the left edge, and a grey cot or pillow at the left.

**Foreground [P]:** out-of-focus, light-brown wooden objects run across the bottom of the frame: finger-like slats, one angled stick and an arc. They are most likely the **wooden hands** (artist's-hand models) of the Horde sign or its supports, very close to the lens [I]. By 25.09 a single wooden hand stood in the heather in front of the close camera (stream-2509-hand.jpg; innhold.ts:273-280).

**tavle-skisse-forsterket.jpg:** this is the same pixels as the board area of tavle-skisse.jpg, upscaled 2x and contrast-enhanced. It is **not an independent source**, and its apparent extra "detail" is upscaling artefact.

---

## 3. Cross-check table against the TAVLE log (innhold.ts)

| Image | Log line(s) | Log text | Verdict |
|---|---|---|---|
| treslag | 1049-1053 | «(kl. 18:13) KANSKJE 35% BJØRK · 25% GRAN · 40% FURU · AKKURAT RUNDT MEG» | ✔ Matches; overlay 18:13:23. The log label "Nattkamera" is misleading (§6.1). |
| 5-siffer | 984-987 | «(kl. 08:24) 5 SIFFER · GANSKE SIKKER (om dørlåsen)» | ✔ Text matches; overlay 08:24:58. ⚠ "(om dørlåsen)" is the log's context and is not on the board. |
| graver | 979-982 | «GRÅVÆR HELE DAGEN» | ✔ (the final «EN» is faint). Diffuse light confirms it visually. |
| hogd | 994-997 | «DET HAR VÆRT HOGD TIDLIGERE DER JEG GIKK I GÅR · GIKK DEN VEIEN → (pil mot høyre i bildet)» | ✔ Text matches. ⚠ The *interpretation* at 213-220 conflicts with «I GÅR» (§4.1). |
| holde-ut | 944-947 | «SKAL KLARE Å HOLDE UT TIL NOEN FINNER MEG» | ✔ |
| ingen-hytte | 964-967 | «(kl. 17:20) INGEN HYTTE I NÆRHETEN SOM JEG VET OM ELLER SER» | ✔ Overlay 17:20:17. The frame is daylight B/W, not "night". |
| ingen-lyd | 969-972 | «INGEN LYD I BOKSEN OVERHODET, JEG HAR KUN DERE Å UNDERHOLDE MEG. INGENTING ANNET» | ✔ (a possible faint glyph before «Å» is irrelevant). |
| ingen-pizza | 934-937 | «INGEN PIZZA ENDA» | ✔ The small sad-face arc is not logged (trivial). |
| kom-fra | 959-962 | «KOM FRA DEN VEIEN ← (pil mot venstre i bildet) · INGEN STIER» | ✔ The log does not record the head turn toward image-left, which supports the direction. |
| laser | 989-992 | «2x HENGELÅS 4 TALL · 1x KODELÅS 5–6 TALL · TROR 5» | ✔ («tall» is lower case on the board). The two padlocks are visible on the money box. |
| mamma | 974-977 | «(kl. 18:07) MAMMA <3» | ✔ Overlay 18:07:15. |
| pizza-coop | 949-952 | «HJEMMELAGET PEPPERONIPIZZA · DRESSING FRA COOP · KNALLGODT» | ✔ |
| ser-chatten | 939-942 | «HJELPER VELDIG AT JEG KAN SE DET DERE SKRIVER <3» | ✔ |
| troa | 954-957 | «JEG HAR TROA PÅ DERE» | ✔ The leaning "stige" in this frame is not mentioned (§6.3). |
| skisse (+forsterket) | 908-915 | «SKISSE av stedet. Beste lesning: «KAMERA» øverst, kassen i midten, «SKILT» til høyre. Ordet til venstre og nederst er ikke lesbart.» | ≈ Agrees with the best reading. Several elements are unlogged (§5.2), and there is an orientation problem (§5.3). |

**Ordering problem (innhold.ts:880).** The header says entries are "i rekkefølgen de kom (nye legges nederst)". The actual 24.09 sequence is: INGEN PIZZA, SER CHATTEN, HOLDE UT, PIZZA COOP, TROA, KOM FRA, INGEN HYTTE **17:20**, INGEN LYD, MAMMA **18:07**, GRÅVÆR, 5 SIFFER **08:24**, LÅSER, HOGD, SÅ INGENTING, and regn **11:05**. Several entries were added at the same moment (commits 18:32–18:43 on 24.09). **Do not infer times from list position.**

**Time bounds from props and clothing [I]:**
- **Morning session, cot flat, beanie on:** 5-siffer (08:24:58), ingen-pizza, holde-ut and ser-chatten. These probably come from the same morning of 24.09, around 08:24.
- **Later session, cot stood on end, no beanie:** graver, kom-fra, troa, ingen-lyd, hogd and laser, together with ingen-hytte (17:20) and mamma (18:07). These are probably from the late morning to evening of 24.09.
- This is a heuristic; she could have taken the beanie off and put it on again.

**Other boards not in the magnus log.** mkekeoooo p.3 lists boards that the magnus TAVLE log does not contain. These are outside this batch and are listed only for completeness:
- «NULL REGN», «det har ikke vært frost», «SER VELDIG MANGE STJERNER» (22.–23.09)
- «DET ER INGEN LYS RUNDT KASSEN» (22.09 21:36)
- «Gule og grønne fugler»

---

## 4. Meaning of the direction boards

### 4.1 «DET HAR VÆRT HOGD TIDLIGERE DER JEG GIKK I GÅR / GIKK DEN VEIEN →»

**Primary facts [P]**
- The words «DER JEG GIKK I GÅR» ("where I walked yesterday") are on the board.
- The arrow points image-right.
- The photo was committed 24.09 18:43:35 CEST, so the board was written on or before 24.09 and «I GÅR» most likely means 23.09.

**Supporting primary context**
- On 23.09 she wrote «GIKK 2 MIN INN I SKOGEN» (innhold.ts:922, logged "23.09 kveld", committed 23.09 19:01).
- She also wrote «SÅ INGENTING SOM IKKE HØRER TIL I EN SKOG I GÅR» (innhold.ts:998, 24.09).

**Reading A (literal, favoured) [I]**
- On 23.09 she left the box and walked about 2 minutes into the forest toward image-right.
- Along that walk there were signs of earlier felling: stumps, slash, a thinning or an old clear-cut.
- If «GIKK DEN VEIEN →» uses the same convention as «KOM FRA DEN VEIEN ←» (image directions), and the heading is about 220°, then:
  - the walk went toward about 310° (NW);
  - there should be an **older felled area within roughly 100–200 m NW of the box**. The distance assumes a slow forest walk of 50–80 m/min for 2 min; it is not measured.
- The side door is in the image-right wall, which faces about 310° under the same heading. A walk out through that door toward image-right is physically natural. This is consistent, not proof.

**Reading B (community) [C]**
- The arrow shows her heading on the walk in: she came from the SE and walked NW.
- The felled area lies SE of the box, between the road and the box (innhold.ts:219; mkekeoooo p.3 "Veiretning ca. 130°").
- **Problem:** the walk in happened on 20/21.09, not «i går» on 24.09. innhold.ts:219 itself admits "Det er uklart hva «i går» viser til".

**Consequence**
- A and B put the felled area on **opposite sides** of the box.
- A search that keys on hogstflater (felled areas) near candidate points should test **both** sides.
- Under A, the target is an older felled area within about 200 m NW. Under B, it is SE between the road and the box.
- Weights: A about 0.6, B about 0.4 [I].

**Caveats**
- The arrow convention (image vs Anja's own frame) is inferred from the kom-fra frame and is not stated by her.
- The 220° heading comes from community and model work.
- She may have been blindfolded on the walk (innhold.ts:433-439, unverified). If so, she could still sense felling underfoot, but «SÅ» ("saw") argues she could see.

### 4.2 «KOM FRA DEN VEIEN ← / INGEN STIER»

- **[P]** The arrow points image-left, and Anja's head is turned the same way.
- **[I]** This supports image-left, about 130° (SE) under the ~220° heading, as the arrival direction.
- **[P]** «INGEN STIER»: no footpaths.
- This reading matches innhold.ts:190 and mkekeoooo p.14 ("Veiretningen omkring 130° … er brukt mykt").

### 4.3 Readings A and 4.2 together (interpretation only)

- The road and the walk in are to the SE (image-left).
- The 23.09 walk to the pause place went NW (image-right), through an older felled area.
- The 25.09 arrow sign stands image-right (NW) and points toward the box (SE).
- If the sign marks the crew's route, the crew's base or pause place may lie NW. That would fit innhold.ts:806-813: "Pausestedet har ikke vinduer eller wifi", "rundt 2 minutter unna".
- This is a hypothesis [I] and is not established.

---

## 5. The sketch (tavle-skisse.jpg): geometry in detail

### 5.1 Which camera, and when

- **[I] Camera.** The framing is Anja's torso above the board, with wooden objects right at the lens and the viewpoint at heather height. This matches the close camera, as in treslag and the 25.09 hand frame, rather than the wide main camera. The frame is in colour because 23.09 was a sunny day («LYDTETT · SOL · VINDSTILLE» 17:49, innhold.ts:917).
- **Time.** The sketch was committed ≤ 23.09 15:43:01 CEST, before the sign was reported gone at 19:12. «KAMERA 41 ØST» was committed 15:45:19 (git 7983773), so it came right after. «118–120 GR ØST» was committed 15:17:06 (git 2eb6f94).
- **Earlier log versions.** At 15:22 (git 86d52b8) the log said Anja "tegnet et kompass" (drew a compass) in connection with «ØST CA 118». A version before 15:43 read the sketch as «SKISSE: et rektangel i midten (kassen?) med ord rundt. Ikke lesbart på bildet.»

### 5.2 Elements and their positions

Coordinates are in tavle-skisse.jpg pixels (510×886). The board runs from y ≈ 535 to 830 and is cropped at both sides. An annotated high-pass image is at `/home/user/test/evidence/sources/whiteboard_photos_b_assets/skisse_highpass_annotated.png`.

| Label | Element | Position (x, y) | Size | Reading |
|---|---|---|---|---|
| A | Rectangle, the thickest strokes on the board (the box) | x 173–325, y 662–720 | ≈152×58 px, aspect ≈2.6:1 | Community: the box. A true plan of the box would be closer to square, so this is schematic. |
| H | Dot or small blob inside A, with faint marks to its right | ≈(245, 690), near the centre, upper half | ~6 px | Unlogged. Possibly Anja ("me") or a short word; unreadable. |
| B | Word at top | x 213–372, y 583–617; centre x ≈292, ≈43 px right of the box centre (249) | 6-ish glyphs | Best reading «KAMERA». The first glyph is larger and may be boxed, possibly a tiny camera icon. |
| C | Word right of the box | x 381–459, y 660–688, level with the upper half of the box, ≈58 px right of its edge | ≈5 glyphs | Best reading «SKILT». Alternatives are not excluded at this resolution (§5.4). |
| E | Horizontal stroke meeting the box's **upper-left corner** and running left | x ≈85–175, y ≈650 | ≈90 px | Unlogged. Possibly a path or arrow to or from the box. |
| F | Group of diagonal strokes rising from lower-left to upper-right at the left end of E | from ≈(20, 648) to ≈(133, 625) | – | Unlogged. Possibly an arrowhead, a slanted word or a path. |
| G | Slanted word at the lower left | x ≈30–140, y ≈680–750 | ≈4–5 upright glyphs, the first S/Z-like | Logged as "ikke lesbart". Unreadable. |
| D | Short item under the box | x ≈198–292, y ≈752–785, ≈35–60 px below it | 3–4 glyphs: a thin stroke, a dark blob, an O with a bright centre, and a trailing stroke | Logged as "ikke lesbart". Could be a number plus a letter or a short word; unreadable. |

- **Not visible:** a compass rose, a north arrow, or any legible number such as «41», «118» or «120». If Anja's compass drawing from 15:22 exists, it may be a different board.
- **Other marks:** a black magnetic holder at the top-left of the board and a black block at the bottom-right.

### 5.3 Orientation analysis

**Evidence**
- **[P] 21.09, main camera** (mkekeoooo `figurer/fig_bildemaling.png`, `fig_kjennetegn_1045.png`). The "Horde" sign is a **cursive logo on two dark supports ("hender"), standing directly in front of the left half of the box**, between camera and box, at x ≈ 500–720 of 1280. The box spans x ≈ 437–835.
- **[P] 25.09 16:20 main camera** (stream-2509-skilt-tilbake.jpg). A **painted wooden arrow board "HORDE" on a post** stands to the **right** of the box and points left.
- **[C]** «KAMERA 41 ØST» is read as: the camera stands at 41° from the box and looks toward about 221° (innhold.ts:480-488). This agrees with the sun-based heading of 219.2–219.6° (mkekeoooo p.10).

**Test 1: a true plan with the camera at the top.** Rotate the plan so that "up" is 41°.
- Right on the sketch is then 131° (SE); left is 311° (NW).
- Someone standing at the camera and looking at the box would see sketch-right on their *left*.
- «SKILT» on the right would therefore put the sign SE of the box, on the stream's left.
- That fits **neither** the 21.09 sign (in front of the box) **nor** the 25.09 sign (image-right, about NW).

**Test 2: a viewer-oriented sketch.** Suppose Anja drew left and right as the audience sees them on stream but put the camera label at the top.
- Then sketch-right is image-right, about 311° (NW). That fits the **25.09** sign position.
- Sketch-left is image-left, about 130° (SE). That fits «KOM FRA DEN VEIEN ←» (24.09).
- The left-hand elements E, F and G could then be the arrival path, the direction she came from.

**Test 3: the sign on 23.09.** The sign may have been moved between 21.09 and 23.09. innhold.ts:630 notes that the hands "ser ut til å ha endret stilling i løpet av 23.09".

**Conclusion [I]**
- The sketch **cannot be used as a true, north-referenced plan.**
- Under the mirror-reversed viewer-orientation reading it is **consistent** with the other direction clues: road side left, about SE; sign side right, about NW.
- The community compass graphic (HintPanel.tsx:171-220, sign at 298°, camera at 41°) is a **community construct**. innhold.ts:138 calls it "Skissen fra fellesskapet". It must not be confused with Anja's own sketch, which has no bearings on it.

### 5.4 Legibility limits

- The source is 510 px wide. Letters are about 8–12 px tall, and JPEG block artefacts are visible (8×8 blocks in the high-pass images).
- The forsterket image adds no information.
- The words for D, E, F and G, and the confirmation of «SKILT» and «KAMERA», need the **original full-resolution frame**: the default.no clip archive, or the YouTube VOD EQHgfmZicc8 on 23.09 some time before 15:43 CEST.
- Useful search cues in the video: Anja in a white numeral sweatshirt, looking up to the right, board at the bottom of the close camera's view.

---

## 6. Details the community missed or mislabelled

### 6.1 The "nattkamera" is a day/night close camera
- **[P]** B/W frames exist at 24.09 08:24:58, 17:20:17 and 18:07:15, and at 25.09 18:13:23. All are before local sunset, about 19:00 CEST at 61°N in late September. The 23.09 frame (sketch) is in **colour**.
- **[I]** The camera switches to B/W in low light, and 24–25.09 were overcast. The magnus labels "Nattkamera 17:20" (innhold.ts:966) and "Nattkamera 18:13" (1052) are therefore slightly misleading.
- **[I]** On a given day, the B/W state could serve as a weak light-level proxy.

### 6.2 What the close camera shows about geometry
- **[P]** The close camera sees the same leaning dead stem (mkekeoooo O1) behind the box, and the same layout: fox at the left, money box at the right.
- **[I]** It looks at the same (front) face of the box as the main camera, from low and close, at glass or heather level.
- **[P]** A wooden artist's hand stands in the heather in front of it (25.09).

### 6.3 The "stige" (ladder) is probably the camp cot stood on end
**[P] Observations**

| Column with C-steps visible | Cot lying flat |
|---|---|
| graver, kom-fra, troa (leaning diagonally), ingen-lyd, hogd, laser, ingen-hytte (left edge, B/W), 2509-koder | ingen-pizza, holde-ut, ser-chatten, 5-siffer (B/W), treslag (B/W), stream-2509-skilt-tilbake, fig_bildemaling (21.09) |

- The two conditions **never co-occur** in the 15+ frames checked.
- In troa the column **leans at about 20° from vertical**, so it is not fixed.
- Its height is about the height of the box, roughly 2 m, which fits a cot's length.
- The C- or bow-shaped steps fit camp-cot legs seen in profile.
- The top looks folded, like fabric.

**[I]** The column is most likely the cot turned on end to free floor space. The "en stige" in the 23.09 video description (innhold.ts:829) is therefore probably not a clue. Confidence is about 0.75.

Contact sheet: `/home/user/test/evidence/sources/whiteboard_photos_b_assets/column_vs_cot_contact_sheet.jpg`.

### 6.4 The 25.09 sign is a new sign, not the old one returned
See finding 5. **[P]** The designs differ: a cursive metal-look logo on two supports versus a flat painted arrow board on a post. innhold.ts:263-269 should say "a different sign". Whether it is the object the 23.09 board «SKILTET ER BORTE» (innhold.ts:929-931) referred to cannot be settled from these images.

### 6.5 The door is in the image-right side wall
- **[P]** The door frame and handle are between the rear-right corner (x ≈ 800) and the front-right corner (x ≈ 890) in kom-fra. The same is visible in graver, holde-ut, ingen-pizza, ser-chatten and troa.
- **[I]** With the camera heading about 220°, that wall faces about 310° (NW).
- **[I]** A person reaching or leaving the box by the door would most naturally use the NW side. This bears on the «GIKK DEN VEIEN →» reading in §4.1.

### 6.6 Locks seen on stream
- **[P]** Two black padlocks sit on the top corners of the transparent money box (hogd, laser, mamma, ingen-hytte). They confirm «2x HENGELÅS» physically.
- **[P]** Inside the money box is a crumpled white or silver item. Given the rules (innhold.ts:689-695), it is possibly the "konvolutt" [I].
- No keypad is resolvable on the door.

### 6.7 «I GÅR» and the blindfold claim
**Contradiction to track:**
- innhold.ts:433-439 says Anja is blindfolded every time she leaves the box. The source is hordejakten.vercel.app, "ikke sjekket selv".
- Her 24.09 boards say «SÅ INGENTING SOM IKKE HØRER TIL I EN SKOG I GÅR» ("saw nothing that doesn't belong in a forest yesterday") and «DET HAR VÆRT HOGD … DER JEG GIKK I GÅR».
- Either she was not blindfolded on the 23.09 walk, or "SÅ" is loose wording. Treat the blindfold claim as unverified.

### 6.8 Heading value was revised
The magnus log used 208° at 23.09 15:22 (git 86d52b8, "kameraet står nord-nordøst og filmer mot ca. 208°") and 221° after «KAMERA 41 ØST» at 15:45. Record this correction; any image-left or image-right conversion made before 15:45 on 23.09 used the older value.

---

## 7. Environment observations useful for geolocation

All of these are [P] observations from the listed frames.

**Tree species (visible)**
- Many slender **birches with yellow autumn leaves**, mostly to the left and upper left behind the box.
- **Dark spruce** crowns, mostly to the right.
- **Tall, straight pines** with orange-brown upper trunks and sky visible between them, directly behind and above the box (ingen-pizza top; mkekeoooo O10 at about 219°).
- Anja's own estimate: **35% bjørk / 25% gran / 40% furu**, right around the box (treslag).
- Autumn colour: birch leaves are mostly yellow on 24.09 and many have fallen. This fits a late-September leaf fall; it is phenology, not a precise location clue.

**Ground cover**
- Dense dwarf-shrub heath (lyng: blueberry/lingonberry type, some reddish leaves), fallen yellow birch leaves, and dry grass stalks near the close camera.
- Mushrooms or leaves are scattered in the foreground (ingen-pizza).
- This agrees with the earlier boards «MYE LYNG», «MASSE SOPP» and «MOSE PÅ STEINER» (innhold.ts:885, 919-920).

**Structures:** no buildings, paths, water, signs or power lines appear in any of the 16 frames. This agrees with «INGEN HYTTE I NÆRHETEN SOM JEG VET OM ELLER SER» and «INGEN STIER».

**Light and weather**
- All 24.09 main-camera frames are overcast and diffuse with no cast shadows, and the sky shows as white between the pine trunks.
- The glass roof is speckled with drops or debris in the 24.09 frames. Rain around 11:05 on 24.09 was reported second-hand (innhold.ts:999); I did not verify it.
- The close camera is in B/W mode on 24–25.09 (dim).

**Terrain**
- The box stands on a raised platform. The foreground heath is roughly level.
- These frames give no reliable slope measure. For measured ground angles see mkekeoooo p.10: M0 at about 218°, −15.3° to −13.7°; B1–B5.

**Landmarks behind the box:** the leaning dead stem (about 218°), a tall trunk directly behind (O5, about 222°), and a birch with a crooked lower trunk to the right (O6, about 238°). These are mkekeoooo labels, visible again in the 24.09 frames here.

---

## 8. What the batch does *not* show
- There are no text clues naming a place, no numbers usable as coordinates, and no bearings on the sketch.
- «KAMERA 41 ØST», «118–120 GR ØST» and «ØST CA 118 · RETNING SKILT» are logged, but none of those boards is in this batch.

---

## 9. Open questions and next steps
1. **Full-resolution sketch frame.** Pull the 23.09 frame, before 15:43 CEST, from default.no cuts or the VOD, to read elements B, C, D, E, F, G and H. This decides whether the sketch is viewer-oriented and whether the left-hand elements mark the arrival path.
2. **Timing of the hogd board.** Find its exact time and the chat question it answered, to confirm that «I GÅR» means the 23.09 walk and to learn the time of that walk. Then check whether she left by the image-right door and whether she was blindfolded.
3. **TavlAI timestamps.** Establish whether TavlAI overlay times are real time or stream time, and who runs TavlAI (probably default.no).
4. **Sign on 23.09.** Where did the sign stand when the sketch was drawn, and when did the 25.09 arrow sign appear?
5. **Cot hypothesis.** Confirm the cot on end by finding a frame that shows the transition.
6. **Mapping test.** Look for older felled areas within about 200 m **NW** of candidate points (reading A), not only SE (reading B), using default.no `public/data/defaultno/hogst/logging_*.png` [M] or Kilden/GFW loss layers.
7. **Pizza and Coop.** Is the timing of the "hjemmelaget pepperonipizza" delivery known? It could bound the crew's driving distance, but only weakly.

---

## 10. Provenance and hashes

**SHA-256** (in `/home/user/test/data/raw/magnus/public/img/`)
```
d2ac40e4baf21f28e2189c9de7b59d41da5b397aa318bb3a901374e1f114e574  tavle-2509-treslag.jpg
781307342f834915362948ec7b78108ac78d9dd6edbc9b85e8fff5bc3f51a637  tavle-5-siffer.jpg
f1a418d5b3436337e970c8032efce6daf4b886ef84d56ed1410be51ab045f088  tavle-graver.jpg
c5441834de164deb10e0075bb384eae4809e36975872e161f368c0bd26c79406  tavle-hogd.jpg
aa2308026eb0533f1691c6fd7201a677a1d22f3c2a32e554e6b0a0c593cafccc  tavle-holde-ut.jpg
afe09b5d3f36307d236ada37ddd01efe8857432d123b2ecd0421f73488cec7b9  tavle-ingen-hytte.jpg
85e65a61cdf0a4ef49d09abfe19559dc5fffe02d019915432b4c408c95393a0c  tavle-ingen-lyd.jpg
c8c4d2294844347159d3607fbf2d5d5453c569404d49668fc500e1838ae24bbd  tavle-ingen-pizza.jpg
92dc372ac515bd5b1d3e23d80d2ce63b892bead98d81a662e5f24de7337e060d  tavle-kom-fra-den-veien.jpg
6715da7d1ecddb97626c2e1a25bd90ad67d3a11ddf24b3e8910626b9838b8f49  tavle-laser.jpg
1892165172607eba3c30c4fc3102eea51dcba1187825e4ff8b164e97d87961fa  tavle-mamma.jpg
b4242f4cf0b139819aac61fdfa4b113df08973fd573883bca33ed830a7014940  tavle-pizza-coop.jpg
8b764ea71eb3f66f2c74d44f46884334c51cf5542879403f70528986572a4ba8  tavle-ser-chatten.jpg
9a06aadd992a17ba843051b54e141e5284416aeb3054190458ffb2624c23f2b4  tavle-skisse-forsterket.jpg
0c641e771aeba827b40f8228df586e97255a31b6787c4f7fe7ccce9ae7bc5a92  tavle-skisse.jpg
b9a26c9892316943fc2ef5c12a9dc2e72c601cf29b26465a1185bb6d332004aa  tavle-troa-pa-dere.jpg
```

**Relevant magnus commits** (CEST, real time)

| Commit | Time | What it added |
|---|---|---|
| c0c849b | 23.09 14:30:30 | repo scaffold |
| cf75140 | 23.09 15:05:31 | «ØST CA 118» |
| 2eb6f94 | 23.09 15:17:06 | «118–120 GR» |
| 86d52b8 | 23.09 15:22:56 | sun clues, sign geometry, "tegnet et kompass", camera 208° |
| eb4093e | 23.09 15:43:01 | sketch images and best reading |
| 7983773 | 23.09 15:45:19 | «KAMERA 41 ØST» |
| 4a9f3ee | 23.09 19:01:16 | «GIKK 2 MIN INN I SKOGEN» |
| b03c6a9 … a269415 | 24.09 18:32:59–18:43:35 | the 24.09 boards |
| ac06655 | 25.09 17:55:41 | sign "back" |
| 4d44d6a | 25.09 19:12:20 | treslag |

**Derived files written by this analysis**
- `/home/user/test/evidence/sources/whiteboard_photos_b_assets/skisse_highpass_annotated.png`: tavle-skisse.jpg board region, gray high-pass (σ = 10 px background subtraction), 3x bicubic, with element boxes A–H.
- `/home/user/test/evidence/sources/whiteboard_photos_b_assets/column_vs_cot_contact_sheet.jpg`: frames with the column visible versus frames with the cot flat.
