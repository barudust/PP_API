from fastapi import APIRouter
from typing import List
from datetime import date, datetime, timezone
from sqlalchemy import select, func, and_, desc
from database import database
# 👇 AQUÍ FALTABA 'inventario'
from models import venta, venta_detalle, producto, inventario

router = APIRouter(
    prefix="/informes",
    tags=["Informes y Reportes"]
)

@router.get("/ventas-dia")
async def reporte_ventas_dia(sucursal_id: int, fecha: date = None):
    if not fecha:
        fecha = datetime.now(timezone.utc).date()
    
    inicio = datetime.combine(fecha, datetime.min.time())
    fin = datetime.combine(fecha, datetime.max.time())
    
    query = select(func.sum(venta.c.total)).where(
        and_(
            venta.c.sucursal_id == sucursal_id,
            venta.c.fecha >= inicio,
            venta.c.fecha <= fin
        )
    )
    total = await database.fetch_val(query) or 0.0
    
    query_list = select(venta).where(
        and_(
            venta.c.sucursal_id == sucursal_id,
            venta.c.fecha >= inicio,
            venta.c.fecha <= fin
        )
    )
    lista = await database.fetch_all(query_list)
    
    return {
        "fecha": fecha,
        "sucursal_id": sucursal_id,
        "total_vendido": total,
        "cantidad_transacciones": len(lista),
        "ventas": lista
    }

@router.get("/productos-mas-vendidos")
async def productos_top(limit: int = 5):
    query = select(
        producto.c.nombre,
        func.sum(venta_detalle.c.cantidad).label("total_cantidad"),
        func.sum(venta_detalle.c.cantidad * venta_detalle.c.precio_unitario).label("total_dinero")
    ).select_from(
        venta_detalle.join(producto)
    ).group_by(
        producto.c.id
    ).order_by(desc("total_cantidad")).limit(limit)
    
    return await database.fetch_all(query)

@router.get("/stock-bajo")
async def alerta_stock_bajo(sucursal_id: int):
    query = select(
        producto.c.nombre,
        producto.c.sku,
        inventario.c.cantidad,
        producto.c.stock_minimo 
    ).select_from(
        inventario.join(producto)
    ).where(
        and_(
            inventario.c.sucursal_id == sucursal_id,
            producto.c.activo == True,
            inventario.c.cantidad <= producto.c.stock_minimo 
        )
    ).order_by(inventario.c.cantidad)
    
    return await database.fetch_all(query)