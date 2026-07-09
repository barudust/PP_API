import json
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from app.schemas import ProductoIn, Producto, ProductoUpdate
from sqlalchemy import select, func, text
from app.core.database import database
from app.core.config import settings
from app.models import producto, inventario
from app.core.dependencies import require_roles, ROL_GERENTE


router = APIRouter(
    prefix="/productos",
    tags=["Productos"]
)

# Modificar el catálogo (crear/editar/eliminar) requiere Gerente o SuperAdmin.
# La LECTURA queda abierta porque el POS (Android) la necesita.
_gestion_catalogo = Depends(require_roles(ROL_GERENTE))


@router.get("/", response_model=List[Producto])
async def obtener_productos(
    tipo: Optional[str] = None,
    marca_id: Optional[int] = None,
    categoria_id: Optional[int] = None,
    especie_id: Optional[int] = None,
    etapa_id: Optional[int] = None,
    q: Optional[str] = None,
    atributos: Optional[str] = Query(
        None, description='Filtro JSONB, ej. {"linea":"Premium","sabor":"Salmón"}'
    ),
    mostrar_inactivos: bool = False,
):
    """
    Lista productos con su stock consolidado. Soporta filtros dinámicos por
    dimensiones relacionales y por atributos JSONB (modelo híbrido — ADR-005).
    """
    query = select(
        producto,
        func.coalesce(func.sum(inventario.c.cantidad), 0).label("stock_actual"),
    ).select_from(
        producto.outerjoin(inventario, producto.c.id == inventario.c.producto_id)
    ).group_by(producto.c.id)

    if not mostrar_inactivos:
        query = query.where(producto.c.activo == True)
    if tipo:
        query = query.where(producto.c.tipo_producto == tipo)
    if marca_id:
        query = query.where(producto.c.marca_id == marca_id)
    if categoria_id:
        query = query.where(producto.c.categoria_id == categoria_id)
    if especie_id:
        query = query.where(producto.c.especie_id == especie_id)
    if etapa_id:
        query = query.where(producto.c.etapa_id == etapa_id)
    if q:
        query = query.where(producto.c.nombre.ilike(f"%{q}%"))
    if atributos:
        try:
            filtros = json.loads(atributos)
        except json.JSONDecodeError:
            raise HTTPException(400, "El parámetro 'atributos' no es JSON válido")
        for clave, valor in filtros.items():
            query = query.where(producto.c.atributos_extra[clave].astext == str(valor))

    return await database.fetch_all(query)


@router.get("/atributos-disponibles")
async def atributos_disponibles(tipo: Optional[str] = None):
    """
    Devuelve las llaves de `atributos_extra` presentes (con sus valores distintos)
    para que el frontend construya filtros dinámicos según el tipo de producto.
    Ej: {"linea": ["Premium","Estándar"], "sabor": ["Salmón","Pollo"]}
    """
    partes = [
        "SELECT kv.key AS clave, array_agg(DISTINCT kv.value) AS valores",
        "FROM producto p, jsonb_each_text(p.atributos_extra) AS kv",
        "WHERE p.activo = true",
    ]
    if tipo:
        partes.append("AND p.tipo_producto = :tipo")
    partes.append("GROUP BY kv.key ORDER BY kv.key")

    stmt = text(" ".join(partes))
    if tipo:
        stmt = stmt.bindparams(tipo=tipo)

    filas = await database.fetch_all(stmt)
    return {f["clave"]: list(f["valores"]) for f in filas}




@router.get("/{id}", response_model=Producto)
async def obtener_producto(id: int):
    query = producto.select().where(producto.c.id == id)
    result = await database.fetch_one(query)
    if result is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return result

@router.post("/", response_model=Producto, dependencies=[_gestion_catalogo])
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

@router.patch("/{id}/", response_model=Producto, dependencies=[_gestion_catalogo])
@router.put("/{id}/", response_model=Producto, dependencies=[_gestion_catalogo])
@router.patch("/{id}", response_model=Producto, dependencies=[_gestion_catalogo])
@router.put("/{id}", response_model=Producto, dependencies=[_gestion_catalogo])
async def actualizar_parcial_producto(id: int, prod: ProductoUpdate):

    # 1. Separar datos
    datos_actualizar = prod.model_dump(exclude_unset=True)
    nuevo_stock = datos_actualizar.pop("stock", None)  # Sacamos el stock
    # sucursal_id NO es columna de producto: es solo para el atajo de stock.
    sucursal_stock = datos_actualizar.pop("sucursal_id", None)

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
        # Sucursal: la enviada en el payload o la configurada por defecto (.env)
        sucursal_destino = sucursal_stock or settings.SUCURSAL_DEFAULT

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
            (inventario.c.sucursal_id == sucursal_destino)
        )
        registro = await database.fetch_one(query_existe)

        if registro:
            query_inv = inventario.update().where(
                (inventario.c.producto_id == id) & 
                (inventario.c.sucursal_id == sucursal_destino)
            ).values(cantidad=cantidad_a_guardar)
            await database.execute(query_inv)
        else:
            query_inv = inventario.insert().values(
                producto_id=id,
                sucursal_id=sucursal_destino,
                cantidad=cantidad_a_guardar
            )
            await database.execute(query_inv)

    # 4. Retornar
    # Reusamos la lógica del GET para devolver el producto con su stock sumado
    return await obtener_producto(id) # Llamamos a la función que ya hace el Join



@router.delete("/{id}", dependencies=[_gestion_catalogo])
async def eliminar_producto(id: int):
    # Soft Delete: Solo cambiamos el estado, no borramos
    query = producto.update().where(producto.c.id == id).values(activo=False)
    result = await database.execute(query)
    
    if result == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    return {"mensaje": "Producto suspendido (soft-delete) exitosamente"}