"""Compare a fresh parse (data/parsed/*.pkl) with what is stored in the database, cell by cell. Expect 0 differences.
Usage: set -a; . .env.local; set +a; python data-engine/verify_regression.py"""
import collections, os, pickle, sys
from decimal import Decimal
sys.path.insert(0, os.path.dirname(__file__))
from sqlalchemy import create_engine, text

ROOT = os.path.join(os.path.dirname(__file__), "..")
e = create_engine(os.environ["DATABASE_URL_UNPOOLED"].replace("postgresql://", "postgresql+psycopg://", 1))
db = collections.defaultdict(dict)
with e.connect() as c:
    for fn, cc, st, lb, cat, rk, pc in c.execute(text(
            "select d.original_filename, cc.choice_code, s.code, cr.stage_label, cr.category_code_raw, cr.closing_rank, cr.closing_percentile "
            "from cutoff_records cr join uploaded_documents d on d.id=cr.source_document_id join college_courses cc on cc.id=cr.college_course_id "
            "join seat_types s on s.id=cr.seat_type_id")):
        db[fn][(cc, st, lb, cat)] = (rk, None if pc is None else Decimal(pc))
tot = bad = 0
for fn in sorted(db):
    _, res = pickle.load(open(os.path.join(ROOT, "data", "parsed", fn + ".pkl"), "rb"))
    new = {(c.choice_code, c.seat_type_code, c.stage_label, c.category_code): (c.closing_rank, c.closing_percentile) for c in res.cells}
    only_db = set(db[fn]) - set(new); only_new = set(new) - set(db[fn])
    diff = [k for k in set(new) & set(db[fn]) if new[k] != db[fn][k]]
    n = len(db[fn]); tot += n; bad += len(only_db) + len(only_new) + len(diff)
    print(f"{fn:28s} db {n:>7,}  parse {len(new):>7,}  only-in-db {len(only_db)}  only-in-parse {len(only_new)}  value-diff {len(diff)}")
print(f"TOTAL {tot:,} cells, {bad} differences")
