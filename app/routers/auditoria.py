import json
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, func, and_

from app.core.database import database, fecha_local_iso
from app.models import inventario, ajuste_inventario, producto, historial_inventario, marca
from app.schemas import AjusteInventarioIn, AjusteInventario, HistorialInventario
from app.core.dependencies import require_roles, ROL_GERENTE
from app.core.constants import TIPOS_AJUSTE, MOV_AJUSTE
from app.services.auditoria_service import analizar_tolerancia
from app.services.inventario_service import registrar_movimiento
from app.services.export_service import generar_excel

# La auditoría física la hace el Gerente (o SuperAdmin).
router = APIRouter(
    prefix="/auditoria",
    tags=["Auditoría e Historial"],
    dependencies=[Depends(require_roles(ROL_GERENTE))],
)


@router.post("/ajuste", response_model=AjusteInventario)
async def registrar_ajuste_inventario(data: AjusteInventarioIn):
    """
    Registra un conteo físico: corrige el inventario al valor real y tipifica
    la diferencia (merma, variación de fábrica, error de sistema, caducidad).
    """
    async with database.transaction():
        prod = await database.fetch_one(
            select(producto).where(producto.c.id == data.producto_id)
        )
        if not prod:
            raise HTTPException(404, "Producto no encontrado")

        # Sistema = stock real en la BD (no confiamos en el enviado por el cliente)
        inv_db = await database.fetch_one(
            select(inventario).where(
                (inventario.c.producto_id == data.producto_id)
                & (inventario.c.sucursal_id == data.sucursal_id)
            )
        )
        cantidad_sistema = float(inv_db["cantidad"]) if inv_db else 0.0
        diferencia = round(data.cantidad_fisica - cantidad_sistema, 3)

        # Tolerancia efectiva:
        #  - Si el producto tiene una tolerancia propia (>0), la usa (simétrica).
        #  - Si no, hereda la de su MARCA/empresa (asimétrica: bajo/alto).
        prod_tol = float(prod["tolerancia_unidad"] or 0)
        if prod_tol > 0:
            tol_bajo = tol_alto = prod_tol
        else:
            tol_bajo = tol_alto = 0.0
            if prod["marca_id"]:
                m = await database.fetch_one(
                    select(marca.c.tolerancia_bajo, marca.c.tolerancia_alto)
                    .where(marca.c.id == prod["marca_id"])
                )
                if m:
                    tol_bajo = float(m["tolerancia_bajo"] or 0)
                    tol_alto = float(m["tolerancia_alto"] or 0)

        limite_bajo, limite_alto, dentro, tipo_sugerido = analizar_tolerancia(
            contenido_neto=prod["contenido_neto"],
            cantidad_sistema=cantidad_sistema,
            diferencia=diferencia,
            tolerancia_bajo=tol_bajo,
            tolerancia_alto=tol_alto,
        )
        # Lado aplicable según el signo de la diferencia (para compatibilidad).
        tolerancia_calc = limite_bajo if diferencia < 0 else limite_alto

        # Tipo: el que envíe el auditor, o la sugerencia automática.
        tipo_final = data.tipo_ajuste or tipo_sugerido
        if tipo_final not in TIPOS_AJUSTE:
            raise HTTPException(
                400,
                f"tipo_ajuste inválido '{tipo_final}'. Válidos: {sorted(TIPOS_AJUSTE)}",
            )

        ahora = datetime.now(timezone.utc)

        ajuste_id = await database.execute(
            ajuste_inventario.insert().values(
                sucursal_id=data.sucursal_id,
                usuario_id=data.usuario_id,
                producto_id=data.producto_id,
                fecha=ahora,
                cantidad_sistema=cantidad_sistema,
                cantidad_fisica=data.cantidad_fisica,
                diferencia=diferencia,
                tipo_ajuste=tipo_final,
                motivo=data.motivo,
            )
        )

        # Inventario queda en el valor físico real
        if inv_db:
            await database.execute(
                inventario.update()
                .where(inventario.c.id == inv_db["id"])
                .values(cantidad=data.cantidad_fisica, fecha_actualizacion=ahora)
            )
        else:
            await database.execute(
                inventario.insert().values(
                    producto_id=data.producto_id,
                    sucursal_id=data.sucursal_id,
                    cantidad=data.cantidad_fisica,
                    fecha_actualizacion=ahora,
                )
            )

        # Bitácora
        await registrar_movimiento(
            sucursal_id=data.sucursal_id,
            usuario_id=data.usuario_id,
            producto_id=data.producto_id,
            tipo_movimiento=MOV_AJUSTE,
            cantidad_anterior=cantidad_sistema,
            cantidad_movida=diferencia,
            cantidad_nueva=data.cantidad_fisica,
            motivo=f"[{tipo_final}] {data.motivo or ''}".strip(),
        )

        return {
            "id": ajuste_id,
            "sucursal_id": data.sucursal_id,
            "usuario_id": data.usuario_id,
            "producto_id": data.producto_id,
            "cantidad_sistema": cantidad_sistema,
            "cantidad_fisica": data.cantidad_fisica,
            "diferencia": diferencia,
            "tipo_ajuste": tipo_final,
            "motivo": data.motivo,
            "fecha": ahora,
            "tolerancia_calculada": tolerancia_calc,
            "tolerancia_bajo": limite_bajo,
            "tolerancia_alto": limite_alto,
            "dentro_de_tolerancia": dentro,
            "tipo_sugerido": tipo_sugerido,
        }


