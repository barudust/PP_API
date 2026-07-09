"""Inventario, ingresos, ajustes de auditoría e historial de movimientos."""
from sqlalchemy import Table, Column, Integer, Text, Numeric, DateTime, ForeignKey
from sqlalchemy.sql import func

from .base import metadata

# Stock actual (siempre en unidad base: kg / ml / pza suelta)
inventario = Table(
    "inventario",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("producto_id", Integer, ForeignKey("producto.id", ondelete="CASCADE")),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id", ondelete="CASCADE")),
    Column("cantidad", Numeric(12, 3), nullable=False, default=0),
    Column("fecha_actualizacion", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

# Registro de Compras / Ingresos
ingreso_inventario = Table(
    "ingreso_inventario",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("producto_id", Integer, ForeignKey("producto.id", ondelete="CASCADE")),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id", ondelete="CASCADE")),
    Column("cantidad", Numeric(12, 3), nullable=False),
    Column("usuario_id", Integer, ForeignKey("usuario.id", ondelete="CASCADE")),
    Column("fecha_actualizacion", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

# Auditoría física (conteo/pesaje real vs. sistema)
ajuste_inventario = Table(
    "ajuste_inventario",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id")),
    Column("usuario_id", Integer, ForeignKey("usuario.id")),
    Column("producto_id", Integer, ForeignKey("producto.id")),
    Column("fecha", DateTime(timezone=True), server_default=func.now()),

    Column("cantidad_sistema", Numeric(12, 3), nullable=False),
    Column("cantidad_fisica", Numeric(12, 3), nullable=False),
    Column("diferencia", Numeric(12, 3), nullable=False),

    # Tipificación de la diferencia (ver constants.TIPOS_AJUSTE):
    # MERMA_OPERATIVA | VARIACION_FABRICA | ERROR_SISTEMA | CADUCIDAD
    Column("tipo_ajuste", Text, nullable=True),
    Column("motivo", Text),  # nota libre adicional
)

# Bitácora completa de movimientos
historial_inventario = Table(
    "historial_inventario",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("fecha", DateTime(timezone=True), server_default=func.now()),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id"), nullable=False),
    Column("usuario_id", Integer, ForeignKey("usuario.id"), nullable=False),
    Column("producto_id", Integer, ForeignKey("producto.id"), nullable=False),
    Column("tipo_movimiento", Text, nullable=False),  # 'VENTA','COMPRA','AJUSTE',...
    Column("cantidad_anterior", Numeric(12, 3), nullable=False),
    Column("cantidad_movida", Numeric(12, 3), nullable=False),
    Column("cantidad_nueva", Numeric(12, 3), nullable=False),
    Column("motivo", Text),
)
