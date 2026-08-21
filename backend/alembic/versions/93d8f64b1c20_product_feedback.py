"""product feedback

Revision ID: 93d8f64b1c20
Revises: 5a54c66dbf47
Create Date: 2026-08-20 16:40:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "93d8f64b1c20"
down_revision: Union[str, None] = "5a54c66dbf47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 本地开发启动会先执行 Base.metadata.create_all；允许随后补齐 Alembic 版本记录。
    if sa.inspect(op.get_bind()).has_table("product_feedback"):
        return
    op.create_table(
        "product_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("contact_email", sa.String(length=320), nullable=True),
        sa.Column("page_url", sa.String(length=1000), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_feedback_user_id", "product_feedback", ["user_id"])
    op.create_index("ix_product_feedback_status", "product_feedback", ["status"])


def downgrade() -> None:
    op.drop_index("ix_product_feedback_status", table_name="product_feedback")
    op.drop_index("ix_product_feedback_user_id", table_name="product_feedback")
    op.drop_table("product_feedback")
