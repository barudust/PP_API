from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone, date # <--- AQUÍ ESTABA EL ERROR (Faltaba date)

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
        
        # 3. Procesar Productos (Inventario y Descuentos)
        for item in data.detalles:
            # A. Datos del Producto
            q_prod = select(producto).where(producto.c.id == item.producto_id)
            prod_db = await database.fetch_one(q_prod)
            if not prod_db:
                raise HTTPException(404, f"Producto {item.producto_id} no encontrado")
            
            # B. Calcular Precio Base (Bulto vs Granel)
            precio_lista = float(prod_db['precio_base'])
            contenido_neto = float(prod_db['contenido_neto'])
            
            # Lógica simple: si es a granel y cantidad < 1 (fracción de bulto), usar precio granel si existe
            if prod_db['se_vende_a_granel'] and prod_db['precio_granel'] and item.cantidad < 1.0:
                precio_lista = float(prod_db['precio_granel'])
            
            # C. --- MOTOR DE DESCUENTOS AUTOMÁTICOS ---
            porcentaje_descuento = 0.0
            
            criterios_cliente = [regla_descuento.c.cliente_id == None]
            if data.cliente_id:
                criterios_cliente.append(regla_descuento.c.cliente_id == data.cliente_id)
            
            criterios_producto = [
                regla_descuento.c.producto_id == item.producto_id,
                regla_descuento.c.marca_id == prod_db['marca_id']
            ]
            
            query_reglas = select(regla_descuento).where(
                and_(
                    regla_descuento.c.activo == True,
                    or_(*criterios_cliente),
                    or_(*criterios_producto)
                )
            ).order_by(desc(regla_descuento.c.descuento_porcentaje))
            
            mejor_regla = await database.fetch_one(query_reglas)
            
            if mejor_regla:
                porcentaje_descuento = float(mejor_regla['descuento_porcentaje'])
            
            # Aplicar Descuento
            precio_final_unitario = precio_lista * (1 - (porcentaje_descuento / 100))
            subtotal = float(item.cantidad) * precio_final_unitario
            total_venta_bruto += subtotal

            # D. Registrar Detalle
            q_detalle = venta_detalle.insert().values(
                venta_id=venta_id,
                producto_id=item.producto_id,
                cantidad=item.cantidad,
                precio_unitario=precio_final_unitario 
            )
            await database.execute(q_detalle)
            
            # E. Descontar Inventario
            if prod_db['unidad_medida'] in ['kg', 'lt']:
                kilos_a_restar = float(item.cantidad)
            else:
                kilos_a_restar = float(item.cantidad) * contenido_neto

            q_inv = select(inventario).where(
                (inventario.c.producto_id == item.producto_id) &
                (inventario.c.sucursal_id == data.sucursal_id)
            )
            inv_db = await database.fetch_one(q_inv)
            
            stock_actual = float(inv_db['cantidad']) if inv_db else 0.0
            nuevo_stock = stock_actual - kilos_a_restar
            
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

        # 4. Cerrar Totales
        total_neto = total_venta_bruto - data.descuento_especial
        await database.execute(
            venta.update().where(venta.c.id == venta_id).values(total=total_neto)
        )
        
        return {
            "mensaje": "Venta registrada",
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
    """Listar ventas resumidas"""
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
    """Obtener el ticket completo"""
    # 1. Cabecera
    q_venta = select(venta).where(venta.c.id == id)
    v = await database.fetch_one(q_venta)
    if not v:
        raise HTTPException(404, "Venta no encontrada")
    
    # 2. Detalles
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
    """Cancela una venta y regresa el stock"""
    async with database.transaction():
        q_venta = select(venta).where(venta.c.id == id)
        v = await database.fetch_one(q_venta)
        if not v:
            raise HTTPException(404, "Venta no encontrada")
        
        # 2. Regresar stock
        q_detalles = select(venta_detalle).where(venta_detalle.c.venta_id == id)
        items = await database.fetch_all(q_detalles)
        
        for item in items:
            q_prod = select(producto).where(producto.c.id == item['producto_id'])
            prod = await database.fetch_one(q_prod)
            
            kilos_a_regresar = 0.0
            if prod['unidad_medida'] in ['kg', 'lt']:
                kilos_a_regresar = float(item['cantidad'])
            else:
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

        # 3. Eliminar venta (Reverso simple)
        await database.execute(venta_detalle.delete().where(venta_detalle.c.venta_id == id))
        await database.execute(venta.delete().where(venta.c.id == id))
        
        return {"mensaje": "Venta cancelada y stock restaurado"}