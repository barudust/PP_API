# routers/inventario.py

from fastapi import APIRouter, HTTPException, Query, Response
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update, func

# --- Importaciones del proyecto ---
from app.models import inventario, ingreso_inventario, ingreso_inventario_lote, producto, sucursal, usuario
from app.schemas import (
    InventarioIn, Inventario, IngresoInventarioIn, IngresoInventario,
    IngresoInventarioLoteIn, IngresoInventarioLoteResumen, IngresoInventarioLoteDetalle,
)
from app.core.database import database, fecha_local_iso, fecha_local_iso_simple
from app.core.constants import MOV_COMPRA
from app.services.inventario_service import registrar_movimiento
from app.services.export_service import generar_excel

router = APIRouter(
    tags=["Inventario"]
)

# === INVENTARIO ===

@router.get("/inventario", response_model=List[Inventario])
async def obtener_inventario(
    producto_id: Optional[int] = Query(None),
    sucursal_id: Optional[int] = Query(None)
):
    query = inventario.select()
    if producto_id is not None:
        query = query.where(inventario.c.producto_id == producto_id)
    if sucursal_id is not None:
        query = query.where(inventario.c.sucursal_id == sucursal_id)
    
    registros = await database.fetch_all(query)
    return [Inventario.from_orm(r) for r in registros]

@router.get("/inventario/{id}", response_model=Inventario)
async def obtener_inventario_id(id: int):
    query = inventario.select().where(inventario.c.id == id)
    r = await database.fetch_one(query)
    if r is None:
        raise HTTPException(status_code=404, detail="Inventario no encontrado")
    return Inventario.from_orm(r)

@router.post("/inventario", response_model=Inventario)
async def crear_inventario(item: InventarioIn):
    query = inventario.insert().values(**item.model_dump())
    last_id = await database.execute(query)
    query_get = inventario.select().where(inventario.c.id == last_id)
    created = await database.fetch_one(query_get)
    return Inventario.from_orm(created)

@router.put("/inventario/{id}", response_model=Inventario)
async def actualizar_inventario(id: int, item: InventarioIn):
    query = inventario.update().where(inventario.c.id == id).values(
        **item.model_dump(),
        fecha_actualizacion=datetime.now(timezone.utc)
    )
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Inventario no encontrado")
    query_get = inventario.select().where(inventario.c.id == id)
    updated = await database.fetch_one(query_get)
    return Inventario.from_orm(updated)

@router.delete("/inventario/{id}")
async def eliminar_inventario(id: int):
    query = inventario.delete().where(inventario.c.id == id)
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Inventario no encontrado")
    return {"mensaje": "Inventario eliminado"}

# === INGRESO DE INVENTARIO (Lógica de Negocio) ===

async def _registrar_ingreso_linea(
    sucursal_id: int, usuario_id: int, producto_id: int, cantidad: float, lote_id: Optional[int] = None
) -> int:
    """Una línea de ingreso: actualiza inventario, inserta el registro de
    ingreso y la bitácora. Debe llamarse dentro de una transacción abierta
    por quien invoca (permite agrupar varias líneas de un lote de forma
    atómica: si una falla, ninguna se aplica)."""
    prod_obj = await database.fetch_one(select(producto).where(producto.c.id == producto_id))
    if not prod_obj:
        raise HTTPException(status_code=404, detail=f"Producto {producto_id} no encontrado")

    # data.cantidad viene del frontend (ej: 5 bultos) — se convierte a kilos/unidad base
    contenido_neto = float(prod_obj["contenido_neto"])
    kilos_reales = float(cantidad) * contenido_neto

    query_inventario = select(inventario).where(
        (inventario.c.producto_id == producto_id) & (inventario.c.sucursal_id == sucursal_id)
    )
    result = await database.fetch_one(query_inventario)

    cantidad_anterior = float(result["cantidad"]) if result else 0.0
    nueva_cantidad = cantidad_anterior + kilos_reales

    if result:
        await database.execute(
            update(inventario)
            .where(inventario.c.id == result["id"])
            .values(cantidad=nueva_cantidad, fecha_actualizacion=datetime.now(timezone.utc))
        )
    else:
        await database.execute(
            inventario.insert().values(
                producto_id=producto_id,
                sucursal_id=sucursal_id,
                cantidad=kilos_reales,
                fecha_actualizacion=datetime.now(timezone.utc),
            )
        )

    id_insertado = await database.execute(
        ingreso_inventario.insert().values(
            producto_id=producto_id,
            sucursal_id=sucursal_id,
            cantidad=cantidad,
            usuario_id=usuario_id,
            lote_id=lote_id,
        )
    )

    await registrar_movimiento(
        sucursal_id=sucursal_id,
        usuario_id=usuario_id,
        producto_id=producto_id,
        tipo_movimiento=MOV_COMPRA,
        cantidad_anterior=cantidad_anterior,
        cantidad_movida=kilos_reales,
        cantidad_nueva=nueva_cantidad,
        motivo=f"Ingreso de {cantidad} ({prod_obj['unidad_medida']})",
    )
    return id_insertado


