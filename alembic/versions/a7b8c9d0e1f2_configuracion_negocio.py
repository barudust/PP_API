"""configuracion basica del negocio (fila unica): nombre, direccion, telefono, rfc

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-07-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "configuracion_negocio",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.Text(), nullable=False, server_default="Punto Peludo"),
        sa.Column("direccion", sa.Text(), nullable=True),
        sa.Column("telefono", sa.Text(), nullable=True),
        sa.Column("rfc", sa.Text(), nullable=True),
    )
    # Fila única (id=1) — el router siempre lee/actualiza este id, así el
    # GET nunca tiene que manejar el caso "todavía no existe configuración".
    op.execute("INSERT INTO configuracion_negocio (id, nombre) VALUES (1, 'Punto Peludo')")


def downgrade() -> None:
    op.drop_table("configuracion_negocio")
