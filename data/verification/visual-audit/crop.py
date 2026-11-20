import json,fitz,os
sel=json.load(open("sample.json")); os.makedirs("crops",exist_ok=True)
info={}
for f,ps in sel.items():
  doc=fitz.open("/Users/vish/collegeFind/data/raw/"+f)
  for p in ps:
    pg=doc[p-1]; tag=f[:4]+"R"+f[12]+f"_p{p}"
    ws=[w for w in pg.get_text("words") if 80<w[1]<pg.rect.height-60 and w[1]<pg.rect.height*0.93]
    ys=[w[3] for w in ws if not w[4].startswith("Cut")] 
    # drop footer note line
    if not ws: print(tag,"NO WORDS"); continue
    y0=max(80,min(w[1] for w in ws)-4); y1=max(w[3] for w in ws)+4
    x1=max(w[2] for w in ws)+6
    x1=min(x1,pg.rect.width)
    parts=[(0,x1)] if x1<=950 else [(0,x1/2+60),(x1/2-60,x1)]
    n=0
    for i,(a,b) in enumerate(parts):
      pg.get_pixmap(matrix=fitz.Matrix(2,2),clip=fitz.Rect(a,y0,b,y1)).save(f"crops/{tag}_{i}.png")
    print(tag,len(parts),int(x1),int(y1-y0))
