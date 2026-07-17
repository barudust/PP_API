"""Configuración básica del negocio (fila única) — nombre, dirección, etc.
usados en tickets y reportes en vez de texto fijo en el código."""
from sqlalchemy import Table, Column, Integer, Text

from .base import metadata

configuracion_negocio = Table(
    "configuracion_negocio",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False, server_default="Punto Peludo"),
    Column("direccion", Text, nullable=True),
    Column("telefono", Text, nullable=True),
    Column("rfc", Text, nullable=True),
)
