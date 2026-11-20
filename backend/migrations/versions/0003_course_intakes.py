"""course_intakes: per-course seat summary from the CET Cell seat matrix

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "course_intakes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("college_course_id", sa.Integer, sa.ForeignKey("college_courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("academic_year_id", sa.Integer, sa.ForeignKey("academic_years.id"), nullable=False),
        sa.Column("si", sa.Integer, nullable=False),
        sa.Column("ms_seats", sa.Integer, nullable=False),
        sa.Column("minority_seats", sa.Integer, nullable=False),
        sa.Column("all_india_seats", sa.Integer, nullable=False),
        sa.Column("institute_seats", sa.Integer, nullable=False),
        sa.Column("orphan_seats", sa.Integer, nullable=False),
        sa.Column("published_date", sa.Date),
        sa.Column("source_document_id", sa.Integer, sa.ForeignKey("uploaded_documents.id"), nullable=False),
        sa.Column("source_page", sa.Integer),
        sa.Column("import_job_id", sa.Integer, sa.ForeignKey("import_jobs.id"), nullable=False),
        sa.Column("verification_status", sa.String(12), nullable=False, server_default="pending"),
        sa.UniqueConstraint("college_course_id", "academic_year_id", "source_document_id", name="uq_intake_course_year_doc"),
        sa.CheckConstraint("si >= 0 and ms_seats >= 0 and minority_seats >= 0 and all_india_seats >= 0 "
                           "and institute_seats >= 0 and orphan_seats >= 0", name="ck_intake_nonneg"),
        sa.CheckConstraint("verification_status in ('pending','verified','rejected','superseded')", name="ck_intake_status"),
    )
    for col in ("college_course_id", "academic_year_id", "source_document_id", "import_job_id"):
        op.create_index(f"ix_course_intakes_{col}", "course_intakes", [col])


def downgrade():
    op.drop_table("course_intakes")
