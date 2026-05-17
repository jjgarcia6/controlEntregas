"""create_usuarios_bancos_destinatarios

Revision ID: v002
Revises: v001
Create Date: 2026-05-12 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "v002"
down_revision: Union[str, None] = "v001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create ENUM types (explicit, before table creation)
    op.execute("CREATE TYPE rol_usuario AS ENUM ('admin', 'operador', 'lectura')")
    op.execute("CREATE TYPE tipo_identificacion AS ENUM ('cedula', 'ruc')")

    # 2. Create usuarios table (must be first — bancos/destinatarios reference it via FKs)
    op.create_table(
        "usuarios",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column(
            "rol",
            postgresql.ENUM(
                "admin", "operador", "lectura", name="rol_usuario", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("ultimo_login", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("ip_ultimo_login", sa.String(45), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
    )
    op.create_unique_constraint("uq_usuarios_email", "usuarios", ["email"])

    # 3. Create bancos and destinatarios (without FK constraints inline)
    op.create_table(
        "bancos",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
    )

    op.create_table(
        "destinatarios",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tipo_identificacion",
            postgresql.ENUM("cedula", "ruc", name="tipo_identificacion", create_type=False),
            nullable=False,
        ),
        sa.Column("identificacion", sa.String(13), nullable=False),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("direccion", sa.Text(), nullable=False),
        sa.Column("telefono", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
    )

    # 4. Add unique indexes
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)
    op.create_index("ix_bancos_nombre", "bancos", ["nombre"], unique=True)
    op.create_index(
        "ix_destinatarios_identificacion", "destinatarios", ["identificacion"], unique=True
    )

    # 5. Add FK constraints for usuarios self-referencing audit fields
    op.create_foreign_key(
        "fk_usuarios_created_by_usuarios", "usuarios", "usuarios", ["created_by"], ["id"]
    )
    op.create_foreign_key(
        "fk_usuarios_updated_by_usuarios", "usuarios", "usuarios", ["updated_by"], ["id"]
    )
    op.create_foreign_key(
        "fk_usuarios_deleted_by_usuarios", "usuarios", "usuarios", ["deleted_by"], ["id"]
    )

    # 6. Add FK constraints for bancos audit fields
    op.create_foreign_key(
        "fk_bancos_created_by_usuarios", "bancos", "usuarios", ["created_by"], ["id"]
    )
    op.create_foreign_key(
        "fk_bancos_updated_by_usuarios", "bancos", "usuarios", ["updated_by"], ["id"]
    )
    op.create_foreign_key(
        "fk_bancos_deleted_by_usuarios", "bancos", "usuarios", ["deleted_by"], ["id"]
    )

    # 7. Add FK constraints for destinatarios audit fields
    op.create_foreign_key(
        "fk_destinatarios_created_by_usuarios",
        "destinatarios",
        "usuarios",
        ["created_by"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_destinatarios_updated_by_usuarios",
        "destinatarios",
        "usuarios",
        ["updated_by"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_destinatarios_deleted_by_usuarios",
        "destinatarios",
        "usuarios",
        ["deleted_by"],
        ["id"],
    )


def downgrade() -> None:
    # Drop FK constraints — destinatarios first
    op.drop_constraint(
        "fk_destinatarios_deleted_by_usuarios", "destinatarios", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_destinatarios_updated_by_usuarios", "destinatarios", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_destinatarios_created_by_usuarios", "destinatarios", type_="foreignkey"
    )

    # Drop FK constraints — bancos
    op.drop_constraint("fk_bancos_deleted_by_usuarios", "bancos", type_="foreignkey")
    op.drop_constraint("fk_bancos_updated_by_usuarios", "bancos", type_="foreignkey")
    op.drop_constraint("fk_bancos_created_by_usuarios", "bancos", type_="foreignkey")

    # Drop FK constraints — usuarios self-reference
    op.drop_constraint(
        "fk_usuarios_deleted_by_usuarios", "usuarios", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_usuarios_updated_by_usuarios", "usuarios", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_usuarios_created_by_usuarios", "usuarios", type_="foreignkey"
    )

    # Drop indexes
    op.drop_index("ix_destinatarios_identificacion", table_name="destinatarios")
    op.drop_index("ix_bancos_nombre", table_name="bancos")
    op.drop_index("ix_usuarios_email", table_name="usuarios")

    # Drop unique constraint
    op.drop_constraint("uq_usuarios_email", "usuarios", type_="unique")

    # Drop tables in reverse dependency order
    op.drop_table("destinatarios")
    op.drop_table("bancos")
    op.drop_table("usuarios")

    # Drop ENUM types
    op.execute("DROP TYPE tipo_identificacion")
    op.execute("DROP TYPE rol_usuario")
