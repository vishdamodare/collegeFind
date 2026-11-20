import os, pickle, json, time, collections
from sqlalchemy import create_engine, text
url = os.environ["DATABASE_URL_UNPOOLED"].replace("postgresql://", "postgresql+psycopg://", 1)
Q = text("""select cr.id, cc.choice_code, st.code sc, cr.stage_label, cr.category_code_raw cat, cr.closing_rank, cr.closing_percentile, cr.source_page, ud.original_filename fn
 from cutoff_records cr join college_courses cc on cc.id=cr.college_course_id join seat_types st on st.id=cr.seat_type_id
 join uploaded_documents ud on ud.id=cr.source_document_id""")
for t in range(6):
    try:
        with create_engine(url).connect() as c: rows = c.execute(Q).fetchall(); break
    except Exception as e:
        if "resolve" in str(e) and t < 5: time.sleep(5); continue
        raise
print("db rows", len(rows))
OUT = "/Users/vish/collegeFind/data/verification/cutoff-reextraction/"
logs = {l["pdf"]: l for l in json.load(open(OUT + "extract_log.json"))}
bydb = collections.defaultdict(dict); dupdb = collections.Counter(); nofile = 0
for r in rows:
    k = (r.choice_code, r.sc, r.stage_label, r.cat)
    if k in bydb[r.fn]: dupdb[r.fn] += 1
    bydb[r.fn][k] = (r.closing_rank, r.closing_percentile, r.source_page, r.id)
res = {}; tot = collections.Counter()
for fn, d in sorted(bydb.items()):
    ex = pickle.load(open(OUT + f"extracted/{fn}.pkl", "rb")) if os.path.exists(OUT + f"extracted/{fn}.pkl") else None
    if ex is None: res[fn] = {"error": "no extraction", "db": len(d)}; continue
    m = 0; only_db = []; only_ex = []; diff = []; pagediff = 0
    for k, (rk, pc, pg, rid) in d.items():
        e = ex.get(k)
        if e is None: only_db.append((k, rk, str(pc), pg, rid)); continue
        if e[0] == rk and ((e[1] is None and pc is None) or (e[1] is not None and pc is not None and e[1] == pc)):
            m += 1
        else: diff.append((k, "db", rk, str(pc), "pdf", e[0], str(e[1]), "dbpage", pg, "pdfpage", e[2], rid))
        if e[2] != pg: pagediff += 1
    for k, e in ex.items():
        if k not in d: only_ex.append((k, e[0], str(e[1]), e[2]))
    res[fn] = dict(db=len(d), dup_db_keys=dupdb[fn], extracted=len(ex), match=m, only_db=len(only_db), only_ex=len(only_ex), diff=len(diff),
                   page_mismatch=pagediff, overflow_cells=logs[fn]["overflow_cells"], ex_only_ex=only_ex[:10], ex_only_db=only_db[:10], ex_diff=diff[:10])
    for k in ("db", "match", "only_db", "only_ex", "diff", "extracted", "page_mismatch"): tot[k] += res[fn][k]
json.dump({"files": res, "total": tot}, open(OUT + "report.json", "w"), indent=1, default=str)
for fn, r in res.items(): print(fn, {k: v for k, v in r.items() if not k.startswith("ex_")})
print(dict(tot))
