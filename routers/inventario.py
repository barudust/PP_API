# routers/inventario.py

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update, func

# --- Importaciones del proyecto ---
from models import inventario, ingreso_inventario, producto, sucursal
from schemas import InventarioIn, Inventario, IngresoInventarioIn, IngresoInventario
from database import database, fecha_local_iso, fecha_local_iso_simple

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

@router.post("/ingreso-inventario/", response_model=IngresoInventario)
async def ingresar_inventario(data: IngresoInventarioIn):
    
    # 1. OBTENER EL PESO DEL BULTO
    query_prod = select(producto).where(producto.c.id == data.producto_id)
    prod_obj = await database.fetch_one(query_prod)
    
    if not prod_obj:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # 2. CALCULAR KILOS REALES
    # data.cantidad viene del frontend (ej: 5 bultos)
    # contenido_neto es Decimal en DB, lo convertimos a float
    contenido_neto = float(prod_obj["contenido_neto"])
    kilos_reales = float(data.cantidad) * contenido_neto

    # 3. ACTUALIZAR O CREAR INVENTARIO
    query_inventario = select(inventario).where(
        (inventario.c.producto_id == data.producto_id) &
        (inventario.c.sucursal_id == data.sucursal_id)
    )
    result = await database.fetch_one(query_inventario)

    if result:
        # --- CORRECCIÓN CRÍTICA AQUÍ ---
        # Convertimos result["cantidad"] (Decimal) a float antes de sumar
        cantidad_actual = float(result["cantidad"])
        nueva_cantidad = cantidad_actual + kilos_reales
        
        update_query = (
            update(inventario)
            .where(inventario.c.id == result["id"])
            .values(
                cantidad=nueva_cantidad,
                fecha_actualizacion=datetime.now(timezone.utc)
            )
        )
        await database.execute(update_query)
    else:   
        # Crear nuevo registro
        insert_inventario = inventario.insert().values(
            producto_id=data.producto_id,
            sucursal_id=data.sucursal_id,
            cantidad=kilos_reales, 
            fecha_actualizacion=datetime.now(timezone.utc)
        )
        await database.execute(insert_inventario)

    # 4. REGISTRAR EL MOVIMIENTO
    insert_ingreso = ingreso_inventario.insert().values(
        producto_id=data.producto_id,
        sucursal_id=data.sucursal_id,
        cantidad=data.cantidad, # Guardamos "5 bultos" tal cual para el historial
        usuario_id=data.usuario_id
    )
    id_insertado = await database.execute(insert_ingreso)

    ingreso_query = ingreso_inventario.select().where(ingreso_inventario.c.id == id_insertado)
    ingreso = await database.fetch_one(ingreso_query)
    
    # Formatear fecha para respuesta
    ingreso_dict = dict(ingreso)
    ingreso_dict["fecha_actualizacion"] = fecha_local_iso(ingreso_dict["fecha_actualizacion"])
    
    return IngresoInventario(**ingreso_dict)


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