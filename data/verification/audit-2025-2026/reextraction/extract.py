"""Independent cut-off PDF extractor (PyMuPDF word boxes, overlap-based column assignment).
Run with: python -I extract.py [pdf...]  -> extracted/<pdf>.pkl, extract_log.json
"""
import fitz, re, sys, pickle, json, os
from decimal import Decimal

RAW = "/Users/vish/collegeFind/data/raw/"
OUT = "/Users/vish/collegeFind/data/verification/audit-2025-2026/reextraction/"
SECTIONS = [  # longest first
    ("Other Than Home University Seats Allotted to Other Than Home University Candidates", "OHU_TO_OHU"),
    ("Other Than Home University Seats Allotted to Home University Candidates", "OHU_TO_HU"),
    ("Home University Seats Allotted to Other Than Home University Candidates", "HU_TO_OHU"),
    ("Home University Seats Allotted to Home University Candidates", "HU_TO_HU"),
    ("Minority Seats Allotted to Maharashtra State Candidature Candidates", "MIN_TO_MH"),
    ("Maharashtra State Seats Allotted to All India Candidature Candidates", "MH_TO_AI"),
    ("State Level", "STATE_LEVEL"),
]
CODE = re.compile(r"^(\d{4,10})([A-Z]{0,3})$")
RANK = re.compile(r"^\d+$")
PCT = re.compile(r"^\((\d+(?:\.\d+)?)\)$")


def rows_of(words, tol=2.5):
    ws = sorted(words, key=lambda w: (w[1], w[0]))
    rows = []
    for w in ws:
        if rows and abs(w[1] - rows[-1][0]) <= tol:
            rows[-1][1].append(w)
        else:
            rows.append([w[1], [w]])
    return [sorted(r[1], key=lambda w: w[0]) for r in rows]


def overlap(a0, a1, b0, b1):
    return min(a1, b1) - max(a0, b0)


def assign(w, headers):
    """column by max horizontal overlap of bboxes; fallback nearest edge gap (counted)"""
    best, bo = None, 0
    for h in headers:
        o = overlap(w[0], w[2], h[0], h[2])
        if o > bo:
            best, bo = h, o
    if best:
        return best[4], False
    h = min(headers, key=lambda h: min(abs(w[0] - h[2]), abs(w[2] - h[0])))
    return h[4], True


def extract(pdf):
    doc = fitz.open(RAW + pdf)
    cells = {}  # key -> (rank, pct, page)
    dups, fallback, ov_rows, ov_cells, unpaired, orphan = [], 0, [], 0, [], []
    college = course = section = headers = None
    for pno, page in enumerate(doc, 1):
        H = page.rect.height
        rows = rows_of([w for w in page.get_text("words") if w[1] < H - 45])  # drop footer/legend/page no.
        seen_college = False
        i = 0
        while i < len(rows):
            r = rows[i]
            toks = [w[4] for w in r]
            text = " ".join(toks)
            m = CODE.match(toks[0]) if len(toks) > 1 and toks[1] == "-" and r[0][0] < 60 else None
            if m:
                if len(m.group(1)) <= 5 and not m.group(2):
                    c5 = m.group(1).zfill(5)
                    if c5 != college:
                        course = None
                    college = c5
                    seen_college = True
                else:
                    course = m.group(1).zfill(10) + m.group(2)
                    section = headers = None
                i += 1
                continue
            sec = next((s for t, s in SECTIONS if text.startswith(t)), None)
            if sec and r[0][0] < 60:
                section, headers = sec, None
                i += 1
                continue
            if toks[0] == "Stage":
                headers = [w for w in r if w[4] != "Stage"]
                i += 1
                continue
            nums = [w for w in r if RANK.match(w[4])]
            others = [w for w in r if not RANK.match(w[4])]
            if nums and len(nums) >= len(others):
                nxt = rows[i + 1] if i + 1 < len(rows) else []
                pcts = [w for w in nxt if PCT.match(w[4])]
                extra = [w for w in nxt if not PCT.match(w[4]) and w[0] < 70]
                if not seen_college and not others:
                    ov_rows.append((pno, len(nums)))
                    ov_cells += len(nums)
                    i += 2 if pcts else 1
                    continue
                if course is None or headers is None or section is None:
                    orphan.append((pno, text[:60]))
                    i += 1
                    continue
                label = " ".join([w[4] for w in others] + [w[4] for w in extra])
                for w in nums:
                    p = next((q for q in pcts if abs(q[0] - w[0]) < 6), None)
                    box = (min(w[0], p[0]) if p else w[0], 0, max(w[2], p[2]) if p else w[2])
                    cat, fb = assign(box, headers)
                    fallback += fb
                    if p is None:
                        unpaired.append((pno, course, section, label, cat, w[4]))
                        pct = None
                    else:
                        v = Decimal(PCT.match(p[4]).group(1))
                        pct = None if v == 0 else v
                    key = (course, section, label, cat)
                    if key in cells:
                        dups.append((pno, key))
                    cells[key] = (int(w[4]), pct, pno)
                i += 2 if (pcts or extra) else 1
                continue
            i += 1
    return cells, dict(pdf=pdf, pages=len(doc), cells=len(cells), dups=dups[:20], ndups=len(dups),
                       fallback_assign=fallback, overflow_rows=len(ov_rows), overflow_cells=ov_cells,
                       overflow_detail=ov_rows[:60], unpaired=len(unpaired), unpaired_ex=unpaired[:10],
                       orphans=len(orphan), orphan_ex=orphan[:10])


if __name__ == "__main__":
    os.makedirs(OUT + "extracted", exist_ok=True)
    files = sys.argv[1:] or [f"{y}ENGG_CAP{c}_CutOff.pdf" for y in (2022, 2023, 2024) for c in (1, 2, 3)]
    logs = []
    for f in files:
        cells, log = extract(f)
        pickle.dump(cells, open(OUT + f"extracted/{f}.pkl", "wb"))
        logs.append(log)
        print(f, log["cells"], "dups", log["ndups"], "ov", log["overflow_rows"], log["overflow_cells"],
              "fb", log["fallback_assign"], "unpaired", log["unpaired"], "orphans", log["orphans"], flush=True)
    json.dump(logs, open(OUT + "extract_log_" + files[0] + ".json", "w"), indent=1, default=str)
