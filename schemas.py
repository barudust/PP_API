from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# === ATRIBUTOS (Sin cambios) ===
class CategoriaIn(BaseModel):
    nombre: str
class Categoria(CategoriaIn):
    id: int
class SubcategoriaIn(BaseModel):
    nombre: str
    categoria_id: int
class Subcategoria(SubcategoriaIn):
    id: int
class MarcaIn(BaseModel):
    nombre: str
class Marca(MarcaIn):
    id: int
class EspecieIn(BaseModel):
    nombre: str
class Especie(EspecieIn):
    id: int
class EtapaIn(BaseModel):
    nombre: str
class Etapa(EtapaIn):
    id: int
class LineaIn(BaseModel):
    nombre: str
class Linea(LineaIn):
    id: int
class SucursalIn(BaseModel):
    nombre: str
    direccion: Optional[str] = None
class SucursalOut(SucursalIn):
    id: int

# === CLIENTES ===
class ClienteIn(BaseModel):
    nombre: str
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    notas: Optional[str] = None
class Cliente(ClienteIn):
    id: int

# === PRODUCTO (ACTUALIZADO CON TU LÓGICA FINAL) ===
class ProductoIn(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    sku: Optional[str] = None
    codigo_barras: Optional[str] = None
    
    # Clasificación
    tipo_producto: str = "Alimento" 
    
    # Relaciones
    marca_id: Optional[int] = None
    categoria_id: Optional[int] = None
    subcategoria_id: Optional[int] = None
    especie_id: Optional[int] = None
    etapa_id: Optional[int] = None
    linea_id: Optional[int] = None
    
    # Lógica de Venta
    unidad_medida: str = "pza"
    contenido_neto: float = 1.0
    se_vende_a_granel: bool = False
    
    # Precios
    precio_base: float # Precio del paquete cerrado
    precio_granel: Optional[float] = None # Precio suelto (opcional)
    
    activo: bool = True

class Producto(ProductoIn):
    id: int

# === INVENTARIO ===
class InventarioIn(BaseModel):
    producto_id: int
    sucursal_id: int
    cantidad: float 

class Inventario(BaseModel):
    id: int
    producto_id: int
    sucursal_id: int
    cantidad: float 
    fecha_actualizacion: str 
    class Config:
        from_attributes = True
    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            producto_id=obj.producto_id,
            sucursal_id=obj.sucursal_id,
            cantidad=obj.cantidad,
            fecha_actualizacion=obj.fecha_actualizacion.date().isoformat()
        )

class IngresoInventarioIn(BaseModel):
    producto_id: int
    sucursal_id: int
    cantidad: float 
    usuario_id: int

class IngresoInventario(IngresoInventarioIn):
    id: int
    fecha_actualizacion: str 

# === AJUSTE INVENTARIO (AUDITORÍA) ===
class AjusteInventarioIn(BaseModel):
    sucursal_id: int
    usuario_id: int
    producto_id: int
    cantidad_sistema: float
    cantidad_fisica: float
    motivo: Optional[str] = None

class AjusteInventario(AjusteInventarioIn):
    id: int
    diferencia: float
    fecha: datetime

# === USUARIOS Y VENTAS ===
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
    cliente_id: Optional[int] = None 
    corte_caja_id: Optional[int] = None 
    total: float
    descuento_especial_monto: float = 0.0
    descuento_especial_motivo: Optional[str] = None

class Venta(VentaIn):
    id: int
    fecha: datetime

class VentaDetalleIn(BaseModel):
    venta_id: int
    producto_id: int
    cantidad: float
    precio_unitario: float
class VentaDetalle(VentaDetalleIn):
    id: int


class ReglaDescuentoIn(BaseModel):
    descripcion: str
    descuento_porcentaje: float
    cliente_id: Optional[int] = None
    marca_id: Optional[int] = None
    producto_id: Optional[int] = None
    activo: bool = True

class ReglaDescuento(ReglaDescuentoIn):
    id: int

# === HISTORIAL (Solo lectura) ===
class HistorialInventario(BaseModel):
    id: int
    fecha: datetime
    sucursal_id: int
    usuario_id: int
    producto_id: int
    tipo_movimiento: str
    cantidad_anterior: float
    cantidad_movida: float
    cantidad_nueva: float
    motivo: Optional[str] = None