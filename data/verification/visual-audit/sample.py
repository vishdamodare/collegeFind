import os,random,fitz,json
random.seed(20241110)
sel={}
for y in (2022,2023,2024):
  for r in (1,2,3):
    f=f"{y}ENGG_CAP{r}_CutOff.pdf"
    n=len(fitz.open("/Users/vish/collegeFind/data/raw/"+f))
    k=n//6
    sel[f]=[random.randint(i*k+1,(i+1)*k) for i in range(6)]
    print(f,n)
hard={"2022ENGG_CAP1_CutOff.pdf":[388,389],"2022ENGG_CAP3_CutOff.pdf":[40],"2023ENGG_CAP3_CutOff.pdf":[292],"2024ENGG_CAP3_CutOff.pdf":[1096],"2024ENGG_CAP1_CutOff.pdf":[266,542,301],"2024ENGG_CAP2_CutOff.pdf":[205,206],"2023ENGG_CAP1_CutOff.pdf":[301]}
for f,p in hard.items(): sel[f]=sorted(set(sel[f]+p))
json.dump(sel,open("sample.json","w"))
print(sel, sum(len(v) for v in sel.values()))
