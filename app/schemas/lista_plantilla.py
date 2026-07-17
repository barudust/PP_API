"""Schemas de la estructura editable de Listas gráficas (Fase 16)."""
from typing import Optional
from pydantic import BaseModel


class ListaPlantillaFila(BaseModel):
    id: int
    marca_id: int
    hoja: str
    panel: str
    orden: int
    tipo: str
    nivel: Optional[int] = None
    texto: str
    producto_id: Optional[int] = None


class ListaPlantillaFilaIn(BaseModel):
    marca_id: int
    hoja: str = "Hoja1"
    panel: str
    orden: int
    tipo: str
    nivel: Optional[int] = None
    texto: str
    producto_id: Optional[int] = None


class ListaPlantillaFilaUpdate(BaseModel):
    hoja: Optional[str] = None
    panel: Optional[str] = None
    orden: Optional[int] = None
    tipo: Optional[str] = None
    nivel: Optional[int] = None
    texto: Optional[str] = None
    producto_id: Optional[int] = None
    desvincular: bool = False  # True = forzar producto_id a NULL aunque no venga en el body


class ReordenarItem(BaseModel):
    id: int
    orden: int


class ReordenarIn(BaseModel):
    items: list[ReordenarItem]


class ListaPlantillaFilaResuelta(BaseModel):
    """Nodo de plantilla + precio resuelto, para el render gráfico."""
    id: int
    hoja: str
    panel: str
    orden: int
    tipo: str
    nivel: Optional[int] = None
    texto: str
    producto_id: Optional[int] = None
    producto_nombre: Optional[str] = None
    precio_base: Optional[float] = None


class ListaPlantillaMarca(BaseModel):
    marca_id: int
    marca_nombre: str
    color: str
    filas: list[ListaPlantillaFilaResuelta]


class ImportarPlantillaResumen(BaseModel):
    marca_id: int
    total_filas: int
    total_encabezados: int
    total_productos: int
    productos_vinculados: int