@router.post("/ingreso-inventario/", response_model=IngresoInventario)
async def ingresar_inventario(data: IngresoInventarioIn):
    # Ingreso suelto de un solo producto — lo sigue usando la app Android.
    # Todo el ingreso corre en una transacción atómica.
    async with database.transaction():
        id_insertado = await _registrar_ingreso_linea(
            data.sucursal_id, data.usuario_id, data.producto_id, data.cantidad
        )

    ingreso = await database.fetch_one(ingreso_inventario.select().where(ingreso_inventario.c.id == id_insertado))
    ingreso_dict = dict(ingreso)
    ingreso_dict["fecha_actualizacion"] = fecha_local_iso(ingreso_dict["fecha_actualizacion"])
    return IngresoInventario(**ingreso_dict)


@router.post("/ingreso-inventario/lote", response_model=IngresoInventarioLoteDetalle)
async def ingresar_inventario_lote(data: IngresoInventarioLoteIn):
    """Surtir varios productos de una sola vez (ej. una entrega de proveedor)
    — todas las líneas quedan agrupadas bajo un mismo lote para poder
    auditar después qué se recibió junto, quién lo registró y cuándo."""
    if not data.lineas:
        raise HTTPException(400, "El lote debe traer al menos una línea")

    async with database.transaction():
        lote_id = await database.execute(
            ingreso_inventario_lote.insert().values(
                sucursal_id=data.sucursal_id,
                usuario_id=data.usuario_id,
                proveedor=data.proveedor,
                nota=data.nota,
            )
        )
        for linea in data.lineas:
            await _registrar_ingreso_linea(
                data.sucursal_id, data.usuario_id, linea.producto_id, linea.cantidad, lote_id=lote_id
            )

    return await _detalle_lote_ingreso(lote_id)


async def _detalle_lote_ingreso(lote_id: int) -> dict:
    lote = await database.fetch_one(
        select(ingreso_inventario_lote, usuario.c.nombre.label("usuario_nombre"))
        .select_from(ingreso_inventario_lote.join(usuario))
        .where(ingreso_inventario_lote.c.id == lote_id)
    )
    if not lote:
        raise HTTPException(404, "Lote de ingreso no encontrado")

    query_lineas = (
        select(
            ingreso_inventario.c.producto_id,
            producto.c.nombre.label("producto_nombre"),
            producto.c.unidad_medida,
            ingreso_inventario.c.cantidad,
        )
        .select_from(ingreso_inventario.join(producto))
        .where(ingreso_inventario.c.lote_id == lote_id)
        .order_by(ingreso_inventario.c.id)
    )
    lineas = await database.fetch_all(query_lineas)

    return {
        "id": lote["id"],
        "fecha": fecha_local_iso_simple(lote["fecha"]),
        "sucursal_id": lote["sucursal_id"],
        "usuario_id": lote["usuario_id"],
        "usuario_nombre": lote["usuario_nombre"],
        "proveedor": lote["proveedor"],
        "nota": lote["nota"],
        "num_lineas": len(lineas),
        "total_unidades": float(sum(l["cantidad"] for l in lineas)),
        "lineas": [dict(l) for l in lineas],
    }


