# Loading into Neon

1. Create a Neon project (https://neon.tech), copy the pooled **connection string**.
2. Put it in `/Users/vish/collegeFind/.env` as `DATABASE_URL=postgresql+psycopg://USER:PASS@HOST/DB?sslmode=require` (never commit `.env`; it is git-ignored).
3. Schema: `cd backend && ../.venv/bin/alembic upgrade head`
4. Reference data: `PYTHONPATH=. ../.venv/bin/python scripts/seed.py`
5. Data: copy the validated local rows (`pg_dump --data-only` of the import tables) or re-run the importer against Neon.
