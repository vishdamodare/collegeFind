# Data verification (audit of 10 Nov 2026)

Seven independent, read-only checkers audited the database; evidence (scripts, reports, rendered pages) is in `data/verification/`.

| Check | Method | Result |
|---|---|---|
| Re-extraction | New PyMuPDF extractor written without access to our parser; cell-by-cell vs DB | 187,149 / 187,149 match; 0 DB-only, 0 PDF-only |
| Visual audit | 65 rendered PDF pages (all hard layouts) read by eye vs DB | 1,112 / 1,119 values; the 7 = a truncated category code (fixed) |
| Completeness | printed (rank, percentile) pairs vs stored, both directions | 187,415 printed; 266 missing = overflow gaps (recovered 24 Nov, see below); 0 phantom |
| Seat matrices | pdfplumber re-extraction vs `course_intakes` | 5,743 / 5,743 match; SI = MS+Minority+AI+Institute on all rows |
| Provenance | re-downloaded the 12 PDFs from the CET Cell; SHA-256; filing; 300 sampled citations | all identical / correct |
| API end-to-end | ≈89,700 checks of /meta, /cutoffs, /colleges, /trends, /predict vs SQL and hand-computed classification | 0 wrong |
| Entities | names, codes, ownership vs PDFs | 44 errors found → fixed (see below) |

## Fixes made because of the audit
`data-engine/fixes/apply_audit_fixes.py` (dry-run by default; each fix aborts unless the row count equals the audit's): 269 category codes restored (`PWDROBC`→`PWDROBCS`, `DEFRSEBC`→`DEFRSEBCS`, `PWDRSEBC`→`PWDRSEBCS`), 15 truncated course names completed, 4 Government-Aided colleges re-labelled `aided`, 21 college names updated to the latest printed name, 31 statuses and 255 home universities from the 2024 lists. Parser fixed (0.7.0): wrapped trailing letters are re-attached; importer ownership mapping fixed.
Regression: after the fixes a fresh parse equals the database exactly (`data-engine/verify_regression.py`).

## What "verified" means here
The stored values equal what the official PDFs print, shown by independent methods. It is **automated**, not a review by a CET Cell official or a human admin (`audit_logs.detail.human_review = false`).
**Held as preview:** 2022-23 Round 1 (title anomaly). **Open decision:** COEP is two colleges (06006, 16006).

## Overflow-band recovery (24 Nov 2026)
Very wide tables print their last columns on the next page with no course or stage label; that page is the right-hand strip of the wide page, so the band's header and value rows share their y-positions with the table's rows there. Parser 0.8.0 attributes a band only when exactly one table header and exactly one stage row match (±2.5 pt); otherwise it stays a reported gap. `data-engine/fixes/recover_overflow_cells.py` inserted the cells only after these gates: recovered set = the audit's `missing_cells.csv` exactly (266, by file/page/rank/percentile); every other cell unchanged; each recovered cell printed on a different page from the rest of its row; category suffix agrees with section. Visual check: 2022 R1 p.102–103, 2023 R1 p.1129–1130, 2024 R2 p.17–18. Regression after insert: **187,415 cells / 0 differences**. Marked verified (automated) except 2022 R1 (held). New category code: `PWDRVJS` (2023-24).

## Lessons from the audit itself
* A blanket correction ("append S to the truncated category codes") was wrong for Home University sections, whose wrapped letter is `H`. The post-fix **regression diff** (fresh parse vs database, `verify_regression.py`) caught it; 52 rows were corrected by the section-aware `fix_category_suffix.py`, then all 269 relabelled rows were re-checked against the letters printed in the PDFs (0 disagreements).
* Final gates before marking anything verified: regression 187,149 cells / **0 differences**; relabelled categories 269 / **0 disagreements**.

## Audit of 2025-26 and 2026-27 (24 Nov 2026)
Scope: CAP Rounds I–IV of both years (8 cut-off PDFs, 204,677 cells) and both seat matrices (4,488 courses). Evidence and scripts:
`data/verification/audit-2025-2026/` (the 10 Nov scripts, copied and pointed at the new files; the old evidence is untouched).

| Check | Method | Result |
|---|---|---|
| Provenance | re-downloaded all 10 PDFs from the CET Cell (fe2026.mahacet.org/2025/, cappublicdocs2026 blob); SHA-256 vs `uploaded_documents` | 10 / 10 identical |
| Re-extraction | independent PyMuPDF extractor (not the parser), cell by cell vs DB | 204,399 exact + 210 equal once the printed wrapped suffix letter is added + 68 overflow cells the extractor does not attribute = 204,677 / 204,677; **0 value differences, 0 unexplained** |
| Wrapped suffix | the 210 above: DB code = extractor code + section letter (HU seats → H, OHU seats → O, State → S), same rank, percentile and page | 210 / 210 |
| Completeness | every printed (rank, percentile) pair vs stored, both directions, per page | 204,677 printed = 204,677 stored; 0 missing, 0 phantom |
| Overflow cells | 68 cells printed on the next page with no course/category label; visual check of 2026 CAP3 p.1071–1072 and 2025 CAP1 p.1170–1171 | course, stage and category correct on all 10 cells viewed |
| Seat matrices | independent PyMuPDF word-position extraction vs `course_intakes`; SI = MS+Minority+AI+Institute | 2025: 2,181 / 2,181; 2026: 2,307 / 2,307 (incl. the 10 pages read via the PyMuPDF fallback); published dates as printed |
| Entities | new colleges, courses and category codes against the PDFs | see notes |
| API end-to-end | /meta, /cutoffs, /colleges, /trends, /predict vs SQL and hand-computed classification (8 new predictor cases for 2025/2026) | see `api/` |

Notes
* 20 new course names differ from the seat matrix: in every case the **seat matrix** truncates (its name is a prefix of the full name in the DB).
* 27 courses are in the cut-off lists but in neither seat matrix; all first appear in Round II or later (the matrices are the Round-I matrices).
* `PWDNT2S`, `PWDNT3S`, `DEFNT2S`, `DEFNT3S` (one cell each, 2026 CAP3 p.1071) are printed that way; stored as printed.
* "IImperial College of Engineering" (03726) is the 2026 PDFs' spelling (2025 prints "Imperial"); kept as the latest printed name.
* 16361 (Zeal, off-campus Induri) has no home university: the PDF prints State Level seats only.
* 13 rows in `branches` have no courses (truncated names from wrapped PDF lines; their courses carry the full name). The site never lists them.
* Bugs found and fixed: `mark_verified.py` missed the lower-case `2026_fe_seatmatrix_V1.pdf` (would have marked 0 rows yet published the job);
  `recover_overflow_cells.py` had the H/O suffix swapped for HU_TO_OHU / OHU_TO_HU (no effect: none of its 266 cells were in those sections).
