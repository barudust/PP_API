"""Gestión de roles y permisos (asignar permisos a cada rol)."""
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from app.core.database import database
from app.models import permiso
from app.core.dependencies import require_perm
from app.core.constants import ROLES_VALIDOS_LISTA
from app.services.permisos_service import permisos_de_rol, set_permisos_rol

router = APIRouter(
    prefix="/roles",
    tags=["Roles y permisos"],
    dependencies=[Depends(require_perm("roles.gestionar"))],
)


class PermisosRolIn(BaseModel):
    permisos: List[str]


@router.get("/permisos")
async def catalogo_permisos():
    """Catálogo maestro de permisos (para pintar la matriz en la UI)."""
    filas = await database.fetch_all(
        select(permiso).order_by(permiso.c.grupo, permiso.c.codigo)
    )
    return [dict(f) for f in filas]


@router.get("/")
async def listar_roles():
    """Cada rol con sus permisos actuales."""
    return [
        {"rol": rol, "permisos": await permisos_de_rol(rol)}
        for rol in ROLES_VALIDOS_LISTA
    ]


@router.put("/{rol}/permisos")
async def actualizar_permisos_rol(rol: str, data: PermisosRolIn):
    """Reemplaza los permisos de un rol (superadmin siempre tiene todos)."""
    if rol.lower() == "superadmin":
        return {"rol": rol, "permisos": await permisos_de_rol("superadmin")}
    permisos_finales = await set_permisos_rol(rol, data.permisos)
    return {"rol": rol, "permisos": permisos_finales}
