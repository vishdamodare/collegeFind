import json, itertools
from decimal import Decimal as D
from common import *
e=eng(); c=e.connect(); T_=T()
q=lambda sql,**k: c.execute(text(sql),k).all()
m=get("/meta"); sts=["verified","pending"] if m["serving_unverified"] else ["verified"]
def cls(s,cl):
    if cl is None: return "insufficient_data",None
    g=s-cl
    return ("ambitious" if g<D("-1.0") else "safer_historical" if g>D("1.0") else "moderate"),g
def expected(cat,st,year,branch,rnd=None):
    rows=q("""select cc.id,s.id,s.code,a.label,a.start_year,c.round_no,r.stage,r.stage_label,r.closing_percentile,r.closing_rank,r.source_page,r.original_metric_text,co.slug,cc.name_raw,cc.choice_code
      from cutoff_records r join colleges co on co.id=r.college_id join college_courses cc on cc.id=r.college_course_id join seat_types s on s.id=r.seat_type_id
      join academic_years a on a.id=r.academic_year_id join counselling_rounds c on c.id=r.round_id
      where r.category_code_raw=:cat and r.verification_status=any(:s) and (cast(:st as text) is null or s.code=:st) and (cast(:y as text) is null or a.label=:y)
      and (cast(:rd as int) is null or c.round_no=:rd) and (cast(:b as text)='' or lower(cc.name_raw) like :bl)""",cat=cat,s=sts,st=st,y=year,rd=rnd,b=branch,bl="%"+branch.lower()+"%")
    best={}
    for r in rows:
        k=(r[0],r[1],r[5],r[4])
        if k not in best or (r[6],r[7])>(best[k][6],best[k][7]): best[k]=r
    g={}
    for r in best.values(): g.setdefault((r[0],r[1]),[]).append(r)
    return g
bodies=[]
for p,cat,st,y,b in [("0.5","GOPENS","STATE_LEVEL",None,"computer"),("35","GOPENS","STATE_LEVEL",None,""),("62.4","GOBCS","STATE_LEVEL","2024-25","computer"),
  ("80","GOPENS","STATE_LEVEL",None,"civil"),("92.5","GOPENS","STATE_LEVEL",None,"computer"),("99.9","GOPENS","STATE_LEVEL","2023-24",""),
  ("92.5","GSCS","STATE_LEVEL",None,"information"),("80","LOPENH","HU_TO_HU",None,"computer"),("62.4","GOPENS","HU_TO_OHU",None,""),
  ("99.9","EWS","STATE_LEVEL","2022-23","mechanical"),("35","GOPENS",None,None,"electronics"),("92.5","GOPENH","HU_TO_HU","2024-25","computer"),
  ("80","TFWS","STATE_LEVEL",None,""),("0.5","TFWS","STATE_LEVEL","2024-25",""),("99.9","GOPENS","OHU_TO_OHU",None,"computer"),("62.4","GSTS","STATE_LEVEL",None,"computer"),
  # 2025-26 / 2026-27 audit (24 Nov 2026)
  ("92.5","GOPENS","STATE_LEVEL","2025-26","computer"),("80","GOBCS","STATE_LEVEL","2026-27",""),("95","ORPHANI","STATE_LEVEL","2026-27",""),
  ("70","ORPHANN","STATE_LEVEL","2026-27",""),("88","EWS","STATE_LEVEL","2025-26","civil"),("99.5","GOPENH","HU_TO_HU","2026-27","computer"),
  ("60","LOPENO","OHU_TO_OHU","2025-26",""),("85","TFWS","STATE_LEVEL","2026-27","information")]:
    bodies.append((p,cat,st,y,b))
