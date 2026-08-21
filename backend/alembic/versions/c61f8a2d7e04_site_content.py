"""site content drafts and published snapshots

Revision ID: c61f8a2d7e04
Revises: 93d8f64b1c20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c61f8a2d7e04"
down_revision: Union[str, None] = "93d8f64b1c20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 本地开发启动会先执行 Base.metadata.create_all；允许随后补齐 Alembic 版本记录。
    if sa.inspect(op.get_bind()).has_table("site_content"):
        return
    op.create_table(
        "site_content",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("draft", sa.JSON(), nullable=False),
        sa.Column("published", sa.JSON(), nullable=False),
        sa.Column("previous_published", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("site_content")
