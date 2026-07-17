"""Schemas de inventario, ingresos, ajustes de auditoría e historial."""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


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
            fecha_actualizacion=obj.fecha_actualizacion.date().isoformat(),
        )


class IngresoInventarioIn(BaseModel):
    producto_id: int
    sucursal_id: int
    cantidad: float
    usuario_id: int


class IngresoInventario(IngresoInventarioIn):
    id: int
    fecha_actualizacion: str


class IngresoInventarioLoteLinea(BaseModel):
    producto_id: int
    cantidad: float


class IngresoInventarioLoteIn(BaseModel):
    sucursal_id: int
    usuario_id: int
    proveedor: Optional[str] = None
    nota: Optional[str] = None
    lineas: List[IngresoInventarioLoteLinea]


class IngresoInventarioLoteResumen(BaseModel):
    id: int
    fecha: str
    sucursal_id: int
    usuario_id: int
    usuario_nombre: Optional[str] = None
    proveedor: Optional[str] = None
    nota: Optional[str] = None
    num_lineas: int
    total_unidades: float


class IngresoInventarioLoteLineaDetalle(BaseModel):
    producto_id: int
    producto_nombre: str
    unidad_medida: str
    cantidad: float


class IngresoInventarioLoteDetalle(IngresoInventarioLoteResumen):
    lineas: List[IngresoInventarioLoteLineaDetalle]


class AjusteInventarioIn(BaseModel):
    sucursal_id: int
    usuario_id: int
    producto_id: int
    cantidad_fisica: float
    # cantidad_sistema es informativa; el backend usa el stock real de la BD.
    cantidad_sistema: Optional[float] = None
    # Tipo de diferencia (opcional: si no se envía, el backend lo sugiere).
    tipo_ajuste: Optional[str] = None
    motivo: Optional[str] = None


class AjusteInventario(BaseModel):
    id: int
    sucursal_id: int
    usuario_id: int
    producto_id: int
    cantidad_sistema: float
    cantidad_fisica: float
    diferencia: float
    tipo_ajuste: Optional[str] = None
    motivo: Optional[str] = None
    fecha: datetime
    # Ayudas de auditoría (tolerancia de fábrica asimétrica)
    tolerancia_calculada: Optional[float] = None
    tolerancia_bajo: Optional[float] = None   # cuánto puede FALTAR (total)
    tolerancia_alto: Optional[float] = None   # cuánto puede SOBRAR (total)
    dentro_de_tolerancia: Optional[bool] = None
    tipo_sugerido: Optional[str] = None


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
