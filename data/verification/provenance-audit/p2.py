import fitz,glob,os,json
pc={}
for f in sorted(glob.glob('/Users/vish/collegeFind/data/raw/*.pdf')):
    d=fitz.open(f); n=os.path.basename(f); pc[n]=len(d)
    print("=====",n,len(d)); print(d[0].get_text()[:700].replace("\n"," | "))
json.dump(pc,open('pagecounts.json','w'))
