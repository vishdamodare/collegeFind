from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal
from app.main import app
from app.prediction.engineering import (AMBITIOUS, INSUFFICIENT, MODERATE, SAFER, compare_percentile, get_engine)
from scripts.seed import seed


def test_all_32_tables_created(migrated):
    with SessionLocal() as s:
        n = s.scalar(text("select count(*) from information_schema.tables where table_schema='public' "
                          "and table_name <> 'alembic_version'"))
    assert n == 32


def test_seed_is_idempotent_and_exams_endpoint(migrated):
    with SessionLocal() as s:
        seed(s); seed(s)
    codes = [e["code"] for e in TestClient(app).get("/api/v1/exams").json()]
    assert codes == ["MHT_CET", "JEE_MAIN", "NEET_UG"]


def test_cutoff_cannot_be_stored_without_any_metric(migrated):
    # A cutoff with no percentile/rank/marks must be rejected by the DB (missing != 0).
    with SessionLocal() as s:
        with pytest.raises(IntegrityError, match="ck_cutoff_has_metric|violates"):
            s.execute(text("""insert into cutoff_records (college_id,college_course_id,course_id,exam_id,
              academic_year_id,authority_id,round_id,stage,category_id,category_code_raw,seat_type_id,quota,
              original_metric_text,source_document_id,import_job_id,verification_status)
              values (1,1,1,1,1,1,1,1,1,'X',1,'q','',1,1,'pending')"""))
        s.rollback()


@pytest.mark.parametrize("student,closing,status", [
    ("90", "95", AMBITIOUS), ("95.5", "95", MODERATE), ("94.2", "95", MODERATE),
    ("96.5", "95", SAFER), ("99.9999", "99.9999", MODERATE),
])
def test_percentile_comparison(student, closing, status):
    assert compare_percentile(Decimal(student), Decimal(closing)).status == status


def test_missing_cutoff_is_insufficient_not_zero():
    r = compare_percentile(Decimal("50"), None)
    assert r.status == INSUFFICIENT and r.gap is None


def test_neet_is_not_routed_to_percentile_engine():
    assert get_engine("MHT_CET") is compare_percentile
    with pytest.raises(NotImplementedError):
        get_engine("NEET_UG")
