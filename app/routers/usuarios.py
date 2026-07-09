from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy import select

from app.models import usuario
from app.schemas import UsuarioIn, Usuario, UsuarioUpdate, CambioPassword
from app.core.database import database
from app.core.security import get_password_hash
from app.core.dependencies import require_roles, ROL_SUPERADMIN, ROLES_VALIDOS

# Toda la gestión de usuarios queda restringida a SuperAdmin.
router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"],
    dependencies=[Depends(require_roles(ROL_SUPERADMIN))],
)


def _validar_rol(rol: str) -> None:
    if rol not in ROLES_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Rol inválido '{rol}'. Válidos: {sorted(ROLES_VALIDOS)}",
        )


async def _obtener_o_404(id: int):
    result = await database.fetch_one(select(usuario).where(usuario.c.id == id))
    if result is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return result


@router.get("/", response_model=List[Usuario])
async def obtener_usuarios():
    return await database.fetch_all(usuario.select())


@router.get("/{id}", response_model=Usuario)
async def obtener_usuario(id: int):
    return await _obtener_o_404(id)


@router.post("/", response_model=Usuario)
async def crear_usuario(u: UsuarioIn):
    _validar_rol(u.rol)
    datos_usuario = u.model_dump()
    # El campo `contrasena_hash` llega en texto plano; lo hasheamos aquí.
    datos_usuario["contrasena_hash"] = get_password_hash(datos_usuario["contrasena_hash"])

    last_id = await database.execute(usuario.insert().values(**datos_usuario))
    return {**datos_usuario, "id": last_id}


@router.put("/{id}", response_model=Usuario)
async def actualizar_usuario(id: int, u: UsuarioUpdate):
    """
    Actualiza solo los campos enviados. La contraseña se re-hashea **únicamente**
    si se envía `contrasena` (antes se re-hasheaba en cada actualización).
    """
    await _obtener_o_404(id)

    cambios = {}
    if u.nombre is not None:
        cambios["nombre"] = u.nombre
    if u.rol is not None:
        _validar_rol(u.rol)
        cambios["rol"] = u.rol
    if u.sucursal_id is not None:
        cambios["sucursal_id"] = u.sucursal_id
    if u.contrasena:
        cambios["contrasena_hash"] = get_password_hash(u.contrasena)

    if not cambios:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

    await database.execute(usuario.update().where(usuario.c.id == id).values(**cambios))
    return await _obtener_o_404(id)


@router.post("/{id}/cambiar-password")
async def cambiar_password(id: int, data: CambioPassword):
    """Cambia solo la contraseña de un usuario."""
    await _obtener_o_404(id)
    await database.execute(
        usuario.update()
        .where(usuario.c.id == id)
        .values(contrasena_hash=get_password_hash(data.contrasena))
    )
    return {"mensaje": "Contraseña actualizada"}


@router.delete("/{id}")
async def eliminar_usuario(id: int):
    result = await database.execute(usuario.delete().where(usuario.c.id == id))
    if result == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"mensaje": "Usuario eliminado"}
