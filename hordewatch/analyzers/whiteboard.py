"""Whiteboard detector + OCR (analyzer name: ``whiteboard``).

What it looks for
-----------------
Anja writes clues on a hand-held white board and holds it up, usually close to
the transparent wall of the box, 4-8 m from a camera looking ~220 deg (SW).
A board is a *large, bright, low-saturation, nearly rectangular* region that
is clearly brighter than its surroundings. It is often tilted and seen in
slight perspective. At 1280x720 and ~6 m a 60x40 cm board is only ~110x75 px,
so the minimum area is deliberately small (0.3 % of the frame).

Detection (per frame, bounded CPU: ~10-25 ms on a 640-px working copy)
  1. HSV of a downscaled frame. Board pixels: V above a *relative* threshold
     between the median and the 99.5th percentile (tried at three levels, a
     cheap MSER-like stack, so a board in shade and a board in sun both
     segment) and S below ``s_max`` (ignored in IR/night mode where the image
     is monochrome).
  2. Morphological closing joins the marker strokes, external contours are
     filled, and each blob is tested: rectangularity (area / minAreaRect area),
     convex-hull solidity, aspect ratio 1.0-3.2, minimum side, brightness
     contrast against a surrounding ring, and "textness" (fraction of dark
     ink pixels inside). A 4-corner polygon is fitted (approxPolyDP on the
     hull, falling back to the minAreaRect box) for perspective rectification.
  3. Temporal persistence: a board must be seen in >= ``persist_frames`` (2)
     consecutive sampled frames (one missed frame tolerated) before it is
     announced. Transient reflections on the plastic walls rarely persist.

On confirmation it emits ``whiteboard_visible`` (bbox, corners), calls
``ctx.trigger('whiteboard')`` (the VLM analyzer transcribes it), sets
``ctx.state['archive_next'] = True`` so the ingest keeps the full frame as
evidence, and publishes the rectified crop in ``ctx.state['whiteboard']``.

OCR
  The board is perspective-rectified from the *full-resolution* frame and
  upscaled so letters are ~40 px tall. Ink is taken as min(R,G,B) (black,
  blue and red marker are all dark in at least one channel), illumination is
  flattened (divide by a heavy blur), CLAHE-enhanced, and read by RapidOCR
  (PP-OCRv4, bundled ONNX models, offline). If the confidence is poor, an
  adaptive-threshold binarised variant is read too and the better read wins.
  If ``pytesseract`` + the ``tesseract`` binary with the ``nor`` language
  are installed, Tesseract (``-l nor+eng --psm 6``) is run as a second engine.

Norwegian post-processing
  PP-OCR's character set has no Æ, Ø or Å: Ø is read as 0/O/Φ, Å as A/Ä/Á,
  Æ as AE/E. :func:`fix_norwegian` restores them with a lexicon of clue-ish
  Norwegian words and place names (only when the ASCII-fied form is not itself
  a common word, or - for compass words like OST/ØST - when the context is
  directional: a number, degree sign or another compass word nearby). Digit/
  letter confusions inside words (0<->O, 1<->I, 5<->S) are also repaired.
  The raw OCR text is always kept alongside.

Merging and de-duplication
  Successive reads of the same board (one physical hold = one *track*) are
  merged line-by-line: lines are clustered across reads by text similarity and
  vertical position, and the best-supported / highest-confidence variant of
  each line wins. One ``whiteboard_text`` observation is emitted per board
  (as soon as two reads agree or after ``emit_after_reads`` reads, else when
  the board goes down); a *revision* is emitted only if later reads change the
  text materially. If she flips the board / writes something new while still
  holding it (text similarity drops), a new board instance starts. Texts are
  compared with earlier boards stored in the DB: a board held up again is
  recorded with ``is_new=False`` and ``repeat_of`` but is **not** re-announced;
  only genuinely new text creates a ``db.add_event``.

Extras
  * Times written on the board ("KL 14:30", "14:30") produce ``clock_seen``
    with ``capture_minus_shown_s`` - an upper bound on stream latency.
  * Stable boards (fixtures, a board leaning on the wall for hours) are not
    re-OCR'd every frame: an appearance hash of the rectified crop gates OCR.

Failure modes
  Overcast sky / sunlit tarpaulin can look like a board (rejected mostly by
  rectangularity, border contact and persistence), strong glare on the plastic
  wall can wash out the text, dye-based marker ink is often *transparent in
  near-IR* so boards shown at night may look blank, handwriting is harder than
  print for PP-OCR (the VLM transcription is the complement), and a board
  held at > 45 deg rotation may be rectified sideways (the OCR angle classifier
  only fixes 180 deg).
"""
from __future__ import annotations

import difflib
import logging
import re
import shutil
import threading
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

import cv2
import numpy as np

from ..types import Observation, iso
from .base import Analyzer, Context

log = logging.getLogger("hordewatch.whiteboard")

