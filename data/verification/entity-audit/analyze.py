import json,re
from collections import defaultdict,Counter
R=json.load(open('raw_extract.json'));D=json.load(open('db.json'))
cols={c['institute_code']:c for c in D['colleges']}
# colleges printed
pc=defaultdict(lambda:defaultdict(list)) # code->year->names
for r in R['cut']:
    if r['t']=='col': pc[r['code']][r['y']].append(('cut',r['name']))
for r in R['sm']:
    if r['t']=='col': pc[r['code']][r['y']].append(('sm',r['name']))
print('printed colleges',len(pc),'db',len(cols))
print('pdf-not-db',sorted(set(pc)-set(cols)));print('db-not-pdf',sorted(set(cols)-set(pc)))
# name variants within a year
def norm(s):return re.sub(r'\s+',' ',s).strip()
intra=0
for c,ys in pc.items():
    for y,l in ys.items():
        if len({norm(n) for _,n in l})>1: intra+=1; 
        if len({norm(n) for _,n in l})>1 and intra<8: print('INTRA',c,y,Counter(n for _,n in l).most_common(4))
print('intra-year variance',intra)
# weird names (trailing continuation?)
print('-----')
def nm(s):return norm(s.replace('¶','’'))
def key(s):return re.sub(r'[^a-z0-9]','',s.lower())
for c,ys in pc.items():
    for y,l in ys.items():
        if len({nm(n) for _,n in l})>1: print('INTRA2',c,y,Counter((s,n) for s,n in l))
# latest-year name (cut lists)
latest_diff=[];yeardiff=[];exact=0
for c,ys in sorted(pc.items()):
    names={y:Counter(nm(n) for s,n in l if s=='cut').most_common(1)[0][0] for y,l in ys.items() if any(s=='cut' for s,_ in l)}
    ly=max(names);ln=names[ly];db=norm(cols[c]['name'])
    if len(set(names.values()))>1: yeardiff.append((c,names))
    if db!=ln: latest_diff.append((c,db,ln,ly,names))
print('colleges w/ name variance across years (cut lists):',len(yeardiff))
print('db name != latest-year printed:',len(latest_diff))
import difflib
def sim(a,b):return difflib.SequenceMatcher(None,a.lower(),b.lower()).ratio()
rows=[]
for c,names in yeardiff:
    ys=sorted(names);db=norm(cols[c]['name'])
    rows.append((sim(names[ys[0]],names[ys[-1]]),c,db,names))
rows.sort()
json.dump(dict(yeardiff=[(c,n) for c,n in yeardiff],latest_diff=latest_diff),open('names.json','w'),indent=1)
for s,c,db,n in rows[:15]:
    print(round(s,2),c,'DB=',db);[print('   ',y,v) for y,v in sorted(n.items())]
print('only-case/punct diffs:',sum(1 for c,n in yeardiff if len({key(v) for v in n.values()})==1))
