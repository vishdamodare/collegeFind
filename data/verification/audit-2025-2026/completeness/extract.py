import fitz,re,sys,pickle,glob,os
from collections import defaultdict
INT=re.compile(r'^\d+$');BR=re.compile(r'^\((\d+\.\d+)\)$')
def page_pairs(page):
    ws=page.get_text('words')
    rows=defaultdict(list)
    for w in ws: rows[round((w[1]+w[3])/2/3)].append(w)   # ~3pt buckets
    # merge adjacent buckets
    ys=sorted(rows);lines=[]
    for k in ys:
        if lines and k-lines[-1][0]<=0 and False: pass
        lines.append((k,sorted(rows[k],key=lambda w:w[0])))
    pairs=[];mism=[];top=None
    for i,(k,l) in enumerate(lines):
        pc=[BR.match(w[4]).group(1) for w in l if BR.match(w[4])]
        if not pc: continue
        j=i-1
        while j>=0 and not any(INT.match(w[4]) for w in lines[j][1]): j-=1
        rk=[w[4] for w in lines[j][1] if INT.match(w[4])] if j>=0 else []
        # course/college code lines contain ints with '-' ; require line has no ' - '
        if len(rk)!=len(pc): mism.append((i,len(rk),len(pc)))
        for r,p in zip(rk,pc): pairs.append((int(r),p,j))
    return pairs,mism,lines
if __name__=='__main__':
    out={}
    for f in ['/Users/vish/collegeFind/data/raw/'+x for x in sys.argv[1:]]:
        d=fitz.open(f);n=os.path.basename(f);res=[];mm=0
        for pi,pg in enumerate(d):
            p,m,_=page_pairs(pg);res.append(p);mm+=len(m)
        out[n]=res;print(n,len(d),sum(map(len,res)),'mismatch lines',mm,flush=True)
    pickle.dump(out,open('printed.pkl','wb'))
