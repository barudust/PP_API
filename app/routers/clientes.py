# routers/clientes.py

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

# --- Importaciones ---
from app.models import cliente
from app.schemas import ClienteIn, Cliente
from app.core.database import database
from app.core.dependencies import require_perm

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)


@router.get("/", response_model=List[Cliente], dependencies=[Depends(require_perm("clientes.ver"))])
async def obtener_clientes(sucursal_id: Optional[int] = None):
    # Los clientes son propios de una sucursal: se filtra por la sucursal del
    # usuario que consulta (el frontend siempre manda la suya).
    query = cliente.select()
    if sucursal_id is not None:
        query = query.where(cliente.c.sucursal_id == sucursal_id)
    return await database.fetch_all(query)


@router.get("/{id}", response_model=Cliente, dependencies=[Depends(require_perm("clientes.ver"))])
async def obtener_cliente(id: int):
    query = cliente.select().where(cliente.c.id == id)
    result = await database.fetch_one(query)
    if result is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return result


@router.post("/", response_model=Cliente, dependencies=[Depends(require_perm("clientes.gestionar"))])
async def crear_cliente(c: ClienteIn):
    query = cliente.insert().values(**c.model_dump())
    last_id = await database.execute(query)
    return {**c.model_dump(), "id": last_id}


@router.put("/{id}", response_model=Cliente, dependencies=[Depends(require_perm("clientes.gestionar"))])
async def actualizar_cliente(id: int, c: ClienteIn):
    query = cliente.update().where(cliente.c.id == id).values(**c.model_dump())
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {**c.model_dump(), "id": id}


@router.delete("/{id}", dependencies=[Depends(require_perm("clientes.gestionar"))])
async def eliminar_cliente(id: int):
    query = cliente.delete().where(cliente.c.id == id)
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"mensaje": "Cliente eliminado"}