@router.get("/plan-conteo")
async def plan_conteo(
    sucursal_id: int,
    tipo_producto: Optional[str] = None,
    marca_id: Optional[int] = None,
    categoria_id: Optional[int] = None,
    ubicacion: Optional[str] = None,
    atributos: Optional[str] = Query(
        None, description='JSON de atributos, ej. {"linea":"Premium"}'
    ),
):
    """
    Lista de productos para el barrido físico de una sucursal, con su stock de
    sistema y filtros (tipo, marca, categoría, ubicación, atributos JSONB).
    Pensado para auditar estantería por estantería desde el celular.
    """
    query = select(
        producto.c.id,
        producto.c.nombre,
        producto.c.unidad_medida,
        producto.c.contenido_neto,
        producto.c.tolerancia_unidad,
        producto.c.ubicacion_fisica,
        producto.c.atributos_extra,
        func.coalesce(inventario.c.cantidad, 0).label("cantidad_sistema"),
    ).select_from(
        producto.outerjoin(
            inventario,
            (inventario.c.producto_id == producto.c.id)
            & (inventario.c.sucursal_id == sucursal_id),
        )
    ).where(producto.c.activo == True)

    if tipo_producto:
        query = query.where(producto.c.tipo_producto == tipo_producto)
    if marca_id:
        query = query.where(producto.c.marca_id == marca_id)
    if categoria_id:
        query = query.where(producto.c.categoria_id == categoria_id)
    if ubicacion:
        query = query.where(producto.c.ubicacion_fisica == ubicacion)
    if atributos:
        try:
            filtros = json.loads(atributos)
        except json.JSONDecodeError:
            raise HTTPException(400, "El parámetro 'atributos' no es JSON válido")
        for clave, valor in filtros.items():
            query = query.where(
                producto.c.atributos_extra[clave].astext == str(valor)
            )

    query = query.order_by(producto.c.ubicacion_fisica.nullslast(), producto.c.nombre)
    filas = await database.fetch_all(query)
    return [dict(f) for f in filas]


@router.get("/ajustes")
async def listar_ajustes(
    sucursal_id: Optional[int] = None,
    tipo_ajuste: Optional[str] = None,
    producto_id: Optional[int] = None,
):
    """Historial de ajustes con filtros (para reportes de mermas por tipo)."""
    query = select(ajuste_inventario)
    if sucursal_id:
        query = query.where(ajuste_inventario.c.sucursal_id == sucursal_id)
    if tipo_ajuste:
        query = query.where(ajuste_inventario.c.tipo_ajuste == tipo_ajuste)
    if producto_id:
        query = query.where(ajuste_inventario.c.producto_id == producto_id)
    query = query.order_by(ajuste_inventario.c.fecha.desc())
    return [dict(r) for r in await database.fetch_all(query)]


@router.get("/ajustes/exportar/excel")
async def exportar_ajustes_excel(
    sucursal_id: Optional[int] = None,
    tipo_ajuste: Optional[str] = None,
    producto_id: Optional[int] = None,
):
    query = (
        select(ajuste_inventario, producto.c.nombre.label("producto_nombre"))
        .select_from(ajuste_inventario.join(producto))
    )
    if sucursal_id:
        query = query.where(ajuste_inventario.c.sucursal_id == sucursal_id)
    if tipo_ajuste:
        query = query.where(ajuste_inventario.c.tipo_ajuste == tipo_ajuste)
    if producto_id:
        query = query.where(ajuste_inventario.c.producto_id == producto_id)
    query = query.order_by(ajuste_inventario.c.fecha.desc())
    registros = await database.fetch_all(query)

    encabezados = ["Fecha", "Producto", "Cant. sistema", "Cant. física", "Diferencia", "Tipo de ajuste", "Motivo"]
    filas = [
        [
            fecha_local_iso(r["fecha"]).replace("T", " ")[:16],
            r["producto_nombre"],
            float(r["cantidad_sistema"]),
            float(r["cantidad_fisica"]),
            float(r["diferencia"]),
            r["tipo_ajuste"] or "",
            r["motivo"] or "",
        ]
        for r in registros
    ]
    contenido = generar_excel(encabezados, filas, "Auditoría")
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=auditoria.xlsx"},
    )


@router.get("/historial", response_model=List[HistorialInventario])
async def ver_historial(producto_id: int):
    """Ver todos los movimientos de un producto específico."""
    query = (
        historial_inventario.select()
        .where(historial_inventario.c.producto_id == producto_id)
        .order_by(historial_inventario.c.fecha.desc())
    )
    return await database.fetch_all(query)
