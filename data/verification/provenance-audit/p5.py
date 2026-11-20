import fitz,re,collections
for y in (2022,2023,2024):
    d=fitz.open(f'/Users/vish/collegeFind/data/raw/{y}SeatMatrix.pdf'); c=collections.Counter(); npg=0
    for pg in d:
        for m in re.findall(r"Published Date\s*:\s*([0-9/ ]+)",pg.get_text()): c[m.strip()]+=1
    print(y,len(d),c.most_common(5))
