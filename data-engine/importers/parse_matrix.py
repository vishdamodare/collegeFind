"""Parse seat-matrix PDFs in parallel and pickle results into data/parsed/. Usage: parse_matrix.py FILE.pdf ..."""
import os, pickle, sys
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from parsers.cet_seat_matrix import PARSER_VERSION, parse_matrix_pdf


def one(path):
    res = parse_matrix_pdf(path)
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(path))), "parsed")
    os.makedirs(out, exist_ok=True)
    pickle.dump((PARSER_VERSION, res), open(os.path.join(out, os.path.basename(path) + ".pkl"), "wb"))
    return os.path.basename(path), len(res.rows), len(res.errors), res.year_label, res.published


if __name__ == "__main__":
    with Pool(3) as p:
        for r in p.imap_unordered(one, sys.argv[1:]):
            print("%s: rows=%d errors=%d year=%s published=%s" % r, flush=True)
