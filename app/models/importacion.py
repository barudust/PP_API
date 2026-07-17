"""Importación de catálogo desde Excel o factura XML (CFDI) — ADR-015."""
from sqlalchemy import Table, Column, Integer, Text, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func

from .base import metadata

# Una corrida de importación: un archivo subido, con sus líneas pendientes
# de revisión antes de tocar el catálogo real.
importacion_lote = Table(
    "importacion_lote",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("tipo", Text, nullable=False),  # 'excel_catalogo' | 'xml_factura'
    Column("nombre_archivo", Text, nullable=False),
    Column("proveedor", Text, nullable=True),  # Emisor del CFDI, si es XML
    Column("marca_default_id", Integer, ForeignKey("marca.id"), nullable=True),
    Column("estado", Text, nullable=False, server_default="revision"),
    Column("usuario_id", Integer, ForeignKey("usuario.id"), nullable=False),
    Column("fecha", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("fecha_confirmacion", DateTime(timezone=True), nullable=True),
    Column("generar_ingreso", Boolean, nullable=False, server_default="false"),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id"), nullable=True),
)

# Cada fila parseada del archivo, con la decisión del dueño (crear/vincular/ignorar).
importacion_linea = Table(
    "importacion_linea",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("lote_id", Integer, ForeignKey("importacion_lote.id", ondelete="CASCADE"), nullable=False),
    Column("nombre_original", Text, nullable=False),
    Column("categoria_sugerida", Text, nullable=True),  # solo Excel "bloques de categoría"
    Column("cantidad", Numeric(12, 3), nullable=True),  # solo XML
    Column("contenido_neto", Numeric(10, 3), nullable=True),  # solo Excel "tabla" (ej. Kg del bulto)
    Column("precio_costo", Numeric(10, 2), nullable=True),  # costo unitario ya con descuento aplicado
    Column("codigo_sat", Text, nullable=True),
    Column("codigo_proveedor", Text, nullable=True),
    Column("marca_id", Integer, ForeignKey("marca.id"), nullable=True),
    Column("producto_match_id", Integer, ForeignKey("producto.id"), nullable=True),
    Column("match_score", Numeric(5, 2), nullable=True),
    Column("margen_aplicado", Numeric(6, 3), nullable=True),
    Column("precio_venta_sugerido", Numeric(10, 2), nullable=True),
    Column("actualizar_precio", Boolean, nullable=False, server_default="false"),
    # 'pendiente' | 'crear' | 'vincular' | 'ignorar'
    Column("decision", Text, nullable=False, server_default="pendiente"),
    Column("producto_creado_id", Integer, ForeignKey("producto.id"), nullable=True),
)
