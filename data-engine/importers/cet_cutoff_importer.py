"""Import a CET Cell cut-off PDF into Postgres as PENDING records (never auto-verified).

Usage: PYTHONPATH=backend:data-engine python data-engine/importers/cet_cutoff_importer.py FILE.pdf SOURCE_URL YEAR_LABEL ROUND_NO
"""
import argparse, hashlib, os, pickle, re, sys
from datetime import datetime, timezone

from sqlalchemy import insert, select

from app.db import SessionLocal
from app.models.admissions import CutoffRecord
from app.models.colleges import Branch, College, CollegeCourse, Course
from app.models.reference import AcademicYear, Category, CounsellingAuthority, CounsellingRound, Examination, SeatType
from app.models.sources import DataSource, ImportJob, ImportValidationError, UploadedDocument
from parsers.cet_cutoff import PARSER_NAME, PARSER_VERSION, parse_pdf


def norm(s): return re.sub(r"\s+", " ", s.strip().lower())
def slugify(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:150]


def ownership(status):
    s = status.lower()
    if s.startswith(("government-aided", "government aided", "aided")): return "aided"   # must precede 'government'
    if s.startswith("government"): return "government"
    if s.startswith(("un-aided", "unaided")): return "unaided"
    return None


def run(path, url, year_label, round_no, allow_header_mismatch=None):
    data = open(path, "rb").read()
    sha = hashlib.sha256(data).hexdigest()
    h_year, h_round, h_scope = read_header(path)
    problems = []
    if h_year != year_label: problems.append(f"header year {h_year} != {year_label}")
    if h_round != round_no: problems.append(f"header round {h_round} != {round_no}")
    if h_scope != "maharashtra": problems.append(f"header scope is '{h_scope}', expected Maharashtra seats")
    if problems and not allow_header_mismatch:
        sys.exit("REFUSING TO IMPORT: " + "; ".join(problems) + "  (override with --allow-header-mismatch 'reason' only after manual review)")
    res = load_parsed(path)
    with SessionLocal() as s:
        if s.scalar(select(UploadedDocument.id).where(UploadedDocument.sha256 == sha)):
            sys.exit("Document already imported (same sha256).")
        exam = s.scalar(select(Examination).where(Examination.code == "MHT_CET"))
        auth = s.scalar(select(CounsellingAuthority).where(CounsellingAuthority.code == "MAHA_CET_CELL"))
        year = s.scalar(select(AcademicYear).where(AcademicYear.label == year_label))
        course = s.scalar(select(Course).where(Course.code == "BE_BTECH"))
        src = s.scalar(select(DataSource).where(DataSource.base_url.like("https://fe2025%")))
        seat = {t.code: t for t in s.scalars(select(SeatType))}
        doc = UploadedDocument(data_source_id=src.id, source_url=url, original_filename=os.path.basename(path),
                               storage_uri="file://" + os.path.abspath(path), sha256=sha, size_bytes=len(data),
                               academic_year_id=year.id)
        s.add(doc); s.flush()
        job = ImportJob(document_id=doc.id, parser_name=PARSER_NAME, parser_version=PARSER_VERSION,
                        status="needs_review", started_at=datetime.now(timezone.utc))
        s.add(job); s.flush()
        rnd = s.scalar(select(CounsellingRound).where(
            CounsellingRound.authority_id == auth.id, CounsellingRound.exam_id == exam.id,
            CounsellingRound.academic_year_id == year.id, CounsellingRound.round_no == round_no))
        if not rnd:
            rnd = CounsellingRound(authority_id=auth.id, exam_id=exam.id, academic_year_id=year.id,
                                   round_no=round_no, label=f"CAP Round {round_no}")
            s.add(rnd); s.flush()

        # Get-or-create so later rounds/years extend existing colleges, branches and courses.
        colleges = {c.institute_code: c for c in s.scalars(select(College))}
        branches = {b.normalized_name: b for b in s.scalars(select(Branch))}
        ccs = {c.choice_code: c for c in s.scalars(select(CollegeCourse))}
        cats = {c.code: c for c in s.scalars(select(Category).where(Category.exam_id == exam.id,
                                                                    Category.academic_year_id == year.id))}
        for c in res.cells:
            if c.institute_code not in colleges:
                col = College(institute_code=c.institute_code, name=c.institute_name, normalized_name=norm(c.institute_name),
                              slug=f"{slugify(c.institute_name)}-{c.institute_code}", status_raw=c.status_raw or None,
                              ownership=ownership(c.status_raw), university=c.university_raw or None)
                s.add(col); colleges[c.institute_code] = col
        s.flush()
        for c in res.cells:
            bn = norm(c.course_name)
            if bn not in branches:
                b = Branch(course_id=course.id, name=c.course_name, normalized_name=bn); s.add(b); branches[bn] = b
        s.flush()
        for c in res.cells:
            if c.choice_code not in ccs:
                cc = CollegeCourse(college_id=colleges[c.institute_code].id, course_id=course.id,
                                   branch_id=branches[norm(c.course_name)].id, choice_code=c.choice_code, name_raw=c.course_name)
                s.add(cc); ccs[c.choice_code] = cc
            if c.category_code not in cats:
                cat = Category(exam_id=exam.id, academic_year_id=year.id, code=c.category_code, is_verified=False)
                s.add(cat); cats[c.category_code] = cat
        s.flush()
        rows = []
        for c in res.cells:
            st = seat[c.seat_type_code]; cc = ccs[c.choice_code]
            rows.append(dict(college_id=cc.college_id, college_course_id=cc.id, course_id=course.id, branch_id=cc.branch_id,
                             exam_id=exam.id, academic_year_id=year.id, authority_id=auth.id, round_id=rnd.id, stage=c.stage, stage_label=c.stage_label,
                             category_id=cats[c.category_code].id, category_code_raw=c.category_code, seat_type_id=st.id,
                             quota=st.quota, home_university_class=st.home_university_class,
                             closing_percentile=c.closing_percentile, closing_rank=c.closing_rank,
                             original_metric_text=c.original_text, source_document_id=doc.id, source_page=c.page,
                             import_job_id=job.id, verification_status="pending"))
        for i in range(0, len(rows), 5000):
            s.execute(insert(CutoffRecord), rows[i:i + 5000])
        if problems:  # a human reviewed and overrode the header check: keep that on the record
            s.add(ImportValidationError(import_job_id=job.id, severity="warning", page_no=1,
                                        message="Header/argument mismatch overridden: " + "; ".join(problems) + " | reason: " + allow_header_mismatch))
        for page, msg, raw in res.errors:
            s.add(ImportValidationError(import_job_id=job.id, severity="error", page_no=page, message=msg, raw_text=raw))
        job.stats = {"cells": len(rows), "errors": len(res.errors), "colleges": len(colleges), "courses": len(ccs)}
        job.finished_at = datetime.now(timezone.utc)
        s.commit()
        print(job.stats)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("file"); ap.add_argument("url"); ap.add_argument("year"); ap.add_argument("round", type=int)
    ap.add_argument("--allow-header-mismatch", metavar="REASON")
    a = ap.parse_args()
    run(a.file, a.url, a.year, a.round, a.allow_header_mismatch)