@router.get("/ingreso-inventario/lotes", response_model=List[IngresoInventarioLoteResumen])
async def listar_lotes_ingreso(sucursal_id: Optional[int] = None):
    """Historial de lotes de ingreso — para poder auditar qué se surtió y
    cuándo, agrupado como se registró (no línea por línea suelta)."""
    query = select(ingreso_inventario_lote, usuario.c.nombre.label("usuario_nombre")).select_from(
        ingreso_inventario_lote.join(usuario)
    )
    if sucursal_id is not None:
        query = query.where(ingreso_inventario_lote.c.sucursal_id == sucursal_id)
    query = query.order_by(ingreso_inventario_lote.c.fecha.desc())
    lotes = await database.fetch_all(query)

    if not lotes:
        return []

    ids = [l["id"] for l in lotes]
    query_totales = (
        select(
            ingreso_inventario.c.lote_id,
            func.count().label("num_lineas"),
            func.sum(ingreso_inventario.c.cantidad).label("total_unidades"),
        )
        .where(ingreso_inventario.c.lote_id.in_(ids))
        .group_by(ingreso_inventario.c.lote_id)
    )
    totales = {t["lote_id"]: t for t in await database.fetch_all(query_totales)}

    return [
        {
            "id": l["id"],
            "fecha": fecha_local_iso_simple(l["fecha"]),
            "sucursal_id": l["sucursal_id"],
            "usuario_id": l["usuario_id"],
            "usuario_nombre": l["usuario_nombre"],
            "proveedor": l["proveedor"],
            "nota": l["nota"],
            "num_lineas": totales[l["id"]]["num_lineas"] if l["id"] in totales else 0,
            "total_unidades": float(totales[l["id"]]["total_unidades"]) if l["id"] in totales else 0.0,
        }
        for l in lotes
    ]


@router.get("/ingreso-inventario/lotes/{lote_id}", response_model=IngresoInventarioLoteDetalle)
async def obtener_lote_ingreso(lote_id: int):
    return await _detalle_lote_ingreso(lote_id)


@router.get("/ingresos-inventario/")
async def listar_ingresos_inventario(
    producto_id: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    usuario_id: Optional[int] = None,
    fecha_inicio: Optional[datetime] = Query(None),
    fecha_fin: Optional[datetime] = Query(None)
):
    query = ingreso_inventario.select()
    if producto_id is not None:
        query = query.where(ingreso_inventario.c.producto_id == producto_id)
    if sucursal_id is not None:
        query = query.where(ingreso_inventario.c.sucursal_id == sucursal_id)
    if usuario_id is not None:
        query = query.where(ingreso_inventario.c.usuario_id == usuario_id)
    if fecha_inicio is not None:
        query = query.where(ingreso_inventario.c.fecha_actualizacion >= fecha_inicio)
    if fecha_fin is not None:
        fecha_fin += timedelta(days=1)
        query = query.where(ingreso_inventario.c.fecha_actualizacion < fecha_fin)

    resultados = await database.fetch_all(query)

    resultados_formateados = [
        {
            "id": r["id"],
            "producto_id": r["producto_id"],
            "sucursal_id": r["sucursal_id"],
            "cantidad": r["cantidad"],
            "usuario_id": r["usuario_id"],
            "fecha_actualizacion": fecha_local_iso_simple(r["fecha_actualizacion"])
        }
        for r in resultados
    ]
    return resultados_formateados


@router.get("/inventario/reporte-sucursal/{sucursal_id}")
async def reporte_inventario_sucursal(sucursal_id: int):
    query = select(
        producto.c.id,
        producto.c.nombre,
        producto.c.unidad_medida,
        producto.c.codigo_barras,
        producto.c.precio_base,
        producto.c.contenido_neto, # <--- ¡AGREGAR ESTA LÍNEA!
        func.coalesce(inventario.c.cantidad, 0).label("cantidad_actual")
    ).select_from(
        producto.outerjoin(
            inventario, 
            (inventario.c.producto_id == producto.c.id) & 
            (inventario.c.sucursal_id == sucursal_id)
        )
    ).where(
        producto.c.activo == True
    ).order_by(producto.c.nombre)
    
    resultados = await database.fetch_all(query)
    return [dict(r) for r in resultados]


@router.get("/inventario/reporte-sucursal/{sucursal_id}/exportar/excel")
async def exportar_reporte_inventario_excel(sucursal_id: int):
    query = select(
        producto.c.nombre,
        producto.c.codigo_barras,
        producto.c.unidad_medida,
        producto.c.precio_base,
        func.coalesce(inventario.c.cantidad, 0).label("cantidad_actual"),
    ).select_from(
        producto.outerjoin(
            inventario,
            (inventario.c.producto_id == producto.c.id) &
            (inventario.c.sucursal_id == sucursal_id)
        )
    ).where(
        producto.c.activo == True
    ).order_by(producto.c.nombre)

    resultados = await database.fetch_all(query)
    encabezados = ["Producto", "Código de barras", "Unidad", "Precio", "Existencia actual"]
    filas = [
        [r["nombre"], r["codigo_barras"] or "", r["unidad_medida"], float(r["precio_base"]), float(r["cantidad_actual"])]
        for r in resultados
    ]
    contenido = generar_excel(encabezados, filas, "Inventario")
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=inventario.xlsx"},
    )