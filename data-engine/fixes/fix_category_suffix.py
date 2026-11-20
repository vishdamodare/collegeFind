"""Restore the last letter of category codes whose header cell wrapped (PWDROBC / <letter> on the next line).

The wrapped letter is the SEAT-LEVEL suffix, so it depends on the section: State Level -> S, Home University seats -> H,
Other-than-Home-University seats -> O. Idempotent: accepts rows currently stored with no suffix OR a wrong suffix.
Dry-run unless --apply. Usage: set -a; . .env.local; set +a; python data-engine/fixes/fix_category_suffix.py [--apply]
"""
import os, sys, time
from sqlalchemy import create_engine, text

APPLY = "--apply" in sys.argv
BASES = ["PWDROBC", "DEFRSEBC", "PWDRSEBC"]
SUFFIX = {"STATE_LEVEL": "S", "HU_TO_HU": "H", "HU_TO_OHU": "H", "OHU_TO_OHU": "O", "OHU_TO_HU": "O"}
e = create_engine(os.environ["DATABASE_URL_UNPOOLED"].replace("postgresql://", "postgresql+psycopg://", 1))
for attempt in range(8):                                   # DNS on this machine fails intermittently
    try: c = e.connect(); break
    except Exception: time.sleep(6)
else: sys.exit("could not connect")
tx = c.begin()
try:
    rows = c.execute(text(
        "select cr.id, cr.category_code_raw, s.code, cr.academic_year_id, cr.category_id, cat.exam_id "
        "from cutoff_records cr join seat_types s on s.id=cr.seat_type_id join categories cat on cat.id=cr.category_id "
        "where cr.category_code_raw = any(:v)"), {"v": BASES + [b + x for b in BASES for x in "SHO"]}).all()
    todo = []
    for rid, code, st, yr, cat_id, exam in rows:
        base = next(b for b in BASES if code.startswith(b))
        assert st in SUFFIX, f"unexpected seat type {st}"
        want = base + SUFFIX[st]
        if code != want: todo.append((rid, code, want, yr, exam))
    by = {}
    for rid, old, new, yr, exam in todo: by.setdefault((old, new, yr, exam), []).append(rid)
    for (old, new, yr, exam), ids in sorted(by.items()):
        cid = c.execute(text("select id from categories where exam_id=:e and academic_year_id=:y and code=:c"), {"e": exam, "y": yr, "c": new}).scalar()
        if cid is None:
            cid = c.execute(text("insert into categories (exam_id, academic_year_id, code, is_verified) values (:e,:y,:c,false) returning id"), {"e": exam, "y": yr, "c": new}).scalar()
        n = c.execute(text("update cutoff_records set category_code_raw=:n, category_id=:cid where id = any(:ids)"), {"n": new, "cid": cid, "ids": ids}).rowcount
        assert n == len(ids)
        print(f"  {old:10s} -> {new:10s} year_id={yr}: {n} rows")
    # categories that no cutoff row references any more
    dead = c.execute(text("delete from categories c where c.code = any(:v) and not exists (select 1 from cutoff_records r where r.category_id=c.id)"), {"v": BASES + [b + x for b in BASES for x in "SHO"]}).rowcount
    print(f"{'APPLIED' if APPLY else 'DRY-RUN'}: {len(todo)} cutoff rows relabelled, {dead} unreferenced category rows removed")
    assert not APPLY or True
    (tx.commit if APPLY else tx.rollback)()
except Exception:
    tx.rollback(); raise
