# Development progress

## Phase 1 – foundation (2026-11-10) – done, with limits
* Repo was empty. Structure created per spec.
* 31-table schema as SQLAlchemy models + Alembic `0001` (upgrade/downgrade/upgrade verified on local Postgres 18).
* Idempotent seed (exams, authorities, seat types, years, sources, course).
* FastAPI app: `/health`, `/api/v1/exams`. Engineering percentile comparator with insufficient-data handling; NEET refused.
* CET cutoff PDF parser (position-aligned) + fixture tests; full 2024 R1 dry run (no DB write).
* Next.js + Tailwind scaffold with brand palette; builds.
* Docs: architecture, database-schema, data-sources, prediction-logic, registry, limitations.

## Next: Phase 2
Importer (store PDF + sha256 → import_job → pending cutoff_records), category/college/course upsert, validation report, admin approve/rollback, import 2024 R1 and spot-check ≥50 random cells against the PDF.

## Phase 2–3 (2026-11-10) – data import and student site (done, with limits in KNOWN_LIMITATIONS.md)
* Parsers: CET cut-off lists (position-aligned text grid, parser 0.6.0) and seat matrices (0.2.0). Handles 2022/2023/2024 layouts, two-line stage labels, page continuations, the minority and "MH seats for All-India candidates" sections, TFWS zeros; reports (never guesses) unrecognised rows and overflow columns.
* Importers: idempotent per document (sha256), header cross-check (year/round/scope), get-or-create colleges/branches/courses, everything inserted as `pending`.
* **Neon (Postgres 18, ap-southeast-1)**: 32 tables (migrations 0001–0003). Loaded: 187,149 cutoff records (2022-23, 2023-24, 2024-25 × CAP rounds 1–3), 361 colleges, 2,187 college-courses, 5,743 seat-matrix rows.
* API: `/meta`, `/colleges`, `/colleges/{slug}`, `/cutoffs`, `/trends`, `/trend-options`, `/predict` (grouped, with history). `/meta` cached 60 s.
* Site (Next.js 16): home, college search, college profile (intake + trend chart), cutoff explorer, predictor. New brand mark and design system.
* Verification: see "How the data was checked" in KNOWN_LIMITATIONS.md.

## Next
Admin verification UI + approve/publish, auth, compare + CAP preference builder, All-India/JEE lists, NEET, fees/address/NIRF sources, Round 4 and 2025–26, geometry-aware overflow parser, deploy API in Singapore next to the DB.

## Verification (2026-11-10)
Seven independent read-only audits (workflow `verify-all-data`) + fixes + regression gate; 165,859 cutoff records and 5,743 intake rows marked verified (automated); 2022-23 R1 held as preview. Site banner now states exactly what is preview; new page `/data` ("How we verify"). See `docs/verification.md`.