# --------------------------------------------------------------------------------------------
# Norwegian lexicon (words with Æ Ø Å likely on a clue board: compass, terrain, nature,
# numbers, function words, towns). Only used to restore letters OCR cannot produce.
# --------------------------------------------------------------------------------------------
COMPASS_WORDS = {
    "NORD", "SØR", "ØST", "VEST", "NORDØST", "NORDVEST", "SØRØST", "SØRVEST", "NØ", "SØ", "NV", "SV",
    "ØSTOVER", "SØROVER", "NORDOVER", "VESTOVER", "ØSTLIG", "SØRLIG", "NORDLIG", "VESTLIG",
    "ØSTSIDEN", "SØRSIDEN", "NORDSIDEN", "VESTSIDEN", "ØSTSIDA", "SØRSIDA",
}
NB_WORDS = set("""
SØR ØST NORDØST SØRØST SØRVEST NØ SØ ØSTOVER SØROVER ØSTLIG SØRLIG ØSTSIDEN SØRSIDEN ØSTSIDA SØRSIDA
PÅ NÅ NÅR GÅ GÅR GÅTT SÅ FÅ FÅR FÅTT MÅ MÅL MÅLT MÅTTE FØR FØRST FØRSTE BÅDE NÆR NÆRE NÆRMERE NÆRMESTE
NÆRHETEN HØY HØYT HØYE HØYDE HØYDEN HØYDER HØYDEDRAG HØYRE ØVERST ØVRE ØVRIGE ØVER STØRRE STØRST STØRSTE
SJØ SJØEN INNSJØ INNSJØEN TJØRN TJØRNA MØRK MØRKT MØRKE MØRKET LØV LØVTRE LØVSKOG BJØRK BJØRKA BJØRKER
BJØRKESKOG BÆR BLÅBÆR TYTTEBÆR MULTEBÆR KRÆKEBÆR BÅT BÅTEN BLÅ BLÅTT GRÅ GRÅTT GRØNN GRØNT GRØNNE RØD RØDT
RØDE SNØ SNØEN TÅKE TÅKA STØY LØYPE LØYPA STØ BRØNN ÅS ÅSEN ÅSER ÅSRYGG ÅSRYGGEN SKRÅNING SKRÅ DØR DØRA
HØST HØSTEN VÅR VÅREN SØNDAG LØRDAG MÅNE MÅNEN MÅNED ÅR ÅRET ÅTTE ÅTTI ØY ØYA ØYER ØYNE ØYE HØRE HØRER
HØRT HØRTE SØKE SØKER SØK LØSNING LØSE LØS SVÆRT LÆRE MØTE MØTES HJØRNE HJØRNET GÅRD GÅRDEN GÅRDER KJØR
KJØRE KJØRT HØYSPENT HØYSPENTLINJE MØLLE KRÅKE MÅKE ØRN ØRNEN BJØRN RÅDYR TÅRN TÅRNET KIRKETÅRN SLØYFE
HÅND HÅNDA HÅNDEN NØKKEL NØKKELEN KLØVER FØTTER DØGN DØGNET TØRR TØRT VÅT VÅTT VÆR VÆRET VÆRE HVOR
TRÆR TRÆRNE FJÆRA FJÆRE LØP LØPE LØPER KLØFT DØDE DØD SLÅ SLÅTT STÅ STÅR STÅTT SMÅ SÆR MØNSTER
FJØS KRØTTER SKJÆR HÆL HØNE LYSSTRÅLE STRÅLE ÅPEN ÅPNE ÅPENT ÅLE BRÅTT GRØFT GRØFTA BRØT DÅRLIG
LÅVE LÅVEN LÅS LÅST HÅP HÅPER NÆRINGS SØPPEL BØKER BØK BØKESKOG ØKS FØLG FØLGE FØLGER SØRPÅ ØSTPÅ
ÅLESUND TØNSBERG GJØVIK HØNEFOSS RØROS BÆRUM SØRUM LØRENSKOG FØRDE HØYANGER ÅRDAL LÆRDAL STØREN RØYKEN
ØYER FÅVANG LØTEN ÅMOT ÅSNES VÅLER SKJÅK VÅGÅ SØR-FRON ØYSTESE ÅMLI SØGNE FLÅ ØSTFOLD TRØNDELAG
MØRE SØRLANDET ØSTLANDET VESTLANDET TRØNDER BØ HÅ ÅL NÆRØY BJØRKELANGEN KONGSVINGER-ØST ØSTERDALEN
GUDBRANDSDALEN HALLINGDAL NUMEDAL VALDRES FJELLSKOG ÅSGÅRDSTRAND SANDSVÆR GRØNLAND BJØRNEBO
""".split())
NB_WORDS |= {w for w in COMPASS_WORDS if any(c in w for c in "ÆØÅ")}
# ASCII forms that are themselves common Norwegian (or English) words -> only fix with context.
PLAIN_WORDS = {"OST", "FOR", "VAR", "SA", "GA", "BLA", "SE", "NER", "HOY", "TAKE", "BAT", "ROD", "MATE",
               "LOS", "LOP", "AR", "HAND", "MANE", "SMA", "FA", "SO", "NO", "OY", "OYE", "DOR", "DOD",
               "VER", "HER", "LAS", "SAR", "SKAR", "HOST", "SOK", "MOTE", "GARD", "LOSE", "BAR"}
DIRECTION_CONTEXT = {"MOT", "RETNING", "FRA", "TIL", "KAMERA", "KAMERAET", "GRADER", "GRAD", "KM", "M", "METER",
                     "MIL", "SIDE", "SIDEN", "LANGT", "FOR", "AV", "°"}
_LOOKALIKE = {  # glyphs PP-OCR emits for letters it does not know; none occur in Norwegian text
    "Φ": "Ø", "φ": "ø", "∅": "Ø", "⊘": "Ø", "Ф": "Ø", "ф": "ø", "Ö": "Ø", "ö": "ø", "Ó": "Ø", "ó": "ø",
    "Ò": "Ø", "ò": "ø", "Ä": "Å", "ä": "å", "Á": "Å", "á": "å", "À": "Å", "à": "å", "Â": "Å", "â": "å",
    "Ã": "Å", "ã": "å", "ā": "å", "Œ": "Æ", "œ": "æ",
}
_FOLD_OPTIONS = {"Ø": ("O", "0"), "Å": ("A",), "Æ": ("AE", "E")}


def _folds(word: str):
    outs = [""]
    for ch in word:
        opts = _FOLD_OPTIONS.get(ch, (ch,))
        outs = [o + x for o in outs for x in opts]
    return outs


def _build_fold_map():
    m: dict[str, set] = {}
    for w in NB_WORDS:
        for f in _folds(w):
            if f != w:
                m.setdefault(f, set()).add(w)
    return m


_FOLD_MAP = _build_fold_map()


def _match_case(src: str, word: str) -> str:
    if src.isupper() or not any(c.isalpha() for c in src):
        return word.upper()
    if src.islower():
        return word.lower()
    if src[:1].isupper():
        return word[:1].upper() + word[1:].lower()
    return word


def _is_number(tok: str) -> bool:
    return bool(re.fullmatch(r"\d+([.,]\d+)?°?", tok))


def _fix_digits_in_token(tok: str) -> str:
    """Repair single digit/letter confusions: '0ST'->'OST', 'KAMERA4I'->kept, '4O'->'40'."""
    letters = sum(c.isalpha() for c in tok)
    digits = sum(c.isdigit() for c in tok)
    if letters >= 2 and 1 <= digits <= 1 and len(tok) >= 3:
        tr = {"0": "O", "1": "I", "5": "S", "8": "B"}
        if all((not c.isdigit()) or c in tr for c in tok):
            return "".join(tr.get(c, c) for c in tok)
    if digits >= 1 and letters == 1 and len(tok) >= 2:
        tr = {"O": "0", "o": "0", "I": "1", "l": "1", "|": "1"}
        if all(c.isdigit() or c in tr for c in tok):
            return "".join(tr.get(c, c) for c in tok)
    return tok


_WORD_RE = re.compile(r"^([^0-9A-Za-zÆØÅæøå]*)([0-9A-Za-zÆØÅæøå\-]+)([^0-9A-Za-zÆØÅæøå]*)$")


