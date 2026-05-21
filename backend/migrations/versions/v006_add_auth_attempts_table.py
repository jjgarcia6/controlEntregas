"""add_auth_attempts_table

Revision ID: v006
Revises: c3d4e5f6a7b8
Create Date: 2026-05-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "v006"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auth_attempts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    # Index to support fast windowed counts by key
    op.create_index(
        "idx_auth_attempts_lookup",
        "auth_attempts",
        ["key", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("idx_auth_attempts_lookup", table_name="auth_attempts")
    op.drop_table("auth_attempts")
