"""create_xmls_xml_items_productos

Revision ID: v003
Revises: v002
Create Date: 2026-05-13 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "v003"
down_revision: Union[str, None] = "v002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

AUDIT_COLS = [
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
]


def upgrade() -> None:
    # 1. Create xmls table (no AuditMixin FKs inline — added via ALTER below)
    op.create_table(
        "xmls",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("clave_acceso", sa.String(49), nullable=False),
        sa.Column("ruc_emisor", sa.String(13), nullable=False),
        sa.Column("razon_social_emisor", sa.String(300), nullable=False),
        sa.Column("nombre_comercial", sa.String(300), nullable=True),
        sa.Column("numero_factura", sa.String(20), nullable=False),
        sa.Column("fecha_emision", sa.Date(), nullable=False),
        sa.Column("direccion_emisor", sa.Text(), nullable=True),
        sa.Column("tipo_emision", sa.SmallInteger(), nullable=False),
        sa.Column("ambiente", sa.SmallInteger(), nullable=False),
        sa.Column("ruc_comprador", sa.String(13), nullable=False),
        sa.Column("razon_social_comprador", sa.String(300), nullable=False),
        sa.Column("direccion_comprador", sa.Text(), nullable=True),
        sa.Column("total_sin_impuestos", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "total_descuento",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "subtotal_iva_0",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "subtotal_gravado",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "valor_iva",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("importe_total", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "moneda",
            sa.String(10),
            nullable=False,
            server_default=sa.text("'DOLAR'"),
        ),
        sa.Column("xml_raw", sa.Text(), nullable=False),
        *AUDIT_COLS,
    )

    # 2. Create productos table (no AuditMixin FKs inline)
    op.create_table(
        "productos",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("codigo_principal", sa.String(50), nullable=False),
        sa.Column("descripcion", sa.String(300), nullable=False),
        sa.Column("unidad_medida", sa.String(20), nullable=True),
        sa.Column(
            "peso_unitario",
            sa.Numeric(12, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "saldo_cantidad",
            sa.Numeric(12, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "saldo_valor",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        *AUDIT_COLS,
    )

    # 3. Create xml_items table (FK to xmls inline; AuditMixin FKs via ALTER below)
    op.create_table(
        "xml_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("xml_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("codigo_principal", sa.String(50), nullable=False),
        sa.Column("codigo_auxiliar", sa.String(50), nullable=True),
        sa.Column("descripcion", sa.String(300), nullable=False),
        sa.Column("cantidad_documento", sa.Numeric(12, 4), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(12, 4), nullable=False),
        sa.Column(
            "descuento",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("precio_total_sin_imp", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "tarifa_iva",
            sa.Numeric(5, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "valor_iva",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "peso_documento",
            sa.Numeric(12, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "peso_unitario",
            sa.Numeric(12, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "cantidad_ingresada",
            sa.Numeric(12, 4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("cantidad_pendiente", sa.Numeric(12, 4), nullable=False),
        *AUDIT_COLS,
        sa.ForeignKeyConstraint(
            ["xml_id"], ["xmls.id"], name="fk_xml_items_xml_id_xmls"
        ),
    )

    # 4–6. Indexes
    op.create_index("ix_xmls_clave_acceso", "xmls", ["clave_acceso"], unique=True)
    op.create_index("ix_xmls_fecha_emision", "xmls", ["fecha_emision"], unique=False)
    op.create_index("ix_xmls_ruc_emisor", "xmls", ["ruc_emisor"], unique=False)

    op.create_index(
        "ix_xml_items_xml_id_codigo",
        "xml_items",
        ["xml_id", "codigo_principal"],
        unique=False,
    )
    op.create_index(
        "ix_xml_items_codigo_principal", "xml_items", ["codigo_principal"], unique=False
    )

    op.create_index(
        "ix_productos_codigo_principal", "productos", ["codigo_principal"], unique=True
    )

    # 7. AuditMixin FK constraints for xmls
    op.create_foreign_key(
        "fk_xmls_created_by_usuarios", "xmls", "usuarios", ["created_by"], ["id"]
    )
    op.create_foreign_key(
        "fk_xmls_updated_by_usuarios", "xmls", "usuarios", ["updated_by"], ["id"]
    )
    op.create_foreign_key(
        "fk_xmls_deleted_by_usuarios", "xmls", "usuarios", ["deleted_by"], ["id"]
    )

    # 8. AuditMixin FK constraints for xml_items
    op.create_foreign_key(
        "fk_xml_items_created_by_usuarios",
        "xml_items",
        "usuarios",
        ["created_by"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_xml_items_updated_by_usuarios",
        "xml_items",
        "usuarios",
        ["updated_by"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_xml_items_deleted_by_usuarios",
        "xml_items",
        "usuarios",
        ["deleted_by"],
        ["id"],
    )

    # 9. AuditMixin FK constraints for productos
    op.create_foreign_key(
        "fk_productos_created_by_usuarios",
        "productos",
        "usuarios",
        ["created_by"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_productos_updated_by_usuarios",
        "productos",
        "usuarios",
        ["updated_by"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_productos_deleted_by_usuarios",
        "productos",
        "usuarios",
        ["deleted_by"],
        ["id"],
    )


def downgrade() -> None:
    # Drop AuditMixin FK constraints — productos first
    op.drop_constraint(
        "fk_productos_deleted_by_usuarios", "productos", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_productos_updated_by_usuarios", "productos", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_productos_created_by_usuarios", "productos", type_="foreignkey"
    )

    # Drop AuditMixin FK constraints — xml_items
    op.drop_constraint(
        "fk_xml_items_deleted_by_usuarios", "xml_items", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_xml_items_updated_by_usuarios", "xml_items", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_xml_items_created_by_usuarios", "xml_items", type_="foreignkey"
    )

    # Drop AuditMixin FK constraints — xmls
    op.drop_constraint("fk_xmls_deleted_by_usuarios", "xmls", type_="foreignkey")
    op.drop_constraint("fk_xmls_updated_by_usuarios", "xmls", type_="foreignkey")
    op.drop_constraint("fk_xmls_created_by_usuarios", "xmls", type_="foreignkey")

    # Drop indexes
    op.drop_index("ix_productos_codigo_principal", table_name="productos")
    op.drop_index("ix_xml_items_codigo_principal", table_name="xml_items")
    op.drop_index("ix_xml_items_xml_id_codigo", table_name="xml_items")
    op.drop_index("ix_xmls_ruc_emisor", table_name="xmls")
    op.drop_index("ix_xmls_fecha_emision", table_name="xmls")
    op.drop_index("ix_xmls_clave_acceso", table_name="xmls")

    # Drop tables in reverse FK dependency order
    op.drop_table("xml_items")
    op.drop_table("productos")
    op.drop_table("xmls")
