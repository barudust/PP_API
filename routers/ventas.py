from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone, date

from sqlalchemy import select, desc, or_, and_

from database import database, fecha_local_iso
from models import venta, venta_detalle, inventario, producto, corte_caja, regla_descuento

router = APIRouter(
    prefix="/ventas",
    tags=["Ventas"]
)

# --- Esquemas ---
class DetalleVentaReq(BaseModel):
    producto_id: int
    cantidad: float
    es_granel: bool = False

class VentaCreateReq(BaseModel):
    sucursal_id: int
    usuario_id: int
    cliente_id: Optional[int] = None
    detalles: List[DetalleVentaReq]
    descuento_especial: float = 0.0
    motivo_descuento: Optional[str] = None

@router.post("/", response_model=dict)
async def registrar_venta(data: VentaCreateReq):
    async with database.transaction():
        
        # 1. Validar Corte de Caja Abierto
        query_corte = select(corte_caja).where(
            (corte_caja.c.usuario_id == data.usuario_id) &
            (corte_caja.c.fecha_cierre == None)
        )
        corte_abierto = await database.fetch_one(query_corte)
        if not corte_abierto:
            raise HTTPException(400, "No hay turno abierto. Debe abrir caja primero.")
        
        total_venta_bruto = 0.0
        
        # 2. Crear Cabecera Venta
        query_venta = venta.insert().values(
            sucursal_id=data.sucursal_id,
            usuario_id=data.usuario_id,
            cliente_id=data.cliente_id,
            corte_caja_id=corte_abierto['id'],
            fecha=datetime.now(timezone.utc),
            total=0, # Se actualiza al final
            descuento_especial_monto=data.descuento_especial,
            descuento_especial_motivo=data.motivo_descuento
        )
        venta_id = await database.execute(query_venta)
        
        # 3. Procesar Productos
        for item in data.detalles:
            # A. Obtener datos maestros del producto
            q_prod = select(producto).where(producto.c.id == item.producto_id)
            prod_db = await database.fetch_one(q_prod)
            
            if not prod_db:
                raise HTTPException(404, f"Producto {item.producto_id} no encontrado")

            # --- LÓGICA DE PRECIO BASE Y DESCUENTO DE STOCK ---
            precio_base = float(prod_db['precio_base'])
            precio_granel = float(prod_db['precio_granel'] or 0.0)
            contenido_neto = float(prod_db['contenido_neto'] or 1.0)
            
            precio_lista_a_usar = 0.0
            kilos_a_restar_total = 0.0

            if item.es_granel:
                # VENTA A GRANEL (Kilos sueltos)
                # 1. Usamos el precio por kilo
                precio_lista_a_usar = precio_granel if precio_granel > 0 else precio_base
                # 2. Restamos la cantidad exacta (ej. 0.5kg)
                kilos_a_restar_total = float(item.cantidad)
            else:
                # VENTA POR PAQUETE (Bulto/Caja cerrada)
                # 1. Usamos el precio del paquete
                precio_lista_a_usar = precio_base
                # 2. Restamos Cantidad * Contenido (ej. 1 bulto * 20kg = 20kg)
                if prod_db['unidad_medida'] in ['kg', 'lt', 'Kg', 'Litro']:
                    kilos_a_restar_total = float(item.cantidad)
                else:
                    kilos_a_restar_total = float(item.cantidad) * contenido_neto

            # --- MOTOR DE DESCUENTOS AUTOMÁTICOS ---
            porcentaje_descuento = 0.0
            query_reglas = select(regla_descuento).where(
                and_(
                    regla_descuento.c.activo == True,
                    or_(regla_descuento.c.cliente_id == data.cliente_id, regla_descuento.c.cliente_id == None),
                    or_(
                        regla_descuento.c.producto_id == item.producto_id,
                        regla_descuento.c.marca_id == prod_db['marca_id'],
                        and_(regla_descuento.c.producto_id == None, regla_descuento.c.marca_id == None)
                    )
                )
            ).order_by(
                desc(regla_descuento.c.producto_id),
                desc(regla_descuento.c.marca_id),
                desc(regla_descuento.c.descuento_porcentaje)
            )

            mejor_regla = await database.fetch_one(query_reglas)
            if mejor_regla:
                porcentaje_descuento = float(mejor_regla['descuento_porcentaje'])
            
            # Cálculo de precios finales
            precio_final_unitario = precio_lista_a_usar * (1 - (porcentaje_descuento / 100))
            subtotal = float(item.cantidad) * precio_final_unitario
            total_venta_bruto += subtotal

            # D. Registrar Detalle en la base de datos
            q_detalle = venta_detalle.insert().values(
                venta_id=venta_id,
                producto_id=item.producto_id,
                cantidad=item.cantidad,
                precio_unitario=precio_final_unitario 
            )
            await database.execute(q_detalle)
            
            # E. Actualizar Inventario (Usando el cálculo corregido)
            q_inv = select(inventario).where(
                (inventario.c.producto_id == item.producto_id) &
                (inventario.c.sucursal_id == data.sucursal_id)
            )
            inv_db = await database.fetch_one(q_inv)
            
            stock_actual = float(inv_db['cantidad']) if inv_db else 0.0
            nuevo_stock = stock_actual - kilos_a_restar_total
            
            if inv_db:
                await database.execute(
                    inventario.update().where(inventario.c.id == inv_db['id']).values(
                        cantidad=nuevo_stock, fecha_actualizacion=datetime.now(timezone.utc)
                    )
                )
            else:
                await database.execute(
                    inventario.insert().values(
                        producto_id=item.producto_id, sucursal_id=data.sucursal_id,
                        cantidad=nuevo_stock, fecha_actualizacion=datetime.now(timezone.utc)
                    )
                )

        # 4. Cerrar Totales Finales
        total_neto = total_venta_bruto - data.descuento_especial
        await database.execute(
            venta.update().where(venta.c.id == venta_id).values(total=total_neto)
        )
        
        return {
            "mensaje": "Venta registrada exitosamente",
            "venta_id": venta_id,
            "total_original": total_venta_bruto,
            "total_final": total_neto,
            "descuento_aplicado": total_venta_bruto - total_neto
        }

