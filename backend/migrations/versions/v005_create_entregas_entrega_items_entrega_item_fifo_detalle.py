"""create_entregas_entrega_items_entrega_item_fifo_detalle

Revision ID: v005
Revises: v004
Create Date: 2026-05-17

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "v005"
down_revision: Union[str, None] = "v004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

estado_entrega_enum = sa.Enum("activa", "eliminada", name="estado_entrega")


def upgrade() -> None:
    op.execute("CREATE SEQUENCE IF NOT EXISTS entregas_numero_seq START 1 INCREMENT 1")

    op.create_table(
        "entregas",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "numero",
            sa.Integer(),
            server_default=sa.text("nextval('entregas_numero_seq')"),
            nullable=False,
        ),
        sa.Column("destinatario_id", sa.UUID(), nullable=False),
        sa.Column("snap_identificacion", sa.String(length=13), nullable=False),
        sa.Column("snap_nombre", sa.String(length=255), nullable=False),
        sa.Column("snap_direccion", sa.Text(), nullable=False),
        sa.Column("snap_telefono", sa.String(length=20), nullable=False),
        sa.Column("comentarios", sa.String(length=255), nullable=True),
        sa.Column("total_entrega", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("saldo_pendiente", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "estado", estado_entrega_enum, nullable=False, server_default="activa"
        ),
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
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.ForeignKeyConstraint(["destinatario_id"], ["destinatarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("numero"),
    )
    op.create_index(
        "ix_entregas_destinatario_id", "entregas", ["destinatario_id"], unique=False
    )
    op.create_index("ix_entregas_estado", "entregas", ["estado"], unique=False)

    op.create_table(
        "entrega_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("entrega_id", sa.UUID(), nullable=False),
        sa.Column("producto_id", sa.UUID(), nullable=False),
        sa.Column("xml_item_id", sa.UUID(), nullable=False),
        sa.Column("cantidad", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column(
            "peso_total",
            sa.Numeric(precision=12, scale=4),
            nullable=False,
            server_default="0",
        ),
        sa.Column("costo_unitario", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("costo_total", sa.Numeric(precision=12, scale=2), nullable=False),
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
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.ForeignKeyConstraint(["entrega_id"], ["entregas.id"]),
        sa.ForeignKeyConstraint(["kardex_movimiento_id"], ["kardex_movimientos.id"]),
        sa.ForeignKeyConstraint(["producto_id"], ["productos.id"]),
        sa.ForeignKeyConstraint(["xml_item_id"], ["xml_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("kardex_movimiento_id"),
    )

    op.create_table(
        "entrega_item_fifo_detalle",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("entrega_item_id", sa.UUID(), nullable=False),
        sa.Column("kardex_ingreso_id", sa.UUID(), nullable=False),
        sa.Column(
            "cantidad_consumida", sa.Numeric(precision=12, scale=4), nullable=False
        ),
        sa.Column("costo_unitario", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.ForeignKeyConstraint(["entrega_item_id"], ["entrega_items.id"]),
        sa.ForeignKeyConstraint(["kardex_ingreso_id"], ["kardex_movimientos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("entrega_item_fifo_detalle")
    op.drop_table("entrega_items")
    op.drop_index("ix_entregas_estado", table_name="entregas")
    op.drop_index("ix_entregas_destinatario_id", table_name="entregas")
    op.drop_table("entregas")
    op.execute("DROP SEQUENCE IF EXISTS entregas_numero_seq")
    estado_entrega_enum.drop(op.get_bind(), checkfirst=True)
