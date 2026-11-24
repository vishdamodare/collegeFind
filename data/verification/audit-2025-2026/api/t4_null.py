from common import *
c=eng().connect()
rows=c.execute(text("select co.slug,cc.choice_code,r.category_code_raw,s.code,a.label,r.stage_label,r.closing_rank from cutoff_records r join colleges co on co.id=r.college_id join college_courses cc on cc.id=r.college_course_id join seat_types s on s.id=r.seat_type_id join academic_years a on a.id=r.academic_year_id where r.closing_percentile is null limit 26")).all()
print(len(rows),rows[:2])
# does the null row win the 'highest stage' pick in trends/predict?
hit=0;ok=0;ins=0
for sl,ch,cat,st,y,sg,rk in rows:
    _,r=post({"exam_code":"MHT_CET","percentile":"50","category":cat,"seat_type":st,"year":y,"branch":"","status":"insufficient_data","limit":100})
    f=[i for i in r["items"] if i["college_slug"]==sl and i["choice_code"]==ch]
    for i in f:
        for rec in i["records"]:
            if rec["closing_percentile"] is None:
                hit+=1; ok+= rec["status"]=="insufficient_data" and rec["gap"] is None
    t=get("/trends",college_slug=sl,choice_code=ch,category=cat,seat_type=st)["points"]
    for p in t:
        if p["closing_percentile"] is None: ins+=1
print("null recs seen in predict",hit,"correct",ok,"null points in trends",ins,"summary example",r["summary"],r["total"])
