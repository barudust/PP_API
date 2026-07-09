"""
Servicio de permisos (RBAC asignable a roles).

- `sincronizar_catalogo()`: al arrancar, asegura que todos los permisos del
  catálogo (constants.PERMISOS) existan en la BD, y siembra los permisos por
  defecto de un rol SOLO si ese rol aún no tiene ninguno (no pisa personalizaciones).
- `permisos_de_rol(rol)`: permisos efectivos de un rol (superadmin = todos).
- `set_permisos_rol(rol, codigos)`: reemplaza los permisos de un rol.
"""
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.database import database
from app.models import permiso, rol_permiso
from app.core.constants import (
    PERMISOS,
    PERMISOS_POR_ROL_DEFAULT,
    TODOS_LOS_PERMISOS,
    ROL_SUPERADMIN,
)


async def sincronizar_catalogo() -> None:
    # 1. Upsert del catálogo de permisos
    for codigo, nombre, grupo in PERMISOS:
        stmt = pg_insert(permiso).values(codigo=codigo, nombre=nombre, grupo=grupo)
        stmt = stmt.on_conflict_do_update(
            index_elements=["codigo"], set_={"nombre": nombre, "grupo": grupo}
        )
        await database.execute(stmt)

    # 2. Sembrar defaults por rol solo si el rol no tiene filas todavía
    for rol, codigos in PERMISOS_POR_ROL_DEFAULT.items():
        if rol == ROL_SUPERADMIN:
            continue  # superadmin es implícito (todos)
        existentes = await database.fetch_one(
            select(rol_permiso.c.id).where(rol_permiso.c.rol == rol).limit(1)
        )
        if existentes:
            continue
        for codigo in codigos:
            await database.execute(
                rol_permiso.insert().values(rol=rol, permiso_codigo=codigo)
            )


async def permisos_de_rol(rol: str) -> list[str]:
    if (rol or "").lower() == ROL_SUPERADMIN:
        return list(TODOS_LOS_PERMISOS)
    filas = await database.fetch_all(
        select(rol_permiso.c.permiso_codigo).where(rol_permiso.c.rol == rol)
    )
    return [f["permiso_codigo"] for f in filas]


async def set_permisos_rol(rol: str, codigos: list[str]) -> list[str]:
    validos = set(TODOS_LOS_PERMISOS)
    limpios = [c for c in dict.fromkeys(codigos) if c in validos]
    async with database.transaction():
        await database.execute(delete(rol_permiso).where(rol_permiso.c.rol == rol))
        for codigo in limpios:
            await database.execute(
                rol_permiso.insert().values(rol=rol, permiso_codigo=codigo)
            )
    return limpios
