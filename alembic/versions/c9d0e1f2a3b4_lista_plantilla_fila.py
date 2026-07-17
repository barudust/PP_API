"""lista_plantilla_fila: estructura editable de las plantillas graficas de Listas (Fase 16)

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-07-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lista_plantilla_fila",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("marca_id", sa.Integer(), sa.ForeignKey("marca.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hoja", sa.Text(), nullable=False, server_default="Hoja1"),
        sa.Column("panel", sa.Text(), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.Text(), nullable=False),
        sa.Column("nivel", sa.Integer(), nullable=True),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("producto_id", sa.Integer(), sa.ForeignKey("producto.id", ondelete="SET NULL"), nullable=True),
        sa.CheckConstraint("panel IN ('izq','der')", name="ck_lista_plantilla_fila_panel"),
        sa.CheckConstraint("tipo IN ('encabezado','producto')", name="ck_lista_plantilla_fila_tipo"),
    )
    op.create_index(
        "ix_lista_plantilla_fila_marca_hoja_panel_orden",
        "lista_plantilla_fila",
        ["marca_id", "hoja", "panel", "orden"],
    )


def downgrade() -> None:
    op.drop_index("ix_lista_plantilla_fila_marca_hoja_panel_orden", table_name="lista_plantilla_fila")
    op.drop_table("lista_plantilla_fila")
