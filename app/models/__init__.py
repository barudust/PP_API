"""
Paquete de modelos (SQLAlchemy Core).

Re-exporta todas las tablas y la `metadata` compartida para conservar la API
histórica `from models import producto, venta, metadata, ...`.
"""
from .base import metadata

from .catalogo import (
    categoria,
    subcategoria,
    marca,
    especie,
    etapa,
    tipo_producto,
)
from .organizacion import (
    sucursal,
    usuario,
    cliente,
)
from .producto import producto
from .inventario import (
    inventario,
    ingreso_inventario,
    ajuste_inventario,
    historial_inventario,
)
from .ventas import (
    corte_caja,
    regla_descuento,
    venta,
    venta_detalle,
)
from .seguridad import permiso, rol_permiso

__all__ = [
    "metadata",
    "categoria", "subcategoria", "marca", "especie", "etapa", "tipo_producto",
    "sucursal", "usuario", "cliente",
    "producto",
    "inventario", "ingreso_inventario", "ajuste_inventario", "historial_inventario",
    "corte_caja", "regla_descuento", "venta", "venta_detalle",
    "permiso", "rol_permiso",
]
