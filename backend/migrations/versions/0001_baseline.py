"""Baseline schema.

The baseline is generated from the SQLAlchemy models (`Base.metadata`) so it can never drift from
them. Every later schema change must be a normal, explicit Alembic migration with its own
revision file (use `alembic revision --autogenerate -m "..."` and review the output).

Revision ID: 0001_baseline
Revises:
"""

from alembic import op

from app.models import Base

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
