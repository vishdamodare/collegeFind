from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

# Verification lifecycle shared by imported datasets and records.
VERIFICATION_STATES = ("pending", "verified", "rejected", "superseded")


def pk() -> Mapped[int]:
    return mapped_column(primary_key=True)


def fk(target: str, nullable: bool = False, index: bool = True, ondelete: Optional[str] = None):
    return mapped_column(ForeignKey(target, ondelete=ondelete), nullable=nullable, index=index)


def created() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())
