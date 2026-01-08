# routers/categorias.py

from fastapi import APIRouter, HTTPException
from typing import List

# --- Importaciones del proyecto ---
from models import categoria, subcategoria
from schemas import CategoriaIn, Categoria, SubcategoriaIn, Subcategoria
from database import database

# --- Router para Categorías ---
router = APIRouter(
    prefix="/categorias",
    tags=["Categorías y Subcategorías"]
)

@router.get("/", response_model=List[Categoria])
@router.get("", response_model=List[Categoria])
async def obtener_categorias():
    query = categoria.select()
    return await database.fetch_all(query)

@router.get("/{id}", response_model=Categoria)
async def obtener_categoria(id: int):
    query = categoria.select().where(categoria.c.id == id)
    result = await database.fetch_one(query)
    if result is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return result

@router.post("/", response_model=Categoria)
async def crear_categoria(cat: CategoriaIn):
    query = categoria.insert().values(**cat.model_dump())
    last_id = await database.execute(query)
    return {**cat.model_dump(), "id": last_id}

@router.put("/{id}", response_model=Categoria)
async def actualizar_categoria(id: int, cat: CategoriaIn):
    query = categoria.update().where(categoria.c.id == id).values(**cat.model_dump())
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return {**cat.model_dump(), "id": id}

@router.delete("/{id}")
async def eliminar_categoria(id: int):
    query = categoria.delete().where(categoria.c.id == id)
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return {"mensaje": "Categoría eliminada"}

# --- Endpoints de Subcategorías (usando el mismo router) ---

@router.get("/subcategorias/", response_model=List[Subcategoria])
async def obtener_subcategorias():
    query = subcategoria.select()
    return await database.fetch_all(query)

@router.get("/subcategorias/{id}", response_model=Subcategoria)
async def obtener_subcategoria(id: int):
    query = subcategoria.select().where(subcategoria.c.id == id)
    result = await database.fetch_one(query)
    if result is None:
        raise HTTPException(status_code=404, detail="Subcategoría no encontrada")
    return result

@router.post("/subcategorias/", response_model=Subcategoria)
async def crear_subcategoria(subcat: SubcategoriaIn):
    query = subcategoria.insert().values(**subcat.model_dump())
    last_id = await database.execute(query)
    return {**subcat.model_dump(), "id": last_id}

@router.put("/subcategorias/{id}", response_model=Subcategoria)
async def actualizar_subcategoria(id: int, subcat: SubcategoriaIn):
    query = subcategoria.update().where(subcategoria.c.id == id).values(**subcat.model_dump())
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Subcategoría no encontrada")
    return {**subcat.model_dump(), "id": id}

@router.delete("/subcategorias/{id}")
async def eliminar_subcategoria(id: int):
    query = subcategoria.delete().where(subcategoria.c.id == id)
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Subcategoría no encontrada")
    return {"mensaje": "Subcategoría eliminada"}