"""Listas gráficas por marca (Fase 16) — reproduce Lista Agromas/Api-Aba con
precios resueltos desde el catálogo, ver PLAN_FASE16.md."""
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select

from app.core.constants import LISTA_PLANTILLA_MARCAS
from app.core.database import database
from app.core.dependencies import require_perm
from app.models import lista_plantilla_fila, marca, producto
from app.schemas import (
    ImportarPlantillaResumen, ListaPlantillaFila, ListaPlantillaFilaIn,
    ListaPlantillaFilaUpdate, ListaPlantillaMarca, ReordenarIn,
)
from app.services.export_service import generar_excel_plantilla
from app.services.lista_plantilla_service import TIPO_PRODUCTO, parsear_plantilla, resolver_vinculos

router = APIRouter(prefix="/listas", tags=["Listas"])

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "plantillas"
_gestion = Depends(require_perm("productos.gestionar"))

_PANELES_VALIDOS = {"izq", "der"}
_TIPOS_VALIDOS = {"encabezado", "producto"}


def _validar_panel_tipo(panel: Optional[str], tipo: Optional[str]):
    if panel is not None and panel not in _PANELES_VALIDOS:
        raise HTTPException(400, "panel debe ser 'izq' o 'der'")
    if tipo is not None and tipo not in _TIPOS_VALIDOS:
        raise HTTPException(400, "tipo debe ser 'encabezado' o 'producto'")


async def _marca_o_404(marca_id: int):
    fila = await database.fetch_one(marca.select().where(marca.c.id == marca_id))
    if not fila:
        raise HTTPException(404, "Marca no encontrada")
    return fila


async def _filas_resueltas(marca_id: int):
    query = (
        select(
            lista_plantilla_fila,
            producto.c.nombre.label("producto_nombre"),
            producto.c.precio_base,
        )
        .select_from(
            lista_plantilla_fila.outerjoin(
                producto,
                (lista_plantilla_fila.c.producto_id == producto.c.id) & (producto.c.activo == True),
            )
        )
        .where(lista_plantilla_fila.c.marca_id == marca_id)
        .order_by(lista_plantilla_fila.c.hoja, lista_plantilla_fila.c.panel, lista_plantilla_fila.c.orden)
    )
    return [dict(f) for f in await database.fetch_all(query)]


@router.get("/plantillas-disponibles")
async def plantillas_disponibles():
    """Marcas con plantilla gráfica configurada (hoy Agromas/Api-Aba) — el
    frontend usa esto para decidir cuándo mostrar el layout gráfico vs la
    tabla plana de respaldo (Enfoque B, marcas sin plantilla)."""
    marcas = await database.fetch_all(marca.select())
    return [
        {"marca_id": m["id"], "marca_nombre": m["nombre"], "color": LISTA_PLANTILLA_MARCAS[m["nombre"]]["color"]}
        for m in marcas
        if m["nombre"] in LISTA_PLANTILLA_MARCAS
    ]


@router.get("/plantilla", response_model=ListaPlantillaMarca)
async def obtener_plantilla(marca_id: int):
    fila_marca = await _marca_o_404(marca_id)
    info = LISTA_PLANTILLA_MARCAS.get(fila_marca["nombre"])
    filas = await _filas_resueltas(marca_id)
    return ListaPlantillaMarca(
        marca_id=marca_id,
        marca_nombre=fila_marca["nombre"],
        color=(info or {}).get("color", "#6B7280"),
        filas=filas,
    )


