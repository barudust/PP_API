"""Schemas de Producto (modelo híbrido relacional + JSONB)."""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ProductoIn(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    sku: Optional[str] = None
    codigo_barras: Optional[str] = None

    # Clasificación
    tipo_producto: str = "Alimento"

    # Relaciones (dimensiones fijas)
    marca_id: Optional[int] = None
    categoria_id: Optional[int] = None
    subcategoria_id: Optional[int] = None
    especie_id: Optional[int] = None
    etapa_id: Optional[int] = None

    # Atributos dinámicos por tipo (sabor, talla, dosis, presentación, material...)
    atributos_extra: Dict[str, Any] = Field(default_factory=dict)

    # Ubicación física (pasillo/estante) para el barrido de auditoría
    ubicacion_fisica: Optional[str] = None

    # Lógica de Venta
    unidad_medida: str = "pza"
    contenido_neto: float = 1.0
    se_vende_a_granel: bool = False

    # Tolerancia de variación de fábrica por empaque (unidad base, ej. kg)
    tolerancia_unidad: float = 0.0

    # Precios
    precio_base: float
    precio_granel: Optional[float] = None

    activo: bool = True
    stock_minimo: float = 5.0


class Producto(ProductoIn):
    id: int
    stock_actual: Optional[float] = 0.0


class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    tipo_producto: Optional[str] = None
    marca_id: Optional[int] = None
    categoria_id: Optional[int] = None
    subcategoria_id: Optional[int] = None
    especie_id: Optional[int] = None
    etapa_id: Optional[int] = None
    atributos_extra: Optional[Dict[str, Any]] = None
    ubicacion_fisica: Optional[str] = None
    precio_base: Optional[float] = None
    precio_granel: Optional[float] = None
    stock_minimo: Optional[float] = None
    contenido_neto: Optional[float] = None
    tolerancia_unidad: Optional[float] = None
    unidad_medida: Optional[str] = None
    se_vende_a_granel: Optional[bool] = None
    activo: Optional[bool] = None
    stock: Optional[float] = None  # atajo para setear inventario (compat)
    sucursal_id: Optional[int] = None  # sucursal del atajo de stock (opcional)