def _directional(context_upper: list) -> bool:
    for t in context_upper:
        t = t.strip(".,:;!?()")
        if (_is_number(t) or "°" in t or t in DIRECTION_CONTEXT or t in COMPASS_WORDS
                or any(t in COMPASS_WORDS for t in _FOLD_MAP.get(t, ()))):
            return True
    return False


def _restore_word(core: str, context_upper: list):
    """Return the corrected (upper-case) form of one OCR token, or None to keep it."""
    up = core.upper()
    if up in NB_WORDS:
        return None
    repaired = _fix_digits_in_token(core).upper()
    for form in dict.fromkeys((up, repaired)):
        if form in NB_WORDS:
            return form
        targets = _FOLD_MAP.get(form)
        if targets and len(targets) == 1:
            target = next(iter(targets))
            if form not in PLAIN_WORDS:
                return target
            if target in COMPASS_WORDS and _directional(context_upper):
                return target
            return form if form != up else None
    return repaired if repaired != up else None


_RUN_RE = re.compile(r"[A-Za-zÆØÅæøå]+|\d+")


def _split_glued(word: str) -> str:
    """Re-insert spaces OCR dropped between words and numbers on small boards.

    'KAMERA410ST' -> 'KAMERA 41 0ST' (a trailing 0 of a digit run is moved to the following
    letters when that makes a Norwegian word, e.g. 0ST -> ØST). Letter runs shorter than 3
    stay glued (E6, 4X4, KM2 are left alone).
    """
    if not re.fullmatch(r"[0-9A-Za-zÆØÅæøå]+", word or "") or len(word) < 5:
        return word
    runs = _RUN_RE.findall(word)
    if len(runs) < 2:
        return word
    for i in range(len(runs) - 1):
        a, b = runs[i], runs[i + 1]
        if a.isdigit() and len(a) >= 2 and a[-1] in "0" and not b.isdigit():
            joined = (a[-1] + b).upper()
            if joined in _FOLD_MAP or joined in NB_WORDS:
                runs[i], runs[i + 1] = a[:-1], a[-1] + b
    letter_len = [len(r) if not r.isdigit() else 0 for r in runs]
    if max(letter_len) < 3:
        return word
    out = runs[0]
    for prev, cur in zip(runs, runs[1:]):
        boundary = prev.isdigit() != cur.isdigit() or (cur[:1].isdigit() and not cur.isdigit())
        long_side = (not prev.isdigit() and len(prev) >= 3) or (not cur.isdigit() and len(cur) >= 3) or \
            cur.upper() in _FOLD_MAP
        out += (" " if boundary and long_side else "") + cur
    return out


def fix_norwegian(text: str) -> tuple[str, list]:
    """Restore Æ/Ø/Å and fix digit/letter confusions in one OCR line.

    Returns (fixed_text, changes) where changes is a list of (old, new) tokens.
    Conservative: ambiguous ASCII forms that are real words (OST, FOR, VAR ...) are
    only changed for compass words in a directional context (number, degree sign,
    another compass word or MOT/FRA/RETNING/KAMERA within two tokens).
    """
    if not text:
        return text, []
    text = "".join(_LOOKALIKE.get(c, c) for c in text)
    text = " ".join(_split_glued(w) for w in text.split(" "))
    pieces = re.split(r"(\s+)", text)
    word_idx = [i for i, p in enumerate(pieces) if p and not p.isspace()]
    uwords = [pieces[i].upper() for i in word_idx]
    changes = []
    for j, i in enumerate(word_idx):
        m = _WORD_RE.match(pieces[i])
        if not m:
            continue
        pre, core, post = m.groups()
        new = _restore_word(core, uwords[max(0, j - 2):j] + uwords[j + 1:j + 3])
        if new is not None and new != core.upper():
            cased = _match_case(core, new)
            changes.append((core, cased))
            pieces[i] = pre + cased + post
    return "".join(pieces), changes


# --------------------------------------------------------------------------------------------
# Text similarity helpers
# --------------------------------------------------------------------------------------------
_KEY_FOLD = str.maketrans({"Ø": "O", "0": "O", "Å": "A", "Æ": "E", "1": "I", "L": "I", "|": "I", "5": "S",
                           "8": "B", "Q": "O", "D": "O"})


def text_key(text: str) -> str:
    """Canonical key for comparing reads: upper-case, no whitespace/punctuation, OCR-confusable
    glyphs folded together (Ø/0/O, 1/I/L, 5/S ...)."""
    if not text:
        return ""
    t = unicodedata.normalize("NFC", text).upper()
    t = "".join(_LOOKALIKE.get(c, c) for c in t).upper()
    t = t.replace("AE", "E")
    t = re.sub(r"[^0-9A-ZÆØÅ]", "", t)
    return t.translate(_KEY_FOLD)


def board_similarity(a: str, b: str) -> float:
    """Similarity of two board texts in [0, 1]; robust to a read that missed a line."""
    ka, kb = text_key(a), text_key(b)
    if not ka or not kb:
        return 0.0
    if ka == kb:
        return 1.0
    sm = difflib.SequenceMatcher(None, ka, kb, autojunk=False)
    ratio = sm.ratio()
    short = min(len(ka), len(kb))
    if short >= 8:
        matched = sum(bl.size for bl in sm.get_matching_blocks())
        ratio = max(ratio, 0.95 * matched / short)
    return float(ratio)


# --------------------------------------------------------------------------------------------
# OCR engines
# --------------------------------------------------------------------------------------------
_RAPID = None
_RAPID_ERR = None
_RAPID_LOCK = threading.Lock()


def get_rapidocr(threads: int = 2):
    """Shared lazily-initialised RapidOCR engine (None if the package is missing)."""
    global _RAPID, _RAPID_ERR
    with _RAPID_LOCK:
        if _RAPID is None and _RAPID_ERR is None:
            try:
                from rapidocr_onnxruntime import RapidOCR
                _RAPID = RapidOCR(intra_op_num_threads=int(threads))
                logging.getLogger("RapidOCR").setLevel(logging.WARNING)
            except Exception as e:  # pragma: no cover - depends on install
                _RAPID_ERR = repr(e)
                log.warning("RapidOCR unavailable (%s); whiteboard OCR disabled (detection still works)", e)
        return _RAPID


_TESS = None  # (module, lang) or False