@router.post("/plantilla/importar", response_model=ImportarPlantillaResumen, dependencies=[Depends(require_perm("catalogo.importar"))])
async def importar_plantilla(marca_id: int):
    """(Re)genera la estructura completa de una marca leyendo su .xlsx base
    (app/assets/plantillas/) y vinculando por nombre normalizado contra el
    catálogo — reemplaza cualquier fila/edición previa de esa marca."""
    fila_marca = await _marca_o_404(marca_id)
    info = LISTA_PLANTILLA_MARCAS.get(fila_marca["nombre"])
    if not info:
        raise HTTPException(400, f"La marca '{fila_marca['nombre']}' no tiene una plantilla gráfica configurada")

    ruta = _ASSETS_DIR / info["archivo"]
    if not ruta.exists():
        raise HTTPException(500, f"Archivo de plantilla no encontrado en el servidor: {info['archivo']}")

    nodos = parsear_plantilla(str(ruta))
    productos_marca = await database.fetch_all(
        producto.select().where((producto.c.marca_id == marca_id) & (producto.c.activo == True))
    )
    vinculos = resolver_vinculos(nodos, [dict(p) for p in productos_marca])

    async with database.transaction():
        await database.execute(lista_plantilla_fila.delete().where(lista_plantilla_fila.c.marca_id == marca_id))
        if nodos:
            await database.execute_many(
                lista_plantilla_fila.insert(),
                [
                    {
                        "marca_id": marca_id, "hoja": n.hoja, "panel": n.panel, "orden": n.orden,
                        "tipo": n.tipo, "nivel": n.nivel, "texto": n.texto, "producto_id": pid,
                    }
                    for n, pid in zip(nodos, vinculos)
                ],
            )

    total_productos = sum(1 for n in nodos if n.tipo == TIPO_PRODUCTO)
    return ImportarPlantillaResumen(
        marca_id=marca_id,
        total_filas=len(nodos),
        total_encabezados=len(nodos) - total_productos,
        total_productos=total_productos,
        productos_vinculados=sum(1 for pid in vinculos if pid),
    )


@router.get("/plantilla/exportar/excel")
async def exportar_plantilla_excel(marca_id: int):
    fila_marca = await _marca_o_404(marca_id)
    info = LISTA_PLANTILLA_MARCAS.get(fila_marca["nombre"])
    if not info:
        raise HTTPException(400, f"La marca '{fila_marca['nombre']}' no tiene una plantilla gráfica configurada")
    filas = await _filas_resueltas(marca_id)
    contenido = generar_excel_plantilla(fila_marca["nombre"], info["color"], filas)
    nombre_archivo = f"lista_{fila_marca['nombre'].lower().replace(' ', '_')}.xlsx"
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"},
    )


@router.post("/plantilla-filas", response_model=ListaPlantillaFila, dependencies=[_gestion])
async def crear_fila(datos: ListaPlantillaFilaIn):
    _validar_panel_tipo(datos.panel, datos.tipo)
    await _marca_o_404(datos.marca_id)
    nuevo_id = await database.execute(lista_plantilla_fila.insert().values(**datos.model_dump()))
    return await database.fetch_one(lista_plantilla_fila.select().where(lista_plantilla_fila.c.id == nuevo_id))


@router.put("/plantilla-filas/{id}", response_model=ListaPlantillaFila, dependencies=[_gestion])
async def actualizar_fila(id: int, datos: ListaPlantillaFilaUpdate):
    actual = await database.fetch_one(lista_plantilla_fila.select().where(lista_plantilla_fila.c.id == id))
    if not actual:
        raise HTTPException(404, "Fila no encontrada")

    cambios = datos.model_dump(exclude_unset=True, exclude={"desvincular"})
    if datos.desvincular:
        cambios["producto_id"] = None
    _validar_panel_tipo(cambios.get("panel"), cambios.get("tipo"))
    if not cambios:
        raise HTTPException(400, "No se enviaron cambios")

    await database.execute(lista_plantilla_fila.update().where(lista_plantilla_fila.c.id == id).values(**cambios))
    return await database.fetch_one(lista_plantilla_fila.select().where(lista_plantilla_fila.c.id == id))


@router.delete("/plantilla-filas/{id}", dependencies=[_gestion])
async def eliminar_fila(id: int):
    resultado = await database.execute(lista_plantilla_fila.delete().where(lista_plantilla_fila.c.id == id))
    if resultado == 0:
        raise HTTPException(404, "Fila no encontrada")
    return {"mensaje": "Fila eliminada"}


@router.post("/plantilla-filas/reordenar", dependencies=[_gestion])
async def reordenar_filas(datos: ReordenarIn):
    async with database.transaction():
        for item in datos.items:
            await database.execute(
                lista_plantilla_fila.update().where(lista_plantilla_fila.c.id == item.id).values(orden=item.orden)
            )
    return {"actualizadas": len(datos.items)}
