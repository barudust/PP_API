"""
Paquete de schemas (Pydantic).

Re-exporta todos los modelos para conservar la API histórica
`from schemas import ProductoIn, Venta, ...`.
"""
from .catalogo import (
    CategoriaIn, Categoria,
    SubcategoriaIn, Subcategoria,
    MarcaIn, Marca,
    EspecieIn, Especie,
    EtapaIn, Etapa,
    TipoProductoIn, TipoProducto,
    SucursalIn, SucursalOut,
    ClienteIn, Cliente,
    UsuarioIn, Usuario, UsuarioUpdate, CambioPassword,
)
from .producto import ProductoIn, Producto, ProductoUpdate
from .inventario import (
    InventarioIn, Inventario,
    IngresoInventarioIn, IngresoInventario,
    AjusteInventarioIn, AjusteInventario,
    HistorialInventario,
)
from .ventas import (
    VentaIn, Venta,
    VentaDetalleIn, VentaDetalle,
    ReglaDescuentoIn, ReglaDescuento,
)

__all__ = [
    "CategoriaIn", "Categoria", "SubcategoriaIn", "Subcategoria",
    "MarcaIn", "Marca", "EspecieIn", "Especie", "EtapaIn", "Etapa",
    "TipoProductoIn", "TipoProducto",
    "SucursalIn", "SucursalOut", "ClienteIn", "Cliente",
    "UsuarioIn", "Usuario", "UsuarioUpdate", "CambioPassword",
    "ProductoIn", "Producto", "ProductoUpdate",
    "InventarioIn", "Inventario", "IngresoInventarioIn", "IngresoInventario",
    "AjusteInventarioIn", "AjusteInventario", "HistorialInventario",
    "VentaIn", "Venta", "VentaDetalleIn", "VentaDetalle",
    "ReglaDescuentoIn", "ReglaDescuento",
]
