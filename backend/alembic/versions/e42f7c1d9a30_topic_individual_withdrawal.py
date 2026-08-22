"""topic recommendation individual publication state

Revision ID: e42f7c1d9a30
Revises: c61f8a2d7e04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e42f7c1d9a30"
down_revision: Union[str, None] = "c61f8a2d7e04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("topic_recommendation")}
    if "is_published" not in columns:
        op.add_column(
            "topic_recommendation",
            sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        )
    op.execute(
        "UPDATE topic_recommendation SET is_published = 1 "
        "WHERE report_id IN (SELECT id FROM daily_report WHERE status = 'published')"
    )


def downgrade() -> None:
    columns = {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns("topic_recommendation")
    }
    if "is_published" in columns:
        op.drop_column("topic_recommendation", "is_published")
