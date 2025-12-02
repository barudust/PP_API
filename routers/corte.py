from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
from sqlalchemy import select, update, func

from database import database, fecha_local_iso
from models import corte_caja, venta, usuario

router = APIRouter(
    prefix="/corte",
    tags=["Corte de Caja"]
)

# --- Esquemas ---
class AperturaCajaReq(BaseModel):
    sucursal_id: int
    usuario_id: int
    fondo_inicial: float

class CierreCajaReq(BaseModel):
    corte_id: int
    efectivo_real: float # Lo que contó el cajero
    monto_retirado: float # Lo que se lleva el dueño
    comentarios: Optional[str] = None

class CorteResponse(BaseModel):
    id: int
    fecha_apertura: str
    fecha_cierre: Optional[str] = None
    fondo_inicial: float
    ventas_totales: float
    efectivo_esperado: float
    efectivo_real: Optional[float] = None
    diferencia: Optional[float] = None
    fondo_siguiente: Optional[float] = None
    estado: str # "ABIERTO" o "CERRADO"

# --- Endpoints ---

@router.post("/abrir", response_model=CorteResponse)
async def abrir_caja(data: AperturaCajaReq):
    # 1. Validar que no haya un corte abierto para este usuario/sucursal
    query_activo = select(corte_caja).where(
        (corte_caja.c.usuario_id == data.usuario_id) &
        (corte_caja.c.fecha_cierre == None)
    )
    activo = await database.fetch_one(query_activo)
    if activo:
        raise HTTPException(400, "Ya existe un turno abierto para este usuario.")

    # 2. Crear el corte
    query = corte_caja.insert().values(
        sucursal_id=data.sucursal_id,
        usuario_id=data.usuario_id,
        fondo_inicial=data.fondo_inicial,
        fecha_apertura=datetime.now(timezone.utc),
        ventas_totales=0,
        efectivo_esperado=data.fondo_inicial # Al inicio es igual al fondo
    )
    corte_id = await database.execute(query)
    
    return {
        "id": corte_id,
        "fecha_apertura": fecha_local_iso(datetime.now(timezone.utc)),
        "fondo_inicial": data.fondo_inicial,
        "ventas_totales": 0.0,
        "efectivo_esperado": data.fondo_inicial,
        "estado": "ABIERTO"
    }

@router.get("/actual/{usuario_id}", response_model=CorteResponse)
async def obtener_corte_actual(usuario_id: int):
    """Obtiene el estado actual del corte"""
    
    # 1. Buscar corte abierto
    query = select(corte_caja).where(
        (corte_caja.c.usuario_id == usuario_id) &
        (corte_caja.c.fecha_cierre == None)
    )
    corte = await database.fetch_one(query)
    if not corte:
        raise HTTPException(404, "No hay turno abierto para este usuario")
        
    # 2. Calcular ventas acumuladas
    query_ventas = select(func.sum(venta.c.total)).where(venta.c.corte_caja_id == corte['id'])
    total_ventas = await database.fetch_val(query_ventas) or 0.0
    
    esperado = float(corte['fondo_inicial']) + float(total_ventas)
    
    return {
        "id": corte['id'],
        "fecha_apertura": fecha_local_iso(corte['fecha_apertura']),
        "fondo_inicial": corte['fondo_inicial'],
        "ventas_totales": total_ventas,
        "efectivo_esperado": esperado,
        "estado": "ABIERTO"
    }

@router.post("/cerrar", response_model=CorteResponse)
async def cerrar_caja(data: CierreCajaReq):
    # 1. Obtener datos actuales
    query = select(corte_caja).where(corte_caja.c.id == data.corte_id)
    corte = await database.fetch_one(query)
    if not corte:
        raise HTTPException(404, "Corte no encontrado")
    if corte['fecha_cierre'] is not None:
        raise HTTPException(400, "Este corte ya está cerrado")

    # 2. Calcular totales finales
    query_ventas = select(func.sum(venta.c.total)).where(venta.c.corte_caja_id == data.corte_id)
    total_ventas = await database.fetch_val(query_ventas) or 0.0
    
    esperado = float(corte['fondo_inicial']) + float(total_ventas)
    diferencia = data.efectivo_real - esperado 
    
    fondo_siguiente = data.efectivo_real - data.monto_retirado
    
    fecha_cierre = datetime.now(timezone.utc)
    
    # 3. Actualizar DB (CORREGIDO: efectivo_real en lugar de efectivo_final_real)
    upd_query = corte_caja.update().where(corte_caja.c.id == data.corte_id).values(
        fecha_cierre=fecha_cierre,
        ventas_totales=total_ventas,
        efectivo_esperado=esperado,
        efectivo_real=data.efectivo_real, # <--- AQUÍ ESTABA EL ERROR
        diferencia=diferencia,
        monto_retirado=data.monto_retirado,
        fondo_siguiente=fondo_siguiente,
        comentarios=data.comentarios
    )
    await database.execute(upd_query)
    
    return {
        "id": data.corte_id,
        "fecha_apertura": fecha_local_iso(corte['fecha_apertura']),
        "fecha_cierre": fecha_local_iso(fecha_cierre),
        "fondo_inicial": corte['fondo_inicial'],
        "ventas_totales": total_ventas,
        "efectivo_esperado": esperado,
        "efectivo_real": data.efectivo_real,
        "diferencia": diferencia,
        "fondo_siguiente": fondo_siguiente,
        "estado": "CERRADO"
    }