"""Configuración básica del negocio (fila única, id=1)."""
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import database
from app.core.dependencies import require_perm
from app.models import configuracion_negocio
from app.schemas import ConfiguracionNegocio, ConfiguracionNegocioIn

router = APIRouter(prefix="/configuracion", tags=["Configuración"])


@router.get("/", response_model=ConfiguracionNegocio)
async def obtener_configuracion():
    # Lectura abierta: el nombre/dirección del negocio no es sensible y lo
    # necesita el ticket (POS) sin exigir permisos de administración.
    fila = await database.fetch_one(configuracion_negocio.select().where(configuracion_negocio.c.id == 1))
    if not fila:
        raise HTTPException(500, "Configuración del negocio no inicializada")
    return fila


@router.put("/", response_model=ConfiguracionNegocio, dependencies=[Depends(require_perm("configuracion.gestionar"))])
async def actualizar_configuracion(datos: ConfiguracionNegocioIn):
    await database.execute(
        configuracion_negocio.update().where(configuracion_negocio.c.id == 1).values(**datos.model_dump())
    )
    return await database.fetch_one(configuracion_negocio.select().where(configuracion_negocio.c.id == 1))