def get_tesseract():
    global _TESS
    if _TESS is None:
        _TESS = False
        if shutil.which("tesseract"):
            try:
                import pytesseract
                langs = set(pytesseract.get_languages(config=""))
                lang = "+".join(x for x in ("nor", "eng") if x in langs) or None
                if lang:
                    _TESS = (pytesseract, lang)
                    if "nor" not in langs:
                        log.info("tesseract has no 'nor' traineddata; using %s (install tesseract-ocr-nor)", lang)
            except Exception as e:  # pragma: no cover
                log.info("pytesseract unusable: %s", e)
    return _TESS or None


@dataclass
class OcrLine:
    text: str
    conf: float
    y: float                     # centre y relative to crop height (0 top .. 1 bottom)
    x: float = 0.0
    raw: str = ""


@dataclass
class BoardRead:
    lines: list
    conf: float
    engine: str
    variant: str
    ts: Optional[datetime] = None
    frame_id: Optional[int] = None

    @property
    def text(self) -> str:
        return "\n".join(l.text for l in self.lines)

    @property
    def raw_text(self) -> str:
        return "\n".join(l.raw or l.text for l in self.lines)

    @property
    def score(self) -> float:
        n = len(text_key(self.text))
        return self.conf * np.sqrt(max(n, 0))


def _group_lines(items, h):
    """items: list of (box 4x2, text, conf). Merge boxes on the same text line."""
    rows = []
    for box, txt, conf in items:
        b = np.asarray(box, float)
        cy, cx = b[:, 1].mean(), b[:, 0].mean()
        bh = max(1.0, b[:, 1].max() - b[:, 1].min())
        placed = False
        for r in rows:
            if abs(r["cy"] - cy) < 0.5 * min(r["h"], bh):
                r["parts"].append((cx, txt, conf, len(txt)))
                r["cy"] = (r["cy"] + cy) / 2
                placed = True
                break
        if not placed:
            rows.append({"cy": cy, "h": bh, "parts": [(cx, txt, conf, len(txt))]})
    rows.sort(key=lambda r: r["cy"])
    out = []
    for r in rows:
        parts = sorted(r["parts"])
        txt = " ".join(p[1].strip() for p in parts if p[1].strip())
        wsum = sum(max(p[3], 1) for p in parts)
        conf = sum(p[2] * max(p[3], 1) for p in parts) / wsum
        out.append((txt, float(conf), float(r["cy"] / max(h, 1)), float(parts[0][0])))
    return out


def ocr_rapid(img: np.ndarray, engine) -> list:
    """Run RapidOCR; returns [(text, conf, y_rel, x)] grouped into lines."""
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    res, _ = engine(img)
    if not res:
        return []
    items = [(r[0], str(r[1]), float(r[2])) for r in res if str(r[1]).strip()]
    return _group_lines(items, img.shape[0])


def ocr_tesseract(gray: np.ndarray, tess) -> list:
    mod, lang = tess
    d = mod.image_to_data(gray, lang=lang, config="--psm 6", output_type=mod.Output.DICT)
    lines = {}
    for i, word in enumerate(d["text"]):
        word = (word or "").strip()
        try:
            c = float(d["conf"][i])
        except (TypeError, ValueError):
            c = -1
        if not word or c < 0:
            continue
        key = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
        L = lines.setdefault(key, {"words": [], "confs": [], "ys": [], "x": d["left"][i]})
        L["words"].append(word)
        L["confs"].append(c / 100.0)
        L["ys"].append(d["top"][i] + d["height"][i] / 2)
    out = []
    for L in lines.values():
        out.append((" ".join(L["words"]), float(np.mean(L["confs"])), float(np.mean(L["ys"]) / gray.shape[0]),
                    float(L["x"])))
    out.sort(key=lambda t: t[2])
    return out


# --------------------------------------------------------------------------------------------
# Detection
# --------------------------------------------------------------------------------------------
@dataclass
class BoardCandidate:
    corners: np.ndarray          # 4x2 float, full-res, ordered tl,tr,br,bl
    bbox: tuple                  # x0,y0,x1,y1 full-res ints
    score: float
    area_frac: float
    aspect: float
    rectangularity: float
    contrast: float
    ink_frac: float
    angle_deg: float
    touches_border: bool
    ir_mode: bool
    features: dict = field(default_factory=dict)


def is_monochrome(rgb_small: np.ndarray, sat_thr: float = 12.0, chan_thr: float = 4.0) -> bool:
    """IR/night mode detector: IR-cut filter removed -> essentially grey image."""
    x = rgb_small.astype(np.int16)
    chan = (np.abs(x[..., 0] - x[..., 1]) + np.abs(x[..., 1] - x[..., 2])).mean() / 2.0
    hsv = cv2.cvtColor(rgb_small, cv2.COLOR_RGB2HSV)
    return bool(np.median(hsv[..., 1]) < sat_thr and chan < chan_thr)


def order_corners(pts: np.ndarray) -> np.ndarray:
    pts = np.asarray(pts, dtype=np.float32).reshape(-1, 2)
    c = pts.mean(axis=0)
    ang = np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0])
    pts = pts[np.argsort(ang)]            # clockwise in image coords (y down), starting near -pi (left)
    start = int(np.argmin(pts.sum(axis=1)))  # top-left has the smallest x+y
    return np.roll(pts, -start, axis=0)


def _fit_quad(cnt: np.ndarray):
    hull = cv2.convexHull(cnt)
    peri = cv2.arcLength(hull, True)
    for eps in (0.015, 0.025, 0.035, 0.05, 0.07):
        ap = cv2.approxPolyDP(hull, eps * peri, True)
        if len(ap) == 4 and cv2.isContourConvex(ap):
            return ap.reshape(4, 2).astype(np.float32)
    return cv2.boxPoints(cv2.minAreaRect(cnt)).astype(np.float32)


