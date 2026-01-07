from fastapi import APIRouter, HTTPException
from typing import List, Optional
from models import producto
from schemas import ProductoIn, Producto, ProductoUpdate
from database import database

router = APIRouter(
    prefix="/productos",
    tags=["Productos"]
)

@router.get("/", response_model=List[Producto])
async def obtener_productos(
    tipo: Optional[str] = None, # Filtro por tipo (Alimento, Accesorio...)
    mostrar_inactivos: bool = False # Filtro soft-delete
):
    query = producto.select()
    
    # 1. Filtro de Activos (Soft Delete)
    if not mostrar_inactivos:
        query = query.where(producto.c.activo == True)
    
    # 2. Filtro por Tipo de Producto
    if tipo:
        query = query.where(producto.c.tipo_producto == tipo)
        
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
    datos = prod.model_dump()
    # Forzamos activo al crear
    datos["activo"] = True 
    query = producto.insert().values(**datos)
    last_id = await database.execute(query)
    return {**datos, "id": last_id}

@router.put("/{id}", response_model=Producto)
async def actualizar_producto(id: int, prod: ProductoIn):
    query = producto.update().where(producto.c.id == id).values(**prod.model_dump())
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {**prod.model_dump(), "id": id}

@router.patch("/{id}", response_model=Producto)
async def actualizar_parcial_producto(id: int, prod: ProductoUpdate): # <--- CAMBIO AQUÍ
    # 1. Extraemos solo los datos que SÍ enviaste
    datos_actualizar = prod.model_dump(exclude_unset=True)
    
    if not datos_actualizar:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

    # 2. Ejecutamos la actualización en BD
    query = producto.update().where(producto.c.id == id).values(**datos_actualizar)
    result = await database.execute(query)
    
    if result == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # 3. Recuperamos el producto actualizado
    query_get = producto.select().where(producto.c.id == id)
    return await database.fetch_one(query_get)

@router.delete("/{id}")
async def eliminar_producto(id: int):
    # Soft Delete: Solo cambiamos el estado, no borramos
    query = producto.update().where(producto.c.id == id).values(activo=False)
    result = await database.execute(query)
    
    if result == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    return {"mensaje": "Producto suspendido (soft-delete) exitosamente"}