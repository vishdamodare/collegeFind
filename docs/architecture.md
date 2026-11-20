# Architecture

```
frontend/ (Next.js, TS, Tailwind)  ──REST /api/v1──▶  backend/ (FastAPI, SQLAlchemy, Alembic)  ──▶  PostgreSQL
                                                          ▲
data-engine/ (parsers → validators → importers) ──────────┘  writes only 'pending' rows; admin approval publishes
```

* **backend/** – API + domain. `prediction/` holds one engine per exam family (engineering = percentile; medical = rank, Phase 6). `get_engine()` refuses to route NEET to the percentile engine.
* **data-engine/** – no web dependencies. A parser turns an official document into cells + errors; the importer (Phase 2) stores the source file (sha256, URL, date), creates an `import_job`, and inserts `cutoff_records` as `pending`. Nothing is visible to students until an admin approves the job. Rollback = mark the job `rolled_back` and its rows `rejected`.
* **Why parsers per document family:** CET lists, All-India lists, seat matrices, DMER/MCC lists have different layouts. Each family gets its own parser module with a name+version recorded on the `import_job`.
* **Python 3.9 note:** the dev machine has only Python 3.9. Code uses `Optional[...]` and `from __future__ import annotations`; target 3.12 in Docker once available.

## Decisions (safe defaults, reversible)
| Decision | Default | Why |
|---|---|---|
| Category / seat-type values | rows in DB, discovered per year, `is_verified=false` until admin confirms vs the PDF legend | spec forbids hardcoding |
| Missing metric | `NULL` + DB CHECK that at least one metric exists | never silently 0 |
| Allotment data | aggregate counts only | no candidate PII |
| Celery/Redis/S3 | deferred until import volume needs it (Phase 2/5); local file storage URI first | avoid infra before it pays off |
| Auth | Phase 5 | needs schema only now |
