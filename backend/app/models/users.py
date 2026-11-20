from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._common import created, fk, pk


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = pk()
    email: Mapped[str] = mapped_column(String(254))
    password_hash: Mapped[str] = mapped_column(String(255))  # argon2/bcrypt hash only
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at = created()
    __table_args__ = (Index("uq_users_email_lower", func.lower(email), unique=True),)


class StudentProfile(Base):
    """Minimal by design: only what predictions need. No phone/address/DOB."""
    __tablename__ = "student_profiles"
    id: Mapped[int] = pk()
    user_id: Mapped[int] = fk("users.id", ondelete="CASCADE")
    display_name: Mapped[Optional[str]] = mapped_column(String(80))
    exam_id: Mapped[Optional[int]] = fk("examinations.id", nullable=True)
    category_code: Mapped[Optional[str]] = mapped_column(String(32))
    home_university: Mapped[Optional[str]] = mapped_column(String(120))
    __table_args__ = (UniqueConstraint("user_id"),)


class AdminUser(Base):
    __tablename__ = "admin_users"
    id: Mapped[int] = pk()
    user_id: Mapped[int] = fk("users.id", ondelete="CASCADE")
    role: Mapped[str] = mapped_column(String(20))  # admin | reviewer | viewer
    __table_args__ = (UniqueConstraint("user_id"),
                      CheckConstraint("role in ('admin','reviewer','viewer')", name="ck_admin_role"))


class SavedCollege(Base):
    __tablename__ = "saved_colleges"
    id: Mapped[int] = pk()
    user_id: Mapped[int] = fk("users.id", ondelete="CASCADE")
    college_id: Mapped[int] = fk("colleges.id", ondelete="CASCADE")
    __table_args__ = (UniqueConstraint("user_id", "college_id"),)


class StudentSearchHistory(Base):
    __tablename__ = "student_search_history"
    id: Mapped[int] = pk()
    user_id: Mapped[int] = fk("users.id", ondelete="CASCADE")
    exam_id: Mapped[int] = fk("examinations.id")
    query: Mapped[dict] = mapped_column(JSONB)
    created_at = created()


class PreferenceList(Base):
    __tablename__ = "preference_lists"
    id: Mapped[int] = pk()
    user_id: Mapped[int] = fk("users.id", ondelete="CASCADE")
    exam_id: Mapped[int] = fk("examinations.id")
    name: Mapped[str] = mapped_column(String(120))
    created_at = created()


class PreferenceListItem(Base):
    __tablename__ = "preference_list_items"
    id: Mapped[int] = pk()
    list_id: Mapped[int] = fk("preference_lists.id", ondelete="CASCADE")
    college_course_id: Mapped[int] = fk("college_courses.id")
    position: Mapped[int] = mapped_column(Integer)
    note: Mapped[Optional[str]] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("list_id", "position", deferrable=True, initially="DEFERRED"),
                      UniqueConstraint("list_id", "college_course_id"),
                      CheckConstraint("position >= 1", name="ck_pref_position"))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = pk()
    actor_user_id: Mapped[Optional[int]] = fk("users.id", nullable=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity_type: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[Optional[str]] = mapped_column(String(60))
    detail: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at = created()
