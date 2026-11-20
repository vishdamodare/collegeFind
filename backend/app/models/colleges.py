from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._common import created, fk, pk


class College(Base):
    __tablename__ = "colleges"
    id: Mapped[int] = pk()
    institute_code: Mapped[str] = mapped_column(String(10), unique=True)  # CET Cell code, e.g. '01002'
    name: Mapped[str] = mapped_column(String(300))
    normalized_name: Mapped[str] = mapped_column(String(300), index=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True)
    # Raw 'Status:' line from the official list ('Government Autonomous', 'Un-Aided') kept verbatim.
    status_raw: Mapped[Optional[str]] = mapped_column(String(120))
    ownership: Mapped[Optional[str]] = mapped_column(String(20))  # government | aided | unaided | None=unknown
    university: Mapped[Optional[str]] = mapped_column(String(160))
    website: Mapped[Optional[str]] = mapped_column(String(300))
    aicte_id: Mapped[Optional[str]] = mapped_column(String(40))
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    __table_args__ = (CheckConstraint(
        "ownership is null or ownership in ('government','aided','unaided')", name="ck_college_ownership"),)


class CollegeLocation(Base):
    __tablename__ = "college_locations"
    id: Mapped[int] = pk()
    college_id: Mapped[int] = fk("colleges.id", ondelete="CASCADE")
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    state: Mapped[str] = mapped_column(String(60), default="Maharashtra")
    pincode: Mapped[Optional[str]] = mapped_column(String(10))
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    source_document_id: Mapped[Optional[int]] = fk("uploaded_documents.id", nullable=True)


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = pk()
    code: Mapped[str] = mapped_column(String(20), unique=True)  # BE_BTECH, MBBS, BDS
    name: Mapped[str] = mapped_column(String(160))
    stream: Mapped[str] = mapped_column(String(32))  # engineering | medical


class Branch(Base):
    __tablename__ = "branches"
    id: Mapped[int] = pk()
    course_id: Mapped[int] = fk("courses.id")
    name: Mapped[str] = mapped_column(String(200))
    normalized_name: Mapped[str] = mapped_column(String(200), unique=True)


class CollegeCourse(Base):
    """A branch offered by a college. choice_code is the CAP 10-digit code (5 institute + 5 course)."""
    __tablename__ = "college_courses"
    id: Mapped[int] = pk()
    college_id: Mapped[int] = fk("colleges.id", ondelete="CASCADE")
    course_id: Mapped[int] = fk("courses.id")
    branch_id: Mapped[Optional[int]] = fk("branches.id", nullable=True)
    choice_code: Mapped[Optional[str]] = mapped_column(String(12))
    name_raw: Mapped[str] = mapped_column(String(250))
    approved_intake: Mapped[Optional[int]] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint("college_id", "choice_code"),)


class CollegeFee(Base):
    __tablename__ = "college_fees"
    id: Mapped[int] = pk()
    college_course_id: Mapped[int] = fk("college_courses.id", ondelete="CASCADE")
    academic_year_id: Mapped[int] = fk("academic_years.id")
    annual_tuition_inr: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    source_document_id: Mapped[int] = fk("uploaded_documents.id")  # fees must cite a source (e.g. FRA)
    __table_args__ = (UniqueConstraint("college_course_id", "academic_year_id"),
                      CheckConstraint("annual_tuition_inr >= 0", name="ck_fee_nonneg"))


class CollegeRanking(Base):
    __tablename__ = "college_rankings"
    id: Mapped[int] = pk()
    college_id: Mapped[int] = fk("colleges.id", ondelete="CASCADE")
    framework: Mapped[str] = mapped_column(String(20))  # NIRF
    category: Mapped[str] = mapped_column(String(40))  # Engineering, Overall...
    year: Mapped[int] = mapped_column(Integer)
    rank_value: Mapped[int] = mapped_column(Integer)
    source_document_id: Mapped[int] = fk("uploaded_documents.id")
    __table_args__ = (UniqueConstraint("college_id", "framework", "category", "year"),)


class CollegePlacement(Base):
    __tablename__ = "college_placements"
    id: Mapped[int] = pk()
    college_id: Mapped[int] = fk("colleges.id", ondelete="CASCADE")
    year: Mapped[int] = mapped_column(Integer)
    median_package_lpa: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    highest_package_lpa: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    students_placed: Mapped[Optional[int]] = mapped_column(Integer)
    source_document_id: Mapped[int] = fk("uploaded_documents.id")
    __table_args__ = (UniqueConstraint("college_id", "year"),)


class CollegeFacility(Base):
    __tablename__ = "college_facilities"
    id: Mapped[int] = pk()
    college_id: Mapped[int] = fk("colleges.id", ondelete="CASCADE")
    facility: Mapped[str] = mapped_column(String(80))  # hostel_boys, library, ...
    details: Mapped[Optional[str]] = mapped_column(Text)
    source_document_id: Mapped[Optional[int]] = fk("uploaded_documents.id", nullable=True)
    __table_args__ = (UniqueConstraint("college_id", "facility"),)
