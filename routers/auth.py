from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from database import database
from models import usuario, sucursal 
from security import verificar_password, crear_token_acceso
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
        "sucursal_nombre": user['sucursal_nombre'] # <--- ESTO YA FUNCIONA
    }