from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timezone
from sqlalchemy import select, update

from database import database
from models import inventario, ajuste_inventario, historial_inventario, producto
from schemas import AjusteInventarioIn, AjusteInventario, HistorialInventario

router = APIRouter(
    prefix="/auditoria",
    tags=["Auditoría e Historial"]
)

@router.post("/ajuste", response_model=AjusteInventario)
async def registrar_ajuste_inventario(data: AjusteInventarioIn):
    """
    Se usa cuando pesas el producto real y quieres corregir el sistema.
    Calcula la diferencia y actualiza el inventario.
    """
    async with database.transaction():
        # 1. Obtener Inventario Actual (Sistema)
        query_inv = select(inventario).where(
            (inventario.c.producto_id == data.producto_id) &
            (inventario.c.sucursal_id == data.sucursal_id)
        )
        inv_db = await database.fetch_one(query_inv)
        
        cantidad_sistema = float(inv_db['cantidad']) if inv_db else 0.0
        
        # 2. Calcular Diferencia (Real - Sistema)
        # Ej: Real 48kg - Sistema 50kg = -2kg (Merma)
        diferencia = data.cantidad_fisica - cantidad_sistema
        
        # 3. Guardar el Ajuste
        query_ajuste = ajuste_inventario.insert().values(
            sucursal_id=data.sucursal_id,
            usuario_id=data.usuario_id,
            producto_id=data.producto_id,
            fecha=datetime.now(timezone.utc),
            cantidad_sistema=cantidad_sistema,
            cantidad_fisica=data.cantidad_fisica,
            diferencia=diferencia,
            motivo=data.motivo
        )
        ajuste_id = await database.execute(query_ajuste)
        
        # 4. Actualizar o Crear el Inventario con el valor FÍSICO (el real)
        if inv_db:
            query_upd = inventario.update().where(inventario.c.id == inv_db['id']).values(
                cantidad=data.cantidad_fisica,
                fecha_actualizacion=datetime.now(timezone.utc)
            )
            await database.execute(query_upd)
        else:
            # Si no existía registro, lo creamos
            query_ins = inventario.insert().values(
                producto_id=data.producto_id,
                sucursal_id=data.sucursal_id,
                cantidad=data.cantidad_fisica,
                fecha_actualizacion=datetime.now(timezone.utc)
            )
            await database.execute(query_ins)
            
        # 5. Registrar en el Historial (El Chismoso)
        query_hist = historial_inventario.insert().values(
            fecha=datetime.now(timezone.utc),
            sucursal_id=data.sucursal_id,
            usuario_id=data.usuario_id,
            producto_id=data.producto_id,
            tipo_movimiento="AJUSTE_AUDITORIA",
            cantidad_anterior=cantidad_sistema,
            cantidad_movida=diferencia,
            cantidad_nueva=data.cantidad_fisica,
            motivo=data.motivo or "Ajuste físico de inventario"
        )
        await database.execute(query_hist)
        
        return {
            "id": ajuste_id,
            "sucursal_id": data.sucursal_id,
            "usuario_id": data.usuario_id,
            "producto_id": data.producto_id,
            "cantidad_sistema": cantidad_sistema,
            "cantidad_fisica": data.cantidad_fisica,
            "diferencia": diferencia,
            "motivo": data.motivo,
            "fecha": datetime.now(timezone.utc)
        }

@router.get("/historial", response_model=List[HistorialInventario])
async def ver_historial(producto_id: int):
    """Ver todos los movimientos de un producto específico"""
    query = historial_inventario.select().where(
        historial_inventario.c.producto_id == producto_id
    ).order_by(historial_inventario.c.fecha.desc())
    
    return await database.fetch_all(query)