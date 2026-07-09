"""
Servicios de inventario: lógica reutilizable de stock y bitácora.

Las funciones que escriben en la BD asumen que corren dentro de una transacción
abierta por el router (`async with database.transaction()`), de modo que si algo
falla, todo se revierte junto (ACID).
"""
from datetime import datetime, timezone
from typing import Optional

from app.core.database import database
from app.models import historial_inventario


async def registrar_movimiento(
    *,
    sucursal_id: int,
    usuario_id: int,
    producto_id: int,
    tipo_movimiento: str,
    cantidad_anterior: float,
    cantidad_movida: float,
    cantidad_nueva: float,
    motivo: Optional[str] = None,
) -> None:
    """Escribe una entrada en la bitácora `historial_inventario`."""
    await database.execute(
        historial_inventario.insert().values(
            fecha=datetime.now(timezone.utc),
            sucursal_id=sucursal_id,
            usuario_id=usuario_id,
            producto_id=producto_id,
            tipo_movimiento=tipo_movimiento,
            cantidad_anterior=cantidad_anterior,
            cantidad_movida=cantidad_movida,
            cantidad_nueva=cantidad_nueva,
            motivo=motivo,
        )
    )
