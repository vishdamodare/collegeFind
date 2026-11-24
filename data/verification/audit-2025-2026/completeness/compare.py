import os,sys,time,pickle,csv,re,fitz
from collections import Counter,defaultdict
from decimal import Decimal
from sqlalchemy import create_engine,text
sys.path.insert(0,'.')
from extract import page_pairs
printed=pickle.load(open('printed.pkl','rb'))
for t in range(6):
    try:
        e=create_engine(os.environ["DATABASE_URL_UNPOOLED"].replace("postgresql://","postgresql+psycopg://",1))
        c=e.connect();c.execute(text('select 1'));break
    except Exception as ex:
        if 'resolve' in str(ex) and t<5: time.sleep(5);continue
        raise
rows=c.execute(text("""select d.original_filename f,r.source_page p,r.closing_rank rk,r.closing_percentile pc,r.id,r.college_course_id cc,r.seat_type_id st,r.stage_label sl,r.category_code_raw cat,r.source_document_id doc
from cutoff_records r join uploaded_documents d on d.id=r.source_document_id""")).fetchall()
print('stored rows',len(rows))
def key(rk,pc):
    return (rk, Decimal('0') if pc is None else Decimal(pc).quantize(Decimal('0.0000001')))
stored=defaultdict(Counter);fp=Counter()
nullnz=0
for r in rows:
    stored[(r.f,r.p)][key(r.rk,r.pc)]+=1;fp[r.f]+=1
files=sorted(printed)
print('db files',sorted(set(k[0] for k in stored)))
CITE=re.compile(r'^\d{4,5} - ')
miss=[];tot={};phantom=[];nopage=[]
zero_printed=0;zero_bad=[]
for f in files:
    d=fitz.open('/Users/vish/collegeFind/data/raw/'+f)
    P=ME=MU=PH=0;prt=0
    dbname=[k for k in set(x[0] for x in stored) if k.split('/')[-1]==f or f in k]
    for pi,pairs in enumerate(printed[f]):
        pg=pi+1
        pc=Counter(key(r,Decimal(p)) for r,p,_ in pairs)
        st=stored.get((f,pg),Counter())
        prt+=len(pairs)
        _,_,lines=page_pairs(d[pi])
        firstcol=next((i for i,(k,l) in enumerate(lines) if CITE.match(' '.join(w[4] for w in l[:3]))),None)
        # match as multiset
        rem=Counter(st)
        for r,p,li in pairs:
            kk=key(r,Decimal(p))
            if p=='0.0000000':zero_printed+=1
            if rem[kk]>0: rem[kk]-=1;continue
            ov = firstcol is None or li<firstcol
            miss.append((f,pg,r,p,'overflow-band' if ov else 'UNEXPLAINED'))
        for kk,n in rem.items():
            if n>0: phantom.append((f,pg,kk[0],str(kk[1]),n))
        # page coverage
        if pairs and not st:
            nopage.append((f,pg,len(pairs),'pure-overflow' if all((firstcol is None or li<firstcol) for _,_,li in pairs) else 'UNEXPLAINED'))
    tot[f]=prt
# stored pages beyond pdf / stored per file
for (f,pg),cn in stored.items():
    if f not in printed: print('stored file not in pdfs',f)
with open('missing_cells.csv','w',newline='') as o:
    w=csv.writer(o);w.writerow(['file','page','rank','percentile','class']);w.writerows(miss)
with open('phantom.csv','w',newline='') as o:
    w=csv.writer(o);w.writerow(['file','page','rank','pct','count']);w.writerows(phantom)
print('%-28s %7s %7s %6s %6s %6s'%('file','printed','stored','ovr','unexp','phant'))
for f in files:
    m=[x for x in miss if x[0]==f];print('%-28s %7d %7d %6d %6d %6d'%(f,tot[f],fp.get(f,0),sum(x[4]=='overflow-band' for x in m),sum(x[4]=='UNEXPLAINED' for x in m),sum(x[4] for x in [(0,)] ) if 0 else sum(y[4] for y in phantom if y[0]==f)))
print('total printed',sum(tot.values()),'missing',len(miss),'unexpl',sum(x[4]=='UNEXPLAINED' for x in miss),'phantom',sum(p[4] for p in phantom))
print('pages w/ pairs but no stored:',len(nopage),Counter(x[3] for x in nopage))
print('printed zero pcts',zero_printed)
# (d) nulls
print('null pct rows',c.execute(text("select count(*) from cutoff_records where closing_percentile is null")).scalar(),
 'zero pct rows',c.execute(text("select count(*) from cutoff_records where closing_percentile=0")).scalar())
print(c.execute(text("select d.original_filename,count(*) from cutoff_records r join uploaded_documents d on d.id=r.source_document_id where closing_percentile is null group by 1")).fetchall())
print('null rows with rank null',c.execute(text("select count(*) from cutoff_records where closing_percentile is null and closing_rank is null")).scalar())
# (e)
print('dup groups',c.execute(text("select count(*) from (select 1 from cutoff_records group by college_course_id,seat_type_id,stage_label,category_code_raw,source_document_id having count(*)>1) x")).scalar())
print('unique idx?',c.execute(text("select indexdef from pg_indexes where tablename='cutoff_records' and indexdef ilike '%unique%'")).fetchall())
print('pages with bad source_page', c.execute(text("select count(*) from cutoff_records where source_page is null or source_page<1")).scalar())
