import fitz,re,glob,json,os
crsre=re.compile(r'^(\d{9,10}[A-Z]{0,3}) - (.+)$')
colre=re.compile(r'^(\d{4,5}) - (.+)$')
out=[]
for f in sorted(glob.glob('/Users/vish/collegeFind/data/raw/*.pdf')):
    b=os.path.basename(f); yr=int(b[:4]); sm='SeatMatrix' in b
    for pn,pg in enumerate(fitz.open(f),1):
        L=[l.strip() for l in pg.get_text().split('\n') if l.strip()]
        for i,l in enumerate(L):
            if sm:
                if re.match(r'^\d{9,10}[A-Z]{0,3}$',l) and i>0 and not l==L[i-1] and i+1<len(L) and not L[i+1].isdigit() and L[i-1] in('Course Name','Choice Code','Orphan','Seats','Institute','Institute Seats') or (re.match(r'^\d{9,10}[A-Z]{0,3}$',l) and 'Choice Code' in L[max(0,i-9):i]):
                    j=i+1;nm=[]
                    while j<len(L) and not L[j].isdigit(): nm.append(L[j]);j+=1
                    out.append(dict(y=yr,p=pn,src='sm',code=l,name=' '.join(nm)))
            else:
                m=crsre.match(l)
                if m:
                    j=i+1;nm=[m.group(2)]
                    while j<len(L) and not L[j].startswith('Status:') and j<i+4: nm.append(L[j]);j+=1
                    out.append(dict(y=yr,p=pn,src='cut',code=m.group(1),name=' '.join(nm) if j<len(L) and L[j].startswith('Status:') else m.group(2),raw1=m.group(2)))
json.dump(out,open('courses2.json','w'));print(len(out),sum(o['src']=='sm' for o in out))
