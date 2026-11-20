import os,time,json
from sqlalchemy import create_engine,text
def eng():
    for i in range(5):
        try:
            e=create_engine(os.environ["DATABASE_URL_UNPOOLED"].replace("postgresql://","postgresql+psycopg://",1))
            e.connect().close(); return e
        except Exception as ex:
            print("retry",type(ex).__name__); time.sleep(5)
    raise SystemExit("no db")
e=eng()
with e.connect() as c:
    rows=c.execute(text("select id,original_filename,source_url,sha256,size_bytes,publication_date from uploaded_documents order by original_filename")).fetchall()
    for r in rows: print(tuple(r))
    print(c.execute(text("select source_document_id,a.label,r.round_no,count(*) from cutoff_records cr join academic_years a on a.id=cr.academic_year_id join counselling_rounds r on r.id=cr.round_id group by 1,2,3 order by 1,2,3")).fetchall())
