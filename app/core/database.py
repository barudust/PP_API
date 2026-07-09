# database.py

from datetime import timezone
from databases import Database
from zoneinfo import ZoneInfo  # Python 3.9+

from app.core.config import settings

# --- Conexión ---
# Nota sobre JSONB (producto.atributos_extra):
# `databases` aplica los procesadores de tipo de SQLAlchemy, por lo que las
# columnas JSONB se serializan (dict -> jsonb) y deserializan (jsonb -> dict)
# automáticamente. NO se debe registrar además un códec asyncpg de json, o se
# produce doble codificación (el valor se guarda como string en vez de objeto).
DATABASE_URL = settings.DATABASE_URL
database = Database(DATABASE_URL)

# Zona horaria de presentación (configurable por .env)
_TZ_LOCAL = ZoneInfo(settings.TIMEZONE)


# --- Funciones de Utilidad de Fechas ---

def fecha_local_iso(fecha_utc):
    """Convierte fecha UTC a string ISO YYYY-MM-DDTHH:MM:SS para el cliente."""
    if not fecha_utc:
        return None

    # Asegurar que tenga zona horaria
    if fecha_utc.tzinfo is None:
        fecha_utc = fecha_utc.replace(tzinfo=timezone.utc)

    fecha_local = fecha_utc.astimezone(_TZ_LOCAL)
    # FORMATO: Año-Mes-Día T Hora:Minuto:Segundo
    return fecha_local.strftime("%Y-%m-%dT%H:%M:%S")


def fecha_local_iso_simple(fecha_utc):
    """Convierte una fecha UTC a un string ISO YYYY-MM-DD en zona local."""
    if not fecha_utc:
        return None
    if fecha_utc.tzinfo is None:
        fecha_utc = fecha_utc.replace(tzinfo=timezone.utc)
    return fecha_utc.astimezone(_TZ_LOCAL).strftime("%Y-%m-%d")
