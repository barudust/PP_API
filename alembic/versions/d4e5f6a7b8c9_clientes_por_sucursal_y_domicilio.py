"""fase10: clientes por sucursal, reglas de descuento por sucursal, venta a domicilio

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- cliente: ahora pertenece a una sucursal (no es global) ---
    op.add_column("cliente", sa.Column("sucursal_id", sa.Integer(), nullable=True))
    # Backfill: los clientes existentes se asignan a la primera sucursal registrada.
    op.execute(
        """
        UPDATE cliente
        SET sucursal_id = (SELECT id FROM sucursal ORDER BY id LIMIT 1)
        WHERE sucursal_id IS NULL
        """
    )
    op.alter_column("cliente", "sucursal_id", nullable=False)
    op.create_foreign_key(
        "fk_cliente_sucursal", "cliente", "sucursal", ["sucursal_id"], ["id"], ondelete="CASCADE"
    )

    # --- regla_descuento: opcionalmente acotada a una sucursal ---
    op.add_column("regla_descuento", sa.Column("sucursal_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_regla_descuento_sucursal", "regla_descuento", "sucursal", ["sucursal_id"], ["id"], ondelete="CASCADE"
    )

    # --- venta: tipo de entrega (tienda | domicilio) ---
    op.add_column(
        "venta",
        sa.Column("tipo_entrega", sa.Text(), server_default="tienda", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("venta", "tipo_entrega")
    op.drop_constraint("fk_regla_descuento_sucursal", "regla_descuento", type_="foreignkey")
    op.drop_column("regla_descuento", "sucursal_id")
    op.drop_constraint("fk_cliente_sucursal", "cliente", type_="foreignkey")
    op.drop_column("cliente", "sucursal_id")
