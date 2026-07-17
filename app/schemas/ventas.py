"""Schemas de ventas, detalle y reglas de descuento."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class VentaIn(BaseModel):
    sucursal_id: int
    usuario_id: int
    cliente_id: Optional[int] = None
    corte_caja_id: Optional[int] = None
    total: float
    descuento_especial_monto: float = 0.0
    descuento_especial_motivo: Optional[str] = None
    tipo_entrega: str = "tienda"  # 'tienda' | 'domicilio'


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
    # Sucursal a la que aplica (None = todas). Si cliente_id viene, el backend
    # la sobrescribe con la sucursal del cliente (un cliente es de una sola sucursal).
    sucursal_id: Optional[int] = None
    activo: bool = True


class ReglaDescuento(ReglaDescuentoIn):
    id: int
