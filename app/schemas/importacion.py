"""Schemas de importación de catálogo (Excel/XML) — Fase 11."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class LineaImportacion(BaseModel):
    id: int
    lote_id: int
    nombre_original: str
    categoria_sugerida: Optional[str] = None
    cantidad: Optional[float] = None
    contenido_neto: Optional[float] = None
    precio_costo: Optional[float] = None
    codigo_sat: Optional[str] = None
    codigo_proveedor: Optional[str] = None
    marca_id: Optional[int] = None
    producto_match_id: Optional[int] = None
    match_score: Optional[float] = None
    margen_aplicado: Optional[float] = None
    precio_venta_sugerido: Optional[float] = None
    actualizar_precio: bool = False
    decision: str = "pendiente"
    producto_creado_id: Optional[int] = None
    precio_actual_producto: Optional[float] = None


class LineaImportacionUpdate(BaseModel):
    nombre_original: Optional[str] = None
    marca_id: Optional[int] = None
    producto_match_id: Optional[int] = None
    margen_aplicado: Optional[float] = None
    precio_venta_sugerido: Optional[float] = None
    actualizar_precio: Optional[bool] = None
    decision: Optional[str] = None


class LoteImportacion(BaseModel):
    id: int
    tipo: str
    nombre_archivo: str
    proveedor: Optional[str] = None
    marca_default_id: Optional[int] = None
    estado: str
    usuario_id: int
    fecha: datetime
    fecha_confirmacion: Optional[datetime] = None
    generar_ingreso: bool = False
    sucursal_id: Optional[int] = None


class LoteImportacionDetalle(LoteImportacion):
    lineas: list[LineaImportacion] = []


class ConfirmarLoteIn(BaseModel):
    generar_ingreso: bool = False
    sucursal_id: Optional[int] = None


class ConfirmarLoteResumen(BaseModel):
    productos_creados: int
    productos_vinculados: int
    lineas_ignoradas: int
    ingresos_generados: int
