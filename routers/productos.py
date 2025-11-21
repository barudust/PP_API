# routers/productos.py

from fastapi import APIRouter, HTTPException
from typing import List

# --- Importaciones del proyecto ---
from models import producto
from schemas import ProductoIn, Producto
from database import database # Importamos la DB desde nuestro nuevo archivo

# 1. Creamos el router
router = APIRouter(
    prefix="/productos", # Todas las rutas aquí empiezan con /productos
    tags=["Productos"]   # Para agrupar en la documentación /docs
)

# 2. Copiamos tus endpoints, pero con @router y rutas relativas
@router.get("/", response_model=List[Producto])
async def obtener_productos():
    query = producto.select()
    return await database.fetch_all(query)

@router.get("/{id}", response_model=Producto)
async def obtener_producto(id: int):
    query = producto.select().where(producto.c.id == id)
    result = await database.fetch_one(query)
    if result is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return result

@router.post("/", response_model=Producto)
async def crear_producto(prod: ProductoIn):
    query = producto.insert().values(**prod.model_dump())
    last_id = await database.execute(query)
    return {**prod.model_dump(), "id": last_id}

@router.put("/{id}", response_model=Producto)
async def actualizar_producto(id: int, prod: ProductoIn):
    query = producto.update().where(producto.c.id == id).values(**prod.model_dump())
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {**prod.model_dump(), "id": id}

@router.delete("/{id}")
async def eliminar_producto(id: int):
    query = producto.delete().where(producto.c.id == id)
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"mensaje": "Producto eliminado"}