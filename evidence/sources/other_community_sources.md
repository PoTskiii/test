# Other public community sources for Hordejakten 2026 (reachable from this machine)

Written 2026-09-25, late evening (about 22:20–23:00 UTC, so 00:20–01:00 CEST on 26.09). Author: sub-agent "other-repos".
Scope: find public GitHub repositories, gists and GitHub-hosted mirrors other than the two already mirrored locally
(`MagnusPladsen/hordejakten-2026` → `data/raw/magnus`, `mkekeoooo/hordejakten-2026` → `data/raw/mkekeoooo` + `data/raw/mk_bevis`).
The main goal was a default.no snapshot newer than 24.09 18:36, plus new hints, field reports or candidate coordinates.

Evidence classes used below: **(a) primary** (whiteboard/tavla, stream, organizer, Horde app responses); **(b) community observation**;
**(c) interpretation/theory**; **(d) model output**. No interpretation below is upgraded to fact.

---

## 0. Bottom line

1. **I found no public GitHub, gist or GitHub Pages mirror of default.no data newer than the local 24.09 18:36 snapshot.**
   BobTheShoplifter (the default.no operator) has 14 public repos and 2 gists. None of them relate to Hordejakten or default.no. The only
   GitHub repo that mirrors default.no data is still MagnusPladsen/hordejakten-2026. Its remote HEAD `68faa86` (25.09 21:04 CEST) is the
   same commit as the local mirror. The last change there to the default.no files was a removal (25.09 14:12, "Remove everything about
   Birkebeinervegen"), not a new fetch.
2. **The mkekeoooo repo has moved on since the local mirrors were made. There are 3 new commits, now cloned into**
   `data/raw/extra/_updates/mkekeoooo__hordejakten-2026`:
   - main `b067a04` (25.09 23:23 CEST) and `ea842e4` (25.09 23:59 CEST) change only the README. They record **new observations of
     afternoon direct sun ("solstjerne") on the stream on 23.09 at 16:45 and 16:50 CEST, and on 25.09 around 17:00 CEST.** They also
     formally **retract** the earlier assumption of a fully overcast afternoon on 25.09, and propose Engerdal–southern Femund and
     Solør/Finnskog for further study.
   - bevis branch `e8178da` (25.09 22:57 CEST) adds a **satellite "sun map" for 25.09 14:30–15:10 UTC** (model output) and an MTG
     truecolour/cloud-type image. The extracted files are in `data/raw/extra/_updates/bevis_new_files/`.
3. **There are 3 other relevant public repos, all now cloned into `data/raw/extra/`:**
   - `Secker17/horde`: source code of the fan site **hordejakten.vercel.app** (municipality rating map and a "confirmed facts" list). Its
     data lives in Firestore project `hordejakten-ddb64`, not in the repo. The 23.09 state of that data is already copied into the Magnus
     mirror.
   - `FruHege87/HordeVakt`: a GitHub-Actions bot that listens to the YouTube stream audio (Whisper speech-to-text, BirdNET, YAMNet) and
     pushes alerts through ntfy.sh. Its keyword list, committed **22.09 16:58 CEST**, already contains **"ld67" / "ld 67"**, 1–1.5 days
     before the Magnus mirror first reports the LD6788 plate (a timeline anomaly, see §6).
   - `danielmb/hordejakten`: a **2023** script that downloads HLS segments from `https://bsstorm.horde.no/hls/stream.m3u8`. It is
     prior-year context only.
4. One empty repo (`fordelabs/hordejakten`, created 25.09 15:14 UTC). All other hits were unrelated. One hit, the repo
   `private-hordeauth/private-hordeauth.github.io`, is an **Italian-language credential-phishing page titled "Benvenuto a Horde"**. It is
   unrelated to the hunt; the clone was deleted and nobody should interact with it.

---

## 1. Access conditions encountered (so later agents do not repeat dead ends)

| Channel | Result |
|---|---|
| WebSearch tool | **Exhausted.** "this session has used its web search budget (200 of 200 WebSearch calls)". No web search was possible in this task. |
| GitHub MCP `search_repositories` / `search_code` / `search_commits` / `search_users` | **Works.** This was the main discovery tool. |
| GitHub MCP `get_file_contents`, issues or PRs of other repos | **Refused.** "repository ... is not configured for this session. Allowed repositories: potskiii/test". `search_issues` returns 0 for other repos. |
| `git clone` / `git ls-remote` of public repos (anonymous proxy) | **Works.** Pull-request refs are not advertised; only `refs/heads/*` and tags are. |
| `raw.githubusercontent.com` | Works (HTTP 200). |
| `api.github.com`, `github.com/<repo>/issues`, `github.com/search`, `github.com/<user>.atom` | **403** from the session proxy ("GitHub access to this repository is not enabled for this session" / "sessions are bound to their configured repositories"). |
| `github.com/user-attachments/files/...` (the ZIPs linked from the mkekeoooo README) | **403**, same message. The ZIP contents could not be fetched. |
| `gist.github.com` user pages and `gist.github.com/search` | **Works** (HTTP 200). |
| npm registry search, PyPI | Work, but return nothing relevant ("hordejakten" → 0 npm packages; PyPI `hordejakten` → 404). |
| `add_repo` (read) for mkekeoooo/hordejakten-2026 | Returned `read_available` (anonymous git read only). Issues need `access:"push"`, which I did not request because the repo belongs to someone else. |
| Vercel sites (hordejakten.vercel.app, hordejakten-2026.vercel.app), Firestore, default.no, EUMETSAT | Not attempted: these are non-GitHub hosts, blocked by task policy. |

---

## 2. Search log (what was searched, so coverage can be judged)

- Repo search: `hordejakten` (4 hits: fordelabs/hordejakten, danielmb/hordejakten, mkekeoooo/hordejakten-2026, MagnusPladsen/hordejakten-2026);
  `hordejakt`, `horde jakten`, `horde-jakten`, `horde skatt`, `hordejakten in:readme` (3 hits: Magnus, Secker17/horde, mkekeoooo);
  `topic:hordejakten` (0); `horde created:>2026-09-19` (44 hits; only Secker17/horde, FruHege87/HordeVakt, fordelabs and the two mirrors
  are relevant); `horde in:description,readme created:>2026-09-20` (194, nothing new); `skattejakt created:>2026-09-15` (1, unrelated);
  `jakten`, `jakt in:name`, `anja boks`, `anja in:name,description created:>2026-09-20` (97, all unrelated or spam); `tavla`, `Evenstad`,
  `kassen skog`, `horde norge`, `millionen`, `treasure hunt norway` (nothing relevant); `default.no` (3188 generic hits, nothing relevant);
  `user:BobTheShoplifter` (14 repos, none relevant); `user:MagnusPladsen` (54, only hordejakten-2026 relevant); `user:mkekeoooo` (1);
  `user:Secker17` (52, only `horde` relevant); `user:FruHege87` (1); `user:fordelabs` (1, empty).
- Code search: `hordejakten` (19 files, all Magnus or danielmb), `EQHgfmZicc8` (2, Magnus), `"horde.no/gjeldfri"` (1, Magnus),
  `"hordejakten.vercel.app"` (6, all Magnus), `"horde.no"` (Magnus, danielmb and unrelated bug-bounty lists), `NOZ9EG` (Magnus only),
  `1116897`, `defaultno`, `osint_notes`, `"Anja Søberg"`, `Jernvinneveien OR Myklebysæterveien OR Madsskardveien`, `BobTheShoplifter`
  (nothing new).
- Commit search: `hordejakten committer-date:>=2026-09-20` (6: 5 Magnus, plus this project's own PoTskiii/test); `horde anja` (1, Magnus);
  `default.no` (generic noise, one Magnus commit).
- User search: `BobTheShoplifter` (found, id 22559547), `hordejakten` (0), `horde in:login created:>2026-09-15` (0).
- `git ls-remote` probes of `{BobTheShoplifter, MagnusPladsen, mkekeoooo, Secker17, FruHege87, fordelabs, danielmb}` ×
  `{hordejakten, hordejakten-2026, hordejakten2026, default.no, defaultno, default, horde, horde-data, hordejakt, hordejakten-data, jakten}`.
  The only hits were the known repos and `BobTheShoplifter/default`, a fork of the Home Assistant HACS `default` list (its branch
  `Remove-And3rsL/Deebot-for-Home-Assistant` shows this); it is unrelated.
- Gists: BobTheShoplifter has 2 (`exfil.py` "ICMP exfiltration", 2023-02-20; `hi.md`, 2020-08-22), both unrelated. MagnusPladsen,
  mkekeoooo and Secker17 have none relevant. Gist search: `hordejakten` 0, `hordejakt` 0, `EQHgfmZicc8` 0, `gjeldfri` 0; `evenstad`,
  `skattejakt`, `anja boksen`, `horde.no` and `default.no` returned only unrelated old gists.
- npm: `hordejakten`, `defaultno` → 0; `horde-jakten`, `anja-horde` → unrelated packages. PyPI `hordejakten` → 404.

---

## 3. NEW vs. local mirrors: mkekeoooo/hordejakten-2026 has moved on

Local mirrors: `data/raw/mkekeoooo` HEAD `d1fbac0` (25.09 04:43 PDT = 13:43 CEST); `data/raw/mk_bevis` HEAD `4baabc5` (25.09 13:09 CEST).
Remote at the time of checking (`git ls-remote`, ~22:20 UTC 25.09): main `ea842e4`, bevis/claude-2026-09-25 `e8178da`.
Fresh clone with both branches: **`/home/user/test/data/raw/extra/_updates/mkekeoooo__hordejakten-2026`** (the mirrors themselves were not modified).

### 3.1 main: commits b067a04 (25.09 23:23:21 +0200) "Dokumenter solobservasjon 25.09 og nytt landsøk" and ea842e4 (25.09 23:59:33 +0200) "Dokumenter ny solobservasjon 23.09 og sammenligning av soldager"

Only README.md changed (`git diff --stat d1fbac0 ea842e4` → README.md, +35/−28; most of the rest is whitespace or re-flow). The new top
paragraphs, verbatim (`_updates/mkekeoooo__hordejakten-2026/README.md:3` and `:5`):

> **Ny originalkontroll: solstjerne også 23.09 kl. 16.45 og 16.50 CEST.** Codex har kontrollert seks bilder fra to minuttklipp. Sammenligningen med 25.09 gir et nytt grunnlag for å undersøke Engerdal–sørlige Femund og Solør/Finnskog; dette er et forslag til videre analyse, ikke en avtalt stedsrangering. [Resultater og svar til Claude · #10](https://github.com/mkekeoooo/hordejakten-2026/issues/10#issuecomment-5840220953) · [Alle nye vedlegg i én ZIP](https://github.com/user-attachments/files/32671438/Hordejakten_ny_solobservasjon_23sep.zip)

> **Ny avklaring 25.09: Direkte sol rundt kl. 17.00 CEST er dokumentert av både Codex og Claude.** Antakelsen om en helt overskyet ettermiddag er trukket tilbake. Satellittsammenligningen velger foreløpig ingen region, og Østerdalen er ikke utelukket. Nye østlige og sørlige områder undersøkes; det er ikke vedtatt en ny stedsrangering.
> [Solobservasjon og landsøk med satellittparallakse · #10](https://github.com/mkekeoooo/hordejakten-2026/issues/10#issuecomment-5839791607) · [Norsk notat, kart, data og kode · én ZIP](https://github.com/user-attachments/files/32670755/Hordejakten_landsok_solsikt_25sep.zip)

Classification:
- "solstjerne" (a sun star, meaning the sun's disc with diffraction spikes seen directly in the camera image) on **23.09 16:45 and 16:50
  CEST** and **25.09 around 17:00 CEST**: a **(b) community observation of primary stream imagery**. It was checked by two AI analysts on
  default.no minute clips (six frames from two clips for 23.09). I have not seen the frames myself, and the ZIP and issue #10 are
  unreachable (403). Stream delay and the clips' clock labels are as default.no marks them.
- **Retraction recorded:** "Antakelsen om en helt overskyet ettermiddag er trukket tilbake" (the assumption of a fully overcast afternoon
  on 25.09 is withdrawn).
- "Engerdal–sørlige Femund og Solør/Finnskog": **(c) interpretation**, explicitly "et forslag til videre analyse, ikke en avtalt stedsrangering".
  "Østerdalen er ikke utelukket" (Østerdalen is not excluded).
- Independent corroboration of the 25.09 observation in the Magnus mirror, `data/raw/magnus/src/data/innhold.ts:263-270` (hint id
  `skilt-tilbake`, source "Opptak av streamen via default.no (202609251620–202609251703)", link
  `https://default.no/cuts/202609251620_202609251703.mp4`): «Solen skinner rett inn i kameraet rundt kl. 16:45–16:50, og hun holder opp
  tavla to ganger.» The same entry notes that a wooden «HORDE» arrow sign is again standing to the right of the box, pointing left.
  Caveat: both groups probably used the **same default.no cut**, so this is not independent footage.
- The inline comment in the new `solkart.mjs` gives the sun window used: «hvor var det klart mens stedet hadde direkte sol 25.09 kl.
  14:33–15:22Z (egne livebilder, solstjerne)», i.e. **16:33–17:22 CEST on 25.09**, from their own live frames.

The README's older "Siste avklaringer" section is unchanged in content: the region is kept open, the pointing gesture is retracted as an
elevation measurement, temperature is not a hard filter, and there are horizon checks of 8.4° / 7.3° / 6.6° at the Jernvinneveien markers.
Repeated coordinates are not new confirmations: «Punktet 61°26′55,3″N 10°58′39,0″E samsvarer innen én meter med default.no sitt site
finder-toppunkt ved A1». There is weak canopy support at A1 (61.4487, 10.9775), and the olivenolje→olivin lead points to Åheim/Almklovdalen.
The historic candidate table is also unchanged: 1 Myklebysæterveien vest 61.3995, 11.0316; 2 Madsskardveien 61.4443, 11.1234;
3 Sørlige Messelt 61.4571, 10.8362 and 61.4545, 10.8406; 4 Madsskardveien øst 61.4518, 11.1428; 5 Jernvinneveien 61.4351, 11.1435.
Other agents cover those in `mkekeoooo_full_report.md`.

### 3.2 bevis/claude-2026-09-25: commit e8178da (25.09 13:57:01 −0700 = 22:57 CEST) "Solkart 25.09 14:30–15:10Z: klart/sky mot klarværsbasis + MTG cloudtype/truecolour (#10)"

New files (extracted to **`/home/user/test/data/raw/extra/_updates/bevis_new_files/`**):
- `solkart.mjs` (38 lines). This is a **(d) model**. It pulls EUMETSAT MTG FCI `mtg_fd:vis06_hrfi` WMS images for 21–25.09 at 14:30,
  14:40, 14:50, 15:00 and 15:10 UTC over the bbox S 58.8, N 63.6, W 6.0, E 13.2 (900 × 1245 px, about 0.43 km/px). The clear-sky baseline
  per pixel is the **minimum** of 21–24.09 in the same slot. The excess on 25.09 is then classified: **green = excess ≤ 15 in at least 4 of
  5 slots ("forenlig", compatible with direct sun); red = ≥ 30 in at least 4 of 5 ("konflikt", cloud); yellow = undetermined.** Verbatim
  header: «Kart: hvor var det klart mens stedet hadde direkte sol 25.09 kl. 14:33–15:22Z (egne livebilder, solstjerne)?»
- `solkart_2509.png` (the classified map; I viewed it). The whole western half of southern Norway (Gol, Fagernes, Otta and west,
  Lillehammer) is mostly **red**. A band from Lillehammer–Gjøvik–Hamar west of Mjøsa is red. Østerdalen south of Koppang, Rena, Elverum,
  Hamar-east, Solør and Oslo-east are **yellow** (undetermined). **Green** areas: Røros–Engerdal–Femund north-east, the Oppdal area,
  Meråker, far south-east (Sweden south of Kongsvinger), and scattered patches.
- `ct_1450.png`: MTG truecolour (left) and cloud-type RGB (right) at 14:50 UTC with town labels. The truecolour shows a **narrow
  cloud-free lane running roughly N–S** from east of Tynset/Røros through between Koppang/Evenstad and Engerdal/Trysil, down past
  Rena–Elverum and on SSW towards Oslo. There is clear ground in the far south-east (Sweden/Østfold); the rest is cloud.
- `README.txt` (my provenance note).

**My own quantification of `solkart_2509.png` (d, derived).** I classified the pixel colours in a 13 × 13 px window (about 5.6 km)
around each point. The file is `bevis_new_files/solkart_2509_point_sampling.csv`; "other" is mostly town-label pixels.

| Point | lat, lon | green (clear) | red (cloud) | yellow (undetermined) |
|---|---|---|---|---|
| K1 Myklebysæterveien V | 61.3995, 11.0316 | 0 % | 22 % | 69 % |
| K2 Madsskardveien | 61.4443, 11.1234 | 0 | 38 | 32 |
| K3 Sørlige Messelt | 61.4571, 10.8362 | 0 | **60** | 40 |
| K4 Madsskardveien Ø | 61.4518, 11.1428 | 0 | 37 | 40 |
| K5 Jernvinneveien | 61.4351, 11.1435 | 0 | 21 | 39 |
| A1 (default.no site-finder top) | 61.4487, 10.9775 | 0 | 21 | 79 |
| P7 | 61.3745, 10.9772 | 0 | 9 | 91 |
| Koppang | 61.57, 11.04 | 0 | 34 | 37 |
| Rena | 61.13, 11.37 | 0 | 0 | 71 |
| Løten | 60.82, 11.35 | 0 | 0 | 76 |
| Elverum | 60.88, 11.56 | 0 | 0 | 71 |
| Trysil | 61.31, 12.26 | 0 | 28 | 43 |
| Engerdal | 61.76, 11.96 | 39 | 0 | 32 |
| Drevsjø (S Femund) | 61.88, 12.03 | **76** | 0 | 24 |
| Elgå | 62.17, 11.96 | **100** | 0 | 0 |
| Flisa (Solør) | 60.61, 12.01 | 0 | 0 | 100 |
| Svullrya (Finnskog) | 60.43, 12.47 | 0 | 23 | 77 |
| Kongsvinger | 60.19, 12.00 | 0 | 53 | 18 |
| Rudshøgda | 60.90, 10.83 | 0 | 7 | 93 |
| Brøttum | 61.03, 10.55 | 0 | **100** | 0 |
| Røros | 62.57, 11.38 | 33 | 0 | 38 |
| Tynset | 62.28, 10.78 | 0 | 33 | 38 |
| Meråker | 63.41, 11.75 | 100 | 0 | 0 |
| Lillehammer | 61.12, 10.47 | 0 | 71 | 0 |

Caveats (from the method and from me):
- The baseline is a 4-day minimum, so a day that was cloudy on all of 21–24.09 in a slot has a biased baseline.
- The sun elevation is only about 11–17° (see §3.3). What matters is cloud **along the line of sight towards WSW (azimuth ~234–246°)**,
  not the pixel directly above the site. At that elevation, a cloud at 2 km altitude is hit about 7–10 km WSW of the camera.
  mkekeoooo's README itself mentions «satellittparallakse»; the published `solkart.mjs` does **not** apply a parallax shift.
- The site only needs a sun gap for part of 14:33–15:22Z, while the classification demands 4 of 5 slots.
- The README says the satellite comparison "velger foreløpig ingen region" (does not yet select any region).
- So the red values at K3 Messelt and Brøttum are soft evidence, not an exclusion.

### 3.3 My geometry check of the afternoon sun observation (d, own computation; NOAA-type formula)

Sun position at 61.42 N 11.08 E (Evenstad). Engerdal (61.76 N 11.96 E) and Finnskog (60.5 N 12.4 E) differ by less than 1.5° in azimuth
and 0.6° in elevation.

| Real time (CEST) | 23.09 az / el | 25.09 az / el |
|---|---|---|
| 16:30 | 234.0° / 17.5° | 233.9° / 16.7° |
| 16:45 | 237.6° / 16.0° | 237.4° / 15.2° |
| 16:50 | 238.8° / 15.5° | 238.6° / 14.7° |
| 17:00 | 241.1° / 14.5° | 241.0° / 13.7° |
| 17:20 | 245.8° / 12.3° | 245.6° / 11.5° |
| 17:22 | 246.2° / 12.1° | 246.1° / 11.3° |

Consistency with the camera model in the local bevis README (`data/raw/mk_bevis/bevis/claude-2026-09-25/README.md`): heading
219.4°, f = 1602 px at 1920 × 1080, giving a half horizontal FOV of 30.9° and a half vertical FOV of 18.6°. Its upper-right box
(x 1500–1920, y 0–300) is stated as «asimut 238–250° og +8,5 til +18,6°». **The 16:45–17:00 CEST sun (az 237–241°, el 13.7–16°) falls
exactly in that upper-right region**, the same region the morning sun lights up at 07:47. This supports a camera heading of about 219–221°
(also written on the tavla as «KAMERA 41 ØST», per Magnus `innhold.ts:138`).

Derived constraint, which is **(c) interpretation**: if direct sun is visible in the frame at about 16:45–17:00 CEST on 23.09 and 25.09,
then the combined terrain and canopy horizon at the camera must be **below about 14–16° at azimuth 237–241°**. If the sun stays direct
until 17:22 CEST (25.09, per `solkart.mjs`), the horizon must also be below about 11.3° at azimuth ~246°. This is only true if the end of
direct sun at 15:22Z is not caused by cloud or by the clip ending, which is unknown. That gives a new **WSW horizon test** to run
alongside the existing morning-sun (ENE) horizon tests. It could hurt sites with a high ridge or valley side to the WSW, and should be
checked against DTM at each candidate.

---

## 4. Secker17/horde: source of the fan site hordejakten.vercel.app

- Clone: **`/home/user/test/data/raw/extra/Secker17__horde`** (HEAD `fb475a6822c9840c301c091450a045569ab8f1d0`, 23.09 20:36:40 +0200, author "Martin <martin@secker.no>").
  The repo was created 21.09 17:22 CEST and has 20 commits (21.09 17:22 → 23.09 20:36).
- Content: a React/Vite app with an interactive map of all 357 municipalities and 15 counties (`public/data/kommuner.geojson`,
  `public/data/fylker.geojson`, Kartverket CC BY 4.0 via robhop/fylker-og-kommuner). An admin can set a rating per area; there is an open
  comment feed, a "Bekreftet arkiv" (confirmed facts) list and a crowd "Gjett koden" 4-digit code-guess widget (`src/CodeLock.jsx`,
  collection `codeGuesses`, top-3 of the last 100 guesses).
- Rating categories (`src/App.jsx:12-16`): `likely` «Sannsynlig» (Sterke spor), `unsure` «Usikkert» (Må undersøkes), `unlikely`
  «Lite sannsynlig» (Svake spor), and **`excluded` «Utelukket» ("Området er avkreftet"), added in commit `a93995b` 23.09 18:46**.
  Disclaimer added 23.09 19:25 (`App.jsx:340`): «PS: Ingen områder kan bekreftes eller utelukkes med 100 % sikkerhet. Vurderingene bygger
  på en samlet tolkning av blant annet vær, vindretning, terreng, avstander og tilgjengelige spor…». A link «Se Default.no for data» was
  added 23.09 20:36 (`App.jsx:341`).
- **The data is not in the repo.** It lives in Firestore project `hordejakten-ddb64` (`src/firebase.js:7-10`, `.firebaserc`). The
  public-read collections per `firestore.rules` are `mapStatuses`, `comments`, `verifiedUsers`, `presence`, `siteContent` and
  `confirmedFacts`. `firebase-debug.log` (21.09 17:58) shows an earlier project id `horde-570cd`. `firestore-debug.har` (21.09
  23:15 CEST, 44 entries) contains only failed Listen/Write channel requests and **no documents**.
  From an unrestricted machine, a Firestore REST read of `mapStatuses` and `confirmedFacts` would give the current state; that was not
  possible here.
- **The 23.09 state is already copied into the Magnus mirror**. This is a **(c) community interpretation** by the site admin, not evidence:
  - `data/raw/magnus/public/data/kommunevurdering.json` (`"kilde":"hordejakten.vercel.app, 23.09"`) has 350 features: **utelukket 164,
    lite sannsynlig 123, usikkert 63, sannsynlig 0**. Unrated: Fedje, Kvitsøy, Lørenskog, Randaberg, Røst, Træna, Utsira.
    - The "usikkert" (not excluded) set is Alvdal, Bamble, Dovre, Drangedal, Eidskog, Elverum, Engerdal, Etnedal, Folldal, Fyresdal,
      Gausdal, Gjøvik, Gran, Grue, Hamar, Hjartdal, Kongsvinger, Kragerø, Kviteseid, Lesja, Lillehammer, Lom, Løten, Midt-Telemark,
      Nissedal, Nome, Nord-Aurdal, Nord-Fron, Nord-Odal, Nordre Land, Notodden, Os, Porsgrunn, Rendalen, Ringebu, Ringsaker, Sel, Seljord,
      Siljan, Skien, Skjåk, Stange, Stor-Elvdal, Søndre Land, Sør-Aurdal, Sør-Fron, Sør-Odal, Tinn, Tokke, Tolga, Trysil, Tynset, Vang,
      Vestre Slidre, Vestre Toten, Vinje, Vågå, Våler (one of the two), Åmot, Åsnes, Østre Toten, Øyer and Øystre Slidre.
    - Examples: Froland "utelukket"; Stad (Åheim/Almklovdalen olivine lead) "lite sannsynlig"; Rosse - Røros, Meråker, Holtålen, Midtre
      Gauldal, Hol, Nesbyen and Gol "lite sannsynlig".
  - `data/raw/magnus/src/data/analyse.json` → `vercelFakta` (the site's "BEKREFTET" list as of 23.09), verbatim:
    «Jenta i boksen heter Anja Søberg.» · «Hun reiste i minst 7 timer etter at hun ble hentet i Oslo.» · «Hun får bind for øynene hver
    gang hun forlater boksen.» · «Det ble mørkt rundt 19:45.» · «Livestreamen starter 06:40.» · «Retningen på kameraet fra henne er 219
    grader.» · «Et hint i appen kan peke mot ordet «Ekorn».» · «Etter å ha vervet noen i appen får man opp bokstaver: I S N D O R U E M
    H.» · «Koden «5008» og navnet «Terje» er to av hintene.»
    These are the site admin's claims; their evidence class varies and each must be traced to its primary source before use. For example,
    "7 timer" and "bind for øynene" should be checked against the tavla.
- Nothing hard-coded in the git history adds facts beyond this (searched `git log -p -S Anja` and App.jsx diffs).

## 5. FruHege87/HordeVakt: automatic audio watcher of the stream

- Clone: **`/home/user/test/data/raw/extra/FruHege87__HordeVakt`**. There are 3 commits: `0bbf1d8` 22.09 16:58:58 +0200 "Add files via
  upload" (adds `hordevakt.py`, `nokkelord.txt`, `requirements.txt`); `e2e872f` 22.09 17:00:35 (workflow); `0e5a090` 22.09 17:49:03
  (workflow update).
- What it does (`hordevakt.py` docstring): every 30 s it takes an audio chunk from the YouTube stream
  (`STANDARD_VIDEO = "https://www.youtube.com/watch?v=EQHgfmZicc8"`, line 33, or whatever video it finds on
  `HORDE_SIDE = "https://horde.no/gjeldfri/hordejakten"`, line 32). It runs faster-whisper (Norwegian speech), **BirdNET**
  (`lat=61.0, lon=9.5`, `min_conf=0.45`, lines 239–240; this is only the script's regional prior, **not** evidence of location) and
  YAMNet (other sounds). It sends ntfy.sh alerts, including a regex for code-like tokens `\b([A-ZÆØÅ]{1,3}\s?-?\d{1,4})\b` (line 79).
  The GitHub Actions cron is `0 */6 * * *` (runs of about 5 h 40 min).
- **Outputs are not public:** the script deliberately writes findings only to a local `logg.txt` («slik at de ikke blir synlige i
  offentlige GitHub-logger»), and the ntfy topic is a secret. The Actions logs are unreachable (API 403). So the repo has **no new data**.
- **Keyword list** (`nokkelord.txt:4-14`, unchanged since 22.09 16:58 CEST): `ekorn`, `nebb`, `rett i nebbet`, `ld67`, `ld 67`, `hint`,
  `kode`, `ledetråd`, `kilometer`, `kommune`, `fylke`. This is a **(b) community artefact** showing which hint words were circulating by
  22.09 afternoon:
  - "ekorn" (squirrel) matches the app's «Verv en venn» → «Hint-hint» squirrel image (Magnus `innhold.ts:576-581`).
  - "nebb" / "rett i nebbet" (beak / "straight in the beak") appears **nowhere** in the Magnus or mkekeoooo mirrors. Its origin is unknown.
  - **"ld67"** is a timeline anomaly; see §6.

## 6. Contradiction or timeline anomaly: "LD67" known by 22.09 16:58 CEST

- Magnus mirror `innhold.ts:385-390`: «Et skjermbilde som er delt i chatten, viser skiltnummer LD6788 lagt inn under «Bil & hus» i appen
  og svaret «Du fant et hint! ENKODE» (rett etter midnatt 24.09). Vi har ikke klart å bekrefte det selv.»
- HordeVakt's keyword file already contained `ld67` and `ld 67` at **22.09 16:58:58 CEST** (commit `0bbf1d8`, `nokkelord.txt:7-8`).
- Interpretation (c): the letters and digits "LD67…" were already circulating in the community about 31 h before the reported ENKODE
  screenshot. That suggests an earlier source for the plate prefix, for example a partly readable plate in a Horde hint or trip video, a
  tavla note, or chat. The source has not been identified. Whoever builds the hints timeline should look for an LD67 mention on 21–22.09.

## 7. danielmb/hordejakten: 2023 edition (prior-year context)

- Clone: **`/home/user/test/data/raw/extra/danielmb__hordejakten`**. There is 1 commit, `feedab3`, 2023-10-19 16:30:57 +0200, message "jaja".
- `main.js:4-5`: `const streamUrl = 'https://bsstorm.horde.no/hls/stream.m3u8'; const m3u8Url = 'https://bsstorm.horde.no/hls/';`. Every
  3 s it downloads new `.ts` segments with a `.info.json` download timestamp.
- Meaning (b): the **2023 Hordejakten** (October 2023) was streamed from Horde's own HLS server `bsstorm.horde.no`, rather than YouTube
  as in 2026. This is useful to the prior-years agent only.

## 8. Other checked items (not relevant or empty)

| Item | Finding |
|---|---|
| `fordelabs/hordejakten` | Created 25.09 15:14 UTC. `git ls-remote` returns no refs, so the repo is **empty**. Re-check later. |
| `private-hordeauth/private-hordeauth.github.io` | Created 25.09 15:03 UTC; a Webflow-exported page, `<title>Posta :: Benvenuto a Hord</title>`, «Autenticazione richiesta … credenziali di posta elettronica». This is a **credential-phishing page unrelated to the hunt**. The clone was deleted; do not visit. |
| `crtGhoul/app-horde` | "APP_HORDE", an index of 4224 apps; unrelated. Clone deleted. |
| `BobTheShoplifter/*` (14 repos) | slidev-addon-studio, supabase-pwn, Spring4Shell-POC, HomeAssistant-Posten, etc.; `BobTheShoplifter/default` is a HACS fork. No default.no source. |
| `TeacherJacob1/skattejakt` | 18.09, a school Python debugging exercise; unrelated. |
| `Johanmkr/tavla` | A research task CLI; unrelated. |
| `xattttt/Anja`, `anjaanzal/anja`, `sjag77/Horde`, many "anja"/"jakt" repos | Unrelated or spam. |
| `PoTskiii/test` | This project's own repo (commit `152752c` "Scaffold Hordejakten 2026 localisation engine"). |
| MagnusPladsen/hordejakten-2026 remote | HEAD `68faa86` = local mirror. No newer default.no data. It has two serverless proxies: `api/kodejakten.ts`, which polls Horde's `https://horde.no/api/spill/status` (POST `{token:'statussjekk'}`; a 503 `not_configured` means the "Kodejakten" game is off), and `api/tiktok.ts` (live status of TikTok `@horde.app`). default.no endpoints referenced in the mirror: `https://default.no/dupedaudio.php`, `/plane.php`, `/map.php`, `/clips.php`, `/cuts/202609251620_202609251703.mp4`. |

---

## 9. Datasets and paths produced or identified

- `/home/user/test/data/raw/extra/_updates/mkekeoooo__hordejakten-2026`: full clone of the current mkekeoooo repo (main `ea842e4`,
  plus `origin/bevis/claude-2026-09-25` `e8178da`). Newer than the local mirrors.
- `/home/user/test/data/raw/extra/_updates/bevis_new_files/`: `solkart.mjs`, `solkart_2509.png`, `ct_1450.png` (from `e8178da`),
  `README.txt` (provenance) and `solkart_2509_point_sampling.csv` (my point sampling).
- `/home/user/test/data/raw/extra/Secker17__horde`: code of hordejakten.vercel.app; `public/data/kommuner.geojson` (357 municipalities,
  properties `kommunenummer`, `kommunenavn`) and `public/data/fylker.geojson`. No hunt data. The Firestore state as of 23.09 is in Magnus
  `public/data/kommunevurdering.json` and `src/data/analyse.json`.
- `/home/user/test/data/raw/extra/FruHege87__HordeVakt`: audio-watch bot and keyword list (22.09 16:58).
- `/home/user/test/data/raw/extra/danielmb__hordejakten`: the 2023 HLS downloader.

## 10. Open questions and recommended follow-ups

1. **Where did "LD67" come from before 22.09 17:00 CEST?** Search the tavla log, hint videos and default.no osint_notes for 21–22.09.
2. **What is "nebb / rett i nebbet"?** It was a hint keyword by 22.09 and is absent from both mirrors.
3. **Run a WSW horizon test** (azimuth 234–246°, elevation 11–17°) at each candidate with DTM/DOM. Direct sun was in frame at 16:45–17:00
   CEST on 23.09 and 25.09, so the terrain and canopy horizon in that direction must be low.
4. **Parallax-shift the 25.09 sun map.** For cloud at 1–3 km, the relevant cloud lies 4–12 km WSW of the site. Re-sample the MTG images
   along the line of sight rather than overhead, and add 23.09 16:45/16:50 CEST (14:45/14:50Z) as a second day. mkekeoooo says the
   23.09/25.09 comparison favours Engerdal–S Femund and Solør/Finnskog, but that ZIP is unreachable from here.
5. Content of mkekeoooo issue #10 and the ZIPs `32671438` and `32670755` (403 here). Someone with normal web access should download them.
6. Current Firestore state of hordejakten.vercel.app (`mapStatuses`, `confirmedFacts`, `comments`) after 23.09. The comments may contain
   field reports of searched areas.
7. `fordelabs/hordejakten` is empty now; re-check later for content.
8. Re-run `git ls-remote https://github.com/mkekeoooo/hordejakten-2026.git` periodically; it is the most active GitHub source (3 new
   commits between 13:43 and 23:59 CEST on 25.09).
