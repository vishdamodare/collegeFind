import sys, collections, json
sys.path.insert(0, "data-engine")
from parsers.cet_cutoff import parse_pdf
r = parse_pdf(sys.argv[1])
print("cells", len(r.cells), "errors", len(r.errors))
print("colleges", len({c.institute_code for c in r.cells}), "courses", len({c.choice_code for c in r.cells}))
print("categories", len({c.category_code for c in r.cells}))
print("sections", collections.Counter(c.seat_type_code for c in r.cells))
print(collections.Counter(e[1] for e in r.errors).most_common(8))
print(r.errors[:8])
