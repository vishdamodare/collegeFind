import random, json
from common import *
from decimal import Decimal
e=eng(); T_=T(); c=e.connect()
m=get("/meta"); srv=m["serving_unverified"]
sts=("verified","pending") if srv else ("verified",)
q=lambda sql,**k: c.execute(text(sql),k).all()
T_.chk(m["years"]==[r[0] for r in q("select distinct a.label from academic_years a join cutoff_records r on r.academic_year_id=a.id where r.verification_status=any(:s) order by 1",s=list(sts))],"years")
T_.chk(m["rounds"]==[r[0] for r in q("select distinct c.round_no from counselling_rounds c join cutoff_records r on r.round_id=c.id where r.verification_status=any(:s) order by 1",s=list(sts))],"rounds")
cats=sorted(q("select distinct r.category_code_raw,s.code from cutoff_records r join seat_types s on s.id=r.seat_type_id where r.verification_status=any(:s)",s=list(sts)))
T_.chk(sorted((x["code"],x["seat_type_code"]) for x in m["categories"])==cats,"categories")
T_.chk(len(m["categories"])==len(cats),"cat count")
T_.chk({x["code"]:x["name"] for x in m["seat_types"]}=={r[0]:r[1] for r in q("select code,name from seat_types")},"seat types")
cnt=dict(q("select verification_status,count(*) from cutoff_records group by 1"))
T_.chk(m["records"]==cnt,"record counts %s vs %s"%(m["records"],cnt))
print("meta",m["records"],srv,len(m["categories"]),"bad",T_.bad)
# (2) cutoffs random
tot=get("/cutoffs",page_size=1)["total"]
sqltot=q("select count(*) from cutoff_records where verification_status=any(:s)",s=list(sts))[0][0]
T_.chk(tot==sqltot,"cutoffs total %s vs %s"%(tot,sqltot))
random.seed(7); ps=200; pages=(sqltot+ps-1)//ps
sample=[]
for p in random.sample(range(1,pages+1),12):
    d=get("/cutoffs",page=p,page_size=ps); sample+=d["items"]
print("fetched",len(sample))
# need row identity: match by natural key
rows={}
fields=0
for it in sample:
    r=q("""select r.closing_percentile,r.closing_rank,r.stage_label,a.label,c.round_no,r.source_page,r.original_metric_text,r.verification_status,s.code,co.name,cc.name_raw,u.source_url,r.stage
      from cutoff_records r join colleges co on co.id=r.college_id join college_courses cc on cc.id=r.college_course_id join seat_types s on s.id=r.seat_type_id
      join academic_years a on a.id=r.academic_year_id join counselling_rounds c on c.id=r.round_id join uploaded_documents u on u.id=r.source_document_id
      where co.slug=:sl and cc.choice_code=:cc and r.category_code_raw=:cat and s.code=:st and a.label=:y and c.round_no=:rd and r.stage_label=:sg""",
      sl=it["college_slug"],cc=it["choice_code"],cat=it["category"],st=it["seat_type_code"],y=it["year"],rd=it["round"],sg=it["stage_label"])
    if len(r)!=1: T_.chk(False,"identity not unique %s n=%d"%(it["college_slug"],len(r))); continue
    r=r[0]
    exp={"closing_percentile":str(r[0]) if r[0] is not None else None,"closing_rank":r[1],"stage_label":r[2],"year":r[3],"round":r[4],"source_page":r[5],"original_text":r[6],"verification_status":r[7],"seat_type_code":r[8],"college":r[9],"branch":r[10],"source_url":r[11],"stage":r[12]}
    for k,v in exp.items():
        T_.chk(it[k]==v,"%s %s: api=%r db=%r"%(it["college_slug"],k,it[k],v))
    # null never zero
    if exp["closing_percentile"] is None: T_.chk(it["closing_percentile"] is None,"null->0")
print("cutoffs rows",len(sample),"checks",T_.n,"ok",T_.ok,"bad",T_.bad[:10])
json.dump({"n":T_.n,"ok":T_.ok,"bad":T_.bad,"rows":len(sample)},open("t1.json","w"))
