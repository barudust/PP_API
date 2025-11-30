from fastapi import APIRouter, HTTPException
from typing import List
from models import usuario
from schemas import UsuarioIn, Usuario
from database import database
from security import get_password_hash # Asegúrate de tener security.py creado

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)

@router.get("/", response_model=List[Usuario])
async def obtener_usuarios():
    query = usuario.select()
    return await database.fetch_all(query)

@router.get("/{id}", response_model=Usuario)
async def obtener_usuario(id: int):
    query = usuario.select().where(usuario.c.id == id)
    result = await database.fetch_one(query)
    if result is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return result

@router.post("/", response_model=Usuario)
async def crear_usuario(u: UsuarioIn):
    # 1. Convertimos los datos a un diccionario modificable
    datos_usuario = u.model_dump()
    
    # 2. --- EL CAMBIO CLAVE ---
    # Encriptamos la contraseña antes de enviarla a la base de datos
    datos_usuario["contrasena_hash"] = get_password_hash(datos_usuario["contrasena_hash"])
    
    # 3. Insertamos los datos ya encriptados
    query = usuario.insert().values(**datos_usuario)
    last_id = await database.execute(query)
    
    return {**datos_usuario, "id": last_id}

@router.put("/{id}", response_model=Usuario)
async def actualizar_usuario(id: int, u: UsuarioIn):
    # También encriptamos al actualizar, por si el usuario cambia su contraseña
    datos_usuario = u.model_dump()
    datos_usuario["contrasena_hash"] = get_password_hash(datos_usuario["contrasena_hash"])

    query = usuario.update().where(usuario.c.id == id).values(**datos_usuario)
    result = await database.execute(query)
    
    if result == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {**datos_usuario, "id": id}

@router.delete("/{id}")
async def eliminar_usuario(id: int):
    query = usuario.delete().where(usuario.c.id == id)
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"mensaje": "Usuario eliminado"}