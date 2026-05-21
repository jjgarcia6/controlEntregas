"""Widen PII columns to TEXT and add identificacion_hash for deterministic lookups.

Column types expand to TEXT to hold Fernet ciphertext (~100-500 bytes base64).
The old unique constraint on identificacion is replaced by one on identificacion_hash.
Run scripts/encrypt_existing_data.py after applying this migration to re-encrypt
existing plaintext rows and populate identificacion_hash.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-20
"""

from alembic import op
import sqlalchemy as sa

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- destinatarios ---
    op.drop_index(
        "ix_destinatarios_identificacion", table_name="destinatarios", if_exists=True
    )
    op.drop_constraint(
        "destinatarios_identificacion_key", "destinatarios", type_="unique"
    )
    op.alter_column(
        "destinatarios", "identificacion", type_=sa.Text, existing_nullable=False
    )
    op.alter_column("destinatarios", "nombre", type_=sa.Text, existing_nullable=False)
    op.alter_column(
        "destinatarios", "direccion", type_=sa.Text, existing_nullable=False
    )
    op.alter_column("destinatarios", "telefono", type_=sa.Text, existing_nullable=False)
    op.alter_column("destinatarios", "email", type_=sa.Text, existing_nullable=True)
    op.add_column(
        "destinatarios",
        sa.Column("identificacion_hash", sa.String(64), nullable=True),
    )
    op.create_index(
        "ix_destinatarios_identificacion_hash", "destinatarios", ["identificacion_hash"]
    )
    op.create_unique_constraint(
        "uq_destinatarios_identificacion_hash", "destinatarios", ["identificacion_hash"]
    )

    # --- pagos ---
    op.alter_column("pagos", "nombre_titular", type_=sa.Text, existing_nullable=False)

    # --- entregas (snap PII fields) ---
    op.alter_column(
        "entregas", "snap_identificacion", type_=sa.Text, existing_nullable=False
    )
    op.alter_column("entregas", "snap_nombre", type_=sa.Text, existing_nullable=False)
    op.alter_column(
        "entregas", "snap_direccion", type_=sa.Text, existing_nullable=False
    )
    op.alter_column("entregas", "snap_telefono", type_=sa.Text, existing_nullable=False)


def downgrade() -> None:
    op.alter_column(
        "entregas", "snap_telefono", type_=sa.String(20), existing_nullable=False
    )
    op.alter_column(
        "entregas", "snap_direccion", type_=sa.Text, existing_nullable=False
    )
    op.alter_column(
        "entregas", "snap_nombre", type_=sa.String(255), existing_nullable=False
    )
    op.alter_column(
        "entregas", "snap_identificacion", type_=sa.String(13), existing_nullable=False
    )

    op.alter_column(
        "pagos", "nombre_titular", type_=sa.String(255), existing_nullable=False
    )

    op.drop_constraint(
        "uq_destinatarios_identificacion_hash", "destinatarios", type_="unique"
    )
    op.drop_index("ix_destinatarios_identificacion_hash", table_name="destinatarios")
    op.drop_column("destinatarios", "identificacion_hash")
    op.alter_column(
        "destinatarios", "email", type_=sa.String(255), existing_nullable=True
    )
    op.alter_column(
        "destinatarios", "telefono", type_=sa.String(20), existing_nullable=False
    )
    op.alter_column(
        "destinatarios", "direccion", type_=sa.Text, existing_nullable=False
    )
    op.alter_column(
        "destinatarios", "nombre", type_=sa.String(255), existing_nullable=False
    )
    op.alter_column(
        "destinatarios", "identificacion", type_=sa.String(13), existing_nullable=False
    )
    op.create_unique_constraint(
        "destinatarios_identificacion_key", "destinatarios", ["identificacion"]
    )
