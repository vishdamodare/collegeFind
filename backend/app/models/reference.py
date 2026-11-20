"""Configurable reference data: exams, years, authorities, rounds, categories, seat types."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._common import fk, pk


class Examination(Base):
    __tablename__ = "examinations"
    id: Mapped[int] = pk()
    code: Mapped[str] = mapped_column(String(32), unique=True)  # MHT_CET, JEE_MAIN, NEET_UG
    name: Mapped[str] = mapped_column(String(120))
    # Which cutoff metric this exam's engine compares. Engines never cross metrics.
    primary_metric: Mapped[str] = mapped_column(String(16))
    stream: Mapped[str] = mapped_column(String(32))  # engineering | medical
    __table_args__ = (CheckConstraint("primary_metric in ('percentile','rank','marks')", name="ck_exam_metric"),)


class AcademicYear(Base):
    __tablename__ = "academic_years"
    id: Mapped[int] = pk()
    label: Mapped[str] = mapped_column(String(9), unique=True)  # '2024-25'
    start_year: Mapped[int] = mapped_column(Integer, unique=True)


class CounsellingAuthority(Base):
    __tablename__ = "counselling_authorities"
    id: Mapped[int] = pk()
    code: Mapped[str] = mapped_column(String(32), unique=True)  # MAHA_CET_CELL, DMER_MH, MCC
    name: Mapped[str] = mapped_column(String(160))
    website: Mapped[Optional[str]] = mapped_column(String(300))


class CounsellingRound(Base):
    __tablename__ = "counselling_rounds"
    id: Mapped[int] = pk()
    authority_id: Mapped[int] = fk("counselling_authorities.id")
    exam_id: Mapped[int] = fk("examinations.id")
    academic_year_id: Mapped[int] = fk("academic_years.id")
    round_no: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(60))  # 'CAP Round 1', 'Stray Vacancy'
    is_additional: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (UniqueConstraint("authority_id", "exam_id", "academic_year_id", "round_no", "label"),)


class Category(Base):
    """Category codes are year- and exam-specific (e.g. GOPENS, LSCH). Never hardcode in app code."""
    __tablename__ = "categories"
    id: Mapped[int] = pk()
    exam_id: Mapped[int] = fk("examinations.id")
    academic_year_id: Mapped[Optional[int]] = fk("academic_years.id", nullable=True)
    code: Mapped[str] = mapped_column(String(32))
    description: Mapped[Optional[str]] = mapped_column(String(200))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)  # code decoded from an official legend
    __table_args__ = (UniqueConstraint("exam_id", "academic_year_id", "code", postgresql_nulls_not_distinct=True),)


class SeatType(Base):
    """Seat level: State Level, Home University, Other Than Home University, All India, ..."""
    __tablename__ = "seat_types"
    id: Mapped[int] = pk()
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    quota: Mapped[str] = mapped_column(String(32))  # maharashtra_state | all_india | institute | ...
    home_university_class: Mapped[Optional[str]] = mapped_column(String(32))  # HU | OHU | None


class AdmissionRule(Base):
    __tablename__ = "admission_rules"
    id: Mapped[int] = pk()
    exam_id: Mapped[int] = fk("examinations.id")
    academic_year_id: Mapped[int] = fk("academic_years.id")
    rule_key: Mapped[str] = mapped_column(String(80))
    rule_value: Mapped[dict] = mapped_column(JSONB)
    description: Mapped[Optional[str]] = mapped_column(Text)
    source_document_id: Mapped[Optional[int]] = fk("uploaded_documents.id", nullable=True)
    __table_args__ = (UniqueConstraint("exam_id", "academic_year_id", "rule_key"),)
