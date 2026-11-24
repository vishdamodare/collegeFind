import random, json
from common import *
e=eng(); c=e.connect(); T_=T()
q=lambda sql,**k: c.execute(text(sql),k).all()
m=get("/meta"); sts=["verified","pending"] if m["serving_unverified"] else ["verified"]
random.seed(11)
# (3) colleges
slugs=[r[0] for r in q("select slug from colleges")]
lst=get("/colleges",page_size=100)
T_.chk(lst["total"]==len(slugs),"colleges total %s vs %s"%(lst["total"],len(slugs)))
pick=random.sample(slugs,40)
ncomp=0
for sl in pick:
    d=get("/colleges/"+sl)
    cr=q("select id,name,institute_code,university,ownership,status_raw from colleges where slug=:s",s=sl)[0]
    T_.chk((d["name"],d["institute_code"],d["university"],d["ownership"],d["status_raw"])==tuple(cr[1:]),"college hdr "+sl)
    cc=q("select cc.choice_code,cc.name_raw,cc.id from college_courses cc where college_id=:i",i=cr[0])
    T_.chk(sorted(b["choice_code"] for b in d["branches"])==sorted(x[0] for x in cc),"branch set "+sl)
    tot_si=0; tot_db=0
    for b in d["branches"]:
        ccid=[x[2] for x in cc if x[0]==b["choice_code"]][0]
        rows=q("""select a.label,i.si,i.ms_seats,i.minority_seats,i.all_india_seats,i.institute_seats,i.orphan_seats,i.published_date,i.source_page
                  from course_intakes i join academic_years a on a.id=i.academic_year_id where i.college_course_id=:c and i.verification_status=any(:s) order by a.start_year desc""",c=ccid,s=sts)
        yrs=q("select distinct a.label from cutoff_records r join academic_years a on a.id=r.academic_year_id where r.college_course_id=:c and r.verification_status=any(:s) order by 1",c=ccid,s=sts)
        T_.chk(b["cutoff_years"]==[y[0] for y in yrs],"cutoff_years %s %s"%(sl,b["choice_code"]))
        if not rows:
            T_.chk(b["intake"] is None,"intake should be null "+sl); continue
        r=rows[0]; i=b["intake"]; ncomp+=1
        exp=dict(year=r[0],si=r[1],ms_seats=r[2],minority_seats=r[3],all_india_seats=r[4],institute_seats=r[5],orphan_seats=r[6],published_date=r[7].isoformat() if r[7] else None,source_page=r[8])
        for k,v in exp.items(): T_.chk(i[k]==v,"intake %s %s %s api=%r db=%r"%(sl,b["choice_code"],k,i[k],v))
        tot_si+=i["si"] or 0; tot_db+=r[1] or 0
        # null never 0
        for k in ("si","ms_seats","minority_seats","all_india_seats","institute_seats","orphan_seats"):
            if r[["si","ms_seats","minority_seats","all_india_seats","institute_seats","orphan_seats"].index(k)+1] is None: T_.chk(i[k] is None,"null->0 intake "+k)
    T_.chk(tot_si==tot_db,"sum SI "+sl)
print("colleges checks",T_.n,T_.ok,"courses compared",ncomp,T_.bad[:10])
c1=(T_.n,T_.ok,list(T_.bad))
# (4) trends
T_=T()
combos=q("""select co.slug,cc.choice_code,r.category_code_raw,s.code from cutoff_records r join colleges co on co.id=r.college_id join college_courses cc on cc.id=r.college_course_id join seat_types s on s.id=r.seat_type_id
 where r.verification_status=any(:s) group by 1,2,3,4 order by random() limit 60""",s=sts)
npts=0
for sl,ch,cat,st in combos:
    d=get("/trends",college_slug=sl,choice_code=ch,category=cat,seat_type=st)["points"]
    rows=q("""select a.label,a.start_year,c.round_no,r.stage,r.stage_label,r.closing_percentile,r.closing_rank,r.source_page,r.original_metric_text
      from cutoff_records r join colleges co on co.id=r.college_id join college_courses cc on cc.id=r.college_course_id join seat_types s on s.id=r.seat_type_id
      join academic_years a on a.id=r.academic_year_id join counselling_rounds c on c.id=r.round_id
      where co.slug=:a and cc.choice_code=:b and r.category_code_raw=:c and s.code=:d and r.verification_status=any(:s)""",a=sl,b=ch,c=cat,d=st,s=sts)
    best={}
    for r in rows:
        k=(r[1],r[2])
        if k not in best or (r[3],r[4])>(best[k][3],best[k][4]): best[k]=r
    exp=[best[k] for k in sorted(best)]
    keys=[(p["year"],p["round"]) for p in d]
    T_.chk(len(set(keys))==len(keys),"dup (year,round) "+sl)
    T_.chk(len(d)==len(exp),"npoints %s %s api=%d db=%d"%(sl,ch,len(d),len(exp)))
    for p,r in zip(d,exp):
        npts+=1
        T_.chk((p["year"],p["round"],p["stage_label"],p["closing_rank"],p["source_page"],p["original_text"])==(r[0],r[2],r[4],r[6],r[7],r[8]),"trend pt %s %s %s"%(sl,ch,p))
        T_.chk(p["closing_percentile"]==(str(r[5]) if r[5] is not None else None),"trend pct %s %s api=%r db=%r"%(sl,ch,p["closing_percentile"],r[5]))
    # trend-options
    o=get("/trend-options",college_slug=sl,choice_code=ch)["options"]
    T_.chk(any(x["seat_type_code"]==st and x["category"]==cat for x in o),"trend-option present "+sl)
print("trends combos",len(combos),"points",npts,"checks",T_.n,T_.ok,T_.bad[:10])
json.dump({"colleges":[c1[0],c1[1],c1[2]],"trends":[T_.n,T_.ok,T_.bad],"courses_compared":ncomp,"points":npts,"combos":len(combos)},open("t2.json","w"))
