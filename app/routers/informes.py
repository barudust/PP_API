from fastapi import APIRouter, Depends
from typing import List, Optional
from datetime import date, datetime, time, timezone
from sqlalchemy import select, func, and_, desc
from app.core.database import database, fecha_local_iso
from app.models import venta, venta_detalle, producto, inventario, ingreso_inventario, ingreso_inventario_lote, usuario, cliente, corte_caja, ajuste_inventario
from app.core.dependencies import require_roles, ROL_GERENTE

# Reportes: Gerente de sucursal o SuperAdmin.
router = APIRouter(
    prefix="/informes",
    tags=["Informes y Reportes"],
    dependencies=[Depends(require_roles(ROL_GERENTE))],
)

# Función auxiliar para convertir fechas
def get_rango_fechas(f_inicio: date, f_fin: date):
    inicio = datetime.combine(f_inicio, time.min)
    fin = datetime.combine(f_fin, time.max)
    return inicio, fin

@router.get("/reporte-ventas")
async def reporte_ventas(sucursal_id: int, inicio: date, fin: date):
    dt_inicio, dt_fin = get_rango_fechas(inicio, fin)
    
    query = select(
        venta.c.id,
        venta.c.fecha,
        venta.c.total,
        venta.c.descuento_especial_monto,
        cliente.c.nombre.label("nombre_cliente"),
        usuario.c.nombre.label("nombre_vendedor")
    ).select_from(
        venta.outerjoin(cliente).join(usuario)
    ).where(
        and_(
            venta.c.sucursal_id == sucursal_id,
            venta.c.fecha >= dt_inicio,
            venta.c.fecha <= dt_fin
        )
    ).order_by(desc(venta.c.fecha))
    
    resultados = await database.fetch_all(query)
    return [{**dict(r), "fecha": fecha_local_iso(r["fecha"])} for r in resultados]

@router.get("/reporte-surtidos")
async def reporte_surtidos(sucursal_id: int, inicio: date, fin: date):
    dt_inicio, dt_fin = get_rango_fechas(inicio, fin)

    # 1. Traemos los datos crudos ordenados por fecha, con el lote real si lo hay
    query = select(
        ingreso_inventario.c.id,
        ingreso_inventario.c.fecha_actualizacion.label("fecha"),
        ingreso_inventario.c.cantidad,
        ingreso_inventario.c.lote_id,
        producto.c.nombre.label("nombre_producto"),
        producto.c.unidad_medida,
        usuario.c.nombre.label("usuario_nombre"),
        ingreso_inventario_lote.c.proveedor,
        ingreso_inventario_lote.c.nota,
    ).select_from(
        ingreso_inventario.join(producto).join(usuario)
        .outerjoin(ingreso_inventario_lote, ingreso_inventario.c.lote_id == ingreso_inventario_lote.c.id)
    ).where(
        and_(
            ingreso_inventario.c.sucursal_id == sucursal_id,
            ingreso_inventario.c.fecha_actualizacion >= dt_inicio,
            ingreso_inventario.c.fecha_actualizacion <= dt_fin
        )
    ).order_by(desc("fecha"))

    resultados = await database.fetch_all(query)

    # 2. AGRUPACIÓN: por lote_id real (Fase 13) cuando existe — ya no hace
    # falta adivinar qué llegó junto. Solo se recurre a la vieja heurística de
    # "mismo minuto + mismo usuario" para ingresos sueltos sin lote (endpoint
    # de un solo producto, usado por la app Android).
    bloques = {}

    for r in resultados:
        fecha_str = r["fecha"].strftime("%Y-%m-%d %H:%M")
        nombre_usuario = r["usuario_nombre"]

        if r["lote_id"] is not None:
            clave = f"lote-{r['lote_id']}"
        else:
            clave = f"suelto|{fecha_str}|{nombre_usuario}"

        if clave not in bloques:
            bloques[clave] = {
                "fecha": fecha_str,
                "usuario": nombre_usuario,
                "lote_id": r["lote_id"],
                "proveedor": r["proveedor"],
                "nota": r["nota"],
                "items": []
            }

        bloques[clave]["items"].append({
            "producto": r["nombre_producto"],
            "cantidad": r["cantidad"],
            "unidad": r["unidad_medida"]
        })

    # 3. Convertimos a lista y devolvemos
    return list(bloques.values())

@router.get("/reporte-cortes")
async def reporte_cortes(sucursal_id: int, inicio: date, fin: date):
    dt_inicio, dt_fin = get_rango_fechas(inicio, fin)
    
    query = select(
        corte_caja.c.id,
        corte_caja.c.fecha_apertura,
        corte_caja.c.fecha_cierre,
        corte_caja.c.ventas_totales,
        corte_caja.c.diferencia,
        usuario.c.nombre.label("usuario_nombre")
    ).select_from(
        corte_caja.join(usuario)
    ).where(
        and_(
            corte_caja.c.sucursal_id == sucursal_id,
            corte_caja.c.fecha_apertura >= dt_inicio,
            corte_caja.c.fecha_apertura <= dt_fin
        )
    ).order_by(desc(corte_caja.c.fecha_apertura))
    
    resultados = await database.fetch_all(query)
    return [
        {
            **dict(r), 
            "fecha_apertura": fecha_local_iso(r["fecha_apertura"]),
            "fecha_cierre": fecha_local_iso(r["fecha_cierre"]) if r["fecha_cierre"] else None
        } 
        for r in resultados
    ]