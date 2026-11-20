import fitz,re,glob,json,os,sys
from collections import defaultdict
colre=re.compile(r'^(\d{4,5}) - (.+)$')
crsre=re.compile(r'^(\d{9,10}[A-Z]{0,3}) - (.+)$')
out={'cut':[], 'sm':[]}
for f in sorted(glob.glob('/Users/vish/collegeFind/data/raw/*.pdf')):
    b=os.path.basename(f); yr=int(b[:4]); sm='SeatMatrix' in b
    d=fitz.open(f)
    for pn,pg in enumerate(d,1):
        L=[l.strip() for l in pg.get_text().split('\n')]
        L=[l for l in L if l]
        for i,l in enumerate(L):
            if sm:
                m=colre.match(l)
                if m and not crsre.match(l):
                    out['sm'].append(dict(y=yr,p=pn,t='col',code=m.group(1).zfill(5),name=m.group(2),prev=L[i-1],next=L[i+1:i+3]))
                elif re.match(r'^\d{9,10}[A-Z]{0,3}$',l) and i+1<len(L) and i>0 and not re.match(r'^\d+$',L[i+1]) :
                    out['sm'].append(dict(y=yr,p=pn,t='crs',code=l,name=L[i+1]))
            else:
                m=colre.match(l)
                if m and not crsre.match(l) and len(m.group(1)) in(4,5) :
                    out['cut'].append(dict(y=yr,p=pn,t='col',code=m.group(1).zfill(5),name=m.group(2),next=L[i+1:i+2]))
                m=crsre.match(l)
                if m:
                    st=None
                    for j in range(i+1,min(i+6,len(L))):
                        if L[j].startswith('Status:'):
                            st=L[j+1:j+3];break
                    out['cut'].append(dict(y=yr,p=pn,t='crs',code=m.group(1),name=m.group(2),status=st))
json.dump(out,open('raw_extract.json','w'))
print(len(out['cut']),len(out['sm']))
