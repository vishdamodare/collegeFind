"""Independent check of rank<->percentile pairing for records already in the database.

Method deliberately different from the parser: PyMuPDF words, grouped into visual lines, and every rank is paired with
the percentile at the SAME POSITION in the line below it (order only, no x-coordinates, no column mapping).
A database record passes when its (rank, percentile) pair is printed together on its cited page.
Usage: DATABASE_URL_UNPOOLED=... python verify_pairing.py
"""
import collections, os, re, sys
from decimal import Decimal

import fitz
from sqlalchemy import create_engine, text

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
RE_PCT = re.compile(r"^\((\d{1,3}(?:\.\d+)?)\)$")


def page_pairs(page):
    """Set of (rank, Decimal pct) pairs printed together on a page, paired by order within the row."""
    words = sorted(page.get_text("words"), key=lambda w: (round(w[1]), w[0]))
    lines, cur, cy = [], [], None
    for w in words:
        if cy is None or abs(w[1] - cy) <= 2.5:
            cur.append(w); cy = w[1] if cy is None else cy
        else:
            lines.append(sorted(cur, key=lambda x: x[0])); cur, cy = [w], w[1]
    if cur: lines.append(sorted(cur, key=lambda x: x[0]))
    pairs, miscount = set(), 0
    for i, ln in enumerate(lines[:-1]):
        ranks = [w[4] for w in ln if w[4].isdigit() and len(w[4]) <= 7]
        if not ranks or any(RE_PCT.match(w[4]) for w in ln): continue
        # a rank row: all numeric tokens except an optional leading stage label / header words
        nxt = [w[4] for w in lines[i + 1] if RE_PCT.match(w[4])]
        if not nxt: continue
        if len(nxt) != len(ranks): miscount += 1; continue
        for r, p in zip(ranks, nxt): pairs.add((int(r), Decimal(RE_PCT.match(p).group(1))))
    return pairs, miscount


def main():
    e = create_engine(os.environ["DATABASE_URL_UNPOOLED"].replace("postgresql://", "postgresql+psycopg://", 1))
    with e.connect() as c:
        rows = c.execute(text("select d.original_filename, cr.source_page, cr.closing_rank, cr.closing_percentile from cutoff_records cr "
                              "join uploaded_documents d on d.id=cr.source_document_id order by 1,2")).all()
    by_doc = collections.defaultdict(lambda: collections.defaultdict(list))
    for fn, pg, rk, pc in rows: by_doc[fn][pg].append((rk, pc))
    grand_ok = grand_n = 0
    for fn in sorted(by_doc):
        doc = fitz.open(os.path.join(RAW, fn)); ok = bad = 0; examples = []
        for pg, recs in by_doc[fn].items():
            pairs, _ = page_pairs(doc[pg - 1])
            prev = page_pairs(doc[pg - 2])[0] if pg > 1 else set()
            for rk, pc in recs:
                if (rk, Decimal(pc)) in pairs or (rk, Decimal(pc)) in prev: ok += 1
                else:
                    bad += 1
                    if len(examples) < 3: examples.append((pg, rk, str(pc)))
        grand_ok += ok; grand_n += ok + bad
        print(f"{fn:28s} {ok+bad:>7,} records  pair printed together: {ok:>7,} ({100*ok/(ok+bad):.3f}%)  not found: {bad}  {examples}")
    print(f"TOTAL {grand_n:,} records, {grand_ok:,} verified ({100*grand_ok/grand_n:.3f}%)")


if __name__ == "__main__":
    main()
