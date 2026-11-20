import os, time, json, urllib.request, urllib.parse
from sqlalchemy import create_engine, text
def eng():
    for i in range(6):
        try:
            e=create_engine(os.environ["DATABASE_URL_UNPOOLED"].replace("postgresql://","postgresql+psycopg://",1))
            e.connect().close(); return e
        except Exception as ex:
            if "resolve" in str(ex) and i<5: time.sleep(5); continue
            raise
B="http://localhost:8000/api/v1"
def get(p,**q):
    q={k:v for k,v in q.items() if v is not None}
    with urllib.request.urlopen(B+p+("?"+urllib.parse.urlencode(q) if q else ""),timeout=120) as r: return json.load(r)
def post(body):
    rq=urllib.request.Request(B+"/predict",json.dumps(body).encode(),{"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(rq,timeout=180) as r: return r.status,json.load(r)
    except urllib.error.HTTPError as e: return e.code,json.loads(e.read() or b"{}")
class T:
    def __init__(s): s.n=0; s.ok=0; s.bad=[]
    def chk(s,cond,msg):
        s.n+=1
        if cond: s.ok+=1
        else: s.bad.append(msg)
