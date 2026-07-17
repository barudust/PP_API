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
from .producto import ProductoIn, Producto, ProductoUpdate, HistorialPrecioProducto
from .inventario import (
    InventarioIn, Inventario,
    IngresoInventarioIn, IngresoInventario,
    IngresoInventarioLoteIn, IngresoInventarioLoteResumen, IngresoInventarioLoteDetalle,
    AjusteInventarioIn, AjusteInventario,
    HistorialInventario,
)
from .ventas import (
    VentaIn, Venta,
    VentaDetalleIn, VentaDetalle,
    ReglaDescuentoIn, ReglaDescuento,
)
from .importacion import (
    LineaImportacion, LineaImportacionUpdate,
    LoteImportacion, LoteImportacionDetalle,
    ConfirmarLoteIn, ConfirmarLoteResumen,
)
from .configuracion import ConfiguracionNegocio, ConfiguracionNegocioIn
from .lista_plantilla import (
    ListaPlantillaFila, ListaPlantillaFilaIn, ListaPlantillaFilaUpdate,
    ReordenarIn, ListaPlantillaFilaResuelta, ListaPlantillaMarca, ImportarPlantillaResumen,
)

__all__ = [
    "CategoriaIn", "Categoria", "SubcategoriaIn", "Subcategoria",
    "MarcaIn", "Marca", "EspecieIn", "Especie", "EtapaIn", "Etapa",
    "TipoProductoIn", "TipoProducto",
    "SucursalIn", "SucursalOut", "ClienteIn", "Cliente",
    "UsuarioIn", "Usuario", "UsuarioUpdate", "CambioPassword",
    "ProductoIn", "Producto", "ProductoUpdate", "HistorialPrecioProducto",
    "InventarioIn", "Inventario", "IngresoInventarioIn", "IngresoInventario",
    "IngresoInventarioLoteIn", "IngresoInventarioLoteResumen", "IngresoInventarioLoteDetalle",
    "AjusteInventarioIn", "AjusteInventario", "HistorialInventario",
    "VentaIn", "Venta", "VentaDetalleIn", "VentaDetalle",
    "ReglaDescuentoIn", "ReglaDescuento",
    "LineaImportacion", "LineaImportacionUpdate",
    "LoteImportacion", "LoteImportacionDetalle",
    "ConfirmarLoteIn", "ConfirmarLoteResumen",
    "ConfiguracionNegocio", "ConfiguracionNegocioIn",
    "ListaPlantillaFila", "ListaPlantillaFilaIn", "ListaPlantillaFilaUpdate",
    "ReordenarIn", "ListaPlantillaFilaResuelta", "ListaPlantillaMarca", "ImportarPlantillaResumen",
]
