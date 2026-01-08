from fastapi import APIRouter, HTTPException
from typing import List, Optional
from schemas import ProductoIn, Producto, ProductoUpdate
from sqlalchemy import select, func
from database import database
from models import producto, inventario  


router = APIRouter(
    prefix="/productos",
    tags=["Productos"]
)


@router.get("/", response_model=List[Producto])
async def obtener_productos(
    tipo: Optional[str] = None, 
    mostrar_inactivos: bool = False 
):
    # Construimos una consulta INTELIGENTE que une Producto + Inventario
    query = select(
        producto, # Trae todas las columnas del producto
        # Sumamos el inventario (si es nulo, ponemos 0) y lo llamamos 'stock_actual'
        func.coalesce(func.sum(inventario.c.cantidad), 0).label("stock_actual")
    ).select_from(
        # Unimos las tablas (Left Join para no perder productos sin stock)
        producto.outerjoin(inventario, producto.c.id == inventario.c.producto_id)
    ).group_by(producto.c.id) # Agrupamos para poder sumar
    
    # Aplicamos tus filtros
    if not mostrar_inactivos:
        query = query.where(producto.c.activo == True)
    
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
    
    # --- CEREBRO DE UNIDADES (CORRECCIÓN AUTOMÁTICA) ---
    unidad = datos.get("unidad_medida", "Pieza")
    
    # REGLA 1: Unidades Base
    # Si es Kg, Litro o Pieza, el contenido neto A FUERZA es 1.0.
    # Esto evita que guardes "1 Kg de 40kg".
    if unidad in ["Kg", "Litro", "Pieza", "Collar", "Unidad"]:
        datos["contenido_neto"] = 1.0
    
    # REGLA 2: Granel Automático
    # Si es Kg o Litro, por lógica se vende a granel (fraccionado).
    if unidad in ["Kg", "Litro"]:
        datos["se_vende_a_granel"] = True

    # REGLA 3: Piezas Cerradas
    # Una Pieza normal (ej. Collar) no se vende a granel (no vendes medio collar).
    if unidad in ["Pieza", "Collar", "Unidad", "Bote"]:
        datos["se_vende_a_granel"] = False
        
    # (Solo Bulto, Saco, Caja y Paquete respetan lo que pongas en contenido y granel)
    # ---------------------------------------------------

    datos["activo"] = True 
    query = producto.insert().values(**datos)
    last_id = await database.execute(query)
    
    # Devolvemos los datos ya corregidos para que Android se actualice
    return {**datos, "id": last_id}

@router.patch("/{id}/", response_model=Producto)
@router.put("/{id}/", response_model=Producto)
@router.patch("/{id}", response_model=Producto)
@router.put("/{id}", response_model=Producto)
async def actualizar_parcial_producto(id: int, prod: ProductoUpdate):

    # 1. Separar datos
    datos_actualizar = prod.model_dump(exclude_unset=True)
    nuevo_stock = datos_actualizar.pop("stock", None) # Sacamos el stock

    if not datos_actualizar and nuevo_stock is None:
         raise HTTPException(status_code=400, detail="No se enviaron datos válidos")

    # 2. Actualizar datos del producto (Nombre, Precio, etc.)
    if datos_actualizar:
        query = producto.update().where(producto.c.id == id).values(**datos_actualizar)
        result = await database.execute(query)
        if result == 0 and nuevo_stock is None: 
            raise HTTPException(status_code=404, detail="Producto no encontrado")

    # 3. ACTUALIZAR INVENTARIO (CON CONVERSIÓN INTELIGENTE)
    if nuevo_stock is not None:
        SUCURSAL_DEFAULT = 1 
        
        # A. Primero consultamos el producto para saber su factor de conversión
        query_prod = producto.select().where(producto.c.id == id)
        prod_info = await database.fetch_one(query_prod)
        
        cantidad_a_guardar = float(nuevo_stock)

        # B. LA MAGIA: Si es Bulto o Saco, multiplicamos por el contenido neto
        # Ejemplo: Si mandas 12 y el contenido es 40kg -> Guarda 480kg
        if prod_info:
            unidad = prod_info.unidad_medida
            contenido = float(prod_info.contenido_neto or 1)
            
            # Lista de unidades que se comportan como "Paquetes"
            if unidad in ["Bulto", "Saco", "Caja", "Paquete"] and contenido > 0:
                cantidad_a_guardar = float(nuevo_stock) * contenido

        # C. Guardamos la cantidad ya convertida (en Kilos/Base)
        query_existe = inventario.select().where(
            (inventario.c.producto_id == id) & 
            (inventario.c.sucursal_id == SUCURSAL_DEFAULT)
        )
        registro = await database.fetch_one(query_existe)

        if registro:
            query_inv = inventario.update().where(
                (inventario.c.producto_id == id) & 
                (inventario.c.sucursal_id == SUCURSAL_DEFAULT)
            ).values(cantidad=cantidad_a_guardar)
            await database.execute(query_inv)
        else:
            query_inv = inventario.insert().values(
                producto_id=id,
                sucursal_id=SUCURSAL_DEFAULT,
                cantidad=cantidad_a_guardar
            )
            await database.execute(query_inv)

    # 4. Retornar
    # Reusamos la lógica del GET para devolver el producto con su stock sumado
    return await obtener_producto(id) # Llamamos a la función que ya hace el Join



@router.delete("/{id}")
async def eliminar_producto(id: int):
    # Soft Delete: Solo cambiamos el estado, no borramos
    query = producto.update().where(producto.c.id == id).values(activo=False)
    result = await database.execute(query)
    
    if result == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    return {"mensaje": "Producto suspendido (soft-delete) exitosamente"}