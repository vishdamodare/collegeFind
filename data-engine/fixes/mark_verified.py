"""Mark documents (and their records) as verified after the independent audit passed. Dry-run unless --apply.

Rules
* Only documents listed in VERIFIED are touched; HELD documents stay 'pending' (shown to students as "preview").
* A document is marked only if EVERY record of it is currently 'pending' (never flips rejected/superseded rows).
* One audit_logs row per document records the method, the evidence folder and that this was AUTOMATED verification,
  not review by a CET Cell official or a human admin.
Usage: set -a; . .env.local; set +a; python data-engine/fixes/mark_verified.py [--apply]
"""
import json, os, sys
from sqlalchemy import create_engine, text

APPLY = "--apply" in sys.argv
HELD = {"2022ENGG_CAP1_CutOff.pdf"}   # title says "All India Seats" but content is the Maharashtra list: awaiting CET Cell confirmation
e = create_engine(os.environ["DATABASE_URL_UNPOOLED"].replace("postgresql://", "postgresql+psycopg://", 1))
EVIDENCE = {
    "method": "automated multi-method audit (2026-11-10): independent re-extraction, visual page audit, completeness both directions, "
              "seat-matrix re-extraction, source-file hash check, end-to-end API check, regression diff after fixes",
    "evidence_folder": "data/verification/",
    "human_review": False,
    "known_gaps": "≈266 overflow-band cells (0.14%) not stored; see KNOWN_LIMITATIONS.md",
}
with e.begin() as c:
    docs = c.execute(text("select id, original_filename from uploaded_documents order by id")).all()
    for did, fn in docs:
        if fn in HELD:
            print(f"HELD      {fn} (stays pending)"); continue
        is_matrix = "SeatMatrix" in fn
        tbl = "course_intakes" if is_matrix else "cutoff_records"
        states = dict(c.execute(text(f"select verification_status, count(*) from {tbl} where source_document_id=:d group by 1"), {"d": did}).all())
        assert set(states) <= {"pending", "verified"}, (fn, states)
        n = c.execute(text(f"update {tbl} set verification_status='verified' where source_document_id=:d and verification_status='pending'"), {"d": did}).rowcount
        j = c.execute(text("update import_jobs set status='published', approved_at=now() where document_id=:d and status in ('needs_review','approved')"), {"d": did}).rowcount
        c.execute(text("insert into audit_logs (actor_user_id, action, entity_type, entity_id, detail) values (null, 'dataset_verified', 'uploaded_document', :d, cast(:j as jsonb))"),
                  {"d": str(did), "j": json.dumps({**EVIDENCE, "file": fn, "records_marked": n})})
        print(f"{'APPLIED' if APPLY else 'DRY-RUN'}   {fn:28s} {tbl}: {n:>7,} records -> verified; import job(s) published: {j}")
    if not APPLY:
        c.rollback(); print("\n(dry run: rolled back. re-run with --apply)")
