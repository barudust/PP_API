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
from .producto import producto, producto_historial_precio
from .inventario import (
    inventario,
    ingreso_inventario,
    ingreso_inventario_lote,
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
from .importacion import importacion_lote, importacion_linea
from .configuracion import configuracion_negocio
from .lista_plantilla import lista_plantilla_fila

__all__ = [
    "metadata",
    "categoria", "subcategoria", "marca", "especie", "etapa", "tipo_producto",
    "sucursal", "usuario", "cliente",
    "producto", "producto_historial_precio",
    "inventario", "ingreso_inventario", "ingreso_inventario_lote", "ajuste_inventario", "historial_inventario",
    "corte_caja", "regla_descuento", "venta", "venta_detalle",
    "permiso", "rol_permiso",
    "importacion_lote", "importacion_linea",
    "configuracion_negocio",
    "lista_plantilla_fila",
]
