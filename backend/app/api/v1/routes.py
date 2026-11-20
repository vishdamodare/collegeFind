from __future__ import annotations

import time

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.db import get_session
from app.models.admissions import CourseIntake, CutoffRecord as CR
from app.models.colleges import College, CollegeCourse
from app.models.reference import AcademicYear, CounsellingRound, Examination, SeatType
from app.models.sources import UploadedDocument
from app.prediction.engineering import AMBITIOUS, MODERATE, SAFER, ComparisonConfig, compare_percentile, get_engine

router = APIRouter(prefix="/api/v1")

# /meta only changes when a dataset is imported, so a short in-process cache saves ~5 DB round-trips per page view.
# ponytail: per-process cache; use Redis (already in the stack plan) if several API instances need instant invalidation.
_META_TTL_S = 60
_meta_cache: dict = {"at": 0.0, "value": None}


def _served():
    return ("verified", "pending") if settings.serve_unverified else ("verified",)


def _cutoff_query():
    """Plain column rows, not ORM entities: hydrating 7 entities per row cost ~2 s for a 1,000-row prediction."""
    return (select(College.name.label("college"), College.slug.label("college_slug"),
                   College.institute_code.label("institute_code"), CollegeCourse.id.label("cc_id"),
                   CollegeCourse.name_raw.label("branch"), CollegeCourse.choice_code.label("choice_code"),
                   SeatType.id.label("st_id"), SeatType.name.label("seat_type"), SeatType.code.label("seat_type_code"),
                   CR.category_code_raw.label("category"), CR.stage.label("stage"), CR.stage_label.label("stage_label"),
                   CR.closing_percentile.label("closing_percentile"), CR.closing_rank.label("closing_rank"),
                   CR.original_metric_text.label("original_text"), CR.source_page.label("source_page"),
                   CR.verification_status.label("verification_status"), AcademicYear.label.label("year"),
                   AcademicYear.start_year.label("year_start"), CounsellingRound.round_no.label("round"),
                   UploadedDocument.source_url.label("source_url"))
            .select_from(CR)
            .join(College, College.id == CR.college_id).join(CollegeCourse, CollegeCourse.id == CR.college_course_id)
            .join(SeatType, SeatType.id == CR.seat_type_id).join(CounsellingRound, CounsellingRound.id == CR.round_id)
            .join(AcademicYear, AcademicYear.id == CR.academic_year_id)
            .join(UploadedDocument, UploadedDocument.id == CR.source_document_id)
            .where(CR.verification_status.in_(_served())))


def _row(r) -> dict:
    return {"college": r.college, "college_slug": r.college_slug, "institute_code": r.institute_code,
            "branch": r.branch, "choice_code": r.choice_code, "category": r.category,
            "seat_type": r.seat_type, "seat_type_code": r.seat_type_code, "year": r.year, "round": r.round,
            "stage": r.stage, "stage_label": r.stage_label,
            "closing_percentile": str(r.closing_percentile) if r.closing_percentile is not None else None,
            "closing_rank": r.closing_rank, "original_text": r.original_text,
            "source_url": r.source_url, "source_page": r.source_page, "verification_status": r.verification_status}


