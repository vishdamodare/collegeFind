"""Idempotent reference-data seed. Only facts verified against official pages/legends (see DATA_SOURCE_REGISTRY.md).

Categories are NOT seeded: they are discovered per year from official PDFs and marked unverified until an
admin confirms them against the legend (Phase 2).
"""
from sqlalchemy.dialects.postgresql import insert

from app.db import SessionLocal
from app.models.reference import AcademicYear, CounsellingAuthority, Examination, SeatType
from app.models.colleges import Course
from app.models.sources import DataSource

EXAMS = [
    dict(code="MHT_CET", name="MHT-CET", primary_metric="percentile", stream="engineering"),
    dict(code="JEE_MAIN", name="JEE Main", primary_metric="percentile", stream="engineering"),
    dict(code="NEET_UG", name="NEET UG", primary_metric="rank", stream="medical"),
]
AUTHORITIES = [
    dict(code="MAHA_CET_CELL", name="Maharashtra State Common Entrance Test Cell", website="https://cetcell.mahacet.org/"),
    dict(code="DMER_MH", name="Directorate of Medical Education & Research, Maharashtra", website="https://dmer.maharashtra.gov.in/"),
    dict(code="MCC", name="Medical Counselling Committee", website="https://mcc.nic.in/"),
]
# Names copied from the section headings in the CET Cell cut-off PDFs.
SEAT_TYPES = [
    dict(code="STATE_LEVEL", name="State Level", quota="maharashtra_state", home_university_class=None),
    dict(code="HU_TO_HU", name="Home University Seats Allotted to Home University Candidates", quota="maharashtra_state", home_university_class="HU"),
    dict(code="HU_TO_OHU", name="Home University Seats Allotted to Other Than Home University Candidates", quota="maharashtra_state", home_university_class="HU"),
    dict(code="OHU_TO_OHU", name="Other Than Home University Seats Allotted to Other Than Home University Candidates", quota="maharashtra_state", home_university_class="OHU"),
    dict(code="OHU_TO_HU", name="Other Than Home University Seats Allotted to Home University Candidates", quota="maharashtra_state", home_university_class="OHU"),
    dict(code="MIN_TO_MH", name="Minority Seats Allotted to Maharashtra State Candidature Candidates", quota="maharashtra_state", home_university_class=None),
    dict(code="MH_TO_AI", name="Maharashtra State Seats Allotted to All India Candidature Candidates", quota="maharashtra_state_ai_candidates", home_university_class=None),
    dict(code="ALL_INDIA", name="All India Seats", quota="all_india", home_university_class=None),
]
YEARS = [dict(label=f"{y}-{str(y + 1)[2:]}", start_year=y) for y in range(2022, 2027)]
SOURCES = [
    dict(name="MH CET Cell FE 2025 portal", base_url="https://fe2025.mahacet.org/"),
    dict(name="MH CET Cell FE 2026 portal", base_url="https://fe2026.mahacet.org/"),
    dict(name="MH CET Cell", base_url="https://cetcell.mahacet.org/"),
    dict(name="Maharashtra DMER", base_url="https://dmer.maharashtra.gov.in/"),
    dict(name="MCC", base_url="https://mcc.nic.in/"),
]
COURSES = [dict(code="BE_BTECH", name="Four Year Degree Courses in Engineering and Technology", stream="engineering")]


def seed(session) -> None:
    for model, rows, key in [(Examination, EXAMS, "code"), (CounsellingAuthority, AUTHORITIES, "code"),
                             (SeatType, SEAT_TYPES, "code"), (AcademicYear, YEARS, "label"),
                             (DataSource, SOURCES, "name"), (Course, COURSES, "code")]:
        session.execute(insert(model).values(rows).on_conflict_do_nothing(index_elements=[key]))
    session.commit()


if __name__ == "__main__":
    with SessionLocal() as s:
        seed(s)
    print("seeded")
