# routers/usuarios.py

from fastapi import APIRouter, HTTPException
from typing import List

# --- Importaciones del proyecto ---
from models import usuario
from schemas import UsuarioIn, Usuario
from database import database

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
    query = usuario.insert().values(**u.model_dump())
    last_id = await database.execute(query)
    return {**u.model_dump(), "id": last_id}

@router.put("/{id}", response_model=Usuario)
async def actualizar_usuario(id: int, u: UsuarioIn):
    query = usuario.update().where(usuario.c.id == id).values(**u.model_dump())
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {**u.model_dump(), "id": id}

@router.delete("/{id}")
async def eliminar_usuario(id: int):
    query = usuario.delete().where(usuario.c.id == id)
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"mensaje": "Usuario eliminado"}