@router.get("/meta")
def meta(db: Session = Depends(get_session)):
    if _meta_cache["value"] is not None and time.monotonic() - _meta_cache["at"] < _META_TTL_S:
        return _meta_cache["value"]
    served = _served()
    cats = db.execute(select(CR.category_code_raw, SeatType.code).join(SeatType, SeatType.id == CR.seat_type_id)
                      .where(CR.verification_status.in_(served)).distinct().order_by(CR.category_code_raw)).all()
    years = db.scalars(select(AcademicYear.label).join(CR, CR.academic_year_id == AcademicYear.id)
                       .where(CR.verification_status.in_(served)).distinct().order_by(AcademicYear.label)).all()
    rounds = db.scalars(select(CounsellingRound.round_no).join(CR, CR.round_id == CounsellingRound.id)
                        .where(CR.verification_status.in_(served)).distinct().order_by(CounsellingRound.round_no)).all()
    seat = db.execute(select(SeatType.code, SeatType.name)).all()
    counts = dict(db.execute(select(CR.verification_status, func.count()).group_by(CR.verification_status)).all())
    # (year, round) combinations that still contain unverified (pending) records: shown to students as "preview".
    preview = db.execute(select(AcademicYear.label, CounsellingRound.round_no).select_from(CR)
                         .join(AcademicYear, AcademicYear.id == CR.academic_year_id)
                         .join(CounsellingRound, CounsellingRound.id == CR.round_id)
                         .where(CR.verification_status == "pending").distinct()
                         .order_by(AcademicYear.label, CounsellingRound.round_no)).all()
    out = {"years": years, "rounds": rounds, "seat_types": [{"code": c, "name": n} for c, n in seat],
           "categories": [{"code": c, "seat_type_code": s} for c, s in cats],
           "records": counts, "serving_unverified": settings.serve_unverified,
           "preview_rounds": [f"{y}|{r}" for y, r in preview]}
    _meta_cache.update(at=time.monotonic(), value=out)
    return out


@router.get("/colleges")
def colleges(q: str = "", ownership: Optional[str] = None, page: int = Query(1, ge=1),
             page_size: int = Query(24, ge=1, le=100), db: Session = Depends(get_session)):
    stmt = select(College, func.count(CollegeCourse.id)).join(CollegeCourse, CollegeCourse.college_id == College.id, isouter=True).group_by(College.id)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(College.normalized_name.like(like), College.institute_code == q.strip()))
    if ownership:
        stmt = stmt.where(College.ownership == ownership)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.execute(stmt.order_by(College.name).offset((page - 1) * page_size).limit(page_size)).all()
    return {"total": total, "page": page, "page_size": page_size,
            "items": [{"name": c.name, "slug": c.slug, "institute_code": c.institute_code, "ownership": c.ownership,
                       "status_raw": c.status_raw, "university": c.university, "branches": n} for c, n in rows]}


@router.get("/colleges/{slug}")
def college(slug: str, db: Session = Depends(get_session)):
    c = db.scalar(select(College).where(College.slug == slug))
    if not c:
        raise HTTPException(404, "College not found")
    courses = db.scalars(select(CollegeCourse).where(CollegeCourse.college_id == c.id).order_by(CollegeCourse.name_raw)).all()
    # Latest seat-matrix row per course (served statuses only).
    intakes = {}
    q = (select(CourseIntake, AcademicYear.label).join(AcademicYear, AcademicYear.id == CourseIntake.academic_year_id)
         .where(CourseIntake.college_course_id.in_([x.id for x in courses]), CourseIntake.verification_status.in_(_served()))
         .order_by(CourseIntake.college_course_id, AcademicYear.start_year.desc()))
    for ci, label in db.execute(q).all():
        intakes.setdefault(ci.college_course_id, (ci, label))
    years_with_cutoffs = dict(db.execute(
        select(CR.college_course_id, func.array_agg(func.distinct(AcademicYear.label)))
        .join(AcademicYear, AcademicYear.id == CR.academic_year_id)
        .where(CR.college_id == c.id, CR.verification_status.in_(_served())).group_by(CR.college_course_id)).all())

    def intake(cc):
        hit = intakes.get(cc.id)
        if not hit:
            return None
        ci, label = hit
        return {"year": label, "si": ci.si, "ms_seats": ci.ms_seats, "minority_seats": ci.minority_seats,
                "all_india_seats": ci.all_india_seats, "institute_seats": ci.institute_seats, "orphan_seats": ci.orphan_seats,
                "published_date": ci.published_date.isoformat() if ci.published_date else None,
                "source_page": ci.source_page, "verification_status": ci.verification_status}

    return {"name": c.name, "slug": c.slug, "institute_code": c.institute_code, "ownership": c.ownership,
            "status_raw": c.status_raw, "university": c.university, "website": c.website,
            "branches": [{"name": b.name_raw, "choice_code": b.choice_code, "intake": intake(b),
                          "cutoff_years": sorted(years_with_cutoffs.get(b.id, []))} for b in courses]}


