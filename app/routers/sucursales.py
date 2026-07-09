# routers/sucursales.py

from fastapi import APIRouter, HTTPException
from typing import List

# --- Importaciones del proyecto ---
from fastapi import Depends
from app.models import sucursal
from app.schemas import SucursalIn, SucursalOut
from app.core.database import database
from app.core.dependencies import require_roles, ROL_SUPERADMIN

router = APIRouter(
    prefix="/sucursales",
    tags=["Sucursales"]
)

# Solo SuperAdmin puede crear/editar/eliminar sucursales.
_solo_superadmin = Depends(require_roles(ROL_SUPERADMIN))

@router.get("/", response_model=List[SucursalOut])
async def obtener_sucursales():
    query = sucursal.select()
    return await database.fetch_all(query)

@router.get("/{id}", response_model=SucursalOut)
async def obtener_sucursal(id: int):
    query = sucursal.select().where(sucursal.c.id == id)
    result = await database.fetch_one(query)
    if result is None:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    return result

@router.post("/", response_model=SucursalOut, dependencies=[_solo_superadmin])
async def crear_sucursal(suc: SucursalIn):
    query = sucursal.insert().values(**suc.model_dump())
    last_id = await database.execute(query)
    return {**suc.model_dump(), "id": last_id}

@router.put("/{id}", response_model=SucursalOut, dependencies=[_solo_superadmin])
async def actualizar_sucursal(id: int, suc: SucursalIn):
    query = sucursal.update().where(sucursal.c.id == id).values(**suc.model_dump())
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    return {**suc.model_dump(), "id": id}

@router.delete("/{id}", dependencies=[_solo_superadmin])
async def eliminar_sucursal(id: int):
    query = sucursal.delete().where(sucursal.c.id == id)
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    return {"mensaje": "Sucursal eliminada"}