"""store the stage label exactly as printed (I, II, I-Non PWD, VII ...)

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

COLS_NEW = ["college_course_id", "round_id", "stage_label", "category_id", "seat_type_id", "source_document_id"]
COLS_OLD = ["college_course_id", "round_id", "stage", "category_id", "seat_type_id", "source_document_id"]


def upgrade():
    op.add_column("cutoff_records", sa.Column("stage_label", sa.String(40), nullable=False, server_default="I"))
    op.drop_constraint("uq_cutoff_cell", "cutoff_records", type_="unique")
    op.create_unique_constraint("uq_cutoff_cell", "cutoff_records", COLS_NEW)


def downgrade():
    # Fails if rows exist whose only difference is the label (e.g. 'I' vs 'I-Non PWD'): intended, never merge silently.
    op.drop_constraint("uq_cutoff_cell", "cutoff_records", type_="unique")
    op.create_unique_constraint("uq_cutoff_cell", "cutoff_records", COLS_OLD)
    op.drop_column("cutoff_records", "stage_label")
