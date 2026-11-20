"""Provenance: data sources, stored documents, import jobs, validation errors."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._common import created, fk, pk


class DataSource(Base):
    __tablename__ = "data_sources"
    id: Mapped[int] = pk()
    name: Mapped[str] = mapped_column(String(160), unique=True)
    base_url: Mapped[str] = mapped_column(String(400))
    authority_id: Mapped[Optional[int]] = fk("counselling_authorities.id", nullable=True)
    licence_note: Mapped[Optional[str]] = mapped_column(Text)  # terms / copyright position
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"
    id: Mapped[int] = pk()
    data_source_id: Mapped[Optional[int]] = fk("data_sources.id", nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(600))
    original_filename: Mapped[str] = mapped_column(String(300))
    storage_uri: Mapped[str] = mapped_column(String(600))  # s3://... or file://...
    sha256: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    academic_year_id: Mapped[Optional[int]] = fk("academic_years.id", nullable=True)
    publication_date: Mapped[Optional[date]] = mapped_column(Date)
    version: Mapped[int] = mapped_column(Integer, default=1)
    supersedes_id: Mapped[Optional[int]] = fk("uploaded_documents.id", nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | superseded
    uploaded_by: Mapped[Optional[int]] = fk("admin_users.id", nullable=True)
    uploaded_at = created()
    __table_args__ = (
        UniqueConstraint("sha256", name="uq_document_sha256"),  # identical bytes are never stored twice
        CheckConstraint("status in ('active','superseded')", name="ck_document_status"),
    )


class ImportJob(Base):
    __tablename__ = "import_jobs"
    id: Mapped[int] = pk()
    document_id: Mapped[int] = fk("uploaded_documents.id")
    parser_name: Mapped[str] = mapped_column(String(80))
    parser_version: Mapped[str] = mapped_column(String(20))
    # pending -> running -> needs_review -> approved -> published ; failed / rolled_back are terminal
    status: Mapped[str] = mapped_column(String(16), default="pending")
    stats: Mapped[Optional[dict]] = mapped_column(JSONB)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[Optional[int]] = fk("admin_users.id", nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    rolled_back_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at = created()
    __table_args__ = (CheckConstraint(
        "status in ('pending','running','needs_review','approved','published','failed','rolled_back')",
        name="ck_import_status"),)


class ImportValidationError(Base):
    __tablename__ = "import_validation_errors"
    id: Mapped[int] = pk()
    import_job_id: Mapped[int] = fk("import_jobs.id", ondelete="CASCADE")
    severity: Mapped[str] = mapped_column(String(10))  # error | warning
    page_no: Mapped[Optional[int]] = mapped_column(Integer)
    row_ref: Mapped[Optional[str]] = mapped_column(String(120))
    message: Mapped[str] = mapped_column(Text)
    raw_text: Mapped[Optional[str]] = mapped_column(Text)
    __table_args__ = (CheckConstraint("severity in ('error','warning')", name="ck_validation_severity"),)
