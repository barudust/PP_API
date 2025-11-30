from fastapi import APIRouter, HTTPException
from typing import List
from models import regla_descuento
from schemas import ReglaDescuentoIn, ReglaDescuento
from database import database

router = APIRouter(
    prefix="/descuentos",
    tags=["Configuración de Descuentos"]
)

@router.get("/", response_model=List[ReglaDescuento])
async def listar_reglas():
    query = regla_descuento.select()
    return await database.fetch_all(query)

@router.post("/", response_model=ReglaDescuento)
async def crear_regla(regla: ReglaDescuentoIn):
    query = regla_descuento.insert().values(**regla.model_dump())
    last_id = await database.execute(query)
    return {**regla.model_dump(), "id": last_id}

@router.delete("/{id}")
async def eliminar_regla(id: int):
    query = regla_descuento.delete().where(regla_descuento.c.id == id)
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return {"mensaje": "Regla eliminada"}