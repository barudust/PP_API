"""Entidades de organización: sucursales, usuarios y clientes."""
from sqlalchemy import Table, Column, Integer, Text, ForeignKey

from .base import metadata

sucursal = Table(
    "sucursal",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False, unique=True),
    Column("direccion", Text, nullable=True),
)

usuario = Table(
    "usuario",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False),
    Column("contrasena_hash", Text, nullable=False),
    Column("rol", Text, nullable=False),  # 'vendedor' | 'gerente' | 'superadmin'
    Column("sucursal_id", Integer, ForeignKey("sucursal.id", ondelete="CASCADE")),
)

cliente = Table(
    "cliente",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False),
    Column("telefono", Text),
    Column("direccion", Text),
    Column("notas", Text),  # "Amigo del dueño", "Cliente Frecuente", etc.
    # Los clientes son propios de una sucursal (no compradores globales): si el
    # mismo comprador va a otra sucursal, se registra ahí como cliente nuevo.
    Column("sucursal_id", Integer, ForeignKey("sucursal.id", ondelete="CASCADE"), nullable=False),
)
