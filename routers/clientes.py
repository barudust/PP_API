# routers/clientes.py

from fastapi import APIRouter, HTTPException
from typing import List

# --- Importaciones ---
from models import cliente
from schemas import ClienteIn, Cliente
from database import database

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)

@router.get("/", response_model=List[Cliente])
async def obtener_clientes():
    query = cliente.select()
    return await database.fetch_all(query)

@router.get("/{id}", response_model=Cliente)
async def obtener_cliente(id: int):
    query = cliente.select().where(cliente.c.id == id)
    result = await database.fetch_one(query)
    if result is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return result

@router.post("/", response_model=Cliente)
async def crear_cliente(c: ClienteIn):
    query = cliente.insert().values(**c.model_dump())
    last_id = await database.execute(query)
    return {**c.model_dump(), "id": last_id}

@router.put("/{id}", response_model=Cliente)
async def actualizar_cliente(id: int, c: ClienteIn):
    query = cliente.update().where(cliente.c.id == id).values(**c.model_dump())
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {**c.model_dump(), "id": id}

@router.delete("/{id}")
async def eliminar_cliente(id: int):
    query = cliente.delete().where(cliente.c.id == id)
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"mensaje": "Cliente eliminado"}