@router.get("/trends")
def trends(college_slug: str, choice_code: str, category: str, seat_type: str, db: Session = Depends(get_session)):
    """One closing value per (year, round) for a course/category/seat type: the highest stage row (its percentile may be null)."""
    stmt = (_cutoff_query().where(College.slug == college_slug, CollegeCourse.choice_code == choice_code,
                                  CR.category_code_raw == category, SeatType.code == seat_type)
            .distinct(AcademicYear.start_year, CounsellingRound.round_no)
            .order_by(AcademicYear.start_year, CounsellingRound.round_no, CR.stage.desc(), CR.stage_label.desc()))
    pts = []
    for r in db.execute(stmt).all():
        row = _row(r)
        pts.append({k: row[k] for k in ("year", "round", "stage_label", "closing_percentile", "closing_rank",
                                         "original_text", "source_url", "source_page", "verification_status")})
    return {"points": pts}


@router.get("/trend-options")
def trend_options(college_slug: str, choice_code: str, db: Session = Depends(get_session)):
    """Which (seat type, category) pairs have cutoffs for this course, so the UI only offers real choices."""
    q = (select(SeatType.code, SeatType.name, CR.category_code_raw, func.count(func.distinct(AcademicYear.label)))
         .select_from(CR).join(College, College.id == CR.college_id)
         .join(CollegeCourse, CollegeCourse.id == CR.college_course_id).join(SeatType, SeatType.id == CR.seat_type_id)
         .join(AcademicYear, AcademicYear.id == CR.academic_year_id)
         .where(College.slug == college_slug, CollegeCourse.choice_code == choice_code, CR.verification_status.in_(_served()))
         .group_by(SeatType.code, SeatType.name, CR.category_code_raw).order_by(SeatType.code, CR.category_code_raw))
    return {"options": [{"seat_type_code": a, "seat_type": b, "category": c, "years": n} for a, b, c, n in db.execute(q).all()]}


@router.get("/cutoffs")
def cutoffs(college_slug: Optional[str] = None, branch: str = "", category: Optional[str] = None,
            seat_type: Optional[str] = None, year: Optional[str] = None, round: Optional[int] = None,
            page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), db: Session = Depends(get_session)):
    stmt = _cutoff_query()
    if college_slug: stmt = stmt.where(College.slug == college_slug)
    if branch: stmt = stmt.where(func.lower(CollegeCourse.name_raw).like(f"%{branch.lower()}%"))
    if category: stmt = stmt.where(CR.category_code_raw == category)
    if seat_type: stmt = stmt.where(SeatType.code == seat_type)
    if year: stmt = stmt.where(AcademicYear.label == year)
    if round: stmt = stmt.where(CounsellingRound.round_no == round)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.execute(stmt.order_by(College.name, CollegeCourse.name_raw, CR.category_code_raw, CR.stage, CR.stage_label)
                      .offset((page - 1) * page_size).limit(page_size)).all()
    return {"total": total, "page": page, "page_size": page_size, "items": [_row(r) for r in rows]}


class PredictIn(BaseModel):
    exam_code: str
    percentile: Decimal = Field(ge=0, le=100)
    category: str
    seat_type: Optional[str] = None
    year: Optional[str] = None
    round: Optional[int] = None
    branch: str = ""
    status: Optional[str] = None            # filter: safer_historical | moderate | ambitious | insufficient_data
    offset: int = Field(0, ge=0)
    limit: int = Field(30, ge=1, le=100)    # page size; the UI loads more on demand


