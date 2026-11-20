import json,re
from collections import defaultdict,Counter
D=json.load(open('db.json'));O=json.load(open('courses2.json'))
byid={c['id']:c for c in D['colleges']}
def nc(c):
    m=re.match(r'^(\d+)([A-Z]*)$',c);return m.group(1).zfill(10)+m.group(2)
def nm(s):return re.sub(r'\s+',' ',s.replace('¶','’')).strip()
cc={c['choice_code']:c for c in D['cc']}
cn=defaultdict(lambda:defaultdict(Counter))
for o in O: cn[nc(o['code'])][(o['src'],o['y'])][nm(o['name'])]+=1
print('codes',len(cn),'eq db',set(cn)==set(cc))
blank=[o for o in O if not o['name']];print('blank names',len(blank))
res=dict(dbwrong=[],ren=[],smcut=[],intra=[])
for c,d in cn.items():
    per={k:v.most_common(1)[0][0] for k,v in d.items()}
    for k,v in d.items():
        if len(v)>1: res['intra'].append((c,k,dict(v)))
    if len(set(per.values()))>1: res['ren'].append((c,{f'{a}{y}':n for (a,y),n in sorted(per.items())}))
    cut={k:v for k,v in per.items() if k[0]=='cut'}
    ly=max(k[1] for k in cut);ln=per[('cut',ly)]
    if nm(cc[c]['name_raw'])!=ln: res['dbwrong'].append((c,cc[c]['name_raw'],ln,ly))
    for y in (2022,2023,2024):
        if ('cut',y) in per and ('sm',y) in per and per[('cut',y)]!=per[('sm',y)]: res['smcut'].append((c,y,per[('cut',y)],per[('sm',y)]))
for k,v in res.items():
    print(k,len(v))
    for x in v[:12]:print('  ',x)
json.dump(res,open('course_names.json','w'),indent=1)
# classify ren: case/space/punct only vs substantive
def key(s):return re.sub(r'[^a-z0-9]','',s.lower())
sub=[(c,n) for c,n in res['ren'] if len({key(v) for v in n.values()})>1];print('substantive renames',len(sub))
for x in sub[:25]:print('  ',x)
# same name dup
dd=defaultdict(list)
for k,v in cc.items(): dd[(v['college_id'],v['name_raw'])].append(k)
print([ (byid[a]['institute_code'],n,ks) for (a,n),ks in dd.items() if len(ks)>1][:20])
