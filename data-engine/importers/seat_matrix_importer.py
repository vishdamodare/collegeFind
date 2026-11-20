"""Import a CET Cell seat-matrix PDF (parsed by parse_matrix.py) into Postgres as PENDING course_intakes.

Usage: PYTHONPATH=backend:data-engine python data-engine/importers/seat_matrix_importer.py FILE.pdf SOURCE_URL YEAR_LABEL
"""
import argparse, hashlib, os, pickle, sys
from datetime import datetime, timezone

from sqlalchemy import insert, select

from app.db import SessionLocal
from app.models.admissions import CourseIntake
from app.models.colleges import Branch, College, CollegeCourse, Course
from app.models.reference import AcademicYear
from app.models.sources import DataSource, ImportJob, ImportValidationError, UploadedDocument
from importers.cet_cutoff_importer import norm, ownership, slugify
from parsers.cet_seat_matrix import PARSER_NAME, PARSER_VERSION, parse_matrix_pdf


def load(path):
    cache = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(path))), "parsed", os.path.basename(path) + ".pkl")
    if os.path.exists(cache) and os.path.getmtime(cache) >= os.path.getmtime(path):
        ver, res = pickle.load(open(cache, "rb"))
        if ver == PARSER_VERSION:
            return res
    return parse_matrix_pdf(path)


def run(path, url, year_label):
    data = open(path, "rb").read()
    sha = hashlib.sha256(data).hexdigest()
    res = load(path)
    if res.year_label != year_label:
        sys.exit(f"REFUSING: PDF header says year {res.year_label}, expected {year_label}")
    with SessionLocal() as s:
        if s.scalar(select(UploadedDocument.id).where(UploadedDocument.sha256 == sha)):
            sys.exit("Document already imported (same sha256).")
        year = s.scalar(select(AcademicYear).where(AcademicYear.label == year_label))
        course = s.scalar(select(Course).where(Course.code == "BE_BTECH"))
        src = s.scalar(select(DataSource).where(DataSource.base_url.like("https://fe2025%")))
        doc = UploadedDocument(data_source_id=src.id, source_url=url, original_filename=os.path.basename(path),
                               storage_uri="file://" + os.path.abspath(path), sha256=sha, size_bytes=len(data),
                               academic_year_id=year.id, publication_date=res.published)
        s.add(doc); s.flush()
        job = ImportJob(document_id=doc.id, parser_name=PARSER_NAME, parser_version=PARSER_VERSION,
                        status="needs_review", started_at=datetime.now(timezone.utc))
        s.add(job); s.flush()

        colleges = {c.institute_code: c for c in s.scalars(select(College))}
        branches = {b.normalized_name: b for b in s.scalars(select(Branch))}
        ccs = {c.choice_code: c for c in s.scalars(select(CollegeCourse))}
        for r in res.rows:
            if r.institute_code not in colleges:
                col = College(institute_code=r.institute_code, name=r.institute_name, normalized_name=norm(r.institute_name),
                              slug=f"{slugify(r.institute_name)}-{r.institute_code}", status_raw=r.status_raw or None,
                              ownership=ownership(r.status_raw))
                s.add(col); colleges[r.institute_code] = col
        s.flush()
        for r in res.rows:
            bn = norm(r.course_name)
            if bn not in branches:
                b = Branch(course_id=course.id, name=r.course_name, normalized_name=bn); s.add(b); branches[bn] = b
        s.flush()
        for r in res.rows:
            if r.choice_code not in ccs:
                cc = CollegeCourse(college_id=colleges[r.institute_code].id, course_id=course.id,
                                   branch_id=branches[norm(r.course_name)].id, choice_code=r.choice_code, name_raw=r.course_name)
                s.add(cc); ccs[r.choice_code] = cc
        s.flush()
        seen, rows = set(), []
        for r in res.rows:
            cc = ccs[r.choice_code]
            if cc.id in seen:  # same course twice in one matrix: report, keep the first
                s.add(ImportValidationError(import_job_id=job.id, severity="warning", page_no=r.page,
                                            message="Duplicate course row in matrix ignored", row_ref=r.choice_code)); continue
            seen.add(cc.id)
            rows.append(dict(college_course_id=cc.id, academic_year_id=year.id, si=r.si, ms_seats=r.ms_seats,
                             minority_seats=r.minority_seats, all_india_seats=r.all_india_seats,
                             institute_seats=r.institute_seats, orphan_seats=r.orphan_seats, published_date=res.published,
                             source_document_id=doc.id, source_page=r.page, import_job_id=job.id,
                             verification_status="pending"))
        for i in range(0, len(rows), 3000):
            s.execute(insert(CourseIntake), rows[i:i + 3000])
        for page, msg, raw in res.errors:
            s.add(ImportValidationError(import_job_id=job.id, severity="error", page_no=page, message=msg, raw_text=raw))
        job.stats = {"courses": len(rows), "errors": len(res.errors), "published": str(res.published)}
        job.finished_at = datetime.now(timezone.utc)
        s.commit()
        print(job.stats)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("file"); ap.add_argument("url"); ap.add_argument("year")
    a = ap.parse_args(); run(a.file, a.url, a.year)
