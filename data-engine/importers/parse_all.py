"""Parse PDFs in parallel and cache results (data/parsed/*.pkl) so imports are quick and sequential.
Usage: python data-engine/importers/parse_all.py data/raw/*.pdf
"""
import os, pickle, sys
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from parsers.cet_cutoff import PARSER_VERSION, parse_pdf


def one(path):
    res = parse_pdf(path)
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(path))), "parsed")
    os.makedirs(out, exist_ok=True)
    pickle.dump((PARSER_VERSION, res), open(os.path.join(out, os.path.basename(path) + ".pkl"), "wb"))
    return os.path.basename(path), len(res.cells), len(res.errors)


if __name__ == "__main__":
    with Pool(4) as p:
        for name, cells, errs in p.imap_unordered(one, sys.argv[1:]):
            print(f"{name}: cells={cells} errors={errs}", flush=True)
