import json,fitz,re
sel=json.load(open("sample.json"))
for f,ps in sel.items():
  d=fitz.open("/Users/vish/collegeFind/data/raw/"+f)
  for p in ps:
    if p>=len(d): continue
    t=d[p].get_text()  # page p+1 (1-based)
    has=bool(re.search(r"^\d{4,5} - ",t,re.M))
    if not has: print(f[:4],f[12],"p",p,"-> next page",p+1,"has no college line; first text:",t[:60].replace("\n"," | "))
