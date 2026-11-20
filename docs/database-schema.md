# Database schema (31 tables, migration `0001`)

Source of truth: `backend/app/models/*.py`; DDL in `backend/migrations/versions/0001_initial_schema.py`.

| Group | Tables |
|---|---|
| Reference (configurable) | examinations, academic_years, counselling_authorities, counselling_rounds, categories (exam+year specific), seat_types, admission_rules |
| Provenance | data_sources, uploaded_documents (sha256 unique, version, supersedes_id), import_jobs (status lifecycle, approver, rollback), import_validation_errors |
| Colleges | colleges (institute_code unique), college_locations, courses, branches, college_courses (CAP 10-digit choice_code, intake), college_fees, college_rankings, college_placements, college_facilities (fees/rankings/placements require a source document) |
| Admissions | seat_matrices, cutoff_records, allotment_records |
| Users | users (case-insensitive unique email), student_profiles, admin_users (role CHECK), saved_colleges, student_search_history, preference_lists, preference_list_items (position unique, deferrable for reordering), audit_logs |

## cutoff_records
FKs: college, college_course, course, branch, exam, academic_year, authority, round, category, seat_type, source_document, import_job.
Metrics: `closing_percentile numeric(10,7)`, `closing_rank int`, `closing_marks numeric(8,2)`; `original_metric_text` keeps the printed cell. Constraints: at least one metric non-null; percentile 0–100; rank > 0; one row per (course, round, stage, category, seat type, document). `category_code_raw` preserves the printed code.
`verification_status`: pending → verified | rejected | superseded. Only `verified` rows are served publicly.
