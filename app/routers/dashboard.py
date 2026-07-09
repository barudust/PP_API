"""
Dashboard analítico del SuperAdmin (KPIs en tiempo real).

Todos los endpoints son de solo lectura y exigen rol SuperAdmin. Aceptan un
filtro opcional `sucursal_id` para aislar la vista a una sola sucursal.
"""
from typing import Optional
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_, desc

from app.core.database import database
from app.core.config import settings
from app.models import (
    venta,
    venta_detalle,
    producto,
    inventario,
    sucursal,
    corte_caja,
    usuario,
    ajuste_inventario,
)
from app.core.dependencies import require_roles, ROL_SUPERADMIN

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard SuperAdmin"],
    dependencies=[Depends(require_roles(ROL_SUPERADMIN))],
)

_TZ = ZoneInfo(settings.TIMEZONE)


def _rango_dias(dias: int):
    """Devuelve (inicio_utc, fin_utc) para los últimos `dias` (incluyendo hoy)."""
    ahora_local = datetime.now(_TZ)
    inicio_local = (ahora_local - _dias(dias)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return inicio_local.astimezone(timezone.utc), ahora_local.astimezone(timezone.utc)


def _dias(n: int):
    from datetime import timedelta
    return timedelta(days=n)


def _rango_fechas(inicio: date, fin: date):
    ini = datetime.combine(inicio, time.min).replace(tzinfo=_TZ).astimezone(timezone.utc)
    fnl = datetime.combine(fin, time.max).replace(tzinfo=_TZ).astimezone(timezone.utc)
    return ini, fnl


async def _suma_ventas(desde, hasta, sucursal_id: Optional[int]):
    q = select(
        func.coalesce(func.sum(venta.c.total), 0),
        func.count(venta.c.id),
    ).where(and_(venta.c.fecha >= desde, venta.c.fecha <= hasta))
    if sucursal_id:
        q = q.where(venta.c.sucursal_id == sucursal_id)
    fila = await database.fetch_one(q)
    return float(fila[0] or 0), int(fila[1] or 0)


@router.get("/resumen")
async def resumen(sucursal_id: Optional[int] = None):
    """KPIs de cabecera: ventas hoy/semana/mes, tickets, stock crítico y cajas."""
    hoy_ini, ahora = _rango_dias(0)
    sem_ini, _ = _rango_dias(6)
    mes_ini, _ = _rango_dias(29)

    ventas_hoy, n_hoy = await _suma_ventas(hoy_ini, ahora, sucursal_id)
    ventas_semana, _ = await _suma_ventas(sem_ini, ahora, sucursal_id)
    ventas_mes, n_mes = await _suma_ventas(mes_ini, ahora, sucursal_id)

    ticket_promedio = round(ventas_hoy / n_hoy, 2) if n_hoy else 0.0

    # Stock crítico (consolidado o por sucursal)
    criticos = await _stock_critico(sucursal_id)

    # Cajas abiertas ahora
    q_cajas = select(func.count(corte_caja.c.id)).where(corte_caja.c.fecha_cierre == None)
    if sucursal_id:
        q_cajas = q_cajas.where(corte_caja.c.sucursal_id == sucursal_id)
    cajas_abiertas = await database.fetch_val(q_cajas) or 0

    return {
        "sucursal_id": sucursal_id,
        "ventas_hoy": ventas_hoy,
        "num_ventas_hoy": n_hoy,
        "ticket_promedio_hoy": ticket_promedio,
        "ventas_semana": ventas_semana,
        "ventas_mes": ventas_mes,
        "num_ventas_mes": n_mes,
        "productos_stock_critico": len(criticos),
        "cajas_abiertas": int(cajas_abiertas),
    }


@router.get("/ventas-por-sucursal")
async def ventas_por_sucursal(inicio: Optional[date] = None, fin: Optional[date] = None):
    """Ventas totales agrupadas por sucursal en el rango (default: últimos 30 días)."""
    if inicio and fin:
        desde, hasta = _rango_fechas(inicio, fin)
    else:
        desde, hasta = _rango_dias(29)

    q = select(
        sucursal.c.id,
        sucursal.c.nombre,
        func.coalesce(func.sum(venta.c.total), 0).label("total_ventas"),
        func.count(venta.c.id).label("num_ventas"),
    ).select_from(
        sucursal.outerjoin(
            venta,
            (venta.c.sucursal_id == sucursal.c.id)
            & (venta.c.fecha >= desde)
            & (venta.c.fecha <= hasta),
        )
    ).group_by(sucursal.c.id, sucursal.c.nombre).order_by(desc("total_ventas"))

    filas = await database.fetch_all(q)
    return [
        {
            "sucursal_id": f["id"],
            "sucursal": f["nombre"],
            "total_ventas": float(f["total_ventas"] or 0),
            "num_ventas": int(f["num_ventas"] or 0),
        }
        for f in filas
    ]


@router.get("/top-productos")
async def top_productos(
    inicio: Optional[date] = None,
    fin: Optional[date] = None,
    limite: int = 10,
    sucursal_id: Optional[int] = None,
):
    """Productos más vendidos por ingreso (y cantidad) en el rango."""
    if inicio and fin:
        desde, hasta = _rango_fechas(inicio, fin)
    else:
        desde, hasta = _rango_dias(29)

    ingreso = func.sum(venta_detalle.c.cantidad * venta_detalle.c.precio_unitario)
    q = select(
        producto.c.id,
        producto.c.nombre,
        func.sum(venta_detalle.c.cantidad).label("cantidad_vendida"),
        func.coalesce(ingreso, 0).label("ingreso"),
    ).select_from(
        venta_detalle.join(venta, venta_detalle.c.venta_id == venta.c.id)
        .join(producto, venta_detalle.c.producto_id == producto.c.id)
    ).where(and_(venta.c.fecha >= desde, venta.c.fecha <= hasta))

    if sucursal_id:
        q = q.where(venta.c.sucursal_id == sucursal_id)

    q = q.group_by(producto.c.id, producto.c.nombre).order_by(desc("ingreso")).limit(limite)

    filas = await database.fetch_all(q)
    return [
        {
            "producto_id": f["id"],
            "nombre": f["nombre"],
            "cantidad_vendida": float(f["cantidad_vendida"] or 0),
            "ingreso": float(f["ingreso"] or 0),
        }
        for f in filas
    ]


async def _stock_critico(sucursal_id: Optional[int]):
    """Productos activos cuyo stock cae por debajo de su mínimo."""
    if sucursal_id:
        stock_col = func.coalesce(
            func.sum(
                inventario.c.cantidad
            ).filter(inventario.c.sucursal_id == sucursal_id),
            0,
        )
    else:
        stock_col = func.coalesce(func.sum(inventario.c.cantidad), 0)

    q = select(
        producto.c.id,
        producto.c.nombre,
        producto.c.unidad_medida,
        producto.c.stock_minimo,
        stock_col.label("stock_actual"),
    ).select_from(
        producto.outerjoin(inventario, inventario.c.producto_id == producto.c.id)
    ).where(producto.c.activo == True).group_by(
        producto.c.id, producto.c.nombre, producto.c.unidad_medida, producto.c.stock_minimo
    ).having(stock_col < producto.c.stock_minimo).order_by("stock_actual")

    filas = await database.fetch_all(q)
    return [
        {
            "producto_id": f["id"],
            "nombre": f["nombre"],
            "unidad_medida": f["unidad_medida"],
            "stock_actual": float(f["stock_actual"] or 0),
            "stock_minimo": float(f["stock_minimo"] or 0),
        }
        for f in filas
    ]


@router.get("/stock-critico")
async def stock_critico(sucursal_id: Optional[int] = None):
    return await _stock_critico(sucursal_id)


@router.get("/cajas")
async def estado_cajas(sucursal_id: Optional[int] = None):
    """Estado de cajas: abiertas ahora y cortes cerrados hoy con su diferencia."""
    hoy_ini, ahora = _rango_dias(0)

    base = select(
        corte_caja.c.id,
        corte_caja.c.sucursal_id,
        sucursal.c.nombre.label("sucursal"),
        usuario.c.nombre.label("usuario"),
        corte_caja.c.fecha_apertura,
        corte_caja.c.fecha_cierre,
        corte_caja.c.ventas_totales,
        corte_caja.c.diferencia,
    ).select_from(corte_caja.join(sucursal).join(usuario))

    if sucursal_id:
        base = base.where(corte_caja.c.sucursal_id == sucursal_id)

    abiertas = await database.fetch_all(
        base.where(corte_caja.c.fecha_cierre == None)
    )
    cerradas_hoy = await database.fetch_all(
        base.where(
            and_(
                corte_caja.c.fecha_cierre != None,
                corte_caja.c.fecha_cierre >= hoy_ini,
            )
        )
    )

    def _fmt(rows):
        return [
            {
                "corte_id": r["id"],
                "sucursal": r["sucursal"],
                "usuario": r["usuario"],
                "ventas_totales": float(r["ventas_totales"] or 0),
                "diferencia": float(r["diferencia"]) if r["diferencia"] is not None else None,
            }
            for r in rows
        ]

    return {"abiertas": _fmt(abiertas), "cerradas_hoy": _fmt(cerradas_hoy)}


@router.get("/rendimiento-financiero")
async def rendimiento_financiero(
    inicio: Optional[date] = None,
    fin: Optional[date] = None,
    sucursal_id: Optional[int] = None,
):
    """Ventas, descuentos y descuadres de caja en el rango (default: 30 días)."""
    if inicio and fin:
        desde, hasta = _rango_fechas(inicio, fin)
    else:
        desde, hasta = _rango_dias(29)

    q_v = select(
        func.coalesce(func.sum(venta.c.total), 0),
        func.coalesce(func.sum(venta.c.descuento_especial_monto), 0),
        func.count(venta.c.id),
    ).where(and_(venta.c.fecha >= desde, venta.c.fecha <= hasta))
    if sucursal_id:
        q_v = q_v.where(venta.c.sucursal_id == sucursal_id)
    total, descuentos, n = await database.fetch_one(q_v)

    # Descuadres de caja (suma de diferencias de cortes cerrados en el rango)
    q_c = select(func.coalesce(func.sum(corte_caja.c.diferencia), 0)).where(
        and_(corte_caja.c.fecha_cierre >= desde, corte_caja.c.fecha_cierre <= hasta)
    )
    if sucursal_id:
        q_c = q_c.where(corte_caja.c.sucursal_id == sucursal_id)
    descuadre = await database.fetch_val(q_c) or 0

    return {
        "ventas_totales": float(total or 0),
        "descuentos_especiales": float(descuentos or 0),
        "num_ventas": int(n or 0),
        "descuadre_caja": float(descuadre),
    }
