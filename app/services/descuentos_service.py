"""
Servicio de reglas de descuento: resolución de sucursal y validación anti-conflicto.

Regla de negocio (decidida con el dueño): para el mismo cliente y la misma
sucursal, no pueden coexistir un descuento a nivel MARCA y un descuento a nivel
PRODUCTO para un producto de esa marca — sería ambiguo cuál debería aplicar.
Se debe editar/desactivar la regla existente antes de crear la que choca.
"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, and_

from app.core.database import database
from app.models import cliente, producto, regla_descuento


async def resolver_sucursal_id(cliente_id: Optional[int], sucursal_id: Optional[int]) -> Optional[int]:
    """Si hay cliente, la sucursal de la regla SIEMPRE es la del cliente
    (un cliente pertenece a una sola sucursal). Si no hay cliente, se respeta
    lo que se haya mandado (None = todas las sucursales)."""
    if cliente_id is None:
        return sucursal_id
    row = await database.fetch_one(select(cliente.c.sucursal_id).where(cliente.c.id == cliente_id))
    if not row:
        raise HTTPException(404, "Cliente no encontrado")
    return row["sucursal_id"]


async def validar_sin_conflicto(
    *,
    cliente_id: Optional[int],
    marca_id: Optional[int],
    producto_id: Optional[int],
    sucursal_id: Optional[int],
    excluir_id: Optional[int] = None,
) -> None:
    """Lanza HTTPException 409 si la regla nueva/editada chocaría con una
    regla activa existente (duplicado exacto, o mezcla marca+producto de esa
    marca para el mismo cliente+sucursal)."""

    base = and_(
        regla_descuento.c.activo == True,
        regla_descuento.c.cliente_id.is_(cliente_id) if cliente_id is None else regla_descuento.c.cliente_id == cliente_id,
        regla_descuento.c.sucursal_id.is_(sucursal_id) if sucursal_id is None else regla_descuento.c.sucursal_id == sucursal_id,
    )
    if excluir_id is not None:
        base = and_(base, regla_descuento.c.id != excluir_id)

    # 1) Duplicado exacto (mismo alcance completo)
    dup = await database.fetch_one(
        select(regla_descuento.c.id).where(
            and_(
                base,
                regla_descuento.c.marca_id.is_(marca_id) if marca_id is None else regla_descuento.c.marca_id == marca_id,
                regla_descuento.c.producto_id.is_(producto_id) if producto_id is None else regla_descuento.c.producto_id == producto_id,
            )
        )
    )
    if dup:
        raise HTTPException(409, "Ya existe una regla activa idéntica para ese cliente/marca/producto/sucursal.")

    # 2) Nueva es de PRODUCTO: ¿ya hay una regla de MARCA activa para la marca de ese producto?
    if producto_id is not None:
        prod = await database.fetch_one(select(producto.c.marca_id).where(producto.c.id == producto_id))
        if prod and prod["marca_id"]:
            choque = await database.fetch_one(
                select(regla_descuento.c.id).where(
                    and_(
                        base,
                        regla_descuento.c.marca_id == prod["marca_id"],
                        regla_descuento.c.producto_id.is_(None),
                    )
                )
            )
            if choque:
                raise HTTPException(
                    409,
                    "Ya existe un descuento general para la marca de este producto, en el mismo "
                    "cliente/sucursal. Edita o desactiva esa regla antes de crear una específica "
                    "por producto.",
                )

    # 3) Nueva es de MARCA: ¿ya hay reglas de PRODUCTO activas para productos de esa marca?
    if marca_id is not None and producto_id is None:
        choque = await database.fetch_one(
            select(regla_descuento.c.id)
            .select_from(regla_descuento.join(producto, regla_descuento.c.producto_id == producto.c.id))
            .where(
                and_(
                    base,
                    regla_descuento.c.producto_id.is_not(None),
                    producto.c.marca_id == marca_id,
                )
            )
        )
        if choque:
            raise HTTPException(
                409,
                "Ya existen descuentos por producto para esta marca, en el mismo cliente/sucursal. "
                "Edita o desactiva esas reglas antes de crear un descuento general de marca.",
            )
