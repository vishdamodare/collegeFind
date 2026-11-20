# Known limitations (updated after the 10 Nov 2026 multi-agent audit; see docs/verification.md)

## Data that is NOT in the database
* **Overflow columns: 86 stage-rows, ≈266 cells (0.14% of 187,149) are missing.** Very wide CET Cell tables print their last
  few columns (usually `DEF*`, `PWD*`, `ORPHAN`, `EWS`) at the top of the *next page*, with no course name or stage label.
  With several wide tables on one page they cannot be attributed safely, so they are **not stored**; each one is recorded as an
  `import_validation_errors` row (page + raw values). Affected files: 2022 R1 (16 rows), 2023 R1 (32), 2023 R2 (1), 2024 R1 (24), 2024 R2 (13).
  Shown on the site as "Data not available". Fix = a geometry-aware parser or a manual pass.
* **Only Maharashtra & Minority seat lists** are imported. All-India lists (`*_AI_CutOff.pdf`) are JEE-based and need their own
  parser/exam mapping; JEE Main and NEET UG are not implemented.
* **No official source loaded yet for:** college address/district, fees, placements, NIRF rank, hostel, AICTE approval. The site says "Data not available".
* **Round 4 / additional rounds and the 2025–2026 lists are not imported** (the portal publishes them; the parser handles the same layouts but they were not requested).

## Data quality caveats
* **Verification status.** 165,859 cutoff records (2022-23 R2–R3, 2023-24 R1–R3, 2024-25 R1–R3) and all 5,743 seat-matrix rows are `verified`: they matched an independent re-extraction, a visual audit, a completeness check and a source-file hash check (`data/verification/`, `audit_logs`). **This is automated verification, not review by a CET Cell official or a human admin** (`human_review=false`). **2022-23 Round 1 (21,290 records) stays `pending`/"preview"** until the CET Cell title anomaly is confirmed. No admin approval UI exists yet.
* **Open decision: COEP is two colleges** (06006 for 2022-23, 16006 for 2024-25 — the CET Cell re-coded it). Merging them would join the history but is an interpretation; not done.
* **Status/university are per college, but printed per course** (a few colleges mix e.g. Government-Aided and Un-Aided courses). The database keeps one value per college.
* **Seat-matrix quirks:** the 2023 matrix prints two dates ("19/07/2023" then "20/07/2023"; we store the first); 17 courses in the 2024 cutoff lists have no matrix row (added after the provisional matrix).
* **2022 CAP Round I file is mis-titled by the CET Cell** ("All India Seats") but is the Maharashtra list: it has Home University
  sections and sits on the same scale as 2022 R2. Imported with a recorded override; confirm with the CET Cell before verifying.
* **TFWS percentile:** the CET Cell prints `(0.0000000)` for 26 TFWS cells in the 2024 lists. These are stored as *no percentile* (NULL), rank kept; never compared.
* **Rank scales differ between categories in 2024.** For 2022–2023, every main category is perfectly monotone (rank ↑ ⇒ percentile ↓; 84,261 records, 0 exceptions). In the 2024 lists ~1% of main-category pairs are not
  monotone against each other although each (rank, percentile) pair **is printed together** in the PDF (verified for 100% of records). This is how the source prints, not an extraction error — but it means rank is not a single comparable scale in 2024. The predictor uses percentile only.
* **Category codes** (e.g. `GOPENS`) are stored as printed; not decoded to plain names (no official legend loaded). Codes whose last letter wraps onto a second line in the PDF header (`PWDROBC` + `S`/`H`) are restored using the seat-level suffix of their section (S = State Level, H = Home University, O = Other than Home); checked against the PDFs for all 269 affected rows.
* **Seat-matrix columns:** "SI" is the printed header; arithmetic shows SI = MS + Minority + All India + Institute seats in 100% of 5,743 courses, so the UI labels it "Intake (SI)". The matrices are the *provisional Round-I* matrices; their publication dates are stored.
* If a college/branch is renamed between years the first-seen name is kept. Local copy of PDFs is in `data/raw` (git-ignored); reuse/licensing terms of the CET Cell PDFs have **not** been reviewed — launch blocker.

## How the data was checked
1. Parser fixtures with hand-transcribed values from real pages (20 tests).
2. Row counts: Neon (187,149) = parsed (187,149); seat-matrix rows = PDF page counts (1,788 / 1,900 / 2,055).
3. DB constraints: no metric-less rows, percentile 0–100, rank > 0, unique cells; 0 violations.
4. Random spot-check: 80/80 records found on their cited PDF page (PyMuPDF, independent of the parser).
5. **Pairing check (`data-engine/verify_pairing.py`): 187,149/187,149 (rank, percentile) pairs are printed together** on the cited page, paired by order only (no x-coordinates).
6. Not independently verified: *which category column* a pair belongs to (relies on x-position geometry; corroborated by the 2022–2023 monotonic check and hand-checked pages).

## Environment / platform
* Python 3.9 only on the dev machine; no Docker; Redis/Celery/S3 not set up (local file storage for PDFs).
* Auth, admin dashboard, comparison and CAP-preference builder: schema only.
* Local Neon access from this machine sometimes fails DNS for the *pooled* hostname (router resolver); the database itself is fine.
