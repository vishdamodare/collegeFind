import json,re
from collections import defaultdict,Counter
R=json.load(open('raw_extract.json'));D=json.load(open('db.json'))
cols={c['institute_code']:c for c in D['colleges']}
byid={c['id']:c for c in D['colleges']}
# college of each course in cut: track by page sequence -- use code[:5]
st=defaultdict(lambda:defaultdict(Counter))  # code->year->status text
for r in R['cut']:
    if r['t']=='crs' and r['status']:
        st[r['code'][:5] if len(r['code'])==10 else r['code'].zfill(10)[:5]][r['y']][r['status'][0]]+=1
# status line forms
forms=Counter()
for c,ys in st.items():
    for y,cn in ys.items():
        for s in cn: forms[(y,s)]+=cn[s]
# strip university
def split(s):
    m=re.match(r'^(.*?)\s*Home University\s*:\s*(.*)$',s)
    return (m.group(1).strip(),m.group(2).strip()) if m else (s.strip(),None)
res=defaultdict(set);uni=defaultdict(set)
for c,ys in st.items():
    for y,cn in ys.items():
        for s in cn:
            a,u=split(s);res[c].add((y,a));uni[c].add((y,u))
bad=[];multi=[]
for c,col in cols.items():
    allst={a for y,a in res[c]}
    latest=max(res[c])[1] if res[c] else None
    if len(allst)>1: multi.append((c,sorted(res[c])))
    if col['status_raw'] not in allst: bad.append((c,col['status_raw'],sorted(res[c])))
print('colleges w/ status in cut lists',len(res),'; db status not among any printed:',len(bad));print(bad[:10])
print('status changes across years:',len(multi))
for m in multi[:30]:print(m, 'DB:',cols[m[0]]['status_raw'])
# DB status vs latest-year status
ld=[(c,cols[c]['status_raw'],max(res[c])) for c in cols if res[c] and cols[c]['status_raw']!=max(res[c])[1]]
print('db status != latest printed',len(ld),ld[:20])
print('university in DB non-null:',sum(1 for c in cols.values() if c['university']), Counter(c['university'] for c in cols.values()).most_common(5))
print('printed uni 2024 values',Counter(u for c in uni.values() for y,u in c if y==2024).most_common(12))
print('status forms 2024 sample',[k for k in forms if k[0]==2024][:15])
# ownership mapping
mp=defaultdict(set)
for c in cols.values(): mp[c['status_raw']].add(c['ownership'])
print(dict(mp))
