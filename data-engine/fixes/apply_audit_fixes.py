"""Corrections found by the independent audit (data/verification/*). Dry-run by default; pass --apply to write.

Every fix runs in its own transaction and aborts unless the number of rows touched equals what the audit predicted.
Usage: set -a; . .env.local; set +a; python data-engine/fixes/apply_audit_fixes.py [--apply]
"""
import collections, json, os, pickle, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from sqlalchemy import create_engine, text

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
APPLY = "--apply" in sys.argv
e = create_engine(os.environ["DATABASE_URL_UNPOOLED"].replace("postgresql://", "postgresql+psycopg://", 1))
norm = lambda s: re.sub(r"\s+", " ", s.strip().lower())


def ownership(status):
    s = status.lower()
    if s.startswith(("government-aided", "government aided", "aided")): return "aided"
    if s.startswith("government"): return "government"
    if s.startswith(("un-aided", "unaided")): return "unaided"
    return None


def fix(title, fn):
    with e.connect() as c:
        tx = c.begin()
        try:
            msg = fn(c)
            if APPLY: tx.commit(); print(f"APPLIED  {title}: {msg}")
            else: tx.rollback(); print(f"DRY-RUN  {title}: {msg}")
        except AssertionError as ex:
            tx.rollback(); print(f"ABORTED  {title}: {ex}"); raise


# A. category codes whose last letter wrapped onto a second line in the PDF header (PWDROBC + S ...)
def a(c):
    m = {"PWDROBC": "PWDROBCS", "DEFRSEBC": "DEFRSEBCS", "PWDRSEBC": "PWDRSEBCS"}
    want = sum(c.execute(text("select count(*) from cutoff_records where category_code_raw=:k"), {"k": k}).scalar() for k in m)
    assert want == 269, f"expected 269 cutoff rows, found {want}"
    assert c.execute(text("select count(*) from cutoff_records where category_code_raw = any(:v)"), {"v": list(m.values())}).scalar() == 0
    n = sum(c.execute(text("update cutoff_records set category_code_raw=:v where category_code_raw=:k"), {"k": k, "v": v}).rowcount for k, v in m.items())
    cats = sum(c.execute(text("update categories set code=:v where code=:k"), {"k": k, "v": v}).rowcount for k, v in m.items())
    assert n == 269, n
    return f"{n} cutoff rows, {cats} category rows"
# A (blanket "+S") was WRONG for Home University sections (their wrapped letter is H). Superseded by fix_category_suffix.py.
print("SKIPPED  A category codes: use data-engine/fixes/fix_category_suffix.py (section-aware)")


# B. course names whose wrapped second line was dropped
def b(c):
    bad = json.load(open(os.path.join(ROOT, "data/verification/entity-audit/course_names.json")))["dbwrong"]
    assert len(bad) == 15, len(bad)
    old_norms = set()
    for code, old, good, _ in bad:
        row = c.execute(text("select id, name_raw, branch_id from college_courses where choice_code=:c"), {"c": code}).one()
        assert row.name_raw == old, (code, row.name_raw)
        old_norms.add(norm(old))
        br = c.execute(text("select id from branches where normalized_name=:n"), {"n": norm(good)}).scalar()
        if br is None:
            br = c.execute(text("insert into branches (course_id, name, normalized_name) select course_id, :nm, :n from branches where id=:b returning id"),
                           {"nm": good, "n": norm(good), "b": row.branch_id}).scalar()
        c.execute(text("update college_courses set name_raw=:g, branch_id=:b where id=:i"), {"g": good, "b": br, "i": row.id})
        c.execute(text("update cutoff_records set branch_id=:b where college_course_id=:i"), {"b": br, "i": row.id})
    gone = 0
    for n_ in old_norms:   # drop the truncated branch rows only if nothing references them any more
        gone += c.execute(text("delete from branches b where b.normalized_name=:n and not exists (select 1 from college_courses where branch_id=b.id) "
                               "and not exists (select 1 from cutoff_records where branch_id=b.id)"), {"n": n_}).rowcount
    return f"{len(bad)} course names completed, {gone} orphan truncated branch rows removed"
fix("B truncated course names", b)


# C. 'Government-Aided' colleges were classified as government
def cfix(c):
    n = c.execute(text("update colleges set ownership='aided' where institute_code in ('02020','03012','03014','06007') and ownership='government' "
                       "and (status_raw ilike 'Government-Aided%' or status_raw ilike 'Government Aided%')")).rowcount
    assert n == 4, n
    return f"{n} colleges -> aided"
fix("C ownership of Government-Aided colleges", cfix)


# D. keep the latest printed name (the importer had kept the first-seen name). Slugs are left unchanged so URLs stay valid.
def d(c):
    items = json.load(open(os.path.join(ROOT, "data/verification/entity-audit/names.json")))["latest_diff"]
    assert len(items) == 21, len(items)
    for code, old, new, _, _ in items:
        n = c.execute(text("update colleges set name=:n, normalized_name=:nn where institute_code=:c and name=:o"), {"n": new, "nn": norm(new), "c": code, "o": old}).rowcount
        assert n == 1, (code, old)
    return f"{len(items)} college names updated to the latest printed name"
fix("D latest college names", d)


# E/F. status and home university from the 2024 lists (per-course status/university lines; only where unambiguous)
def ef(c):
    st, un = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    for r in (1, 2, 3):
        _, res = pickle.load(open(os.path.join(ROOT, f"data/parsed/2024ENGG_CAP{r}_CutOff.pdf.pkl"), "rb"))
        seen = set()
        for cell in res.cells:
            if (cell.choice_code) in seen: continue
            seen.add(cell.choice_code)
            if cell.status_raw: st[cell.institute_code][cell.status_raw] += 1
            if cell.university_raw: un[cell.institute_code][cell.university_raw] += 1
    cur = {r.institute_code: r for r in c.execute(text("select institute_code, status_raw, ownership, university from colleges"))}
    ns = nu = cleared = 0
    for code, row in cur.items():
        if len(st[code]) == 1:
            s = next(iter(st[code]))
            if s != row.status_raw:
                o = ownership(s) or row.ownership
                c.execute(text("update colleges set status_raw=:s, ownership=:o where institute_code=:c"), {"s": s, "o": o, "c": code}); ns += 1
        real = {k: v for k, v in un[code].items() if k.strip().lower() != "autonomous institute"}
        if real:
            u = max(real, key=real.get)
            if u != row.university:
                c.execute(text("update colleges set university=:u where institute_code=:c"), {"u": u, "c": code}); nu += 1
        elif (row.university or "").strip().lower() == "autonomous institute":
            c.execute(text("update colleges set university=null where institute_code=:c"), {"c": code}); cleared += 1
    return f"{ns} statuses updated, {nu} universities set, {cleared} non-university values cleared"
fix("E/F latest status and home university", ef)
if not APPLY: print("\n(dry run: nothing was written. re-run with --apply)")
