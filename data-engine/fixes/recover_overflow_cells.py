"""Insert the overflow-band cells recovered by parser 0.8.0 (see KNOWN_LIMITATIONS / docs/verification.md).

Gates (all must hold, or nothing is written):
* For every imported cut-off PDF, a fresh parse (data/parsed/*.pkl, parser 0.8.0) equals the database exactly,
  EXCEPT for cells that are only in the parse.
* Those parse-only cells are, as a multiset of (file, page, rank, percentile), exactly the completeness audit's list
  data/verification/completeness-audit/missing_cells.csv (266 cells), and each one is an overflow cell: printed on a
  different page from the stored cells of its row.
* Every category code's seat-level suffix agrees with its section (S = State Level, H = Home University, O = Other).
Rows go in as 'pending' under a new import_job per document (parser 0.8.0); mark them verified separately.
Dry-run by default.  Usage: set -a; . .env.local; set +a; python data-engine/fixes/recover_overflow_cells.py [--apply]
"""
import collections, csv, json, os, pickle, sys
from datetime import datetime, timezone
from decimal import Decimal
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from sqlalchemy import create_engine, text
from parsers.cet_cutoff import PARSER_NAME, PARSER_VERSION

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
APPLY = "--apply" in sys.argv
e = create_engine(os.environ["DATABASE_URL_UNPOOLED"].replace("postgresql://", "postgresql+psycopg://", 1))
# Suffix = whose seat it is, as printed (HU seats -> H, OHU seats -> O). Was swapped for HU_TO_OHU / OHU_TO_HU until the
# 24 Nov 2026 audit; harmless then because none of the 266 recovered cells were in those two sections.
SUFFIX = {"STATE_LEVEL": "S", "HU_TO_HU": "H", "HU_TO_OHU": "H", "OHU_TO_HU": "O", "OHU_TO_OHU": "O"}
NO_SUFFIX = {"TFWS", "EWS", "ORPHAN", "MI"}

expected = collections.Counter(
    (r["file"], int(r["page"]), int(r["rank"]), Decimal(r["percentile"]))
    for r in csv.DictReader(open(os.path.join(ROOT, "data/verification/completeness-audit/missing_cells.csv"))))

