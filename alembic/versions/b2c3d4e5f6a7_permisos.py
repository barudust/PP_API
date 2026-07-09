"""fase6: sistema de permisos (RBAC asignable a roles)

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "permiso",
        sa.Column("codigo", sa.Text(), nullable=False),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("grupo", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("codigo"),
    )
    op.create_table(
        "rol_permiso",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rol", sa.Text(), nullable=False),
        sa.Column("permiso_codigo", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["permiso_codigo"], ["permiso.codigo"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rol", "permiso_codigo", name="uq_rol_permiso"),
    )
    op.create_index("ix_rol_permiso_rol", "rol_permiso", ["rol"])


def downgrade() -> None:
    op.drop_index("ix_rol_permiso_rol", table_name="rol_permiso")
    op.drop_table("rol_permiso")
    op.drop_table("permiso")
