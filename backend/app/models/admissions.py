from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, Date, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._common import created, fk, pk


class SeatMatrix(Base):
    __tablename__ = "seat_matrices"
    id: Mapped[int] = pk()
    college_course_id: Mapped[int] = fk("college_courses.id", ondelete="CASCADE")
    academic_year_id: Mapped[int] = fk("academic_years.id")
    seat_type_id: Mapped[int] = fk("seat_types.id")
    category_id: Mapped[Optional[int]] = fk("categories.id", nullable=True)
    seats: Mapped[int] = mapped_column(Integer)
    source_document_id: Mapped[int] = fk("uploaded_documents.id")
    import_job_id: Mapped[Optional[int]] = fk("import_jobs.id", nullable=True)
    verification_status: Mapped[str] = mapped_column(String(12), default="pending")
    __table_args__ = (
        CheckConstraint("seats >= 0", name="ck_seats_nonneg"),
        UniqueConstraint("college_course_id", "academic_year_id", "seat_type_id", "category_id",
                         postgresql_nulls_not_distinct=True),
    )


class CutoffRecord(Base):
    """One official closing cutoff. A missing metric is NULL — never 0.

    Engineering rows carry percentile (+ optional rank). NEET rows carry rank/marks. The engines in
    app/prediction read only the metric matching the exam, so metrics are never mixed.
    """
    __tablename__ = "cutoff_records"
    id: Mapped[int] = pk()
    college_id: Mapped[int] = fk("colleges.id")
    college_course_id: Mapped[int] = fk("college_courses.id")
    course_id: Mapped[int] = fk("courses.id")
    branch_id: Mapped[Optional[int]] = fk("branches.id", nullable=True)
    exam_id: Mapped[int] = fk("examinations.id")
    academic_year_id: Mapped[int] = fk("academic_years.id")
    authority_id: Mapped[int] = fk("counselling_authorities.id")
    round_id: Mapped[int] = fk("counselling_rounds.id")
    stage: Mapped[int] = mapped_column(Integer, default=1)  # leading roman numeral value; not unique on its own
    stage_label: Mapped[str] = mapped_column(String(40), default="I")  # exactly as printed: I, II, I-Non PWD, VII ...
    category_id: Mapped[int] = fk("categories.id")
    category_code_raw: Mapped[str] = mapped_column(String(32))  # exactly as printed, e.g. 'GOPENS'
    seat_type_id: Mapped[int] = fk("seat_types.id")
    quota: Mapped[str] = mapped_column(String(32))  # maharashtra_state | all_india | ...
    home_university_class: Mapped[Optional[str]] = mapped_column(String(8))  # HU | OHU | NULL
    closing_percentile: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 7))
    closing_rank: Mapped[Optional[int]] = mapped_column(Integer)
    closing_marks: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    original_metric_text: Mapped[str] = mapped_column(String(80))  # raw cell text(s) for audit
    source_document_id: Mapped[int] = fk("uploaded_documents.id")
    source_page: Mapped[Optional[int]] = mapped_column(Integer)
    import_job_id: Mapped[int] = fk("import_jobs.id")
    verification_status: Mapped[str] = mapped_column(String(12), default="pending")
    created_at = created()
    __table_args__ = (
        CheckConstraint("closing_percentile is not null or closing_rank is not null or closing_marks is not null",
                        name="ck_cutoff_has_metric"),
        CheckConstraint("closing_percentile is null or closing_percentile between 0 and 100", name="ck_cutoff_pct"),
        CheckConstraint("closing_rank is null or closing_rank > 0", name="ck_cutoff_rank"),
        CheckConstraint("verification_status in ('pending','verified','rejected','superseded')", name="ck_cutoff_status"),
        # Same document must not yield the same cell twice.
        UniqueConstraint("college_course_id", "round_id", "stage_label", "category_id", "seat_type_id",
                         "source_document_id", name="uq_cutoff_cell"),
        Index("ix_cutoff_lookup", "exam_id", "academic_year_id", "round_id", "category_id", "verification_status"),
    )


class AllotmentRecord(Base):
    """Aggregate allotment counts only. No candidate-level PII is stored."""
    __tablename__ = "allotment_records"
    id: Mapped[int] = pk()
    college_course_id: Mapped[int] = fk("college_courses.id")
    round_id: Mapped[int] = fk("counselling_rounds.id")
    category_id: Mapped[int] = fk("categories.id")
    seat_type_id: Mapped[int] = fk("seat_types.id")
    allotted_count: Mapped[int] = mapped_column(Integer)
    source_document_id: Mapped[int] = fk("uploaded_documents.id")
    import_job_id: Mapped[Optional[int]] = fk("import_jobs.id", nullable=True)
    verification_status: Mapped[str] = mapped_column(String(12), default="pending")
    __table_args__ = (UniqueConstraint("college_course_id", "round_id", "category_id", "seat_type_id",
                                       "source_document_id"),)


class CourseIntake(Base):
    """Per-course seat summary from the CET Cell 'Provisional Seat Matrix for CAP Round I' (one row per course/year).

    Column meanings follow the printed header: SI, MS Seats, Minority Seats, All India, Institute Seats, Orphan.
    """
    __tablename__ = "course_intakes"
    id: Mapped[int] = pk()
    college_course_id: Mapped[int] = fk("college_courses.id", ondelete="CASCADE")
    academic_year_id: Mapped[int] = fk("academic_years.id")
    si: Mapped[int] = mapped_column(Integer)
    ms_seats: Mapped[int] = mapped_column(Integer)
    minority_seats: Mapped[int] = mapped_column(Integer)
    all_india_seats: Mapped[int] = mapped_column(Integer)
    institute_seats: Mapped[int] = mapped_column(Integer)
    orphan_seats: Mapped[int] = mapped_column(Integer)
    published_date: Mapped[Optional[date]] = mapped_column(Date)
    source_document_id: Mapped[int] = fk("uploaded_documents.id")
    source_page: Mapped[Optional[int]] = mapped_column(Integer)
    import_job_id: Mapped[int] = fk("import_jobs.id")
    verification_status: Mapped[str] = mapped_column(String(12), default="pending")
    __table_args__ = (
        UniqueConstraint("college_course_id", "academic_year_id", "source_document_id", name="uq_intake_course_year_doc"),
        CheckConstraint("si >= 0 and ms_seats >= 0 and minority_seats >= 0 and all_india_seats >= 0 "
                        "and institute_seats >= 0 and orphan_seats >= 0", name="ck_intake_nonneg"),
        CheckConstraint("verification_status in ('pending','verified','rejected','superseded')", name="ck_intake_status"),
    )
