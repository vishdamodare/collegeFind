import pdfplumber,re,json,sys
out={}
for y in (2022,2023,2024):
    pdf=pdfplumber.open(f'/Users/vish/collegeFind/data/raw/{y}SeatMatrix.pdf')
    rows=[];anom=[];pub=None
    for i,pg in enumerate(pdf.pages,1):
        ws=pg.extract_words()
        if i==1:
            for k,w in enumerate(ws):
                if w['text']=='Published': pub=[x['text'] for x in ws[k:k+5]]
        cc=[w for w in ws if re.fullmatch(r'\d{9,10}[A-Z]{0,3}',w['text']) and w['x0']<130]
        hdr=[w for w in ws if w['text']=='Orphan']
        if len(cc)<1 or not hdr: anom.append((i,'nocode',len(cc)));continue
        hy=hdr[0]['top']
        cc=[w for w in cc if w['top']>hy]
        if not cc: anom.append((i,'nocode2'));continue
        c=cc[0]
        line=[w for w in ws if abs(w['top']-c['top'])<3 and w['x0']>340 and re.fullmatch(r'\d+',w['text'])]
        # header x centers
        def cx(names):
            return None
        rows.append(dict(page=i,code=c['text'],nums=[(round(w['x0']),int(w['text'])) for w in line],ncc=len(cc),
          name=' '.join(w['text'] for w in ws if abs(w['top']-c['top'])<3 and 130<w['x0']<340)))
    out[y]=dict(rows=rows,anom=anom,pub=pub,pages=len(pdf.pages))
    print(y,len(pdf.pages),len(rows),anom[:5],pub)
json.dump(out,open('/Users/vish/collegeFind/data/verification/seat-matrix-audit/raw_extract.json','w'))
