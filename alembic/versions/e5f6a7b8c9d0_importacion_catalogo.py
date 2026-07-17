"""fase11: importacion de catalogo (excel/xml), costo y margen por marca/producto

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- marca: margen de venta por defecto (%) ---
    op.add_column(
        "marca",
        sa.Column("margen_default", sa.Numeric(6, 3), nullable=False, server_default="0"),
    )

    # --- producto: costo de compra (solo visible con permiso) + excepción de margen ---
    op.add_column("producto", sa.Column("costo", sa.Numeric(10, 2), nullable=True))
    op.add_column("producto", sa.Column("margen_override", sa.Numeric(6, 3), nullable=True))

    # --- importacion_lote: una corrida de importación (un archivo subido) ---
    op.create_table(
        "importacion_lote",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo", sa.Text(), nullable=False),  # 'excel_catalogo' | 'xml_factura'
        sa.Column("nombre_archivo", sa.Text(), nullable=False),
        sa.Column("proveedor", sa.Text(), nullable=True),  # Emisor del CFDI, si es XML
        sa.Column("marca_default_id", sa.Integer(), sa.ForeignKey("marca.id"), nullable=True),
        sa.Column("estado", sa.Text(), nullable=False, server_default="revision"),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("fecha_confirmacion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("generar_ingreso", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sucursal_id", sa.Integer(), sa.ForeignKey("sucursal.id"), nullable=True),
    )

    # --- importacion_linea: cada fila parseada, pendiente de revisión ---
    op.create_table(
        "importacion_linea",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "lote_id", sa.Integer(),
            sa.ForeignKey("importacion_lote.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nombre_original", sa.Text(), nullable=False),
        sa.Column("categoria_sugerida", sa.Text(), nullable=True),  # solo Excel "bloques"
        sa.Column("cantidad", sa.Numeric(12, 3), nullable=True),  # solo XML
        sa.Column("contenido_neto", sa.Numeric(10, 3), nullable=True),  # solo Excel "tabla" (ej. Kg del bulto)
        sa.Column("precio_costo", sa.Numeric(10, 2), nullable=True),  # costo unitario ya con descuento
        sa.Column("codigo_sat", sa.Text(), nullable=True),
        sa.Column("codigo_proveedor", sa.Text(), nullable=True),
        sa.Column("marca_id", sa.Integer(), sa.ForeignKey("marca.id"), nullable=True),
        sa.Column("producto_match_id", sa.Integer(), sa.ForeignKey("producto.id"), nullable=True),
        sa.Column("match_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("margen_aplicado", sa.Numeric(6, 3), nullable=True),
        sa.Column("precio_venta_sugerido", sa.Numeric(10, 2), nullable=True),
        sa.Column("actualizar_precio", sa.Boolean(), nullable=False, server_default="false"),
        # 'pendiente' | 'crear' | 'vincular' | 'ignorar'
        sa.Column("decision", sa.Text(), nullable=False, server_default="pendiente"),
        sa.Column("producto_creado_id", sa.Integer(), sa.ForeignKey("producto.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("importacion_linea")
    op.drop_table("importacion_lote")
    op.drop_column("producto", "margen_override")
    op.drop_column("producto", "costo")
    op.drop_column("marca", "margen_default")
