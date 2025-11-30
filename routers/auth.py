from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from database import database
from models import usuario
from security import verificar_password, crear_token_acceso
from sqlalchemy import select

router = APIRouter(tags=["Autenticación"])

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # 1. Buscar usuario por nombre
    query = select(usuario).where(usuario.c.nombre == form_data.username)
    user_db = await database.fetch_one(query)
    
    # 2. Validar si existe y si la contraseña coincide
    if not user_db or not verificar_password(form_data.password, user_db["contrasena_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Generar Token
    # Guardamos en el token el ID y el ROL (útil para el frontend)
    access_token = crear_token_acceso(
        data={"sub": user_db["nombre"], "id": user_db["id"], "rol": user_db["rol"]}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}