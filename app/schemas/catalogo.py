"""Schemas de catálogos y organización."""
from typing import Optional
from pydantic import BaseModel


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
    # Variación de fábrica esperada por empaque (unidad base), según la empresa.
    tolerancia_bajo: float = 0.0   # cuánto puede FALTAR por bulto
    tolerancia_alto: float = 0.0   # cuánto puede SOBRAR por bulto
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


class TipoProductoIn(BaseModel):
    nombre: str
class TipoProducto(TipoProductoIn):
    id: int


class SucursalIn(BaseModel):
    nombre: str
    direccion: Optional[str] = None
class SucursalOut(SucursalIn):
    id: int


class ClienteIn(BaseModel):
    nombre: str
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    notas: Optional[str] = None
class Cliente(ClienteIn):
    id: int


class UsuarioIn(BaseModel):
    nombre: str
    contrasena_hash: str  # contraseña en texto plano; el backend la hashea
    rol: str
    sucursal_id: int
class Usuario(UsuarioIn):
    id: int

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    rol: Optional[str] = None
    sucursal_id: Optional[int] = None
    contrasena: Optional[str] = None  # si viene, se re-hashea; si no, se conserva

class CambioPassword(BaseModel):
    contrasena: str
