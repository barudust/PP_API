"""fase2: atributos JSONB, tolerancia, ubicacion, tipo_ajuste y trazabilidad de venta

Revision ID: a1b2c3d4e5f6
Revises: 6bf6ad8ecc19
Create Date: 2026-07-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "6bf6ad8ecc19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- producto: atributos dinámicos (híbrido) + auditoría ---
    op.add_column(
        "producto",
        sa.Column(
            "atributos_extra",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column("producto", sa.Column("ubicacion_fisica", sa.Text(), nullable=True))
    op.add_column(
        "producto",
        sa.Column(
            "tolerancia_unidad",
            sa.Numeric(precision=12, scale=3),
            server_default="0",
            nullable=False,
        ),
    )
    # Índice GIN para consultas de contención sobre JSONB
    op.create_index(
        "ix_producto_atributos_extra",
        "producto",
        ["atributos_extra"],
        postgresql_using="gin",
    )

    # --- ajuste_inventario: tipificación de la diferencia ---
    op.add_column(
        "ajuste_inventario", sa.Column("tipo_ajuste", sa.Text(), nullable=True)
    )

    # --- venta_detalle: trazabilidad de venta híbrida (arregla la cancelación) ---
    op.add_column(
        "venta_detalle",
        sa.Column(
            "es_granel", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
    )
    op.add_column(
        "venta_detalle",
        sa.Column("cantidad_base", sa.Numeric(precision=12, scale=3), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("venta_detalle", "cantidad_base")
    op.drop_column("venta_detalle", "es_granel")
    op.drop_column("ajuste_inventario", "tipo_ajuste")
    op.drop_index("ix_producto_atributos_extra", table_name="producto")
    op.drop_column("producto", "tolerancia_unidad")
    op.drop_column("producto", "ubicacion_fisica")
    op.drop_column("producto", "atributos_extra")
