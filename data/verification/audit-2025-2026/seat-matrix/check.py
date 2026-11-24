"""Independent seat-matrix check for 2025 and 2026 (PyMuPDF word boxes, not the parser's text regex).
Each page: the choice-code word under the column header, then the integers on the same visual row right of the course
name, read left to right: SI, MS, Minority, All India, Institute, then 1 (2025) or 2 (2026: OrphanI, OrphanN) orphan columns.
Compared with course_intakes: every value, page, published date, and SI = MS + Minority + AI + Institute."""
import fitz, os, re, collections, datetime, json
from sqlalchemy import create_engine, text
FILES = {"2025SeatMatrix.pdf": ("2025-26", datetime.date(2025, 7, 25)), "2026_fe_seatmatrix_V1.pdf": ("2026-27", datetime.date(2026, 7, 27))}
CODE = re.compile(r"^\d{9,10}[A-Z]{0,3}$")
e = create_engine(os.environ["DATABASE_URL_UNPOOLED"].replace("postgresql://", "postgresql+psycopg://", 1))
with e.connect() as c:
    db = c.execute(text("""select ud.original_filename fn, cc.choice_code, si, ms_seats, minority_seats, all_india_seats, institute_seats, orphan_seats, source_page, published_date
        from course_intakes ci join college_courses cc on cc.id=ci.college_course_id join uploaded_documents ud on ud.id=ci.source_document_id
        where ud.original_filename = any(:f)"""), {"f": list(FILES)}).mappings().all()
out = {}
for fn, (year, pub) in FILES.items():
    dbk = {r["choice_code"]: r for r in db if r["fn"] == fn}
    d = fitz.open("/Users/vish/collegeFind/data/raw/" + fn)
    printed_pub = re.search(r"Published Date\s*:\s*(\d{1,2})/(\d{1,2})/(\d{4})", d[0].get_text())
    match = 0; bad = []; seen = collections.Counter(); arith = []; norow = []
    for pno, page in enumerate(d, 1):
        ws = page.get_text("words")
        hdr = [w for w in ws if w[4] == "Choice"]
        codes = [w for w in ws if CODE.match(w[4]) and hdr and w[1] > hdr[0][3] and w[0] < 100]
        if not codes: norow.append(pno); continue
        cw = codes[0]; y = (cw[1] + cw[3]) / 2
        row = sorted([w for w in ws if abs((w[1] + w[3]) / 2 - y) < 3 and w[0] > cw[2]], key=lambda w: w[0])
        nums = []
        for w in reversed(row):  # integers at the right end of the row (the course name never ends in a bare number column run)
            if re.fullmatch(r"\d+", w[4]): nums.append(int(w[4]))
            else: break
        nums.reverse()
        code = cw[4].rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ").zfill(10) + re.sub(r"^\d+", "", cw[4])
        seen[code] += 1
        si, ms, mi, ai, ins, *orph = nums
        if si != ms + mi + ai + ins: arith.append((pno, code, nums))
        r = dbk.get(code)
        got = None if r is None else [r["si"], r["ms_seats"], r["minority_seats"], r["all_india_seats"], r["institute_seats"], r["orphan_seats"], r["source_page"], r["published_date"]]
        exp = [si, ms, mi, ai, ins, sum(orph), pno, pub]
        if got == exp: match += 1
        else: bad.append((pno, code, exp, got))
    pdf_pub = printed_pub and datetime.date(int(printed_pub.group(3)), int(printed_pub.group(2)), int(printed_pub.group(1)))
    res = dict(pages=len(d), db=len(dbk), match=match, mismatch=len(bad), pdf_codes_not_in_db=len(set(seen) - set(dbk)),
               db_codes_not_in_pdf=len(set(dbk) - set(seen)), dup_codes=sum(1 for n in seen.values() if n > 1),
               arith_fail=len(arith), pages_without_row=len(norow), published_printed=str(pdf_pub), published_ok=pdf_pub == pub,
               examples=bad[:5], arith_ex=arith[:5], norow_ex=norow[:10])
    out[fn] = res; print(fn, {k: v for k, v in res.items() if not k.endswith("_ex") and k != "examples"}, res["examples"][:3])
json.dump(out, open("result.json", "w"), indent=1, default=str)