@router.post("/predict")
def predict(body: PredictIn, db: Session = Depends(get_session)):
    """One result per (college branch, seat type), with its full year-by-round history attached.

    Headline comparison = the most recent year available, using that year's earliest round (Round 1, the strictest
    closing cutoff). Every other record is compared too and listed under `records`. See docs/prediction-logic.md.
    """
    try:
        engine = get_engine(body.exam_code)
    except NotImplementedError as e:
        raise HTTPException(501, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    if body.exam_code != "MHT_CET":
        raise HTTPException(501, "No official cutoff data imported for this exam yet")
    stmt = _cutoff_query().where(CR.category_code_raw == body.category)
    if body.seat_type: stmt = stmt.where(SeatType.code == body.seat_type)
    if body.year: stmt = stmt.where(AcademicYear.label == body.year)
    if body.round: stmt = stmt.where(CounsellingRound.round_no == body.round)
    if body.branch: stmt = stmt.where(func.lower(CollegeCourse.name_raw).like(f"%{body.branch.lower()}%"))
    # Last stage of each (course, seat type, round, year) = that round's final closing value.
    stmt = stmt.distinct(CR.college_course_id, CR.seat_type_id, CR.round_id, CR.academic_year_id).order_by(
        CR.college_course_id, CR.seat_type_id, CR.round_id, CR.academic_year_id, CR.stage.desc(), CR.stage_label.desc())

    groups: dict = {}
    for r in db.execute(stmt).all():
        cmp = engine(body.percentile, r.closing_percentile, ComparisonConfig())
        rec = {**_row(r), "status": cmp.status, "gap": str(cmp.gap) if cmp.gap is not None else None, "reason": cmp.reason,
               "_year_start": r.year_start}
        groups.setdefault((r.cc_id, r.st_id), []).append(rec)

    items = []
    for recs in groups.values():
        recs.sort(key=lambda x: (-x["_year_start"], x["round"]))
        latest_year = recs[0]["_year_start"]
        head = min((x for x in recs if x["_year_start"] == latest_year), key=lambda x: x["round"])
        idx = next(i for i, x in enumerate(recs) if x is head)
        for x in recs:
            x.pop("_year_start")
        items.append({"college": head["college"], "college_slug": head["college_slug"], "branch": head["branch"],
                      "choice_code": head["choice_code"], "category": head["category"],
                      "seat_type_code": head["seat_type_code"], "status": head["status"], "headline_idx": idx,
                      "_head": head, "records": recs})

    def sort_key(it):
        h = it["_head"]
        c = float(h["closing_percentile"]) if h["closing_percentile"] is not None else None
        g = abs(float(h["gap"])) if h["gap"] is not None else 0.0
        if it["status"] == SAFER: return (0, -(c or 0))        # best colleges you clear first
        if it["status"] == MODERATE: return (1, g)             # nearest to your score first
        if it["status"] == AMBITIOUS: return (2, c or 0)       # closest reach first (lowest cutoff above you)
        return (3, 0)
    items.sort(key=sort_key)
    summary = {k: sum(1 for x in items if x["status"] == k) for k in (SAFER, MODERATE, AMBITIOUS)}
    shown = [x for x in items if not body.status or x["status"] == body.status]
    page = shown[body.offset: body.offset + body.limit]

    # Compact payload: per-record fields only; repeated strings (college, seat type, source URL) are sent once.
    keep = ("year", "round", "stage_label", "closing_percentile", "closing_rank", "status", "gap", "source_page", "original_text")
    sources = {}
    for it in page:
        for r in it["records"]:
            sources[f'{r["year"]}|{r["round"]}'] = r["source_url"]
        it["records"] = [{k: r[k] for k in keep} for r in it["records"]]
        it.pop("_head")
    return {"summary": summary, "total": len(shown), "offset": body.offset, "items": page, "sources": sources,
            "basis": "Most recent year available, Round 1 (strictest closing cutoff).",
            "disclaimer": "Historical comparison only. Past cutoffs do not guarantee future admission."}
