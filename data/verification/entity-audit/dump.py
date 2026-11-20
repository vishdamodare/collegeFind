import os,time,json
from sqlalchemy import create_engine,text
for t in range(5):
    try:
        e=create_engine(os.environ["DATABASE_URL_UNPOOLED"].replace("postgresql://","postgresql+psycopg://",1))
        with e.connect() as c:
            out={}
            out['colleges']=[dict(r._mapping) for r in c.execute(text("select * from colleges"))]
            out['cc']=[dict(r._mapping) for r in c.execute(text("select * from college_courses"))]
            out['cut_cc']=[r[0] for r in c.execute(text("select distinct college_course_id from cutoff_records"))]
            out['cut_col']=[r[0] for r in c.execute(text("select distinct college_id from cutoff_records"))]
            out['int_cc']=[r[0] for r in c.execute(text("select distinct college_course_id from course_intakes"))]
            out['cols_info']={tb:[r[0] for r in c.execute(text(f"select column_name from information_schema.columns where table_name='{tb}'"))] for tb in ('colleges','college_courses')}
            out['own']=[list(r) for r in c.execute(text("select ownership,status_raw,count(*) from colleges group by 1,2 order by 3 desc"))]
        json.dump(out,open('db.json','w'),default=str);print('ok',len(out['colleges']),len(out['cc']));break
    except Exception as ex:
        print('err',str(ex)[:80]);time.sleep(5)
