import os,sys,time,hashlib,urllib.request,json
sys.path.insert(0,'.')
from sqlalchemy import create_engine,text
e=create_engine(os.environ["DATABASE_URL_UNPOOLED"].replace("postgresql://","postgresql+psycopg://",1))
for i in range(5):
    try:
        rows=e.connect().execute(text("select original_filename,source_url,sha256,size_bytes from uploaded_documents order by 1")).fetchall();break
    except Exception as ex: print("retry");time.sleep(5)
res={}
sh=lambda p:hashlib.sha256(open(p,'rb').read()).hexdigest()
for fn,url,db,sz in rows:
    p='dl/'+fn; st=None
    for t in range(3):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req,timeout=120) as r: st=r.status; open(p,'wb').write(r.read())
            break
        except Exception as ex: st=repr(ex)[:100]; time.sleep(3)
    ok=os.path.exists(p) and os.path.getsize(p)>0
    h=sh(p) if ok else None
    loc=sh('/Users/vish/collegeFind/data/raw/'+fn)
    res[fn]=dict(status=st,live=h,db=db,local=loc,size_live=os.path.getsize(p) if ok else None,size_db=sz,live_eq_db=h==db,live_eq_local=h==loc,db_eq_local=db==loc)
    print(fn,st,res[fn]['live_eq_db'],res[fn]['live_eq_local'],res[fn]['db_eq_local'],flush=True)
    time.sleep(3)
json.dump(res,open('hashes.json','w'),indent=1)
