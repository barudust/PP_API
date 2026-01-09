# database.py

from databases import Database
from zoneinfo import ZoneInfo  # Python 3.9+

# --- Tu configuración de conexión ---
DATABASE_URL = "postgresql+asyncpg://postgres:1234@localhost:5433/negocio"
database = Database(DATABASE_URL)

# --- Funciones de Utilidad de Fechas ---
# Movimos tus funciones de ayuda de 'main.py' aquí

def fecha_local_iso(fecha_utc):
    """Convierte fecha UTC a string ISO YYYY-MM-DDTHH:MM:SS para Android."""
    if not fecha_utc: return None
    cdmx_tz = ZoneInfo("America/Mexico_City")
    
    # Asegurar que tenga zona horaria
    if fecha_utc.tzinfo is None:
        fecha_utc = fecha_utc.replace(tzinfo=timezone.utc)
    
    fecha_local = fecha_utc.astimezone(cdmx_tz)
    # FORZAMOS el formato: Año-Mes-Día T Hora:Minuto:Segundo
    return fecha_local.strftime("%Y-%m-%dT%H:%M:%S")

def fecha_local_iso_simple(fecha_utc):
    """Convierte una fecha UTC a un string ISO YYYY-MM-DD en zona CDMX."""
    # (Esta función estaba duplicada en tu main.py, la unificamos)
    cdmx_tz = ZoneInfo("America/Mexico_City")
    return fecha_utc.astimezone(cdmx_tz).strftime("%Y-%m-%d")