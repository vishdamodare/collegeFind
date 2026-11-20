"""Historical cutoff comparison for percentile-based engineering exams (MHT-CET, JEE Main).

This is a *historical comparison*, not an admission prediction: it says where a student's score sits
relative to what a seat closed at in a past round. See docs/prediction-logic.md.
NEET (rank-based, different counselling rules) must never be routed here — see get_engine().
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

PERCENTILE_EXAMS = {"MHT_CET", "JEE_MAIN"}

AMBITIOUS, MODERATE, SAFER = "ambitious", "moderate", "safer_historical"
INSUFFICIENT = "insufficient_data"


@dataclass(frozen=True)
class ComparisonConfig:
    # A student within +/- this many percentile points of the closing cutoff is "moderate".
    # Default is a documented starting point, not a calibrated value — tune against backtests (Phase 4).
    percentile_margin: Decimal = Decimal("1.0")


@dataclass(frozen=True)
class Comparison:
    status: str
    gap: Optional[Decimal]  # student - closing, in percentile points; None when not comparable
    reason: Optional[str] = None


def compare_percentile(student: Decimal, closing: Optional[Decimal],
                       cfg: ComparisonConfig = ComparisonConfig()) -> Comparison:
    if not (Decimal(0) <= student <= Decimal(100)):
        raise ValueError("student percentile must be between 0 and 100")
    if closing is None:  # missing is never treated as 0
        return Comparison(INSUFFICIENT, None, "No official closing percentile for this record")
    gap = student - closing
    if gap < -cfg.percentile_margin:
        return Comparison(AMBITIOUS, gap)
    if gap > cfg.percentile_margin:
        return Comparison(SAFER, gap)
    return Comparison(MODERATE, gap)


def get_engine(exam_code: str):
    if exam_code in PERCENTILE_EXAMS:
        return compare_percentile
    if exam_code == "NEET_UG":
        raise NotImplementedError("NEET uses a separate rank-based engine (Phase 6)")
    raise ValueError(f"Unknown exam {exam_code}")
