"""ingreso de inventario por lista (lote) para poder auditarlo como grupo

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-07-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, Sequence[str], None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ingreso_inventario_lote",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("sucursal_id", sa.Integer(), sa.ForeignKey("sucursal.id", ondelete="CASCADE"), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False),
        sa.Column("proveedor", sa.Text(), nullable=True),
        sa.Column("nota", sa.Text(), nullable=True),
    )
    op.add_column(
        "ingreso_inventario",
        sa.Column("lote_id", sa.Integer(), sa.ForeignKey("ingreso_inventario_lote.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_ingreso_inventario_lote_id", "ingreso_inventario", ["lote_id"])


def downgrade() -> None:
    op.drop_index("ix_ingreso_inventario_lote_id", table_name="ingreso_inventario")
    op.drop_column("ingreso_inventario", "lote_id")
    op.drop_table("ingreso_inventario_lote")
