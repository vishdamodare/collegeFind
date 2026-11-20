import os,time
from sqlalchemy import create_engine,text
for i in range(5):
  try:
    c=create_engine(os.environ["DATABASE_URL_UNPOOLED"].replace("postgresql://","postgresql+psycopg://",1)).connect();break
  except Exception: time.sleep(5)
for r in c.execute(text("""select r.category_code_raw,count(*) from cutoff_records r where category_code_raw ~ '^(PWDR|DEFR|PWDS|DEFS|PWDO|DEFO)' group by 1 order by 1""")): print(r)
print("--- by year")
for r in c.execute(text("""select ay.label,r.category_code_raw,count(*) from cutoff_records r join academic_years ay on ay.id=r.academic_year_id where category_code_raw in ('PWDROBC','PWDROBCS','DEFRSEBC','DEFRSEBCS','PWDRSEBC','PWDRSEBCS','DEFROBC','DEFROBCS') group by 1,2 order by 1,2""")): print(r)
