import os,json,time,random,re,fitz,collections
from sqlalchemy import create_engine,text
e=create_engine(os.environ["DATABASE_URL_UNPOOLED"].replace("postgresql://","postgresql+psycopg://",1))
pc=json.load(open('pagecounts.json'))
def q(s,**k):
    for i in range(5):
        try:
            with e.connect() as c: return c.execute(text(s),k).fetchall()
        except Exception as ex:
            print("retry",repr(ex)[:60]); time.sleep(5)
docs={r[0]:r[1] for r in q("select id,original_filename from uploaded_documents")}
# (4) page range
st=q("select source_document_id,count(*),min(source_page),max(source_page),count(*) filter (where source_page is null) from cutoff_records group by 1 order by 1")
bad4=0;tot4=0;out4=[]
for d,n,mn,mx,nl in st:
    out4.append((docs[d],n,mn,mx,nl,pc[docs[d]]))
    print(docs[d],n,mn,mx,nl,pc[docs[d]])
    pcn=pc[docs[d]]
    r=q("select count(*) from cutoff_records where source_document_id=:d and (source_page is null or source_page<1 or source_page>:p)",d=d,p=pcn)[0][0]
    bad4+=r; tot4+=n
print("page-range total",tot4,"bad",bad4)
# (3) sample
ids=[r[0] for r in q("select id from cutoff_records order by id")]
random.seed(20241110); samp=sorted(random.sample(ids,300))
rows=q("select id,source_document_id,source_page,original_metric_text,closing_rank,closing_percentile,stage_label from cutoff_records where id=any(:ids) order by id",ids=samp)
cache={}
def pg(doc,p):
    k=(doc,p)
    if k not in cache:
        if doc not in cache: cache[doc]=fitz.open('/Users/vish/collegeFind/data/raw/'+docs[doc])
        cache[k]=cache[doc][p-1].get_text() if 1<=p<=len(cache[doc]) else ""
    return cache[k]
norm=lambda s:re.sub(r"\s+","",s)
res=[];fails=[]
for id_,d,p,m,rk,pe,sl in rows:
    pat=norm(m)
    t0=norm(pg(d,p)); where=None
    if pat in t0: where="same"
    elif p>1 and pat in norm(pg(d,p-1)): where="prev"
    elif p>2 and pat in norm(pg(d,p-2)): where="prev2"
    elif p<pc[docs[d]] and pat in norm(pg(d,p+1)): where="next"
    res.append((id_,docs[d],p,m,where))
    if where not in("same","prev"): fails.append((id_,docs[d],p,m,where,rk,pe,sl))
print("sample",len(rows),collections.Counter(r[4] for r in res))
for f in fails: print("FAIL",f)
json.dump(dict(sample=res,fails=fails,pr=out4,bad4=bad4,tot4=tot4),open('results34.json','w'),default=str)
