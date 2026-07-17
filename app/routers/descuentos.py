from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select

from app.models import regla_descuento
from app.schemas import ReglaDescuentoIn, ReglaDescuento
from app.core.database import database
from app.core.dependencies import require_perm
from app.services.descuentos_service import resolver_sucursal_id, validar_sin_conflicto

router = APIRouter(
    prefix="/descuentos",
    tags=["Configuración de Descuentos"],
    dependencies=[Depends(require_perm("descuentos.gestionar"))],
)


@router.get("/", response_model=List[ReglaDescuento])
async def listar_reglas(sucursal_id: Optional[int] = None, cliente_id: Optional[int] = None):
    query = regla_descuento.select()
    if sucursal_id is not None:
        # Incluye reglas globales (sucursal_id NULL) + las de esa sucursal.
        query = query.where(
            (regla_descuento.c.sucursal_id == sucursal_id) | (regla_descuento.c.sucursal_id.is_(None))
        )
    if cliente_id is not None:
        query = query.where(regla_descuento.c.cliente_id == cliente_id)
    return await database.fetch_all(query)


@router.post("/", response_model=ReglaDescuento)
async def crear_regla(regla: ReglaDescuentoIn):
    datos = regla.model_dump()
    datos["sucursal_id"] = await resolver_sucursal_id(datos["cliente_id"], datos["sucursal_id"])
    await validar_sin_conflicto(
        cliente_id=datos["cliente_id"],
        marca_id=datos["marca_id"],
        producto_id=datos["producto_id"],
        sucursal_id=datos["sucursal_id"],
    )
    last_id = await database.execute(regla_descuento.insert().values(**datos))
    return {**datos, "id": last_id}


@router.put("/{id}", response_model=ReglaDescuento)
async def actualizar_regla(id: int, regla: ReglaDescuentoIn):
    existente = await database.fetch_one(select(regla_descuento).where(regla_descuento.c.id == id))
    if not existente:
        raise HTTPException(404, "Regla no encontrada")
    datos = regla.model_dump()
    datos["sucursal_id"] = await resolver_sucursal_id(datos["cliente_id"], datos["sucursal_id"])
    await validar_sin_conflicto(
        cliente_id=datos["cliente_id"],
        marca_id=datos["marca_id"],
        producto_id=datos["producto_id"],
        sucursal_id=datos["sucursal_id"],
        excluir_id=id,
    )
    await database.execute(regla_descuento.update().where(regla_descuento.c.id == id).values(**datos))
    return {**datos, "id": id}


@router.delete("/{id}")
async def eliminar_regla(id: int):
    result = await database.execute(regla_descuento.delete().where(regla_descuento.c.id == id))
    if result == 0:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return {"mensaje": "Regla eliminada"}
