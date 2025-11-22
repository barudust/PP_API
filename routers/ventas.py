# routers/ventas.py

from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from datetime import datetime, timezone

from database import database
from models import venta, venta_detalle, inventario, producto
# (Nota: schemas lo usamos para respuesta, pero para entrada definiremos uno custom aquí para facilitar)

router = APIRouter(
    prefix="/ventas",
    tags=["Ventas"]
)

# --- Esquemas Especiales para Venta (Request) ---
class DetalleVentaReq(BaseModel):
    producto_id: int
    cantidad: float # Puede ser 0.5 (medio kilo) o 1 (un bulto)

class VentaCreateReq(BaseModel):
    sucursal_id: int
    usuario_id: int
    cliente_id: int | None = None
    detalles: List[DetalleVentaReq]
    descuento_especial: float = 0.0
    motivo_descuento: str | None = None

@router.post("/")
async def registrar_venta(data: VentaCreateReq):
    """
    Registra una venta, descuenta inventario y calcula totales.
    Todo ocurre dentro de una transacción atómica.
    """
    async with database.transaction():
        total_venta = 0.0
        
        # 1. Crear la cabecera de la Venta (con total 0 temporalmente)
        query_venta = venta.insert().values(
            sucursal_id=data.sucursal_id,
            usuario_id=data.usuario_id,
            cliente_id=data.cliente_id,
            fecha=datetime.now(timezone.utc),
            total=0, # Lo actualizamos al final
            descuento_especial_monto=data.descuento_especial,
            descuento_especial_motivo=data.motivo_descuento
        )
        venta_id = await database.execute(query_venta)
        
        # 2. Procesar cada producto
        for item in data.detalles:
            # A. Obtener info del producto (precios y peso)
            q_prod = producto.select().where(producto.c.id == item.producto_id)
            prod_db = await database.fetch_one(q_prod)
            
            if not prod_db:
                raise HTTPException(404, f"Producto {item.producto_id} no encontrado")
            
            # B. Determinar Precio y Descuento de Inventario
            # LÓGICA: Si se vende a granel y la cantidad es fraccionaria (o según tu regla de negocio),
            # usamos precio_granel. Si es entero, precio_base.
            # POR SIMPLICIDAD AHORA: 
            # Si 'unidad_medida' es 'kg', la cantidad son kilos -> Precio Granel.
            # Si 'unidad_medida' es 'bulto', la cantidad son bultos -> Precio Base.
            
            precio_final = float(prod_db['precio_base']) # Default
            kilos_a_descontar = float(item.cantidad) * float(prod_db['contenido_neto'])
            
            # Si es venta a granel (ej. maíz suelto) y el producto lo permite:
            if prod_db['se_vende_a_granel'] and prod_db['precio_granel']:
                 # Aquí tu lógica puede variar. 
                 # Asumiremos: si el cliente pide < 1 'contenido_neto', es granel.
                 # O simplemente multiplicamos cantidad * precio_base.
                 pass 
            
            subtotal = float(item.cantidad) * precio_final
            total_venta += subtotal
            
            # C. Insertar Detalle
            q_detalle = venta_detalle.insert().values(
                venta_id=venta_id,
                producto_id=item.producto_id,
                cantidad=item.cantidad,
                precio_unitario=precio_final
            )
            await database.execute(q_detalle)
            
            # D. Descontar Inventario
            # Buscamos el inventario en esa sucursal
            q_inv = inventario.select().where(
                (inventario.c.producto_id == item.producto_id) &
                (inventario.c.sucursal_id == data.sucursal_id)
            )
            inv_db = await database.fetch_one(q_inv)
            
            if not inv_db:
                raise HTTPException(400, f"No hay inventario inicial para producto {prod_db['nombre']}")
            
            nuevo_stock = float(inv_db['cantidad']) - kilos_a_descontar
            
            if nuevo_stock < 0:
                raise HTTPException(400, f"Stock insuficiente para {prod_db['nombre']}. Disponible: {inv_db['cantidad']}, Requerido: {kilos_a_descontar}")
            
            # Actualizamos stock
            q_upd_inv = inventario.update().where(inventario.c.id == inv_db['id']).values(
                cantidad=nuevo_stock,
                fecha_actualizacion=datetime.now(timezone.utc)
            )
            await database.execute(q_upd_inv)
            
        # 3. Actualizar total final de la venta
        total_final = total_venta - data.descuento_especial
        await database.execute(
            venta.update().where(venta.c.id == venta_id).values(total=total_final)
        )
        
        return {
            "venta_id": venta_id,
            "total_bruto": total_venta,
            "total_final": total_final,
            "mensaje": "Venta registrada exitosamente"
        }