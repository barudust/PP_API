"""Ventas, detalle de venta, corte de caja y reglas de descuento."""
from sqlalchemy import Table, Column, Integer, Text, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func

from .base import metadata

corte_caja = Table(
    "corte_caja",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id"), nullable=False),
    Column("usuario_id", Integer, ForeignKey("usuario.id"), nullable=False),

    Column("fecha_apertura", DateTime(timezone=True), server_default=func.now()),
    Column("fecha_cierre", DateTime(timezone=True), nullable=True),

    Column("fondo_inicial", Numeric(10, 2), nullable=False),
    Column("ventas_totales", Numeric(10, 2), default=0),
    Column("efectivo_esperado", Numeric(10, 2)),
    Column("efectivo_real", Numeric(10, 2)),
    Column("diferencia", Numeric(10, 2)),

    Column("monto_retirado", Numeric(10, 2), default=0),
    Column("fondo_siguiente", Numeric(10, 2), default=0),

    Column("comentarios", Text),
)

regla_descuento = Table(
    "regla_descuento",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("descripcion", Text, nullable=False),
    Column("descuento_porcentaje", Numeric(5, 2), nullable=False),

    Column("cliente_id", Integer, ForeignKey("cliente.id", ondelete="CASCADE")),
    Column("marca_id", Integer, ForeignKey("marca.id", ondelete="CASCADE")),
    Column("producto_id", Integer, ForeignKey("producto.id", ondelete="CASCADE")),

    Column("activo", Boolean, default=True),
)

venta = Table(
    "venta",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("sucursal_id", Integer, ForeignKey("sucursal.id", ondelete="CASCADE")),
    Column("usuario_id", Integer, ForeignKey("usuario.id", ondelete="CASCADE")),
    Column("cliente_id", Integer, ForeignKey("cliente.id", ondelete="SET NULL")),
    Column("corte_caja_id", Integer, ForeignKey("corte_caja.id")),

    Column("fecha", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("total", Numeric(10, 2), nullable=False),

    Column("descuento_especial_monto", Numeric(10, 2), default=0),
    Column("descuento_especial_motivo", Text),
)

venta_detalle = Table(
    "venta_detalle",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("venta_id", Integer, ForeignKey("venta.id", ondelete="CASCADE")),
    Column("producto_id", Integer, ForeignKey("producto.id", ondelete="CASCADE")),

    Column("cantidad", Numeric(12, 3), nullable=False),
    Column("precio_unitario", Numeric(10, 2), nullable=False),

    # Trazabilidad de la venta híbrida (evita adivinar al cancelar) — ADR/Fase 4
    Column("es_granel", Boolean, nullable=False, server_default="false"),
    Column("cantidad_base", Numeric(12, 3), nullable=True),  # unidad base descontada del stock
)
