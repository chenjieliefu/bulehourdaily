"""personalized report user/date uniqueness

Revision ID: 9b7c31f2a640
Revises: e42f7c1d9a30
Create Date: 2026-08-24
"""

from typing import Sequence, Union

from alembic import op


revision: str = "9b7c31f2a640"
down_revision: Union[str, None] = "e42f7c1d9a30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("personalized_report") as batch_op:
        batch_op.create_unique_constraint(
            "uq_personalized_report_user_date",
            ["user_id", "report_date"],
        )


def downgrade() -> None:
    with op.batch_alter_table("personalized_report") as batch_op:
        batch_op.drop_constraint("uq_personalized_report_user_date", type_="unique")
