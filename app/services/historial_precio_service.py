"""Bitácora de cambios de costo/precio_base de un producto."""
from typing import Optional

from app.core.database import database
from app.models import producto_historial_precio


async def registrar_cambio_precio(
    producto_id: int,
    usuario_id: int,
    costo_anterior: Optional[float],
    costo_nuevo: Optional[float],
    precio_anterior: Optional[float],
    precio_nuevo: Optional[float],
    origen: str,
    lote_id: Optional[int] = None,
) -> None:
    """Solo escribe una fila si costo o precio_base realmente cambiaron."""
    cambio_costo = costo_nuevo is not None and float(costo_anterior or 0) != float(costo_nuevo)
    cambio_precio = precio_nuevo is not None and float(precio_anterior or 0) != float(precio_nuevo)
    if not cambio_costo and not cambio_precio:
        return
    await database.execute(
        producto_historial_precio.insert().values(
            producto_id=producto_id,
            usuario_id=usuario_id,
            costo_anterior=costo_anterior if cambio_costo else None,
            costo_nuevo=costo_nuevo if cambio_costo else None,
            precio_anterior=precio_anterior if cambio_precio else None,
            precio_nuevo=precio_nuevo if cambio_precio else None,
            origen=origen,
            lote_id=lote_id,
        )
    )
