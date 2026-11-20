import os,json,time,collections,datetime
from sqlalchemy import create_engine,text
d=json.load(open('raw_extract.json'))
e=create_engine(os.environ['DATABASE_URL_UNPOOLED'].replace('postgresql://','postgresql+psycopg://',1))
for t in range(5):
    try:
        with e.begin() as c:
            db=c.execute(text("""select ci.id,ci.college_course_id,cc.choice_code,ci.academic_year_id,ay.label,si,ms_seats,minority_seats,all_india_seats,institute_seats,orphan_seats,published_date,source_page,source_document_id,ud.original_filename
              from course_intakes ci join college_courses cc on cc.id=ci.college_course_id join academic_years ay on ay.id=ci.academic_year_id join uploaded_documents ud on ud.id=ci.source_document_id""")).mappings().all()
            cut=c.execute(text("""select distinct cc.choice_code,ay.label from cutoff_records cr join college_courses cc on cc.id=cr.college_course_id join academic_years ay on ay.id=cr.academic_year_id""")).all()
        break
    except Exception as ex:
        print('retry',str(ex)[:60]);time.sleep(5)
rep={}
ymap={'2022-23':2022,'2023-24':2023,'2024-25':2024}
dbk={}
dups=0
for r in db:
    k=(ymap[r['label']],r['choice_code'])
    if k in dbk: dups+=1
    dbk[k]=r
pubexp={2022:datetime.date(2022,10,12),2023:datetime.date(2023,7,19),2024:datetime.date(2024,8,8)}
diffs=[];match=0;checked=0;arith=[];pdfkeys=collections.Counter();pdfonly=[];ndiff=collections.Counter()
seen=set()
for y in ('2022','2023','2024'):
    yy=int(y)
    for r in d[y]['rows']:
        code=r['code']; digits=''.join(ch for ch in code if ch.isdigit()); suf=code[len(digits):]
        code10=digits.zfill(10)+suf
        pdfkeys[(yy,code10)]+=1
        v=[n for _,n in r['nums']]
        k=(yy,code10)
        row=dbk.get(k)
        if not row: pdfonly.append((yy,code10,r['page']));continue
        checked+=1
        got=[row[x] for x in ('si','ms_seats','minority_seats','all_india_seats','institute_seats','orphan_seats')]
        bad=[]
        if got!=v: bad.append(('seats',v,got))
        if row['source_page']!=r['page']: bad.append(('page',r['page'],row['source_page']))
        if row['published_date']!=pubexp[yy]: bad.append(('pub',str(pubexp[yy]),str(row['published_date'])))
        if row['original_filename']!=f'{y}SeatMatrix.pdf': bad.append(('doc',row['original_filename']))
        if bad: diffs.append((yy,code10,r['page'],bad))
        else: match+=1
        if v[0]!=sum(v[1:5]): arith.append((yy,code10,r['page'],v))
dbonly=[k for k in dbk if k not in pdfkeys]
pdfdup=[(k,n) for k,n in pdfkeys.items() if n>1]
print('db rows',len(db),'dbdups',dups,'checked',checked,'match',match,'diffs',len(diffs),'pdfonly',len(pdfonly),'dbonly',len(dbonly),'pdfdup',len(pdfdup),'arith',len(arith))
print(diffs[:10]);print(pdfonly[:10]);print(dbonly[:10]);print(arith[:20])
print(collections.Counter(y for y,_,_,_ in arith), collections.Counter(b[0] for *_,bs in diffs for b in bs))
# cutoff cross-check
cs=collections.defaultdict(set)
for code,lab in cut: cs[ymap[lab]].add(code)
x={}
for yy in cs:
    mset={c for (y,c) in pdfkeys if y==yy}
    x[yy]=dict(cutoff_codes=len(cs[yy]),in_matrix=len(cs[yy]&mset),cutoff_not_in_matrix=sorted(cs[yy]-mset),matrix_not_in_cutoff=len(mset-cs[yy]))
    print(yy,{k:(v if not isinstance(v,list) else (len(v),v[:15])) for k,v in x[yy].items()})
json.dump(dict(diffs=diffs,pdfonly=pdfonly,dbonly=dbonly,arith=arith,cut=x,counts=dict(checked=checked,match=match)),open('compare_result.json','w'),default=str)
