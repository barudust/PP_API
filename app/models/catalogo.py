"""Catálogos simples de clasificación (dimensiones para filtros y KPIs)."""
from sqlalchemy import Table, Column, Integer, Text, Numeric, ForeignKey

from .base import metadata

categoria = Table(
    "categoria",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False, unique=True),
)

subcategoria = Table(
    "subcategoria",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False),
    Column("categoria_id", Integer, ForeignKey("categoria.id", ondelete="CASCADE")),
)

marca = Table(
    "marca",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False, unique=True),
    # Tolerancia de variación de fábrica por empaque (unidad base, ej. kg).
    # Asimétrica: cuánto puede FALTAR y cuánto puede SOBRAR por bulto según la
    # empresa. Ej: una marca cuyos bultos llegan con hasta -0.5kg -> bajo=0.5, alto=0.
    Column("tolerancia_bajo", Numeric(12, 3), nullable=False, server_default="0"),
    Column("tolerancia_alto", Numeric(12, 3), nullable=False, server_default="0"),
)

especie = Table(
    "especie",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False, unique=True),
)

etapa = Table(
    "etapa",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False, unique=True),
)

tipo_producto = Table(
    "tipo_producto",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", Text, nullable=False, unique=True),
)
