from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from datetime import datetime, timezone

# Importamos la DB y Modelos
from database import database
from models import venta, venta_detalle, inventario, producto, corte_caja

router = APIRouter(
    prefix="/ventas",
    tags=["Ventas"]
)

# --- Esquemas Locales para recibir la venta (Request) ---
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
    async with database.transaction():
        
        # --- NUEVO: Buscar Corte Abierto --- 
        query_corte = select(corte_caja).where(
            (corte_caja.c.usuario_id == data.usuario_id) &
            (corte_caja.c.fecha_cierre == None)
        )
        corte_abierto = await database.fetch_one(query_corte)
        
        if not corte_abierto:
            raise HTTPException(400, "No hay un turno/corte abierto para este usuario. Debe abrir caja primero.")
        
        corte_id = corte_abierto['id']
        # -----------------------------------

        total_venta = 0.0
        
        # Actualizar la creación de la venta con el corte_id
        query_venta = venta.insert().values(
            sucursal_id=data.sucursal_id,
            usuario_id=data.usuario_id,
            cliente_id=data.cliente_id,
            corte_caja_id=corte_id, # <--- AQUÍ LO USAMOS
            fecha=datetime.now(timezone.utc),
            total=0, 
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
            
            # Lógica de Precio:
            # Por simplicidad inicial: Si el producto se vende a granel y piden < 1 (fracción), usamos precio granel.
            # Si no, usamos precio base. (Esto lo puliremos después con tu regla de 'unidad_medida').
            
            precio_usar = float(prod_db['precio_base'])
            
            # Calculamos cuántos KILOS reales se van a descontar
            # Ejemplo: Vendemos 2 Bultos (de 40kg).
            # cantidad_item = 2.0
            # contenido_neto = 40.0
            # kilos_a_descontar = 80.0
            contenido_neto_float = float(prod_db['contenido_neto'])
            kilos_a_descontar = float(item.cantidad) * contenido_neto_float
            
            subtotal = float(item.cantidad) * precio_usar
            total_venta += subtotal
            
            # C. Insertar Detalle
            q_detalle = venta_detalle.insert().values(
                venta_id=venta_id,
                producto_id=item.producto_id,
                cantidad=item.cantidad,
                precio_unitario=precio_usar
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
                raise HTTPException(400, f"No hay inventario inicial para {prod_db['nombre']}")
            
            # Convertimos Decimal a float para la resta
            stock_actual = float(inv_db['cantidad'])
            nuevo_stock = stock_actual - kilos_a_descontar
            
            if nuevo_stock < 0:
                raise HTTPException(400, f"Stock insuficiente para {prod_db['nombre']}. Disponible: {stock_actual}, Requerido: {kilos_a_descontar}")
            
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