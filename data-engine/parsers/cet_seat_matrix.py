"""Parser for CET Cell 'Provisional Seat Matrix for CAP Round I' PDFs (FE 2022-2024).

Only the per-course summary line is extracted:
    <choice code> <course name> SI  MS-seats  Minority-seats  All-India  Institute-seats  Orphan
The per-category seat tables are not parsed (not needed yet). A line that starts like a course row but does not
match is reported as an error, never skipped silently.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

PARSER_NAME, PARSER_VERSION = "cet_seat_matrix_text", "0.2.0"
RE_INST = re.compile(r"^(\d{4,5}) - (.+)$")
RE_COURSE = re.compile(r"^(\d{9,10})([A-Z]{0,3}) (.+?) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)$")
RE_CAPLINE = re.compile(r"^(.*?)\s*CAP Seats\s*:\s*(\d+)$")
RE_COURSE_START = re.compile(r"^\d{9,10}[A-Z]{0,3} ")
RE_PUB = re.compile(r"Published Date\s*:\s*(\d{1,2})/(\d{1,2})/(\d{4})")
RE_YEAR = re.compile(r"A\.Y\.\s*(\d{4}-\d{2})")
EXPECTED_COLUMNS = "SI MS Seats Minority Seats All India Institute"  # header start; wraps differ between years


@dataclass
class MatrixRow:
    institute_code: str
    institute_name: str
    status_raw: str
    choice_code: str
    course_name: str
    si: int
    ms_seats: int
    minority_seats: int
    all_india_seats: int
    institute_seats: int
    orphan_seats: int
    page: int


@dataclass
class MatrixResult:
    rows: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    year_label: Optional[str] = None
    published: Optional[date] = None


class _State:
    def __init__(self):
        self.inst = None
        self.status = ""
        self.header_ok = False


def consume_page(text: str, pno: int, res: MatrixResult, st: _State) -> None:
    """Parse one page of extracted text, appending rows/errors to res. Separate from PDF I/O so it can be tested."""
    for line in text.split("\n"):
        line = line.strip()
        m = RE_INST.match(line)
        if m:
            st.inst = (m.group(1).zfill(5), m.group(2).strip()); st.status = ""; continue
        m = RE_CAPLINE.match(line)
        if m and st.inst:
            st.status = m.group(1).strip(); continue
        if line.startswith("Choice Code Course Name"):
            st.header_ok = EXPECTED_COLUMNS in line
            if not st.header_ok:
                res.errors.append((pno, "Unexpected column header", line[:120]))
            continue
        if RE_COURSE_START.match(line) and "Choice Code" not in line and "TFWS" not in line:
            m = RE_COURSE.match(line)
            if not m or not st.inst or not st.header_ok:
                res.errors.append((pno, "Course row not parsed", line[:140])); continue
            code = m.group(1).zfill(10) + m.group(2)
            if code[:5] != st.inst[0]:
                res.errors.append((pno, "Choice code does not match institute", line[:140])); continue
            n = [int(x) for x in m.groups()[3:]]
            res.rows.append(MatrixRow(st.inst[0], st.inst[1], st.status, code, m.group(3).strip(), *n, pno))


def parse_matrix_pdf(path: str) -> MatrixResult:
    import pdfplumber
    res, st = MatrixResult(), _State()
    with pdfplumber.open(path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            if pno == 1:
                m = RE_PUB.search(text)
                if m:
                    res.published = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
                y = RE_YEAR.search(text.replace("\n", " "))
                res.year_label = y.group(1) if y else None
            consume_page(text, pno, res, st)
    return res
