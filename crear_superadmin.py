"""
Bootstrap de acceso (RBAC).

Al activar el control por roles, crear usuarios vía API exige ya ser SuperAdmin.
Este script resuelve ese arranque insertando —directamente en la BD— una sucursal
por defecto y un usuario SuperAdmin inicial. Es idempotente: si ya existen, no los
duplica.

Uso:
    python crear_superadmin.py
    python crear_superadmin.py --nombre Admin --password miClave --sucursal "Matriz"
"""

import argparse
import asyncio
import sys

# La consola de Windows usa cp1252 por defecto y truena con emojis.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from sqlalchemy import select

from app.core.database import database
from app.models import sucursal, usuario
from app.core.security import get_password_hash
from app.core.dependencies import ROL_SUPERADMIN


async def _ensure_sucursal(nombre: str) -> int:
    existente = await database.fetch_one(
        select(sucursal).where(sucursal.c.nombre == nombre)
    )
    if existente:
        return existente["id"]
    # Si ya hay cualquier sucursal, reutiliza la primera
    alguna = await database.fetch_one(select(sucursal).order_by(sucursal.c.id))
    if alguna:
        return alguna["id"]
    return await database.execute(sucursal.insert().values(nombre=nombre))


async def main(nombre: str, password: str, sucursal_nombre: str) -> None:
    await database.connect()
    try:
        suc_id = await _ensure_sucursal(sucursal_nombre)

        ya = await database.fetch_one(
            select(usuario).where(usuario.c.nombre == nombre)
        )
        if ya:
            print(f"⚠️  El usuario '{nombre}' ya existe (id={ya['id']}, rol={ya['rol']}). Nada que hacer.")
            return

        user_id = await database.execute(
            usuario.insert().values(
                nombre=nombre,
                contrasena_hash=get_password_hash(password),
                rol=ROL_SUPERADMIN,
                sucursal_id=suc_id,
            )
        )
        print("✅ SuperAdmin creado.")
        print(f"   id={user_id}  usuario='{nombre}'  sucursal_id={suc_id}  rol={ROL_SUPERADMIN}")
        print(f"   contraseña='{password}'  (cámbiala en producción)")
    finally:
        await database.disconnect()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Crea el SuperAdmin inicial.")
    p.add_argument("--nombre", default="Admin")
    p.add_argument("--password", default="admin123")
    p.add_argument("--sucursal", default="Sucursal Centro")
    args = p.parse_args()
    asyncio.run(main(args.nombre, args.password, args.sucursal))
