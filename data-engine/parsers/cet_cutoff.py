"""Parser for Maharashtra CET Cell CAP 'Cut Off List' PDFs (format observed in FE 2022-2024 State/Minority lists).

Layout: per college -> per course -> seat-level section -> 'Stage' header row of category codes, then for each
stage a rank row and a percentile row in brackets. Empty cells are omitted from the text layer, so values are
mapped to header columns by x-position, never by order. Anything that cannot be mapped confidently is reported
as an error instead of guessed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Optional

PARSER_NAME, PARSER_VERSION = "cet_cutoff_text_grid", "0.8.0"

# Section headings exactly as printed -> seat_types.code
SECTIONS = {
    "State Level": "STATE_LEVEL",
    "Home University Seats Allotted to Home University Candidates": "HU_TO_HU",
    "Home University Seats Allotted to Other Than Home University Candidates": "HU_TO_OHU",
    "Other Than Home University Seats Allotted to Other Than Home University Candidates": "OHU_TO_OHU",
    "Other Than Home University Seats Allotted to Home University Candidates": "OHU_TO_HU",
    # seen in the 2022 Round III list; rows are labelled 'MH' instead of a roman-numeral stage
    "Minority Seats Allotted to Maharashtra State Candidature Candidates": "MIN_TO_MH",
    # seen in the 2023 and 2024 Round III lists. Kept as its own seat type: it must never merge into State Level.
    "Maharashtra State Seats Allotted to All India Candidature Candidates": "MH_TO_AI",
}
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}
# 2023 lists drop leading zeros (1002 / 100219110); 2024 keeps them (01002 / 0100219110). Normalised below.
RE_COLLEGE = re.compile(r"^(\d{4,5}) - (.+)$")
RE_COURSE = re.compile(r"^(\d{9,10})([A-Z]{0,3}) - (.+)$")  # some codes carry a trailing letter, e.g. 0302524570U
RE_ANY_CODE = re.compile(r"^\d{5,}\S* - ")
RE_STATUS = re.compile(r"^Status:\s*(.*?)(?:\s+Home University\s*:\s*(.*))?$")  # university part absent in 2023
RE_PCT = re.compile(r"^\((\d{1,3}(?:\.\d+)?)\)$")
# Stage row label: 'I', 'II', ... 'VII', or 'I-Non' whose label continues on the next line ('I-Non' + 'PWD' / 'Defence').
RE_STAGE = re.compile(r"^(I|II|III|IV|V|VI|VII|VIII|IX|X|MH)(-Non)?$")
# Printed footer lines that legitimately follow the tables.
FOOTER_PREFIXES = ("Legends", "PWDR", "*", "Maharashtra State Seats - Cut Off", "Stage", "D ", "i ", "r ", "Degree", "Cut Off", "Master", "S S")
# Page-width overflow: very wide tables print their last few columns on the NEXT page, with no course name or stage
# label. That page is the right-hand strip of the wide page: the band's header and value rows sit at exactly the same
# y-positions as the table's header and stage rows on the previous page. A band is attributed only when its header
# matches exactly ONE table header there and each value row matches exactly ONE stage row; otherwise it stays a
# reported data gap (never guessed).
RE_CATCODE = re.compile(r"^[A-Z][A-Z0-9]{1,11}$")
ARTIFACT_LINES = {"S"}
Y_TOL = 2.5  # pt; same-y matching across the page split (observed offsets <= 0.5)  # stray vertical-text letters from the rotated word "Stage"


@dataclass
class Cell:
    institute_code: str
    institute_name: str
    choice_code: str
    course_name: str
    status_raw: str
    university_raw: str
    seat_type_code: str
    stage: int  # leading roman numeral value; NOT unique (see stage_label)
    stage_label: str  # exactly as printed, e.g. "I", "II", "I-Non PWD", "VII"
    category_code: str
    closing_rank: Optional[int]
    closing_percentile: Optional[Decimal]
    original_text: str
    page: int


@dataclass
class ParseResult:
    cells: list = field(default_factory=list)
    errors: list = field(default_factory=list)  # (page, message, raw)


def _lines(words, tol=2.0):
    out = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if out and abs(out[-1][0] - w["top"]) <= tol:
            out[-1][1].append(w)
        else:
            out.append([w["top"], [w]])
    return [sorted(ws, key=lambda w: w["x0"]) for _, ws in out]


def _xc(w):
    return (w["x0"] + w["x1"]) / 2


class CetCutoffParser:
    def __init__(self):
        self.res = ParseResult()
        self.inst = self.course = self.status = self.univ = None
        self.section = None
        self.header = []  # [(x_center, category_code)]
        self.pending = None  # (stage, [(x, rank_text)])
        self.gap = None  # active overflow band (see RE_CATCODE)
        self.page_tables = []  # tables on the current page: {"y", "ctx", "rows": [[rank_y, label]]}
        self.prev_tables = []  # same, for the previous page (overflow bands are attributed to these)
        self.page_no = None

    def _err(self, page, msg, raw=""):
        self.res.errors.append((page, msg, raw))

    def _col(self, x):
        """Nearest header column; ambiguous if farther than half the column pitch."""
        if not self.header:
            return None
        xs = [h[0] for h in self.header]
        pitch = min((b - a for a, b in zip(xs, xs[1:])), default=50.0)
        i = min(range(len(xs)), key=lambda k: abs(xs[k] - x))
        return i if abs(xs[i] - x) <= pitch * 0.6 else None

    def _flush_orphan(self, page_no, why):
        if self.pending:
            self._err(page_no, f"Rank row {self.pending[0]!r} {why}", str(self.pending[1])[:120])
            self.pending = None

    def feed_page(self, page_no: int, words: list) -> None:
        if page_no != self.page_no:
            self.prev_tables = self.page_tables if self.page_no == page_no - 1 else []
            self.page_tables, self.page_no = [], page_no
        for ws in _lines(words):
            text = " ".join(w["text"] for w in ws)
            first = ws[0]["text"]
            at_margin = ws[0]["x0"] < 75

            # Continuation of a two-line stage label: 'PWD (39.43..)' / 'Defence (48.06..)'
            if self.pending and self.pending[2] and at_margin and not first.startswith("("):
                i = 0
                label = self.pending[0]
                while i < len(ws) and not ws[i]["text"].startswith("("):
                    label += " " + ws[i]["text"]; i += 1
                self.pending = (label, self.pending[1], False)
                if self.page_tables and self.page_tables[-1]["rows"]:
                    self.page_tables[-1]["rows"][-1][1] = label
                self._emit(page_no, ws[i:]); self.pending = None
                continue
            if self.pending and not first.startswith("("):
                self._flush_orphan(page_no, "has no percentile row")
            if self.gap and self.gap[2] and self.gap[2]["rank"] and not first.startswith("("):
                self._err(page_no, "Overflow band rank row has no percentile row (data gap)", str(self.gap[2]["rank"])[:120])
                self.gap[2]["rank"] = None

            if self.gap and (RE_COLLEGE.match(text) or RE_COURSE.match(text) or text in SECTIONS or first == "Stage"):
                self.gap = None
            m = RE_COLLEGE.match(text)
            if m:
                code = m.group(1).zfill(5)
                if not (self.inst and self.inst[0] == code):  # same college again = page continuation: keep the course
                    self.course = None
                self.inst = (code, m.group(2).strip()); self.section = None; self.header = []; continue
            m = RE_COURSE.match(text)
            if m:
                code = m.group(1).zfill(10) + m.group(2)
                self.section = None; self.header = []
                if not self.inst or code[:5] != self.inst[0]:  # course code must start with its institute code
                    self.course = None
                    self._err(page_no, "Course code does not match current institute", f"{text} / inst={self.inst and self.inst[0]}")
                else:
                    self.course = (code, m.group(3).strip())
                continue
            if RE_ANY_CODE.match(text):  # looks like a code line we cannot parse: never reuse stale context
                self.course = None; self.section = None; self.header = []
                self._err(page_no, "Unrecognised college/course line", text); continue
            m = RE_STATUS.match(text)
            if m:
                self.status, self.univ = m.group(1), m.group(2) or ""; continue
            if text in SECTIONS:
                self.section = SECTIONS[text]; self.header = []; continue
            if first == "Stage":
                self.header = [(_xc(w), w["text"]) for w in ws[1:]]
                self.page_tables.append({"y": ws[0]["top"], "ctx": (self.inst, self.course, self.section, self.status, self.univ), "rows": []})
                if not self.header:
                    self._err(page_no, "Stage header with no categories", text)
                continue
            m = RE_STAGE.match(first)
            if m and at_margin and self.header:
                self.pending = (first, [(_xc(w), w["text"]) for w in ws[1:]], bool(m.group(2)))
                if self.page_tables:
                    self.page_tables[-1]["rows"].append([ws[0]["top"], first])
                continue
            if first.startswith("(") and self.pending:
                self._emit(page_no, ws); self.pending = None
                continue
            if self.gap and self.gap[2] and all(w["text"] in ("S", "H", "O") for w in ws):
                hdr = self.gap[2]["header"]  # wrapped suffix letter under an overflow-band header word
                for w in ws:
                    j = min(range(len(hdr)), key=lambda k: abs(hdr[k][0] - _xc(w)))
                    if abs(hdr[j][0] - _xc(w)) <= 10 and hdr[j][1][-1] not in "SHO":
                        hdr[j] = (hdr[j][0], hdr[j][1] + w["text"])
                continue
            if self.header and all(w["text"] in ("S", "H", "O") for w in ws):
                # A category code too long for its column wraps its LAST LETTER onto the next line (PWDROBC / S).
                # That letter is the seat-level suffix: S = State Level, H = Home University, O = Other than Home.
                # The lone letter sits directly under its header word: put it back. One under no header word is ignored.
                for w in ws:
                    j = min(range(len(self.header)), key=lambda k: abs(self.header[k][0] - _xc(w)))
                    if abs(self.header[j][0] - _xc(w)) <= 10 and self.header[j][1][-1] not in "SHO":
                        self.header[j] = (self.header[j][0], self.header[j][1] + w["text"])
                continue
            if text in ARTIFACT_LINES:
                continue
            if self.header and all(RE_CATCODE.match(w["text"]) for w in ws) and not self.pending:
                y = ws[0]["top"]
                hits = [t for t in self.prev_tables if abs(t["y"] - y) <= Y_TOL]
                band = None
                if len(hits) == 1 and all(hits[0]["ctx"][:3]):
                    band = {"table": hits[0], "header": [(_xc(w), w["text"]) for w in ws], "rank": None}
                self.gap = [text, 0, band]  # overflow header: its rank/percentile rows below are attributed or reported
                if not band:
                    self._err(page_no, "Overflow band from a table wider than the page: columns not attributed (data gap)", text)
                continue
            if self.gap and all(re.match(r"^(\d+|\(\d{1,3}(\.\d+)?\))$", w["text"]) for w in ws):
                self.gap[1] += 1
                if not (self.gap[2] and self._band_row(page_no, ws)):
                    self._err(page_no, "Overflow band values (data gap)", text[:120])
                continue
            # Anything else inside a table region that we do not recognise must be loud, not skipped.
            if self.header and at_margin and not text.startswith(FOOTER_PREFIXES):
                self._err(page_no, "Unrecognised row inside table", text[:120])

    def _band_row(self, page, ws):
        """One rank or percentile row of an attributed overflow band. False = cannot attribute (caller reports it)."""
        band = self.gap[2]
        if ws[0]["text"].startswith("("):
            if not band["rank"]:
                return False
            label, ranks = band["rank"]; band["rank"] = None
            saved = (self.header, self.inst, self.course, self.section, self.status, self.univ, self.pending)
            inst, course, section, status, univ = band["table"]["ctx"]
            self.header, self.inst, self.course, self.section, self.status, self.univ = band["header"], inst, course, section, status, univ
            self.pending = (label, ranks, False)
            n = len(self.res.cells)
            try:
                self._emit(page, ws)
            finally:
                self.header, self.inst, self.course, self.section, self.status, self.univ, self.pending = saved
            return len(self.res.cells) > n
        rows = [r for r in band["table"]["rows"] if abs(r[0] - ws[0]["top"]) <= Y_TOL]
        if len(rows) != 1 or band["rank"]:
            return False
        band["rank"] = (rows[0][1], [(_xc(w), w["text"]) for w in ws])
        return True

    def _emit(self, page, pct_words):
        label, ranks, _ = self.pending
        stage = ROMAN.get(RE_STAGE.match(label.split(' ')[0]).group(1), 0)  # 0 = non-roman label such as 'MH'
        ctx = (self.inst, self.course, self.section)
        if not all(ctx):
            return self._err(page, "Data row outside college/course/section context", str(ranks))
        by_col = {}
        for x, t in ranks:
            c = self._col(x)
            if c is None:
                self._err(page, "Rank value not alignable to a header column", t); continue
            by_col[c] = [t, None]
        for w in pct_words:
            c = self._col(_xc(w) - 7)  # percentile text is centred ~7pt right of the rank text
            if c is None or c not in by_col:
                self._err(page, "Percentile has no matching rank column", w["text"]); continue
            by_col[c][1] = w["text"]
        if len(pct_words) != len(ranks):
            self._err(page, f"{len(ranks)} ranks vs {len(pct_words)} percentiles", self.course[0])
        for c, (rt, pt) in sorted(by_col.items()):
            try:
                rank = int(rt)
                pct = Decimal(RE_PCT.match(pt).group(1)) if pt else None
            except (ValueError, AttributeError, InvalidOperation):
                self._err(page, "Unparsable rank/percentile cell", f"{rt} {pt}"); continue
            if rank <= 0 or (pct is not None and not Decimal(0) <= pct <= 100):
                self._err(page, "Out-of-range value", f"{rt} {pt}"); continue
            if pct == 0:
                # The CET Cell prints '(0.0000000)' for TFWS (Tuition Fee Waiver) seats, which are ranked on their own
                # list and have no percentile. A closing percentile of exactly 0 is never a real cutoff: store it as
                # missing (NULL) so it can never be compared against, and keep the printed text in original_text.
                pct = None
            self.res.cells.append(Cell(self.inst[0], self.inst[1], self.course[0], self.course[1], self.status or "",
                                       self.univ or "", self.section, stage, label, self.header[c][1], rank, pct,
                                       f"{rt} {pt or ''}".strip(), page))


def parse_pdf(path: str, first: int = 1, last: Optional[int] = None) -> ParseResult:
    import pdfplumber
    p = CetCutoffParser()
    with pdfplumber.open(path) as pdf:
        for i in range(first - 1, last or len(pdf.pages)):
            p.feed_page(i + 1, pdf.pages[i].extract_words())
    return p.res
