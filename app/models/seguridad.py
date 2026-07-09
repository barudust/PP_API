"""Modelo de permisos (RBAC asignable a roles)."""
from sqlalchemy import Table, Column, Integer, Text, ForeignKey, UniqueConstraint

from .base import metadata

# Catálogo maestro de permisos
permiso = Table(
    "permiso",
    metadata,
    Column("codigo", Text, primary_key=True),  # ej. "pos.vender"
    Column("nombre", Text, nullable=False),
    Column("grupo", Text, nullable=False),
)

# Relación rol -> permiso (el rol es el string de `usuario.rol`)
rol_permiso = Table(
    "rol_permiso",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("rol", Text, nullable=False),
    Column("permiso_codigo", Text, ForeignKey("permiso.codigo", ondelete="CASCADE"), nullable=False),
    UniqueConstraint("rol", "permiso_codigo", name="uq_rol_permiso"),
)
