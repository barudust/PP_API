import json
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from typing import List, Optional
from app.schemas import ProductoIn, Producto, ProductoUpdate, HistorialPrecioProducto
from sqlalchemy import select, func, text, desc
from app.core.database import database
from app.core.config import settings
from app.models import producto, inventario, especie, categoria, subcategoria, marca, producto_historial_precio, usuario
from app.core.dependencies import require_roles, ROL_GERENTE, ROL_SUPERADMIN, get_current_user_optional, get_current_user, require_perm
from app.services.permisos_service import permisos_de_rol
from app.services.historial_precio_service import registrar_cambio_precio
from app.services.export_service import generar_excel


router = APIRouter(
    prefix="/productos",
    tags=["Productos"]
)

# Modificar el catálogo (crear/editar/eliminar) requiere Gerente o SuperAdmin.
# La LECTURA queda abierta porque el POS (Android) la necesita.
_gestion_catalogo = Depends(require_roles(ROL_GERENTE))


async def _puede_ver_costo(usuario_actual) -> bool:
    """El costo de compra es sensible: solo lo ven roles con el permiso
    `productos.ver_costo` (no el vendedor). La lectura de productos es
    pública (Android sin login), por eso esto es opcional, no obligatorio."""
    if not usuario_actual:
        return False
    rol = (usuario_actual["rol"] or "").lower()
    if rol == ROL_SUPERADMIN:
        return True
    return "productos.ver_costo" in await permisos_de_rol(rol)


