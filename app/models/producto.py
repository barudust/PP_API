"""Producto: el núcleo del catálogo (modelo híbrido relacional + JSONB)."""
from sqlalchemy import Table, Column, Integer, Text, Numeric, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import text

from .base import metadata

producto = Table(
    "producto",
    metadata,
    Column("id", Integer, primary_key=True),

    # Identificación
    Column("nombre", Text, nullable=False),
    Column("tipo_producto", Text, nullable=False, server_default="Alimento"),
    Column("sku", Text, unique=True, nullable=True),
    Column("codigo_barras", Text, nullable=True),
    Column("descripcion", Text, nullable=True),

    # Clasificación relacional (dimensiones de alto valor para KPIs / joins)
    Column("marca_id", Integer, ForeignKey("marca.id")),
    Column("categoria_id", Integer, ForeignKey("categoria.id")),
    Column("subcategoria_id", Integer, ForeignKey("subcategoria.id")),
    Column("especie_id", Integer, ForeignKey("especie.id")),
    Column("etapa_id", Integer, ForeignKey("etapa.id")),

    # Atributos dinámicos por tipo de producto (modelo híbrido — ADR-005)
    # Ej. Alimento: {"linea":"Premium","sabor":"Salmón"} · Accesorio: {"talla":"G"}
    Column("atributos_extra", JSONB, nullable=False, server_default=text("'{}'::jsonb")),

    # Ubicación física para el barrido de auditoría (pasillo/estante)
    Column("ubicacion_fisica", Text, nullable=True),

    # Lógica de Peso y Venta
    Column("unidad_medida", Text, nullable=False, server_default="pza"),
    Column("contenido_neto", Numeric(10, 3), nullable=False, server_default="1.0"),
    Column("se_vende_a_granel", Boolean, nullable=False, server_default="false"),

    # Tolerancia de variación de fábrica por empaque (misma unidad base, ej. kg).
    # Ej. bulto de 40kg con ±0.250kg de variación → 0.250
    Column("tolerancia_unidad", Numeric(12, 3), nullable=False, server_default="0"),

    # Precios Diferenciados
    Column("precio_base", Numeric(10, 2), nullable=False),
    Column("precio_granel", Numeric(10, 2), nullable=True),

    Column("activo", Boolean, default=True),  # Soft Delete
    Column("stock_minimo", Numeric(12, 3), default=5.0),
)
