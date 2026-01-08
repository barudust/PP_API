# routers/atributos.py

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from models import marca, especie, etapa, tipo_producto
from schemas import ( 
    MarcaIn, Marca, EspecieIn, Especie, 
    EtapaIn, Etapa,TipoProductoIn, TipoProducto
)
from database import database

router = APIRouter(
    prefix="",  # O puedes poner "/atributos" si prefieres
    tags=["Atributos (Marcas, Especies, etc)"]
)

# === MARCAS ===
@router.get("/marcas", response_model=List[Marca])
@router.get("/marcas/", response_model=List[Marca]) 
async def obtener_marcas(q: Optional[str] = Query(None, description="Buscar por nombre")):
    query = marca.select()
    if q:
        # Búsqueda insensible a mayúsculas/minúsculas (ilike)
        query = query.where(marca.c.nombre.ilike(f"%{q}%"))
    return await database.fetch_all(query)

@router.get("/marcas/{id}", response_model=Marca)
async def obtener_marca(id: int):
    query = marca.select().where(marca.c.id == id)
    result = await database.fetch_one(query)
    if result is None:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    return result

@router.post("/marcas/", response_model=Marca)
async def crear_marca(m: MarcaIn):
    query = marca.insert().values(**m.model_dump())
    last_id = await database.execute(query)
    return {**m.model_dump(), "id": last_id}

@router.put("/marcas/{id}", response_model=Marca)
async def actualizar_marca(id: int, m: MarcaIn):
    query = marca.update().where(marca.c.id == id).values(**m.model_dump())
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    return {**m.model_dump(), "id": id}

@router.delete("/marcas/{id}")
async def eliminar_marca(id: int):
    query = marca.delete().where(marca.c.id == id)
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Marca no encontrada")
    return {"mensaje": "Marca eliminada"}


# === ESPECIES ===
@router.get("/especies", response_model=List[Especie])
@router.get("/especies/", response_model=List[Especie])
async def obtener_especies(q: Optional[str] = Query(None)):
    query = especie.select()
    if q:
        query = query.where(especie.c.nombre.ilike(f"%{q}%"))
    return await database.fetch_all(query)

@router.get("/especies/{id}", response_model=Especie)
async def obtener_especie(id: int):
    query = especie.select().where(especie.c.id == id)
    result = await database.fetch_one(query)
    if result is None:
        raise HTTPException(status_code=404, detail="Especie no encontrada")
    return result

@router.post("/especies/", response_model=Especie)
async def crear_especie(e: EspecieIn):
    query = especie.insert().values(**e.model_dump())
    last_id = await database.execute(query)
    return {**e.model_dump(), "id": last_id}

@router.put("/especies/{id}", response_model=Especie)
async def actualizar_especie(id: int, e: EspecieIn):
    query = especie.update().where(especie.c.id == id).values(**e.model_dump())
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Especie no encontrada")
    return {**e.model_dump(), "id": id}

@router.delete("/especies/{id}")
async def eliminar_especie(id: int):
    query = especie.delete().where(especie.c.id == id)
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Especie no encontrada")
    return {"mensaje": "Especie eliminada"}


# === ETAPAS ===
@router.get("/etapas", response_model=List[Etapa])
@router.get("/etapas/", response_model=List[Etapa])
async def obtener_etapas(q: Optional[str] = Query(None)):
    query = etapa.select()
    if q:
        query = query.where(etapa.c.nombre.ilike(f"%{q}%"))
    return await database.fetch_all(query)

@router.get("/etapas/{id}", response_model=Etapa)
async def obtener_etapa(id: int):
    query = etapa.select().where(etapa.c.id == id)
    result = await database.fetch_one(query)
    if result is None:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")
    return result

@router.post("/etapas/", response_model=Etapa)
async def crear_etapa(e: EtapaIn):
    query = etapa.insert().values(**e.model_dump())
    last_id = await database.execute(query)
    return {**e.model_dump(), "id": last_id}

@router.put("/etapas/{id}", response_model=Etapa)
async def actualizar_etapa(id: int, e: EtapaIn):
    query = etapa.update().where(etapa.c.id == id).values(**e.model_dump())
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")
    return {**e.model_dump(), "id": id}

@router.delete("/etapas/{id}")
async def eliminar_etapa(id: int):
    query = etapa.delete().where(etapa.c.id == id)
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")
    return {"mensaje": "Etapa eliminada"}




@router.get("/tipos-producto", response_model=List[str])
async def obtener_tipos_producto():
    """Devuelve la lista de tipos de producto permitidos."""
    return ["Alimento", "Materia Prima", "Accesorio", "Medicina", "Agricola"]

@router.get("/unidades-medida", response_model=List[str])
async def obtener_unidades_medida():
    """Devuelve la lista de unidades de medida permitidas."""
    return ["pza", "kg", "lt", "bulto", "caja", "bote", "sobre", "bolsa"]

@router.get("/tipos-producto/", response_model=List[TipoProducto])
async def obtener_tipos():
    query = tipo_producto.select()
    return await database.fetch_all(query)

@router.post("/tipos-producto/", response_model=TipoProducto)
async def crear_tipo(t: TipoProductoIn):
    query = tipo_producto.insert().values(nombre=t.nombre)
    last_id = await database.execute(query)
    return {**t.model_dump(), "id": last_id}
# En routers/atributos.py

@router.delete("/tipos-producto/{id}")
async def eliminar_tipo(id: int):
    query = tipo_producto.delete().where(tipo_producto.c.id == id)
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Tipo de producto no encontrado")
    return {"mensaje": "Tipo de producto eliminado"}