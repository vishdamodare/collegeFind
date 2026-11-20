# Data verification (audit of 10 Nov 2026)

Seven independent, read-only checkers audited the database; evidence (scripts, reports, rendered pages) is in `data/verification/`.

| Check | Method | Result |
|---|---|---|
| Re-extraction | New PyMuPDF extractor written without access to our parser; cell-by-cell vs DB | 187,149 / 187,149 match; 0 DB-only, 0 PDF-only |
| Visual audit | 65 rendered PDF pages (all hard layouts) read by eye vs DB | 1,112 / 1,119 values; the 7 = a truncated category code (fixed) |
| Completeness | printed (rank, percentile) pairs vs stored, both directions | 187,415 printed; 266 missing = documented overflow gaps; 0 phantom |
| Seat matrices | pdfplumber re-extraction vs `course_intakes` | 5,743 / 5,743 match; SI = MS+Minority+AI+Institute on all rows |
| Provenance | re-downloaded the 12 PDFs from the CET Cell; SHA-256; filing; 300 sampled citations | all identical / correct |
| API end-to-end | ≈89,700 checks of /meta, /cutoffs, /colleges, /trends, /predict vs SQL and hand-computed classification | 0 wrong |
| Entities | names, codes, ownership vs PDFs | 44 errors found → fixed (see below) |

## Fixes made because of the audit
`data-engine/fixes/apply_audit_fixes.py` (dry-run by default; each fix aborts unless the row count equals the audit's): 269 category codes restored (`PWDROBC`→`PWDROBCS`, `DEFRSEBC`→`DEFRSEBCS`, `PWDRSEBC`→`PWDRSEBCS`), 15 truncated course names completed, 4 Government-Aided colleges re-labelled `aided`, 21 college names updated to the latest printed name, 31 statuses and 255 home universities from the 2024 lists. Parser fixed (0.7.0): wrapped trailing letters are re-attached; importer ownership mapping fixed.
Regression: after the fixes a fresh parse equals the database exactly (`data-engine/verify_regression.py`).

## What "verified" means here
The stored values equal what the official PDFs print, shown by independent methods. It is **automated**, not a review by a CET Cell official or a human admin (`audit_logs.detail.human_review = false`).
**Held as preview:** 2022-23 Round 1 (title anomaly). **Not stored:** ≈266 overflow-band cells (listed in `data/verification/completeness-audit/`). **Open decision:** COEP is two colleges (06006, 16006).

## Lessons from the audit itself
* A blanket correction ("append S to the truncated category codes") was wrong for Home University sections, whose wrapped letter is `H`. The post-fix **regression diff** (fresh parse vs database, `verify_regression.py`) caught it; 52 rows were corrected by the section-aware `fix_category_suffix.py`, then all 269 relabelled rows were re-checked against the letters printed in the PDFs (0 disagreements).
* Final gates before marking anything verified: regression 187,149 cells / **0 differences**; relabelled categories 269 / **0 disagreements**.
