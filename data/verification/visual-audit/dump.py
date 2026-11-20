import os,json,fitz,time
from sqlalchemy import create_engine,text
sel=json.load(open("sample.json"))
for i in range(5):
  try:
    e=create_engine(os.environ["DATABASE_URL_UNPOOLED"].replace("postgresql://","postgresql+psycopg://",1)); c=e.connect(); break
  except Exception as ex: print("retry"); time.sleep(5)
os.makedirs("pages",exist_ok=True); os.makedirs("dbdump",exist_ok=True)
q=text("""select cc.choice_code,s.code st,r.category_code_raw cat,r.stage_label sl,r.closing_rank rk,r.closing_percentile pc,co.institute_code ic
from cutoff_records r join uploaded_documents d on d.id=r.source_document_id join college_courses cc on cc.id=r.college_course_id join colleges co on co.id=r.college_id join seat_types s on s.id=r.seat_type_id
where d.original_filename=:f and r.source_page=:p order by cc.choice_code,s.code,r.id""")
for f,ps in sel.items():
  doc=fitz.open("/Users/vish/collegeFind/data/raw/"+f)
  for p in ps:
    pg=doc[p-1]; tag=f[:4]+"R"+f[12]+f"_p{p}"
    pg.get_pixmap(matrix=fitz.Matrix(2,2)).save(f"pages/{tag}.png")
    rows=c.execute(q,{"f":f,"p":p}).fetchall()
    out=[];cur=None
    for ch,st,cat,sl,rk,pc,ic in rows:
      k=(ic,ch,st,sl)
      if k!=cur: out.append(f"\n[{ic} {ch} {st} | stage={sl}]"); cur=k
      out.append(f"{cat}:{rk}({'NULL' if pc is None else str(pc)[:10]})")
    open(f"dbdump/{tag}.txt","w").write(" ".join(out)+f"\n#rows={len(rows)}\n")
    print(tag,len(rows),pg.rect.width,pg.rect.height)