def detect_boards(rgb: np.ndarray, work_w: int = 640, min_area_frac: float = 0.003, max_area_frac: float = 0.45,
                  s_max: int = 75, min_score: float = 0.55, ir_mode: Optional[bool] = None) -> list:
    """Return whiteboard candidates sorted by score (best first)."""
    H, W = rgb.shape[:2]
    s = min(1.0, work_w / float(W))
    small = cv2.resize(rgb, (int(round(W * s)), int(round(H * s))), interpolation=cv2.INTER_AREA) if s < 1 else rgb
    h, w = small.shape[:2]
    hsv = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)
    S, V = hsv[..., 1], hsv[..., 2]
    if ir_mode is None:
        ir_mode = is_monochrome(small)
    Vb = cv2.GaussianBlur(V, (3, 3), 0)
    med = float(np.median(Vb))
    top = float(np.percentile(Vb, 99.5))
    if top - med < 25:
        return []
    min_area = min_area_frac * h * w
    max_area = max_area_frac * h * w
    k = max(3, int(round(w / 160.0)) | 1)
    close_k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    lowsat = np.ones_like(V, bool) if ir_mode else (S <= s_max)
    cands = []
    for frac in (0.35, 0.55, 0.75):
        thr = max(90.0, med + frac * (top - med))
        mask = ((Vb >= thr) & lowsat).astype(np.uint8) * 255
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, close_k)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in cnts:
            area = cv2.contourArea(cnt)
            if area < min_area or area > max_area:
                continue
            c = _score_candidate(cnt, area, small, V, S, ir_mode, h, w)
            if c is None or c["score"] < min_score:
                continue
            corners = c["quad"] / s
            xs, ys = corners[:, 0], corners[:, 1]
            bbox = (int(max(0, xs.min())), int(max(0, ys.min())), int(min(W - 1, xs.max())), int(min(H - 1, ys.max())))
            cands.append(BoardCandidate(corners=order_corners(corners), bbox=bbox, score=c["score"],
                                        area_frac=area / (h * w), aspect=c["aspect"],
                                        rectangularity=c["rect"], contrast=c["contrast"], ink_frac=c["ink"],
                                        angle_deg=c["angle"], touches_border=c["border"], ir_mode=ir_mode,
                                        features={"solidity": c["solidity"], "thr_frac": frac}))
    # non-maximum suppression across the threshold stack
    cands.sort(key=lambda c: -c.score)
    keep = []
    for c in cands:
        if all(bbox_iou(c.bbox, k.bbox) < 0.5 for k in keep):
            keep.append(c)
    return keep


def _score_candidate(cnt, area, small, V, S, ir_mode, h, w):
    rect = cv2.minAreaRect(cnt)
    (cx, cy), (rw, rh), ang = rect
    if min(rw, rh) < 10:
        return None
    rect_area = max(rw * rh, 1.0)
    rectangularity = area / rect_area
    hull_area = max(cv2.contourArea(cv2.convexHull(cnt)), 1.0)
    solidity = area / hull_area
    aspect = max(rw, rh) / max(min(rw, rh), 1.0)
    if rectangularity < 0.72 or solidity < 0.88 or aspect > 3.2:
        return None
    x, y, bw, bh = cv2.boundingRect(cnt)
    border = x <= 1 or y <= 1 or x + bw >= w - 2 or y + bh >= h - 2
    inner = np.zeros((h, w), np.uint8)
    cv2.drawContours(inner, [cnt], -1, 255, -1)
    ek = max(3, int(0.08 * min(rw, rh)) | 1)
    ring_k = cv2.getStructuringElement(cv2.MORPH_RECT, (max(5, int(0.25 * min(rw, rh)) | 1),) * 2)
    dil = cv2.dilate(inner, ring_k)
    ring = (dil > 0) & (inner == 0)
    ero = cv2.erode(inner, cv2.getStructuringElement(cv2.MORPH_RECT, (ek, ek))) > 0
    if ring.sum() < 10 or ero.sum() < 10:
        return None
    vin = V[ero]
    paper = float(np.percentile(vin, 75))
    contrast = paper - float(np.median(V[ring]))
    if contrast < 25:
        return None
    ink = float(np.mean(vin < paper - 55))
    # score components
    s_rect = np.clip((rectangularity - 0.72) / 0.2, 0, 1)
    s_contrast = np.clip((contrast - 25) / 55.0, 0, 1)
    s_aspect = 1.0 if 1.05 <= aspect <= 2.3 else 0.6
    s_ink = 1.0 if 0.004 <= ink <= 0.35 else (0.5 if ink < 0.004 else 0.2)
    s_sat = 1.0 if ir_mode else float(np.clip((80 - np.median(S[ero])) / 50.0, 0, 1))
    score = 0.32 * s_rect + 0.30 * s_contrast + 0.12 * s_aspect + 0.14 * s_ink + 0.12 * s_sat
    if border:
        score *= 0.75
        if y <= 1 and area > 0.05 * h * w:     # large bright thing touching the top: sky
            score *= 0.5
    quad = _fit_quad(cnt)
    return {"score": float(score), "rect": float(rectangularity), "solidity": float(solidity), "aspect": float(aspect),
            "contrast": contrast, "ink": ink, "angle": float(ang), "border": bool(border), "quad": quad}


