import pdfplumber,json,re,random,collections
d=json.load(open('raw_extract.json'))
random.seed(7)
res=[];stats=collections.defaultdict(collections.Counter);ex=collections.defaultdict(list)
for y in ('2022','2023','2024'):
    rows=d[y]['rows']
    samp=sorted(random.sample(range(len(rows)),220))
    p=pdfplumber.open(f'/Users/vish/collegeFind/data/raw/{y}SeatMatrix.pdf')
    for i in samp:
        r=rows[i];v=[n for _,n in r['nums']];si,ms,mi,ai,ins,orph=v
        t=p.pages[i].extract_text().split('\n')
        T=0;rowsum_ok=True;secs=0
        for ln in t:
            m=re.match(r'^(State Level|HU|OHU)\s+([\d ]+)$',ln)
            if m:
                nums=[int(x) for x in m.group(2).split()]
                T+=nums[-1];secs+=1
                if sum(nums[:-1])!=nums[-1]: rowsum_ok=False
        s=' '.join(t)
        m=re.search(r'\(EWS\) Seats:\s*(\d+)',s);ews=int(m.group(1)) if m else None
        m=re.search(r'Choice Code:\s*(\w*)\s*:?\s*Seats:\s*(\d+)',s);tf=int(m.group(2)) if m else None
        tfc=m.group(1) if m else None
        m=re.search(r'CAP Seats:\s*(\d+)',s);cap=int(m.group(1)) if m else None
        st=stats[y];st['n']+=1
        if secs==0: st['no_section_rows']+=1;continue
        st['rowsum_ok']+=rowsum_ok
        st['cap_seats==SI']+=(cap==si)
        e=(ews or 0)
        h={'MS==T':ms==T,'MS==T+EWS':ms==T+e,'MS==T+EWS-orphan':ms==T+e-orph,'SI-AI-Min-Inst==T+EWS':ms==T+e}
        for k,b in h.items(): st[k]+=b
        st['ews_present']+=ews is not None
        st['tfws_present']+=tf is not None
        st['tfws_code_matches_choice']+=(tfc==r['code'][:-1]+'1T' or tfc==r['code'][:-1]+'1'+'T'); st['tfws_code_blank']+=(tfc=='')
        res.append((y,r['page'],ms,T,e,tf,orph,ai,mi,ins))
        if not h['MS==T+EWS'] and len(ex[y])<6: ex[y].append((r['page'],r['code'],v,T,ews,tf))
        # which of the two ties
        st['MS==T+EWS or -orph']+= (h['MS==T+EWS'] or h['MS==T+EWS-orphan'])
for y in stats: print(y,dict(stats[y]));print(' ex',ex[y])
import collections as C
for y in ('2022','2023','2024'):
    c=C.Counter(((ms-T)-(e),tf,orph) for yy,pg,ms,T,e,tf,orph,ai,mi,ins in res if yy==y);print(y,'resid-EWS,tfws,orph',c.most_common(8))
    c=C.Counter((ms-T-e-tf+orph) for yy,pg,ms,T,e,tf,orph,ai,mi,ins in res if yy==y);print(' ms-T-ews-tfws+orph',c.most_common(6))
json.dump({y:dict(stats[y]) for y in stats},open('tables_result.json','w'))