tot_items=0; nrec=0; cmbs=0
for p,cat,st,y,b in bodies:
    body={"exam_code":"MHT_CET","percentile":p,"category":cat,"seat_type":st,"year":y,"branch":b,"status":None,"offset":0,"limit":100}
    code,full=post(body)
    if code!=200: T_.chk(False,"predict %s -> %s"%(body,code)); continue
    cmbs+=1
    # page everything
    items=list(full["items"]); off=100
    while len(items)<full["total"]:
        _,pg=post({**body,"offset":off}); items+=pg["items"]; off+=100
        if not pg["items"]: break
    ex=expected(cat,st,y,b); S=D(p)
    T_.chk(full["total"]==len(ex)==len(items),"total/groups %s ex=%d api=%d/%d"%(body,len(ex),full["total"],len(items)))
    # map items by (slug,choice,seat)
    cnt={"safer_historical":0,"moderate":0,"ambitious":0}
    heads=[]
    ccmap={ (r[12],) :0 for g in ex.values() for r in g}
    exmap={}
    for (ccid,stid),g in ex.items(): exmap[(g[0][12],g[0][2],g[0][14])]=g
    seen=set()
    for it in items:
        key=(it["college_slug"],it["seat_type_code"],it["choice_code"]); T_.chk(key not in seen,"dup group "+str(key)); seen.add(key)
        g=exmap.get(key)
        if g is None: T_.chk(False,"extra group "+str(key)); continue
        T_.chk(len(it["records"])==len(g),"nrecords "+str(key))
        recs=sorted(g,key=lambda r:(-r[4],r[5]))
        for ar,r in zip(it["records"],recs):
            nrec+=1
            est,eg=cls(S,r[8])
            ok=(ar["year"]==r[3] and ar["round"]==r[5] and ar["stage_label"]==r[7] and ar["closing_rank"]==r[9] and ar["source_page"]==r[10]
                and ar["closing_percentile"]==(str(r[8]) if r[8] is not None else None) and ar["status"]==est and ((ar["gap"] is None) if eg is None else D(ar["gap"])==eg))
            T_.chk(ok,"record %s %s api=%s exp=%s %s"%(key,body["percentile"],ar,est,eg))
            if r[8] is None: T_.chk(ar["status"]=="insufficient_data" and ar["gap"] is None and ar["closing_percentile"] is None,"null handling "+str(key))
        lat=recs[0][4]; hd=min([r for r in recs if r[4]==lat],key=lambda r:r[5])
        hs,hg=cls(S,hd[8])
        T_.chk(it["status"]==hs,"headline status %s"%(key,))
        T_.chk(it["headline_idx"]==recs.index(hd) and it["records"][it["headline_idx"]]["year"]==hd[3] and it["records"][it["headline_idx"]]["round"]==hd[5],"headline idx %s"%(key,))
        T_.chk(it["choice_code"] is not None and it["category"]==cat,"fields")
        heads.append((hs,hd[8],abs(hg) if hg is not None else None,key))
        if hs in cnt: cnt[hs]+=1
    # summary
    T_.chk(full["summary"]==cnt,"summary %s api=%s exp=%s"%(body,full["summary"],cnt))
    # ordering: api order by status then key
    order={"safer_historical":0,"moderate":1,"ambitious":2,"insufficient_data":3}
    seq=[]
    for it in items:
        key=(it["college_slug"],it["seat_type_code"],it["choice_code"]); h=[x for x in heads if x[3]==key]
        if h: seq.append(h[0])
    ok=True
    for a,b2 in zip(seq,seq[1:]):
        if order[a[0]]>order[b2[0]]: ok=False
        elif a[0]==b2[0]:
            if a[0]=="safer_historical" and a[1]<b2[1]: ok=False
            if a[0]=="moderate" and a[2]>b2[2]: ok=False
            if a[0]=="ambitious" and a[1]>b2[1]: ok=False
    T_.chk(ok,"ordering %s"%(body,)); tot_items+=len(items)
    # paging + status filter
    if len(items)>=7:
        _,p1=post({**body,"offset":3,"limit":4}); T_.chk([ (x["college_slug"],x["seat_type_code"],x["choice_code"]) for x in p1["items"]]==[(x["college_slug"],x["seat_type_code"],x["choice_code"]) for x in items[3:7]] and p1["total"]==full["total"],"paging "+str(body))
    for stt in cnt:
        if cnt[stt]:
            _,f=post({**body,"status":stt,"limit":100}); T_.chk(f["total"]==cnt[stt] and all(x["status"]==stt for x in f["items"]) and f["summary"]==full["summary"],"status filter %s %s"%(body,stt))
    print(body["percentile"],cat,st,y,b,"groups",len(items),cnt,flush=True)
# (6) NEET + zero handling
code,r=post({"exam_code":"NEET_UG","percentile":"92.5","category":"GOPENS","seat_type":"STATE_LEVEL","branch":""})
T_.chk(code>=400 and "items" not in r,"NEET error code=%s"%code); print("NEET",code,r)
code2,r2=post({"exam_code":"BOGUS","percentile":"92.5","category":"GOPENS"}); T_.chk(code2>=400,"bogus exam"); print("BOGUS",code2)
code3,r3=post({"exam_code":"MHT_CET","percentile":"101","category":"GOPENS"}); T_.chk(code3==422,"pct>100 rejected"); print("101",code3)
code4,r4=post({"exam_code":"MHT_CET","percentile":"-1","category":"GOPENS"}); T_.chk(code4==422,"pct<0 rejected")
# null count in db vs api never 0
nn=q("select count(*) from cutoff_records where closing_percentile is null and verification_status=any(:s)",s=sts)[0][0]
zero=q("select count(*) from cutoff_records where closing_percentile=0")[0][0]
print("null pct rows",nn,"zero pct rows in db",zero)
print("predict combos",cmbs,"items",tot_items,"records",nrec,"checks",T_.n,"ok",T_.ok,"bad",T_.bad[:15])
json.dump({"combos":cmbs,"groups":tot_items,"records":nrec,"n":T_.n,"ok":T_.ok,"bad":T_.bad,"neet":[code,r],"null_rows":nn,"zero_rows":zero},open("t3.json","w"),default=str)