with e.connect() as c:
    tx = c.begin()
    db = collections.defaultdict(dict)
    for fn, cc, st, lb, cat, rk, pc in c.execute(text(
            "select d.original_filename, cc.choice_code, s.code, cr.stage_label, cr.category_code_raw, cr.closing_rank, cr.closing_percentile "
            "from cutoff_records cr join uploaded_documents d on d.id=cr.source_document_id join college_courses cc on cc.id=cr.college_course_id "
            "join seat_types s on s.id=cr.seat_type_id")):
        db[fn][(cc, st, lb, cat)] = (rk, None if pc is None else Decimal(pc))

    new_cells, problems = [], []
    for fn in sorted(db):
        ver, res = pickle.load(open(os.path.join(ROOT, "data", "parsed", fn + ".pkl"), "rb"))
        if ver != PARSER_VERSION:
            problems.append(f"{fn}: parsed with {ver}, need {PARSER_VERSION}")
        new = {(x.choice_code, x.seat_type_code, x.stage_label, x.category_code): x for x in res.cells}
        only_db = set(db[fn]) - set(new)
        diff = [k for k in set(new) & set(db[fn]) if (new[k].closing_rank, new[k].closing_percentile) != db[fn][k]]
        if only_db or diff:
            problems.append(f"{fn}: only-in-db {len(only_db)}, value-diff {len(diff)}")
        stored_pages = collections.defaultdict(set)  # (choice, seat, stage) -> pages its stored cells were printed on
        for k, x in new.items():
            if k in db[fn]:
                stored_pages[k[:3]].add(x.page)
        before = len(new_cells)
        for k in set(new) - set(db[fn]):
            x = new[k]
            if x.page in stored_pages[k[:3]]:
                problems.append(f"{fn}: {k} is on the same page as the rest of its row (not an overflow cell)")
            want = SUFFIX.get(x.seat_type_code)
            if want and x.category_code not in NO_SUFFIX and not x.category_code.endswith(want):
                problems.append(f"{fn}: {k} suffix does not match section {x.seat_type_code}")
            new_cells.append((fn, x))
        print(f"{fn:28s} db {len(db[fn]):>7,}  parse {len(new):>7,}  recovered {len(new_cells) - before}")

    got = collections.Counter((fn, x.page, x.closing_rank, x.closing_percentile) for fn, x in new_cells)
    if got != expected:
        problems.append(f"recovered != audit list: extra {sum((got - expected).values())}, still missing {sum((expected - got).values())}")
    if problems:
        tx.rollback(); sys.exit("ABORT, nothing written:\n  " + "\n  ".join(problems))

    now = datetime.now(timezone.utc)
    inserted = collections.Counter()
    for fn in sorted({fn for fn, _ in new_cells}):
        doc_id = c.execute(text("select id from uploaded_documents where original_filename=:f"), {"f": fn}).scalar_one()
        ref = c.execute(text("select exam_id, academic_year_id, authority_id, round_id, course_id from cutoff_records "
                             "where source_document_id=:d limit 1"), {"d": doc_id}).one()
        cells = [x for f, x in new_cells if f == fn]
        job_id = c.execute(text(
            "insert into import_jobs (document_id, parser_name, parser_version, status, stats, started_at, finished_at) "
            "values (:d, :n, :v, 'needs_review', cast(:s as jsonb), :t, :t) returning id"),
            {"d": doc_id, "n": PARSER_NAME, "v": PARSER_VERSION, "t": now,
             "s": json.dumps({"cells": len(cells), "kind": "overflow-band recovery",
                              "audit_list": "data/verification/completeness-audit/missing_cells.csv"})}).scalar()
        for x in cells:
            cc = c.execute(text("select id, college_id, branch_id from college_courses where choice_code=:c"), {"c": x.choice_code}).one()
            st = c.execute(text("select id, quota, home_university_class from seat_types where code=:c"), {"c": x.seat_type_code}).one()
            cat = c.execute(text("select id from categories where exam_id=:e and academic_year_id=:y and code=:c"),
                            {"e": ref.exam_id, "y": ref.academic_year_id, "c": x.category_code}).scalar()
            if cat is None:
                cat = c.execute(text("insert into categories (exam_id, academic_year_id, code, is_verified) values (:e, :y, :c, false) returning id"),
                                {"e": ref.exam_id, "y": ref.academic_year_id, "c": x.category_code}).scalar()
                print(f"  new category {x.category_code} for {fn}")
            c.execute(text(
                "insert into cutoff_records (college_id, college_course_id, course_id, branch_id, exam_id, academic_year_id, authority_id, round_id, "
                "stage, stage_label, category_id, category_code_raw, seat_type_id, quota, home_university_class, closing_percentile, closing_rank, "
                "original_metric_text, source_document_id, source_page, import_job_id, verification_status) values "
                "(:college, :cc, :course, :branch, :exam, :year, :auth, :rnd, :stage, :label, :cat, :catraw, :st, :quota, :huc, :pct, :rank, "
                ":orig, :doc, :page, :job, 'pending')"),
                {"college": cc.college_id, "cc": cc.id, "course": ref.course_id, "branch": cc.branch_id, "exam": ref.exam_id,
                 "year": ref.academic_year_id, "auth": ref.authority_id, "rnd": ref.round_id, "stage": x.stage, "label": x.stage_label,
                 "cat": cat, "catraw": x.category_code, "st": st.id, "quota": st.quota, "huc": st.home_university_class,
                 "pct": x.closing_percentile, "rank": x.closing_rank, "orig": x.original_text, "doc": doc_id, "page": x.page, "job": job_id})
            inserted[fn] += 1
        print(f"  {fn}: import_job {job_id}, {inserted[fn]} rows (pending)")
    assert sum(inserted.values()) == sum(expected.values()), inserted
    if APPLY:
        tx.commit(); print(f"APPLIED: {sum(inserted.values())} cells inserted as pending")
    else:
        tx.rollback(); print(f"DRY-RUN: {sum(inserted.values())} cells would be inserted (rolled back; re-run with --apply)")
