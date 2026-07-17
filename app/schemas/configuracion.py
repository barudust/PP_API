"""Schema de configuración básica del negocio (fila única)."""
from typing import Optional
from pydantic import BaseModel


class ConfiguracionNegocio(BaseModel):
    id: int
    nombre: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    rfc: Optional[str] = None


class ConfiguracionNegocioIn(BaseModel):
    nombre: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    rfc: Optional[str] = None
