from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from database import database
from models import usuario
from security import verificar_password, crear_token_acceso
from sqlalchemy import select

router = APIRouter(tags=["Autenticación"])

# En auth.py
@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # ... código de búsqueda ...
    query = select(usuario).where(usuario.c.nombre == form_data.username)
    user = await database.fetch_one(query) # <--- La variable se llama 'user'

    if not user or not verificar_password(form_data.password, user["contrasena_hash"]):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    # CORRECCIÓN AQUÍ: Cambia 'user_db' por 'user'
    access_token = crear_token_acceso(
        data={"sub": user["nombre"], "id": user["id"], "rol": user["rol"]}
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "usuario_id": user["id"],      # <--- 'user' en lugar de 'user_db'
        "sucursal_id": user["sucursal_id"]
    }