@router.get("/", response_model=List[Producto])
async def obtener_productos(
    tipo: Optional[str] = None,
    marca_id: Optional[int] = None,
    categoria_id: Optional[int] = None,
    subcategoria_id: Optional[int] = None,
    especie_id: Optional[int] = None,
    etapa_id: Optional[int] = None,
    q: Optional[str] = None,
    atributos: Optional[str] = Query(
        None, description='Filtro JSONB, ej. {"linea":"Premium","sabor":"Salmón"}'
    ),
    mostrar_inactivos: bool = False,
    usuario_actual=Depends(get_current_user_optional),
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
    if subcategoria_id:
        query = query.where(producto.c.subcategoria_id == subcategoria_id)
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

    filas = [dict(f) for f in await database.fetch_all(query)]
    if not await _puede_ver_costo(usuario_actual):
        for f in filas:
            f["costo"] = None
    return filas


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


@router.get("/filtros")
async def filtros_jerarquicos(
    marca_id: Optional[int] = None, categoria_id: Optional[int] = None, tipo: Optional[str] = None
):
    """
    Filtros de segundo nivel (categoría padre → opciones hija): dado un marca_id
    (y opcionalmente un tipo), devuelve solo las especies/categorías que
    realmente tienen productos activos de esa marca — para no mostrar filtros
    irrelevantes (ej. si la marca solo vende para cerdo/ave, no listar gato/perro).
    Si además se manda `categoria_id`, también devuelve las subcategorías de
    esa categoría que tienen productos (para el filtro en cascada
    Marca → Categoría → Subcategoría → Especie).
    """
    base_where = [producto.c.activo == True]
    if marca_id:
        base_where.append(producto.c.marca_id == marca_id)
    if tipo:
        base_where.append(producto.c.tipo_producto == tipo)

    q_especies = (
        select(especie.c.id, especie.c.nombre)
        .select_from(producto.join(especie, producto.c.especie_id == especie.c.id))
        .where(*base_where)
        .distinct()
        .order_by(especie.c.nombre)
    )
    q_categorias = (
        select(categoria.c.id, categoria.c.nombre)
        .select_from(producto.join(categoria, producto.c.categoria_id == categoria.c.id))
        .where(*base_where)
        .distinct()
        .order_by(categoria.c.nombre)
    )

    especies = await database.fetch_all(q_especies)
    categorias = await database.fetch_all(q_categorias)

    subcategorias = []
    if categoria_id:
        q_subcategorias = (
            select(subcategoria.c.id, subcategoria.c.nombre)
            .select_from(producto.join(subcategoria, producto.c.subcategoria_id == subcategoria.c.id))
            .where(*base_where, subcategoria.c.categoria_id == categoria_id)
            .distinct()
            .order_by(subcategoria.c.nombre)
        )
        subcategorias = await database.fetch_all(q_subcategorias)

    return {
        "especies": [dict(e) for e in especies],
        "categorias": [dict(c) for c in categorias],
        "subcategorias": [dict(s) for s in subcategorias],
    }


@router.get("/{id}", response_model=Producto)
async def obtener_producto(id: int, usuario_actual=Depends(get_current_user_optional)):
    query = producto.select().where(producto.c.id == id)
    result = await database.fetch_one(query)
    if result is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    datos = dict(result)
    if not await _puede_ver_costo(usuario_actual):
        datos["costo"] = None
    return datos

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
async def actualizar_parcial_producto(id: int, prod: ProductoUpdate, usuario=Depends(get_current_user)):

    # 1. Separar datos
    datos_actualizar = prod.model_dump(exclude_unset=True)
    nuevo_stock = datos_actualizar.pop("stock", None)  # Sacamos el stock
    # sucursal_id NO es columna de producto: es solo para el atajo de stock.
    sucursal_stock = datos_actualizar.pop("sucursal_id", None)

    if not datos_actualizar and nuevo_stock is None:
         raise HTTPException(status_code=400, detail="No se enviaron datos válidos")

    # Estado previo, para la bitácora de costo/precio (solo si alguno de los
    # dos viene en el payload — evita una consulta extra en el caso común).
    anterior = None
    if "costo" in datos_actualizar or "precio_base" in datos_actualizar:
        anterior = await database.fetch_one(producto.select().where(producto.c.id == id))

    # 2. Actualizar datos del producto (Nombre, Precio, etc.)
    if datos_actualizar:
        query = producto.update().where(producto.c.id == id).values(**datos_actualizar)
        result = await database.execute(query)
        if result == 0 and nuevo_stock is None:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        if anterior is not None:
            await registrar_cambio_precio(
                producto_id=id,
                usuario_id=usuario["id"],
                costo_anterior=anterior["costo"],
                costo_nuevo=datos_actualizar.get("costo"),
                precio_anterior=anterior["precio_base"],
                precio_nuevo=datos_actualizar.get("precio_base"),
                origen="manual",
            )

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
    # Nota: no reusamos la función del GET porque ahora depende de la inyección
    # de FastAPI (usuario_actual) y esta llamada es directa, no HTTP.
    actualizado = await database.fetch_one(producto.select().where(producto.c.id == id))
    if actualizado is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return dict(actualizado)



@router.delete("/{id}", dependencies=[_gestion_catalogo])
async def eliminar_producto(id: int):
    # Soft Delete: Solo cambiamos el estado, no borramos
    query = producto.update().where(producto.c.id == id).values(activo=False)
    result = await database.execute(query)
    
    if result == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return {"mensaje": "Producto suspendido (soft-delete) exitosamente"}


@router.get(
    "/{id}/historial-precio",
    response_model=List[HistorialPrecioProducto],
    dependencies=[Depends(require_perm("productos.ver_costo"))],
)
async def historial_precio_producto(id: int):
    """Bitácora de cambios de costo/precio_base — requiere el mismo permiso
    que ver el costo, ya que el historial también lo expone."""
    query = (
        select(producto_historial_precio, usuario.c.nombre.label("usuario_nombre"))
        .select_from(producto_historial_precio.join(usuario))
        .where(producto_historial_precio.c.producto_id == id)
        .order_by(desc(producto_historial_precio.c.fecha))
    )
    filas = await database.fetch_all(query)
    return [dict(f) for f in filas]


@router.get("/exportar/excel")
async def exportar_lista_precios_excel(marca_id: Optional[int] = None):
    """Lista de precios actual del catálogo (para la sección Listas) — no es
    el reporte de inventario (que trae existencia); este es solo nombre +
    presentación + precio, pensado para imprimir/mandar a un cliente."""
    query = (
        select(
            producto.c.nombre,
            producto.c.unidad_medida,
            producto.c.contenido_neto,
            producto.c.precio_base,
            producto.c.precio_granel,
            marca.c.nombre.label("marca_nombre"),
        )
        .select_from(producto.outerjoin(marca, producto.c.marca_id == marca.c.id))
        .where(producto.c.activo == True)
    )
    if marca_id:
        query = query.where(producto.c.marca_id == marca_id)
    query = query.order_by(marca.c.nombre.nullslast(), producto.c.nombre)

    resultados = await database.fetch_all(query)
    encabezados = ["Marca", "Producto", "Presentación", "Precio"]
    filas = [
        [
            r["marca_nombre"] or "Sin marca",
            r["nombre"],
            f"{r['contenido_neto']} {r['unidad_medida']}" if r["contenido_neto"] and float(r["contenido_neto"]) != 1 else r["unidad_medida"],
            float(r["precio_base"]),
        ]
        for r in resultados
    ]
    contenido = generar_excel(encabezados, filas, "Lista de precios")
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=lista_precios.xlsx"},
    )