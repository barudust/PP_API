from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.core.database import database
from app.models import usuario, sucursal
from app.core.security import verificar_password, crear_token_acceso
from app.core.dependencies import get_current_user
from app.services.permisos_service import permisos_de_rol
from sqlalchemy import select

router = APIRouter(tags=["Autenticación"])

# En auth.py
@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # 1. Hacemos un JOIN para traer el nombre de la sucursal junto con los datos del usuario
    query = select(
        usuario, 
        sucursal.c.nombre.label("sucursal_nombre") # Traemos el nombre de la sucursal
    ).select_from(
        usuario.join(sucursal, usuario.c.sucursal_id == sucursal.c.id)
    ).where(usuario.c.nombre == form_data.username)
    
    user = await database.fetch_one(query)

    if not user or not verificar_password(form_data.password, user["contrasena_hash"]):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    # 2. Generar token
    access_token = crear_token_acceso(
        data={"sub": user["nombre"], "id": user["id"], "rol": user["rol"]}
    )
    
    # 3. Ahora 'sucursal_nombre' ya no dará error porque viene en el JOIN
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario_id": user["id"],
        "sucursal_id": user["sucursal_id"],
        "nombre": user['nombre'],
        "rol": user["rol"],
        "sucursal_nombre": user['sucursal_nombre']
    }


@router.get("/auth/me")
async def leer_usuario_actual(actual=Depends(get_current_user)):
    """Devuelve el usuario autenticado y sus permisos efectivos.

    El frontend usa esto para armar el menú y proteger rutas por permiso.
    """
    suc = await database.fetch_one(
        select(sucursal.c.nombre).where(sucursal.c.id == actual["sucursal_id"])
    )
    return {
        "id": actual["id"],
        "nombre": actual["nombre"],
        "rol": actual["rol"],
        "sucursal_id": actual["sucursal_id"],
        "sucursal_nombre": suc["nombre"] if suc else None,
        "permisos": await permisos_de_rol(actual["rol"]),
    }