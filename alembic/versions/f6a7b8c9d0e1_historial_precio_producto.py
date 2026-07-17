"""historial de costo/precio por producto (bitácora de cambios)

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "producto_historial_precio",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("producto_id", sa.Integer(), sa.ForeignKey("producto.id", ondelete="CASCADE"), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("costo_anterior", sa.Numeric(10, 2), nullable=True),
        sa.Column("costo_nuevo", sa.Numeric(10, 2), nullable=True),
        sa.Column("precio_anterior", sa.Numeric(10, 2), nullable=True),
        sa.Column("precio_nuevo", sa.Numeric(10, 2), nullable=True),
        sa.Column("origen", sa.Text(), nullable=False),  # 'manual' | 'importacion'
        sa.Column("lote_id", sa.Integer(), sa.ForeignKey("importacion_lote.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index(
        "ix_producto_historial_precio_producto_id",
        "producto_historial_precio",
        ["producto_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_producto_historial_precio_producto_id", table_name="producto_historial_precio")
    op.drop_table("producto_historial_precio")
