# config.py
"""
Configuración centralizada del proyecto.

Lee variables desde el entorno y, si existe, desde un archivo `.env` en la raíz.
Usa SOLO la librería estándar (parser propio de `.env`) para no agregar
dependencias nuevas ni romper el arranque si falta un paquete.

Los valores por defecto corresponden al entorno de DESARROLLO actual, de modo
que si no hay `.env` la app arranca igual que antes.
"""

import os
from pathlib import Path

# --- Cargador de .env sin dependencias externas ---
def _cargar_dotenv(ruta: Path) -> None:
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        clave = clave.strip()
        valor = valor.strip().strip('"').strip("'")
        # No sobrescribir variables ya definidas en el entorno real
        os.environ.setdefault(clave, valor)


_cargar_dotenv(Path(__file__).resolve().parent / ".env")


def _lista(valor: str) -> list[str]:
    return [item.strip() for item in valor.split(",") if item.strip()]


class Settings:
    """Configuración de la aplicación (valores de desarrollo por defecto)."""

    # --- Base de datos ---
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:1234@localhost:5433/negocio",
    )

    # --- Seguridad / JWT ---
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "tu_secreto_super_seguro_cambialo_por_algo_largo",
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24))  # 1 día
    )

    # --- CORS (orígenes permitidos: app web, dev server, etc.) ---
    # La app Android nativa no requiere CORS; la web sí.
    CORS_ORIGINS: list[str] = _lista(
        os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    )

    # --- Zona horaria para presentación de fechas ---
    TIMEZONE: str = os.getenv("TIMEZONE", "America/Mexico_City")

    # --- Reglas de negocio ---
    # Sucursal usada por el atajo de "stock" al editar un producto sin especificar
    # sucursal (compatibilidad con el POS). Antes estaba hardcodeada a 1.
    SUCURSAL_DEFAULT: int = int(os.getenv("SUCURSAL_DEFAULT", "1"))
    # Si es False (default), una venta no puede dejar el stock por debajo de 0.
    PERMITIR_STOCK_NEGATIVO: bool = os.getenv(
        "PERMITIR_STOCK_NEGATIVO", "false"
    ).lower() in ("1", "true", "yes", "si")


settings = Settings()
