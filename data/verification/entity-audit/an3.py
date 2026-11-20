import json,re
from collections import defaultdict,Counter
R=json.load(open('raw_extract.json'));D=json.load(open('db.json'))
cols={c['institute_code']:c for c in D['colleges']}; byid={c['id']:c for c in D['colleges']}
def nc(c):
    m=re.match(r'^(\d+)([A-Z]*)$',c);return m.group(1).zfill(10)+m.group(2)
def nm(s):return re.sub(r'\s+',' ',s.replace('¶','’')).strip()
def sp(s):
    m=re.match(r'^(.*?)\s*Home University\s*:\s*(.*)$',s);return (m.group(1).strip(),m.group(2).strip()) if m else (s.strip(),None)
cn=defaultdict(lambda:defaultdict(Counter))  # code->(src,year)->names
stc=defaultdict(lambda:defaultdict(Counter));unic=defaultdict(lambda:defaultdict(Counter))
for r in R['cut']:
    if r['t']=='crs':
        c=nc(r['code']);cn[c][('cut',r['y'])][nm(r['name'])]+=1
        if r['status']:
            a,u=sp(r['status'][0]);stc[c[:5]][r['y']][a]+=1;unic[c[:5]][r['y']][u]+=1
for r in R['sm']:
    if r['t']=='crs': cn[nc(r['code'])][('sm',r['y'])][nm(r['name'])]+=1
cc={c['choice_code']:c for c in D['cc']}
P=set(cn);S=set(cc)
print('printed',len(P),'db',len(S),'pdf-not-db',sorted(P-S)[:20],len(P-S),'db-not-pdf',sorted(S-P)[:20],len(S-P))
# prefix
bp=[k for k,v in cc.items() if k[:5]!=byid[v['college_id']]['institute_code']];print('prefix mismatch',len(bp))
# cut-only / sm-only
cutset={c for c in P if any(k[0]=='cut' for k in cn[c])};smset={c for c in P if any(k[0]=='sm' for k in cn[c])}
print('in cut',len(cutset),'in sm',len(smset),'cut-not-sm',len(cutset-smset),'sm-not-cut',len(smset-cutset))
print('sm-not-cut sample',sorted(smset-cutset)[:10]); print('cut-not-sm sample',sorted(cutset-smset)[:10])
# names
dbwrong=[];ren=[];sm_vs_cut=[]
for c,d in cn.items():
    allnames=Counter()
    for k,v in d.items():allnames.update(v)
    per={k:v.most_common(1)[0][0] for k,v in d.items()}
    if len(set(per.values()))>1: ren.append((c,per))
    cuts={k:v for k,v in per.items() if k[0]=='cut'}
    if cuts:
        ly=max(k[1] for k in cuts);ln=per[('cut',ly)]
    else: ly=max(k[1] for k in per);ln=per[('sm',ly)]
    if c in cc and nm(cc[c]['name_raw'])!=ln: dbwrong.append((c,cc[c]['name_raw'],ln,ly))
    if any(k[0]=='cut' for k in per) and any(k[0]=='sm' for k in per):
        for y in (2022,2023,2024):
            if ('cut',y) in per and ('sm',y) in per and per[('cut',y)]!=per[('sm',y)]: sm_vs_cut.append((c,y,per[('cut',y)],per[('sm',y)]))
print('courses with name variance:',len(ren),'db!=latest',len(dbwrong),'sm vs cut same-year diffs',len(sm_vs_cut))
for x in dbwrong[:12]:print(x)
for x in sm_vs_cut[:15]:print(x)
# multiple names within same src/year
intra=[(c,k,dict(v)) for c,d in cn.items() for k,v in d.items() if len(v)>1];print('intra-source variance',len(intra),intra[:5])
# courses without data
cutc=set(D['cut_cc']);print('db courses without cutoff rows',len([k for k,v in cc.items() if v['id'] not in cutc]),'without intake rows',len([k for k,v in cc.items() if v['id'] not in set(D['int_cc'])]))
print('colleges w/o cutoff rows',len([c for c in D['colleges'] if c['id'] not in set(D['cut_col'])]),'w/o courses',len(set(c['id'] for c in D['colleges'])-set(v['college_id'] for v in cc.values())))
# dup
slugs=Counter(c['slug'] for c in D['colleges']);print('dup slugs',[s for s,n in slugs.items() if n>1])
nn=defaultdict(list)
for c in D['colleges']: nn[re.sub(r'[^a-z0-9]','',c['normalized_name'])].append(c['institute_code'])
print('dup normalized',{k:v for k,v in nn.items() if len(v)>1})
nn2=Counter(c['normalized_name'] for c in D['colleges']);print('exact dup normalized_name',[k for k,v in nn2.items() if v>1])
# cc name dup within college
dd=Counter((v['college_id'],v['name_raw']) for v in cc.values());print('same college same name courses',sum(1 for x in dd.values() if x>1))
json.dump(dict(ren=ren,dbwrong=dbwrong,sm_vs_cut=sm_vs_cut),open('course_names.json','w'),indent=1)
# status per course vs college
print('colleges w/ multiple statuses within one year:')
for c,ys in stc.items():
    for y,v in ys.items():
        if len(v)>1:print(c,y,dict(v),'DB',cols[c]['status_raw'],cols[c]['ownership'])
print('colleges with status data',len(stc), 'not in db',[c for c in stc if c not in cols])
# university check
ub=[];um=0
for c,col in cols.items():
    ys=unic.get(c,{});
    if not ys: continue
    ly=max(ys);u=[x for x in ys[ly] if x]
    if u and col['university'] is None: um+=1
    if u and col['university'] and col['university'] not in u: ub.append((c,col['university'],u))
print('univ printed (latest yr) but DB null',um,'DB univ differs from printed',ub[:10],len(ub))
