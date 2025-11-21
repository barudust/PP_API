from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# === Producto ===
class ProductoIn(BaseModel):
    nombre: str
    marca_id: Optional[int] = None   # <-- cambio aquí
    categoria_id: Optional[int] = None
    subcategoria_id: Optional[int] = None
    especie_id: Optional[int] = None   # <-- agregado
    etapa_id: Optional[int] = None     # <-- agregado
    linea_id: Optional[int] = None     # <-- agregado
    unidad: Optional[str] = None
    peso_bulto_kg: Optional[int] = None
    precio_unitario: Optional[float] = None

class Producto(ProductoIn):
    id: int

# === Inventario ===

class InventarioIn(BaseModel):
    producto_id: int
    sucursal_id: int
    cantidad: int

class Inventario(BaseModel):
    id: int
    producto_id: int
    sucursal_id: int
    cantidad: int
    fecha_actualizacion: str  # 👈 solo string (YYYY-MM-DD)

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        # 👇 formateamos la fecha como string limpio
        return cls(
            id=obj.id,
            producto_id=obj.producto_id,
            sucursal_id=obj.sucursal_id,
            cantidad=obj.cantidad,
            fecha_actualizacion=obj.fecha_actualizacion.date().isoformat()
        )


# === Categoría ===
class CategoriaIn(BaseModel):
    nombre: str

class Categoria(CategoriaIn):
    id: int

# === Subcategoría ===
class SubcategoriaIn(BaseModel):
    nombre: str
    categoria_id: int

class Subcategoria(SubcategoriaIn):
    id: int


# === Sucursal ===
class SucursalIn(BaseModel):
    nombre: str
    direccion: Optional[str] = None

class SucursalOut(SucursalIn):
    id: int

class IngresoInventarioIn(BaseModel):
    producto_id: int
    sucursal_id: int
    cantidad: int
    usuario_id: int
    

class IngresoInventario(IngresoInventarioIn):
    id: int
    fecha_actualizacion: datetime


class UsuarioIn(BaseModel):
    nombre: str
    contrasena_hash: str
    rol: str
    sucursal_id: int

class Usuario(UsuarioIn):
    id: int

class VentaIn(BaseModel):
    sucursal_id: int
    usuario_id: int
    total: float

class Venta(VentaIn):
    id: int
    fecha: datetime

class VentaDetalleIn(BaseModel):
    venta_id: int
    producto_id: int
    cantidad: int
    precio_unitario: float

class VentaDetalle(VentaDetalleIn):
    id: int


# === MARCAS ===
class MarcaIn(BaseModel):
    nombre: str

class Marca(MarcaIn):
    id: int


# === ESPECIES ===
class EspecieIn(BaseModel):
    nombre: str

class Especie(EspecieIn):
    id: int


# === ETAPAS ===
class EtapaIn(BaseModel):
    nombre: str

class Etapa(EtapaIn):
    id: int


# === LÍNEAS DE PRODUCTOS ===
class LineaIn(BaseModel):
    nombre: str

class Linea(LineaIn):
    id: int