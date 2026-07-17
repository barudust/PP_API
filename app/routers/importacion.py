"""Importación de catálogo desde Excel o factura XML (CFDI) — Fase 11."""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy import select

from app.core.database import database
from app.core.dependencies import require_perm, get_current_user
from app.models import importacion_lote, importacion_linea, producto
from app.schemas import (
    LoteImportacion,
    LoteImportacionDetalle,
    LineaImportacion,
    LineaImportacionUpdate,
    ConfirmarLoteIn,
    ConfirmarLoteResumen,
)
from app.services import importacion_service as servicio

router = APIRouter(prefix="/importacion", tags=["Importación"])

_requiere_importar = Depends(require_perm("catalogo.importar"))


async def _detalle_lote(lote_id: int) -> dict:
    lote = await database.fetch_one(importacion_lote.select().where(importacion_lote.c.id == lote_id))
    if not lote:
        raise HTTPException(404, "Lote no encontrado")
    query = (
        select(importacion_linea, producto.c.precio_base.label("precio_actual_producto"))
        .select_from(
            importacion_linea.outerjoin(producto, importacion_linea.c.producto_match_id == producto.c.id)
        )
        .where(importacion_linea.c.lote_id == lote_id)
        .order_by(importacion_linea.c.id)
    )
    lineas = await database.fetch_all(query)
    return {**dict(lote), "lineas": [dict(l) for l in lineas]}


@router.post("/excel", response_model=LoteImportacionDetalle, dependencies=[_requiere_importar])
async def importar_excel(
    archivo: UploadFile = File(...),
    marca_default_id: Optional[int] = Form(None),
    usuario=Depends(get_current_user),
):
    if not archivo.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(400, "El archivo debe ser un Excel (.xlsx)")
    contenido = await archivo.read()
    lote_id = await servicio.crear_lote_excel(contenido, archivo.filename, usuario["id"], marca_default_id)
    return await _detalle_lote(lote_id)


@router.post("/xml", response_model=LoteImportacionDetalle, dependencies=[_requiere_importar])
async def importar_xml(
    archivo: UploadFile = File(...),
    marca_default_id: Optional[int] = Form(None),
    usuario=Depends(get_current_user),
):
    if not archivo.filename.lower().endswith(".xml"):
        raise HTTPException(400, "El archivo debe ser un XML (CFDI)")
    contenido = await archivo.read()
    lote_id = await servicio.crear_lote_xml(contenido, archivo.filename, usuario["id"], marca_default_id)
    return await _detalle_lote(lote_id)


@router.post("/pdf", response_model=LoteImportacionDetalle, dependencies=[_requiere_importar])
async def importar_pdf(
    archivo: UploadFile = File(...),
    marca_default_id: Optional[int] = Form(None),
    usuario=Depends(get_current_user),
):
    if not archivo.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "El archivo debe ser un PDF")
    contenido = await archivo.read()
    lote_id = await servicio.crear_lote_pdf(contenido, archivo.filename, usuario["id"], marca_default_id)
    return await _detalle_lote(lote_id)


@router.get("/lotes", response_model=List[LoteImportacion], dependencies=[_requiere_importar])
async def listar_lotes():
    query = importacion_lote.select().order_by(importacion_lote.c.fecha.desc())
    return await database.fetch_all(query)


@router.get("/lotes/{lote_id}", response_model=LoteImportacionDetalle, dependencies=[_requiere_importar])
async def obtener_lote(lote_id: int):
    return await _detalle_lote(lote_id)


@router.patch(
    "/lotes/{lote_id}/lineas/{linea_id}",
    response_model=LineaImportacion,
    dependencies=[_requiere_importar],
)
async def editar_linea(lote_id: int, linea_id: int, cambios: LineaImportacionUpdate):
    await servicio.actualizar_linea(lote_id, linea_id, cambios.model_dump(exclude_unset=True))
    fila = await database.fetch_one(importacion_linea.select().where(importacion_linea.c.id == linea_id))
    if not fila:
        raise HTTPException(404, "Línea no encontrada")
    return fila


@router.delete(
    "/lotes/{lote_id}/lineas/{linea_id}",
    dependencies=[_requiere_importar],
)
async def borrar_linea(lote_id: int, linea_id: int):
    await servicio.eliminar_linea(lote_id, linea_id)
    return {"mensaje": "Línea eliminada"}


@router.post(
    "/lotes/{lote_id}/confirmar",
    response_model=ConfirmarLoteResumen,
    dependencies=[_requiere_importar],
)
async def confirmar(lote_id: int, datos: ConfirmarLoteIn, usuario=Depends(get_current_user)):
    return await servicio.confirmar_lote(lote_id, usuario, datos.generar_ingreso, datos.sucursal_id)


@router.post("/lotes/{lote_id}/cancelar", dependencies=[_requiere_importar])
async def cancelar(lote_id: int):
    await servicio.cancelar_lote(lote_id)
    return {"mensaje": "Lote cancelado"}