@router.get("/", response_model=List[dict])
async def listar_ventas(
    sucursal_id: Optional[int] = None,
    fecha: Optional[date] = None
):
    query = select(venta)
    if sucursal_id:
        query = query.where(venta.c.sucursal_id == sucursal_id)
    if fecha:
        inicio = datetime.combine(fecha, datetime.min.time())
        fin = datetime.combine(fecha, datetime.max.time())
        query = query.where((venta.c.fecha >= inicio) & (venta.c.fecha <= fin))
    
    query = query.order_by(desc(venta.c.fecha))
    registros = await database.fetch_all(query)
    
    return [
        {**dict(r), "fecha": fecha_local_iso(r["fecha"])} 
        for r in registros
    ]

@router.get("/{id}", response_model=dict)
async def obtener_venta(id: int):
    q_venta = select(venta).where(venta.c.id == id)
    v = await database.fetch_one(q_venta)
    if not v:
        raise HTTPException(404, "Venta no encontrada")
    
    q_detalles = select(
        venta_detalle.c.cantidad,
        venta_detalle.c.precio_unitario,
        producto.c.nombre,
        producto.c.unidad_medida
    ).select_from(
        venta_detalle.join(producto)
    ).where(venta_detalle.c.venta_id == id)
    
    detalles = await database.fetch_all(q_detalles)
    
    return {
        "venta": {**dict(v), "fecha": fecha_local_iso(v["fecha"])},
        "productos": [dict(d) for d in detalles]
    }

@router.put("/{id}/cancelar")
async def cancelar_venta(id: int):
    async with database.transaction():
        q_venta = select(venta).where(venta.c.id == id)
        v = await database.fetch_one(q_venta)
        if not v:
            raise HTTPException(404, "Venta no encontrada")
        
        q_detalles = select(venta_detalle).where(venta_detalle.c.venta_id == id)
        items = await database.fetch_all(q_detalles)
        
        for item in items:
            q_prod = select(producto).where(producto.c.id == item['producto_id'])
            prod = await database.fetch_one(q_prod)
            
            # Al cancelar, regresamos exactamente lo que se restó
            # (Aquí asumimos que la venta original se hizo con la lógica de bulto/kg)
            # Como no guardamos en venta_detalle si fue granel o no, 
            # inferimos por la unidad medida como fallback seguro.
            kilos_a_regresar = float(item['cantidad'])
            if prod['unidad_medida'] not in ['kg', 'lt', 'Kg', 'Litro']:
                # Si la cantidad es entera, es probable que fuera un bulto
                if float(item['cantidad']) % 1 == 0:
                     kilos_a_regresar = float(item['cantidad']) * float(prod['contenido_neto'])
            
            q_inv = select(inventario).where(
                (inventario.c.producto_id == item['producto_id']) &
                (inventario.c.sucursal_id == v['sucursal_id'])
            )
            inv = await database.fetch_one(q_inv)
            
            if inv:
                nuevo_stock = float(inv['cantidad']) + kilos_a_regresar
                await database.execute(
                    inventario.update().where(inventario.c.id == inv['id']).values(
                        cantidad=nuevo_stock,
                        fecha_actualizacion=datetime.now(timezone.utc)
                    )
                )

        await database.execute(venta_detalle.delete().where(venta_detalle.c.venta_id == id))
        await database.execute(venta.delete().where(venta.c.id == id))
        
        return {"mensaje": "Venta cancelada y stock restaurado"}