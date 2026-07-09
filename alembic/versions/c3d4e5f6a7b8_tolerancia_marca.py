"""fase7: tolerancia de fabrica asimetrica por marca

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("marca", sa.Column("tolerancia_bajo", sa.Numeric(12, 3), server_default="0", nullable=False))
    op.add_column("marca", sa.Column("tolerancia_alto", sa.Numeric(12, 3), server_default="0", nullable=False))


def downgrade() -> None:
    op.drop_column("marca", "tolerancia_alto")
    op.drop_column("marca", "tolerancia_bajo")
