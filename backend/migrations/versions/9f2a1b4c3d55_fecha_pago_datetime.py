"""Change pagos.fecha_pago to datetime.

Revision ID: 9f2a1b4c3d55
Revises: 388c17d81ee0
Create Date: 2026-05-19 05:46:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9f2a1b4c3d55"
down_revision = "388c17d81ee0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "pagos",
        "fecha_pago",
        type_=sa.DateTime(),
        existing_type=sa.Date(),
        postgresql_using="fecha_pago::timestamp",
    )


def downgrade() -> None:
    op.alter_column(
        "pagos",
        "fecha_pago",
        type_=sa.Date(),
        existing_type=sa.DateTime(),
        postgresql_using="fecha_pago::date",
    )
