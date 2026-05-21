"""create_kardex_movimientos_xml_item_ingresos

Revision ID: v004
Revises: v003
Create Date: 2026-05-13

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "v004"
down_revision: Union[str, None] = "v003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "kardex_movimientos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("producto_id", sa.UUID(), nullable=False),
        sa.Column(
            "tipo",
            sa.Enum("ingreso", "egreso", name="tipo_movimiento"),
            nullable=False,
        ),
        sa.Column(
            "origen",
            sa.Enum("xml", "entrega", "reversa_entrega", name="origen_movimiento"),
            nullable=False,
        ),
        sa.Column("documento_origen_id", sa.UUID(), nullable=False),
        sa.Column("fecha_movimiento", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("cantidad", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("peso_unitario", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("peso_total", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("costo_unitario", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("costo_total", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("saldo_cantidad", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("saldo_valor", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("lote_fifo_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.UUID(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["usuarios.id"],
            name="fk_created_by_usuarios",
            use_alter=True,
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by"],
            ["usuarios.id"],
            name="fk_deleted_by_usuarios",
            use_alter=True,
        ),
        sa.ForeignKeyConstraint(["lote_fifo_id"], ["kardex_movimientos.id"]),
        sa.ForeignKeyConstraint(["producto_id"], ["productos.id"]),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["usuarios.id"],
            name="fk_updated_by_usuarios",
            use_alter=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_kardex_movimientos_producto_fecha",
        "kardex_movimientos",
        ["producto_id", "fecha_movimiento"],
        unique=False,
    )
    op.create_table(
        "xml_item_ingresos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("xml_item_id", sa.UUID(), nullable=False),
        sa.Column(
            "cantidad_ingresada", sa.Numeric(precision=12, scale=4), nullable=False
        ),
        sa.Column("kardex_movimiento_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_by", sa.UUID(), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.UUID(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["usuarios.id"],
            name="fk_created_by_usuarios",
            use_alter=True,
        ),
        sa.ForeignKeyConstraint(
            ["deleted_by"],
            ["usuarios.id"],
            name="fk_deleted_by_usuarios",
            use_alter=True,
        ),
        sa.ForeignKeyConstraint(["kardex_movimiento_id"], ["kardex_movimientos.id"]),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["usuarios.id"],
            name="fk_updated_by_usuarios",
            use_alter=True,
        ),
        sa.ForeignKeyConstraint(["xml_item_id"], ["xml_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("kardex_movimiento_id"),
    )


def downgrade() -> None:
    op.drop_table("xml_item_ingresos")
    op.drop_index(
        "ix_kardex_movimientos_producto_fecha", table_name="kardex_movimientos"
    )
    op.drop_table("kardex_movimientos")
    sa.Enum(name="origen_movimiento").drop(op.get_bind(), checkfirst=False)
    sa.Enum(name="tipo_movimiento").drop(op.get_bind(), checkfirst=False)