def bbox_iou(a, b) -> float:
    ix0, iy0 = max(a[0], b[0]), max(a[1], b[1])
    ix1, iy1 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = max(0, ix1 - ix0), max(0, iy1 - iy0)
    inter = iw * ih
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def rectify(rgb: np.ndarray, corners: np.ndarray, target_long: int = 900, max_scale: float = 6.0,
            expand: float = 0.015) -> np.ndarray:
    """Perspective-rectify the board (corners tl,tr,br,bl in full-res pixels)."""
    c = np.asarray(corners, np.float32)
    ctr = c.mean(axis=0)
    c = ctr + (c - ctr) * (1.0 + expand)
    wtop, wbot = np.linalg.norm(c[1] - c[0]), np.linalg.norm(c[2] - c[3])
    hl, hr = np.linalg.norm(c[3] - c[0]), np.linalg.norm(c[2] - c[1])
    bw, bh = max(wtop, wbot), max(hl, hr)
    scale = float(np.clip(target_long / max(bw, bh, 1.0), 1.0, max_scale))
    ow, oh = int(round(bw * scale)), int(round(bh * scale))
    dst = np.array([[0, 0], [ow - 1, 0], [ow - 1, oh - 1], [0, oh - 1]], np.float32)
    M = cv2.getPerspectiveTransform(c, dst)
    return cv2.warpPerspective(rgb, M, (ow, oh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def enhance(crop_rgb: np.ndarray) -> dict:
    """Return OCR-ready variants: 'clahe' (flattened, contrast-enhanced ink map) and 'binary'."""
    ink = crop_rgb.min(axis=2).astype(np.float32)          # coloured markers are dark in >= 1 channel
    # paper level: grey-scale closing (max filter wider than a marker stroke) removes the ink,
    # a heavy blur then gives a smooth illumination field (shade, glare gradients)
    k = max(5, int(0.035 * max(ink.shape)) | 1)
    bg = cv2.dilate(ink, cv2.getStructuringElement(cv2.MORPH_RECT, (k, k)))
    bg = cv2.GaussianBlur(bg, (0, 0), max(4.0, 0.04 * max(ink.shape)))
    flat = np.clip(ink / np.maximum(bg, 1.0) * 215.0, 0, 255).astype(np.uint8)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(flat)
    block = max(15, int(0.05 * max(ink.shape)) | 1)
    binary = cv2.adaptiveThreshold(clahe, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block, 12)
    binary = cv2.medianBlur(binary, 3)
    return {"clahe": clahe, "binary": binary}


def read_board(crop_rgb: np.ndarray, rapid=None, tess=None, good_conf: float = 0.85) -> Optional[BoardRead]:
    """OCR a rectified board with the available engines; returns the best read (or None)."""
    variants = enhance(crop_rgb)
    reads = []

    def mk(lines, engine, variant):
        out = []
        for txt, conf, y, x in lines:
            fixed, _ = fix_norwegian(txt)
            out.append(OcrLine(text=fixed, conf=conf, y=y, x=x, raw=txt))
        if not out:
            return None
        n = [max(len(text_key(l.text)), 1) for l in out]
        conf = float(np.average([l.conf for l in out], weights=n))
        return BoardRead(lines=out, conf=conf, engine=engine, variant=variant)

    if rapid is not None:
        for name in ("clahe", "binary"):
            try:
                r = mk(ocr_rapid(variants[name], rapid), "rapidocr", name)
            except Exception as e:  # pragma: no cover
                log.warning("rapidocr failed: %s", e)
                r = None
            if r is not None:
                reads.append(r)
                if r.conf >= good_conf:
                    break
    if tess is not None:
        try:
            r = mk(ocr_tesseract(variants["binary"], tess), "tesseract", "binary")
            if r is not None:
                reads.append(r)
        except Exception as e:  # pragma: no cover
            log.warning("tesseract failed: %s", e)
    if not reads:
        return None
    return max(reads, key=lambda r: r.score)


def merge_reads(reads: list) -> dict:
    """Merge several reads of one board line-by-line (consensus + best confidence)."""
    reads = [r for r in reads if r is not None and r.lines]
    if not reads:
        return {"text": "", "lines": [], "conf": 0.0, "n_reads": 0, "support": 0}
    clusters = []
    for ri, r in enumerate(reads):
        for ln in r.lines:
            k = text_key(ln.text)
            if not k:
                continue
            best, bsim = None, 0.0
            for c in clusters:
                sim = max(board_similarity(ln.text, v.text) for v in c["variants"])
                dy = abs(float(np.mean(c["ys"])) - ln.y)
                if (sim >= 0.5 and dy < 0.18) or sim >= 0.8:
                    if sim > bsim:
                        best, bsim = c, sim
            if best is None:
                best = {"variants": [], "ys": [], "reads": set()}
                clusters.append(best)
            best["variants"].append(ln)
            best["ys"].append(ln.y)
            best["reads"].add(ri)
    n = len(reads)
    lines, confs, weights = [], [], []
    for c in clusters:
        vs = c["variants"]

        def vscore(v):
            agree = np.mean([board_similarity(v.text, o.text) for o in vs if o is not v]) if len(vs) > 1 else 0.0
            return v.conf * (1.0 + agree) * (1.0 + 0.02 * len(text_key(v.text)))
        best = max(vs, key=vscore)
        support = len(c["reads"])
        if support < min(2, n) and best.conf < 0.85:
            continue
        lines.append((float(np.mean(c["ys"])), best, support))
    lines.sort(key=lambda t: t[0])
    for _, v, sup in lines:
        confs.append(v.conf)
        weights.append(max(len(text_key(v.text)), 1))
    conf = float(np.average(confs, weights=weights)) if confs else 0.0
    support = int(min((s for _, _, s in lines), default=0))
    return {"text": "\n".join(v.text for _, v, _ in lines),
            "raw_text": "\n".join(v.raw for _, v, _ in lines),
            "lines": [v.text for _, v, _ in lines], "conf": conf, "n_reads": n, "support": support}


_CLOCK_RE = re.compile(r"(?:\bKL\.?\s*(\d{1,2})[:.](\d{2})\b)|(?:\b(\d{1,2}):(\d{2})\b)", re.I)


def find_clock(text: str):
    """Return 'HH:MM' strings written on the board (with KL prefix or a colon)."""
    out = []
    for m in _CLOCK_RE.finditer(text or ""):
        hh, mm = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        hh, mm = int(hh), int(mm)
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            out.append(f"{hh:02d}:{mm:02d}")
    return out


def _oslo_tz():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Europe/Oslo")
    except Exception:  # pragma: no cover
        return timezone(timedelta(hours=2))


# --------------------------------------------------------------------------------------------
# Analyzer
# --------------------------------------------------------------------------------------------
@dataclass
class _Instance:
    reads: list = field(default_factory=list)
    first_ts: Optional[datetime] = None
    first_capture: Optional[datetime] = None
    frame_id: Optional[int] = None
    emitted: Optional[Observation] = None
    emitted_text: str = ""
    emitted_conf: float = 0.0
    is_new: Optional[bool] = None
    n_empty: int = 0
    all_emitted: list = field(default_factory=list)


@dataclass
class _Track:
    id: int
    bbox: tuple
    corners: np.ndarray
    n: int = 1
    misses: int = 0
    confirmed: bool = False
    first_ts: Optional[datetime] = None
    last_ts: Optional[datetime] = None
    last_frame_id: Optional[int] = None
    thumb: Optional[np.ndarray] = None
    last_ocr_ts: Optional[datetime] = None
    archived: int = 0
    inst: _Instance = field(default_factory=_Instance)
    visible_obs: Optional[Observation] = None


class WhiteboardAnalyzer(Analyzer):
    """Detect a held-up whiteboard, OCR it, merge/de-duplicate reads, announce new text."""

    name = "whiteboard"
    wants_frames = True
    min_interval_s = 0.0

    DEFAULTS = {
        "work_w": 640, "min_area_frac": 0.003, "max_area_frac": 0.45, "s_max": 75, "min_score": 0.55,
        "persist_frames": 2, "max_gap_frames": 1, "emit_after_reads": 3, "agree_sim": 0.8,
        "dedup_sim": 0.8, "new_instance_sim": 0.45, "ocr": True, "ocr_threads": 2,
        "ocr_stable_every_s": 60.0, "thumb_change": 12.0, "rectify_long": 900, "archive_max_per_track": 12,
        "min_text_chars": 2,
    }

    def __init__(self, config=None):
        super().__init__(config)
        self.p = {**self.DEFAULTS, **{k: v for k, v in (config or {}).items() if k != "_global"}}
        self._track: Optional[_Track] = None
        self._next_id = 1
        self._known = None           # list of dicts {key, text, id}
        self._trigger_pending_since = None

    # ---------------------------------------------------------------- helpers
    def available(self) -> bool:
        if self.p.get("ocr", True) and get_rapidocr(self.p["ocr_threads"]) is None and get_tesseract() is None:
            log.warning("whiteboard: no OCR engine (rapidocr_onnxruntime / pytesseract) - detection only")
        return True

    def _load_known(self, ctx):
        """Earlier boards from the DB (so restarts do not re-announce old text)."""
        if self._known is not None:
            return
        self._known = []
        db = getattr(ctx, "db", None)
        if db is None:
            return
        try:
            for o in db.observations(kind="whiteboard_text"):
                v = o["value"] or {}
                if o.get("analyzer") == self.name and v.get("text"):
                    self._known.append({"text": v["text"], "id": o["id"], "obs": None})
        except Exception as e:  # pragma: no cover
            log.warning("whiteboard: could not load earlier boards: %s", e)

    @staticmethod
    def _kid(k):
        return k["id"] if k.get("id") is not None else (k["obs"].id if k.get("obs") is not None else None)

    def _match_known(self, text, exclude=()):
        best, bsim = None, 0.0
        for k in self._known or []:
            if k.get("obs") is not None and any(k["obs"] is e for e in exclude):
                continue
            sim = board_similarity(text, k["text"])
            if min(len(text_key(text)), len(text_key(k["text"]))) < 6 and text_key(text) != text_key(k["text"]):
                sim = min(sim, 0.5)   # short texts must match exactly
            if sim > bsim:
                best, bsim = k, sim
        return best, bsim

    def _expire_trigger(self, ctx, frame):
        # ctx.trigger is a pulse: if nobody consumed it (VLM not loaded) drop it after 2 frames,
        # otherwise the runner keeps force-calling every analyzer on every frame.
        if self._trigger_pending_since is not None:
            if "whiteboard" not in ctx.triggers:
                self._trigger_pending_since = None
            elif frame.index - self._trigger_pending_since >= 2:
                ctx.triggers.discard("whiteboard")
                self._trigger_pending_since = None

    def _fire_trigger(self, ctx, frame):
        ctx.trigger("whiteboard")
        self._trigger_pending_since = frame.index

    @staticmethod
    def _associate(tr: _Track, c: BoardCandidate) -> bool:
        if bbox_iou(tr.bbox, c.bbox) >= 0.2:
            return True
        a, b = tr.bbox, c.bbox
        ca = np.array([(a[0] + a[2]) / 2, (a[1] + a[3]) / 2])
        cb = np.array([(b[0] + b[2]) / 2, (b[1] + b[3]) / 2])
        diag = np.hypot(a[2] - a[0], a[3] - a[1])
        ar = ((b[2] - b[0]) * (b[3] - b[1])) / max((a[2] - a[0]) * (a[3] - a[1]), 1)
        return np.linalg.norm(ca - cb) < 0.6 * diag and 0.5 <= ar <= 2.0

    # ---------------------------------------------------------------- main
    def on_frame(self, frame, ctx: Context):
        self._expire_trigger(ctx, frame)
        self._load_known(ctx)
        out = []
        try:
            cands = detect_boards(frame.image, work_w=self.p["work_w"], min_area_frac=self.p["min_area_frac"],
                                  max_area_frac=self.p["max_area_frac"], s_max=self.p["s_max"],
                                  min_score=self.p["min_score"])
        except Exception as e:  # never kill the runner
            log.warning("whiteboard detection failed: %s", e)
            cands = []
        best = cands[0] if cands else None
        tr = self._track
        if best is not None and tr is not None and self._associate(tr, best):
            tr.n += 1
            tr.misses = 0
            tr.bbox, tr.corners = best.bbox, best.corners
            tr.last_ts, tr.last_frame_id = frame.real_ts, frame.id
        elif best is not None:
            if tr is not None:
                out += self._end_track(tr, ctx, frame)
            tr = self._track = _Track(id=self._next_id, bbox=best.bbox, corners=best.corners,
                                      first_ts=frame.real_ts, last_ts=frame.real_ts, last_frame_id=frame.id)
            self._next_id += 1
        else:
            if tr is not None:
                tr.misses += 1
                if tr.misses > self.p["max_gap_frames"]:
                    out += self._end_track(tr, ctx, frame)
                    self._track = None
            if self._track is None:
                ctx.state.pop("whiteboard", None)
            return out

        crop = rectify(frame.image, tr.corners, target_long=self.p["rectify_long"])
        if not tr.confirmed and tr.n >= self.p["persist_frames"]:
            tr.confirmed = True
            v = {"bbox": list(tr.bbox), "corners": np.round(tr.corners, 1).tolist(), "score": round(best.score, 3),
                 "track_id": tr.id, "area_frac": round(best.area_frac, 5), "aspect": round(best.aspect, 2),
                 "angle_deg": round(best.angle_deg, 1), "ir_mode": best.ir_mode,
                 "first_seen_ts": iso(tr.first_ts), "frame_w": frame.w, "frame_h": frame.h}
            tr.visible_obs = Observation(kind="whiteboard_visible", ts=frame.real_ts, value=v, analyzer=self.name,
                                         confidence=float(np.clip(best.score, 0.3, 0.9)), frame_id=frame.id,
                                         ts_capture=frame.capture_ts)
            out.append(tr.visible_obs)
            self._fire_trigger(ctx, frame)
            log.info("whiteboard visible (track %d) bbox=%s score=%.2f", tr.id, tr.bbox, best.score)
        ctx.state["whiteboard"] = {"bbox": list(tr.bbox), "corners": tr.corners.tolist(), "crop": crop,
                                   "track_id": tr.id, "frame_id": frame.id, "frame_index": frame.index,
                                   "ts": frame.real_ts, "confirmed": tr.confirmed}
        if tr.confirmed and tr.archived < self.p["archive_max_per_track"]:
            ctx.state["archive_next"] = True
            tr.archived += 1

        read = self._maybe_read(tr, crop, frame)
        if read is not None:
            if tr.inst.first_ts is None:
                tr.inst.first_ts, tr.inst.first_capture, tr.inst.frame_id = frame.real_ts, frame.capture_ts, frame.id
            cur = merge_reads(tr.inst.reads)["text"] if tr.inst.reads else ""
            if (cur and len(text_key(read.text)) >= 4 and len(text_key(cur)) >= 4
                    and board_similarity(read.text, cur) < self.p["new_instance_sim"] and tr.confirmed):
                # she flipped the board / wrote something new while holding it up
                out += self._finalize(tr, ctx, frame, final=True)
                tr.inst = _Instance(first_ts=frame.real_ts, first_capture=frame.capture_ts, frame_id=frame.id)
                self._fire_trigger(ctx, frame)
            tr.inst.reads.append(read)
        if tr.confirmed:
            out += self._finalize(tr, ctx, frame, final=False)
        return out

    def _maybe_read(self, tr: _Track, crop, frame) -> Optional[BoardRead]:
        if not self.p.get("ocr", True):
            return None
        thumb = cv2.resize(cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY), (48, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
        changed = tr.thumb is None or float(np.mean(np.abs(thumb - tr.thumb))) > self.p["thumb_change"]
        stale = tr.last_ocr_ts is None or (frame.real_ts - tr.last_ocr_ts).total_seconds() >= self.p["ocr_stable_every_s"]
        # read every frame until the instance is emitted; afterwards only when it looks different or is stale
        if tr.inst.emitted is not None and not changed and not stale:
            return None
        rapid = get_rapidocr(self.p["ocr_threads"])
        tess = get_tesseract()
        if rapid is None and tess is None:
            return None
        tr.thumb, tr.last_ocr_ts = thumb, frame.real_ts
        r = read_board(crop, rapid=rapid, tess=tess)
        if r is None or len(text_key(r.text)) < self.p["min_text_chars"]:
            tr.inst.n_empty += 1
            return None
        r.ts, r.frame_id = frame.real_ts, frame.id
        return r

    def _ready(self, inst: _Instance) -> bool:
        reads = inst.reads
        if len(reads) >= self.p["emit_after_reads"]:
            return True
        if len(reads) >= 2:
            a, b = sorted(reads, key=lambda r: -r.score)[:2]
            return board_similarity(a.text, b.text) >= self.p["agree_sim"]
        return False

    def _finalize(self, tr: _Track, ctx, frame, final: bool):
        inst = tr.inst
        if not inst.reads or not tr.confirmed:
            return []
        if inst.emitted is None and not (final or self._ready(inst)):
            return []
        m = merge_reads(inst.reads)
        text = m["text"]
        if len(text_key(text)) < self.p["min_text_chars"]:
            return []
        if inst.emitted is not None:
            # only revise if the text changed materially and is at least as confident
            if not final or board_similarity(text, inst.emitted_text) >= 0.92 or m["conf"] < inst.emitted_conf - 0.05:
                return []
        own = [r for r in inst.all_emitted]
        known, sim = self._match_known(text, exclude=own)
        is_new = known is None or sim < self.p["dedup_sim"]
        support_factor = 0.6 + 0.4 * min(1.0, (m["support"] - 1) / 2.0) if m["support"] else 0.6
        conf = float(np.clip(m["conf"] * support_factor, 0.05, 0.95))
        vis_id = tr.visible_obs.id if tr.visible_obs is not None else None
        vlm_text = None
        vw = ctx.state.get("vlm_whiteboard") if isinstance(ctx.state.get("vlm_whiteboard"), dict) else None
        if vw:
            vlm_text = (vw.get(tr.id) or {}).get("text")
        value = {"text": text, "raw_text": m.get("raw_text", ""), "lines": m["lines"], "lang": "nb",
                 "ocr_conf": round(m["conf"], 3), "vlm_text": vlm_text, "n_reads": m["n_reads"],
                 "support": m["support"], "engines": sorted({r.engine for r in inst.reads}),
                 "track_id": tr.id, "first_seen_ts": iso(inst.first_ts or tr.first_ts),
                 "last_seen_ts": iso(tr.last_ts), "bbox": list(tr.bbox), "is_new": bool(is_new),
                 "repeat_of": self._kid(known) if (known is not None and not is_new) else None,
                 "repeat_sim": round(sim, 3), "revision_of": inst.emitted.id if inst.emitted is not None else None,
                 "visible_obs_id": vis_id}
        ts = inst.first_ts or tr.first_ts
        obs = Observation(kind="whiteboard_text", ts=ts, value=value, analyzer=self.name, confidence=conf,
                          frame_id=inst.frame_id, ts_capture=inst.first_capture,
                          notes="revision" if inst.emitted is not None else "")
        out = [obs]
        first_emission = inst.emitted is None
        announce = is_new and (first_emission or board_similarity(text, inst.emitted_text) < self.p["dedup_sim"])
        if announce:
            self._announce(ctx, ts, text, value, conf)
        inst.emitted, inst.emitted_text, inst.emitted_conf, inst.is_new = obs, text, m["conf"], is_new
        inst.all_emitted.append(obs)
        self._known.append({"text": text, "id": None, "obs": obs})
        out += self._clock_obs(text, ts, inst.first_capture, inst.frame_id)
        log.info("whiteboard text (track %d, %s, conf %.2f): %r", tr.id, "NEW" if is_new else "repeat", conf, text)
        return out

    def _announce(self, ctx, ts, text, value, conf):
        db = getattr(ctx, "db", None)
        if db is None:
            return
        try:
            db.add_event(ts, "whiteboard_text", "New whiteboard text: " + text.replace("\n", " / "),
                         {"text": text, "lines": value["lines"], "conf": round(conf, 3), "track_id": value["track_id"],
                          "bbox": value["bbox"]})
        except Exception as e:  # pragma: no cover
            log.warning("whiteboard: add_event failed: %s", e)

    def _clock_obs(self, text, ts, capture, frame_id):
        out = []
        for hhmm in find_clock(text):
            hh, mm = map(int, hhmm.split(":"))
            tz = _oslo_tz()
            ref = (capture or ts).astimezone(tz)
            shown = ref.replace(hour=hh, minute=mm, second=0, microsecond=0)
            diff = (ref - shown).total_seconds()
            if diff > 43200:
                shown += timedelta(days=1)
            elif diff < -43200:
                shown -= timedelta(days=1)
            diff = ((capture or ts) - shown).total_seconds()
            if abs(diff) > 3 * 3600:
                continue
            out.append(Observation(kind="clock_seen", ts=ts, analyzer=self.name, confidence=0.4, frame_id=frame_id,
                                   ts_capture=capture,
                                   value={"shown_time": hhmm, "shown_utc": iso(shown), "real_ts": iso(ts),
                                          "capture_ts": iso(capture) if capture else None,
                                          "capture_minus_shown_s": round(diff, 1), "source": "whiteboard",
                                          "text": text}))
        return out

    def _end_track(self, tr: _Track, ctx, frame):
        out = self._finalize(tr, ctx, frame, final=True) if tr.confirmed else []
        if ctx.state.get("whiteboard", {}).get("track_id") == tr.id:
            ctx.state.pop("whiteboard", None)
        return out
